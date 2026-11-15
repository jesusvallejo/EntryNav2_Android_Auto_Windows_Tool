# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Release catalogue, GitHub release management, and SHA-256 integrity verification."""

import hashlib
import json
import urllib.request
from pathlib import Path

DEFAULT_REPO = "Jiraiya43/EntryNav2-Android-Auto"

# Known release hashes for cryptographic version identification
KNOWN_RELEASE_MD5S = {
    # entry-aad binary MD5 -> Version Tag
    "78661be323ab42622004b91083ebbbdc": "v0.12.1-rc.4",
    "dfb0ebefe6e2a85041f6bb47646655eb": "v0.12.1-rc.3",
    "b6c72ae9f4c144a4ad27b41944a05e8c": "v0.12.1-rc.2",
    "f17b95fa8653992442daac05d03ff605": "v0.12.1-rc.1",
    "b983052e63affecce7ff8c83594b2b6c": "v0.12.0",
}

BUILTIN_RELEASES = [
    {
        "tag": "v0.12.1-rc.4",
        "name": "EntryNav2 (EntryEvo) Android Auto 0.12.1-rc.4",
        "prerelease": True,
        "published_at": "2026-11-14",
        "tar_name": "entrynav2-android-auto-0.12.1-rc.4-armhf.tar",
        "tar_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.4/entrynav2-android-auto-0.12.1-rc.4-armhf.tar",
        "tar_size": 634880,
        "sha_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.4/entrynav2-android-auto-0.12.1-rc.4-armhf.tar.sha256",
        "sha_name": "entrynav2-android-auto-0.12.1-rc.4-armhf.tar.sha256",
        "sha_hash": "a445a9697d1668c274dea598ba18cdfc2b13746534ac5675e96723b842357ff0",
        "body": "Pre-release v0.12.1-rc.4 (Media double-press fix on older controller)",
    },
    {
        "tag": "v0.12.1-rc.3",
        "name": "EntryNav2 (EntryEvo) Android Auto 0.12.1-rc.3",
        "prerelease": True,
        "published_at": "2026-11-14",
        "tar_name": "entrynav2-android-auto-0.12.1-rc.3-armhf.tar",
        "tar_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.3/entrynav2-android-auto-0.12.1-rc.3-armhf.tar",
        "tar_size": 26603520,
        "sha_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.3/entrynav2-android-auto-0.12.1-rc.3-armhf.tar.sha256",
        "sha_name": "entrynav2-android-auto-0.12.1-rc.3-armhf.tar.sha256",
        "sha_hash": "8fa11fc02460e164432adb0c46e1f91f936ed467ccb78219b43456e7f03ba5fa",
        "body": "Pre-release v0.12.1-rc.3",
    },
    {
        "tag": "v0.12.1-rc.2",
        "name": "EntryNav2 (EntryEvo) Android Auto 0.12.1-rc.2",
        "prerelease": True,
        "published_at": "2026-11-14",
        "tar_name": "entrynav2-android-auto-0.12.1-rc.2-armhf.tar",
        "tar_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.2/entrynav2-android-auto-0.12.1-rc.2-armhf.tar",
        "tar_size": 26603520,
        "sha_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.2/entrynav2-android-auto-0.12.1-rc.2-armhf.tar.sha256",
        "sha_name": "entrynav2-android-auto-0.12.1-rc.2-armhf.tar.sha256",
        "sha_hash": "98073b5bb51fe8f9b023532688abf1ee1664fa8befaa2f6f50c6bc22f441e876",
        "body": "Pre-release v0.12.1-rc.2",
    },
    {
        "tag": "v0.12.1-rc.1",
        "name": "EntryNav2 (EntryEvo) Android Auto 0.12.1-rc.1",
        "prerelease": True,
        "published_at": "2026-11-14",
        "tar_name": "entrynav2-android-auto-0.12.1-rc.1-armhf.tar",
        "tar_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.1/entrynav2-android-auto-0.12.1-rc.1-armhf.tar",
        "tar_size": 26603520,
        "sha_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.1-rc.1/entrynav2-android-auto-0.12.1-rc.1-armhf.tar.sha256",
        "sha_name": "entrynav2-android-auto-0.12.1-rc.1-armhf.tar.sha256",
        "sha_hash": "8e7762e12c4bcde93ceef565378b14c088c3238f495372b18262d22fd27c0d46",
        "body": "Pre-release v0.12.1-rc.1",
    },
    {
        "tag": "v0.12.0",
        "name": "EntryNav2 (EntryEvo) Android Auto 0.12.0 (Stable)",
        "prerelease": False,
        "published_at": "2026-11-13",
        "tar_name": "entrynav2-android-auto-0.12.0-armhf.tar",
        "tar_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.0/entrynav2-android-auto-0.12.0-armhf.tar",
        "tar_size": 26593280,
        "sha_url": "https://github.com/Jiraiya43/EntryNav2-Android-Auto/releases/download/v0.12.0/entrynav2-android-auto-0.12.0-armhf.tar.sha256",
        "sha_name": "entrynav2-android-auto-0.12.0-armhf.tar.sha256",
        "sha_hash": "5dba7ec176b101b04750bf6e80712141ed91a85ea328ecc4a3d2056c483bf005",
        "body": "Stable release v0.12.0",
    },
]


