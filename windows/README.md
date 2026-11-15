# BMW EntryNav2 Android Auto - Windows Management & Flashing Suite v2.0

A dedicated Windows suite designed specifically for the [EntryNav2-Android-Auto](https://github.com/Jiraiya43/EntryNav2-Android-Auto) project. It provides automated safe updates with rollback protection, one-click autologin root SSH terminal, full command and head unit output transparency, diagnostic log extraction with real-time Wi-Fi link analysis, ENET network adapter diagnostics, and iDrive feature configuration for BMW EntryNav2 (EntryEvo) head units.

---

## 🌟 Key Capabilities

1. **Maximum Execution Transparency (Real-Time Live Streaming)**:
   - **Timestamped Command Logging**: Every single shell command sent over SSH is displayed verbatim:
     `[HH:MM:SS] [CMD >>] ssh root@169.254.1.0 "head -n 1 /etc/version"`
   - **Live Head Unit Output Stream**: Output from the car's Linux kernel and BusyBox environment streams directly to the GUI line-by-line in real time:
     `[HH:MM:SS] [HU <<] 201910092124`
   - **Exit Status Confirmation**: Displays exact return codes and human-readable diagnostic status:
     `[HH:MM:SS] [EXIT] Return code: 0 (Success)`
   - **Real-Time SCP/SFTP Transfer Metrics**: Displays transfer speeds, byte counters, and upload/download durations:
     `[HH:MM:SS] [SCP >>] Uploading entrynav2-android-auto-0.12.1-rc.4-armhf.tar (620.0 KB) -> root@169.254.1.0:/tmp/`
     `[HH:MM:SS] [SCP <<] Upload complete in 1.1s (0.55 MB/s) -> Success (Code 0)`
   - **Session Logging**: Automatically saves a timestamped log to `BMW_Logs\session_YYYYMMDD_HHMMSS.log`.

2. **One-Click Autologin Root SSH Terminal**:
   - Automatically authenticates root access using the known EntryNav2 password `Entry0?Evo!1`.
   - Injects credentials via native Windows OpenSSH or PuTTY with zero manual password typing and zero heuristic-triggering binary blobs.

3. **Automated Safe Update & Flash (With Pre-Flash Snapshot & Rollback)**:
   - **Release Catalogue**: Built-in support for official releases (including `v0.12.1-rc.4`, `v0.12.1-rc.3`, `v0.12.0`), GitHub API release fetching, and local custom `.tar` archives.
   - **Pre-Transfer SHA-256 Check**: Computes and validates the local archive against official `.sha256` digests before touching the car.
   - **Flash Storage Pre-check**: Checks `df -k /` on the head unit with robust multi-line parsing and requires $\ge 16\text{ MB}$ free.
   - **Clean Process Termination**: Sends graceful `SIGTERM` first, waits, and verifies termination before applying `SIGKILL`.
   - **RAM-Disk Transfer**: Uploads strictly to `/tmp/` (tmpfs ramdisk) to eliminate unnecessary flash storage wear.
   - **Remote MD5 Verification**: Checks archive integrity with `md5sum -c MD5SUMS` inside the car's BusyBox environment.
   - **Dynamic Linker & Symbol Check**: Validates shared libraries and symbols with `LD_TRACE_LOADED_OBJECTS=1` before execution.
   - **Rehearsal Compatibility Check**: Runs `aa-supervisor --compat` with full environment (`XDG_RUNTIME_DIR=/run/system/0`, `WAYLAND_DISPLAY=wayland-0`) to detect `@block`, `@warn`, and `@ok` flags.
   - **Pre-Flash Snapshot Backup**: Backs up existing binaries to `/tmp/aa_backup/` before touching flash.
   - **Atomic Write & Remount**: Remounts root `/` read-write only for the duration of the copy, creates `.installed-by-entryaad` markers, calls `sync`, and safely remounts `/` read-only.
   - **Post-Install MD5 Verification & Automated Rollback**: Runs `md5sum -c` directly on flashed files. If any discrepancy is detected, the tool automatically restores the prior snapshot, syncs, and remounts `/` read-only.
   - **Ramdisk Cleanup**: Automatically removes temporary staging files from `/tmp`.

4. **Diagnostic Logs & Wi-Fi Link Analysis**:
   - **One-Click Enable**: Creates `/var/local/data/AA/maintenance` to activate logging.
   - **Pull Logs**: Downloads `app.log`, `app.old.log`, `entry-aa-service.log`, `app-guard`, and `vehicle` into timestamped local folders (`BMW_Logs\Logs_YYYYMMDD_HHMMSS\`).
   - **Wi-Fi Diagnostics Analyzer**: Automatically parses `[WifiLink]` metrics into structured diagnostics:
     - Band (2.4 GHz vs 5 GHz) and Wi-Fi Channel
     - Signal strength (dBm) with Quality Rating (Excellent / Good / Fair / Poor)
     - Rx / Tx bitrates (Mbps)
     - Retried frames & dropped packet counts
     - Round-trip time (RTT in ms)
     - Actionable RF health advice (e.g. phone placement, interference detection)
   - **Clear Logs**: Purges all log files and turns off maintenance mode in one step.

5. **ENET Network & Adapter Diagnostics**:
   - Scans Windows network adapters and verifies APIPA (`169.254.x.x`) auto-IP assignment.
   - Direct ICMP ping test to the head unit (`169.254.1.0`) with delay troubleshooting.

6. **iDrive Settings & Quick Actions**:
   - Configure vehicle model and year (`/var/local/data/AA/vehicle`).
   - Disconnect-safe feature flag management (never wipes user settings if connection drops):
     - `autostart`: Auto-start Android Auto on iDrive boot.
     - `usb`: Force USB cable mode instead of wireless.
     - `entry-direct`: Launch directly without sub-menu.
     - `kombi-off`: Disable cluster / HUD navigation display.
     - `kombi-single-maneuver`: Single maneuver route graph for clusters that reject full graphs.
     - `gps-telephone`: Use phone's internal GPS instead of car GPS.
   - **Start / Stop Android Auto**: Immediate daemon control buttons.
   - **Explore /opt/aa**: Inspect installed binaries, plugins, and file permissions.
   - **Reset App Guard**: Clear `app-guard` and `app.disable` after crash recovery.
   - **Reboot Head Unit**: Trigger a clean head unit reboot over SSH.
   - **Safe Uninstall**: Completely and cleanly remove Android Auto from the car.

---

## 🚀 Quick Start on Windows

### Operational Profile: Engine Running (14.2V Power)
- A PC running **Windows 10** (build 1809 or newer) or **Windows 11**.
- An **ENET Cable** (OBD2 to RJ45 Ethernet) connecting the car's OBD port to your PC (or via USB-C Ethernet adapter).
- **Engine Running**: Keep the car engine running with transmission in Park (P). The alternator delivers continuous ~14.2V power, eliminating battery discharge, sleep mode shutdowns, or BDC terminal 15 timeouts.

### Connecting to the Car
1. Plug the ENET cable into the OBD2 port (driver footwell) and your PC.
2. Start the car engine (vehicle in Park / P).
3. On Windows, leave your Ethernet adapter on **Automatic (DHCP)**.
4. The car will assign an automatic private IP (e.g. `169.254.x.x`). The head unit default IP is `169.254.1.0`.

### Launching the Tool

* **Zero-Window Invisible Launch**: Double-click [Launch_Silent.vbs](file:///c:/Users/Chusa%20Collados/Downloads/EntryNav2_Windows_Tool/Launch_Silent.vbs) to start the tool with **no PowerShell or CMD console screen visible at all**.
* **Standard Launch**: Double-click [Launch_Windows_Tool.bat](file:///c:/Users/Chusa%20Collados/Downloads/EntryNav2_Windows_Tool/Launch_Windows_Tool.bat).
* **PowerShell WPF Native Mode**: Run `.\windows\Launch_Tool.bat --powershell` (the console window automatically hides on startup so only the GUI is displayed).
* **Standalone Single-File EXE**: Run `windows\build_exe.bat` to build a portable `dist\EntryNav2_Manager.exe` with zero Python prerequisites.

---

## 🛠️ Step-by-Step Instructions

### 1. Root SSH Shell Autologin
1. Verify the car IP (default `169.254.1.0`).
2. Click **"Test Connection"**. You will see the exact command sent, the response `● Connected (<firmware version>)`, and confirmation in the activity log.
3. Click **"🚀 Open Root SSH Terminal"**.
4. A dedicated terminal window will open, authenticate `Entry0?Evo!1` automatically, and land directly on the car's `#` root prompt!

---

### 2. Updating or Installing EntryNav2 Android Auto
1. Open the **"Update / Flash Car"** tab.
2. Click **"Fetch Releases from GitHub"** to load published releases, or click **"Browse Local .tar..."** if you have a local archive.
3. Select the desired release (e.g. `v0.12.1-rc.4` or `v0.12.0`). The official **Expected SHA-256** populates automatically.
4. *(Optional)* Enter your car model (e.g. `320d`, `X3`, `M340i`) and year (e.g. `2020`).
5. Click **"⚡ START SAFE FLASH / UPDATE"**.
6. Watch the **"Live Head Unit Output Streamed & Confirmed"** terminal in real time as each step executes:
   - Step 1: Archive SHA-256 integrity check.
   - Step 2: Car SSH pre-flight connectivity, firmware check, and 16 MB space check.
   - Step 3: RAM-disk `/tmp/` upload via SFTP/SCP with transfer rate reporting.
   - Step 4: Archive extraction and in-car MD5 checksum verification.
   - Step 5: Dynamic linker resolution (`LD_TRACE_LOADED_OBJECTS=1`).
   - Step 6: Non-destructive rehearsal dry-run (`aa-supervisor --compat`).
   - Step 7: Pre-flash snapshot backup in `/tmp/aa_backup/` and atomic flash install (`mount -o remount,rw /`, copy, `sync`, remount `ro`).
   - Step 8: Post-install bit-for-bit MD5 verification against flash (with automatic rollback on mismatch).
7. When prompted, choose **Yes** to reboot the head unit.
8. On iDrive: Go to **Media -> Android Auto -> Start**.

---

### 3. Collecting and Analyzing Diagnostic Logs
If you encounter any issues (connection dropouts, Wi-Fi stutter, or crashing):
1. In the **"Diagnostic Logs & Wi-Fi"** tab, check the **Car Maintenance Logging Status** banner:
   - `● Logging: ENABLED (/var/local/data/AA/maintenance active)` (Green)
   - `○ Logging: DISABLED (Normal mode - no logs written)` (Red / Gray)
   - `● Logging: Offline / Unreachable` (if head unit is unreachable)
2. Click **"✅ Enable Maintenance Logging"** to begin recording logs.
3. Reproduce the problem in your car (start Android Auto or connect your phone).
4. Click **"📥 Pull Logs to PC"**.
5. The tool downloads all logs into a timestamped directory (`BMW_Logs\Logs_YYYYMMDD_HHMMSS\`).
6. Review the **Wi-Fi Link Diagnostic Analysis Card**:
   - Signal dBm and Quality Rating (Excellent / Good / Fair / Poor)
   - Frequency band (2.4 GHz vs 5 GHz) and channel
   - Bitrates (Rx/Tx Mbps)
   - Frame retries and packet loss metrics
   - Diagnostic insights and recommendations
7. Review raw logs in the embedded log viewer or click **"📂 Open Logs Folder"**.
8. Once finished diagnosing, click **"❌ Disable & Clear Logs"** to stop logging and purge files from flash.

---

### 4. CLI Usage (Automation & Scripts)

The tool supports complete non-interactive command-line usage:

```bash
# Check installed Android Auto version and car firmware
python windows\entrynav2_tool.py --ip 169.254.1.0 --aa-version

# Check if maintenance logging is currently enabled on the head unit
python windows\entrynav2_tool.py --ip 169.254.1.0 --log-status

# Check connectivity and storage
python windows\entrynav2_tool.py --ip 169.254.1.0 --check

# Launch interactive root shell with autologin
python windows\entrynav2_tool.py --ip 169.254.1.0 --shell

# Reboot head unit over SSH
python windows\entrynav2_tool.py --ip 169.254.1.0 --reboot

# Safe flash with strict SHA-256 enforcement
python windows\entrynav2_tool.py --ip 169.254.1.0 --update entrynav2-android-auto-0.12.1-rc.4-armhf.tar --sha256 <hash> --model 320d --year 2020

# Enable diagnostic logging
python windows\entrynav2_tool.py --ip 169.254.1.0 --enable-logs

# Pull logs to local folder and analyze Wi-Fi link
python windows\entrynav2_tool.py --ip 169.254.1.0 --pull-logs --wifi-diag

# Disable and clear logs
python windows\entrynav2_tool.py --ip 169.254.1.0 --disable-logs

# Inspect network adapters and ping car
python windows\entrynav2_tool.py --ip 169.254.1.0 --net-check
```

---

## 🔒 Automotive Safety & Failsafe Architecture

| Safety Standard | Implementation |
|---|---|
| **Engine Running Power Rail** | Standard operating profile with engine running guarantees constant ~14.2V alternator rail. |
| **Local Digest Validation** | Validates SHA-256 locally before transfer. Aborts immediately on mismatch. |
| **Flash Wear Prevention** | Archive transfers strictly to in-memory `/tmp` tmpfs ramdisk. |
| **Storage Protection** | Verifies root `/` has $\ge 16\text{ MB}$ free with robust multi-line BusyBox parsing. |
| **Clean Process Safety** | Stops running `aa-supervisor` or `entry-aad` with graceful `SIGTERM` followed by `SIGKILL`. |
| **Library Verification** | Checks symbol resolution using the car's dynamic linker `/lib/ld-linux-armhf.so.3` before flashing. |
| **Dry-Run Compatibility** | Executes `aa-supervisor --compat`. If any `@block` issue is reported, installation halts. |
| **Pre-Flash Snapshot** | Backs up existing `/opt/aa` and plugins to `/tmp/aa_backup/` before touching flash. |
| **Read-Only Flash System** | Root filesystem `/` remains read-only at all times except during the exact seconds of file copying. |
| **Post-Write Validation & Rollback** | Runs `md5sum -c` directly on flash. Automatically restores previous snapshot if verification fails. |
| **Crash Guard** | If iDrive crashes 3 times within 2 minutes of app load, head unit disables the plugin (`app-guard`). Reset with 1 click. |

---

## 🧪 Automated Test Suite

Run unit tests locally with `pytest`:

```bash
python -m pytest tests/ -v
```

---

## 📄 License

This tool is distributed under the [PolyForm Noncommercial License 1.0.0](https://github.com/Jiraiya43/EntryNav2-Android-Auto/blob/main/LICENSE.md) consistent with the EntryNav2-Android-Auto project.
