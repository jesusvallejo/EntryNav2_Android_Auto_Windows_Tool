#!/usr/bin/env python3
# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""EntryNav2 Android Auto Windows Manager & Flashing Tool (Entry Point).

Supports full GUI execution and automated non-interactive CLI workflows.
"""

import argparse
import sys
from pathlib import Path

# Ensure this script's directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from entrynav2.config import CarConfigManager
from entrynav2.diagnostics import LogManager
from entrynav2.network import NetworkDiagnostics
from entrynav2.safety import SafetyWorkflow
from entrynav2.transport import (
    DEFAULT_IP,
    DEFAULT_PASS,
    DEFAULT_PORT,
    DEFAULT_USER,
    GLOBAL_LOGGER,
    SSHClientWrapper,
)
from entrynav2.ui import run_gui


def main():
    parser = argparse.ArgumentParser(
        description="EntryNav2 Android Auto Windows Manager & Flashing Tool v2.0"
    )
    parser.add_argument("--ip", default=DEFAULT_IP, help=f"Car IP address (default: {DEFAULT_IP})")
    parser.add_argument("--user", default=DEFAULT_USER, help=f"SSH username (default: {DEFAULT_USER})")
    parser.add_argument("--password", default=DEFAULT_PASS, help=f"SSH password (default: {DEFAULT_PASS})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"SSH port (default: {DEFAULT_PORT})")

    parser.add_argument("--cli", action="store_true", help="Run in CLI mode without launching GUI")
    parser.add_argument(
        "--version-id", "--installed-version", "--aa-version",
        dest="version_id",
        action="store_true",
        help="Retrieve installed Android Auto version and car firmware"
    )
    parser.add_argument(
        "--log-status", "--check-logs",
        action="store_true",
        help="Check if maintenance logging is currently enabled on the car"
    )
    parser.add_argument("--check", action="store_true", help="Check car connectivity, space, and running processes")
    parser.add_argument("--shell", action="store_true", help="Launch interactive root shell with autologin")
    parser.add_argument("--reboot", action="store_true", help="Reboot the BMW head unit over SSH")
    parser.add_argument("--update", help="Update car using specified local .tar file or release tag")
    parser.add_argument("--sha256", help="Expected SHA-256 digest for the update archive")
    parser.add_argument("--pull-logs", action="store_true", help="Pull logs from car to local directory")
    parser.add_argument("--wifi-diag", action="store_true", help="Analyze Wi-Fi link diagnostics from pulled logs")
    parser.add_argument("--enable-logs", action="store_true", help="Enable maintenance logging on car")
    parser.add_argument("--disable-logs", action="store_true", help="Disable and clear logs on car")
    parser.add_argument("--net-check", "--ping", dest="net_check", action="store_true", help="Inspect local ENET adapters and ping car")
    parser.add_argument("--model", default="", help="Vehicle model (e.g. 320d)")
    parser.add_argument("--year", default="", help="Vehicle year (e.g. 2020)")

    args = parser.parse_args()

    # Launch GUI if no specific action argument was passed
    has_action = (
        args.cli or args.version_id or args.log_status or args.check or
        args.shell or args.reboot or args.update or args.pull_logs or
        args.wifi_diag or args.enable_logs or args.disable_logs or args.net_check
    )

    if not has_action:
        try:
            run_gui()
            return
        except Exception as e:
            print(f"GUI launch failed ({e}), falling back to CLI help.")
            parser.print_help()
            sys.exit(1)

    GLOBAL_LOGGER.add_listener(lambda line: print(line))
    ssh = SSHClientWrapper(host=args.ip, user=args.user, password=args.password, port=args.port, logger=GLOBAL_LOGGER)

    if args.net_check:
        print("\n" + "=" * 60)
        print("ENET NETWORK & ADAPTER DIAGNOSTICS")
        print("=" * 60)
        summary = NetworkDiagnostics.get_adapter_summary()
        ping_ok, ping_msg = NetworkDiagnostics.ping_host(args.ip)
        print(f"Status:             {summary['recommendation']}")
        print(f"Car Ping Response:  {ping_msg}")
        print(f"Active Adapters:    {len(summary['active_adapters'])}")
        for ad in summary["active_adapters"]:
            print(f"  • {ad.get('name', 'Adapter')}: {ad.get('ip', 'N/A')}")
        print("=" * 60 + "\n")
        sys.exit(0 if ping_ok else 1)

    if args.version_id:
        wf = SafetyWorkflow(ssh)
        info = wf.get_installed_version_info()
        print("\n" + "=" * 60)
        print("ANDROID AUTO INSTALLED VERSION REPORT")
        print("=" * 60)
        print(f"Car IP:                 {args.ip}")
        if not info["connected"]:
            print("Connection Status:      OFFLINE / UNREACHABLE")
            print(f"Error Detail:           {info.get('raw_output', 'Host unreachable')}")
        else:
            print(f"Android Auto Status:    {'INSTALLED & READY' if info['installed'] else 'NOT INSTALLED'}")
            print(f"Android Auto Version:   {info['version']}")
            print(f"Detection Method:       {info['detection_method']}")
            if info["installed"]:
                print(f"entry-aad MD5:          {info['entry_aad_md5'] or 'N/A'}")
                print(f"aa-supervisor MD5:      {info['aa_supervisor_md5'] or 'N/A'}")
                print(f"libEntryAad.so MD5:     {info['lib_entry_aad_md5'] or 'N/A'}")
            print(f"Running Processes:      {info['running_pids'] or 'None (Stopped)'}")
            print(f"Car iDrive Firmware:    {info['hu_firmware']}")
            print(f"Vehicle Profile:        Model: {info['vehicle_model'] or 'iDrive (default)'}, Year: {info['vehicle_year'] or '2019'}")
        print("=" * 60 + "\n")
        sys.exit(0 if info["connected"] else 1)

    if args.log_status:
        lm = LogManager(ssh)
        st = lm.get_logging_status()
        print("\n" + "=" * 60)
        print("CAR MAINTENANCE LOGGING STATUS")
        print("=" * 60)
        print(f"Car IP:               {args.ip}")
        print(f"Connection Status:    {'CONNECTED' if st['connected'] else 'OFFLINE / UNREACHABLE'}")
        print(f"Maintenance Logging:  {st['status_text']}")
        print(f"Flag Path:            {st['flag_file']}")
        print(f"Diagnostic Files:     {', '.join(st['files']) if st['files'] else 'None found on head unit'}")
        print("=" * 60 + "\n")
        sys.exit(0 if st["connected"] else 1)

    if args.reboot:
        print(f"Transmitting reboot command to car at {args.ip}...")
        ssh.run_command("reboot")
        return

    if args.shell:
        ssh.launch_interactive_shell()
        return

    if args.check:
        wf = SafetyWorkflow(ssh)
        res = wf.run_preflight_checks()
        sys.exit(0 if (res["connected"] and not res["error"]) else 1)

    if args.enable_logs:
        lm = LogManager(ssh)
        ok = lm.enable_logs()
        sys.exit(0 if ok else 1)

    if args.disable_logs:
        lm = LogManager(ssh)
        ok = lm.disable_and_clear_logs()
        sys.exit(0 if ok else 1)

    if args.pull_logs or args.wifi_diag:
        lm = LogManager(ssh)
        ok, pulled_dir, data = lm.pull_logs()
        if ok and data.get("wifi_analysis", {}).get("detected"):
            w = data["wifi_analysis"]
            print("\n" + "=" * 60)
            print("WI-FI LINK DIAGNOSTIC ANALYSIS")
            print("=" * 60)
            print(f"Summary:     {w.get('summary')}")
            print(f"Diagnosis:   {w.get('diagnosis')}")
            print(f"Total Lost:  {w.get('total_lost_frames')} frames | Total Retries: {w.get('total_retries')}")
            print("=" * 60 + "\n")
        sys.exit(0 if ok else 1)

    if args.update:
        if not args.sha256:
            print("Error: --sha256 is required when updating via CLI to guarantee archive integrity.")
            sys.exit(1)
        wf = SafetyWorkflow(ssh)
        success = wf.verify_and_install(
            local_tar_path=args.update,
            expected_sha256=args.sha256,
            vehicle_model=args.model,
            vehicle_year=args.year
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
