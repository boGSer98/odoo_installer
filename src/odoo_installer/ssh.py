from __future__ import annotations

from dataclasses import dataclass
import os
import shlex
import subprocess
from typing import Any


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class SSHExecutor:
    def __init__(
        self,
        host: str,
        user: str,
        port: int = 22,
        ssh_key_path: str | None = None,
        ssh_password: str | None = None,
        host_key_mode: str = "accept-new",
        dry_run: bool = False,
        connect_timeout: int = 12,
    ) -> None:
        self.host = host
        self.user = user
        self.port = port
        self.ssh_key_path = ssh_key_path
        self.ssh_password = ssh_password
        self.host_key_mode = host_key_mode
        self.dry_run = dry_run
        self.connect_timeout = connect_timeout
        self._paramiko_client: Any | None = None

    def _null_known_hosts_target(self) -> str:
        return "NUL" if os.name == "nt" else "/dev/null"

    def _build_ssh_base(self) -> list[str]:
        command = [
            "ssh",
            "-p",
            str(self.port),
            "-o",
            f"ConnectTimeout={self.connect_timeout}",
        ]

        if self.host_key_mode == "strict":
            command.extend(["-o", "StrictHostKeyChecking=yes"])
        elif self.host_key_mode == "accept-new":
            command.extend(["-o", "StrictHostKeyChecking=accept-new"])
        elif self.host_key_mode == "insecure":
            command.extend(["-o", "StrictHostKeyChecking=no"])
            command.extend(["-o", f"UserKnownHostsFile={self._null_known_hosts_target()}"])

        if self.ssh_password:
            command.extend(["-o", "BatchMode=no"])
            command.extend(["-o", "PreferredAuthentications=password,keyboard-interactive,publickey"])
        else:
            command.extend(["-o", "BatchMode=yes"])

        if self.ssh_key_path:
            command.extend(["-i", self.ssh_key_path, "-o", "IdentitiesOnly=yes"])

        command.append(f"{self.user}@{self.host}")
        return command

    def _ensure_paramiko_client(self) -> Any:
        if self._paramiko_client is not None:
            return self._paramiko_client

        try:
            import paramiko  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "SSH-Passwortmodus benoetigt das Python-Paket 'paramiko'. "
                "Bitte lokal installieren: pip install paramiko"
            ) from exc

        client = paramiko.SSHClient()
        if self.host_key_mode == "strict":
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        elif self.host_key_mode == "accept-new":
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(
            hostname=self.host,
            port=self.port,
            username=self.user,
            password=self.ssh_password,
            key_filename=self.ssh_key_path,
            timeout=self.connect_timeout,
            auth_timeout=self.connect_timeout,
            banner_timeout=self.connect_timeout,
            look_for_keys=not bool(self.ssh_password),
            allow_agent=not bool(self.ssh_password),
        )
        self._paramiko_client = client
        return client

    def _run_with_paramiko(self, remote_command: str) -> CommandResult:
        try:
            client = self._ensure_paramiko_client()
            wrapped = f"bash -lc {shlex.quote(remote_command)}"
            stdin, stdout, stderr = client.exec_command(wrapped)
            _ = stdin
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            returncode = int(stdout.channel.recv_exit_status())
            return CommandResult(
                command=["paramiko", wrapped],
                returncode=returncode,
                stdout=out,
                stderr=err,
            )
        except Exception as exc:  # noqa: BLE001
            return CommandResult(
                command=["paramiko", remote_command],
                returncode=255,
                stdout="",
                stderr=str(exc),
            )

    def run(self, remote_command: str) -> CommandResult:
        wrapped = f"bash -lc {shlex.quote(remote_command)}"
        command = [*self._build_ssh_base(), wrapped]
        if self.dry_run:
            rendered = " ".join(shlex.quote(part) for part in command)
            return CommandResult(command=command, returncode=0, stdout=f"[DRY-RUN] {rendered}\n", stderr="")

        if self.ssh_password:
            return self._run_with_paramiko(remote_command)

        proc = subprocess.run(command, capture_output=True, text=True)
        return CommandResult(
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    def close(self) -> None:
        if self._paramiko_client is not None:
            try:
                self._paramiko_client.close()
            finally:
                self._paramiko_client = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:  # noqa: BLE001
            pass
