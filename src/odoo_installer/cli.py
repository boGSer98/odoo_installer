from __future__ import annotations

import argparse
from dataclasses import asdict
from getpass import getpass
import json
from pathlib import Path
from .backup_restore import run_backup, run_restore
from .models import InstallerConfig
from .pipeline import run_installation
from .prompts import collect_config
from .state import ProgressState
from .ssh import SSHExecutor
from .ui import ui


def _load_config(path: Path) -> InstallerConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    config = InstallerConfig(**data)
    return config


def _save_config(path: Path, config: InstallerConfig) -> None:
    payload = asdict(config)
    # SSH-Passwort absichtlich nicht persistent speichern.
    payload["ssh_password"] = ""
    # Private SSH-Keys sollen nicht in Konfigurationsdateien landen.
    payload["support_ssh_private_key_path"] = ""
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _print_summary(config: InstallerConfig) -> None:
    ui.section("Konfigurationsuebersicht", "✓")
    ui.key_values(config.safe_dict())
    ui.section("Installationsumfang", "→")
    ui.checklist(
        [
            ("Odoo + PostgreSQL + Systemd-Service", True),
            ("Nginx Reverse Proxy", config.enable_nginx),
            ("Let's Encrypt Zertifikat", config.enable_certbot),
            ("UFW Firewall-Basisregeln", config.enable_ufw),
            ("AHD Support-SSH-Zugang", config.enable_support_ssh),
        ]
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="odoo-installer",
        description="Gefuehrte Installation von Odoo auf entfernten Ubuntu-24.04-Servern via SSH.",
    )
    parser.add_argument("--config", type=Path, help="Pfad zu einer JSON-Konfigurationsdatei.")
    parser.add_argument("--save-config", type=Path, help="Optionaler Pfad zum Speichern der Konfiguration.")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, welche Kommandos ausgefuehrt werden.")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Kommandos direkt auf diesem System ausfuehren, ohne SSH-Verbindung aufzubauen.",
    )
    parser.add_argument(
        "--ask-ssh-password",
        action="store_true",
        help="SSH-Passwort interaktiv abfragen (nicht in Konfig speichern).",
    )
    parser.add_argument(
        "--ssh-host-key-mode",
        choices=["strict", "accept-new", "insecure"],
        help="Ueberschreibt den Host-Key-Modus aus der Konfiguration.",
    )
    operation_group = parser.add_mutually_exclusive_group()
    operation_group.add_argument("--backup", action="store_true", help="Remote-Datenbankbackup erstellen.")
    operation_group.add_argument(
        "--restore",
        metavar="REMOTE_BACKUP_PATH",
        help="Remote-Backupdatei in die konfigurierte Odoo-Datenbank einspielen.",
    )
    parser.add_argument("--backup-dir", help="Zielverzeichnis auf dem Server fuer Backups.")
    parser.add_argument("--backup-name", help="Dateiname fuer das Backup (optional, inkl. Endung).")
    parser.add_argument(
        "--backup-keep-last",
        type=int,
        help="Loescht nach erfolgreichem Backup aeltere DB-Backups und behaelt nur die letzten N (namensbasiert).",
    )
    parser.add_argument(
        "--backup-format",
        choices=["zip", "dump"],
        default="zip",
        help="Backup-Format fuer `db dump` (Standard: zip).",
    )
    parser.add_argument(
        "--no-filestore",
        action="store_true",
        help="Bei ZIP-Backups den Filestore nicht mit sichern.",
    )
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
    parser.add_argument(
        "--no-force-restore",
        action="store_true",
        help="Restore ohne erzwungenes Ueberschreiben ausfuehren.",
    )
    parser.add_argument(
        "--neutralize",
        action="store_true",
        help="Bei Restore die Odoo-Neutralisierung aktivieren.",
    )
    parser.add_argument(
        "--no-restart-after-restore",
        action="store_true",
        help="Service beim Restore nicht automatisch stoppen/starten.",
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
            if args.backup or args.restore:
                raise ValueError("Fuer --backup/--restore ist --config erforderlich.")
            config = collect_config(default_dry_run=args.dry_run)

        if args.ssh_host_key_mode:
            config.ssh_host_key_mode = args.ssh_host_key_mode

        if args.local:
            config.execution_mode = "local"

        if args.ask_ssh_password:
            config.ssh_password = getpass("SSH-Passwort: ").strip()

        config.validate_or_raise()

        if args.backup_keep_last is not None:
            if not args.backup:
                raise ValueError("--backup-keep-last kann nur zusammen mit --backup verwendet werden.")
            if args.backup_keep_last <= 0:
                raise ValueError("--backup-keep-last muss groesser als 0 sein.")

        if args.save_config:
            _save_config(args.save_config, config)
            print(f"Konfiguration gespeichert: {args.save_config}")

        _print_summary(config)

        operation_label = "Installation"
        if args.backup:
            operation_label = "Backup"
        elif args.restore:
            operation_label = "Restore"

        if not args.yes:
            confirm = input(f"\n{operation_label} starten? (j/n) [j]: ").strip().lower()
            if confirm not in {"", "j", "ja", "y", "yes"}:
                ui.warning("Abgebrochen.")
                return 0

        executor = SSHExecutor(
            host=config.host,
            user=config.ssh_user,
            port=config.ssh_port,
            ssh_key_path=config.ssh_key_path,
            ssh_password=config.ssh_password or None,
            host_key_mode=config.ssh_host_key_mode,
            execution_mode=config.execution_mode,
            dry_run=config.dry_run,
        )

        try:
            if args.backup:
                backup_path = run_backup(
                    executor=executor,
                    config=config,
                    backup_dir=args.backup_dir,
                    backup_name=args.backup_name,
                    dump_format=args.backup_format,
                    include_filestore=not args.no_filestore,
                    keep_last=args.backup_keep_last,
                )
                ui.success(f"Backup-Pfad: {backup_path}")
                return 0

            if args.restore:
                run_restore(
                    executor=executor,
                    config=config,
                    backup_path=args.restore,
                    force=not args.no_force_restore,
                    neutralize=args.neutralize,
                    restart_service=not args.no_restart_after_restore,
                )
                ui.success("Restore abgeschlossen.")
                return 0

            progress = None if config.dry_run else ProgressState(args.state_file, config, resume=args.resume)
            run_installation(executor, config, progress=progress, rollback_on_fail=args.rollback_on_fail)
            if progress:
                progress.clear()
            ui.success("Installation abgeschlossen.")
            return 0
        finally:
            executor.close()
    except KeyboardInterrupt:
        ui.warning("Abbruch durch Benutzer.")
        return 130
    except Exception as exc:  # noqa: BLE001
        ui.error(f"Fehler: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
