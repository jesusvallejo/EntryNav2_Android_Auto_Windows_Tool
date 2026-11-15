# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""ENET network adapter diagnostics, IP configuration checks, and reachability testing."""

import platform
import re
import subprocess


class NetworkDiagnostics:
    """Provides local network adapter inspection and ENET cable diagnostics."""

    @staticmethod
    def ping_host(host: str = "169.254.1.0", timeout_sec: int = 2) -> tuple[bool, str]:
        """Send quick ICMP ping to verify physical link and IP routing to the car."""
        is_windows = platform.system() == "Windows"
        cmd = ["ping", "-n", "2", "-w", str(timeout_sec * 1000), host] if is_windows else ["ping", "-c", "2", "-W", str(timeout_sec), host]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec + 2)
            out = res.stdout
            if is_windows:
                success = "Reply from" in out and "bytes=" in out and "Destination host unreachable" not in out
            else:
                success = res.returncode == 0

            if success:
                return True, f"Car at {host} responded to ping successfully."
            else:
                return False, f"Car at {host} did not respond to ping. (Check ENET cable & ignition)"
        except Exception as e:
            return False, f"Ping check error: {e}"

    @staticmethod
    def get_adapter_summary() -> dict:
        """Scan active network adapters to identify ENET / APIPA connections."""
        is_windows = platform.system() == "Windows"
        summary = {
            "has_apipa": False,
            "apipa_ip": "",
            "active_adapters": [],
            "recommendation": ""
        }

        try:
            if is_windows:
                res = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=5)
                lines = res.stdout.splitlines()
                cur_adapter = ""

                for line in lines:
                    if "adapter" in line.lower() and ":" in line:
                        cur_adapter = line.split("adapter")[-1].strip(" :")
                    elif "ipv4" in line.lower() or "adresse ipv4" in line.lower():
                        m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if m:
                            ip = m.group(1)
                            summary["active_adapters"].append({"name": cur_adapter, "ip": ip})
                            if ip.startswith("169.254."):
                                summary["has_apipa"] = True
                                summary["apipa_ip"] = ip
            else:
                res = subprocess.run(["ip", "addr"], capture_output=True, text=True, timeout=5)
                for line in res.stdout.splitlines():
                    if "inet " in line:
                        m = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                        if m:
                            ip = m.group(1)
                            summary["active_adapters"].append({"name": "Interface", "ip": ip})
                            if ip.startswith("169.254."):
                                summary["has_apipa"] = True
                                summary["apipa_ip"] = ip
        except Exception:
            pass

        if summary["has_apipa"]:
            summary["recommendation"] = f"ENET Link Ready: PC assigned private IP {summary['apipa_ip']} (APIPA)."
        else:
            summary["recommendation"] = "No 169.254.x.x link detected. Plug in ENET cable with car engine running and wait ~15s."

        return summary
