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

Waehrend der Installation zeigt das Tool eine Statusleiste mit Fortschritt in Prozent sowie Anzahl erledigter Kommandos an.

Das Tool fragt folgende Bereiche gefuehrt ab:

- SSH-Verbindung (Host, Benutzer, Port, Key)
- Ausfuehrungsmodus: lokal auf diesem System oder remote per SSH
- SSH-Passwort (optional, falls kein Key/Agent genutzt wird)
- Odoo-Parameter (Version, Pfade, Service)
- Custom-Addons-Pfade und optionale Git-Repositories
- PostgreSQL-Parameter (DB, Benutzer, Passwort)
- Weboptionen (Domain, Nginx, Certbot)
- Sicherheitsoptionen (UFW)
- AHD Support-Zugriff mit automatisch erzeugtem SSH-Key

## SSH-Authentifizierung

Wenn der Installer bereits direkt auf dem Kundensystem gestartet wird, ist der lokale Modus empfohlen. Dabei wird in Punkt **1 Zielsystem** keine SSH-Verbindung aufgebaut; die Installation laeuft direkt auf dem aktuellen System.

Lokaler Modus mit gespeicherter Konfiguration:

```bash
odoo-installer --config run-config.json --local --yes
```

Remote-Modus per SSH:

Key/Agent (Standard):

```bash
odoo-installer --config run-config.json --yes
```

Linux-Passwort interaktiv abfragen:

```bash
odoo-installer --config run-config.json --ask-ssh-password --yes
```

Host-Key-Modi:

- `strict`: nur bereits bekannte Host Keys akzeptieren
- `accept-new`: neue Host Keys automatisch akzeptieren (empfohlen)
- `insecure`: Host-Key-Pruefung deaktivieren (nur Test/Lab)

Beispiel bei `Host key verification failed`:

```bash
odoo-installer --config run-config.json --ask-ssh-password --ssh-host-key-mode accept-new --yes
```

## Custom-Addons

Im interaktiven Schritt **3 Custom-Addons** kann der Installer Kunden- oder Partner-Addons vorbereiten.

Verhalten:

- `<install_dir>/custom-addons` wird standardmaessig angelegt und in `addons_path` aufgenommen.
- Weitere absolute Pfade koennen ueber `custom_addons_paths` ergaenzt werden.
- Git-Repositories koennen ueber `custom_addons_repositories` als Odoo-Systembenutzer geklont oder aktualisiert werden.
- Repository-Ziele werden ebenfalls in `addons_path` aufgenommen.
- `requirements.txt` aus Addon-Repositories wird nur installiert, wenn `custom_addons_install_python_requirements` auf `true` gesetzt ist.

Beispiel:

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

Die erzeugte Odoo-Konfiguration enthaelt danach z. B.:

```text
addons_path = /opt/odoo/src/odoo/odoo/addons,/opt/odoo/src/odoo/addons,/opt/odoo/custom-addons,/srv/odoo/customer-addons,/opt/odoo/custom-addons/customer
```

## AHD Support-Zugriff

Im interaktiven Schritt **6 AHD Support-Zugriff** kann ein dedizierter Support-Benutzer fuer IT-Service AHD eingerichtet werden.

Bei Aktivierung erzeugt der Installer lokal automatisch ein eigenes RSA-4096-SSH-Key-Paar. Der Private Key wird im PEM-Format ausgegeben, damit Clients, die PEM verlangen, den Key direkt importieren koennen. Der Public Key wird fuer den Support-Benutzer auf dem Zielserver genutzt.

Standardwerte:

- Benutzer: `itservice-ahd-support`
- Vollstaendiger Name: `IT-Service AHD`
- Private-Key-Format: PEM (`-----BEGIN RSA PRIVATE KEY-----`)
- lokaler Key-Ordner: `~/.odoo-installer/support-keys/`

Der Ablauf:

