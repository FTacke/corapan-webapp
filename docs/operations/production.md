# Produktion

**Scope:** Production Deployment und Betrieb  
**Source-of-truth:** `infra/docker-compose.prod.yml`, `Dockerfile`, `scripts/deploy_prod.sh`

## Automated Deployment (GitHub Actions)

**Production uses automated deployment via GitHub self-hosted runner.**

When code is pushed to `main`:
1. GitHub Actions triggers [.github/workflows/deploy.yml](../../.github/workflows/deploy.yml)
2. Self-hosted runner on production server executes [scripts/deploy_prod.sh](../../scripts/deploy_prod.sh)
3. Script performs:
   - Git fetch/reset to latest main
   - Deployment via `docker-compose -f infra/docker-compose.prod.yml up -d --force-recreate --build`
   - **Mount verification** (runtime-first paths only)
   - Database setup

**Container Names:**
- Web: `corapan-web-prod`
- DB: `corapan-db-prod`

**Mount Requirements (Runtime-First):**
```
/app/data   ← /srv/webapps/corapan/runtime/corapan/data
/app/media  ← /srv/webapps/corapan/runtime/corapan/media
/app/logs   ← /srv/webapps/corapan/runtime/corapan/logs
/app/config ← /srv/webapps/corapan/runtime/corapan/config
```

**CRITICAL:** Legacy mounts (`/srv/webapps/corapan/{data,media,logs}`) are **NOT** allowed.  
Deploy script will fail if wrong mounts are detected.

**Server uses docker-compose v1** (`docker-compose` command, not `docker compose`).

---

## Manual Deployment (For Reference)

**Note:** Automated deployment via GitHub Actions is the standard process.  
Manual steps are documented here for troubleshooting or emergency scenarios.

### Voraussetzungen

- **Docker & Docker Compose (v1)** installiert
- **Nginx** konfiguriert (Reverse Proxy)
- **SSL-Zertifikate** (Let's Encrypt)
- **Domain** konfiguriert (DNS)
- **ENV-Secrets** gesetzt

---

## Manual Deployment Process

### 1. Code aktualisieren

```bash
cd /srv/webapps/corapan
git pull origin main
```

### 2. Secrets konfigurieren

**Host `passwords.env` (nicht in Git!):**
```bash
FLASK_SECRET_KEY=<64-char-hex-secret>
JWT_SECRET_KEY=<64-char-hex-secret>
POSTGRES_PASSWORD=<db-password>
CORAPAN_RUNTIME_ROOT=/srv/webapps/corapan/runtime/corapan
CORAPAN_MEDIA_ROOT=/srv/webapps/corapan/runtime/corapan/media
```

**Generierung:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Deploy mit docker-compose.prod.yml

**IMPORTANT: Use docker-compose v1 syntax:**
```bash
cd /srv/webapps/corapan
docker-compose -f infra/docker-compose.prod.yml up -d --force-recreate --build
```

### 4. Verify runtime-first mounts

```bash
docker inspect corapan-web-prod --format '{{range .Mounts}}{{println .Destination "<-" .Source}}{{end}}' | sort
```

Expected output should include:
```
/app/data <- /srv/webapps/corapan/runtime/corapan/data
/app/media <- /srv/webapps/corapan/runtime/corapan/media
/app/logs <- /srv/webapps/corapan/runtime/corapan/logs
/app/config <- /srv/webapps/corapan/runtime/corapan/config
```

### 5. Health Check

```bash
curl http://localhost:6000/health
# {"status": "ok"}
```

### 6. Logs prüfen

```bash
docker logs corapan-web-prod -f
```

---

## Runtime Roots (Source of Truth)

**Production runtime root:** `/srv/webapps/corapan/runtime/corapan`

App path resolution (evidence):
- Data root resolves to `${CORAPAN_RUNTIME_ROOT}/data` in [src/app/config/__init__.py](src/app/config/__init__.py#L66-L120).
- Media root is required via `CORAPAN_MEDIA_ROOT` in [src/app/config/__init__.py](src/app/config/__init__.py#L137-L154).
- Statistics root resolves from `CORAPAN_RUNTIME_ROOT` in [src/app/config/__init__.py](src/app/config/__init__.py#L159-L169).
- Advanced search docmeta reads from `DATA_ROOT/blacklab_export/docmeta.jsonl` in [src/app/search/advanced_api.py](src/app/search/advanced_api.py#L72-L77).

**Expected production roots:**
- Data: `/srv/webapps/corapan/runtime/corapan/data`
- Media: `/srv/webapps/corapan/runtime/corapan/media`

Sync scripts and docker mounts are aligned to these paths.

Metadata layout: `data/public/metadata/` is canonical; `latest/` is optional and preferred if present.

### BlackLab Export (Sync Decision)

Decision: **Keep syncing** `data/blacklab_export/` to runtime data root.

Evidence:
- **Runtime-required:** advanced search enriches results from `DATA_ROOT/blacklab_export/docmeta.jsonl` in [src/app/search/advanced_api.py](src/app/search/advanced_api.py#L72-L77).
- **Build-only (generation):** export and index scripts write to `data/blacklab_export/` in [src/scripts/blacklab_index_creation.py](src/scripts/blacklab_index_creation.py#L554-L563) and [scripts/blacklab/build_blacklab_index.ps1](scripts/blacklab/build_blacklab_index.ps1#L17-L39).

Rationale: the app reads `docmeta.jsonl` at runtime; syncing keeps advanced search metadata enrichment consistent with production.

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
docker stats corapan-web-prod
```

### Logs

```bash
# Live Logs
docker logs corapan-web-prod -f

# Letzte 100 Zeilen
docker logs corapan-web-prod --tail 100
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
    /srv/webapps/corapan/runtime/corapan/logs \
    /srv/webapps/corapan/runtime/corapan/data/counters

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
/srv/webapps/corapan/runtime/corapan/logs/blacklab_build_YYYY-MM-DD_HHMMSS.log
```

### Nach dem Rebuild

BlackLab-Server neu starten:
```bash
sudo bash /srv/webapps/corapan/app/scripts/blacklab/run_bls_prod.sh
```

---

## Troubleshooting

Siehe [docs/operations/troubleshooting.md](troubleshooting.md)
