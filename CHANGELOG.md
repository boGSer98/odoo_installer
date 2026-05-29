# CHANGELOG

## Unreleased

- Restic-Snapshots und Repository-Checks koennen jetzt ueber `--restic-snapshots` und `--restic-check --restic-read-data-subset <WERT>` ausgefuehrt werden; eine neue Testlauf-Anleitung beschreibt Installation, nachtraegliche Custom-Addon-Repositories und Backup-Pruefung.
- Restic Cloud-Backups koennen jetzt ueber `backup_enabled` eingerichtet werden; der Installer installiert `restic`, schreibt `/etc/odoo-backup/env`, erzeugt `/usr/local/sbin/odoo-backup`, legt `/etc/cron.d/odoo-backup` an und wendet daily/weekly/monthly Retention an.
- Custom-Addons koennen jetzt ueber `custom_addons_paths` und `custom_addons_repositories` eingerichtet werden; der Installer legt Pfade an, synchronisiert Git-Repositories, ergaenzt `addons_path` und kann optional Repository-`requirements.txt` installieren.
- PostgreSQL-Datenbanken werden mit UTF8-Encoding (`--encoding=UTF8 --locale=C.UTF-8 --template=template0`) angelegt; noch nicht initialisierte SQL_ASCII-Datenbanken werden automatisch neu erstellt, damit Odoo Unicode/JSON-Daten laden kann.
- Odoo-Datenbankinitialisierung nutzt jetzt ein mehrzeiliges Shell-Skript ohne `||`-Kurzschlussoperatoren und gibt bei Fehlern Vorabdiagnosen sowie die letzten 120 Odoo-Logzeilen aus.
- Odoo-Konfiguration schreibt jetzt auch den Core-Addon-Pfad `<install_dir>/src/odoo/odoo/addons`, damit `base` bei der Erstinitialisierung gefunden wird.
- Leere Odoo-Datenbanken werden vor dem ersten Service-Start automatisch mit dem Basismodul initialisiert, um HTTP-500-Fehler durch uninitialisierte Datenbanken zu vermeiden.
- Lokalen Ausfuehrungsmodus (`--local`) hinzugefuegt, damit der Installer direkt auf dem Kundensystem ohne zusaetzliche SSH-Verbindung laufen kann.
- AHD Support-Key-Erzeugung auf RSA Private Key im PEM-Format umgestellt.
- Installationsanleitung und Anwenderanleitung um den automatisch erzeugten AHD Support-SSH-Key, den Benutzer `itservice-ahd-support` und den vollstaendigen Namen `IT-Service AHD` ergaenzt.

## 0.1.6 - 2026-05-24

- Terminal-Statusleiste fuer den Installationsfortschritt hinzugefuegt (Prozent + `x/y` Kommandos).
- Linux-Installationsanleitung als separates Dokument hinzugefuegt (`docs/Installationsanleitung_Linux.md`).

## 0.1.5 - 2026-05-24

- SSH-Authentifizierung um Passwortmodus erweitert (interaktiv via `--ask-ssh-password`).
- SSH Host-Key-Modus konfigurierbar gemacht (`strict`, `accept-new`, `insecure`).
- `--save-config` speichert das SSH-Passwort bewusst nicht persistent.
- Tests fuer SSH-Optionserzeugung und Host-Key-Validierung ergaenzt.

## 0.1.4 - 2026-05-24

- Backup-Retention hinzugefuegt (`--backup-keep-last N`), um alte DB-Backups automatisch zu bereinigen.
- Validierung fuer Retention-Optionen in der CLI ergaenzt.
- Unit-Test fuer Retention-Kommandoerzeugung hinzugefuegt.

## 0.1.3 - 2026-05-24

- Remote Backup-Funktion hinzugefuegt (`--backup`) mit `zip`/`dump`-Format.
- Remote Restore-Funktion hinzugefuegt (`--restore <REMOTE_BACKUP_PATH>`).
- Zusatzauswahl fuer Backup/Restore eingebaut (`--backup-dir`, `--backup-name`, `--no-filestore`, `--neutralize`).
- Installer-Konfiguration um `data_dir` erweitert und in die erzeugte Odoo-Konfiguration geschrieben.
- Neue Unit-Tests fuer Backup/Restore-Kommandosequenzen ergaenzt.

## 0.1.2 - 2026-05-24

- Optionalen Rollback-Modus bei Fehlschlag hinzugefuegt (`--rollback-on-fail`).
- Rollback-Kommandos fuer Odoo-Service- und Nginx-Schritte eingefuehrt (best effort).
- Resume-State wird nach aktivem Rollback aus Sicherheitsgruenden geloescht.
- Unit-Tests fuer Rollback-Reihenfolge und Fehlerverhalten ergaenzt.

## 0.1.1 - 2026-05-24

- Resume-Funktion mit lokaler State-Datei implementiert (`--resume`, `--state-file`).
- Schutz gegen Resume mit geaenderter Konfiguration per Konfigurations-Hash hinzugefuegt.
- Pipeline erweitert, um bereits erfolgreich ausgefuehrte Kommandos gezielt zu ueberspringen.
- Anwenderdokumentation fuer Resume-Lauf aktualisiert.

## 0.1.0 - 2026-05-24

- Initiales Projektgeruest fuer `odoo_installer` erstellt.
- Interaktive CLI mit gefuehrten Abfragen und Konfigurationsvalidierung implementiert.
- SSH-basierte Preflight- und Installationspipeline fuer Ubuntu 24.04 angelegt.
- Odoo-Installation aus `odoo/odoo` Branch `19.0` inklusive `systemd`-Service umgesetzt.
- Optionale Bausteine fuer Nginx, Certbot und UFW hinzugefuegt.
- Erste Anwenderanleitung in `docs/Anwenderanleitung.md` dokumentiert.