1. Der Installer erzeugt oder verwendet lokal einen passenden SSH-Key unter `~/.odoo-installer/support-keys/`.
2. Der **Private Key** wird im Terminal angezeigt, damit du ihn kopieren kannst.
3. Kopiere den Private Key in deinen SSH-Client, z. B. Termius oder Termux.
4. Auf dem Zielserver legt der Installer den Benutzer `itservice-ahd-support` mit dem vollstaendigen Namen `IT-Service AHD` an.
5. Der Public Key wird in `/home/itservice-ahd-support/.ssh/authorized_keys` geschrieben.
6. Der Passwort-Login fuer den Support-Benutzer wird gesperrt.
7. Der Support-Benutzer erhaelt sudo-Zugriff ohne Passwort; die sudoers-Datei wird mit `visudo` geprueft.

Sicherheitshinweise:

- Der Private Key wird nicht in gespeicherte Konfigurationsdateien geschrieben.
- In der Konfigurationsuebersicht wird der Public Key maskiert.
- Auf dem Kundensystem landet nur der Public Key.
- Den angezeigten Private Key nur in sichere SSH-Clients uebernehmen und nicht in Git, Tickets oder Kundendokumentation speichern.

Verbindung nach der Installation:

```bash
ssh -i ~/.odoo-installer/support-keys/<host>_itservice-ahd-support_rsa.pem itservice-ahd-support@<host>
```

Der exakte lokale Key-Pfad wird waehrend der Installation im Terminal angezeigt.

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

Hinweis: `ssh_password` und `support_ssh_private_key_path` werden beim Speichern absichtlich geleert. Der Private Key fuer den AHD Support-Zugriff bleibt lokal unter `~/.odoo-installer/support-keys/`.

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

- `--backup-dir`: Zielverzeichnis auf dem Remote-Server (Standard: `<install_dir>/backups`)
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
- Custom-Addons-Standardpfad unter `<install_dir>/custom-addons` sowie optional weitere Pfade/Repository-Ziele
- optionaler Support-Benutzer `itservice-ahd-support` mit Public-Key-Zugriff und gesperrtem Passwort-Login

Vor dem ersten Start initialisiert der Installer die konfigurierte Odoo-Datenbank automatisch mit dem Basismodul (`-i base --without-demo=all --stop-after-init`), falls die Datenbank noch keine Odoo-Tabellen enthaelt. Die erzeugte Odoo-Konfiguration enthaelt dabei sowohl den Core-Addon-Pfad `<install_dir>/src/odoo/odoo/addons` als auch `<install_dir>/src/odoo/addons`, `<install_dir>/custom-addons` und alle konfigurierten Custom-Addon-Pfade, damit Basis- und Kundenmodule gefunden werden. Dadurch ist die Weboberflaeche nach erfolgreicher Installation direkt unter dem konfigurierten HTTP-Port erreichbar.

## Fehlerbehandlung

- Bei einem Fehler stoppt der Installer am betroffenen Schritt.
- Die Fehlermeldung zeigt Schrittname, Kommando und Exit-Code an.
- Nach Korrektur kann der Installer erneut gestartet werden (idempotente Schritte, soweit moeglich).

### `500 Internal Server Error` beim ersten Aufruf von Odoo

Wenn `http://localhost:8069` direkt nach einer Installation mit einem HTTP-500-Fehler antwortet, pruefe zuerst den Odoo-Log:

```bash
sudo tail -n 100 /opt/odoo/logs/odoo.log
```

Bei aelteren Installer-Staenden konnte die PostgreSQL-Datenbank angelegt, aber noch nicht als Odoo-Datenbank initialisiert sein. Wenn der Odoo-Log `unsupported Unicode escape sequence` und `server's encoding SQL_ASCII` meldet, wurde die Datenbank mit falschem Encoding angelegt. Aktualisiere in diesem Fall den Installer und starte ihn lokal erneut:

```bash
git pull
odoo-installer --config run-config.json --local --yes
```

Der Lauf ist idempotent und initialisiert eine noch leere Odoo-Datenbank nachtraeglich. Noch nicht initialisierte Datenbanken mit Nicht-UTF8-Encoding werden automatisch mit UTF8 neu angelegt.