class ReleaseManager:
    """Manages release discovery, downloading, and checksum verification."""

    @staticmethod
    def get_releases(repo: str = DEFAULT_REPO) -> list[dict]:
        """Fetch list of releases from GitHub API with fallback to verified offline catalogue."""
        url = f"https://api.github.com/repos/{repo}/releases"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EntryNav2-Windows-Tool/2.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            releases = []
            for r in data:
                tar_asset = None
                sha_asset = None
                for a in r.get("assets", []):
                    name = a.get("name", "")
                    if name.endswith(".tar"):
                        tar_asset = a
                    elif name.endswith(".tar.sha256") or name.endswith(".sha256"):
                        sha_asset = a

                if tar_asset:
                    pub = r.get("published_at") or r.get("created_at") or ""
                    tag = r.get("tag_name")
                    # Check if hash is known in builtin catalogue
                    known_hash = None
                    for b in BUILTIN_RELEASES:
                        if b["tag"] == tag and b.get("sha_hash"):
                            known_hash = b["sha_hash"]
                            break

                    releases.append({
                        "tag": tag,
                        "name": r.get("name") or tag,
                        "prerelease": r.get("prerelease", False),
                        "published_at": pub[:10] if len(pub) >= 10 else pub,
                        "tar_name": tar_asset["name"],
                        "tar_url": tar_asset["browser_download_url"],
                        "tar_size": tar_asset.get("size", 0),
                        "sha_url": sha_asset["browser_download_url"] if sha_asset else None,
                        "sha_name": sha_asset["name"] if sha_asset else None,
                        "sha_hash": known_hash,
                        "body": r.get("body", "")
                    })
            if releases:
                return releases
        except Exception:
            pass
        return list(BUILTIN_RELEASES)

    @staticmethod
    def download_file(url: str, dest_path: str, progress_cb=None) -> bool:
        """Download file with progress reporting (downloaded bytes, total bytes)."""
        req = urllib.request.Request(url, headers={"User-Agent": "EntryNav2-Windows-Tool/2.0"})
        with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, "wb") as out_file:
            total_size = int(response.info().get("Content-Length", 0))
            downloaded = 0
            chunk_size = 65536
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if progress_cb and total_size > 0:
                    progress_cb(downloaded, total_size)
        return True

    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        """Calculate SHA-256 digest of a local file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest().lower()

    @staticmethod
    def verify_sha256(file_path: str, expected_hash: str) -> bool:
        """Check if file matches expected SHA-256."""
        if not expected_hash:
            return False
        calculated = ReleaseManager.calculate_sha256(file_path)
        return calculated.strip() == expected_hash.strip().lower()
