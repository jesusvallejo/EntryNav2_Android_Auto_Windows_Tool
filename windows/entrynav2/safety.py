# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Automotive safety workflows, flash integrity checks, and automated rollback protection."""

import os
import re
import tarfile
import time
from datetime import datetime
from pathlib import Path

from .releases import ReleaseManager, KNOWN_RELEASE_MD5S
from .transport import SSHClientWrapper


class SafetyWorkflow:
    """Implements strict automotive safety standards and flash rollback mechanisms."""

    def __init__(self, ssh: SSHClientWrapper, log_callback=None):
        self.ssh = ssh
        self.logger = ssh.logger
        self.log_cb = log_callback or (lambda msg: None)

    def log(self, tag: str, msg: str):
        self.logger.log(tag, msg)
        self.log_cb(f"[{datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}")

    @staticmethod
    def parse_df_free_kb(df_output: str) -> int:
        """Parse BusyBox df output robustly, handling single-line and wrapped device names."""
        for line in df_output.splitlines():
            # Match standard df row ending with ' /'
            m = re.search(r'(\d+)\s+\d+%\s+/\s*$', line.strip())
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    pass
        # Fallback: token scan
        tokens = df_output.strip().split()
        for i, t in enumerate(tokens):
            if t == "/" and i >= 3:
                try:
                    return int(tokens[i - 2])
                except ValueError:
                    pass
        return 0

    def get_installed_version_info(self) -> dict:
        """Retrieve complete information and cryptographic ID of installed Android Auto."""
        self.log("INFO", "Querying BMW EntryNav2 for installed Android Auto version...")
        info = {
            "connected": False,
            "installed": False,
            "version": "Offline / Unreachable",
            "hu_firmware": "Unknown",
            "kernel": "",
            "entry_aad_md5": "",
            "aa_supervisor_md5": "",
            "lib_entry_aad_md5": "",
            "running_pids": "",
            "vehicle_model": "",
            "vehicle_year": "",
            "detection_method": "None",
            "raw_output": ""
        }

        # 1. Car connectivity & firmware ID (/etc/version)
        code_v, out_v, err_v = self.ssh.run_command("head -n 1 /etc/version")
        if code_v != 0 or not out_v.strip():
            info["raw_output"] = err_v.strip() or "No response from car (offline / unreachable)"
            self.log("ERROR", f"Could not connect to car head unit: {info['raw_output']}")
            return info

        info["connected"] = True
        info["hu_firmware"] = out_v.strip()
        info["version"] = "Unknown"
        self.log("OK", f"Car iDrive OS Firmware: {info['hu_firmware']}")

        # 2. Check if Android Auto binaries exist on flash
        code_chk, out_chk, _ = self.ssh.run_command("test -f /opt/aa/entry-aad && echo EXISTS || echo NOT_INSTALLED")
        if "EXISTS" not in out_chk:
            code_plg, out_plg, _ = self.ssh.run_command(
                "test -f /opt/hmi/data/ro/Plugins/EntryAad/libEntryAad.so && echo EXISTS || echo NOT_INSTALLED"
            )
            if "EXISTS" not in out_plg:
                info["version"] = "Not Installed"
                info["detection_method"] = "Flash inspection (/opt/aa empty)"
                self.log("WARN", "Android Auto is NOT currently installed on this head unit.")
                return info

        info["installed"] = True

        # 3. Check for dedicated version stamp files
        code_stamp, out_stamp, _ = self.ssh.run_command("cat /opt/aa/.version /var/local/data/AA/installed_version 2>/dev/null")
        if code_stamp == 0 and out_stamp.strip():
            for line in out_stamp.splitlines():
                if "tag=" in line or "version=" in line:
                    val = line.split("=")[-1].strip()
                    if val and info["version"] == "Unknown":
                        info["version"] = val if val.startswith("v") else f"v{val}"
                        info["detection_method"] = "Version stamp file (/opt/aa/.version)"

        # 4. Compute cryptographic MD5 checksums of installed binaries
        cmd_md5 = "md5sum /opt/aa/entry-aad /opt/aa/aa-supervisor /opt/hmi/data/ro/Plugins/EntryAad/libEntryAad.so 2>/dev/null"
        code_md5, out_md5, _ = self.ssh.run_command(cmd_md5)
        if code_md5 == 0 and out_md5.strip():
            for line in out_md5.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    h, f = parts[0].lower(), parts[1]
                    if "entry-aad" in f and "libEntryAad" not in f:
                        info["entry_aad_md5"] = h
                        if h in KNOWN_RELEASE_MD5S:
                            info["version"] = KNOWN_RELEASE_MD5S[h]
                            info["detection_method"] = f"Cryptographic MD5 Match ({KNOWN_RELEASE_MD5S[h]})"
                    elif "aa-supervisor" in f:
                        info["aa_supervisor_md5"] = h
                    elif "libEntryAad.so" in f:
                        info["lib_entry_aad_md5"] = h

        # 5. Fallback: Parse binary version strings inside entry-aad
        if info["version"] == "Unknown":
            cmd_str = r"strings /opt/aa/entry-aad 2>/dev/null | grep -E '^[0-9]+\.[0-9]+' | head -n 5"
            code_str, out_str, _ = self.ssh.run_command(cmd_str)
            if code_str == 0 and out_str:
                m = re.findall(r'(?<![\d\.])0\.[1-9][0-9]*\.[0-9]+(?:-rc\.[0-9]+)?(?![\d\.])', out_str)
                if m:
                    ver_tag = m[0]
                    info["version"] = f"v{ver_tag}" if not ver_tag.startswith("v") else ver_tag
                    info["detection_method"] = "Binary internal version string"

        # 6. Check running processes
        code_p, out_p, _ = self.ssh.run_command("pidof aa-supervisor entry-aad")
        info["running_pids"] = out_p.strip()

        # 7. Check vehicle profile
        code_veh, out_veh, _ = self.ssh.run_command("cat /var/local/data/AA/vehicle 2>/dev/null")
        if code_veh == 0 and out_veh.strip():
            for line in out_veh.splitlines():
                if "model=" in line:
                    info["vehicle_model"] = line.split("=")[-1].strip()
                elif "year=" in line:
                    info["vehicle_year"] = line.split("=")[-1].strip()

        # Log summary
        self.log("STEP", "==========================================================")
        if info["installed"]:
            self.log("OK", f"📦 ANDROID AUTO INSTALLED VERSION: {info['version']}")
            self.log("INFO", f"   • Detection Source:   {info['detection_method']}")
            if info["entry_aad_md5"]:
                self.log("INFO", f"   • entry-aad MD5:      {info['entry_aad_md5']}")
            if info["aa_supervisor_md5"]:
                self.log("INFO", f"   • aa-supervisor MD5:  {info['aa_supervisor_md5']}")
            if info["lib_entry_aad_md5"]:
                self.log("INFO", f"   • libEntryAad.so MD5: {info['lib_entry_aad_md5']}")
        else:
            self.log("WARN", "📦 ANDROID AUTO STATUS: NOT INSTALLED (/opt/aa empty)")
        self.log("INFO", f"   • Car iDrive Firmware: {info['hu_firmware']}")
        self.log("INFO", f"   • Process State:      {'Active (PID ' + info['running_pids'] + ')' if info['running_pids'] else 'Stopped'}")
        if info["vehicle_model"] or info["vehicle_year"]:
            self.log("INFO", f"   • Vehicle Profile:    Model={info['vehicle_model'] or 'iDrive'}, Year={info['vehicle_year'] or '2019'}")
        self.log("STEP", "==========================================================")

        return info

    def run_preflight_checks(self, auto_stop_aa: bool = True) -> dict:
        """Check car connectivity, OS version, disk space, and clean process termination."""
        results = {"connected": False, "version": "", "free_kb": 0, "is_running": False, "error": ""}
        self.log("INFO", "Testing SSH connection to BMW EntryNav2...")
        code, out, err = self.ssh.run_command("head -n 1 /etc/version")
        if code != 0:
            results["error"] = f"Failed to connect to car: {err.strip() or 'No response from 169.254.1.0:22'}"
            self.log("ERROR", f"❌ {results['error']}")
            return results

        results["connected"] = True
        results["version"] = out.strip()
        self.log("OK", f"✅ Connected to car. iDrive firmware version: {results['version']}")

        # Check free disk space on root /
        self.log("INFO", "Checking root partition space (df -k /)...")
        code, out, _ = self.ssh.run_command("df -k /")
        results["free_kb"] = self.parse_df_free_kb(out)

        free_mb = results["free_kb"] / 1024
        self.log("INFO", f"Available space on /: {results['free_kb']} KB ({free_mb:.1f} MB)")
        if results["free_kb"] < 16384:
            results["error"] = f"Insufficient disk space on /: {results['free_kb']} KB available, need at least 16384 KB (16 MB)."
            self.log("ERROR", f"❌ {results['error']}")
            return results
        self.log("OK", f"✅ Sufficient disk space verified ({free_mb:.1f} MB >= 16 MB).")

        # Check if Android Auto is running
        self.log("INFO", "Checking running processes (pidof aa-supervisor entry-aad)...")
        code, out, _ = self.ssh.run_command("pidof aa-supervisor entry-aad")
        if out.strip():
            results["is_running"] = True
            self.log("WARN", f"⚠️ Android Auto is currently running (PID {out.strip()}).")
            if auto_stop_aa:
                self.log("INFO", "Safely stopping active Android Auto processes before proceeding...")
                # Graceful SIGTERM first
                self.ssh.run_command("killall aa-supervisor entry-aad 2>/dev/null")
                time.sleep(1.0)
                code_verify, out_verify, _ = self.ssh.run_command("pidof aa-supervisor entry-aad")
                if out_verify.strip():
                    # Force SIGKILL if needed
                    self.ssh.run_command("killall -9 aa-supervisor entry-aad 2>/dev/null")
                    time.sleep(0.5)

                code_final, out_final, _ = self.ssh.run_command("pidof aa-supervisor entry-aad")
                if out_final.strip():
                    self.log("WARN", f"⚠️ Processes still active (PID {out_final.strip()}). Please stop from iDrive.")
                else:
                    self.log("OK", "✅ Android Auto processes stopped cleanly.")
                    results["is_running"] = False
        else:
            self.log("OK", "✅ Android Auto is not running.")

        return results

    def verify_and_install(
        self,
        local_tar_path: str,
        expected_sha256: str,
        vehicle_model: str = "",
        vehicle_year: str = ""
    ) -> bool:
        """Execute full 8-step safe installation with pre-flash snapshot and automated rollback."""
        tar_name = Path(local_tar_path).name
        self.log("STEP", "==========================================================")
        self.log("STEP", "🚀 STARTING ENTRYNAV2 ANDROID AUTO UPDATE / INSTALL")
        self.log("STEP", "==========================================================")

        # 1. Local SHA-256 check
        self.log("STEP", "[Step 1/8] Verifying local archive SHA-256 integrity...")
        calculated_sha = ReleaseManager.calculate_sha256(local_tar_path)
        self.log("INFO", f"Expected SHA-256:   {expected_sha256}")
        self.log("INFO", f"Calculated SHA-256: {calculated_sha}")
        if calculated_sha != expected_sha256.lower().strip():
            self.log("ERROR", "❌ SHA-256 verification failed! Corrupted or altered archive. Aborting.")
            return False
        self.log("OK", "✅ Local SHA-256 matches perfectly.")

        # Determine archive folder name
        archive_folder = ""
        try:
            with tarfile.open(local_tar_path, "r:*") as tf:
                members = tf.getnames()
                if members:
                    archive_folder = members[0].split("/")[0]
        except Exception:
            pass

        if not archive_folder:
            m = re.search(r"(?:entrynav2-android-auto|entry-aad)-([0-9a-zA-Z\.\-]+)-armhf\.tar", tar_name)
            if not m:
                m = re.search(r"entrynav2-android-auto-([0-9a-zA-Z\.\-]+)\.tar", tar_name)
            v_str = m.group(1) if m else "current"
            folder_prefix = "entrynav2-android-auto" if "entrynav2" in tar_name else "entry-aad"
            archive_folder = f"{folder_prefix}-{v_str}"

        extracted_folder = f"/tmp/{archive_folder}"
        self.log("INFO", f"Target staging folder on head unit: {extracted_folder}")

        # 2. Pre-flight checks on car
        self.log("STEP", "[Step 2/8] Performing pre-flight car checks (Engine running)...")
        pre = self.run_preflight_checks(auto_stop_aa=True)
        if not pre["connected"] or pre["error"]:
            return False

        # 3. Upload to car RAM-disk /tmp/
        self.log("STEP", f"[Step 3/8] Uploading {tar_name} to car RAM-disk /tmp/...")
        code, out, err = self.ssh.scp_upload(local_tar_path, "/tmp/")
        if code != 0:
            self.log("ERROR", f"❌ Upload to RAM-disk failed: {err}")
            return False
        self.log("OK", "✅ Upload to RAM-disk /tmp/ complete.")

        # Dynamically inspect archive contents on the car to guarantee 100% accurate staging folder
        code_tar, out_tar, _ = self.ssh.run_command(f"tar -tf /tmp/{tar_name} 2>/dev/null | head -n 1 | cut -d/ -f1")
        if code_tar == 0 and out_tar.strip():
            archive_folder = out_tar.strip()
            extracted_folder = f"/tmp/{archive_folder}"
            self.log("INFO", f"Dynamically resolved staging folder from archive: {archive_folder}")

        # 4. Extract in /tmp and verify MD5SUMS
        self.log("STEP", "[Step 4/8] Extracting archive and checking MD5 checksums on car...")
        unpack_cmd = f"cd /tmp && rm -rf {archive_folder} && tar -xvf {tar_name} && cd {archive_folder} && md5sum -c MD5SUMS"
        code, out, err = self.ssh.run_command(unpack_cmd, timeout=60)
        if code != 0 or "FAILED" in out:
            self.log("ERROR", "❌ MD5SUMS check failed on car! Files in /tmp are corrupted.")
            return False
        self.log("OK", "✅ All files in archive verified intact via MD5SUMS.")

        # 5. Dynamic Linker & Symbol Resolution Check
        self.log("STEP", "[Step 5/8] Running dynamic linker check (verifying shared libraries & symbols)...")
        linker_cmd = f"""
export L=/usr/local/lib:/opt/hmi/lib:/usr/lib:/lib
cd {extracted_folder}
for f in opt/aa/entry-aad opt/aa/aa-supervisor opt/hmi/data/ro/Plugins/EntryAad/libEntryAad.so; do
    if [ -f "$f" ]; then
        echo "Checking $f..."
        LD_TRACE_LOADED_OBJECTS=1 LD_WARN=yes LD_BIND_NOW=yes LD_LIBRARY_PATH=$L /lib/ld-linux-armhf.so.3 ./$f 2>&1 |
            grep -E 'not found|undefined symbol|not defined in file'
    fi
done
"""
        code, out, err = self.ssh.run_command(linker_cmd, timeout=60)
        if out.strip() and ("not found" in out or "undefined symbol" in out or "not defined in file" in out):
            self.log("ERROR", f"❌ Dynamic linker reported unresolved symbols or missing libraries:\n{out}")
            self.log("ERROR", "❌ Car firmware does not provide required symbols. Aborting to protect system.")
            return False
        self.log("OK", "✅ Dynamic linker resolution passed (no missing symbols or libraries).")

        # 6. Rehearsal Compatibility Check (aa-supervisor --compat)
        self.log("STEP", "[Step 6/8] Executing non-destructive compatibility test (aa-supervisor --compat)...")
        compat_cmd = f"""
cd {extracted_folder} && \\
export L=/usr/local/lib:/opt/hmi/lib:/usr/lib:/lib && \\
export LD_LIBRARY_PATH=$L && \\
export XDG_RUNTIME_DIR=/run/system/0 && \\
export WAYLAND_DISPLAY=wayland-0 && \\
export HOME=/tmp && \\
./opt/aa/aa-supervisor --compat 2>&1
"""
        code, out, err = self.ssh.run_command(compat_cmd, timeout=75)
        if "@block" in out:
            self.log("ERROR", "❌ Compatibility check detected blocking issues! Cannot install on this unit.")
            return False
        if "@warn" in out:
            self.log("WARN", "⚠️ Compatibility check reported non-fatal warnings (safe to proceed).")
        self.log("OK", "✅ Compatibility check passed successfully.")

        # 7. Pre-flash snapshot backup & Atomic Flash Installation
        self.log("STEP", "[Step 7/8] Creating pre-flash snapshot backup and installing to flash...")
        backup_cmd = "rm -rf /tmp/aa_backup && mkdir -p /tmp/aa_backup/opt_aa /tmp/aa_backup/plugin && cp -r /opt/aa/* /tmp/aa_backup/opt_aa/ 2>/dev/null; cp -r /opt/hmi/data/ro/Plugins/EntryAad/* /tmp/aa_backup/plugin/ 2>/dev/null; true"
        self.ssh.run_command(backup_cmd)
        self.log("INFO", "Pre-flash backup snapshot created in /tmp/aa_backup.")

        install_cmd = f"""
cd {extracted_folder} && \\
echo "Remounting / rw..." && \\
mount -o remount,rw / && \\
mkdir -p /opt/hmi/data/ro/Plugins/EntryAad /opt/aa /var/local/data/AA && \\
rm -f /opt/hmi/data/ro/Plugins/EntryAad/* /opt/aa/* && \\
echo "Copying plugins and binaries..." && \\
cp -v opt/hmi/data/ro/Plugins/EntryAad/* /opt/hmi/data/ro/Plugins/EntryAad/ && \\
cp -v opt/aa/* /opt/aa/ && \\
chmod 755 /opt/aa/entry-aad /opt/aa/aa-supervisor /opt/hmi/data/ro/Plugins/EntryAad/libEntryAad.so && \\
touch /opt/aa/.installed-by-entryaad /opt/hmi/data/ro/Plugins/EntryAad/.installed-by-entryaad && \\
printf "version={archive_folder}\\ntag={archive_folder}\\nsha256={expected_sha256}\\ninstalled_at=$(date -Iseconds 2>/dev/null || date)\\n" > /opt/aa/.version && \\
cp /opt/aa/.version /var/local/data/AA/installed_version && \\
echo "Syncing flash..." && \\
sync && \\
(mount -o remount,ro / 2>/dev/null || true) && \\
echo "Flash write completed."
"""
        code, out, err = self.ssh.run_command(install_cmd, timeout=90)
        self.ssh.run_command("sync; mount -o remount,ro / 2>/dev/null || true")

        if code != 0:
            self.log("ERROR", f"❌ Flash install copy failed: {err}")
            self._attempt_rollback()
            return False
        self.log("OK", "✅ Flash files copied, version stamped, and synced.")

        # 8. Post-install MD5 verification on Flash & Automated Rollback
        self.log("STEP", "[Step 8/8] Verifying installed files on flash against MD5SUMS...")
        post_verify_cmd = f"cd / && md5sum -c {extracted_folder}/MD5SUMS"
        code, out, err = self.ssh.run_command(post_verify_cmd, timeout=60)
        if code != 0 or "FAILED" in out:
            self.log("ERROR", "❌ Post-installation MD5 check failed on flash! Files may be corrupted.")
            self._attempt_rollback()
            return False
        self.log("OK", "✅ Flash files verified bit-for-bit identical to release MD5SUMS!")

        # Vehicle model and year configuration
        if vehicle_model or vehicle_year:
            m_val = vehicle_model.strip() or "iDrive"
            y_val = vehicle_year.strip() or "2019"
            self.log("INFO", f"Configuring vehicle profile: model={m_val}, year={y_val}...")
            veh_cmd = f"mkdir -p /var/local/data/AA && printf 'model={m_val}\\nyear={y_val}\\n' > /var/local/data/AA/vehicle"
            self.ssh.run_command(veh_cmd)

        # Cleanup /tmp
        self.log("INFO", "Cleaning up /tmp staging files and snapshot...")
        cleanup_cmd = f"rm -rf {extracted_folder} /tmp/{tar_name} /tmp/aa_backup"
        self.ssh.run_command(cleanup_cmd)

        self.log("STEP", "==========================================================")
        self.log("OK", "🎉 INSTALLATION / UPDATE COMPLETED SUCCESSFULLY!")
        self.log("INFO", f"   Installed Version ID: {archive_folder}")
        self.log("INFO", "   Next steps:")
        self.log("INFO", "   1. Reboot head unit to load new binaries into HmiMain3D.")
        self.log("INFO", "   2. On iDrive screen: Media -> Android Auto -> Start.")
        self.log("STEP", "==========================================================")
        return True

    def _attempt_rollback(self):
        """Restore prior binaries from pre-flash snapshot in case of failure."""
        self.log("WARN", "🔄 Attempting automatic rollback from /tmp/aa_backup...")
        rollback_cmd = """
mount -o remount,rw / && \\
if [ -d /tmp/aa_backup/opt_aa ]; then cp -r /tmp/aa_backup/opt_aa/* /opt/aa/ 2>/dev/null; fi && \\
if [ -d /tmp/aa_backup/plugin ]; then cp -r /tmp/aa_backup/plugin/* /opt/hmi/data/ro/Plugins/EntryAad/ 2>/dev/null; fi && \\
chmod 755 /opt/aa/entry-aad /opt/aa/aa-supervisor /opt/hmi/data/ro/Plugins/EntryAad/libEntryAad.so 2>/dev/null && \\
sync && \\
(mount -o remount,ro / 2>/dev/null || true)
"""
        code, out, err = self.ssh.run_command(rollback_cmd, timeout=30)
        self.ssh.run_command("sync; mount -o remount,ro / 2>/dev/null || true")
        if code == 0:
            self.log("OK", "✅ Rollback completed. Head unit flash restored to prior state.")
        else:
            self.log("ERROR", f"❌ Rollback failed: {err}")
