# Deployment & Runtime

**Scope:** Wie die Anwendung in Produktion läuft  
**Source-of-truth:** `Dockerfile`, `docker-compose.yml`, `infra/docker-compose.prod.yml`, `scripts/start_waitress.py`

## Production-Stack

```
┌────────────────────────────────────────────────────┐
│  Internet (HTTPS: 443)                             │
└──────────────────┬─────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────┐
│  Nginx Reverse Proxy (Host-System)                 │
│  - HTTPS Termination (Let's Encrypt)               │
│  - Static File Serving (/static/*)                 │
│  - Proxy Pass → http://localhost:6000              │
└──────────────────┬─────────────────────────────────┘
                   │ HTTP
┌──────────────────▼─────────────────────────────────┐
│  Docker Container: corapan-container               │
│  - Exposed Port: 6000 → 8000 (intern)              │
│  - Image: corapan-webapp:latest                    │
│  - Restart: unless-stopped                         │
│  - Health Check: curl http://localhost:8000/health │
└──────────────────┬─────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────┐
│  Gunicorn WSGI Server                              │
│  - Workers: 4                                      │
│  - Bind: 0.0.0.0:8000                              │
│  - Timeout: 120s                                   │
│  - App: src.app.main:app                           │
└──────────────────┬─────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────┐
│  Flask Application (src/app/)                      │
│  - Umgebung: FLASK_ENV=production                  │
│  - Debug: False                                    │
│  - Workers: 4 (parallel request handling)          │
└────────────────────────────────────────────────────┘
```

---

## Docker Image

### Multi-Stage Build

**Datei:** `Dockerfile`

```dockerfile
# Stage 1: Builder (Dependencies installieren)
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y build-essential libpq-dev
COPY requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt gunicorn>=21.2.0

# Stage 2: Runtime (Minimal Production Image)
FROM python:3.12-slim
RUN apt-get update && apt-get install -y \
    ffmpeg libsndfile1 curl libpq5 postgresql-client
RUN useradd -m -u 1000 -s /bin/bash corapan
WORKDIR /app
COPY --from=builder /root/.local /home/corapan/.local
COPY . .
USER corapan
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", \
     "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", \
     "src.app.main:app"]
```

**Optimierungen:**
- **Multi-Stage:** Build-Dependencies nur in Builder-Stage (reduziert Image-Größe)
- **Non-Root User:** Security Best Practice (User `corapan`, UID 1000)
- **Minimal Base:** `python:3.12-slim` (keine unnötigen Pakete)
- **Health Check:** `/health` Endpoint (siehe unten)

---

## Docker Compose

### Produktion

**Datei:** `docker-compose.yml` (Root)

```yaml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: corapan-container
    ports:
      - "6000:8000"  # Host:Container
    volumes:
      # Read-Only Volumes (Daten werden extern gepflegt)
      - ~/corapan/media/mp3-full:/app/media/mp3-full:ro
      - ~/corapan/media/mp3-split:/app/media/mp3-split:ro
      - ~/corapan/media/transcripts:/app/media/transcripts:ro
      - ~/corapan/config/keys:/app/config/keys:ro
      - ~/corapan/data/db:/app/data/db:ro
      
      # Read-Write Volumes (App schreibt)
      - ~/corapan/data/counters:/app/data/counters
      - ~/corapan/logs:/app/logs
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
    
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

networks:
  default:
    name: corapan-network
```

**Wichtig:**
- **Read-Only Volumes:** Audio/Transkripte/Daten werden extern gepflegt (kein Schreibzugriff durch App nötig)
- **Logs:** Persistent auf Host (`~/corapan/logs`)
- **Resource Limits:** Verhindert OOM auf kleinen VPS
- **Health Check:** Automatischer Restart bei Fehlern

---

## Gunicorn

### Konfiguration

**Command (in Dockerfile):**
```bash
gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  src.app.main:app
```

**Parameter:**
- `--workers 4`: 4 Worker-Prozesse (parallel request handling)
  - **Faustregel:** `(2 × CPU_CORES) + 1`
  - Beispiel: 2 CPU Cores → 5 Workers
- `--timeout 120`: Max. Request-Zeit (2 Minuten)
  - Wichtig für lange Exporte/Searches
- `--access-logfile -`: Logs auf stdout (Docker fängt ab)
- `--error-logfile -`: Errors auf stderr

**Worker-Klasse:**
```bash
# Default: sync (ausreichend für die meisten Requests)
# Alternative: gevent (für viele Concurrent Connections)
gunicorn --worker-class gevent --workers 4 ...
```

**Aktuell:** Sync Worker (keine async nötig, da BlackLab Server externe Requests handled)

---

## Nginx Reverse Proxy

**Beispiel-Config (nicht im Repo):**

```nginx
# /etc/nginx/sites-available/corapan

upstream corapan_backend {
    server localhost:6000;
}

server {
    listen 443 ssl http2;
    server_name corapan.hispanistica.com;

    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/corapan.hispanistica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/corapan.hispanistica.com/privkey.pem;
    
    # SSL Hardening
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Static Files (direkt von Nginx serviert)
    location /static/ {
        alias /var/www/corapan/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy zu Gunicorn
    location / {
        proxy_pass http://corapan_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        
        # Timeouts für lange Requests (Exports)
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
    
    # Health Check (optionally public)
    location /health {
        proxy_pass http://corapan_backend;
        access_log off;
    }
}

# HTTP → HTTPS Redirect
server {
    listen 80;
    server_name corapan.hispanistica.com;
    return 301 https://$host$request_uri;
}
```

