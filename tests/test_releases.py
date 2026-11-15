# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Unit tests for release management and offline catalogue."""

import sys
from pathlib import Path

# Add windows directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "windows"))

from entrynav2.releases import ReleaseManager, BUILTIN_RELEASES, KNOWN_RELEASE_MD5S


def test_builtin_releases_completeness():
    """Verify built-in release catalogue contains mandatory releases."""
    tags = [r["tag"] for r in BUILTIN_RELEASES]
    assert "v0.12.1-rc.4" in tags
    assert "v0.12.1-rc.3" in tags
    assert "v0.12.0" in tags

    for r in BUILTIN_RELEASES:
        assert r["tag"].startswith("v0.")
        assert r["tar_name"].endswith(".tar")
        assert len(r["sha_hash"]) == 64


def test_known_release_md5_mapping():
    """Verify cryptographic MD5 mapping identifies releases."""
    assert KNOWN_RELEASE_MD5S["78661be323ab42622004b91083ebbbdc"] == "v0.12.1-rc.4"
    assert KNOWN_RELEASE_MD5S["b983052e63affecce7ff8c83594b2b6c"] == "v0.12.0"
