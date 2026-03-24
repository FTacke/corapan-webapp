# Production

Use this document for the active production contract only.

## Source of Truth

- `app/infra/docker-compose.prod.yml`
- `app/Dockerfile`
- `app/scripts/deploy_prod.sh`
- `.github/workflows/deploy.yml`

## Required Environment

Production secrets remain outside Git in `passwords.env`.

Required variables:

- `FLASK_SECRET_KEY`
- `JWT_SECRET_KEY`
- `AUTH_DATABASE_URL`
- `BLS_BASE_URL`
- `BLS_CORPUS`
- `CORAPAN_RUNTIME_ROOT`
- `CORAPAN_MEDIA_ROOT`

`AUTH_DATABASE_URL` is the only valid auth/core database variable.

## Runtime Layout

Host roots:

- `/srv/webapps/corapan/data`
- `/srv/webapps/corapan/media`
- `/srv/webapps/corapan/logs`

Container mount targets:

- `/app/data`
- `/app/media`
- `/app/logs`
- `/app/config`

## Deployment Notes

- do not deploy from `main` without the normal workflow
- do not start legacy containers such as `corapan-webapp`
- BlackLab must be reachable through the production Docker network, not a host-port localhost shortcut

## Validation

Typical production checks:

- `docker compose -f infra/docker-compose.prod.yml config`
- `curl http://localhost:6000/health`
- container logs for `corapan-web-prod`

**Cron Job:**
```cron
0 3 * * * /path/to/scripts/backup.sh
```

---

## Restart

```bash
# Graceful Restart (Zero-Downtime)
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml restart

# Hard Restart
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml down
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d
```

---

## Rollback

```bash
# Zu vorherigem Commit
git checkout <previous-commit-hash>
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml build
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d
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
/srv/webapps/corapan/logs/blacklab_build_YYYY-MM-DD_HHMMSS.log
```

### Nach dem Rebuild

BlackLab-Server neu starten:
```bash
sudo bash /srv/webapps/corapan/app/scripts/blacklab/run_bls_prod.sh
```

---

## Troubleshooting

Siehe [docs/operations/troubleshooting.md](troubleshooting.md)