**Wichtig:**
- **X-Forwarded-* Headers:** Flask nutzt `ProxyFix` Middleware (siehe `src/app/__init__.py`)
- **Static Serving:** Nginx liefert `/static/` direkt (entlastet Flask)
- **Timeouts:** Müssen mit Gunicorn übereinstimmen (120s)

---

## Health Check

**Endpoint:** `GET /health`

**Implementierung (implizit in Flask):**
```python
# src/app/routes/public.py (oder separater Health Blueprint)
@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200
```

**Docker Health Check:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 3s
  retries: 3
```

**Bedeutung:**
- **Interval:** Alle 30s prüfen
- **Retries:** 3 Fehlversuche → Container als "unhealthy" markieren
- **Docker Restart:** Bei `restart: unless-stopped` wird Container neu gestartet

---

## Logging

### Container-Logs

**Docker:**
```bash
# Logs anzeigen (letzte 100 Zeilen)
docker logs corapan-container --tail 100 -f

# Logs in Datei speichern
docker logs corapan-container > /var/log/corapan-docker.log
```

### Anwendungs-Logs

**Flask Logging:**
```python
# src/app/__init__.py → setup_logging()
handler = RotatingFileHandler("logs/app.log", maxBytes=10485760, backupCount=5)
app.logger.addHandler(handler)
```

**Log-Files:**
- `logs/app.log` (Application Logs)
- `logs/gunicorn_access.log` (Gunicorn Access)
- `logs/gunicorn_error.log` (Gunicorn Errors)

**Rotation:**
- Max. 10 MB pro File
- 5 Backup-Dateien (total 50 MB)

**Persistenz:**
```yaml
# docker-compose.yml
volumes:
  - ~/corapan/logs:/app/logs
```

---

## Ports

| Port | Zweck | Extern? |
|------|-------|---------|
| 443 | HTTPS (Nginx) | Ja |
| 80 | HTTP Redirect → 443 | Ja |
| 6000 | Docker Exposed Port (Nginx → Container) | Nein (localhost) |
| 8000 | Gunicorn (intern im Container) | Nein |
| 8080 | BlackLab Server (separater Container) | Nein (Docker Network) |
| 5432 | PostgreSQL (externer Service oder Docker) | Nein |

**Firewall (Host):**
```bash
# Nur 80 und 443 offen für Internet
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## Static File Serving

### Entwicklung
```python
# Flask Dev-Server serviert /static/ automatisch
# Konfiguriert via static_folder in create_app()
app = Flask(__name__, static_folder="static")
```

### Produktion (Nginx)
```nginx
location /static/ {
    alias /var/www/corapan/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Deployment:**
```bash
# Static Files auf Host kopieren (beim Deploy)
rsync -av static/ /var/www/corapan/static/
```

**Vorteil:** Nginx ist **deutlich schneller** im Serving von Static Files als Flask/Gunicorn.

---

## Deployment-Prozess

**Skript:** `scripts/deploy_prod.sh`

1. **Code aktualisieren:** `git pull origin main`
2. **Dependencies prüfen:** `pip install -r requirements.txt` (im Container)
3. **Tests laufen lassen:** `pytest` (optional, empfohlen)
4. **Docker Image neu bauen:** `docker-compose build`
5. **Container neu starten:** `docker-compose down && docker-compose up -d`
6. **Health Check:** `curl http://localhost:6000/health`
7. **Logs prüfen:** `docker logs corapan-container -f`

**Zero-Downtime Deployment (Advanced):**
- Blue-Green Deployment (2 Container, Load Balancer)
- Rolling Update (Docker Swarm oder Kubernetes)

---

## Monitoring

### Docker Stats
```bash
docker stats corapan-container
```

### Resource Usage
```bash
# CPU/Memory im Container
docker exec corapan-container top
```

### Disk Usage
```bash
# Logs, Datenbanken, Exports
du -sh ~/corapan/logs
du -sh ~/corapan/data/exports
```

---

## Backup

**Skript:** `scripts/backup.sh`

```bash
#!/bin/bash
# Backup Auth-DB, Logs, Counters
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /backup/corapan_${DATE}.tar.gz \
  ~/corapan/data/db \
  ~/corapan/data/counters \
  ~/corapan/logs
```

**Cron Job:**
```cron
# Täglich um 3 Uhr
0 3 * * * /path/to/scripts/backup.sh
```

---

## Troubleshooting

### Container startet nicht
```bash
# Logs prüfen
docker logs corapan-container

# Manuell starten (Debug)
docker run -it --rm corapan-webapp:latest /bin/bash
```

### Health Check schlägt fehl
```bash
# Innerhalb des Containers testen
docker exec corapan-container curl http://localhost:8000/health

# Gunicorn-Prozesse prüfen
docker exec corapan-container ps aux | grep gunicorn
```

### Hohe CPU/Memory
```bash
# Worker reduzieren (in Dockerfile)
gunicorn --workers 2 ...

# Memory Limit erhöhen (in docker-compose.yml)
deploy:
  resources:
    limits:
      memory: 4G
```

### Static Files nicht serviert
```nginx
# Nginx Config prüfen
nginx -t

# Static Files auf Host vorhanden?
ls -la /var/www/corapan/static/
```

---

## Extension Points

**Neue Services hinzufügen:**
1. Service in `docker-compose.yml` definieren (z.B. Redis, Celery)
2. Network-Verbindung konfigurieren
3. ENV-Vars für Connection-Strings
4. Dependencies in `requirements.txt` hinzufügen

**Beispiel: Redis für Caching**
```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: corapan-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
```

```python
# src/app/config/__init__.py
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```
