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

## Troubleshooting

Siehe [docs/operations/troubleshooting.md](troubleshooting.md)
