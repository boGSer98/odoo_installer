from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re


NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
VERSION_RE = re.compile(r"^\d+\.\d+$")
DOMAIN_RE = re.compile(r"^(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}$")
HOST_KEY_MODES = {"strict", "accept-new", "insecure"}
SSH_KEY_RE = re.compile(r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521))\s+\S+(?:\s+.*)?$")
EXECUTION_MODES = {"local", "ssh"}


@dataclass(slots=True)
class InstallerConfig:
    host: str
    ssh_user: str
    execution_mode: str = "ssh"
    ssh_port: int = 22
    ssh_key_path: str | None = None
    ssh_password: str = ""
    ssh_host_key_mode: str = "accept-new"
    use_sudo: bool = True
    odoo_version: str = "19.0"
    install_dir: str = "/opt/odoo"
    odoo_system_user: str = "odoo"
    service_name: str = "odoo"
    data_dir: str | None = None
    db_name: str = "odoo"
    db_user: str = "odoo"
    db_password: str = ""
    admin_password: str = ""
    domain: str | None = None
    enable_nginx: bool = False
    enable_certbot: bool = False
    enable_ufw: bool = False
    enable_support_ssh: bool = False
    support_ssh_user: str = "itservice-ahd-support"
    support_ssh_full_name: str = "IT-Service AHD"
    support_ssh_public_key: str = ""
    support_ssh_private_key_path: str = ""
    custom_addons_enabled: bool = True
    custom_addons_paths: list[str] = field(default_factory=list)
    custom_addons_repositories: list[dict[str, str]] = field(default_factory=list)
    custom_addons_install_python_requirements: bool = False
    backup_enabled: bool = False
    backup_repository_url: str = ""
    backup_password_file: str = "/etc/odoo-backup/restic-password"
    backup_schedule: str = "0 2 * * *"
    backup_include_filestore: bool = True
    backup_include_config: bool = True
    backup_include_custom_addons: bool = True
    backup_retention_daily: int = 7
    backup_retention_weekly: int = 4
    backup_retention_monthly: int = 6
    http_port: int = 8069
    longpolling_port: int = 8072
    dry_run: bool = False

    def effective_custom_addons_paths(self) -> list[str]:
        if not self.custom_addons_enabled:
            return []

        paths = [f"{self.install_dir.rstrip('/')}/custom-addons"]
        paths.extend(self.custom_addons_paths)
        for repository in self.custom_addons_repositories:
            target = repository.get("target", "").strip()
            if target:
                paths.append(target)

        deduped: list[str] = []
        for path in paths:
            cleaned = path.rstrip("/") or "/"
            if cleaned not in deduped:
                deduped.append(cleaned)
        return deduped

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.execution_mode not in EXECUTION_MODES:
            errors.append("execution_mode muss 'local' oder 'ssh' sein.")
        if self.execution_mode == "ssh":
            if not self.host.strip():
                errors.append("SSH-Host darf nicht leer sein.")
            if not self.ssh_user.strip():
                errors.append("SSH-Benutzer darf nicht leer sein.")
        if not (1 <= self.ssh_port <= 65535):
            errors.append("SSH-Port muss zwischen 1 und 65535 liegen.")
        if self.ssh_host_key_mode not in HOST_KEY_MODES:
            errors.append("ssh_host_key_mode muss 'strict', 'accept-new' oder 'insecure' sein.")
        if not VERSION_RE.match(self.odoo_version):
            errors.append("Odoo-Version muss dem Format X.Y entsprechen (z.B. 19.0).")
        if not self.install_dir.startswith("/"):
            errors.append("Installationspfad muss ein absoluter Linux-Pfad sein.")
        if not NAME_RE.match(self.odoo_system_user):
            errors.append("Odoo-Systembenutzer enthaelt ungueltige Zeichen.")
        if not NAME_RE.match(self.service_name):
            errors.append("Service-Name enthaelt ungueltige Zeichen.")
        if self.data_dir and not self.data_dir.startswith("/"):
            errors.append("data_dir muss ein absoluter Linux-Pfad sein.")
        if self.custom_addons_enabled:
            for path in self.custom_addons_paths:
                if not path.startswith("/"):
                    errors.append(f"Custom-Addon-Pfad muss absolut sein: {path}")
            for index, repository in enumerate(self.custom_addons_repositories, start=1):
                url = repository.get("url", "").strip()
                branch = repository.get("branch", "").strip()
                target = repository.get("target", "").strip()
                if not url:
                    errors.append(f"Custom-Addon-Repository {index} benoetigt eine url.")
                if not branch:
                    errors.append(f"Custom-Addon-Repository {index} benoetigt einen branch.")
                if not target:
                    errors.append(f"Custom-Addon-Repository {index} benoetigt ein target.")
                elif not target.startswith("/"):
                    errors.append(f"Custom-Addon-Repository target muss absolut sein: {target}")
        if not NAME_RE.match(self.db_user):
            errors.append("Datenbankbenutzer enthaelt ungueltige Zeichen.")
        if not NAME_RE.match(self.db_name):
            errors.append("Datenbankname enthaelt ungueltige Zeichen.")
        if self.http_port == self.longpolling_port:
            errors.append("HTTP-Port und Longpolling-Port muessen unterschiedlich sein.")
        if not (1 <= self.http_port <= 65535):
            errors.append("HTTP-Port muss zwischen 1 und 65535 liegen.")
        if not (1 <= self.longpolling_port <= 65535):
            errors.append("Longpolling-Port muss zwischen 1 und 65535 liegen.")
        if self.enable_certbot and not self.enable_nginx:
            errors.append("Certbot kann nur aktiviert werden, wenn Nginx aktiv ist.")
        if self.enable_certbot and not self.domain:
            errors.append("Certbot benoetigt eine Domain.")
        if self.domain and not DOMAIN_RE.match(self.domain):
            errors.append("Die Domain ist formal ungueltig.")
        if self.enable_support_ssh:
            if not NAME_RE.match(self.support_ssh_user):
                errors.append("Support-SSH-Benutzer enthaelt ungueltige Zeichen.")
            if not self.support_ssh_full_name.strip():
                errors.append("Support-SSH Vollstaendiger Name darf nicht leer sein.")
            if not self.support_ssh_public_key.strip():
                errors.append("Support-SSH benoetigt einen SSH Public Key.")
            elif not SSH_KEY_RE.match(self.support_ssh_public_key.strip()):
                errors.append("Support-SSH Public Key ist formal ungueltig.")
        if self.backup_enabled:
            if not self.backup_repository_url.strip():
                errors.append("Backup-Repository-URL darf nicht leer sein.")
            if not self.backup_password_file.startswith("/"):
                errors.append("Backup-Passwortdatei muss ein absoluter Linux-Pfad sein.")
            if not self.backup_schedule.strip():
                errors.append("Backup-Zeitplan darf nicht leer sein.")
            for label, value in (
                ("daily", self.backup_retention_daily),
                ("weekly", self.backup_retention_weekly),
                ("monthly", self.backup_retention_monthly),
            ):
                if value < 0:
                    errors.append(f"Backup-Retention {label} darf nicht negativ sein.")
        if not self.db_password:
            errors.append("Datenbankpasswort darf nicht leer sein.")
        if not self.admin_password:
            errors.append("Odoo-Admin-Passwort darf nicht leer sein.")
        return errors

    def validate_or_raise(self) -> None:
        errors = self.validate()
        if errors:
            joined = "\n".join(f"- {entry}" for entry in errors)
            raise ValueError(f"Ungueltige Konfiguration:\n{joined}")

    def safe_dict(self) -> dict[str, object]:
        data = asdict(self)
        for key in ("ssh_password", "db_password", "admin_password", "support_ssh_public_key"):
            if data.get(key):
                data[key] = "***"
        return data
