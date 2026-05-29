# Installationsanleitung Linux (Start vom Linux-System)

Diese Anleitung beschreibt, wie du den `odoo-installer` direkt auf einem Linux-System (z. B. Ubuntu 24.04) installierst und startest.

## 1. Voraussetzungen auf dem Linux-System

```bash
sudo apt update
sudo apt install -y git python3 python3-venv openssh-client
```

## 2. Repository von GitHub klonen

```bash
git clone https://github.com/boGSer98/odoo_installer.git
cd odoo_installer
```

Optional: auf einen Feature-Branch wechseln, falls du einen PR-Stand testen willst:

```bash
git fetch --all
git checkout codex/ssh-password-auth
```

## 3. Python-Umgebung einrichten

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Danach steht der Befehl `odoo-installer` in der aktiven venv bereit.

## 4. Konfiguration erstellen

Interaktiv starten und Konfiguration speichern:

```bash
odoo-installer --save-config run-config.json
```

Hinweise:

- Wenn du bereits per SSH auf dem Kundensystem angemeldet bist, waehle in Punkt **1 Zielsystem** den lokalen Modus. Dann baut der Installer keine weitere SSH-Verbindung auf und fuehrt die Kommandos direkt auf diesem System aus.
- `ssh_password` wird absichtlich **nicht** in `run-config.json` gespeichert.
- Der Private Key fuer den optionalen AHD Support-Zugriff wird ebenfalls **nicht** in `run-config.json` gespeichert.
- Fuer Linux-Passwort-Login das Passwort beim Start per `--ask-ssh-password` eingeben.

### Custom-Addons in Schritt 3

Der interaktive Punkt **3 Custom-Addons** bereitet Addon-Pfade fuer Kunden- oder Partner-Module vor. Standardmaessig wird `<install_dir>/custom-addons` angelegt und in `addons_path` aufgenommen.

Optional kannst du weitere absolute Pfade angeben, z. B.:

```text
/srv/odoo/customer-addons,/srv/odoo/partner-addons
```

Optional koennen auch Git-Repositories definiert werden. Der Installer klont sie als Odoo-Systembenutzer oder aktualisiert bestehende Checkouts per `git fetch`, `git checkout` und `git pull --ff-only`. Repository-Ziele werden automatisch in `addons_path` aufgenommen.

Beispiel fuer `run-config.json`:

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

`custom_addons_install_python_requirements` sollte nur bewusst aktiviert werden. Dann installiert der Installer eine vorhandene `requirements.txt` aus jedem konfigurierten Addon-Repository in die Odoo-venv.

### Restic Cloud-Backup in Schritt 7

Der interaktive Punkt **7 Backups** richtet optional automatische, verschluesselte Cloud-Backups mit `restic` ein.

Vor dem produktiven Lauf muss die Restic-Passwortdatei auf dem Zielsystem existieren. Beispiel:

```bash
sudo install -d -m 700 -o root -g root /etc/odoo-backup
sudo sh -c 'umask 077; printf "%s\n" "<RESTIC-PASSWORT>" > /etc/odoo-backup/restic-password'
sudo chown root:root /etc/odoo-backup/restic-password
sudo chmod 600 /etc/odoo-backup/restic-password
```

Beispiel-Konfiguration:

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

Der Installer erstellt `/usr/local/sbin/odoo-backup` und `/etc/cron.d/odoo-backup`. Gesichert werden Datenbank-Dump, Filestore, Odoo-Konfiguration und Custom-Addons. Nach der Installation kannst du das Backup manuell testen:

```bash
sudo /usr/local/sbin/odoo-backup
sudo tail -n 100 /var/log/odoo-backup.log
```

Snapshots und Repository-Check ueber den Installer:

```bash
odoo-installer --config run-config.json --local --restic-snapshots --yes
odoo-installer --config run-config.json --local --restic-check --restic-read-data-subset 5% --yes
```

Ein kompletter Ablauf fuer Installation, nachtraegliche Repository-Einbindung und Backup-Test steht in `docs/Testlauf_Installation_Addons_Backup.md`.

### AHD Support-Zugriff in Schritt 6

Wenn du den Punkt **6 AHD Support-Zugriff** im interaktiven Installer aktivierst, erzeugt der Installer automatisch einen eigenen lokalen SSH-Key fuer den Support-Zugang.

Standardwerte:

- Benutzer auf dem Zielsystem: `itservice-ahd-support`
- Vollstaendiger Name/Kommentar: `IT-Service AHD`
- Key-Typ: RSA 4096 Bit
- Private-Key-Format in der Terminalausgabe: PEM (`-----BEGIN RSA PRIVATE KEY-----`)
- lokaler Speicherort: `~/.odoo-installer/support-keys/`

