from __future__ import annotations

from getpass import getpass
import secrets

from .models import InstallerConfig


def _normalize_empty(value: str) -> str | None:
    cleaned = value.strip()
    return cleaned or None


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


def generate_secret() -> str:
    return secrets.token_urlsafe(24)


def collect_config(default_dry_run: bool = False) -> InstallerConfig:
    print("Gefuehrter Odoo-Installer fuer Ubuntu 24.04")
    print("Das Tool wird lokal auf dem Zielserver ausgefuehrt (kein SSH).")

    use_sudo = ask_bool("Soll sudo verwendet werden?", True)

    print("\nInstallationsparameter")
    odoo_version = ask_text("Odoo-Version", "19.0")
    install_dir = ask_text("Installationspfad", "/opt/odoo")
    data_dir = ask_text("Odoo data_dir", f"{install_dir.rstrip('/')}/data")
    odoo_system_user = ask_text("Linux-Systembenutzer fuer Odoo", "odoo")
    service_name = ask_text("Systemd-Service-Name", "odoo")
    http_port = ask_int("HTTP-Port", 8069)
    longpolling_port = ask_int("Longpolling-Port", 8072)

    print("\nDatenbank")
    db_name = ask_text("PostgreSQL Datenbankname", "odoo")
    db_user = ask_text("PostgreSQL Benutzername", "odoo")
    db_password = ask_secret("PostgreSQL Passwort (leer = automatisch generieren)", allow_empty=True)
    if not db_password:
        db_password = generate_secret()
        print("PostgreSQL Passwort wurde automatisch generiert.")

    admin_password = ask_secret("Odoo Master/Admin-Passwort (leer = automatisch generieren)", allow_empty=True)
    if not admin_password:
        admin_password = generate_secret()
        print("Odoo Admin-Passwort wurde automatisch generiert.")

    print("\nWeb/SSL")
    domain = _normalize_empty(ask_text("Domain (optional, z.B. odoo.example.de)", "", required=False))
    enable_nginx = ask_bool("Nginx als Reverse-Proxy konfigurieren?", bool(domain))
    enable_certbot = False
    if enable_nginx and domain:
        enable_certbot = ask_bool("Let's Encrypt via Certbot aktivieren?", True)
    enable_ufw = ask_bool("UFW Basisregeln setzen?", False)

    dry_run = ask_bool("Dry-Run (nur anzeigen, nichts aendern)?", default_dry_run)

    return InstallerConfig(
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
        http_port=http_port,
        longpolling_port=longpolling_port,
        dry_run=dry_run,
    )
