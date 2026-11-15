# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Modernized High-DPI Tkinter GUI for BMW EntryNav2 Windows Suite."""

import os
import platform
import re
import subprocess
import tempfile
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from ..config import CarConfigManager, SUPPORTED_FLAGS
from ..diagnostics import LogManager, WifiAnalyzer
from ..network import NetworkDiagnostics
from ..releases import ReleaseManager, BUILTIN_RELEASES
from ..safety import SafetyWorkflow
from ..transport import (
    DEFAULT_IP,
    DEFAULT_PASS,
    DEFAULT_PORT,
    DEFAULT_USER,
    GLOBAL_LOGGER,
    SSHClientWrapper,
)


def run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    # Enable High-DPI awareness on Windows to prevent blurry rendering on high-res laptop displays
    if platform.system() == "Windows":
        try:
            import ctypes
            try:
                ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)  # Per-monitor v2
            except Exception:
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except Exception:
                    pass

            # Hide console window if launched via python.exe
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass

    root = tk.Tk()
    root.title("BMW EntryNav2 Android Auto - Management & Flashing Suite v2.0")
    root.geometry("1100x820")
    root.minsize(960, 680)

    # BMW Dark Theme Colors
    BG_DARK = "#16181B"
    BG_PANEL = "#21262D"
    BG_INPUT = "#2E3339"
    FG_TEXT = "#E6EDF3"
    FG_MUTED = "#8B949E"
    BMW_BLUE = "#0066B2"
    BMW_LIGHT_BLUE = "#58A6FF"
    BMW_RED = "#D32F2F"
    ACCENT_GREEN = "#2E7D32"

    root.configure(bg=BG_DARK)

    # Configure TTK Styles
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(".", background=BG_DARK, foreground=FG_TEXT)
    style.configure("TNotebook", background=BG_DARK, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background=BG_PANEL,
        foreground=FG_TEXT,
        padding=[16, 8],
        font=("Segoe UI", 10, "bold"),
    )
    style.map("TNotebook.Tab", background=[("selected", BMW_BLUE)], foreground=[("selected", "#FFFFFF")])
    style.configure("TFrame", background=BG_DARK)
    style.configure("Panel.TFrame", background=BG_PANEL, relief="flat")
    style.configure("TLabel", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 9))
    style.configure("Panel.TLabel", background=BG_PANEL, foreground=FG_TEXT, font=("Segoe UI", 9))
    style.configure("Title.TLabel", background=BG_PANEL, foreground=BMW_LIGHT_BLUE, font=("Segoe UI", 11, "bold"))
    style.configure(
        "TButton",
        background=BMW_BLUE,
        foreground="#FFFFFF",
        borderwidth=0,
        padding=[10, 6],
        font=("Segoe UI", 9, "bold"),
    )
    style.map("TButton", background=[("active", BMW_LIGHT_BLUE), ("disabled", "#3A3F45")])
    style.configure("Red.TButton", background=BMW_RED, foreground="#FFFFFF")
    style.map("Red.TButton", background=[("active", "#B71C1C")])
    style.configure("Green.TButton", background=ACCENT_GREEN, foreground="#FFFFFF")
    style.map("Green.TButton", background=[("active", "#1B5E20")])

    # Top Connection Header Panel
    top_frame = ttk.Frame(root, style="Panel.TFrame", padding=12)
    top_frame.pack(fill="x", padx=12, pady=(12, 6))

    ttk.Label(top_frame, text="BMW EntryNav2 Connection (Engine Running):", style="Title.TLabel").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 6)
    )

    ttk.Label(top_frame, text="Car IP:", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=4)
    ip_var = tk.StringVar(value=DEFAULT_IP)
    ip_entry = tk.Entry(
        top_frame, textvariable=ip_var, width=14, bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT, font=("Consolas", 10)
    )
    ip_entry.grid(row=1, column=1, sticky="w", padx=4)

    ttk.Label(top_frame, text="Port:", style="Panel.TLabel").grid(row=1, column=2, sticky="w", padx=4)
    port_var = tk.StringVar(value=str(DEFAULT_PORT))
    port_entry = tk.Entry(
        top_frame, textvariable=port_var, width=5, bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT, font=("Consolas", 10)
    )
    port_entry.grid(row=1, column=3, sticky="w", padx=4)

    ttk.Label(top_frame, text="User:", style="Panel.TLabel").grid(row=1, column=4, sticky="w", padx=4)
    user_var = tk.StringVar(value=DEFAULT_USER)
    user_entry = tk.Entry(
        top_frame, textvariable=user_var, width=6, bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT, font=("Consolas", 10)
    )
    user_entry.grid(row=1, column=5, sticky="w", padx=4)

    ttk.Label(top_frame, text="Password:", style="Panel.TLabel").grid(row=1, column=6, sticky="w", padx=4)
    pass_var = tk.StringVar(value=DEFAULT_PASS)
    pass_entry = tk.Entry(
        top_frame,
        textvariable=pass_var,
        width=14,
        bg=BG_INPUT,
        fg=FG_TEXT,
        insertbackground=FG_TEXT,
        font=("Consolas", 10),
        show="*",
    )
    pass_entry.grid(row=1, column=7, sticky="w", padx=4)

    def toggle_pass_show():
        pass_entry.config(show="" if pass_entry.cget("show") == "*" else "*")

    show_btn = tk.Button(top_frame, text="👁", command=toggle_pass_show, bg=BG_INPUT, fg=FG_TEXT, relief="flat", padx=6)
    show_btn.grid(row=1, column=8, padx=2)

    status_lbl = ttk.Label(
        top_frame, text="● Not Checked", style="Panel.TLabel", foreground=FG_MUTED, font=("Segoe UI", 9, "bold")
    )
    status_lbl.grid(row=1, column=9, padx=8)

    installed_badge_lbl = ttk.Label(
        top_frame, text="AA: ● Not Checked", style="Panel.TLabel", foreground=FG_MUTED, font=("Segoe UI", 9, "bold")
    )
    installed_badge_lbl.grid(row=1, column=10, padx=8)

    def get_ssh() -> SSHClientWrapper:
        return SSHClientWrapper(
            host=ip_var.get().strip(),
            user=user_var.get().strip(),
            password=pass_var.get().strip(),
            port=int(port_var.get().strip() or "22"),
            logger=GLOBAL_LOGGER,
        )

    def reboot_hu():
        if messagebox.askyesno(
            "Confirm Reboot",
            "Are you sure you want to reboot the BMW head unit?\n\nThe central display and audio will restart briefly.",
        ):
            def _worker():
                GLOBAL_LOGGER.log("CMD >>", f"Rebooting head unit at {ip_var.get().strip()}...")
                root.after(0, lambda: status_lbl.config(text="● Rebooting...", foreground="orange"))
                get_ssh().run_command("reboot")
                GLOBAL_LOGGER.log("OK", "🔄 Reboot signal transmitted to head unit.")
            threading.Thread(target=_worker, daemon=True).start()

    btn_top_reboot = tk.Button(
        top_frame,
        text="🔄 Reboot Head Unit",
        command=reboot_hu,
        bg="#8957E5",
        fg="#FFFFFF",
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=8,
        pady=2,
    )
    btn_top_reboot.grid(row=1, column=11, padx=6)

    # Notebook Tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=12, pady=6)

    tab_dash = ttk.Frame(notebook)
    tab_update = ttk.Frame(notebook)
    tab_logs = ttk.Frame(notebook)
    tab_settings = ttk.Frame(notebook)
    tab_net = ttk.Frame(notebook)

    notebook.add(tab_dash, text=" Dashboard & Terminal ")
    notebook.add(tab_update, text=" Update / Flash Car ")
    notebook.add(tab_logs, text=" Diagnostic Logs & Wi-Fi ")
    notebook.add(tab_settings, text=" iDrive Settings & Flags ")
    notebook.add(tab_net, text=" ENET Network Diagnostics ")

    # Bottom Global Log Console
    log_panel = ttk.Frame(root, style="Panel.TFrame", padding=8)
    log_panel.pack(fill="x", padx=12, pady=(0, 10))

    log_bar = ttk.Frame(log_panel, style="Panel.TFrame")
    log_bar.pack(fill="x", pady=(0, 4))
    ttk.Label(
        log_bar, text="Activity, Commands & Head Unit Output Log:", style="Panel.TLabel", font=("Segoe UI", 9, "bold")
    ).pack(side="left")

    autoscroll_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        log_bar,
        text="Autoscroll",
        variable=autoscroll_var,
        bg=BG_PANEL,
        fg=FG_TEXT,
        selectcolor=BG_INPUT,
        activebackground=BG_PANEL,
        activeforeground=FG_TEXT,
        font=("Segoe UI", 8),
    ).pack(side="right", padx=6)

    console_txt = scrolledtext.ScrolledText(
        log_panel, height=8, bg="#0D1117", fg="#E6EDF3", insertbackground="#58A6FF", font=("Consolas", 9)
    )
    console_txt.pack(fill="x", expand=True)

    def setup_text_tags(txt):
        txt.tag_configure("ts", foreground="#8B949E", font=("Consolas", 9))
        txt.tag_configure("cmd", foreground="#58A6FF", font=("Consolas", 9, "bold"))
        txt.tag_configure("hu", foreground="#3FB950", font=("Consolas", 9))
        txt.tag_configure("scp", foreground="#D2A8FF", font=("Consolas", 9, "bold"))
        txt.tag_configure("exit", foreground="#8B949E", font=("Consolas", 9))
        txt.tag_configure("ok", foreground="#3FB950", font=("Consolas", 9, "bold"))
        txt.tag_configure("warn", foreground="#D29922", font=("Consolas", 9, "bold"))
        txt.tag_configure("err", foreground="#F85149", font=("Consolas", 9, "bold"))
        txt.tag_configure("step", foreground="#79C0FF", font=("Consolas", 9, "bold"))
        txt.tag_configure("info", foreground="#E6EDF3", font=("Consolas", 9))

    setup_text_tags(console_txt)

    LOG_LINE_REGEX = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s+\[(.*?)\]\s+(.*)$")

    def insert_formatted_line(txt_widget, text: str, autoscroll: bool = True):
        m = LOG_LINE_REGEX.match(text)
        if m:
            ts, tag, rest = m.groups()
            txt_widget.insert(tk.END, f"[{ts}] ", "ts")
            t_low = tag.lower()
            if "cmd" in t_low:
                s_tag = "cmd"
            elif "hu" in t_low:
                s_tag = "hu"
            elif "scp" in t_low:
                s_tag = "scp"
            elif "exit" in t_low:
                s_tag = "exit"
            elif "ok" in t_low:
                s_tag = "ok"
            elif "warn" in t_low:
                s_tag = "warn"
            elif "err" in t_low or "fail" in t_low:
                s_tag = "err"
            elif "step" in t_low:
                s_tag = "step"
            else:
                s_tag = "info"

            txt_widget.insert(tk.END, f"[{tag}] ", s_tag)
            body_tag = s_tag if s_tag in ("hu", "err") else "info"
            txt_widget.insert(tk.END, f"{rest}\n", body_tag)
        else:
            lower = text.lower()
            tag = "info"
            if "error" in lower or "failed" in lower or "❌" in text:
                tag = "err"
            elif "warn" in lower or "⚠️" in text:
                tag = "warn"
            elif "success" in lower or "✅" in text or "🎉" in text:
                tag = "ok"
            elif "step" in lower or "🚀" in text or "===" in text:
                tag = "step"
            txt_widget.insert(tk.END, f"{text}\n", tag)

        if autoscroll:
            txt_widget.see(tk.END)

    def append_log(formatted_msg: str):
        def _ins():
            insert_formatted_line(console_txt, formatted_msg, autoscroll=autoscroll_var.get())
        root.after(0, _ins)

    GLOBAL_LOGGER.add_listener(append_log)

    def clear_console():
        console_txt.delete("1.0", tk.END)

    def copy_console():
        content = console_txt.get("1.0", tk.END).strip()
        if content:
            root.clipboard_clear()
            root.clipboard_append(content)
            messagebox.showinfo("Copied", "Log content copied to clipboard!")

    def save_console():
        content = console_txt.get("1.0", tk.END).strip()
        if not content:
            return
        f = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"BMW_EntryNav2_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        )
        if f:
            with open(f, "w", encoding="utf-8") as out_f:
                out_f.write(content)
            messagebox.showinfo("Saved", f"Log saved to:\n{f}")

    tk.Button(log_bar, text="💾 Save Log...", command=save_console, bg=BG_INPUT, fg=FG_TEXT, relief="flat", font=("Segoe UI", 8), padx=6).pack(side="right", padx=2)
    tk.Button(log_bar, text="📋 Copy All", command=copy_console, bg=BG_INPUT, fg=FG_TEXT, relief="flat", font=("Segoe UI", 8), padx=6).pack(side="right", padx=2)
    tk.Button(log_bar, text="🗑️ Clear Log", command=clear_console, bg=BG_INPUT, fg=FG_TEXT, relief="flat", font=("Segoe UI", 8), padx=6).pack(side="right", padx=2)

    # ---------------- VERSION ID RETRIEVAL ACTION ----------------
    def retrieve_installed_version_action(show_dialog: bool = True):
        def _worker():
            ssh = get_ssh()
            wf = SafetyWorkflow(ssh)
            info = wf.get_installed_version_info()

            if not info["connected"]:
                err_msg = info.get("raw_output") or f"Host unreachable at {ip_var.get().strip()}"
                root.after(
                    0,
                    lambda: (
                        status_lbl.config(text="● Disconnected", foreground=BMW_RED),
                        installed_badge_lbl.config(text="AA: ● Offline", foreground=BMW_RED),
                        cur_installed_lbl.config(text="Head Unit: Offline / Unreachable (Check ENET Cable)", foreground=BMW_RED),
                    ),
                )
                if show_dialog:
                    root.after(
                        0,
                        lambda: messagebox.showerror(
                            "Connection Error",
                            f"Could not reach head unit at {ip_var.get().strip()}.\n\nError: {err_msg}\n\nPlease verify:\n1. ENET cable is firmly plugged into OBD2 port\n2. Car engine is running (14V power)\n3. Ethernet adapter has 169.254.x.x IP assigned",
                        ),
                    )
                return

            # Update badges
            root.after(0, lambda: status_lbl.config(text=f"● Connected ({info['hu_firmware']})", foreground="#00FF66"))

            if info["installed"]:
                root.after(0, lambda: installed_badge_lbl.config(text=f"AA: ● {info['version']}", foreground="#00FF66"))
                root.after(
                    0,
                    lambda: cur_installed_lbl.config(
                        text=f"Android Auto: {info['version']} ({info['detection_method']}) | iDrive FW: {info['hu_firmware']}",
                        foreground="#00FF66",
                    ),
                )
            else:
                root.after(0, lambda: installed_badge_lbl.config(text="AA: ● Not Installed", foreground=BMW_RED))
                root.after(
                    0,
                    lambda: cur_installed_lbl.config(
                        text=f"Android Auto: NOT INSTALLED | iDrive FW: {info['hu_firmware']}",
                        foreground=BMW_RED,
                    ),
                )

            if show_dialog:
                status_txt = "INSTALLED & READY" if info["installed"] else "NOT INSTALLED"
                msg = (
                    f"=== Android Auto Installation Details ===\n\n"
                    f"• Android Auto Status:   {status_txt}\n"
                    f"• Android Auto Version:  {info['version']}\n"
                    f"• Detection Method:     {info['detection_method']}\n\n"
                    f"• Running Processes:    {info['running_pids'] or 'None (Stopped)'}\n"
                    f"• Car iDrive Firmware:  {info['hu_firmware']}\n"
                    f"• Vehicle Profile:      Model: {info['vehicle_model'] or 'iDrive (default)'}, Year: {info['vehicle_year'] or '2019'}\n\n"
                    f"• Installed Binary Checksums (MD5):\n"
                    f"  - entry-aad:      {info['entry_aad_md5'] or 'N/A'}\n"
                    f"  - aa-supervisor:  {info['aa_supervisor_md5'] or 'N/A'}\n"
                    f"  - libEntryAad.so: {info['lib_entry_aad_md5'] or 'N/A'}\n"
                )
                root.after(0, lambda: messagebox.showinfo("Android Auto Installed Version", msg))

        threading.Thread(target=_worker, daemon=True).start()

    # ---------------- TAB 1: DASHBOARD & TERMINAL ----------------
    dash_top = ttk.Frame(tab_dash, padding=8)
    dash_top.pack(fill="x")

    def test_conn():
        retrieve_installed_version_action(show_dialog=False)
        update_log_status_ui()

    def launch_terminal():
        ssh = get_ssh()
        ssh.launch_interactive_shell()

    def start_android_auto():
        def _worker():
            GLOBAL_LOGGER.log("INFO", "Starting Android Auto on head unit...")
            cmd = "export XDG_RUNTIME_DIR=/run/system/0 WAYLAND_DISPLAY=wayland-0 LD_LIBRARY_PATH=/usr/local/lib:/opt/hmi/lib:/usr/lib:/lib HOME=/tmp; nohup /opt/aa/aa-supervisor > /dev/null 2>&1 &"
            get_ssh().run_command(cmd)
            time.sleep(1.0)
            code, out, _ = get_ssh().run_command("pidof aa-supervisor entry-aad")
            if out.strip():
                GLOBAL_LOGGER.log("OK", f"✅ Android Auto started successfully (PID: {out.strip()}).")
            else:
                GLOBAL_LOGGER.log("WARN", "⚠️ Start command sent, but PID not detected. Try starting from iDrive Media menu.")
        threading.Thread(target=_worker, daemon=True).start()

    def stop_android_auto():
        def _worker():
            GLOBAL_LOGGER.log("INFO", "Stopping Android Auto processes on head unit...")
            get_ssh().run_command("killall aa-supervisor entry-aad 2>/dev/null; sleep 1; killall -9 aa-supervisor entry-aad 2>/dev/null")
            time.sleep(1.0)
            code, out, _ = get_ssh().run_command("pidof aa-supervisor entry-aad")
            if not out.strip():
                GLOBAL_LOGGER.log("OK", "✅ Android Auto processes stopped cleanly.")
            else:
                GLOBAL_LOGGER.log("WARN", f"⚠️ Processes still active: {out.strip()}")
        threading.Thread(target=_worker, daemon=True).start()

    ttk.Button(dash_top, text="Test Car Connection", command=test_conn).pack(side="left", padx=4)
    ttk.Button(dash_top, text="🔍 Check AA Version", command=lambda: retrieve_installed_version_action(show_dialog=True), style="Green.TButton").pack(side="left", padx=4)
    ttk.Button(dash_top, text="🚀 Open Root SSH Terminal", command=launch_terminal).pack(side="left", padx=6)
    ttk.Button(dash_top, text="🟢 Start AA", command=start_android_auto).pack(side="left", padx=4)
    ttk.Button(dash_top, text="🔴 Stop AA", command=stop_android_auto, style="Red.TButton").pack(side="left", padx=4)

    # Info display
    info_frame = ttk.Frame(tab_dash, style="Panel.TFrame", padding=12)
    info_frame.pack(fill="both", expand=True, padx=4, pady=6)

    dash_info_txt = scrolledtext.ScrolledText(info_frame, bg=BG_INPUT, fg=FG_TEXT, font=("Consolas", 10), relief="flat")
    dash_info_txt.pack(fill="both", expand=True)
    dash_info_txt.insert(
        tk.END,
        """=== BMW EntryNav2 Android Auto Windows Management Suite v2.0 ===

Operational Profile: Engine Running (14.2V Alternator Rail Active)

Capabilities & Safety Safeguards:
1. Version Identification:
   Click 'Check AA Version' to detect the installed Android Auto release
   and car firmware via cryptographic MD5 checksum verification.
2. Root SSH Autologin:
   Click 'Open Root SSH Terminal' to open an interactive root shell instantly.
   Password authentication is injected automatically without manual typing.
3. Flash Safety with Automated Rollback:
   Under 'Update / Flash Car', uploads stage strictly in RAM (/tmp),
   run dynamic linker checks (LD_TRACE_LOADED_OBJECTS), compatibility dry-run
   (aa-supervisor --compat), create pre-flash backups, and automatically roll back
   if flash write or verification encounters any anomaly.
4. Wi-Fi Diagnostics Analyzer:
   Head to 'Diagnostic Logs & Wi-Fi' to inspect signal strength (dBm), channel,
   bitrates, packet retries, and dropped frames from real in-car logs.
5. ENET Network Inspector:
   Head to 'ENET Network Diagnostics' to test physical cable link and APIPA IP.

Ready. Click 'Test Car Connection' or 'Check AA Version' to begin.
""",
    )

    # ---------------- TAB 2: UPDATE / FLASH CAR ----------------
    up_frame = ttk.Frame(tab_update, padding=10)
    up_frame.pack(fill="both", expand=True)

    cur_ver_frame = ttk.Frame(up_frame, style="Panel.TFrame", padding=10)
    cur_ver_frame.pack(fill="x", pady=(0, 6))
    ttk.Label(cur_ver_frame, text="Current Car State:", style="Panel.TLabel", font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
    cur_installed_lbl = ttk.Label(cur_ver_frame, text="Android Auto: Not Checked | iDrive FW: Not Checked", style="Panel.TLabel", foreground=BMW_LIGHT_BLUE)
    cur_installed_lbl.pack(side="left", padx=8)
    ttk.Button(cur_ver_frame, text="🔍 Detect Version", command=lambda: retrieve_installed_version_action(show_dialog=False)).pack(side="right", padx=4)

    rel_box = ttk.Frame(up_frame, style="Panel.TFrame", padding=10)
    rel_box.pack(fill="x", pady=4)

    ttk.Label(rel_box, text="Step 1: Select Release or Local Archive", style="Title.TLabel").pack(anchor="w")

    rel_ctrl_frame = ttk.Frame(rel_box, style="Panel.TFrame")
    rel_ctrl_frame.pack(fill="x", pady=6)

    rel_combobox = ttk.Combobox(rel_ctrl_frame, width=52, state="readonly")
    rel_combobox.pack(side="left", padx=4)

    fetched_releases = []

    def fetch_rels():
        def _worker():
            GLOBAL_LOGGER.log("INFO", "Fetching releases from GitHub...")
            try:
                rels = ReleaseManager.get_releases()
                fetched_releases.clear()
                fetched_releases.extend(rels)
                display_items = [
                    f"{r['tag']} ({r['published_at']}) {'[PRE-RELEASE]' if r['prerelease'] else '[STABLE]'}"
                    for r in rels
                ]
                def _update():
                    rel_combobox["values"] = display_items
                    if display_items:
                        rel_combobox.current(0)
                        on_rel_selected(None)
                    GLOBAL_LOGGER.log("OK", f"Loaded {len(rels)} release(s).")
                root.after(0, _update)
            except Exception as e:
                GLOBAL_LOGGER.log("ERROR", f"Error fetching releases: {e}")
        threading.Thread(target=_worker, daemon=True).start()

    fetch_btn = ttk.Button(rel_ctrl_frame, text="Fetch Releases from GitHub", command=fetch_rels)
    fetch_btn.pack(side="left", padx=6)

    local_tar_path_var = tk.StringVar()
    expected_sha_var = tk.StringVar()

    def browse_local():
        f = filedialog.askopenfilename(filetypes=[("Tar archives", "*.tar"), ("All files", "*.*")])
        if f:
            local_tar_path_var.set(f)
            rel_combobox.set(f"Local: {Path(f).name}")
            sha_cand = f + ".sha256"
            if os.path.exists(sha_cand):
                try:
                    with open(sha_cand, "r") as sf:
                        parts = sf.read().strip().split()
                        if parts:
                            expected_sha_var.set(parts[0])
                except Exception:
                    pass

    browse_btn = ttk.Button(rel_ctrl_frame, text="Browse Local .tar...", command=browse_local)
    browse_btn.pack(side="left", padx=6)

    def on_rel_selected(event):
        idx = rel_combobox.current()
        if 0 <= idx < len(fetched_releases):
            r = fetched_releases[idx]
            if r.get("sha_hash"):
                expected_sha_var.set(r["sha_hash"])
            elif r.get("sha_url"):
                def _get_sha():
                    try:
                        req = urllib.request.Request(r["sha_url"], headers={"User-Agent": "EntryNav2-Windows-Tool/2.0"})
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            sha_content = resp.read().decode("utf-8").strip()
                            sha_hash = sha_content.split()[0]
                            root.after(0, lambda: expected_sha_var.set(sha_hash))
                    except Exception:
                        pass
                threading.Thread(target=_get_sha, daemon=True).start()

    rel_combobox.bind("<<ComboboxSelected>>", on_rel_selected)

    sha_frame = ttk.Frame(rel_box, style="Panel.TFrame")
    sha_frame.pack(fill="x", pady=4)
    ttk.Label(sha_frame, text="Expected SHA-256:", style="Panel.TLabel", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
    sha_entry = tk.Entry(
        sha_frame, textvariable=expected_sha_var, width=72, bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT, font=("Consolas", 9)
    )
    sha_entry.grid(row=0, column=1, padx=6)

    # Vehicle details (optional)
    veh_frame = ttk.Frame(up_frame, style="Panel.TFrame", padding=8)
    veh_frame.pack(fill="x", pady=4)
    ttk.Label(veh_frame, text="Step 2: Vehicle Details (Optional)", style="Title.TLabel").grid(
        row=0, column=0, columnspan=4, sticky="w", pady=(0, 4)
    )
    ttk.Label(veh_frame, text="Vehicle Model (e.g. 320d, X3, M340i):", style="Panel.TLabel").grid(row=1, column=0, sticky="w", padx=4)
    model_var = tk.StringVar(value="")
    tk.Entry(veh_frame, textvariable=model_var, width=15, bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT, font=("Segoe UI", 9)).grid(row=1, column=1, sticky="w", padx=4)

    ttk.Label(veh_frame, text="Year (e.g. 2020):", style="Panel.TLabel").grid(row=1, column=2, sticky="w", padx=4)
    year_var = tk.StringVar(value="")
    tk.Entry(veh_frame, textvariable=year_var, width=8, bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT, font=("Segoe UI", 9)).grid(row=1, column=3, sticky="w", padx=4)

    # Live Head Unit Stream Panel
    hu_stream_frame = ttk.Frame(up_frame, style="Panel.TFrame", padding=10)
    hu_stream_frame.pack(fill="both", expand=True, pady=4)

    stream_bar = ttk.Frame(hu_stream_frame, style="Panel.TFrame")
    stream_bar.pack(fill="x", pady=(0, 4))
    ttk.Label(stream_bar, text="📡 Live Head Unit Output Streamed & Confirmed:", style="Title.TLabel").pack(side="left")

    def clear_hu_stream():
        hu_stream_txt.delete("1.0", tk.END)

    def copy_hu_stream():
        content = hu_stream_txt.get("1.0", tk.END).strip()
        if content:
            root.clipboard_clear()
            root.clipboard_append(content)
            messagebox.showinfo("Copied", "Stream content copied to clipboard!")

    tk.Button(stream_bar, text="📋 Copy Stream", command=copy_hu_stream, bg=BG_INPUT, fg=FG_TEXT, relief="flat", font=("Segoe UI", 8), padx=6).pack(side="right", padx=2)
    tk.Button(stream_bar, text="🗑️ Clear Stream", command=clear_hu_stream, bg=BG_INPUT, fg=FG_TEXT, relief="flat", font=("Segoe UI", 8), padx=6).pack(side="right", padx=2)

    hu_stream_txt = scrolledtext.ScrolledText(
        hu_stream_frame, height=10, bg="#0D1117", fg="#3FB950", insertbackground="#3FB950", font=("Consolas", 10)
    )
    hu_stream_txt.pack(fill="both", expand=True)
    setup_text_tags(hu_stream_txt)

    def append_hu_stream(msg: str):
        def _ins():
            insert_formatted_line(hu_stream_txt, msg, autoscroll=True)
        root.after(0, _ins)

    GLOBAL_LOGGER.add_listener(append_hu_stream)

    # Flashing Progress & Action
    flash_box = ttk.Frame(up_frame, style="Panel.TFrame", padding=8)
    flash_box.pack(fill="x", pady=4)

    def set_flash_progress(step: int, text: str):
        root.after(0, lambda: (
            flash_progressbar.configure(value=step),
            flash_progress_lbl.configure(text=text)
        ))

    def start_flashing():
        expected_sha = expected_sha_var.get().strip().lower()
        if not expected_sha:
            messagebox.showerror("Error", "Please select a release or enter expected SHA-256 first.")
            return

        idx = rel_combobox.current()
        local_path = local_tar_path_var.get()
        flash_btn.configure(state="disabled")
        set_flash_progress(0, "Starting safe update...")

        def _flash_thread():
            try:
                target_tar = local_path
                if not target_tar or not os.path.exists(target_tar):
                    if idx < 0 or idx >= len(fetched_releases):
                        root.after(0, lambda: messagebox.showerror("Error", "Please select a valid release or local archive."))
                        set_flash_progress(0, "Failed: No release selected")
                        return
                    r = fetched_releases[idx]
                    target_tar = os.path.join(tempfile.gettempdir(), r["tar_name"])
                    GLOBAL_LOGGER.log("INFO", f"Downloading {r['tar_name']} from GitHub...")

                    def download_prog(down, total):
                        pct = (down / total) * 100 if total > 0 else 0
                        mb_d = down / (1024 * 1024)
                        mb_t = total / (1024 * 1024)
                        set_flash_progress(1, f"Downloading: {mb_d:.1f}/{mb_t:.1f} MB ({pct:.0f}%)")

                    try:
                        ReleaseManager.download_file(r["tar_url"], target_tar, progress_cb=download_prog)
                        GLOBAL_LOGGER.log("OK", "Download complete.")
                    except Exception as e:
                        GLOBAL_LOGGER.log("ERROR", f"Download failed: {e}")
                        set_flash_progress(0, "Failed: Download error")
                        return

                def logged_progress(msg: str):
                    if "[Step 1/8]" in msg:
                        set_flash_progress(1, "Step 1/8: Verifying archive SHA-256...")
                    elif "[Step 2/8]" in msg:
                        set_flash_progress(2, "Step 2/8: In-car pre-flight checks...")
                    elif "[Step 3/8]" in msg:
                        set_flash_progress(3, "Step 3/8: RAM-disk upload...")
                    elif "[Step 4/8]" in msg:
                        set_flash_progress(4, "Step 4/8: In-car MD5 verify...")
                    elif "[Step 5/8]" in msg:
                        set_flash_progress(5, "Step 5/8: Linker symbol resolution...")
                    elif "[Step 6/8]" in msg:
                        set_flash_progress(6, "Step 6/8: Compatibility test...")
                    elif "[Step 7/8]" in msg:
                        set_flash_progress(7, "Step 7/8: Flash install & backup...")
                    elif "[Step 8/8]" in msg:
                        set_flash_progress(8, "Step 8/8: Verifying flash...")
                    elif "INSTALLATION / UPDATE COMPLETED SUCCESSFULLY" in msg:
                        set_flash_progress(8, "✅ Done / Completed")

                ssh = get_ssh()
                wf = SafetyWorkflow(ssh, log_callback=logged_progress)
                success = wf.verify_and_install(
                    local_tar_path=target_tar,
                    expected_sha256=expected_sha,
                    vehicle_model=model_var.get(),
                    vehicle_year=year_var.get(),
                )

                if success:
                    set_flash_progress(8, "✅ Done / Completed")
                    retrieve_installed_version_action(show_dialog=False)
                    ask = messagebox.askyesno(
                        "Installation Complete",
                        "Installation completed and verified on flash!\n\nWould you like to reboot the head unit now?",
                    )
                    if ask:
                        reboot_hu()
                else:
                    set_flash_progress(0, "Failed: Aborted")
                    messagebox.showerror(
                        "Installation Aborted",
                        "Safety checks prevented installation or an error occurred. Any previous state was protected.",
                    )
            finally:
                root.after(0, lambda: flash_btn.configure(state="normal"))

        threading.Thread(target=_flash_thread, daemon=True).start()

    flash_btn = ttk.Button(flash_box, text="⚡ START SAFE FLASH / UPDATE", command=start_flashing, style="Green.TButton")
    flash_btn.pack(pady=4)

    prog_frame = ttk.Frame(flash_box, style="Panel.TFrame")
    prog_frame.pack(fill="x", pady=(2, 4))
    flash_progressbar = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate", maximum=8)
    flash_progressbar.pack(side="left", fill="x", expand=True, padx=(0, 10))
    flash_progress_lbl = ttk.Label(prog_frame, text="Ready", style="Panel.TLabel", font=("Segoe UI", 9, "bold"))
    flash_progress_lbl.pack(side="right")

    # ---------------- TAB 3: DIAGNOSTIC LOGS & WI-FI ----------------
    logs_frame = ttk.Frame(tab_logs, padding=12)
    logs_frame.pack(fill="both", expand=True)

    log_status_box = ttk.Frame(logs_frame, style="Panel.TFrame", padding=12)
    log_status_box.pack(fill="x", pady=(0, 8))

    stat_top_row = ttk.Frame(log_status_box, style="Panel.TFrame")
    stat_top_row.pack(fill="x")
    ttk.Label(stat_top_row, text="Car Maintenance Logging Status", style="Title.TLabel").pack(side="left")

    log_status_lbl = ttk.Label(
        stat_top_row, text="● Logging: Not Checked", style="Panel.TLabel", font=("Segoe UI", 10, "bold"), foreground="#8B949E"
    )
    log_status_lbl.pack(side="right")

    log_files_lbl = ttk.Label(
        log_status_box,
        text="Flag: /var/local/data/AA/maintenance | Diagnostic files on car: Not checked",
        style="Panel.TLabel",
        foreground="#8B949E",
        font=("Segoe UI", 9),
    )
    log_files_lbl.pack(anchor="w", pady=(6, 2))

    # Wi-Fi Link Diagnostics Card
    wifi_card = ttk.Frame(logs_frame, style="Panel.TFrame", padding=12)
    wifi_card.pack(fill="x", pady=4)
    ttk.Label(wifi_card, text="📡 Wi-Fi Link Diagnostic Analysis:", style="Title.TLabel").pack(anchor="w")

    wifi_status_lbl = ttk.Label(
        wifi_card,
        text="No logs pulled yet. Click 'Pull Logs to PC' to analyze wireless connection performance.",
        style="Panel.TLabel",
        font=("Segoe UI", 9),
        foreground="#E6EDF3",
    )
    wifi_status_lbl.pack(anchor="w", pady=(4, 2))

    wifi_rec_lbl = ttk.Label(
        wifi_card,
        text="",
        style="Panel.TLabel",
        font=("Segoe UI", 9, "bold"),
        foreground="#58A6FF",
    )
    wifi_rec_lbl.pack(anchor="w", pady=(2, 0))

    # Controls Box
    log_btn_frame = ttk.Frame(logs_frame, style="Panel.TFrame", padding=10)
    log_btn_frame.pack(fill="x", pady=6)

    def update_log_status_ui():
        def _worker():
            lm = LogManager(get_ssh())
            st = lm.get_logging_status()
            if not st["connected"]:
                root.after(0, lambda: (
                    log_status_lbl.config(text="● Logging: Offline / Unreachable", foreground=BMW_RED),
                    log_files_lbl.config(text="Could not reach head unit to verify logging state.")
                ))
                return
            if st["enabled"]:
                status_str = "● Logging: ENABLED (/var/local/data/AA/maintenance active)"
                color = "#00FF66"
            else:
                status_str = "○ Logging: DISABLED (Normal mode - no logs written)"
                color = "#FF6B6B"

            files_str = f"Diagnostic files on car: {', '.join(st['files']) if st['files'] else 'None present'}"
            root.after(0, lambda: (
                log_status_lbl.config(text=status_str, foreground=color),
                log_files_lbl.config(text=f"Flag: /var/local/data/AA/maintenance | {files_str}")
            ))
        threading.Thread(target=_worker, daemon=True).start()

    def on_enable_logs():
        def _worker():
            lm = LogManager(get_ssh())
            if lm.enable_logs():
                update_log_status_ui()
        threading.Thread(target=_worker, daemon=True).start()

    def on_disable_clear_logs():
        def _worker():
            lm = LogManager(get_ssh())
            if lm.disable_and_clear_logs():
                update_log_status_ui()
        threading.Thread(target=_worker, daemon=True).start()

    last_pulled_dir = tk.StringVar(value="")

    def on_pull_logs():
        def _worker():
            lm = LogManager(get_ssh())
            success, target_dir, data = lm.pull_logs()
            if success:
                last_pulled_dir.set(target_dir)
                GLOBAL_LOGGER.log("OK", f"Logs successfully saved to: {target_dir}")
                dl = data.get("downloaded", {})
                content = []
                for fname, p in dl.items():
                    content.append(f"=== {fname} ({os.path.getsize(p)} bytes) ===")
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as lf:
                            lines = lf.readlines()
                            content.extend([l.rstrip() for l in lines[-100:]])
                    except Exception as e:
                        content.append(f"Error reading file: {e}")
                    content.append("\n")

                full_text = "\n".join(content)
                wifi_diag = data.get("wifi_analysis", {})

                def _update_view():
                    log_viewer.delete("1.0", tk.END)
                    log_viewer.insert(tk.END, full_text)
                    if wifi_diag.get("detected"):
                        wifi_status_lbl.config(text=wifi_diag.get("summary", ""), foreground="#00FF66")
                        wifi_rec_lbl.config(text=f"Diagnostic Insight: {wifi_diag.get('diagnosis', '')}")
                    else:
                        wifi_status_lbl.config(text="No [WifiLink] records found in current logs.", foreground="#8B949E")
                        wifi_rec_lbl.config(text="")

                root.after(0, _update_view)
            update_log_status_ui()
        threading.Thread(target=_worker, daemon=True).start()

    def on_open_folder():
        d = last_pulled_dir.get()
        if d and os.path.isdir(d):
            if platform.system() == "Windows":
                os.startfile(d)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", d])
            else:
                subprocess.Popen(["xdg-open", d])
        else:
            messagebox.showinfo("Info", "No logs pulled yet. Click 'Pull Logs to PC' first.")

    ttk.Button(log_btn_frame, text="🔄 Check Status", command=update_log_status_ui).pack(side="left", padx=4)
    ttk.Button(log_btn_frame, text="✅ Enable Maintenance Logging", command=on_enable_logs, style="Green.TButton").pack(side="left", padx=4)
    ttk.Button(log_btn_frame, text="❌ Disable & Clear Logs", command=on_disable_clear_logs, style="Red.TButton").pack(side="left", padx=4)
    ttk.Button(log_btn_frame, text="📥 Pull Logs to PC", command=on_pull_logs).pack(side="left", padx=8)
    ttk.Button(log_btn_frame, text="📂 Open Logs Folder", command=on_open_folder).pack(side="left", padx=4)

    ttk.Label(logs_frame, text="Pulled Logs Viewer (Last 100 lines per file):", style="Panel.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6, 2))
    log_viewer = scrolledtext.ScrolledText(logs_frame, height=10, bg=BG_INPUT, fg=FG_TEXT, font=("Consolas", 9))
    log_viewer.pack(fill="both", expand=True)

    # ---------------- TAB 4: IDRIVE SETTINGS & FLAGS ----------------
    set_frame = ttk.Frame(tab_settings, padding=12)
    set_frame.pack(fill="both", expand=True)

    action_box = ttk.Frame(set_frame, style="Panel.TFrame", padding=10)
    action_box.pack(fill="x", pady=4)
    ttk.Label(action_box, text="Head Unit Quick Actions", style="Title.TLabel").pack(anchor="w", pady=(0, 6))

    def on_reset_app_guard():
        def _worker():
            cfg = CarConfigManager(get_ssh())
            cfg.reset_app_guard()
        threading.Thread(target=_worker, daemon=True).start()

    def on_check_status():
        def _worker():
            ssh = get_ssh()
            ssh.run_command("head -n 1 /etc/version")
            ssh.run_command("uptime")
            ssh.run_command("free -m")
            ssh.run_command("df -h /")
            ssh.run_command("pidof HmiMain3D aa-supervisor entry-aad")
            ssh.run_command("grep -c libEntryAad /proc/$(pidof HmiMain3D)/maps 2>/dev/null")
        threading.Thread(target=_worker, daemon=True).start()

    def on_explore_opt_aa():
        def _worker():
            ssh = get_ssh()
            GLOBAL_LOGGER.log("INFO", "Listing files and permissions in /opt/aa and plugins...")
            ssh.run_command("ls -la /opt/aa /opt/hmi/data/ro/Plugins/EntryAad")
        threading.Thread(target=_worker, daemon=True).start()

    def on_uninstall():
        if messagebox.askyesno(
            "CONFIRM UNINSTALL",
            "Are you sure you want to uninstall EntryNav2 Android Auto from the car?\nThis will remove /opt/aa, plugins, and reset configurations.",
        ):
            def _worker():
                GLOBAL_LOGGER.log("WARN", "Removing Android Auto from head unit...")
                cmd = """
mount -o remount,rw / && \\
rm -rf /opt/hmi/data/ro/Plugins/EntryAad /opt/aa && \\
sync && \\
(mount -o remount,ro / 2>/dev/null || true) && \\
rm -rf /var/local/data/AA
"""
                code, out, err = get_ssh().run_command(cmd)
                get_ssh().run_command("sync; mount -o remount,ro / 2>/dev/null || true")
                if code == 0:
                    GLOBAL_LOGGER.log("OK", "✅ Android Auto uninstalled. Reboot head unit to finish.")
                    root.after(0, lambda: installed_badge_lbl.config(text="AA: ● Not Installed", foreground=BMW_RED))
                else:
                    GLOBAL_LOGGER.log("ERROR", f"❌ Uninstall failed: {err}")
            threading.Thread(target=_worker, daemon=True).start()

    ttk.Button(action_box, text="🔍 Check AA Version", command=lambda: retrieve_installed_version_action(show_dialog=True), style="Green.TButton").pack(side="left", padx=4)
    ttk.Button(action_box, text="Check System Status", command=on_check_status).pack(side="left", padx=4)
    ttk.Button(action_box, text="Explore /opt/aa", command=on_explore_opt_aa).pack(side="left", padx=4)
    ttk.Button(action_box, text="Reset App Guard", command=on_reset_app_guard).pack(side="left", padx=4)
    ttk.Button(action_box, text="🔄 Reboot Head Unit", command=reboot_hu).pack(side="left", padx=4)
    ttk.Button(action_box, text="⚠️ Uninstall Android Auto", command=on_uninstall, style="Red.TButton").pack(side="right", padx=4)

    # Flags toggles
    toggles_box = ttk.Frame(set_frame, style="Panel.TFrame", padding=10)
    toggles_box.pack(fill="x", pady=8)
    ttk.Label(toggles_box, text="Android Auto Configuration Flags (/var/local/data/AA)", style="Title.TLabel").pack(anchor="w", pady=(0, 6))

    flags_dict = {key: tk.BooleanVar(value=False) for key in SUPPORTED_FLAGS}

    for key, label in SUPPORTED_FLAGS.items():
        cb = tk.Checkbutton(
            toggles_box,
            text=f"{key}: {label}",
            variable=flags_dict[key],
            bg=BG_PANEL,
            fg=FG_TEXT,
            selectcolor=BG_INPUT,
            activebackground=BG_PANEL,
            activeforeground=FG_TEXT,
            font=("Segoe UI", 9),
        )
        cb.pack(anchor="w", pady=2)

    def read_flags():
        def _worker():
            cfg = CarConfigManager(get_ssh())
            success, flags = cfg.read_flags()
            if success:
                for key, val in flags.items():
                    if key in flags_dict:
                        root.after(0, lambda v=flags_dict[key], s=val: v.set(s))
            else:
                GLOBAL_LOGGER.log("WARN", "Flags preserved (did not overwrite local selections while offline).")
        threading.Thread(target=_worker, daemon=True).start()

    def save_flags():
        def _worker():
            cfg = CarConfigManager(get_ssh())
            current = {k: v.get() for k, v in flags_dict.items()}
            cfg.save_flags(current)
            update_log_status_ui()
        threading.Thread(target=_worker, daemon=True).start()

    ctrl_flags_frame = ttk.Frame(toggles_box, style="Panel.TFrame")
    ctrl_flags_frame.pack(fill="x", pady=6)
    ttk.Button(ctrl_flags_frame, text="Read Current Settings from Car", command=read_flags).pack(side="left", padx=4)
    ttk.Button(ctrl_flags_frame, text="💾 Save Settings to Car", command=save_flags, style="Green.TButton").pack(side="left", padx=8)

    # ---------------- TAB 5: ENET NETWORK DIAGNOSTICS ----------------
    net_frame = ttk.Frame(tab_net, padding=12)
    net_frame.pack(fill="both", expand=True)

    net_box = ttk.Frame(net_frame, style="Panel.TFrame", padding=12)
    net_box.pack(fill="x", pady=4)
    ttk.Label(net_box, text="ENET Cable & Network Adapter Inspection", style="Title.TLabel").pack(anchor="w", pady=(0, 6))

    net_info_lbl = ttk.Label(net_box, text="Click 'Scan Network Adapters' to check ENET link status.", style="Panel.TLabel", font=("Segoe UI", 9))
    net_info_lbl.pack(anchor="w", pady=4)

    def scan_network():
        def _worker():
            GLOBAL_LOGGER.log("INFO", "Scanning local network adapters for ENET connection...")
            summary = NetworkDiagnostics.get_adapter_summary()
            ping_ok, ping_msg = NetworkDiagnostics.ping_host(ip_var.get().strip())

            lines = [
                f"• Link Status:       {summary['recommendation']}",
                f"• Head Unit Ping:    {ping_msg}",
                f"• Active Adapters:   {len(summary['active_adapters'])} detected"
            ]
            for ad in summary["active_adapters"]:
                lines.append(f"  - {ad.get('name', 'Adapter')}: {ad.get('ip', 'N/A')}")

            full_text = "\n".join(lines)
            root.after(0, lambda: net_info_lbl.config(text=full_text))
            GLOBAL_LOGGER.log("OK" if (summary["has_apipa"] or ping_ok) else "WARN", ping_msg)
        threading.Thread(target=_worker, daemon=True).start()

    ttk.Button(net_box, text="🔍 Scan Network Adapters & Ping Car", command=scan_network).pack(anchor="w", pady=6)

    net_guide = scrolledtext.ScrolledText(net_frame, height=12, bg=BG_INPUT, fg=FG_TEXT, font=("Consolas", 9), relief="flat")
    net_guide.pack(fill="both", expand=True, pady=6)
    net_guide.insert(
        tk.END,
        """=== ENET OBD2 Hardware & Connection Troubleshooting Guide ===

1. Operational Profile: Engine Running (Park / P)
   • Keep the car engine running so the alternator delivers continuous ~14.2V power.
   • This prevents battery drain, sleep-mode shutdowns, and terminal 15 timeouts.

2. Physical Connection:
   • Plug the OBD2 connector firmly into the driver footwell port.
   • Connect the RJ45 Ethernet cable to your PC (or via USB-C Ethernet adapter).

3. Windows Auto-IP (APIPA 169.254.x.x):
   • In Windows Network Settings, leave your Ethernet adapter on 'Automatic (DHCP)'.
   • The BMW head unit assigns an automatic IP (169.254.x.x).
   • Note: Windows often takes 15-30 seconds to configure this link. If ping fails,
     wait 20 seconds and click 'Scan Network Adapters & Ping Car' again.

4. Default IP Addresses:
   • Head Unit: 169.254.1.0 (Port: 22, User: root, Pass: Entry0?Evo!1)
""",
    )

    def on_tab_changed(event):
        try:
            sel = notebook.select()
            tab_name = notebook.tab(sel, "text")
            if "Diagnostic Logs" in tab_name:
                update_log_status_ui()
            elif "Settings" in tab_name:
                read_flags()
        except Exception:
            pass

    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    # Initialize with verified built-in releases
    fetched_releases.extend(BUILTIN_RELEASES)
    display_items = [
        f"{r['tag']} ({r['published_at']}) {'[PRE-RELEASE]' if r['prerelease'] else '[STABLE]'}"
        for r in BUILTIN_RELEASES
    ]
    rel_combobox["values"] = display_items
    if display_items:
        rel_combobox.current(0)
        on_rel_selected(None)

    # Refresh releases from GitHub live in background
    fetch_rels()

    root.mainloop()
