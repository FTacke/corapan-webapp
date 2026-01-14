# Troubleshooting

**Scope:** Häufige Probleme und Lösungen  
**Source-of-truth:** Praxiserfahrung, Error Logs

## Auth-Probleme

### Login funktioniert nicht

**Symptom:** `Invalid credentials` trotz korrektem Passwort

**Diagnose:**
```bash
# DB-Verbindung prüfen
docker exec -it corapan-postgres psql -U corapan -d corapan_auth -c "SELECT username, is_active FROM users;"
```

**Mögliche Ursachen:**
1. **Account deaktiviert:** `is_active = false`
2. **Account gelöscht:** `deleted_at IS NOT NULL`
3. **Password-Hash falsch:** Initial Admin neu erstellen
4. **DB nicht erreichbar:** Siehe "DB-Probleme"

**Lösung:**
```bash
# Initial Admin neu erstellen
python scripts/create_initial_admin.py
```

---

### JWT-Token ungültig

**Symptom:** `401 Unauthorized` bei geschützten Routes

**Diagnose:**
```javascript
// Browser Console
document.cookie  // Prüfe ob JWT-Cookies gesetzt sind
```

**Mögliche Ursachen:**
1. **Cookie-Domain falsch:** `SESSION_COOKIE_SECURE=true` aber HTTP (nicht HTTPS)
2. **JWT_SECRET_KEY geändert:** Tokens ungültig geworden
3. **Token abgelaufen:** Access Token Lifetime (60min)

**Lösung:**
```bash
# Dev: HTTPS-Requirement deaktivieren
export FLASK_ENV=development

# Prod: Sicherstellen dass HTTPS aktiv ist
curl -I https://corapan.hispanistica.com
```

---

## DB-Probleme

### Connection refused

**Symptom:** `psycopg2.OperationalError: could not connect to server`

**Diagnose:**
```bash
# PostgreSQL läuft?
docker ps | grep postgres

# Port erreichbar?
telnet localhost 5432
```

**Lösung:**
```bash
# Docker Service starten
docker-compose -f docker-compose.dev-postgres.yml up -d

# Oder Neustart
docker-compose restart
```

---

### Migration failed

**Symptom:** `relation "users" does not exist`

**Lösung:**
```bash
# Migrations neu ausführen
psql -U corapan -h localhost -d corapan_auth -f migrations/0001_create_auth_schema_postgres.sql
psql -U corapan -h localhost -d corapan_auth -f migrations/0002_create_analytics_tables.sql
```

---

## BlackLab-Probleme

### Search timeout

**Symptom:** Suche lädt ewig, dann Timeout

**Diagnose:**
```bash
# BlackLab Server läuft?
curl http://localhost:8080/blacklab-server/

# Logs prüfen
docker logs corapan-blacklab -f
```

**Lösung:**
```bash
# BlackLab neu starten
docker restart corapan-blacklab

# Index neu laden (falls korrupt)
docker exec corapan-blacklab rm -rf /data/index/*
# Dann Index neu erstellen (siehe Dokumentation)
```

---

## Static Files nicht gefunden

**Symptom:** `404 Not Found` für `/static/css/...`

**Diagnose (Dev):**
```bash
# Dateien vorhanden?
ls -la static/css/
```

**Diagnose (Prod):**
```bash
# Nginx serviert?
curl -I https://corapan.hispanistica.com/static/css/layout.css

# Dateien auf Host?
ls -la /var/www/corapan/static/
```

**Lösung (Prod):**
```bash
# Static Files kopieren
rsync -av static/ /var/www/corapan/static/

# Nginx neu laden
sudo nginx -t
sudo systemctl reload nginx
```

---

## Port bereits belegt

**Symptom (Dev):** `Address already in use: 8000`

**Diagnose:**
```powershell
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

**Lösung:**
```powershell
# Windows: Prozess beenden
taskkill /PID <PID> /F

# Linux/Mac
kill -9 <PID>
```

---

## Docker-Probleme

### Container startet nicht

**Diagnose:**
```bash
docker ps -a  # Alle Container (auch gestoppte)
docker logs corapan-container
```

**Mögliche Ursachen:**
1. **Port-Konflikt:** 6000 bereits belegt
2. **Volume-Problem:** Pfad existiert nicht
3. **Health Check fehlgeschlagen:** App startet nicht

**Lösung:**
```bash
# Container neu bauen
docker-compose build --no-cache
docker-compose up -d

# Volumes prüfen
docker volume ls
docker volume inspect <volume-name>
```

---

### Health Check failed

**Symptom:** Container wird als "unhealthy" markiert

**Diagnose:**
```bash
# Health Check manuell ausführen
docker exec corapan-container curl -f http://localhost:8000/health
```

**Lösung:**
```bash
# Logs prüfen (meist App-Fehler beim Start)
docker logs corapan-container

# Gunicorn-Prozesse prüfen
docker exec corapan-container ps aux | grep gunicorn
```

---

## Performance-Probleme

### Langsame Requests

**Diagnose:**
```bash
# Gunicorn Worker-Anzahl prüfen
docker exec corapan-container ps aux | grep gunicorn | wc -l

# CPU/Memory
docker stats corapan-container
```

**Lösung:**
```dockerfile
# Mehr Workers (in Dockerfile)
CMD ["gunicorn", "--workers", "8", ...]

# Container neu bauen
docker-compose build
docker-compose up -d
```

---

## HTTPS/SSL-Probleme

### Certificate invalid

**Diagnose:**
```bash
curl -vI https://corapan.hispanistica.com
```

**Lösung:**
```bash
# Let's Encrypt neu beziehen
sudo certbot --nginx -d corapan.hispanistica.com --force-renewal

# Nginx neu starten
sudo systemctl restart nginx
```

---

## Log-Übersicht

| Log-Datei | Zweck | Pfad |
|-----------|-------|------|
| App-Logs | Flask Application | `logs/app.log` |
| Gunicorn Access | HTTP-Requests | stdout (Docker) |
| Gunicorn Error | Gunicorn-Fehler | stderr (Docker) |
| Docker-Logs | Container-Lifecycle | `docker logs <container>` |
| Nginx Access | Reverse Proxy | `/var/log/nginx/access.log` |
| Nginx Error | Proxy-Fehler | `/var/log/nginx/error.log` |

---

## Debugging-Checkliste

1. [ ] **Services laufen?** `docker ps`
2. [ ] **Health Check OK?** `curl http://localhost:6000/health`
3. [ ] **Logs prüfen** `docker logs corapan-container -f`
4. [ ] **DB erreichbar?** `psql -U corapan -h localhost -d corapan_auth`
5. [ ] **ENV-Vars gesetzt?** `docker exec corapan-container env | grep FLASK`
6. [ ] **Static Files vorhanden?** `ls -la /var/www/corapan/static/`
7. [ ] **Nginx läuft?** `sudo systemctl status nginx`
8. [ ] **SSL gültig?** `curl -vI https://corapan.hispanistica.com`

---

## Weiterführende Hilfe

- **Docker Issues:** [docs/architecture/deployment-runtime.md](../architecture/deployment-runtime.md)
- **Auth Issues:** [docs/architecture/security-auth.md](../architecture/security-auth.md)
- **DB Issues:** [docs/architecture/data-model.md](../architecture/data-model.md)
- **Dev Setup:** [docs/operations/local-dev.md](local-dev.md)
