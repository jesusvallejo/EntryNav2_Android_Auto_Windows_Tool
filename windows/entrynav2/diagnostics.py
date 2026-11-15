# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Diagnostic log management, maintenance mode toggling, and Wi-Fi link analysis."""

import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .transport import SSHClientWrapper


@dataclass
class WifiMetrics:
    """Parsed metrics for a Wi-Fi link sample."""
    frequency_mhz: int = 0
    band: str = "Unknown"
    channel: int = 0
    signal_dbm: int = 0
    quality_rating: str = "Unknown"
    rx_bitrate_mbps: float = 0.0
    tx_bitrate_mbps: float = 0.0
    retry_count: int = 0
    lost_frames: int = 0
    rtt_ms: float = 0.0
    timestamp: str = ""
    raw_line: str = ""


class WifiAnalyzer:
    """Parses and evaluates [WifiLink] metrics from entry-aa-service logs."""

    WIFI_LINE_REGEX = re.compile(
        r"(?:\[(?P<ts>\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]\s*)?\[WifiLink\]\s+(?P<rest>.*)",
        re.IGNORECASE
    )

    @staticmethod
    def _freq_to_band_and_channel(freq: int) -> tuple[str, int]:
        if 2412 <= freq <= 2484:
            ch = (freq - 2407) // 5 if freq <= 2472 else 14
            return "2.4 GHz", ch
        elif 5170 <= freq <= 5825:
            ch = (freq - 5000) // 5
            return "5 GHz", ch
        return "Unknown", 0

    @staticmethod
    def _rate_signal(dbm: int) -> str:
        if dbm == 0:
            return "Unknown"
        if dbm >= -50:
            return "Excellent"
        elif dbm >= -65:
            return "Good"
        elif dbm >= -75:
            return "Fair"
        elif dbm >= -85:
            return "Poor"
        return "Critical (Drop Risk)"

    @classmethod
    def parse_line(cls, line: str) -> WifiMetrics | None:
        """Parse a single log line into structured WifiMetrics."""
        m = cls.WIFI_LINE_REGEX.search(line)
        if not m:
            if "[WifiLink]" not in line:
                return None
            rest = line.split("[WifiLink]", 1)[-1]
            ts = ""
        else:
            ts = m.group("ts") or ""
            rest = m.group("rest")

        metrics = WifiMetrics(timestamp=ts, raw_line=line.strip())

        # Extract freq
        m_freq = re.search(r'freq[=:\s]+(\d+)', rest, re.IGNORECASE)
        if m_freq:
            metrics.frequency_mhz = int(m_freq.group(1))
            metrics.band, metrics.channel = cls._freq_to_band_and_channel(metrics.frequency_mhz)

        # Extract signal / RSSI
        m_sig = re.search(r'(?:signal|rssi)[=:\s]+(-?\d+)', rest, re.IGNORECASE)
        if m_sig:
            metrics.signal_dbm = int(m_sig.group(1))
            metrics.quality_rating = cls._rate_signal(metrics.signal_dbm)

        # Extract rx_rate / tx_rate
        m_rx = re.search(r'rx[_\-\s]*rate[=:\s]+([0-9\.]+)', rest, re.IGNORECASE)
        if m_rx:
            metrics.rx_bitrate_mbps = float(m_rx.group(1))

        m_tx = re.search(r'tx[_\-\s]*rate[=:\s]+([0-9\.]+)', rest, re.IGNORECASE)
        if m_tx:
            metrics.tx_bitrate_mbps = float(m_tx.group(1))

        # Extract retry count
        m_ret = re.search(r'retry(?:_count)?[=:\s]+(\d+)', rest, re.IGNORECASE)
        if m_ret:
            metrics.retry_count = int(m_ret.group(1))

        # Extract lost frames
        m_lost = re.search(r'lost(?:_frames)?[=:\s]+(\d+)', rest, re.IGNORECASE)
        if m_lost:
            metrics.lost_frames = int(m_lost.group(1))

        # Extract RTT
        m_rtt = re.search(r'rtt[=:\s]+([0-9\.]+)', rest, re.IGNORECASE)
        if m_rtt:
            metrics.rtt_ms = float(m_rtt.group(1))

        return metrics

    @classmethod
    def analyze_log_content(cls, content: str) -> dict:
        """Analyze entire log text and generate comprehensive Wi-Fi diagnosis."""
        samples: list[WifiMetrics] = []
        for line in content.splitlines():
            metric = cls.parse_line(line)
            if metric:
                samples.append(metric)

        if not samples:
            return {
                "detected": False,
                "count": 0,
                "latest": None,
                "diagnosis": "No Wi-Fi link diagnostic records found in log.",
                "summary": "Wireless connection statistics were not recorded. Ensure maintenance logging was active during wireless session."
            }

        latest = samples[-1]
        signals = [s.signal_dbm for s in samples if s.signal_dbm != 0]
        avg_signal = sum(signals) / len(signals) if signals else 0
        total_lost = sum(s.lost_frames for s in samples)
        total_retries = sum(s.retry_count for s in samples)

        # Build diagnostic advice
        status_flags = []
        if latest.band == "5 GHz":
            status_flags.append("5 GHz Band (High throughput)")
        elif latest.band == "2.4 GHz":
            status_flags.append("2.4 GHz Band (Crowded frequency, prone to audio stutter)")

        if latest.signal_dbm and latest.signal_dbm <= -75:
            status_flags.append("Weak signal (Keep phone close to head unit or away from metallic objects)")

        if total_lost > 5:
            status_flags.append(f"Significant packet loss ({total_lost} frames lost)")
        elif total_retries > 50:
            status_flags.append(f"High frame retries ({total_retries} retries, possible radio interference)")
        else:
            status_flags.append("Clean RF link (Low packet retries / zero dropouts)")

        diagnosis_text = " | ".join(status_flags)

        return {
            "detected": True,
            "count": len(samples),
            "latest": asdict(latest),
            "avg_signal_dbm": round(avg_signal, 1),
            "total_lost_frames": total_lost,
            "total_retries": total_retries,
            "diagnosis": diagnosis_text,
            "summary": (
                f"Wi-Fi Link: {latest.band} Ch {latest.channel} @ {latest.signal_dbm} dBm ({latest.quality_rating}) | "
                f"Tx/Rx: {latest.tx_bitrate_mbps}/{latest.rx_bitrate_mbps} Mbps | "
                f"Retries: {total_retries}, Lost: {total_lost}"
            )
        }


