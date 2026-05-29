from __future__ import annotations

from getpass import getpass
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
    ui.info("Der Installer verbindet sich per SSH mit dem Kundensystem und fuehrt alle Schritte dort aus.")

    ui.section("Zielsystem", "1")

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

    ui.section("Datenbank", "3")
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

    ui.section("Web/SSL", "4")
    domain = _normalize_empty(ask_text("Domain (optional, z.B. odoo.example.de)", "", required=False))
    enable_nginx = ask_bool("Nginx als Reverse-Proxy konfigurieren?", bool(domain))
    enable_certbot = False
    if enable_nginx and domain:
        enable_certbot = ask_bool("Let's Encrypt via Certbot aktivieren?", True)
    enable_ufw = ask_bool("UFW Basisregeln setzen?", False)

    ui.section("AHD Support-Zugriff", "5")
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
        ui.warning("Kopiere den folgenden PRIVATE KEY in Termius/Termux. Er wird danach nicht in der Konfiguration gespeichert.")
        print()
        print(generated_key.private_key.rstrip())
        print()
        ui.info("Public Key fuer authorized_keys:")
        print(generated_key.public_key)

    ui.section("Ausfuehrung", "6")
    dry_run = ask_bool("Dry-Run (nur anzeigen, nichts aendern)?", default_dry_run)

    return InstallerConfig(
        host=host,
        ssh_user=ssh_user,
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
        http_port=http_port,
        longpolling_port=longpolling_port,
        dry_run=dry_run,
    )
