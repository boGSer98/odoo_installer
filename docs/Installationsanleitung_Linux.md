# Installationsanleitung Linux (lokaler Start auf dem Zielserver)

Diese Anleitung beschreibt, wie du den `odoo-installer` direkt auf dem Ubuntu-24.04-Server installierst und startest, auf dem Odoo spaeter laufen soll.

## 1. Voraussetzungen auf dem Zielserver

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
```

## 2. Repository von GitHub klonen

```bash
git clone https://github.com/boGSer98/odoo_installer.git
cd odoo_installer
```

Optional: einen bestimmten Branch testen:

```bash
git fetch --all
git checkout <branch-name>
```

## 3. Python-Umgebung einrichten

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
which odoo-installer
```

Danach steht der Befehl `odoo-installer` in der aktiven venv bereit.
Wichtig: Der Parameter heisst `--upgrade` (ohne Leerzeichen), nicht `-- upgrade`.

## 4. Konfiguration erstellen

Interaktiv starten und Konfiguration speichern:

```bash
odoo-installer --save-config run-config.json
```

## 5. Ersttest als Dry-Run

```bash
odoo-installer --config run-config.json --dry-run --yes
```

Damit siehst du alle geplanten Kommandos ohne Aenderungen auf dem System.

## 6. Produktiver Installationslauf

```bash
odoo-installer --config run-config.json --yes
```

Im Terminal wird dabei eine Statusleiste mit Prozentwert und Anzahl der bereits erledigten Kommandos angezeigt.

## 7. Optional: Backup/Restore

Backup:

```bash
odoo-installer --config run-config.json --backup --backup-format dump --backup-keep-last 7 --yes
```

Restore:

```bash
odoo-installer --config run-config.json --restore /opt/odoo/backups/DATEI.dump --yes
```

## 8. Typische Fehler und Loesungen

`odoo-installer: command not found`

- Pruefen, ob die venv aktiv ist (Prompt startet mit `(.venv)`).
- Falls nicht aktiv:

```bash
source .venv/bin/activate
```

- Installation in der venv erneut ausfuehren:

```bash
python3 -m pip install -e .
```

- Direkt ohne PATH nutzen:

```bash
.venv/bin/odoo-installer --save-config run-config.json
```

`Sudo ohne interaktive Passworteingabe ist nicht verfuegbar`

- Als `root` ausfuehren
- oder passenden `sudo`-Zugang fuer den aufrufenden Benutzer konfigurieren

`Zielsystem ist nicht Ubuntu 24.04`

- Installer nur auf Ubuntu 24.04 nutzen
- oder fuer Testzwecke zuerst mit `--dry-run` pruefen

`Port bereits belegt`

- In der Konfiguration andere Ports waehlen (`http_port`, `longpolling_port`)
- Oder den belegenden Dienst beenden/umkonfigurieren
