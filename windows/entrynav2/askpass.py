# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Native askpass credential provider for Windows OpenSSH without heuristic-triggering binary blobs."""

import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

# Plain C# source for transparent, on-the-fly compilation via native Windows csc.exe
CS_SOURCE = r"""using System;
class P {
    static void Main() {
        string p = Environment.GetEnvironmentVariable("ENTRYNAV2_PASSWORD");
        if (!string.IsNullOrEmpty(p)) Console.Write(p);
    }
}
"""


def get_system_csc_path() -> str | None:
    """Find native Microsoft .NET C# compiler present on all Windows 10 and 11 installations."""
    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
    candidates = [
        Path(sys_root) / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe",
        Path(sys_root) / "Microsoft.NET" / "Framework" / "v4.0.30319" / "csc.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def ensure_windows_askpass() -> str | None:
    """Ensure a clean, locally-compiled askpass helper exists in %TEMP% for OpenSSH."""
    if platform.system() != "Windows":
        return None

    temp_dir = Path(tempfile.gettempdir())
    askpass_exe = temp_dir / "entrynav2_askpass.exe"

    if askpass_exe.is_file() and askpass_exe.stat().st_size > 0:
        return str(askpass_exe)

    csc_path = get_system_csc_path()
    if csc_path:
        cs_file = temp_dir / "entrynav2_askpass.cs"
        try:
            cs_file.write_text(CS_SOURCE, encoding="utf-8")
            cmd = [
                csc_path,
                "/nologo",
                "/target:winexe",
                "/optimize+",
                f"/out:{askpass_exe}",
                str(cs_file)
            ]
            res = subprocess.run(cmd, capture_output=True, timeout=10, check=False)
            if res.returncode == 0 and askpass_exe.is_file():
                try:
                    cs_file.unlink(missing_ok=True)
                except Exception:
                    pass
                return str(askpass_exe)
        except Exception:
            pass

    # Secondary fallback: Standalone script runner if csc not available
    cmd_file = temp_dir / "entrynav2_askpass.cmd"
    try:
        cmd_file.write_text("@echo %ENTRYNAV2_PASSWORD%", encoding="utf-8")
    except Exception:
        pass

    return str(askpass_exe) if askpass_exe.is_file() else str(cmd_file)
