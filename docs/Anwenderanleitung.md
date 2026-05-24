# Anwenderanleitung odoo_installer

## Zweck

`odoo_installer` installiert Odoo 19 auf einem entfernten Ubuntu-24.04-Server, der per SSH erreichbar ist.

## Voraussetzungen

- Lokaler Rechner mit Python 3.11+
- SSH-Zugang zum Zielserver
- Ausreichende Rechte auf dem Zielserver (`sudo` ohne Passwort oder root)

## Installation lokal

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Interaktiver Start

```bash
odoo-installer
```

Das Tool fragt folgende Bereiche gefuehrt ab:

- SSH-Verbindung (Host, Benutzer, Port, Key)
- Odoo-Parameter (Version, Pfade, Service)
- PostgreSQL-Parameter (DB, Benutzer, Passwort)
- Weboptionen (Domain, Nginx, Certbot)
- Sicherheitsoptionen (UFW)

## Dry-Run

```bash
odoo-installer --dry-run
```

Im Dry-Run werden keine aendernden Kommandos ausgefuehrt. Du siehst nur die geplanten SSH-Kommandos.

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

## Ergebnis auf dem Zielserver

- Odoo-Quellcode unter `<install_dir>/src/odoo`
- Python-Umgebung unter `<install_dir>/venv`
- Konfigurationsdatei unter `/etc/<service_name>.conf`
- `systemd`-Service unter `/etc/systemd/system/<service_name>.service`

## Fehlerbehandlung

- Bei einem Fehler stoppt der Installer am betroffenen Schritt.
- Die Fehlermeldung zeigt Schrittname, Kommando und Exit-Code an.
- Nach Korrektur kann der Installer erneut gestartet werden (idempotente Schritte, soweit moeglich).
