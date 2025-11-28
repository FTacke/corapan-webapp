# CO.RA.PAN Deployment Guide

**Letzte Aktualisierung:** 2025-11-28

---

## 📋 Übersicht

Dieser Guide beschreibt das Deployment der CO.RA.PAN-Webapp auf dem Production-Server.

**Server-Setup:**
- Ubuntu Server mit Docker
- **PostgreSQL** für Auth-Datenbank (empfohlen)
- **BlackLab Server** für Corpus-Suche
- nginx als Reverse Proxy (Port 80/443 → 6000)
- VPN-Zugang erforderlich
- Media-Dateien werden extern verwaltet (nicht im Docker-Image)

---

## 🗄️ Datenbank-Konfiguration

### Production (Empfohlen): PostgreSQL

```bash
# Environment-Variable setzen
AUTH_DATABASE_URL=postgresql+psycopg://corapan_auth:<PASSWORD>@<HOST>:5432/corapan_auth
```

PostgreSQL bietet:
- Bessere Concurrency als SQLite
- Robuste ACID-Garantien
- Einfache Skalierung und Backups

### Fallback: SQLite (nur für einfache Setups)

```bash
AUTH_DATABASE_URL=sqlite:///data/db/auth.db
```

> ⚠️ SQLite ist nicht für Produktionsumgebungen mit hoher Last empfohlen.

---

## 🔑 Environment-Variablen

| Variable | Beschreibung | Beispiel |
|----------|-------------|----------|
| `FLASK_SECRET_KEY` | Flask Session Secret | `<random-secret>` |
| `JWT_SECRET_KEY` | JWT Signing Key | `<random-secret>` |
| `AUTH_DATABASE_URL` | Auth-DB Connection URL | `postgresql+psycopg://...` |
| `BLACKLAB_BASE_URL` | BlackLab Server URL | `http://localhost:8081/blacklab-server` |

---

## 🚀 Quick Start: Deployment

### Option 1: Automatisches Update (empfohlen)

```bash
# Auf dem Server via SSH
cd /root/corapan
./update.sh
```

Das war's! Das Script macht automatisch:
- ✅ Backup der Counter-Daten
- ✅ Git Pull der neuesten Änderungen
- ✅ Docker Image neu bauen
- ✅ Container neu starten
- ✅ Health Check

### Option 2: Manuelles Update (alter Workflow)

Siehe Abschnitt "Manuelles Deployment" weiter unten.

---

## 📦 Erstmaliges Server-Setup

### 1. Git Repository clonen

```bash
cd /root
git clone <your-git-repo-url> corapan
cd corapan
```

### 2. Verzeichnisstruktur auf Server erstellen

```bash
# Basis-Struktur
mkdir -p /root/corapan/{media,data,config,logs,backups}
mkdir -p /root/corapan/media/{mp3-full,mp3-split,mp3-temp,transcripts}
mkdir -p /root/corapan/data/{db,db_public,counters}
mkdir -p /root/corapan/config/keys
```

### 3. Dateien auf Server kopieren

**Von lokalem Rechner:**

```powershell
# Media-Dateien (initial, einmalig)
scp -r ./media/mp3-full/* user@server:/root/corapan/media/mp3-full/
scp -r ./media/mp3-split/* user@server:/root/corapan/media/mp3-split/
scp -r ./media/transcripts/* user@server:/root/corapan/media/transcripts/

# Datenbank (initial, einmalig)
scp -r ./data/db/* user@server:/root/corapan/data/db/

# Config (Passwörter, JWT-Keys)
scp ./passwords.env user@server:/root/corapan/
scp ./config/keys/* user@server:/root/corapan/config/keys/
```

### 4. Update-Script ausführbar machen

```bash
chmod +x /root/corapan/update.sh
```

### 5. Erstes Deployment

```bash
cd /root/corapan
./update.sh --no-backup  # Erstes Mal, kein Backup nötig
```

### 6. nginx Reverse Proxy konfigurieren (falls noch nicht)

**`/etc/nginx/sites-available/corapan`:**

