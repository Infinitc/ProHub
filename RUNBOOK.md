# 🚀 ProHub v2.0 Deployment Runbook
## Python 3.13 - Ohne Virtual Environment

**Geschätzte Dauer:** 30-40 Minuten

---

# SCHRITT 1: Server-Verbindung

```bash
ssh root@YOUR_SERVER_IP
```

---

# SCHRITT 2: System aktualisieren

```bash
apt update && apt upgrade -y
apt install -y git curl wget vim nano htop unzip
```

---

# SCHRITT 3: PostgreSQL installieren

```bash
apt install -y postgresql postgresql-contrib
systemctl start postgresql
systemctl enable postgresql
systemctl status postgresql
```

✅ **Erwartung:** "active (running)"

---

# SCHRITT 4: Datenbank erstellen

```bash
sudo -u postgres psql
```

**In PostgreSQL:**

```sql
CREATE DATABASE prohub_db;
CREATE USER prohub_user WITH PASSWORD 'dein_sicheres_passwort_hier';
GRANT ALL PRIVILEGES ON DATABASE prohub_db TO prohub_user;
\c prohub_db
GRANT ALL ON SCHEMA public TO prohub_user;
\q
```

**Test:**
```bash
psql -U prohub_user -d prohub_db -h localhost
# \q zum Beenden
```

---

# SCHRITT 5: Python & Build-Tools

```bash
apt install -y python3 python3-pip python3-dev build-essential libpq-dev gcc

python3 --version
# Sollte Python 3.13 oder 3.12 zeigen
```

---

# SCHRITT 6: Projektverzeichnis

```bash
mkdir -p /var/www/prohub
cd /var/www/prohub
```

---

# SCHRITT 7: Dateien hochladen

**Auf deinem PC:**

```bash
scp prohub-v2-python313-final.tar.gz root@YOUR_SERVER_IP:/var/www/prohub/
```

**Auf dem Server:**

```bash
cd /var/www/prohub
tar -xzf prohub-v2-python313-final.tar.gz
cd prohub-final
ls -la
# Du solltest sehen: backend/ frontend/ RUNBOOK.md etc.
```

---

# SCHRITT 8: Backend Dependencies installieren

```bash
cd /var/www/prohub/prohub-final/backend

# requirements.txt ist schon im Paket enthalten!
# Direkt installieren (OHNE venv):
pip3 install -r requirements.txt --break-system-packages
```

✅ **Erwartung:** Viele "Successfully installed..." Meldungen  
⚠️ **Warnungen über "externally managed" sind OK!**

---

# SCHRITT 9: .env konfigurieren

```bash
cd /var/www/prohub/prohub-final/backend

cp .env.example .env
nano .env
```

**Ändere:**

```env
DATABASE_URL=postgresql://prohub_user:dein_passwort_von_schritt4@localhost/prohub_db
SECRET_KEY=GENERIERE_MICH_GLEICH
```

**Speichern:** `STRG + O` → Enter → `STRG + X`

**Secret Key generieren:**

```bash
openssl rand -hex 32
# Kopiere die Ausgabe
```

**Nochmal .env öffnen und SECRET_KEY ersetzen:**

```bash
nano .env
```

**Speichern:** `STRG + O` → `STRG + X`

---

# SCHRITT 10: Datenbank-Tabellen erstellen

```bash
cd /var/www/prohub/prohub-final/backend

python3 -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"
```

✅ **Erwartung:** Keine Fehler

---

# SCHRITT 11: Backend testen

```bash
cd /var/www/prohub/prohub-final/backend

python3 main.py
```

✅ **Erwartung:**
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Im Browser:** `http://YOUR_SERVER_IP:8000/docs`

✅ **Du solltest sehen:** Swagger API Dokumentation

**Teste:** `/api/health` → Try it out → Execute  
**Antwort:** `{"status": "healthy", "version": "2.0.0"}`

**Backend stoppen:** `STRG + C`

---

# SCHRITT 12: Nginx installieren

```bash
apt install -y nginx
systemctl start nginx
systemctl enable nginx
systemctl status nginx
```

✅ **Erwartung:** "active (running)"

---

# SCHRITT 13: Nginx konfigurieren

```bash
nano /etc/nginx/sites-available/prohub
```

**Kopiere rein:**

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.com;
    # ODER: server_name YOUR_SERVER_IP;
    
    client_max_body_size 50M;

    location / {
        root /var/www/prohub/prohub-final/frontend;
        try_files $uri $uri/ /login.html;
        index login.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
    }

    location /caldav {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

**Speichern:** `STRG + O` → `STRG + X`

**Aktivieren:**

```bash
ln -s /etc/nginx/sites-available/prohub /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

---

# SCHRITT 14: Systemd Service (OHNE venv!)

```bash
nano /etc/systemd/system/prohub.service
```

**Kopiere rein:**

```ini
[Unit]
Description=ProHub v2.0 FastAPI Application
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/prohub/prohub-final/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Wichtig:** 
- ✅ Kein venv Path!
- ✅ Nutzt direkt `/usr/bin/python3`

**Speichern:** `STRG + O` → `STRG + X`

**Aktivieren:**

```bash
systemctl daemon-reload
systemctl enable prohub
systemctl start prohub
systemctl status prohub
```

✅ **Erwartung:** "active (running)"

---

# SCHRITT 15: SSL (Optional)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

---

# SCHRITT 16: Firewall

```bash
apt install -y ufw
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

---

# SCHRITT 17: Finale Tests

### Test 1: API
```bash
curl http://localhost:8000/api/health
```

### Test 2: Frontend
**Browser:** `http://YOUR_SERVER_IP`

### Test 3: Registrierung
1. Username: `testuser`
2. Passwort: `test123456`

### Test 4: API Docs
**Browser:** `http://YOUR_SERVER_IP/docs`

---

# 🎉 FERTIG!

**Zugriff:**
- App: http://YOUR_SERVER_IP
- API Docs: http://YOUR_SERVER_IP/docs
- CalDAV: http://YOUR_SERVER_IP/caldav

---

# 📊 WARTUNG

## Logs
```bash
journalctl -u prohub -f
```

## Neu starten
```bash
systemctl restart prohub
```

## Backup
```bash
sudo -u postgres pg_dump prohub_db > backup.sql
```

---

# 🆘 TROUBLESHOOTING

## Service startet nicht
```bash
journalctl -u prohub -n 100
# Prüfe .env und DB-Verbindung
```

## 502 Bad Gateway
```bash
systemctl status prohub
systemctl restart prohub
```

---

**Fertig! App läuft! 🚀**
