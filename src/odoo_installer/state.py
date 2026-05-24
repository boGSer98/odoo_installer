from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from .models import InstallerConfig


class ProgressState:
    def __init__(self, path: Path, config: InstallerConfig, resume: bool) -> None:
        self.path = path
        self.config_hash = _config_hash(config)
        self._completed: set[tuple[int, int]] = set()
        self._load_or_init(resume=resume)

    def _load_or_init(self, resume: bool) -> None:
        if not self.path.exists():
            self._persist()
            return

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        stored_hash = payload.get("config_hash")
        completed = payload.get("completed", [])

        if not resume:
            self._persist()
            return

        if stored_hash != self.config_hash:
            raise RuntimeError(
                "Resume-State passt nicht zur aktuellen Konfiguration. "
                "Bitte ohne --resume starten oder eine passende Konfiguration verwenden."
            )

        self._completed = {
            (int(entry["step_index"]), int(entry["command_index"]))
            for entry in completed
            if "step_index" in entry and "command_index" in entry
        }

    def should_skip(self, step_index: int, command_index: int) -> bool:
        return (step_index, command_index) in self._completed

    def mark_done(self, step_index: int, command_index: int) -> None:
        self._completed.add((step_index, command_index))
        self._persist()

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def _persist(self) -> None:
        payload = {
            "config_hash": self.config_hash,
            "completed": [
                {"step_index": step_index, "command_index": command_index}
                for step_index, command_index in sorted(self._completed)
            ],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _config_hash(config: InstallerConfig) -> str:
    encoded = json.dumps(asdict(config), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
