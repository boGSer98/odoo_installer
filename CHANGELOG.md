# CHANGELOG

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
