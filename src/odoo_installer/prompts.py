from __future__ import annotations

from getpass import getpass, getuser
import secrets

from .models import InstallerConfig
from .support_ssh import generate_support_key
from .ui import ui


def _normalize_empty(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned == "":
        return None
    return cleaned


def ask_text(label: str, default: str | None = None, required: bool = True) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""
        print("Eingabe ist erforderlich.")


def ask_int(label: str, default: int) -> int:
    while True:
        raw = ask_text(label, str(default), required=True)
        try:
            value = int(raw)
        except ValueError:
            print("Bitte eine gueltige Zahl eingeben.")
            continue
        if 1 <= value <= 65535:
            return value
        print("Bitte eine Zahl zwischen 1 und 65535 eingeben.")


def ask_bool(label: str, default: bool = False) -> bool:
    default_label = "j" if default else "n"
    while True:
        raw = ask_text(f"{label} (j/n)", default_label, required=True).lower()
        if raw in {"j", "ja", "y", "yes"}:
            return True
        if raw in {"n", "nein", "no"}:
            return False
        print("Bitte mit j oder n antworten.")


def ask_secret(label: str, allow_empty: bool = False) -> str:
    while True:
        value = getpass(f"{label}: ").strip()
        if value:
            return value
        if allow_empty:
            return ""
        print("Eingabe ist erforderlich.")


def ask_choice(label: str, choices: list[str], default: str) -> str:
    value_set = {entry.lower() for entry in choices}
    while True:
        value = ask_text(label, default, required=True).strip().lower()
        if value in value_set:
            return value
        print(f"Ungueltige Eingabe. Erlaubt: {', '.join(choices)}")


def generate_secret() -> str:
    return secrets.token_urlsafe(24)


def collect_config(default_dry_run: bool = False) -> InstallerConfig:
    ui.banner("AHD Odoo Installer", "Gefuehrte Installation fuer Ubuntu 24.04")
    ui.info("Der Installer kann direkt auf dem Kundensystem laufen oder sich per SSH mit einem Zielsystem verbinden.")

    ui.section("Zielsystem", "1")

    local_execution = ask_bool("Installer direkt auf diesem System ausfuehren (keine SSH-Verbindung aufbauen)?", True)
    execution_mode = "local" if local_execution else "ssh"
    if local_execution:
        host = "localhost"
        ssh_user = getuser()
        ssh_port = 22
        ssh_key_path = None
        ssh_password = ""
        ssh_host_key_mode = "accept-new"
        ui.info("Lokaler Modus aktiv: Punkt 1 baut keine SSH-Verbindung auf; alle Kommandos laufen direkt auf diesem System.")
    else:
        host = ask_text("SSH-Host/IP")
        ssh_user = ask_text("SSH-Benutzer", "root")
        ssh_port = ask_int("SSH-Port", 22)
        ssh_key_path = _normalize_empty(ask_text("Pfad zur SSH-Key-Datei (optional)", "", required=False))
        ssh_password = ask_secret("SSH-Passwort (optional, leer = Key/Agent)", allow_empty=True)
        ssh_host_key_mode = ask_choice(
            "SSH Host-Key-Modus (strict/accept-new/insecure)",
            choices=["strict", "accept-new", "insecure"],
            default="accept-new",
        )
    use_sudo = ask_bool("Soll sudo verwendet werden?", True)

    ui.section("Installationsparameter", "2")
    odoo_version = ask_text("Odoo-Version", "19.0")
    install_dir = ask_text("Installationspfad", "/opt/odoo")
    data_dir = ask_text("Odoo data_dir", f"{install_dir.rstrip('/')}/data")
    odoo_system_user = ask_text("Linux-Systembenutzer fuer Odoo", "odoo")
    service_name = ask_text("Systemd-Service-Name", "odoo")
    http_port = ask_int("HTTP-Port", 8069)
    longpolling_port = ask_int("Longpolling-Port", 8072)

    ui.section("Custom-Addons", "3")
    custom_addons_enabled = ask_bool("Custom-Addons-Verzeichnis vorbereiten und in addons_path aufnehmen?", True)
    custom_addons_paths: list[str] = []
    custom_addons_repositories: list[dict[str, str]] = []
    custom_addons_install_python_requirements = False
    if custom_addons_enabled:
        ui.info(f"Standardpfad: {install_dir.rstrip('/')}/custom-addons")
        extra_paths = ask_text(
            "Weitere Custom-Addon-Pfade, komma-getrennt (optional)",
            "",
            required=False,
        )
        custom_addons_paths = [entry.strip() for entry in extra_paths.split(",") if entry.strip()]
        if ask_bool("Custom-Addon-Git-Repositories konfigurieren?", False):
            while True:
                repo_url = ask_text("Repository-URL", required=True)
                repo_branch = ask_text("Repository-Branch", odoo_version)
                repo_target = ask_text(
                    "Zielpfad",
                    f"{install_dir.rstrip('/')}/custom-addons/{repo_branch.replace('/', '-')}-addons",
                )
                custom_addons_repositories.append(
                    {"url": repo_url, "branch": repo_branch, "target": repo_target}
                )
                if not ask_bool("Weiteres Custom-Addon-Repository hinzufuegen?", False):
                    break
            custom_addons_install_python_requirements = ask_bool(
                "requirements.txt aus Custom-Addon-Repositories installieren?", False
            )

    ui.section("Datenbank", "4")
    db_name = ask_text("PostgreSQL Datenbankname", "odoo")
    db_user = ask_text("PostgreSQL Benutzername", "odoo")
    db_password = ask_secret("PostgreSQL Passwort (leer = automatisch generieren)", allow_empty=True)
    if not db_password:
        db_password = generate_secret()
        ui.success("PostgreSQL Passwort wurde automatisch generiert.")

    admin_password = ask_secret("Odoo Master/Admin-Passwort (leer = automatisch generieren)", allow_empty=True)
    if not admin_password:
        admin_password = generate_secret()
        ui.success("Odoo Admin-Passwort wurde automatisch generiert.")

    ui.section("Web/SSL", "5")
    domain = _normalize_empty(ask_text("Domain (optional, z.B. odoo.example.de)", "", required=False))
    enable_nginx = ask_bool("Nginx als Reverse-Proxy konfigurieren?", bool(domain))
    enable_certbot = False
    if enable_nginx and domain:
        enable_certbot = ask_bool("Let's Encrypt via Certbot aktivieren?", True)
    enable_ufw = ask_bool("UFW Basisregeln setzen?", False)

    ui.section("AHD Support-Zugriff", "6")
    ui.info("Optional wird ein SSH-Key-basierter Support-Benutzer fuer Termius/Termux/Terminal-Zugriff angelegt.")
    enable_support_ssh = ask_bool("Support-SSH-Zugang fuer AHD einrichten?", False)
    support_ssh_user = "itservice-ahd-support"
    support_ssh_full_name = "IT-Service AHD"
    support_ssh_public_key = ""
    support_ssh_private_key_path = ""
    if enable_support_ssh:
        support_ssh_user = ask_text("Support-SSH-Benutzer", support_ssh_user)
        support_ssh_full_name = ask_text("Vollstaendiger Name", support_ssh_full_name)
        generated_key = generate_support_key(host, support_ssh_user)
        support_ssh_public_key = generated_key.public_key
        support_ssh_private_key_path = str(generated_key.private_key_path)
        ui.success(f"SSH-Key wurde erzeugt: {generated_key.private_key_path}")
        ui.warning("Kopiere den folgenden PRIVATE KEY im PEM-Format in Termius/Termux. Er wird danach nicht in der Konfiguration gespeichert.")
        print()
        print(generated_key.private_key.rstrip())
        print()
        ui.info("Public Key fuer authorized_keys:")
        print(generated_key.public_key)

    ui.section("Backups", "7")
    backup_enabled = ask_bool("Restic Cloud-Backup mit Cronjob einrichten?", False)
    backup_repository_url = ""
    backup_password_file = "/etc/odoo-backup/restic-password"
    backup_schedule = "0 2 * * *"
    backup_include_filestore = True
    backup_include_config = True
    backup_include_custom_addons = True
    backup_retention_daily = 7
    backup_retention_weekly = 4
    backup_retention_monthly = 6
    if backup_enabled:
        ui.info("Das Restic-Passwort wird nicht abgefragt und nicht gespeichert. Lege die Passwortdatei separat mit chmod 600 an.")
        backup_repository_url = ask_text(
            "Restic Repository-URL (z.B. sftp:user@example.com:/backups/customer-odoo)"
        )
        backup_password_file = ask_text("Restic Passwortdatei", backup_password_file)
        backup_schedule = ask_text("Cron-Zeitplan", backup_schedule)
        backup_include_filestore = ask_bool("Odoo-Filestore sichern?", True)
        backup_include_config = ask_bool("/etc/<service>.conf sichern?", True)
        backup_include_custom_addons = ask_bool("Custom-Addons sichern?", True)
        backup_retention_daily = int(ask_text("Restic Retention daily", "7"))
        backup_retention_weekly = int(ask_text("Restic Retention weekly", "4"))
        backup_retention_monthly = int(ask_text("Restic Retention monthly", "6"))

    ui.section("Ausfuehrung", "8")
    dry_run = ask_bool("Dry-Run (nur anzeigen, nichts aendern)?", default_dry_run)

    return InstallerConfig(
        host=host,
        ssh_user=ssh_user,
        execution_mode=execution_mode,
        ssh_port=ssh_port,
        ssh_key_path=ssh_key_path,
        ssh_password=ssh_password,
        ssh_host_key_mode=ssh_host_key_mode,
        use_sudo=use_sudo,
        odoo_version=odoo_version,
        install_dir=install_dir,
        data_dir=data_dir,
        odoo_system_user=odoo_system_user,
        service_name=service_name,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        admin_password=admin_password,
        domain=domain,
        enable_nginx=enable_nginx,
        enable_certbot=enable_certbot,
        enable_ufw=enable_ufw,
        enable_support_ssh=enable_support_ssh,
        support_ssh_user=support_ssh_user,
        support_ssh_full_name=support_ssh_full_name,
        support_ssh_public_key=support_ssh_public_key,
        support_ssh_private_key_path=support_ssh_private_key_path,
        custom_addons_enabled=custom_addons_enabled,
        custom_addons_paths=custom_addons_paths,
        custom_addons_repositories=custom_addons_repositories,
        custom_addons_install_python_requirements=custom_addons_install_python_requirements,
        backup_enabled=backup_enabled,
        backup_repository_url=backup_repository_url,
        backup_password_file=backup_password_file,
        backup_schedule=backup_schedule,
        backup_include_filestore=backup_include_filestore,
        backup_include_config=backup_include_config,
        backup_include_custom_addons=backup_include_custom_addons,
        backup_retention_daily=backup_retention_daily,
        backup_retention_weekly=backup_retention_weekly,
        backup_retention_monthly=backup_retention_monthly,
        http_port=http_port,
        longpolling_port=longpolling_port,
        dry_run=dry_run,
    )
