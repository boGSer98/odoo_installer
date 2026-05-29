# Testlauf: Installation, Custom-Addons und restic Backup

Diese Anleitung beschreibt einen kompletten Testlauf auf einem Linux-/Ubuntu-System, auf dem du bereits per SSH angemeldet bist.

## 1. Installer aktualisieren

```bash
cd ~/odoo_installer
# falls das Repository woanders liegt, entsprechend anpassen
git pull
source .venv/bin/activate 2>/dev/null || true
pip install -e .
```

Falls noch kein Checkout existiert:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv openssh-client

git clone https://github.com/boGSer98/odoo_installer.git
cd odoo_installer
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## 2. Restic-Passwortdatei vorbereiten

Das Passwort nicht in Git, Tickets oder `run-config.json` speichern.

```bash
sudo install -d -m 700 -o root -g root /etc/odoo-backup
sudo sh -c 'umask 077; printf "%s\n" "<RESTIC-PASSWORT>" > /etc/odoo-backup/restic-password'
sudo chown root:root /etc/odoo-backup/restic-password
sudo chmod 600 /etc/odoo-backup/restic-password
```

## 3. Konfiguration fuer Installation + spaetere Addons + Backup erstellen

Passe Host, Repository-URLs und Backup-Ziel an. Im lokalen Modus ist `host` nur ein Platzhalter.

```bash
cat > run-config.json <<'JSON'
{
  "host": "localhost",
  "ssh_user": "root",
  "execution_mode": "local",
  "use_sudo": true,
  "odoo_version": "19.0",
  "install_dir": "/opt/odoo",
  "data_dir": "/opt/odoo/data",
  "odoo_system_user": "odoo",
  "service_name": "odoo",
  "db_name": "odoo",
  "db_user": "odoo",
  "db_password": "BITTE_AENDERN_DB_PASSWORT",
  "admin_password": "BITTE_AENDERN_ODOO_MASTER_PASSWORT",
  "custom_addons_enabled": true,
  "custom_addons_paths": [
    "/srv/odoo/customer-addons"
  ],
  "custom_addons_repositories": [],
  "custom_addons_install_python_requirements": false,
  "backup_enabled": true,
  "backup_repository_url": "sftp:backup@example.com:/backups/customer-odoo",
  "backup_password_file": "/etc/odoo-backup/restic-password",
  "backup_schedule": "0 2 * * *",
  "backup_retention_daily": 7,
  "backup_retention_weekly": 4,
  "backup_retention_monthly": 6,
  "http_port": 8069,
  "longpolling_port": 8072,
  "dry_run": false
}
JSON
chmod 600 run-config.json
```

## 4. Dry-Run pruefen

```bash
odoo-installer --config run-config.json --local --dry-run --yes
```

Achte im Output auf:

- `Custom-Addons vorbereiten`
- `Restic Cloud-Backup einrichten`
- `addons_path = .../odoo/addons,.../addons,.../custom-addons`
- `/usr/local/sbin/odoo-backup`
- `/etc/cron.d/odoo-backup`

## 5. Installation ausfuehren

```bash
odoo-installer --config run-config.json --local --yes
```

## 6. Installation pruefen

```bash
sudo systemctl status odoo --no-pager --full
sudo tail -n 100 /opt/odoo/logs/odoo.log
curl -I http://127.0.0.1:8069
```

Erwartung: Odoo-Service laeuft und `curl` liefert eine HTTP-Antwort, z. B. `200`, `303` oder `404` je nach Odoo-Zustand/Route.

## 7. Zusaetzliche Repositories nachtraeglich einbinden

Passe `run-config.json` an und trage die Repositories ein:

```json
"custom_addons_repositories": [
  {
    "url": "https://github.com/example/customer-addons.git",
    "branch": "19.0",
    "target": "/opt/odoo/custom-addons/customer"
  }
]
```

Wenn das Repository Python-Abhaengigkeiten installieren soll:

```json
"custom_addons_install_python_requirements": true
```

Danach zuerst Dry-Run:

```bash
odoo-installer --config run-config.json --local --dry-run --yes
```

Dann anwenden:

```bash
odoo-installer --config run-config.json --local --yes
```

Odoo neu starten und Addon-Pfad pruefen:

```bash
sudo systemctl restart odoo
sudo grep '^addons_path' /etc/odoo.conf
sudo systemctl status odoo --no-pager --full
```

Danach in Odoo den Apps-Cache aktualisieren und das neue Modul installieren/aktualisieren.

## 8. Backup manuell erstellen

Der Cronjob laeuft automatisch nach `backup_schedule`. Fuer den Test direkt starten:

```bash
sudo /usr/local/sbin/odoo-backup
sudo tail -n 100 /var/log/odoo-backup.log
```

## 9. Backup pruefen

Snapshots anzeigen:

```bash
odoo-installer --config run-config.json --local --restic-snapshots --yes
```

Repository pruefen:

```bash
odoo-installer --config run-config.json --local --restic-check --restic-read-data-subset 5% --yes
```

Alternativ direkt mit restic:

```bash
sudo bash -lc 'set -a && . /etc/odoo-backup/env && set +a && restic snapshots'
sudo bash -lc 'set -a && . /etc/odoo-backup/env && set +a && restic check --read-data-subset=5%'
```

## 10. Restore grob testen / vorbereiten

Snapshots ansehen:

```bash
odoo-installer --config run-config.json --local --restic-snapshots --yes
```

Snapshot in ein Testverzeichnis wiederherstellen:

```bash
sudo install -d -m 700 -o root -g root /restore/odoo-test
sudo bash -lc 'set -a && . /etc/odoo-backup/env && set +a && restic restore latest --target /restore/odoo-test'
```

Danach sollten u. a. der Datenbank-Dump und gesicherte Pfade unter `/restore/odoo-test` liegen. Einen produktiven Restore nicht ohne Wartungsfenster und vorherige Ruecksprache ausfuehren.
