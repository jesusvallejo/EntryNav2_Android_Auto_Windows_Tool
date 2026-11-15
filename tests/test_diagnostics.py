# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Unit tests for diagnostic logs and Wi-Fi link analysis."""

import sys
from pathlib import Path

# Add windows directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "windows"))

from entrynav2.diagnostics import WifiAnalyzer, WifiMetrics


def test_wifi_line_parser_5ghz():
    """Test parsing a real 5 GHz Wi-Fi link sample."""
    line = "[10:21:03.452] [WifiLink] freq=5180 signal=-45 dBm rx_rate=433.3 Mbps tx_rate=433.3 Mbps lost=0 retry=2 rtt=12.4ms"
    metric = WifiAnalyzer.parse_line(line)
    assert metric is not None
    assert metric.frequency_mhz == 5180
    assert metric.band == "5 GHz"
    assert metric.channel == 36
    assert metric.signal_dbm == -45
    assert metric.quality_rating == "Excellent"
    assert metric.rx_bitrate_mbps == 433.3
    assert metric.tx_bitrate_mbps == 433.3
    assert metric.lost_frames == 0
    assert metric.retry_count == 2
    assert metric.rtt_ms == 12.4


def test_wifi_line_parser_24ghz():
    """Test parsing a 2.4 GHz Wi-Fi link sample."""
    line = "[WifiLink] freq: 2412, RSSI: -78 dBm, rx_rate: 72.2 Mbps, tx_rate: 65.0 Mbps, retry: 45, lost: 3, rtt: 35.1ms"
    metric = WifiAnalyzer.parse_line(line)
    assert metric is not None
    assert metric.frequency_mhz == 2412
    assert metric.band == "2.4 GHz"
    assert metric.channel == 1
    assert metric.signal_dbm == -78
    assert metric.quality_rating == "Poor"
    assert metric.lost_frames == 3
    assert metric.retry_count == 45


def test_wifi_analyzer_summary_and_diagnosis():
    """Test batch analysis of multiple Wi-Fi samples."""
    log_content = """
[11:00:01] [Info] Starting aa-supervisor
[11:00:02] [WifiLink] freq=5200 signal=-50 dBm rx_rate=433.3 Mbps tx_rate=433.3 Mbps lost=0 retry=1 rtt=10.0ms
[11:00:05] [WifiLink] freq=5200 signal=-48 dBm rx_rate=433.3 Mbps tx_rate=433.3 Mbps lost=0 retry=0 rtt=9.8ms
[11:00:10] [WifiLink] freq=5200 signal=-52 dBm rx_rate=433.3 Mbps tx_rate=433.3 Mbps lost=0 retry=2 rtt=11.2ms
"""
    diag = WifiAnalyzer.analyze_log_content(log_content)
    assert diag["detected"] is True
    assert diag["count"] == 3
    assert diag["total_lost_frames"] == 0
    assert diag["total_retries"] == 3
    assert "5 GHz Band" in diag["diagnosis"]
    assert "Clean RF link" in diag["diagnosis"]
