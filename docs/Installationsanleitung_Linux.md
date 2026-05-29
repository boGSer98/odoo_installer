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

- `ssh_password` wird absichtlich **nicht** in `run-config.json` gespeichert.
- Der Private Key fuer den optionalen AHD Support-Zugriff wird ebenfalls **nicht** in `run-config.json` gespeichert.
- Fuer Linux-Passwort-Login das Passwort beim Start per `--ask-ssh-password` eingeben.

### AHD Support-Zugriff in Schritt 5

Wenn du den Punkt **5 AHD Support-Zugriff** im interaktiven Installer aktivierst, erzeugt der Installer automatisch einen eigenen lokalen SSH-Key fuer den Support-Zugang.

Standardwerte:

- Benutzer auf dem Zielsystem: `itservice-ahd-support`
- Vollstaendiger Name/Kommentar: `IT-Service AHD`
- Key-Typ: `ed25519`
- lokaler Speicherort: `~/.odoo-installer/support-keys/`

Der Installer zeigt den erzeugten **Private Key** direkt im Terminal an. Kopiere diesen Key in deinen SSH-Client, z. B. Termius oder Termux. Auf dem Kundensystem wird nur der Public Key als `authorized_keys` fuer den Benutzer `itservice-ahd-support` hinterlegt.

Wichtig:

- Den Private Key nur sicher speichern und nicht an Kunden oder in Git weitergeben.
- Der Passwort-Login fuer `itservice-ahd-support` wird gesperrt.
- Der Benutzer erhaelt sudo-Zugriff ohne Passwort; die sudoers-Datei wird mit `visudo` validiert.

## 5. Ersttest als Dry-Run

```bash
odoo-installer --config run-config.json --ask-ssh-password --ssh-host-key-mode accept-new --dry-run --yes
```

Damit siehst du alle geplanten Kommandos ohne Aenderungen auf dem Zielsystem.

Wenn der AHD Support-Zugriff aktiviert ist, zeigt der Dry-Run auch die geplanten Schritte fuer den Benutzer `itservice-ahd-support`, `authorized_keys`, Passwortsperre und sudoers-Konfiguration an.

## 6. Produktiver Installationslauf

```bash
odoo-installer --config run-config.json --ask-ssh-password --ssh-host-key-mode accept-new --yes
```

Empfohlen:

- `--ssh-host-key-mode accept-new` fuer den ersten Kontakt mit neuen Hosts
- `--ssh-host-key-mode strict` fuer strengere Produktivumgebungen

## 7. Optional: Backup/Restore

Backup:

```bash
odoo-installer --config run-config.json --backup --backup-format dump --backup-keep-last 7 --ask-ssh-password --yes
```

Restore:

```bash
odoo-installer --config run-config.json --restore /opt/odoo/backups/DATEI.dump --ask-ssh-password --yes
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
