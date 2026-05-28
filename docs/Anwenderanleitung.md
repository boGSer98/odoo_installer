# Anwenderanleitung odoo_installer

## Zweck

`odoo_installer` installiert Odoo 19 auf einem Ubuntu-24.04-Server, direkt lokal auf diesem Zielsystem.

## Voraussetzungen

- Ubuntu 24.04 Zielserver
- Python 3.11+
- Ausreichende Rechte (`sudo` ohne interaktive Passwortabfrage oder root)

## Installation auf dem Zielserver

```bash
git clone https://github.com/boGSer98/odoo_installer.git
cd odoo_installer
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Interaktiver Start

```bash
odoo-installer
```

Waehrend der Installation zeigt das Tool eine Statusleiste mit Fortschritt in Prozent sowie Anzahl erledigter Kommandos an.

Das Tool fragt folgende Bereiche gefuehrt ab:

- Odoo-Parameter (Version, Pfade, Service)
- PostgreSQL-Parameter (DB, Benutzer, Passwort)
- Weboptionen (Domain, Nginx, Certbot)
- Sicherheitsoptionen (UFW)

## Dry-Run

```bash
odoo-installer --dry-run
```

Im Dry-Run werden keine aendernden Kommandos ausgefuehrt. Du siehst nur die geplanten lokalen Shell-Kommandos.

## Konfiguration speichern und wiederverwenden

```bash
odoo-installer --save-config run-config.json
odoo-installer --config run-config.json --yes
```

Hinweis: Konfigurationsdateien koennen sensible Daten enthalten. Sicher speichern und nicht committen.

## Resume nach Abbruch

```bash
odoo-installer --config run-config.json --resume --state-file .odoo-installer-state.json --yes
```

Verhalten:

- Bei einer fehlgeschlagenen Installation bleibt die State-Datei erhalten.
- Bereits erfolgreich ausgefuehrte Kommandos werden beim Resume uebersprungen.
- Wenn die Konfiguration seit dem letzten Lauf geaendert wurde, blockiert der Resume-Lauf zum Schutz vor Inkonsistenzen.

## Rollback bei Fehlschlag (best effort)

```bash
odoo-installer --config run-config.json --rollback-on-fail --yes
```

Verhalten:

- Bei einem Fehler fuehrt der Installer fuer unterstuetzte Schritte Rollback-Kommandos in umgekehrter Reihenfolge aus.
- Nach einem Rollback wird der lokale Resume-State aus Sicherheitsgruenden geloescht.
- Rollback ist nicht vollstaendig fuer alle Schritte (z.B. Paketinstallation, UFW oder Certbot werden nicht global rueckgaengig gemacht).

## Backup erstellen

```bash
odoo-installer --config run-config.json --backup --backup-format zip --yes
```

Optionen:

- `--backup-dir`: Zielverzeichnis auf dem lokalen Server (Standard: `<install_dir>/backups`)
- `--backup-name`: Dateiname fuer das Backup
- `--backup-keep-last N`: nach erfolgreichem Backup nur die letzten `N` DB-Backups behalten
- `--backup-format`: `zip` (DB + Filestore) oder `dump` (nur DB-Dump)
- `--no-filestore`: nur bei `zip`, schliesst den Filestore aus

Beispiel mit Retention:

```bash
odoo-installer --config run-config.json --backup --backup-format dump --backup-keep-last 7 --yes
```

## Restore aus Backup

```bash
odoo-installer --config run-config.json --restore /opt/odoo/backups/odoo_20260524_130000.zip --yes
```

Optionen:

- `--no-force-restore`: Restore ohne erzwungenes Ueberschreiben
- `--neutralize`: Odoo-Neutralisierung beim Restore aktivieren
- `--no-restart-after-restore`: Service nicht automatisch stoppen/starten

## Ergebnis auf dem Zielserver

- Odoo-Quellcode unter `<install_dir>/src/odoo`
- Python-Umgebung unter `<install_dir>/venv`
- Konfigurationsdatei unter `/etc/<service_name>.conf`
- `systemd`-Service unter `/etc/systemd/system/<service_name>.service`

## Fehlerbehandlung

- Bei einem Fehler stoppt der Installer am betroffenen Schritt.
- Die Fehlermeldung zeigt Schrittname, Kommando und Exit-Code an.
- Nach Korrektur kann der Installer erneut gestartet werden (idempotente Schritte, soweit moeglich).
