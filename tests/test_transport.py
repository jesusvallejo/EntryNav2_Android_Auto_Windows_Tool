# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Unit tests for event logger and transport safety."""

import sys
from pathlib import Path

# Add windows directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "windows"))

from entrynav2.transport import EventLogger, SSHClientWrapper


def test_event_logger_broadcast():
    """Verify EventLogger formats lines and dispatches to listeners."""
    logger = EventLogger()
    captured = []

    def callback(line):
        captured.append(line)

    logger.add_listener(callback)
    logger.log("CMD >>", 'ssh root@169.254.1.0 "uptime"')
    logger.log("HU <<", "load average: 0.12")
    logger.remove_listener(callback)
    logger.log("INFO", "Ignored line")

    assert len(captured) == 2
    assert "[CMD >>]" in captured[0]
    assert "uptime" in captured[0]
    assert "[HU <<]" in captured[1]


def test_socket_connection_refused():
    """Verify test_connection accurately reports connection failure on unused port."""
    client = SSHClientWrapper(host="127.0.0.1", port=49151)
    reachable, msg = client.test_connection(timeout=0.5)
    assert reachable is False
    assert "refused" in msg.lower() or "timed out" in msg.lower() or "failed" in msg.lower()
