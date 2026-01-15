# Produktion

**Scope:** Production Deployment und Betrieb  
**Source-of-truth:** `docker-compose.yml`, `Dockerfile`, `scripts/deploy_prod.sh`

## Voraussetzungen

- **Docker & Docker Compose** installiert
- **Nginx** konfiguriert (Reverse Proxy)
- **SSL-Zertifikate** (Let's Encrypt)
- **Domain** konfiguriert (DNS)
- **ENV-Secrets** gesetzt

---

## Deployment-Prozess

### 1. Code aktualisieren

```bash
cd ~/corapan-webapp
git pull origin main
```

### 2. Secrets konfigurieren

**Host `.env` (nicht in Git!):**
```bash
FLASK_SECRET_KEY=<64-char-hex-secret>
JWT_SECRET_KEY=<64-char-hex-secret>
AUTH_DATABASE_URL=postgresql://corapan:<password>@localhost:5432/corapan_auth
```

**Generierung:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Docker Image bauen

```bash
docker-compose build
```

### 4. Container starten

```bash
docker-compose up -d
```

### 5. Health Check

```bash
curl http://localhost:6000/health
# {"status": "ok"}
```

### 6. Logs prüfen

```bash
docker logs corapan-container -f
```

---

## Nginx-Konfiguration

**Datei:** `/etc/nginx/sites-available/corapan`

```nginx
upstream corapan_backend {
    server localhost:6000;
}

server {
    listen 443 ssl http2;
    server_name corapan.hispanistica.com;

    ssl_certificate /etc/letsencrypt/live/corapan.hispanistica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/corapan.hispanistica.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;

    location /static/ {
        alias /var/www/corapan/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://corapan_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
    }
}

server {
    listen 80;
    server_name corapan.hispanistica.com;
    return 301 https://$host$request_uri;
}
```

**Aktivieren:**
```bash
sudo ln -s /etc/nginx/sites-available/corapan /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL-Zertifikate (Let's Encrypt)

```bash
sudo certbot --nginx -d corapan.hispanistica.com
```

**Auto-Renewal:**
```bash
# Cron Job (prüft täglich)
0 3 * * * certbot renew --quiet
```

---

## Monitoring

### Container Status

```bash
docker ps
docker stats corapan-container
```

### Logs

```bash
# Live Logs
docker logs corapan-container -f

# Letzte 100 Zeilen
docker logs corapan-container --tail 100
```

### Health Check

```bash
curl https://corapan.hispanistica.com/health
```

---

## Backup

**Skript:** `scripts/backup.sh`

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p /backup/corapan

# PostgreSQL Dump
docker exec corapan-postgres pg_dump -U corapan corapan_auth > /backup/corapan/db_${DATE}.sql

# Logs, Counters
tar -czf /backup/corapan/data_${DATE}.tar.gz \
  ~/corapan/logs \
  ~/corapan/data/counters

echo "Backup completed: $DATE"
```

**Cron Job:**
```cron
0 3 * * * /path/to/scripts/backup.sh
```

---

## Restart

```bash
# Graceful Restart (Zero-Downtime)
docker-compose restart

# Hard Restart
docker-compose down
docker-compose up -d
```

---

## Rollback

```bash
# Zu vorherigem Commit
git checkout <previous-commit-hash>
docker-compose build
docker-compose up -d
```

---

## BlackLab Index Rebuild (Production)

**Skript:** `scripts/blacklab/build_blacklab_index_prod.sh`

Der Index-Rebuild erfolgt mit mehrfacher Validierung und automatischem Rollback bei Fehlern.

### Sicherheits-Mechanismen

1. **Strikte Exit-Codes:** Script bricht bei jedem Fehler ab (`set -euo pipefail`)
2. **Pre-Validation:** Prüfung von Dateizahl (>20), Größe (>50MB), BlackLab-Strukturdateien
3. **Post-Validation:** Test-Container startet neuen Index und prüft `documentCount > 0` und `tokenCount > 0`
4. **Atomischer Swap:** Backup mit Timestamp, erst nach erfolgreicher Validierung
5. **Auto-Rollback:** Bei fehlgeschlagenem Swap wird automatisch auf Backup zurückgesetzt

### Ausführung

```bash
sudo bash /srv/webapps/corapan/app/scripts/blacklab/build_blacklab_index_prod.sh
```

**Dauer:** Ca. 10-30 Minuten (je nach Datenmenge)

**Memory-Settings** (für Low-RAM Hosts)

Default: `JAVA_XMX=1400m JAVA_XMS=512m` (läuft auf 4GB-RAM Hosts)

```bash
# Custom Java heap (z.B. bei mehr RAM verfügbar)
JAVA_XMX=2000m JAVA_XMS=512m bash /srv/webapps/corapan/app/scripts/blacklab/build_blacklab_index_prod.sh

# Mit Docker Memory-Limits (optional)
DOCKER_MEM=2500m DOCKER_MEMSWAP=3g JAVA_XMX=2000m bash /srv/webapps/corapan/app/scripts/blacklab/build_blacklab_index_prod.sh
```

**Troubleshooting OOM:**
- Exit-Code 137 = Out of Memory
- Lösung: `JAVA_XMX` reduzieren (z.B. `JAVA_XMX=1000m`)

**Optional:** Input-Cleanup aktivieren (Standard: behalten)
```bash
CLEAN_INPUTS=1 bash /srv/webapps/corapan/app/scripts/blacklab/build_blacklab_index_prod.sh
```

### Log-Überwachung

Timestamped Logs unter:
```
/srv/webapps/corapan/data/logs/blacklab_build_YYYY-MM-DD_HHMMSS.log
```

### Nach dem Rebuild

BlackLab-Server neu starten:
```bash
sudo bash /srv/webapps/corapan/app/scripts/blacklab/run_bls_prod.sh
```

---

## Troubleshooting

Siehe [docs/operations/troubleshooting.md](troubleshooting.md)
