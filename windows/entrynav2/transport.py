# Copyright (c) 2026 Jiraiya43 / EntryNav2 Community
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""High-performance, transparent SSH and SFTP transport layer for BMW EntryNav2."""

import os
import platform
import re
import shutil
import socket
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from .askpass import ensure_windows_askpass

try:
    import paramiko
    HAVE_PARAMIKO = True
except ImportError:
    HAVE_PARAMIKO = False

DEFAULT_IP = "169.254.1.0"
DEFAULT_USER = "root"
DEFAULT_PASS = "Entry0?Evo!1"
DEFAULT_PORT = 22


def find_windows_binary(name: str) -> str:
    """Locate OpenSSH binary on Windows, checking System32 and Sysnative paths."""
    if platform.system() != "Windows":
        return name
    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
    candidates = [
        Path(sys_root) / "System32" / "OpenSSH" / f"{name}.exe",
        Path(sys_root) / "Sysnative" / "OpenSSH" / f"{name}.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    w = shutil.which(name)
    return w if w else name


class EventLogger:
    """Thread-safe event logger dispatching timestamped lines to listeners and session files."""

    def __init__(self):
        self._listeners = []
        self._lock = threading.Lock()
        self._file_handle = None
        self._init_session_file()

    def _init_session_file(self):
        try:
            log_dir = Path("BMW_Logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = log_dir / f"session_{ts}.log"
            self._file_handle = open(log_path, "a", encoding="utf-8")
        except Exception:
            self._file_handle = None

    def add_listener(self, callback):
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_listener(self, callback):
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def log(self, tag: str, message: str):
        """Format and broadcast a log line."""
        ts = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{ts}] [{tag}] {message}"
        with self._lock:
            if self._file_handle:
                try:
                    self._file_handle.write(formatted + "\n")
                    self._file_handle.flush()
                except Exception:
                    pass
            for cb in list(self._listeners):
                try:
                    cb(formatted)
                except Exception:
                    pass


# Global singleton logger
GLOBAL_LOGGER = EventLogger()


class SSHClientWrapper:
    """Transparent SSH & SFTP client wrapper supporting both Paramiko and OpenSSH."""

    def __init__(
        self,
        host: str = DEFAULT_IP,
        user: str = DEFAULT_USER,
        password: str = DEFAULT_PASS,
        port: int = DEFAULT_PORT,
        logger: EventLogger | None = None
    ):
        self.host = host.strip()
        self.user = user.strip()
        self.password = password
        self.port = int(port)
        self.logger = logger or GLOBAL_LOGGER
        self.is_windows = platform.system() == "Windows"
        self._askpass_file = None
        self._paramiko_client = None
        self._lock = threading.Lock()

    def _log(self, tag: str, message: str):
        if self.logger:
            self.logger.log(tag, message)

    def _get_ssh_env(self) -> dict:
        env = os.environ.copy()
        env["ENTRYNAV2_PASSWORD"] = self.password
        if self.is_windows:
            if not self._askpass_file:
                self._askpass_file = ensure_windows_askpass()
            if self._askpass_file and os.path.exists(self._askpass_file):
                env["SSH_ASKPASS"] = self._askpass_file
                env["SSH_ASKPASS_REQUIRE"] = "force"
                env["DISPLAY"] = "entrynav2:0"
        return env

    def _get_paramiko_client(self, timeout: float = 6.0):
        """Get or create an active Paramiko SSH client with connection pooling."""
        if not HAVE_PARAMIKO:
            return None

        with self._lock:
            if self._paramiko_client is not None:
                transport = self._paramiko_client.get_transport()
                if transport and transport.is_active():
                    return self._paramiko_client
                try:
                    self._paramiko_client.close()
                except Exception:
                    pass
                self._paramiko_client = None

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    timeout=timeout,
                    banner_timeout=10,
                    auth_timeout=6,
                    look_for_keys=False,
                    allow_agent=False
                )
                self._paramiko_client = client
                return self._paramiko_client
            except Exception as e:
                try:
                    client.close()
                except Exception:
                    pass
                raise e

    def test_connection(self, timeout: float = 3.0) -> tuple[bool, str]:
        """Test quick TCP socket reachability on port 22."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((self.host, self.port))
            s.close()
            return True, "Port reachable"
        except socket.timeout:
            return False, f"Connection to {self.host}:{self.port} timed out"
        except ConnectionRefusedError:
            return False, f"Connection to {self.host}:{self.port} refused"
        except Exception as e:
            return False, f"Connection failed: {e}"

    def run_command(self, cmd: str, timeout: int = 60, line_cb=None) -> tuple[int, str, str]:
        """Execute a remote command over SSH with transparent command logging and live streaming."""
        clean_cmd = cmd.strip()
        self._log("CMD >>", f'ssh {self.user}@{self.host}:{self.port} "{clean_cmd}"')

        # 1. Primary: Paramiko
        if HAVE_PARAMIKO:
            try:
                client = self._get_paramiko_client(timeout=8.0)
                channel = client.get_transport().open_session()
                channel.settimeout(timeout)
                channel.exec_command(clean_cmd)

                out_lines = []
                err_lines = []

                # Stream stdout and stderr cooperatively
                stdout_f = channel.makefile("r", 1)
                stderr_f = channel.makefile_stderr("r", 1)

                def read_stdout():
                    for line in iter(stdout_f.readline, ""):
                        out_lines.append(line)
                        l = line.rstrip("\r\n")
                        if l:
                            self._log("HU <<", l)
                            if line_cb:
                                line_cb(l)

                def read_stderr():
                    for line in iter(stderr_f.readline, ""):
                        err_lines.append(line)
                        l = line.rstrip("\r\n")
                        if l:
                            self._log("HU <<", l)
                            if line_cb:
                                line_cb(l)

                t_out = threading.Thread(target=read_stdout, daemon=True)
                t_err = threading.Thread(target=read_stderr, daemon=True)
                t_out.start()
                t_err.start()
                t_out.join()
                t_err.join()

                code = channel.recv_exit_status()
                channel.close()

                status_str = "Success" if code == 0 else f"Code {code}"
                self._log("EXIT", f"Command finished -> {status_str}")
                return code, "".join(out_lines), "".join(err_lines)
            except (socket.timeout, paramiko.SSHException, socket.error) as pe:
                # If network connection is definitively refused or timed out, report directly
                err_text = str(pe)
                if "refused" in err_text.lower() or "timed out" in err_text.lower() or "unreachable" in err_text.lower():
                    self._log("HU <<", f"ssh: connect to host {self.host} port {self.port}: {err_text}")
                    self._log("EXIT", f"Return code: 255 (Host unreachable or connection refused at {self.host})")
                    return 255, "", err_text
                # If crypto/cipher mismatch or other Paramiko anomaly, fall back to OpenSSH binary
                self._log("WARN", f"Paramiko session issue ({pe}), falling back to OpenSSH...")

        # 2. Fallback: OpenSSH subprocess
        env = self._get_ssh_env()
        ssh_bin = find_windows_binary("ssh")

        args = [
            ssh_bin,
            "-p", str(self.port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=" + ("NUL" if self.is_windows else "/dev/null"),
            "-o", "ConnectTimeout=6",
            "-o", "BatchMode=no",
            "-o", "LogLevel=ERROR",
            f"{self.user}@{self.host}",
            clean_cmd
        ]

        try:
            proc = subprocess.Popen(
                args,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                stdin=subprocess.DEVNULL
            )
            out_acc = []
            err_acc = []

            def read_pipe(pipe, acc):
                for line in iter(pipe.readline, ''):
                    acc.append(line)
                    l = line.rstrip("\r\n")
                    if l:
                        self._log("HU <<", l)
                        if line_cb:
                            line_cb(l)
                pipe.close()

            t1 = threading.Thread(target=read_pipe, args=(proc.stdout, out_acc), daemon=True)
            t2 = threading.Thread(target=read_pipe, args=(proc.stderr, err_acc), daemon=True)
            t1.start()
            t2.start()

            proc.wait(timeout=timeout)
            t1.join()
            t2.join()

            code = proc.returncode
            if code == 0:
                self._log("EXIT", "Return code: 0 (Success)")
            elif code == 255:
                self._log("EXIT", f"Return code: 255 (Host unreachable or connection refused at {self.host})")
            else:
                self._log("EXIT", f"Return code: {code}")

            return code, "".join(out_acc), "".join(err_acc)
        except subprocess.TimeoutExpired:
            proc.kill()
            self._log("EXIT", f"Return code: -1 (Command timed out after {timeout}s)")
            return -1, "".join(out_acc), f"Connection or command timed out after {timeout}s."
        except FileNotFoundError:
            self._log("ERROR", f"OpenSSH client binary ({ssh_bin}) not found.")
            return -2, "", f"OpenSSH client ({ssh_bin}) not found on system."
        except Exception as e:
            self._log("ERROR", f"SSH Execution Exception: {e}")
            return -3, "", str(e)

    def scp_upload(
        self,
        local_file: str,
        remote_dest: str,
        timeout: int = 180,
        progress_cb=None
    ) -> tuple[int, str, str]:
        """Upload a file using Paramiko SFTP (native) or OpenSSH scp with speed metrics."""
        size_bytes = os.path.getsize(local_file) if os.path.exists(local_file) else 0
        size_str = f"{size_bytes / (1024 * 1024):.2f} MB" if size_bytes >= 1024 * 1024 else f"{size_bytes / 1024:.1f} KB"
        filename = Path(local_file).name
        self._log("SCP >>", f"Uploading {filename} ({size_str}) -> {self.user}@{self.host}:{remote_dest}")

        t0 = time.time()

        # 1. Primary: Paramiko SFTP
        if HAVE_PARAMIKO:
            try:
                client = self._get_paramiko_client(timeout=10.0)
                sftp = client.open_sftp()
                remote_target = remote_dest
                if remote_dest.endswith("/"):
                    remote_target = remote_dest + filename

                def sftp_callback(transferred, total):
                    if progress_cb and total > 0:
                        progress_cb(transferred, total)

                sftp.put(local_file, remote_target, callback=sftp_callback)
                sftp.close()

                elapsed = max(0.1, time.time() - t0)
                speed_mb = (size_bytes / (1024 * 1024)) / elapsed
                self._log("SCP <<", f"Upload complete in {elapsed:.1f}s ({speed_mb:.2f} MB/s) -> Success (Code 0)")
                return 0, "", ""
            except Exception as e:
                self._log("WARN", f"Paramiko SFTP upload issue ({e}), trying OpenSSH scp...")

        # 2. Fallback: OpenSSH scp
        env = self._get_ssh_env()
        scp_bin = find_windows_binary("scp")
        args = [
            scp_bin,
            "-P", str(self.port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=" + ("NUL" if self.is_windows else "/dev/null"),
            "-o", "ConnectTimeout=10",
            "-o", "LogLevel=ERROR",
            local_file,
            f"{self.user}@{self.host}:{remote_dest}"
        ]

        try:
            proc = subprocess.run(
                args,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL
            )
            elapsed = max(0.1, time.time() - t0)
            speed_mb = (size_bytes / (1024 * 1024)) / elapsed
            if proc.returncode == 0:
                self._log("SCP <<", f"Upload complete in {elapsed:.1f}s ({speed_mb:.2f} MB/s) -> Success (Code 0)")
            else:
                self._log("SCP <<", f"Upload failed in {elapsed:.1f}s (Code {proc.returncode}): {proc.stderr.strip()}")
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            self._log("SCP <<", f"Upload timed out after {timeout}s.")
            return -1, "", "SCP upload timed out."
        except Exception as e:
            self._log("SCP <<", f"Upload error: {e}")
            return -3, "", str(e)

    def scp_download(
        self,
        remote_file: str,
        local_dest: str,
        timeout: int = 60,
        progress_cb=None
    ) -> tuple[int, str, str]:
        """Download a file using Paramiko SFTP or OpenSSH scp."""
        self._log("SCP >>", f"Downloading {remote_file} -> {local_dest}")
        t0 = time.time()

        # 1. Primary: Paramiko SFTP
        if HAVE_PARAMIKO:
            try:
                client = self._get_paramiko_client(timeout=10.0)
                sftp = client.open_sftp()

                def sftp_cb(transferred, total):
                    if progress_cb and total > 0:
                        progress_cb(transferred, total)

                sftp.get(remote_file, local_dest, callback=sftp_cb)
                sftp.close()

                elapsed = max(0.1, time.time() - t0)
                downloaded_bytes = os.path.getsize(local_dest) if os.path.exists(local_dest) else 0
                self._log("SCP <<", f"Download complete in {elapsed:.1f}s ({downloaded_bytes} bytes) -> Success (Code 0)")
                return 0, "", ""
            except Exception as e:
                self._log("WARN", f"Paramiko SFTP download issue ({e}), trying OpenSSH scp...")

        # 2. Fallback: OpenSSH scp
        env = self._get_ssh_env()
        scp_bin = find_windows_binary("scp")
        args = [
            scp_bin,
            "-P", str(self.port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=" + ("NUL" if self.is_windows else "/dev/null"),
            "-o", "ConnectTimeout=10",
            "-o", "LogLevel=ERROR",
            f"{self.user}@{self.host}:{remote_file}",
            local_dest
        ]

        try:
            proc = subprocess.run(
                args,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL
            )
            elapsed = max(0.1, time.time() - t0)
            downloaded_bytes = os.path.getsize(local_dest) if os.path.exists(local_dest) else 0
            if proc.returncode == 0:
                self._log("SCP <<", f"Download complete in {elapsed:.1f}s ({downloaded_bytes} bytes) -> Success (Code 0)")
            else:
                self._log("SCP <<", f"Download failed (Code {proc.returncode}): {proc.stderr.strip()}")
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            self._log("SCP <<", f"Download timed out after {timeout}s.")
            return -1, "", "SCP download timed out."
        except Exception as e:
            self._log("SCP <<", f"Download error: {e}")
            return -3, "", str(e)

    def launch_interactive_shell(self) -> bool:
        """Launch an interactive root shell with autologin in a dedicated terminal window."""
        self._log("CMD >>", f"Opening interactive autologin terminal to {self.user}@{self.host}:{self.port}...")
        if self.is_windows:
            askpass_path = ensure_windows_askpass()
            putty = shutil.which("putty.exe")
            if putty:
                cmd = f'"{putty}" -ssh {self.user}@{self.host} {self.port} -pw "{self.password}"'
                subprocess.Popen(cmd, shell=True)
                self._log("OK", "Launched PuTTY SSH session with autologin.")
                return True

            script = (
                f'$env:ENTRYNAV2_PASSWORD="{self.password}"; '
                f'$env:SSH_ASKPASS="{askpass_path}"; '
                f'$env:SSH_ASKPASS_REQUIRE="force"; '
                f'Write-Host "==========================================================" -ForegroundColor Cyan; '
                f'Write-Host " Connected to BMW EntryNav2 at {self.host} as root" -ForegroundColor Green; '
                f'Write-Host " Password was authenticated automatically via ASKPASS." -ForegroundColor Green; '
                f'Write-Host " Type exit to disconnect." -ForegroundColor Gray; '
                f'Write-Host "==========================================================" -ForegroundColor Cyan; '
                f'ssh -p {self.port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL {self.user}@{self.host}'
            )
            cmd = f'start powershell.exe -NoExit -Command "{script}"'
            subprocess.Popen(cmd, shell=True)
            self._log("OK", "Launched PowerShell SSH session with autologin.")
            return True
        else:
            terminals = ["x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "xterm"]
            for term in terminals:
                if shutil.which(term):
                    if shutil.which("sshpass"):
                        subprocess.Popen([term, "-e", f"sshpass -p '{self.password}' ssh -p {self.port} -o StrictHostKeyChecking=no {self.user}@{self.host}"])
                    else:
                        subprocess.Popen([term, "-e", f"ssh -p {self.port} -o StrictHostKeyChecking=no {self.user}@{self.host}"])
                    self._log("OK", f"Launched terminal {term}.")
                    return True
            self._log("INFO", f"Run manually: ssh -p {self.port} {self.user}@{self.host} (Password: {self.password})")
            return False

    def close(self):
        """Close active Paramiko connections."""
        with self._lock:
            if self._paramiko_client:
                try:
                    self._paramiko_client.close()
                except Exception:
                    pass
                self._paramiko_client = None
