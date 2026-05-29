from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Palette:
    reset: str = "\033[0m"
    bold: str = "\033[1m"
    dim: str = "\033[2m"
    blue: str = "\033[34m"
    cyan: str = "\033[36m"
    green: str = "\033[32m"
    yellow: str = "\033[33m"
    red: str = "\033[31m"


class TerminalUI:
    """Small dependency-free terminal UI helpers for the customer installer."""

    def __init__(self, *, stream=sys.stdout, force_color: bool | None = None) -> None:  # type: ignore[assignment]
        self.stream = stream
        if force_color is None:
            no_color = os.environ.get("NO_COLOR") is not None
            force = os.environ.get("FORCE_COLOR") in {"1", "true", "yes"}
            force_color = force or (stream.isatty() and not no_color)
        self.color_enabled = force_color
        self.palette = Palette()

    @property
    def width(self) -> int:
        return max(60, min(100, shutil.get_terminal_size((88, 24)).columns))

    def color(self, text: str, color_name: str) -> str:
        if not self.color_enabled:
            return text
        color = getattr(self.palette, color_name)
        return f"{color}{text}{self.palette.reset}"

    def print(self, text: str = "") -> None:
        print(text, file=self.stream)

    def banner(self, title: str, subtitle: str | None = None) -> None:
        line = "═" * (self.width - 2)
        self.print(self.color(f"╔{line}╗", "cyan"))
        self.print(self.color(f"║ {title.center(self.width - 4)} ║", "cyan"))
        if subtitle:
            self.print(self.color(f"║ {subtitle.center(self.width - 4)} ║", "cyan"))
        self.print(self.color(f"╚{line}╝", "cyan"))

    def section(self, title: str, icon: str = "▸") -> None:
        self.print()
        self.print(self.color(f"{icon} {title}", "bold"))
        self.print(self.color("─" * min(self.width, len(title) + 8), "dim"))

    def info(self, text: str) -> None:
        self.print(f"{self.color('ℹ', 'blue')} {text}")

    def success(self, text: str) -> None:
        self.print(f"{self.color('✓', 'green')} {text}")

    def warning(self, text: str) -> None:
        self.print(f"{self.color('!', 'yellow')} {text}")

    def error(self, text: str) -> None:
        self.print(f"{self.color('✗', 'red')} {text}")

    def key_values(self, values: dict[str, object]) -> None:
        if not values:
            return
        key_width = min(30, max(len(str(key)) for key in values))
        for key, value in values.items():
            label = self.color(str(key).ljust(key_width), "dim")
            self.print(f"  {label} : {value}")

    def checklist(self, items: list[tuple[str, bool]]) -> None:
        for label, active in items:
            marker = self.color("●", "green") if active else self.color("○", "dim")
            self.print(f"  {marker} {label}")

    def command_status(self, step_name: str, command_index: int, command_count: int) -> None:
        self.info(f"{step_name}: Kommando {command_index}/{command_count}")


ui = TerminalUI()
