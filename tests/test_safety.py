# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Unit tests for automotive safety workflows and BusyBox df parser."""

import os
import tempfile
import sys
from pathlib import Path

# Add windows directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "windows"))

from entrynav2.safety import SafetyWorkflow
from entrynav2.releases import ReleaseManager


def test_parse_df_single_line():
    """Test standard single-line df output from Linux/BusyBox."""
    df_output = """Filesystem           1k-blocks      Used Available Use% Mounted on
/dev/root              1928380   1234567    693813  64% /
tmpfs                    65536         0     65536   0% /tmp
"""
    free_kb = SafetyWorkflow.parse_df_free_kb(df_output)
    assert free_kb == 693813


def test_parse_df_wrapped_line():
    """Test wrapped BusyBox df output where filesystem name is on its own line."""
    df_output = """Filesystem           1k-blocks      Used Available Use% Mounted on
/dev/block/bootdevice/by-name/system
                       1928380   1234567    693813  64% /
"""
    free_kb = SafetyWorkflow.parse_df_free_kb(df_output)
    assert free_kb == 693813


def test_parse_df_low_space():
    """Test space check with low flash storage (< 16 MB)."""
    df_output = """Filesystem           1k-blocks      Used Available Use% Mounted on
/dev/root              1928380   1920000      8380  99% /
"""
    free_kb = SafetyWorkflow.parse_df_free_kb(df_output)
    assert free_kb == 8380
    assert free_kb < 16384  # Less than 16 MB requirement


def test_sha256_calculation_and_verification():
    """Test SHA-256 computation and matching."""
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(b"EntryNav2 Test Payload 2026")
        temp_path = f.name

    try:
        calculated = ReleaseManager.calculate_sha256(temp_path)
        assert len(calculated) == 64
        assert ReleaseManager.verify_sha256(temp_path, calculated)
        assert not ReleaseManager.verify_sha256(temp_path, "0" * 64)
    finally:
        os.remove(temp_path)
