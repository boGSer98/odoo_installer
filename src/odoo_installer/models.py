from __future__ import annotations

from dataclasses import asdict, dataclass
import re


NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
VERSION_RE = re.compile(r"^\d+\.\d+$")
DOMAIN_RE = re.compile(r"^(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}$")


@dataclass(slots=True)
class InstallerConfig:
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
    http_port: int = 8069
    longpolling_port: int = 8072
    dry_run: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
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
        for key in ("db_password", "admin_password"):
            if data.get(key):
                data[key] = "***"
        return data
