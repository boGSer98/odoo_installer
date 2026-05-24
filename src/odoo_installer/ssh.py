from __future__ import annotations

from dataclasses import dataclass
import shlex
import subprocess


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
        dry_run: bool = False,
        connect_timeout: int = 12,
    ) -> None:
        self.host = host
        self.user = user
        self.port = port
        self.ssh_key_path = ssh_key_path
        self.dry_run = dry_run
        self.connect_timeout = connect_timeout

    def _build_ssh_base(self) -> list[str]:
        command = [
            "ssh",
            "-p",
            str(self.port),
            "-o",
            f"ConnectTimeout={self.connect_timeout}",
            "-o",
            "BatchMode=yes",
        ]
        if self.ssh_key_path:
            command.extend(["-i", self.ssh_key_path, "-o", "IdentitiesOnly=yes"])
        command.append(f"{self.user}@{self.host}")
        return command

    def run(self, remote_command: str) -> CommandResult:
        wrapped = f"bash -lc {shlex.quote(remote_command)}"
        command = [*self._build_ssh_base(), wrapped]
        if self.dry_run:
            rendered = " ".join(shlex.quote(part) for part in command)
            return CommandResult(command=command, returncode=0, stdout=f"[DRY-RUN] {rendered}\n", stderr="")
        proc = subprocess.run(command, capture_output=True, text=True)
        return CommandResult(
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