Der Installer zeigt den erzeugten **Private Key** direkt im Terminal an. Kopiere diesen Key in deinen SSH-Client, z. B. Termius oder Termux. Auf dem Kundensystem wird nur der Public Key als `authorized_keys` fuer den Benutzer `itservice-ahd-support` hinterlegt.

Wichtig:

- Den Private Key nur sicher speichern und nicht an Kunden oder in Git weitergeben.
- Der Passwort-Login fuer `itservice-ahd-support` wird gesperrt.
- Der Benutzer erhaelt sudo-Zugriff ohne Passwort; die sudoers-Datei wird mit `visudo` validiert.

## 5. Ersttest als Dry-Run

```bash
odoo-installer --config run-config.json --local --dry-run --yes
```

Damit siehst du alle geplanten Kommandos ohne Aenderungen auf dem Zielsystem.

Wenn du bewusst ein anderes Zielsystem per SSH installieren willst, verwende statt `--local` weiterhin z. B.:

```bash
odoo-installer --config run-config.json --ask-ssh-password --ssh-host-key-mode accept-new --dry-run --yes
```

Wenn der AHD Support-Zugriff aktiviert ist, zeigt der Dry-Run auch die geplanten Schritte fuer den Benutzer `itservice-ahd-support`, `authorized_keys`, Passwortsperre und sudoers-Konfiguration an.

Der Dry-Run zeigt ausserdem die automatische Odoo-Datenbankinitialisierung. Der Installer prueft, ob die Tabelle `ir_module_module` bereits existiert. Falls nicht, wird die Datenbank vor dem Service-Start mit `-i base --without-demo=all --stop-after-init` initialisiert. Die generierte `addons_path` enthaelt den Odoo-Core-Pfad `<install_dir>/src/odoo/odoo/addons`, den Standard-Addon-Pfad `<install_dir>/src/odoo/addons`, `<install_dir>/custom-addons` sowie alle zusaetzlichen Custom-Addon-Pfade und Repository-Ziele. Wenn `backup_enabled` aktiv ist, zeigt der Dry-Run auch die restic-Installation, `/etc/odoo-backup/env`, das Backup-Script und den Cronjob.

## 6. Produktiver Installationslauf

```bash
odoo-installer --config run-config.json --local --yes
```

Im lokalen Modus wird keine SSH-Verbindung aufgebaut. Das ist der empfohlene Modus, wenn du den Installer direkt auf dem Kundensystem startest.

Empfohlen:

- `--local`, wenn du bereits per SSH auf dem Kundensystem bist
- `--ssh-host-key-mode accept-new` fuer den ersten Kontakt mit neuen Hosts
- `--ssh-host-key-mode strict` fuer strengere Produktivumgebungen

## 7. Optional: Backup/Restore

Es gibt zwei Backup-Varianten:

1. einmaliges Remote-Backup ueber `odoo-bin db dump/load`
2. automatisches restic Cloud-Backup ueber `backup_enabled` in der Installation

Einmaliges Backup:

```bash
odoo-installer --config run-config.json --backup --backup-format dump --backup-keep-last 7 --ask-ssh-password --yes
```

Restore aus einem einmaligen Backup:

```bash
odoo-installer --config run-config.json --restore /opt/odoo/backups/DATEI.dump --ask-ssh-password --yes
```

Restic-Backups werden durch den Cronjob `/etc/cron.d/odoo-backup` ausgefuehrt. Ein manueller Test ist nach der Installation moeglich:

```bash
sudo /usr/local/sbin/odoo-backup
```

Snapshots und Repository-Check:

```bash
odoo-installer --config run-config.json --local --restic-snapshots --yes
odoo-installer --config run-config.json --local --restic-check --restic-read-data-subset 5% --yes
```

## 8. Typische Fehler und Loesungen

`Host key verification failed`

- Einmal mit `--ssh-host-key-mode accept-new` starten
- oder alten Key entfernen:

```bash
ssh-keygen -R <hostname-oder-ip>
```

`Permission denied (publickey,password)`

- Benutzer/Passwort pruefen
- SSH-Port pruefen (`ssh_port` in der Konfig)
- auf Zielserver sicherstellen, dass Passwort-Login erlaubt ist (falls ohne Key gearbeitet wird)

`sudo`-Fehler im Installer

- entweder als `root` verbinden
- oder auf Zielsystem passenden `sudo`-Zugang konfigurieren

`500 Internal Server Error` auf `localhost:8069`

- Odoo-Log pruefen:

```bash
sudo tail -n 100 /opt/odoo/logs/odoo.log
```

- Wenn die Datenbank noch nicht initialisiert wurde oder der Odoo-Log `server's encoding SQL_ASCII` meldet, Installer aktualisieren und lokal erneut starten. Nicht initialisierte Nicht-UTF8-Datenbanken werden dann automatisch mit UTF8 neu angelegt:

```bash
git pull
odoo-installer --config run-config.json --local --yes
```
