# odoo_installer

Gefuehrter Installer fuer Odoo 19 auf entfernten Ubuntu-24.04-Servern via SSH.

## Ziel

Das Projekt richtet sich an Kundeninstallationen auf Remote-Servern. Die Installation wird ueber gefuehrte Abfragen gesteuert und kann als `dry-run` getestet werden.

Linux-Setup Schritt fuer Schritt: `docs/Installationsanleitung_Linux.md`

## Aktueller Funktionsumfang

- Interaktive, gegliederte Terminal-UI fuer SSH, Odoo, PostgreSQL, Nginx, TLS, Firewall und Support-Zugriff
- Validierung der Eingaben vor dem Start
- Preflight fuer Ubuntu-Version, SSH-Konnektivitaet, RAM, Disk und Port-Hinweise
- Idempotente Grundinstallation von Odoo aus dem offiziellen Git-Repository
- Erstellung von `odoo.conf`, `systemd`-Service und optional Nginx/Certbot/UFW
- `--dry-run` fuer sichere Vorschau der ausgefuehrten Kommandos
- Resume-Funktion mit lokaler State-Datei (`--resume`, `--state-file`)
- Optionaler Rollback-Modus bei Fehlschlag (`--rollback-on-fail`)
- Remote Backup/Restore ueber `odoo-bin db dump/load`
- SSH-Login via Key/Agent **oder** Linux-Passwort (`--ask-ssh-password`)
- Statusleiste im Terminal mit aktuellem Installationsfortschritt und klaren Schritt-/Kommando-Hinweisen
- Optionaler AHD Support-SSH-Zugang: legt einen Key-basierten Admin-Benutzer fuer Termius/Termux/Terminal-Zugriff an

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

Resume-Beispiel mit gespeicherter Konfiguration:

```powershell
odoo-installer --config run-config.json --resume --state-file .odoo-installer-state.json --yes
```

Rollback-Beispiel bei Fehlern:

```powershell
odoo-installer --config run-config.json --rollback-on-fail --yes
```

SSH-Passwort interaktiv eingeben:

```powershell
odoo-installer --config run-config.json --ask-ssh-password --yes
```

Falls `Host key verification failed` auftritt:

```powershell
odoo-installer --config run-config.json --ask-ssh-password --ssh-host-key-mode accept-new --yes
```

Hinweis: `--ssh-host-key-mode insecure` deaktiviert die Host-Key-Pruefung (nur fuer Testumgebungen).

Backup erstellen (auf dem Remote-Server):

```powershell
odoo-installer --config run-config.json --backup --backup-format zip --yes
```

Backup mit Retention (nur die letzten 7 Backups behalten):

```powershell
odoo-installer --config run-config.json --backup --backup-format dump --backup-keep-last 7 --yes
```

Restore aus einem Remote-Backup:

```powershell
odoo-installer --config run-config.json --restore /opt/odoo/backups/odoo_20260524_130000.zip --yes
```

## Sicherheitshinweise

- Das Tool erwartet fuer automatisierte Laeufe `sudo` ohne interaktive Passwortabfrage oder einen root-Login.
- Zugangsdaten werden nicht in Git gespeichert. Optional gespeicherte JSON-Konfigurationen sollten sicher abgelegt werden.
- Der optionale AHD Support-Zugang arbeitet per SSH Public Key, sperrt Passwort-Login fuer den Support-Benutzer und validiert die sudoers-Datei mit `visudo`.
- `wkhtmltopdf` wird aktuell ueber Ubuntu-Pakete installiert. Fuer produktive PDF-Layouts kann eine gezielte Versionierung erforderlich sein.
- Rollback ist bewusst konservativ und deckt nur unterstuetzte Schritte ab (best effort, kein vollstaendiges System-Undo).

## Naechste Schritte

- Erweiterte Nginx/Websocket-Konfiguration fuer Lastprofile
- CI-Integrationstests gegen Ubuntu-24.04-Testsystem
