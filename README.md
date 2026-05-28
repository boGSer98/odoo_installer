# odoo_installer

Gefuehrter Installer fuer Odoo 19 auf Ubuntu-24.04-Servern.

## Ziel

Das Projekt richtet sich an Kundeninstallationen, bei denen der Installer direkt auf dem Zielserver ausgefuehrt wird. Die Installation wird ueber gefuehrte Abfragen gesteuert und kann als `dry-run` getestet werden.

Linux-Setup Schritt fuer Schritt: `docs/Installationsanleitung_Linux.md`

## Aktueller Funktionsumfang

- Interaktive Konfigurationsabfragen fuer Odoo, PostgreSQL, Nginx, TLS und Firewall
- Validierung der Eingaben vor dem Start
- Preflight fuer Ubuntu-Version, lokale Shell, RAM, Disk und Port-Hinweise
- Idempotente Grundinstallation von Odoo aus dem offiziellen Git-Repository
- Erstellung von `odoo.conf`, `systemd`-Service und optional Nginx/Certbot/UFW
- `--dry-run` fuer sichere Vorschau der ausgefuehrten Kommandos
- Resume-Funktion mit lokaler State-Datei (`--resume`, `--state-file`)
- Optionaler Rollback-Modus bei Fehlschlag (`--rollback-on-fail`)
- Lokales Backup/Restore ueber `odoo-bin db dump/load`
- Statusleiste im Terminal mit aktuellem Installationsfortschritt

## Voraussetzungen

- Ubuntu 24.04 Zielserver
- Linux-Shell auf dem Zielserver
- Python 3.11+
- Benutzer mit passenden Rechten (`sudo` ohne interaktive Passwortabfrage oder root)

## Schnellstart

```bash
git clone https://github.com/boGSer98/odoo_installer.git
cd odoo_installer
python -m venv .venv
source .venv/bin/activate
pip install -e .
odoo-installer
```

Resume-Beispiel mit gespeicherter Konfiguration:

```bash
odoo-installer --config run-config.json --resume --state-file .odoo-installer-state.json --yes
```

Rollback-Beispiel bei Fehlern:

```bash
odoo-installer --config run-config.json --rollback-on-fail --yes
```

Backup erstellen:

```bash
odoo-installer --config run-config.json --backup --backup-format zip --yes
```

Backup mit Retention (nur die letzten 7 Backups behalten):

```bash
odoo-installer --config run-config.json --backup --backup-format dump --backup-keep-last 7 --yes
```

Restore aus einem lokalen Backup:

```bash
odoo-installer --config run-config.json --restore /opt/odoo/backups/odoo_20260524_130000.zip --yes
```

## Sicherheitshinweise

- Der Installer ist auf lokale Ausfuehrung auf Linux ausgelegt und beendet sich auf Nicht-Linux-Systemen.
- Das Tool erwartet fuer automatisierte Laeufe `sudo` ohne interaktive Passwortabfrage oder einen root-Login.
- Zugangsdaten werden nicht in Git gespeichert. Optional gespeicherte JSON-Konfigurationen sollten sicher abgelegt werden.
- `wkhtmltopdf` wird aktuell ueber Ubuntu-Pakete installiert. Fuer produktive PDF-Layouts kann eine gezielte Versionierung erforderlich sein.
- Rollback ist bewusst konservativ und deckt nur unterstuetzte Schritte ab (best effort, kein vollstaendiges System-Undo).

## Naechste Schritte

- Erweiterte Nginx/Websocket-Konfiguration fuer Lastprofile
- CI-Integrationstests gegen Ubuntu-24.04-Testsystem
