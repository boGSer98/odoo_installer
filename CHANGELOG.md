# CHANGELOG

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
