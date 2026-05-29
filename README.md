# odoo_installer

Gefuehrter Installer fuer Odoo 19 auf entfernten Ubuntu-24.04-Servern via SSH.

## Ziel

Das Projekt richtet sich an Kundeninstallationen auf Remote-Servern. Die Installation wird ueber gefuehrte Abfragen gesteuert und kann als `dry-run` getestet werden.

Linux-Setup Schritt fuer Schritt: `docs/Installationsanleitung_Linux.md`

Kompletter Testlauf mit Installation, Custom-Addon-Repositories und restic Backup: `docs/Testlauf_Installation_Addons_Backup.md`

## Aktueller Funktionsumfang

- Interaktive, gegliederte Terminal-UI fuer SSH, Odoo, PostgreSQL, Nginx, TLS, Firewall und Support-Zugriff
- Validierung der Eingaben vor dem Start
- Preflight fuer Ubuntu-Version, SSH-Konnektivitaet, RAM, Disk und Port-Hinweise
- Idempotente Grundinstallation von Odoo aus dem offiziellen Git-Repository
- Erstellung von `odoo.conf`, `systemd`-Service und optional Nginx/Certbot/UFW
- Custom-Addons-Pfade und optionale Git-Repositories werden angelegt, synchronisiert und automatisch in `addons_path` aufgenommen
- Automatische Initialisierung leerer Odoo-Datenbanken mit dem Basismodul vor dem ersten Service-Start
- `--dry-run` fuer sichere Vorschau der ausgefuehrten Kommandos
- Resume-Funktion mit lokaler State-Datei (`--resume`, `--state-file`)
- Optionaler Rollback-Modus bei Fehlschlag (`--rollback-on-fail`)
- Remote Backup/Restore ueber `odoo-bin db dump/load`
- Optionales restic Cloud-Backup mit Cronjob, Repository-URL (z. B. SFTP), verschluesselter Ablage und Retention
- SSH-Login via Key/Agent **oder** Linux-Passwort (`--ask-ssh-password`)
- Statusleiste im Terminal mit aktuellem Installationsfortschritt und klaren Schritt-/Kommando-Hinweisen
- Lokaler Ausfuehrungsmodus (`--local`) fuer Installationen, bei denen der Installer bereits direkt auf dem Kundensystem gestartet wird
- Optionaler AHD Support-SSH-Zugang: erzeugt lokal einen RSA-PEM-SSH-Key, zeigt den Private Key zum Kopieren an und legt den Benutzer `itservice-ahd-support` mit vollem Namen `IT-Service AHD` an

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

Lokale Installation ohne zusaetzliche SSH-Verbindung, wenn du bereits auf dem Kundensystem bist:

```powershell
odoo-installer --config run-config.json --local --yes
```

Custom-Addons koennen in `run-config.json` vorbereitet werden:

```json
{
  "custom_addons_enabled": true,
  "custom_addons_paths": ["/srv/odoo/customer-addons"],
  "custom_addons_repositories": [
    {
      "url": "https://github.com/example/customer-addons.git",
      "branch": "19.0",
      "target": "/opt/odoo/custom-addons/customer"
    }
  ],
  "custom_addons_install_python_requirements": false
}
```

Der Standardpfad `<install_dir>/custom-addons` bleibt automatisch aktiv, solange `custom_addons_enabled` nicht auf `false` gesetzt wird.

Restic Cloud-Backups koennen ebenfalls in `run-config.json` vorbereitet werden:

```json
{
  "backup_enabled": true,
  "backup_repository_url": "sftp:backup@example.com:/backups/customer-odoo",
  "backup_password_file": "/etc/odoo-backup/restic-password",
  "backup_schedule": "0 2 * * *",
  "backup_retention_daily": 7,
  "backup_retention_weekly": 4,
  "backup_retention_monthly": 6
}
```

Das Restic-Passwort wird nicht in der JSON-Konfiguration gespeichert; der Installer erwartet eine separat angelegte Passwortdatei mit sicheren Rechten.

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

Restic-Snapshots anzeigen und Repository pruefen:

```powershell
odoo-installer --config run-config.json --restic-snapshots --yes
odoo-installer --config run-config.json --restic-check --restic-read-data-subset 5% --yes
```

## Sicherheitshinweise

- Das Tool erwartet fuer automatisierte Laeufe `sudo` ohne interaktive Passwortabfrage oder einen root-Login.
- Zugangsdaten werden nicht in Git gespeichert. Optional gespeicherte JSON-Konfigurationen sollten sicher abgelegt werden.
- Restic-Backups speichern nur den Pfad zur Passwortdatei; das Passwort selbst gehoert nicht in `run-config.json`, Logs oder Git. Die Datei sollte `root:root` gehoeren und `chmod 600` haben.
- Der optionale AHD Support-Zugang erzeugt den Private Key lokal unter `~/.odoo-installer/support-keys/` im PEM-Format, zeigt ihn einmal zum Kopieren in Termius/Termux an, schreibt nur den Public Key auf das Kundensystem, sperrt Passwort-Login fuer den Support-Benutzer und validiert die sudoers-Datei mit `visudo`.
- `wkhtmltopdf` wird aktuell ueber Ubuntu-Pakete installiert. Fuer produktive PDF-Layouts kann eine gezielte Versionierung erforderlich sein.
- Rollback ist bewusst konservativ und deckt nur unterstuetzte Schritte ab (best effort, kein vollstaendiges System-Undo).

## Troubleshooting

Bei `500 Internal Server Error` nach der Installation zuerst den Odoo-Log pruefen:

```bash
sudo tail -n 100 /opt/odoo/logs/odoo.log
```

Wenn die Datenbank noch leer bzw. nicht als Odoo-Datenbank initialisiert ist, den aktuellen Installer pullen und erneut lokal starten. Der Installer schreibt dabei auch eine korrigierte `addons_path` inklusive Odoo-Core-Addons (`/opt/odoo/src/odoo/odoo/addons`) und gibt bei Initialisierungsfehlern die letzten Odoo-Logzeilen direkt aus. Meldet der Log `server's encoding SQL_ASCII`, wird eine noch nicht initialisierte Datenbank automatisch mit UTF8 neu angelegt:

```powershell
git pull
odoo-installer --config run-config.json --local --yes
```

## Naechste Schritte

- Erweiterte Nginx/Websocket-Konfiguration fuer Lastprofile
- CI-Integrationstests gegen Ubuntu-24.04-Testsystem
