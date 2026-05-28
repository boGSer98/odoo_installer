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


class LocalExecutor:
    """Fuehrt Kommandos lokal per bash aus."""

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def run(self, local_command: str) -> CommandResult:
        command = ["bash", "-lc", local_command]
        if self.dry_run:
            rendered = " ".join(shlex.quote(part) for part in command)
            return CommandResult(
                command=command,
                returncode=0,
                stdout=f"[DRY-RUN][LOCAL] {rendered}\n",
                stderr="",
            )
        proc = subprocess.run(command, capture_output=True, text=True)
        return CommandResult(
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )

    def close(self) -> None:
        return


# Rueckwaertskompatibilitaet fuer bestehende Imports.
SSHExecutor = LocalExecutor
