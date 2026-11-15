# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Unit tests for configuration flags and disconnect safety."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add windows directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "windows"))

from entrynav2.config import CarConfigManager, SUPPORTED_FLAGS
from entrynav2.transport import SSHClientWrapper


def test_supported_flags_list():
    """Verify all 7 supported iDrive feature flags are registered."""
    expected = {
        "autostart", "usb", "entry-direct", "kombi-off",
        "kombi-single-maneuver", "gps-telephone", "maintenance"
    }
    assert set(SUPPORTED_FLAGS.keys()) == expected


def test_read_flags_success():
    """Verify flags parsing when car returns ls output."""
    mock_ssh = MagicMock(spec=SSHClientWrapper)
    mock_ssh.logger = MagicMock()
    mock_ssh.run_command.return_value = (0, "autostart\nkombi-off\nmaintenance", "")

    cfg = CarConfigManager(mock_ssh)
    success, flags = cfg.read_flags()

    assert success is True
    assert flags["autostart"] is True
    assert flags["kombi-off"] is True
    assert flags["maintenance"] is True
    assert flags["usb"] is False
    assert flags["gps-telephone"] is False


def test_read_flags_disconnect_preserves_state():
    """Verify disconnect (returncode != 0) does NOT wipe flags."""
    mock_ssh = MagicMock(spec=SSHClientWrapper)
    mock_ssh.logger = MagicMock()
    mock_ssh.run_command.return_value = (255, "", "Host unreachable")

    cfg = CarConfigManager(mock_ssh)
    success, flags = cfg.read_flags()

    assert success is False
    assert flags == {}  # Empty dict indicates failure; caller must not overwrite UI state
