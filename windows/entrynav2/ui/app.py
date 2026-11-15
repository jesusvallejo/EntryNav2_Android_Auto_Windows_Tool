# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Clean, focused, modern High-DPI GUI for BMW EntryNav2 Windows Suite."""

import os
import platform
import re
import subprocess
import tempfile
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

from ..config import CarConfigManager, SUPPORTED_FLAGS
from ..diagnostics import LogManager
from ..network import NetworkDiagnostics
from ..releases import ReleaseManager, BUILTIN_RELEASES, UPSTREAM_URL, DEFAULT_REPO
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

    # Enable High-DPI awareness on Windows to prevent blurry rendering
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
    root.title("BMW EntryNav2 Android Auto - Windows Suite v2.0")
    root.geometry("1100x800")
    root.minsize(940, 660)

    # Clean Dark Palette
    BG_DARK = "#0D1117"
    BG_PANEL = "#161B22"
    BG_CARD = "#21262D"
    BG_INPUT = "#0D1117"
    BORDER_COLOR = "#30363D"
    BORDER_ACTIVE = "#58A6FF"
    FG_TEXT = "#F0F6FC"
    FG_MUTED = "#8B949E"
    COLOR_BLUE = "#1F6FEB"
    COLOR_LIGHT_BLUE = "#58A6FF"
    COLOR_GREEN = "#238636"
    COLOR_GREEN_BRIGHT = "#3FB950"
    COLOR_RED = "#DA3633"
    COLOR_AMBER = "#D29922"

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
        padding=[18, 9],
        font=("Segoe UI", 10, "bold"),
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLOR_BLUE), ("active", BG_CARD)],
        foreground=[("selected", "#FFFFFF"), ("active", "#FFFFFF")],
    )
    style.configure("TFrame", background=BG_DARK)
    style.configure("Panel.TFrame", background=BG_PANEL, relief="flat")
    style.configure("Card.TFrame", background=BG_CARD, relief="flat")
    style.configure("TLabel", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 9))
    style.configure("Panel.TLabel", background=BG_PANEL, foreground=FG_TEXT, font=("Segoe UI", 9))
    style.configure("Card.TLabel", background=BG_CARD, foreground=FG_TEXT, font=("Segoe UI", 9))

    style.configure(
        "Horizontal.TProgressbar",
        background=COLOR_GREEN_BRIGHT,
        troughcolor=BG_INPUT,
        borderwidth=0,
        thickness=8,
    )

    style.configure(
        "TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_CARD,
        foreground=FG_TEXT,
        arrowcolor=FG_TEXT,
        bordercolor=BORDER_COLOR,
        padding=4,
    )
    style.map("TCombobox", fieldbackground=[("readonly", BG_INPUT)], foreground=[("readonly", FG_TEXT)])

    # Helper: Flat Button with Hover Effect (100% text-based, no broken emoji glyphs)
    def create_btn(
        parent,
        text,
        command,
        bg=COLOR_BLUE,
        fg="#FFFFFF",
        hover_bg=None,
        font=("Segoe UI", 9, "bold"),
        padx=10,
        pady=5,
        cursor="hand2",
    ):
        if hover_bg is None:
            hover_bg = COLOR_LIGHT_BLUE if bg == COLOR_BLUE else "#388BFD"
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground="#FFFFFF",
            relief="flat",
            cursor=cursor,
            font=font,
            padx=padx,
            pady=pady,
            bd=0,
            highlightthickness=0,
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg) if str(btn["state"]) != "disabled" else None)
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg) if str(btn["state"]) != "disabled" else None)
        return btn

    # Helper: Card Frame with Subtle Border
    def create_card(parent, title=None, subtitle=None, fill="x", padx=12, pady=10, pady_outer=4):
        card = tk.Frame(
            parent,
            bg=BG_PANEL,
            highlightbackground=BORDER_COLOR,
            highlightcolor=BORDER_ACTIVE,
            highlightthickness=1,
            padx=padx,
            pady=pady,
        )
        card.pack(fill=fill, pady=pady_outer, padx=2)
        if title or subtitle:
            hdr = tk.Frame(card, bg=BG_PANEL)
            hdr.pack(fill="x", pady=(0, 6))
            if title:
                tk.Label(hdr, text=title, bg=BG_PANEL, fg=COLOR_LIGHT_BLUE, font=("Segoe UI", 10, "bold")).pack(
                    side="left"
                )
            if subtitle:
                tk.Label(hdr, text=subtitle, bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 8)).pack(
                    side="right", padx=4
                )
        return card

    # ---------------- 1. TOP TITLE & UPSTREAM BAR ----------------
    top_header = tk.Frame(root, bg=BG_PANEL, padx=16, pady=8, highlightbackground=BORDER_COLOR, highlightthickness=1)
    top_header.pack(fill="x", padx=12, pady=(8, 4))

    # Left: Brand & Version
    brand_frame = tk.Frame(top_header, bg=BG_PANEL)
    brand_frame.pack(side="left")

    tk.Label(
        brand_frame,
        text="BMW EntryNav2 Android Auto",
        bg=BG_PANEL,
        fg=FG_TEXT,
        font=("Segoe UI", 12, "bold"),
    ).pack(side="left")

    version_pill = tk.Label(
        brand_frame,
        text=" v2.0 ",
        bg=BG_CARD,
        fg=COLOR_LIGHT_BLUE,
        font=("Segoe UI", 8, "bold"),
        padx=6,
        pady=2,
    )
    version_pill.pack(side="left", padx=8)

    # Right: Upstream Link & Status Indicators
    header_right = tk.Frame(top_header, bg=BG_PANEL)
    header_right.pack(side="right")

    upstream_btn = create_btn(
        header_right,
        text=f"Upstream: {DEFAULT_REPO}",
        command=lambda: webbrowser.open(UPSTREAM_URL),
        bg=BG_CARD,
        fg=COLOR_LIGHT_BLUE,
        hover_bg="#2D333B",
        font=("Segoe UI", 8, "bold"),
        padx=8,
        pady=3,
    )
    upstream_btn.pack(side="left", padx=6)

    status_pill = tk.Label(
        header_right,
        text=" Head Unit: Not Checked ",
        bg=BG_CARD,
        fg=FG_MUTED,
        font=("Segoe UI", 9, "bold"),
        padx=10,
        pady=3,
    )
    status_pill.pack(side="left", padx=4)

    aa_badge_pill = tk.Label(
        header_right,
        text=" AA: Not Checked ",
        bg=BG_CARD,
        fg=FG_MUTED,
        font=("Segoe UI", 9, "bold"),
        padx=10,
        pady=3,
    )
    aa_badge_pill.pack(side="left", padx=4)

    # ---------------- 2. CONNECTION PARAMETERS CARD ----------------
    conn_card = tk.Frame(root, bg=BG_CARD, padx=12, pady=8, highlightbackground=BORDER_COLOR, highlightthickness=1)
    conn_card.pack(fill="x", padx=12, pady=(2, 6))

    inputs_frame = tk.Frame(conn_card, bg=BG_CARD)
    inputs_frame.pack(side="left")

    def make_input(parent, label_text, default_val, width=12, show=None):
        f = tk.Frame(parent, bg=BG_CARD)
        f.pack(side="left", padx=5)
        tk.Label(f, text=label_text, bg=BG_CARD, fg=COLOR_LIGHT_BLUE, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        var = tk.StringVar(value=default_val)
        entry = tk.Entry(
            f,
            textvariable=var,
            width=width,
            bg=BG_INPUT,
            fg=FG_TEXT,
            insertbackground=COLOR_LIGHT_BLUE,
            font=("Consolas", 10),
            show=show or "",
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=COLOR_LIGHT_BLUE,
        )
        entry.pack(pady=2)
        return var, entry

    ip_var, ip_entry = make_input(inputs_frame, "Car IP Address", DEFAULT_IP, width=14)
    port_var, port_entry = make_input(inputs_frame, "Port", str(DEFAULT_PORT), width=5)
    user_var, user_entry = make_input(inputs_frame, "User", DEFAULT_USER, width=7)
    pass_var, pass_entry = make_input(inputs_frame, "Password", DEFAULT_PASS, width=13, show="*")

    def toggle_pass():
        if pass_entry.cget("show") == "*":
            pass_entry.config(show="")
            show_pass_btn.config(text="Hide")
        else:
            pass_entry.config(show="*")
            show_pass_btn.config(text="Show")

    show_pass_btn = tk.Button(
        inputs_frame,
        text="Show",
        command=toggle_pass,
        bg=BG_INPUT,
        fg=FG_TEXT,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 8),
        bd=0,
        padx=6,
        pady=3,
    )
    show_pass_btn.pack(side="left", padx=(0, 8), pady=(14, 0))

    conn_actions = tk.Frame(conn_card, bg=BG_CARD)
    conn_actions.pack(side="right")

    def get_ssh() -> SSHClientWrapper:
        return SSHClientWrapper(
            host=ip_var.get().strip(),
            user=user_var.get().strip(),
            password=pass_var.get().strip(),
            port=int(port_var.get().strip() or "22"),
            logger=GLOBAL_LOGGER,
        )

    # ---------------- 3. CORE LOGIC & ACTIONS ----------------
    def update_connection_status(info: dict):
        if not info["connected"]:
            status_pill.config(text=" Head Unit: Unreachable ", bg="#3A1515", fg=COLOR_RED)
            aa_badge_pill.config(text=" AA: Offline ", bg="#3A1515", fg=COLOR_RED)
            cur_installed_lbl.config(text="Head Unit: Unreachable (Check ENET cable and IP configuration)", fg=COLOR_RED)
            return

        status_pill.config(text=f" Reachable: {info['hu_firmware']} ", bg="#122E1A", fg=COLOR_GREEN_BRIGHT)

        if info["installed"]:
            aa_badge_pill.config(text=f" AA: {info['version']} ", bg="#122E1A", fg=COLOR_GREEN_BRIGHT)
            cur_installed_lbl.config(
                text=f"Android Auto: {info['version']} ({info['detection_method']}) | Firmware: {info['hu_firmware']}",
                fg=COLOR_GREEN_BRIGHT,
            )
        else:
            aa_badge_pill.config(text=" AA: Not Installed ", bg="#3A1515", fg=COLOR_RED)
            cur_installed_lbl.config(
                text=f"Android Auto: NOT INSTALLED | Firmware: {info['hu_firmware']}",
                fg=COLOR_RED,
            )

    def retrieve_installed_version_action(show_dialog: bool = True):
        def _worker():
            ssh = get_ssh()
            wf = SafetyWorkflow(ssh)
            info = wf.get_installed_version_info()
            root.after(0, lambda: update_connection_status(info))

            if not info["connected"] and show_dialog:
                err_msg = info.get("raw_output") or f"Host unreachable at {ip_var.get().strip()}"
                root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Connection Failed",
                        f"Could not reach head unit at {ip_var.get().strip()}.\n\nError: {err_msg}\n\nPlease verify:\n1. ENET cable is securely connected to OBD2 port\n2. Ethernet adapter has an automatic private IP (169.254.x.x)",
                    ),
                )
                return

            if show_dialog and info["connected"]:
                status_txt = "INSTALLED" if info["installed"] else "NOT INSTALLED"
                msg = (
                    f"=== Head Unit Status ===\n\n"
                    f"• Head Unit Firmware:   {info['hu_firmware']}\n"
                    f"• Android Auto Status:  {status_txt}\n"
                    f"• Installed Version:    {info['version']}\n"
                    f"• Detection Method:     {info['detection_method']}\n"
                    f"• Active Processes:     {info['running_pids'] or 'None (Stopped)'}\n\n"
                    f"• Installed Binary Checksums (MD5):\n"
                    f"  - entry-aad:      {info['entry_aad_md5'] or 'N/A'}\n"
                    f"  - aa-supervisor:  {info['aa_supervisor_md5'] or 'N/A'}\n"
                    f"  - libEntryAad.so: {info['lib_entry_aad_md5'] or 'N/A'}\n"
                )
                root.after(0, lambda: messagebox.showinfo("Android Auto Version Info", msg))

        threading.Thread(target=_worker, daemon=True).start()

    def test_conn():
        retrieve_installed_version_action(show_dialog=False)

    def launch_terminal():
        ssh = get_ssh()
        ssh.launch_interactive_shell()

    create_btn(conn_actions, "Test Connection", test_conn, bg=COLOR_BLUE, hover_bg="#388BFD").pack(side="left", padx=3)
    create_btn(conn_actions, "Check AA Version", lambda: retrieve_installed_version_action(show_dialog=True), bg=COLOR_GREEN, hover_bg="#2EA043").pack(side="left", padx=3)
    create_btn(conn_actions, "Open SSH Terminal", launch_terminal, bg="#316DCA", hover_bg="#4B89E8").pack(side="left", padx=3)

    # ---------------- 4. MAIN TABS ----------------
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=12, pady=4)

    tab_update = ttk.Frame(notebook)
    tab_settings = ttk.Frame(notebook)
    tab_net = ttk.Frame(notebook)
    tab_logs = ttk.Frame(notebook)

    notebook.add(tab_update, text=" Flash & Update ")
    notebook.add(tab_settings, text=" iDrive Settings & Flags ")
    notebook.add(tab_net, text=" ENET Network Diagnostics ")
    notebook.add(tab_logs, text=" Diagnostic Logs ")

    # ---------------- 5. BOTTOM GLOBAL LOG CONSOLE ----------------
    log_panel = tk.Frame(root, bg=BG_PANEL, padx=12, pady=6, highlightbackground=BORDER_COLOR, highlightthickness=1)
    log_panel.pack(fill="x", padx=12, pady=(4, 8))

    log_bar = tk.Frame(log_panel, bg=BG_PANEL)
    log_bar.pack(fill="x", pady=(0, 4))

    tk.Label(
        log_bar,
        text="Activity, Terminal Commands & Output Log:",
        bg=BG_PANEL,
        fg=COLOR_LIGHT_BLUE,
        font=("Segoe UI", 9, "bold"),
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

    def clear_console():
        console_txt.delete("1.0", tk.END)

    def copy_console():
        content = console_txt.get("1.0", tk.END).strip()
        if content:
            root.clipboard_clear()
            root.clipboard_append(content)
            messagebox.showinfo("Copied", "Log output copied to clipboard!")

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

    create_btn(log_bar, "Save Log...", save_console, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B", font=("Segoe UI", 8), padx=6, pady=2).pack(side="right", padx=2)
    create_btn(log_bar, "Copy All", copy_console, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B", font=("Segoe UI", 8), padx=6, pady=2).pack(side="right", padx=2)
    create_btn(log_bar, "Clear", clear_console, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B", font=("Segoe UI", 8), padx=6, pady=2).pack(side="right", padx=2)

    console_txt = scrolledtext.ScrolledText(
        log_panel,
        height=7,
        bg="#05080A",
        fg="#E6EDF3",
        insertbackground=COLOR_LIGHT_BLUE,
        font=("Consolas", 9),
        relief="flat",
        bd=0,
    )
    console_txt.pack(fill="x", expand=True)

    tk.Label(
        log_panel,
        text="DISCLAIMER: Modifying vehicle head unit flash carries inherent risk. All actions are taken entirely at your own risk and responsibility. No warranty is provided.",
        bg=BG_PANEL,
        fg=COLOR_AMBER,
        font=("Segoe UI", 8),
    ).pack(fill="x", pady=(4, 0))

    def setup_text_tags(txt):
        txt.tag_configure("ts", foreground="#6E7681", font=("Consolas", 9))
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
            if "error" in lower or "failed" in lower or "fail" in lower:
                tag = "err"
            elif "warn" in lower:
                tag = "warn"
            elif "success" in lower or "passed" in lower:
                tag = "ok"
            elif "step" in lower or "===" in text:
                tag = "step"
            txt_widget.insert(tk.END, f"{text}\n", tag)

        if autoscroll:
            txt_widget.see(tk.END)

    def append_log(formatted_msg: str):
        def _ins():
            insert_formatted_line(console_txt, formatted_msg, autoscroll=autoscroll_var.get())
        root.after(0, _ins)

    GLOBAL_LOGGER.add_listener(append_log)

    # =========================================================================
    # TAB 1: FLASH & UPDATE
    # =========================================================================
    up_container = tk.Frame(tab_update, bg=BG_DARK, padx=8, pady=8)
    up_container.pack(fill="both", expand=True)

    # State Banner
    state_card = tk.Frame(up_container, bg=BG_PANEL, padx=12, pady=8, highlightbackground=BORDER_COLOR, highlightthickness=1)
    state_card.pack(fill="x", pady=(0, 6))
    tk.Label(state_card, text="Current State:", bg=BG_PANEL, fg=COLOR_LIGHT_BLUE, font=("Segoe UI", 9, "bold")).pack(side="left")
    cur_installed_lbl = tk.Label(state_card, text="Head Unit: Not Checked | Android Auto: Not Checked", bg=BG_PANEL, fg=FG_TEXT, font=("Segoe UI", 9))
    cur_installed_lbl.pack(side="left", padx=8)
    create_btn(state_card, "Refresh State", lambda: retrieve_installed_version_action(show_dialog=False), bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B", font=("Segoe UI", 8), padx=8, pady=2).pack(side="right")

    # Step 1: Release Archive Selection
    rel_card = create_card(up_container, "Select Release Archive")
    rel_ctrl_frame = tk.Frame(rel_card, bg=BG_PANEL)
    rel_ctrl_frame.pack(fill="x", pady=4)

    rel_combobox = ttk.Combobox(rel_ctrl_frame, width=54, state="readonly")
    rel_combobox.pack(side="left", padx=(0, 6))

    fetched_releases = []

    def fetch_rels():
        def _worker():
            GLOBAL_LOGGER.log("INFO", f"Fetching live releases from {UPSTREAM_URL}...")
            try:
                rels = ReleaseManager.get_releases()
                fetched_releases.clear()
                fetched_releases.extend(rels)
                display_items = [
                    f"{r['tag']} ({r['published_at'][:10] if r.get('published_at') else ''}) {'[Pre-Release]' if r['prerelease'] else '[Stable]'}"
                    for r in rels
                ]
                def _update():
                    rel_combobox["values"] = display_items
                    if display_items:
                        rel_combobox.current(0)
                        on_rel_selected(None)
                    GLOBAL_LOGGER.log("OK", f"Loaded {len(rels)} release(s) dynamically from GitHub.")
                root.after(0, _update)
            except Exception as e:
                GLOBAL_LOGGER.log("ERROR", f"Error fetching releases: {e}")
        threading.Thread(target=_worker, daemon=True).start()

    create_btn(rel_ctrl_frame, "Refresh Releases", fetch_rels, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B", font=("Segoe UI", 8, "bold")).pack(side="left", padx=3)

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

    create_btn(rel_ctrl_frame, "Browse Local .tar...", browse_local, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B", font=("Segoe UI", 8, "bold")).pack(side="left", padx=3)
    create_btn(rel_ctrl_frame, "Open Upstream Repo", lambda: webbrowser.open(UPSTREAM_URL), bg=BG_CARD, fg=COLOR_LIGHT_BLUE, hover_bg="#2D333B", font=("Segoe UI", 8), padx=6).pack(side="right")

    def on_rel_selected(event):
        idx = rel_combobox.current()
        if 0 <= idx < len(fetched_releases):
            r = fetched_releases[idx]
            def _get_sha():
                sha = ReleaseManager.fetch_sha256_for_release(r)
                if sha:
                    root.after(0, lambda: expected_sha_var.set(sha))
            threading.Thread(target=_get_sha, daemon=True).start()

    rel_combobox.bind("<<ComboboxSelected>>", on_rel_selected)

    sha_row = tk.Frame(rel_card, bg=BG_PANEL)
    sha_row.pack(fill="x", pady=(6, 2))
    tk.Label(sha_row, text="Expected SHA-256:", bg=BG_PANEL, fg=COLOR_LIGHT_BLUE, font=("Segoe UI", 8, "bold")).pack(side="left")
    sha_entry = tk.Entry(
        sha_row,
        textvariable=expected_sha_var,
        width=74,
        bg=BG_INPUT,
        fg=FG_TEXT,
        insertbackground=COLOR_LIGHT_BLUE,
        font=("Consolas", 9),
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
    )
    sha_entry.pack(side="left", padx=8)

    # Step 2: Flash Action & Progress
    flash_card = create_card(up_container, "Flash Procedure", "In-Car Installation & Verification", fill="both")

    def set_flash_progress(step: int, text: str):
        root.after(0, lambda: (
            flash_progressbar.configure(value=step),
            flash_progress_lbl.configure(text=text)
        ))

    def start_flashing():
        expected_sha = expected_sha_var.get().strip().lower()
        if not expected_sha:
            messagebox.showerror("SHA Required", "Please select a release or enter the expected SHA-256 first.")
            return

        confirm = messagebox.askyesno(
            "Confirm Flash / Update",
            "DISCLAIMER: Modifying vehicle head unit software carries inherent risk. You proceed entirely at your own risk and responsibility.\n\nRecommendation: Keep the car engine running during flashing to ensure stable power.\n\nDo you want to proceed with installing this update?",
        )
        if not confirm:
            return

        idx = rel_combobox.current()
        local_path = local_tar_path_var.get()
        flash_btn.configure(state="disabled")
        set_flash_progress(0, "Starting update...")

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
                        set_flash_progress(4, "Step 4/8: In-car MD5 check...")
                    elif "[Step 5/8]" in msg:
                        set_flash_progress(5, "Step 5/8: Dynamic linker resolution...")
                    elif "[Step 6/8]" in msg:
                        set_flash_progress(6, "Step 6/8: Compatibility test...")
                    elif "[Step 7/8]" in msg:
                        set_flash_progress(7, "Step 7/8: Flash install & snapshot...")
                    elif "[Step 8/8]" in msg:
                        set_flash_progress(8, "Step 8/8: Verifying flash...")
                    elif "INSTALLATION / UPDATE COMPLETED SUCCESSFULLY" in msg:
                        set_flash_progress(8, "Completed successfully")

                ssh = get_ssh()
                wf = SafetyWorkflow(ssh, log_callback=logged_progress)
                success = wf.verify_and_install(
                    local_tar_path=target_tar,
                    expected_sha256=expected_sha,
                )

                if success:
                    set_flash_progress(8, "Completed successfully")
                    retrieve_installed_version_action(show_dialog=False)
                    messagebox.showinfo(
                        "Installation Complete",
                        "Android Auto has been installed and verified on head unit flash.\n\nRestart iDrive by holding the volume knob for 25 seconds, then open Android Auto from the Media menu.",
                    )
                else:
                    set_flash_progress(0, "Failed: Aborted")
                    messagebox.showerror(
                        "Installation Aborted",
                        "Pre-installation checks or verification failed. Previous head unit state was preserved.",
                    )
            finally:
                root.after(0, lambda: flash_btn.configure(state="normal"))

        threading.Thread(target=_flash_thread, daemon=True).start()

    tk.Label(
        flash_card,
        text="Recommendation: Keep the car engine running during flashing to ensure stable power.",
        bg=BG_PANEL,
        fg=COLOR_AMBER,
        font=("Segoe UI", 9),
    ).pack(anchor="w", pady=(0, 6))

    flash_bar_row = tk.Frame(flash_card, bg=BG_PANEL)
    flash_bar_row.pack(fill="x", pady=4)

    flash_btn = create_btn(
        flash_bar_row,
        "Start Update / Flash",
        start_flashing,
        bg=COLOR_GREEN,
        hover_bg="#2EA043",
        font=("Segoe UI", 10, "bold"),
        padx=16,
        pady=7,
    )
    flash_btn.pack(side="left", padx=(0, 12))

    prog_area = tk.Frame(flash_bar_row, bg=BG_PANEL)
    prog_area.pack(side="left", fill="x", expand=True)

    flash_progressbar = ttk.Progressbar(prog_area, orient="horizontal", mode="determinate", maximum=8)
    flash_progressbar.pack(fill="x", pady=2)

    flash_progress_lbl = tk.Label(prog_area, text="Ready to update", bg=BG_PANEL, fg=COLOR_LIGHT_BLUE, font=("Segoe UI", 8, "bold"))
    flash_progress_lbl.pack(anchor="w")

    # In-Car Live Stream Console
    stream_hdr = tk.Frame(flash_card, bg=BG_PANEL)
    stream_hdr.pack(fill="x", pady=(6, 2))
    tk.Label(stream_hdr, text="In-Car Terminal Execution Trace:", bg=BG_PANEL, fg=FG_TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")

    def clear_hu_stream():
        hu_stream_txt.delete("1.0", tk.END)

    def copy_hu_stream():
        c = hu_stream_txt.get("1.0", tk.END).strip()
        if c:
            root.clipboard_clear()
            root.clipboard_append(c)
            messagebox.showinfo("Copied", "Trace copied to clipboard!")

    create_btn(stream_hdr, "Copy", copy_hu_stream, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B", font=("Segoe UI", 8), padx=6, pady=1).pack(side="right", padx=2)
    create_btn(stream_hdr, "Clear", clear_hu_stream, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B", font=("Segoe UI", 8), padx=6, pady=1).pack(side="right", padx=2)

    hu_stream_txt = scrolledtext.ScrolledText(
        flash_card,
        height=11,
        bg="#05080A",
        fg="#3FB950",
        insertbackground="#3FB950",
        font=("Consolas", 9),
        relief="flat",
        bd=0,
    )
    hu_stream_txt.pack(fill="both", expand=True)
    setup_text_tags(hu_stream_txt)

    def append_hu_stream(msg: str):
        def _ins():
            insert_formatted_line(hu_stream_txt, msg, autoscroll=True)
        root.after(0, _ins)

    GLOBAL_LOGGER.add_listener(append_hu_stream)

    # =========================================================================
    # TAB 2: IDRIVE SETTINGS & FLAGS
    # =========================================================================
    set_container = tk.Frame(tab_settings, bg=BG_DARK, padx=8, pady=8)
    set_container.pack(fill="both", expand=True)

    flags_card = create_card(set_container, "iDrive Configuration Flags", "Saved in /var/local/data/AA", fill="both")
    flags_dict = {key: tk.BooleanVar(value=False) for key in SUPPORTED_FLAGS}

    flags_grid = tk.Frame(flags_card, bg=BG_PANEL)
    flags_grid.pack(fill="both", expand=True, pady=4)
    flags_grid.columnconfigure(0, weight=1)
    flags_grid.columnconfigure(1, weight=1)

    flag_descriptions = {
        "autostart": "Auto-start Android Auto daemon immediately on iDrive boot",
        "usb": "Force USB wired connection (disables Wi-Fi requirement)",
        "entry-direct": "Launch directly into Android Auto without sub-menu navigation",
        "kombi-off": "Disable turn-by-turn navigation arrows in instrument cluster / HUD",
        "kombi-single-maneuver": "Display single maneuver route graph (for clusters rejecting full graphs)",
        "gps-telephone": "Use phone's internal GPS antenna instead of vehicle roof antenna",
    }

    row_idx = 0
    for key, label in SUPPORTED_FLAGS.items():
        col_idx = row_idx % 2
        r = row_idx // 2
        item_box = tk.Frame(flags_grid, bg=BG_CARD, padx=10, pady=8, highlightbackground=BORDER_COLOR, highlightthickness=1)
        item_box.grid(row=r, column=col_idx, sticky="nsew", padx=4, pady=4)

        cb = tk.Checkbutton(
            item_box,
            text=f" {key}",
            variable=flags_dict[key],
            bg=BG_CARD,
            fg=COLOR_LIGHT_BLUE,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
            activeforeground=COLOR_LIGHT_BLUE,
            font=("Segoe UI", 10, "bold"),
        )
        cb.pack(anchor="w")

        desc_text = flag_descriptions.get(key, label)
        tk.Label(item_box, text=desc_text, bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 8), wraplength=420, justify="left").pack(anchor="w", padx=20, pady=(2, 0))
        row_idx += 1

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
        threading.Thread(target=_worker, daemon=True).start()

    def on_uninstall():
        if messagebox.askyesno(
            "Confirm Uninstall",
            "DISCLAIMER: Modifying vehicle head unit software carries inherent risk. You proceed entirely at your own risk and responsibility.\n\nAre you sure you want to completely uninstall EntryNav2 Android Auto from the car?\n\nThis removes /opt/aa, plugins, and configuration flags.",
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
                    GLOBAL_LOGGER.log("OK", "Android Auto uninstalled successfully.")
                    root.after(0, lambda: aa_badge_pill.config(text=" AA: Not Installed ", bg="#3A1515", fg=COLOR_RED))
                else:
                    GLOBAL_LOGGER.log("ERROR", f"Uninstall failed: {err}")
            threading.Thread(target=_worker, daemon=True).start()

    flags_btn_row = tk.Frame(flags_card, bg=BG_PANEL)
    flags_btn_row.pack(fill="x", pady=6)
    create_btn(flags_btn_row, "Read Settings from Car", read_flags, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B").pack(side="left", padx=4)
    create_btn(flags_btn_row, "Save Settings to Car", save_flags, bg=COLOR_GREEN, hover_bg="#2EA043").pack(side="left", padx=6)
    create_btn(flags_btn_row, "Uninstall Android Auto", on_uninstall, bg=COLOR_RED, hover_bg="#B62324").pack(side="right", padx=4)

    # =========================================================================
    # TAB 3: ENET NETWORK DIAGNOSTICS
    # =========================================================================
    net_container = tk.Frame(tab_net, bg=BG_DARK, padx=8, pady=8)
    net_container.pack(fill="both", expand=True)

    net_card = create_card(net_container, "ENET Cable & Network Adapter Check", "Scans Windows Adapters & Pings Car")
    net_info_lbl = tk.Label(net_card, text="Click 'Scan Network & Ping Car' to check physical and IP connection.", bg=BG_PANEL, fg=FG_TEXT, font=("Segoe UI", 9), justify="left")
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

    create_btn(net_card, "Scan Network & Ping Car", scan_network, bg=COLOR_BLUE, hover_bg="#388BFD").pack(anchor="w", pady=6)

    net_guide_card = create_card(net_container, "Hardware Connection Checklist", "Standard OBD2 ENET Setup", fill="both")
    net_guide = scrolledtext.ScrolledText(net_guide_card, height=12, bg=BG_INPUT, fg=FG_TEXT, font=("Consolas", 9), relief="flat", bd=0)
    net_guide.pack(fill="both", expand=True)
    net_guide.insert(
        tk.END,
        """=== ENET OBD2 Hardware & Connection Checklist ===

1. Physical Connection:
   • Plug the OBD2 connector into the driver footwell diagnostic port.
   • Connect the RJ45 Ethernet cable to your PC (or USB-C Ethernet adapter).

2. Network Adapter Configuration:
   • Leave the Ethernet adapter on 'Automatic (DHCP)'.
   • The BMW head unit assigns an automatic private IP (169.254.x.x).
   • Note: Windows may take 10-20 seconds to establish the APIPA link.

3. Default Head Unit Credentials:
   • Head Unit IP: 169.254.1.0
   • Port:         22
   • Username:     root
   • Password:     Entry0?Evo!1
""",
    )

    # =========================================================================
    # TAB 4: DIAGNOSTIC LOGS
    # =========================================================================
    logs_container = tk.Frame(tab_logs, bg=BG_DARK, padx=8, pady=8)
    logs_container.pack(fill="both", expand=True)

    log_status_card = create_card(logs_container, "Head Unit Maintenance Logging", "Controls /var/local/data/AA/maintenance")
    stat_row = tk.Frame(log_status_card, bg=BG_PANEL)
    stat_row.pack(fill="x")

    log_status_lbl = tk.Label(stat_row, text="Logging: Not Checked", bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 10, "bold"))
    log_status_lbl.pack(side="left")

    log_files_lbl = tk.Label(log_status_card, text="Files on car: Not checked", bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 8))
    log_files_lbl.pack(anchor="w", pady=(4, 0))

    log_ctrl_card = create_card(logs_container, "Log Actions", "Retrieve Diagnostic Logs from Car")
    log_ctrl_row = tk.Frame(log_ctrl_card, bg=BG_PANEL)
    log_ctrl_row.pack(fill="x", pady=2)

    def update_log_status_ui():
        def _worker():
            lm = LogManager(get_ssh())
            st = lm.get_logging_status()
            if not st["connected"]:
                root.after(0, lambda: (
                    log_status_lbl.config(text="Logging: Unreachable", fg=COLOR_RED),
                    log_files_lbl.config(text="Could not reach head unit to verify logging state.", fg=FG_MUTED)
                ))
                return
            if st["enabled"]:
                status_str = "Logging: ENABLED (/var/local/data/AA/maintenance active)"
                color = COLOR_GREEN_BRIGHT
            else:
                status_str = "Logging: DISABLED (Normal mode)"
                color = FG_MUTED

            files_str = f"Diagnostic files on car: {', '.join(st['files']) if st['files'] else 'None'}"
            root.after(0, lambda: (
                log_status_lbl.config(text=status_str, fg=color),
                log_files_lbl.config(text=files_str, fg=FG_TEXT)
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

                def _update_view():
                    log_viewer.delete("1.0", tk.END)
                    log_viewer.insert(tk.END, full_text)

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

    create_btn(log_ctrl_row, "Check Status", update_log_status_ui, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B").pack(side="left", padx=3)
    create_btn(log_ctrl_row, "Enable Logging", on_enable_logs, bg=COLOR_GREEN, hover_bg="#2EA043").pack(side="left", padx=3)
    create_btn(log_ctrl_row, "Disable & Clear", on_disable_clear_logs, bg=COLOR_RED, hover_bg="#B62324").pack(side="left", padx=3)
    create_btn(log_ctrl_row, "Pull Logs to PC", on_pull_logs, bg=COLOR_BLUE, hover_bg="#388BFD").pack(side="left", padx=6)
    create_btn(log_ctrl_row, "Open Logs Folder", on_open_folder, bg=BG_CARD, fg=FG_TEXT, hover_bg="#2D333B").pack(side="left", padx=3)

    log_viewer_card = create_card(logs_container, "Pulled Logs Viewer", "Last 100 lines per file", fill="both")
    log_viewer = scrolledtext.ScrolledText(
        log_viewer_card,
        height=12,
        bg=BG_INPUT,
        fg=FG_TEXT,
        font=("Consolas", 9),
        relief="flat",
        bd=0,
    )
    log_viewer.pack(fill="both", expand=True)

    # Tab change listener
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
        f"{r['tag']} ({r['published_at']}) {'[Pre-Release]' if r['prerelease'] else '[Stable]'}"
        for r in BUILTIN_RELEASES
    ]
    rel_combobox["values"] = display_items
    if display_items:
        rel_combobox.current(0)
        on_rel_selected(None)

    # Fetch live releases in background
    fetch_rels()

    root.mainloop()