class LogManager:
    """Manages head unit maintenance logging, diagnostic log extraction, and analysis."""

    def __init__(self, ssh: SSHClientWrapper, log_callback=None):
        self.ssh = ssh
        self.logger = ssh.logger
        self.log_cb = log_callback or (lambda msg: None)

    def log(self, tag: str, msg: str):
        self.logger.log(tag, msg)
        self.log_cb(f"[{datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}")

    def get_logging_status(self) -> dict:
        """Check whether maintenance logging is enabled on head unit with true offline awareness."""
        self.log("INFO", "Checking maintenance logging status on car (/var/local/data/AA/maintenance)...")

        # Execute check with explicit status handling
        code_m, out_m, err_m = self.ssh.run_command(
            "test -f /var/local/data/AA/maintenance && echo ENABLED || echo DISABLED"
        )

        # Connection error: Host is offline or unreachable
        if code_m not in (0, 1) or ("Connection refused" in err_m or "timed out" in err_m or "Host unreachable" in err_m):
            status_info = {
                "connected": False,
                "enabled": False,
                "status_text": "OFFLINE / UNREACHABLE",
                "files": [],
                "flag_file": "/var/local/data/AA/maintenance",
                "raw_output": err_m.strip() or "Connection error"
            }
            self.log("WARN", f"Head unit unreachable at {self.ssh.host}:{self.ssh.port}.")
            return status_info

        enabled = "ENABLED" in out_m

        cmd_files = "ls -lh /var/local/data/AA/app.log /var/local/data/AA/app.old.log /tmp/entry-aa-service.log 2>/dev/null"
        code_ls, out_ls, _ = self.ssh.run_command(cmd_files)
        file_details = []
        if code_ls == 0 and out_ls.strip():
            for line in out_ls.splitlines():
                parts = line.strip().split()
                if len(parts) >= 9:
                    fname = os.path.basename(parts[8])
                    fsize = parts[4]
                    file_details.append(f"{fname} ({fsize})")

        status_info = {
            "connected": True,
            "enabled": enabled,
            "status_text": "ENABLED" if enabled else "DISABLED",
            "files": file_details,
            "flag_file": "/var/local/data/AA/maintenance",
            "raw_output": out_m.strip()
        }

        if enabled:
            self.log("OK", "🔍 Maintenance logging is currently ENABLED on car.")
        else:
            self.log("INFO", "🔍 Maintenance logging is currently DISABLED on car (Normal mode).")

        if file_details:
            self.log("INFO", f"   Active diagnostic logs on car: {', '.join(file_details)}")
        else:
            self.log("INFO", "   No diagnostic log files currently present on car.")

        return status_info

    def enable_logs(self) -> bool:
        """Enable diagnostic maintenance logging on car."""
        self.log("INFO", "Enabling maintenance logging on car (/var/local/data/AA/maintenance)...")
        code, _, err = self.ssh.run_command("mkdir -p /var/local/data/AA && touch /var/local/data/AA/maintenance")
        if code == 0:
            self.log("OK", "✅ Maintenance logs ENABLED. Logs will be recorded when Android Auto runs.")
            return True
        self.log("ERROR", f"❌ Failed to enable logs: {err}")
        return False

    def disable_and_clear_logs(self) -> bool:
        """Disable maintenance logging and purge diagnostic files to preserve flash storage."""
        self.log("INFO", "Disabling maintenance logging and purging log files from car...")
        cmd = "rm -f /var/local/data/AA/maintenance /var/local/data/AA/app.log /var/local/data/AA/app.old.log /tmp/entry-aa-service.log"
        code, _, err = self.ssh.run_command(cmd)
        if code == 0:
            self.log("OK", "✅ Logs purged and maintenance logging disabled.")
            return True
        self.log("ERROR", f"❌ Failed to clear logs: {err}")
        return False

    def pull_logs(self, target_dir: str | None = None) -> tuple[bool, str, dict]:
        """Pull diagnostic logs from car and analyze Wi-Fi metrics."""
        if not target_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_dir = os.path.join(os.getcwd(), "BMW_Logs", f"Logs_{timestamp}")
        os.makedirs(target_dir, exist_ok=True)

        self.log("INFO", f"Pulling diagnostic logs from EntryNav2 to: {target_dir}")
        files_to_pull = [
            ("/var/local/data/AA/app.log", "app.log"),
            ("/var/local/data/AA/app.old.log", "app.old.log"),
            ("/tmp/entry-aa-service.log", "entry-aa-service.log"),
            ("/var/local/data/AA/app-guard", "app-guard"),
            ("/var/local/data/AA/vehicle", "vehicle"),
        ]

        downloaded = {}
        wifi_raw_content = ""

        for remote_path, filename in files_to_pull:
            local_path = os.path.join(target_dir, filename)
            code, out, err = self.ssh.scp_download(remote_path, local_path)
            if code == 0 and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                downloaded[filename] = local_path
                self.log("OK", f"   [Pulled] {filename} ({os.path.getsize(local_path)} bytes)")
                if filename == "entry-aa-service.log":
                    try:
                        with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                            wifi_raw_content = f.read()
                    except Exception:
                        pass

        if not downloaded:
            self.log("WARN", "⚠️ No logs found on car. (Ensure maintenance logs are enabled and Android Auto has run).")
            return False, target_dir, {}

        self.log("OK", f"✅ Successfully pulled {len(downloaded)} log file(s).")

        wifi_analysis = WifiAnalyzer.analyze_log_content(wifi_raw_content) if wifi_raw_content else {"detected": False}
        if wifi_analysis.get("detected"):
            self.log("OK", f"📡 Wi-Fi Link Diagnostics: {wifi_analysis['summary']}")
            self.log("INFO", f"   • Health Advice: {wifi_analysis['diagnosis']}")

        return True, target_dir, {
            "downloaded": downloaded,
            "wifi_analysis": wifi_analysis
        }