```nginx
server {
    listen 80;
    server_name corapan.yourdomain.com;

    # Optional: Redirect to HTTPS
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://localhost:6000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket Support (falls benötigt)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Aktivieren:**

```bash
ln -s /etc/nginx/sites-available/corapan /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## 🔄 Workflow: Code-Änderungen deployen

### Lokaler Rechner (Windows)

```powershell
# 1. Änderungen committen
git add .
git commit -m "Beschreibung der Änderungen"

# 2. Zu Git pushen
git push origin main
```

### Server (über VPN + SSH)

```bash
# 3. Auf Server einloggen
ssh user@server

# 4. Update ausführen
cd /root/corapan
./update.sh
```

**Fertig!** ✅

---

## 📁 Neue Media-Dateien hinzufügen

Wenn neue Audio-Dateien und Transkripte hinzukommen:

### 1. Lokal: Datenbank neu erstellen

```powershell
# Neue Dateien zu media/ hinzufügen
# Dann DB neu generieren (verwende dein existierendes Script)
python LOKAL/database/database_creation_v2.py
```

### 2. Dateien auf Server kopieren

```powershell
# Neue Media-Dateien
scp -r ./media/mp3-full/neue-datei.mp3 user@server:/root/corapan/media/mp3-full/
scp -r ./media/mp3-split/neue-datei/* user@server:/root/corapan/media/mp3-split/

# Aktualisierte Datenbank
scp -r ./data/db/* user@server:/root/corapan/data/db/
```

### 3. Docker Container neustarten (damit DB neu geladen wird)

```bash
ssh user@server
cd /root/corapan
docker compose restart
```

---

## 🛠️ Nützliche Befehle

### Container Management

```bash
# Status prüfen
docker compose ps

# Logs anzeigen
docker compose logs -f
docker compose logs --tail=100

# Container neustarten
docker compose restart

# Container stoppen
docker compose down

# Container starten
docker compose up -d

# In Container einloggen (debugging)
docker exec -it corapan-container bash
```

### Update-Script Optionen

```bash
# Normales Update (mit Backup)
./update.sh

# Update ohne Backup (schneller)
./update.sh --no-backup

# Force Rebuild (ignoriert Docker Cache)
./update.sh --force

# Hilfe anzeigen
./update.sh --help
```

### Health Check

```bash
# App-Status prüfen
curl http://localhost:6000/health

# Von außen (mit nginx)
curl http://corapan.yourdomain.com/health
```

### Backups

```bash
# Backups anzeigen
ls -lh /root/corapan/backups/

# Backup manuell wiederherstellen
tar -xzf /root/corapan/backups/backup_20251019_143022.tar.gz -C /root/corapan/
```

---

## 🔧 Manuelles Deployment (alter Workflow)

Falls das Update-Script nicht funktioniert:

```bash
# 1. Code aktualisieren
cd /root/corapan
git pull origin main

# 2. Alten Container stoppen und löschen
docker stop corapan-container
docker rm corapan-container

# 3. Neues Image bauen
docker build -t corapan-app .

# 4. Container starten (mit allen Volumes)
docker run -d --name corapan-container \
  --restart unless-stopped \
  -p 6000:8000 \
  -v /root/corapan/media/mp3-full:/app/media/mp3-full:ro \
  -v /root/corapan/media/mp3-split:/app/media/mp3-split:ro \
  -v /root/corapan/media/mp3-temp:/app/media/mp3-temp \
  -v /root/corapan/media/transcripts:/app/media/transcripts:ro \
  -v /root/corapan/passwords.env:/app/passwords.env:ro \
  -v /root/corapan/config/keys:/app/config/keys:ro \
  -v /root/corapan/data/db:/app/data/db:ro \
  -v /root/corapan/data/counters:/app/data/counters \
  -v /root/corapan/logs:/app/logs \
  corapan-app

# 5. Health Check
sleep 5
curl http://localhost:6000/health
```

**Oder mit Docker Compose:**

```bash
docker compose down
docker compose build
docker compose up -d
```

