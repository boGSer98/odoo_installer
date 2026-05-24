# odoo_installer

Gefuehrter Installer fuer Odoo 19 auf entfernten Ubuntu-24.04-Servern via SSH.

## Ziel

Das Projekt richtet sich an Kundeninstallationen auf Remote-Servern. Die Installation wird ueber gefuehrte Abfragen gesteuert und kann als `dry-run` getestet werden.

## Aktueller Funktionsumfang

- Interaktive Konfigurationsabfragen fuer SSH, Odoo, PostgreSQL, Nginx, TLS und Firewall
- Validierung der Eingaben vor dem Start
- Preflight fuer Ubuntu-Version, SSH-Konnektivitaet, RAM, Disk und Port-Hinweise
- Idempotente Grundinstallation von Odoo aus dem offiziellen Git-Repository
- Erstellung von `odoo.conf`, `systemd`-Service und optional Nginx/Certbot/UFW
- `--dry-run` fuer sichere Vorschau der ausgefuehrten Kommandos

## Voraussetzungen lokal

- Python 3.11+
- SSH-Client im PATH
- SSH-Zugang zum Zielserver (Schluessel-basiert empfohlen)

## Schnellstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
odoo-installer
```

Unter Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
odoo-installer
```

## Sicherheitshinweise

- Das Tool erwartet fuer automatisierte Laeufe `sudo` ohne interaktive Passwortabfrage oder einen root-Login.
- Zugangsdaten werden nicht in Git gespeichert. Optional gespeicherte JSON-Konfigurationen sollten sicher abgelegt werden.
- `wkhtmltopdf` wird aktuell ueber Ubuntu-Pakete installiert. Fuer produktive PDF-Layouts kann eine gezielte Versionierung erforderlich sein.

## Naechste Schritte

- Resume- und Rollback-Mechanismus
- Erweiterte Nginx/Websocket-Konfiguration fuer Lastprofile
- Backup/Restore-Subcommands
- CI-Integrationstests gegen Ubuntu-24.04-Testsystem
