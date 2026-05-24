from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .models import InstallerConfig
from .pipeline import run_installation
from .prompts import collect_config
from .state import ProgressState
from .ssh import SSHExecutor


def _load_config(path: Path) -> InstallerConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    config = InstallerConfig(**data)
    return config


def _save_config(path: Path, config: InstallerConfig) -> None:
    path.write_text(json.dumps(config.__dict__, indent=2), encoding="utf-8")


def _print_summary(config: InstallerConfig) -> None:
    print("\nKonfigurationsuebersicht:")
    for key, value in config.safe_dict().items():
        print(f"- {key}: {value}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="odoo-installer",
        description="Gefuehrte Installation von Odoo auf entfernten Ubuntu-24.04-Servern via SSH.",
    )
    parser.add_argument("--config", type=Path, help="Pfad zu einer JSON-Konfigurationsdatei.")
    parser.add_argument("--save-config", type=Path, help="Optionaler Pfad zum Speichern der Konfiguration.")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, welche Kommandos ausgefuehrt werden.")
    parser.add_argument("--resume", action="store_true", help="Abgebrochene Installation anhand der State-Datei fortsetzen.")
    parser.add_argument(
        "--rollback-on-fail",
        action="store_true",
        help="Bei Fehlern einen best-effort Rollback fuer unterstuetzte Schritte ausfuehren.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path(".odoo-installer-state.json"),
        help="Pfad zur lokalen State-Datei fuer Resume.",
    )
    parser.add_argument("--yes", action="store_true", help="Rueckfrage zur Ausfuehrung ueberspringen.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        if args.config:
            config = _load_config(args.config)
            if args.dry_run:
                config.dry_run = True
        else:
            config = collect_config(default_dry_run=args.dry_run)

        config.validate_or_raise()

        if args.save_config:
            _save_config(args.save_config, config)
            print(f"Konfiguration gespeichert: {args.save_config}")

        _print_summary(config)

        if not args.yes:
            confirm = input("\nInstallation starten? (j/n) [j]: ").strip().lower()
            if confirm not in {"", "j", "ja", "y", "yes"}:
                print("Abgebrochen.")
                return 0

        executor = SSHExecutor(
            host=config.host,
            user=config.ssh_user,
            port=config.ssh_port,
            ssh_key_path=config.ssh_key_path,
            dry_run=config.dry_run,
        )
        progress = None if config.dry_run else ProgressState(args.state_file, config, resume=args.resume)
        run_installation(executor, config, progress=progress, rollback_on_fail=args.rollback_on_fail)
        if progress:
            progress.clear()
        print("\nInstallation abgeschlossen.")
        return 0
    except KeyboardInterrupt:
        print("\nAbbruch durch Benutzer.")
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"\nFehler: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