---

## 🐛 Troubleshooting

### Problem: Container startet nicht

```bash
# Logs checken
docker compose logs

# Letzten Build-Fehler sehen
docker compose build

# Force rebuild
docker compose build --no-cache
```

### Problem: "Permission denied" auf Volumes

```bash
# Permissions auf Server prüfen
ls -la /root/corapan/data/counters/

# Falls nötig: Permissions anpassen
chmod -R 755 /root/corapan/data/counters/
```

### Problem: Health Check schlägt fehl

```bash
# Container läuft?
docker compose ps

# Port erreichbar?
curl http://localhost:6000/health

# Logs prüfen
docker compose logs --tail=50
```

### Problem: Git Pull schlägt fehl

```bash
# Uncommitted changes?
git status

# Falls ja: Stash oder Commit
git stash
git pull origin main
```

### Problem: Alte Images füllen Festplatte

```bash
# Alte Images löschen
docker image prune -a

# Alle ungenutzten Ressourcen löschen
docker system prune -a
```

---

## 📊 Monitoring

### Log-Dateien

```bash
# App-Logs (im Container)
docker compose logs -f

# App-Logs (auf Host persistiert)
tail -f /root/corapan/logs/corapan.log

# nginx Logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Resource Usage

```bash
# Container Stats (CPU, RAM, Network)
docker stats corapan-container

# Disk Usage
df -h
du -sh /root/corapan/*
```

---

## 🔐 Security Checklist

- [ ] `passwords.env` ist nur auf Server (nicht in Git!)
- [ ] JWT Keys sind nur auf Server (nicht in Git!)
- [ ] nginx HTTPS konfiguriert (Let's Encrypt)
- [ ] Firewall aktiv (nur VPN + Port 80/443)
- [ ] SSH Key-basiert (kein Passwort-Login)
- [ ] Regelmäßige Backups der Counter-Daten
- [ ] Logs werden rotiert (nicht unbegrenzt wachsen)

---

## 📝 Verzeichnisstruktur auf Server

```
/root/corapan/
├── src/                    # App-Code (aus Git)
├── static/                 # Frontend-Assets (aus Git)
├── templates/              # HTML-Templates (aus Git)
├── media/                  # Media-Dateien (NICHT in Git)
│   ├── mp3-full/          # Original-Audios
│   ├── mp3-split/         # Segmentierte Audios
│   ├── mp3-temp/          # Temp-Verarbeitung
│   └── transcripts/       # Transkript-Dateien
├── data/                   # Datenbank (NICHT in Git)
│   ├── db/                # SQLite-Datenbanken
│   └── counters/          # JSON-Counter-Dateien
├── config/                 # Credentials (NICHT in Git)
│   └── keys/              # JWT Public/Private Keys
├── logs/                   # Log-Dateien
├── backups/                # Automatische Backups
├── passwords.env           # Environment-Variablen (NICHT in Git)
├── docker-compose.yml      # Docker Compose Config (aus Git)
├── update.sh               # Update-Script (aus Git)
└── Dockerfile              # Docker Build (aus Git)
```

---

## 🚨 Emergency Rollback

Falls ein Update Probleme verursacht:

```bash
# 1. Letztes Backup wiederherstellen
cd /root/corapan
tar -xzf backups/backup_TIMESTAMP.tar.gz

# 2. Zum vorherigen Git-Commit zurück
git log --oneline  # Commit-Hash finden
git reset --hard <commit-hash>

# 3. Container neu bauen mit alter Version
docker compose down
docker compose build
docker compose up -d
```

---

## 📧 Support

Bei Problemen:
1. Logs prüfen: `docker compose logs -f`
2. Health Check: `curl http://localhost:6000/health`
3. Container Status: `docker compose ps`

**Hilfreich für Debugging:**
- Git Commit-Hash: `git rev-parse --short HEAD`
- Docker Image ID: `docker images corapan-app`
- Container Start-Zeit: `docker inspect corapan-container | grep StartedAt`

---

**Ende des Deployment-Guides**
