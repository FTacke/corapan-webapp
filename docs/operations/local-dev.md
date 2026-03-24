# Local Development

Use the root workspace as the canonical development entry point.

## Source of Truth

- `../docker-compose.dev-postgres.yml`
- `../scripts/dev-setup.ps1`
- `../scripts/dev-start.ps1`

`runtime/corapan` inside the repository is not a valid development fallback.

## Quick Start

```powershell
cd ..
.\scripts\dev-setup.ps1
```

Daily restart:

```powershell
.\scripts\dev-start.ps1
```

## Required Local Layout

The canonical dev layout is the workspace root with sibling runtime folders:

```text
CORAPAN/
    app/
    data/
    media/
```

The dev scripts set:

- `CORAPAN_RUNTIME_ROOT` to the workspace root
- `CORAPAN_MEDIA_ROOT` to `CORAPAN/media`
- `AUTH_DATABASE_URL` to the local PostgreSQL DSN
- `BLS_BASE_URL` and `BLS_CORPUS` for the local BlackLab stack

## Ports

- app: `http://localhost:8000`
- auth database: `localhost:54320`
- BlackLab: `http://localhost:8081/blacklab-server`

## Optional Local Overrides

Use `app/.env.example` as the reference for a local `.env` file. The dev scripts already provide the canonical defaults for normal local work.

## Statistics

Statistics files are runtime output under `data/public/statistics/` and are not versioned.

The maintenance pipeline that generates them is outside the scope of the app runtime contract.

## Validation

```powershell
cd app
pytest
ruff check src tests
```
```

---

## Troubleshooting

### Port bereits belegt
```powershell
# Port 8000 prüfen
netstat -ano | findstr :8000

# Prozess beenden
taskkill /PID <PID> /F
```

### Docker startet nicht
```powershell
# Docker Desktop Status prüfen
docker ps

# Services neu starten
docker-compose -f docker-compose.dev-postgres.yml restart
```

### DB-Migration schlägt fehl
```powershell
# DB löschen und neu erstellen
docker-compose -f docker-compose.dev-postgres.yml down -v
docker-compose -f docker-compose.dev-postgres.yml up -d
# Migration erneut ausführen
```

### Import-Fehler
```powershell
# Virtual Environment aktiviert?
.\.venv\Scripts\Activate.ps1

# Dependencies neu installieren
pip install -r requirements.txt --force-reinstall
```

---

## Docker Image Pinning (Determinismus)

### Warum Docker-Images pinnen?

Dev kann **plötzlich brechen**, wenn wir floating Tags wie `latest` verwenden:

```yaml
# ❌ NICHT SICHER:
image: instituutnederlandsetaal/blacklab:latest  # Wird jedes Mal neu gezogen!

# ✅ SICHER:
image: instituutnederlandsetaal/blacklab@sha256:3753dbce4fee...  # Immer gleich
```

**Problem mit `latest`:**
- Upstream ändert Image → Lokales System zieht neue Version
- Alte Index-Dateien sind nicht kompatibel mit neuer Version
- Container wird `unhealthy`, Container-Logs zeigen Deserialisierungsfehler
- Ursache ist nicht offensichtlich (sieht aus wie Zufall)

**Lösung: SHA256-Digest pinnen**
- Immer exakt die gleiche Version
- Reproduzierbar (alle Devs, alle Runs)
- Wenn Update nötig: expliziter Prozess mit Index-Rebuild

### Index und Image sind versionsgebunden

Der BlackLab-Index (`data/blacklab_index`) ist **an die Image-Version gebunden**:

- **Beim Image-Digest-Update**: Alten Index sichern und neu bauen
- **Nicht einfach übernehmen**: Alte Indizes sind oft nicht kompatibel

```powershell
# Wenn Image-Digest in docker-compose.yml geändert wird:
docker compose down
Rename-Item data/blacklab_index "blacklab_index.backup_$(Get-Date -Format yyyyMMdd_HHmmss)"
docker compose up -d
# Neuer Index wird automatisch initialisiert
```

### Weitere Informationen

Detaillierte Diagnostik und Lösungsschritte:
→ Siehe [docs/operations/blacklab_dev_health.md](./blacklab_dev_health.md)

---

## Extension Points

**Neue Dependencies hinzufügen:**
1. In `requirements.txt` eintragen
2. `pip install -r requirements.txt`
3. Für andere Entwickler committen

**Neue Umgebungsvariablen:**
1. In `.env` (lokal) hinzufügen
2. In `src/app/config/__init__.py` als `os.getenv()` definieren
3. Dokumentation in `docs/architecture/configuration.md` aktualisieren
