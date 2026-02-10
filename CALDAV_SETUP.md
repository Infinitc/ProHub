# 📱 CalDAV Setup - Apple Calendar Sync

## iPhone/iPad Setup

1. Einstellungen → Kalender → Accounts
2. Account hinzufügen → Andere → CalDAV-Account
3. Server: `deine-domain.com` (oder IP)
4. Benutzername: Dein ProHub Username
5. Passwort: Dein ProHub Passwort
6. Fertig! ✅

## Mac Setup

1. Systemeinstellungen → Internet-Accounts
2. Anderen Account hinzufügen → CalDAV-Account
3. Serveradresse: `deine-domain.com/caldav`
4. Benutzername & Passwort eingeben
5. Fertig! ✅

## Test

1. Erstelle Event in ProHub → erscheint in Apple Kalender
2. Erstelle Event in Apple → erscheint in ProHub

## Troubleshooting

- Server URL: Mit HTTPS: Port 443, ohne: Port 80
- Falls Fehler: ProHub Backend läuft? `systemctl status prohub`
- Firewall: Ports 80/443 offen? `ufw status`

**Mehr Details im RUNBOOK.md**
