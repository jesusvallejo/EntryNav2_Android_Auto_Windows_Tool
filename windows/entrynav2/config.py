# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""iDrive configuration flags and vehicle profile manager."""

from .transport import SSHClientWrapper

SUPPORTED_FLAGS = {
    "autostart": "Auto-start Android Auto automatically with iDrive",
    "usb": "Force USB Cable connection instead of Wireless",
    "entry-direct": "Direct launch into Android Auto (skip sub-menu)",
    "kombi-off": "Disable Turn-by-Turn guidance on instrument cluster / HUD",
    "kombi-single-maneuver": "Cluster single-maneuver mode (for clusters that reject full route graphs)",
    "gps-telephone": "Use phone's internal GPS instead of car's GPS",
    "maintenance": "Enable diagnostic maintenance logging (/var/local/data/AA/maintenance)",
}


class CarConfigManager:
    """Manages iDrive feature flags and vehicle metadata on the car with disconnect protection."""

    def __init__(self, ssh: SSHClientWrapper, log_callback=None):
        self.ssh = ssh
        self.logger = ssh.logger
        self.log_cb = log_callback or (lambda msg: None)

    def log(self, tag: str, msg: str):
        self.logger.log(tag, msg)
        self.log_cb(msg)

    def read_flags(self) -> tuple[bool, dict[str, bool]]:
        """Read configuration flags from car. Returns (False, {}) if car is unreachable."""
        self.log("INFO", "Reading current configuration flags from car (/var/local/data/AA)...")
        code, out, err = self.ssh.run_command("ls /var/local/data/AA 2>/dev/null")

        if code != 0:
            self.log("WARN", f"Could not read flags: Head unit unreachable ({err.strip() or 'No response'}).")
            return False, {}

        existing_files = set(out.strip().split())
        flags = {flag: (flag in existing_files) for flag in SUPPORTED_FLAGS}
        self.log("OK", "✅ Configuration flags synchronized from car.")
        return True, flags

    def save_flags(self, flags: dict[str, bool]) -> tuple[bool, str]:
        """Save configuration flags to car."""
        self.log("INFO", "Saving configuration flags to car (/var/local/data/AA)...")
        cmds = ["mkdir -p /var/local/data/AA"]

        for flag, enabled in flags.items():
            if flag not in SUPPORTED_FLAGS:
                continue
            if enabled:
                cmds.append(f"touch /var/local/data/AA/{flag}")
            else:
                cmds.append(f"rm -f /var/local/data/AA/{flag}")

        full_cmd = " && ".join(cmds)
        code, out, err = self.ssh.run_command(full_cmd)

        if code == 0:
            self.log("OK", "✅ Configuration flags successfully saved to car.")
            return True, "Flags saved"
        else:
            self.log("ERROR", f"❌ Failed to save flags: {err.strip()}")
            return False, err.strip()

    def read_vehicle_profile(self) -> tuple[bool, dict[str, str]]:
        """Read vehicle model and year from /var/local/data/AA/vehicle."""
        code, out, err = self.ssh.run_command("cat /var/local/data/AA/vehicle 2>/dev/null")
        if code != 0:
            return False, {"model": "", "year": ""}

        profile = {"model": "", "year": ""}
        for line in out.splitlines():
            if "model=" in line:
                profile["model"] = line.split("=")[-1].strip()
            elif "year=" in line:
                profile["year"] = line.split("=")[-1].strip()
        return True, profile

    def save_vehicle_profile(self, model: str, year: str) -> tuple[bool, str]:
        """Save vehicle profile metadata."""
        m_val = model.strip() or "iDrive"
        y_val = year.strip() or "2019"
        cmd = f"mkdir -p /var/local/data/AA && printf 'model={m_val}\\nyear={y_val}\\n' > /var/local/data/AA/vehicle"
        code, out, err = self.ssh.run_command(cmd)
        if code == 0:
            self.log("OK", f"✅ Vehicle profile saved (Model: {m_val}, Year: {y_val}).")
            return True, "Profile saved"
        return False, err.strip()

    def reset_app_guard(self) -> tuple[bool, str]:
        """Reset crash counters and disable flags on head unit."""
        self.log("INFO", "Resetting app-guard crash counters and disable flags on car...")
        code, out, err = self.ssh.run_command("rm -f /var/local/data/AA/app.disable /var/local/data/AA/app-guard")
        if code == 0:
            self.log("OK", "✅ App guard cleared.")
            return True, "App guard reset"
        return False, err.strip()
