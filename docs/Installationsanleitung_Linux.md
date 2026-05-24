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
- Fuer Linux-Passwort-Login das Passwort beim Start per `--ask-ssh-password` eingeben.

## 5. Ersttest als Dry-Run

```bash
odoo-installer --config run-config.json --ask-ssh-password --ssh-host-key-mode accept-new --dry-run --yes
```

Damit siehst du alle geplanten Kommandos ohne Aenderungen auf dem Zielsystem.

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
