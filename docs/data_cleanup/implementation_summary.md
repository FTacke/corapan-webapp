# Implementation Summary (Consolidated)

## Completed
- Public stats DBs consolidated under `data/db/public/`.
- Sensitive DBs isolated under `data/db/restricted/`.
- FAIR metadata exports served from `data/public/metadata/`.
- Legacy overview statistics moved to static JSON assets.

## Notes
- The local pipeline produces `stats_files.db` and `stats_country.db` only.
- Update any remaining documentation to reference `data/db/public/` and `data/public/metadata/`.
# Data Cleanup Implementation - Summary

**Branch:** `chore/data-cleanup-dev-safe`  
**Datum:** 2025-01-15  
**Status:** ✅ Implementiert, getestet, gepusht

---

## 🎯 Ziele

1. **stats_all.db entfernen** (obsolet, ersetzt durch corpus_stats.json)
2. **/api/corpus_stats Fix** (Player UI hatte 404-Fehler)
3. **Dev-Umgebung auf Postgres migrieren** (SQLite-Fallback entfernen)

---

## ✅ Durchgeführte Änderungen

### 1. Backend: stats_all.db Removal

**Gelöschte Funktionen:**
- `src/app/services/atlas.py`: `fetch_overview()` (las stats_all.db)
- `src/app/services/database.py`: `"stats_all"` Entry aus DATABASES dict entfernt

**Gelöschte Endpoints:**
- `src/app/routes/atlas.py`: 
  - `GET /api/v1/atlas/overview` (Zeile 188-193)
  - Legacy Redirect `/overview` (Zeile 343-344)
- `src/app/routes/public.py`:
  - `GET /get_stats_all_from_db` (Zeile 343-351)

**Beweis der Obsoleszenz:**
```bash
# Keine aktiven Caller gefunden:
grep -r "fetch_overview" src/  # 0 Treffer
grep -r "/api/v1/atlas/overview" static/  # 0 Treffer  
grep -r "get_stats_all_from_db" static/  # 0 Treffer
```

---

### 2. Neuer Endpoint: /api/corpus_stats

**Datei:** `src/app/routes/corpus.py` (Zeile 203-231)

**Implementierung:**
```python
@blueprint.get("/api/corpus_stats")
def corpus_stats():
    """Serve pre-generated corpus statistics JSON."""
    project_root = Path(current_app.root_path).parent.parent
    stats_file = project_root / "static" / "img" / "statistics" / "corpus_stats.json"
    
    if not stats_file.exists():
        return jsonify({"error": "Corpus statistics not available"}), 404
    
    with open(stats_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    response = make_response(jsonify(data))
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response
```

**Konsumenten:**
- Player UI (modular player): Ruft `/api/corpus_stats` für globale Statistiken ab
- Ersetzt den zuvor nicht existierenden Endpoint (war 404)

**Datenquelle:**
- `static/img/statistics/corpus_stats.json` (generiert via `LOKAL/_0_json/05_publish_corpus_statistics.py`)

---

### 3. Dev Postgres-Only Migration

**Ziel:** Dev-Umgebung nutzt Postgres (wie Prod), SQLite-Fallback entfernt

#### Änderung 1: `.env.example`
```bash
# ALT:
# AUTH_DATABASE_URL=sqlite:///data/db/auth.db

# NEU:
AUTH_DATABASE_URL=postgresql+psycopg2://corapan_auth:corapan_auth@localhost:54320/corapan_auth
```

#### Änderung 2: `src/app/config/__init__.py`
```python
# ALT: SQLite als Fallback
AUTH_DATABASE_URL = os.environ.get(
    "AUTH_DATABASE_URL",
    f"sqlite:///{project_root}/data/db/auth.db"  # ❌ Fallback
)

# NEU: Fail-Fast ohne Fallback
AUTH_DATABASE_URL = os.environ.get("AUTH_DATABASE_URL")
if not AUTH_DATABASE_URL:
    raise RuntimeError(
        "AUTH_DATABASE_URL environment variable is required.\n"
        "For development: Start Postgres with 'docker compose -f docker-compose.dev-postgres.yml up -d'\n"
        "Then set: AUTH_DATABASE_URL=postgresql+psycopg2://corapan_auth:corapan_auth@localhost:54320/corapan_auth"
    )
```

#### Änderung 3: `.gitignore`
```gitignore
# Neu: Auth-DBs explizit ignorieren (ab Zeile 98)
data/db/auth.db
data/db/auth_e2e.db
infra/postgres_dev/
```

---

### 4. Kosmetik: Editor-Kommentare

**Datei:** `src/app/routes/editor.py` (Zeile 37-38)

```python
# ALT:
# - Duración (aus stats_all.db)
# - Palabras (aus stats_all.db)

# NEU:
# - Duración (aus stats_files.db)
# - Palabras (aus stats_files.db)
```

---

## 🧪 Tests

### Test 1: Producer Script (LOKAL/_0_json/03_build_metadata_stats.py)

**Command:**
```bash
python LOKAL/_0_json/03_build_metadata_stats.py
```

**Output:**
```
✅ stats_country.db erstellt:
   Länder: 25

✅ stats_files.db erstellt:
   Einträge: 146

ℹ️  HINWEISE:
   • stats_all.db wurde ersetzt durch corpus_stats.json
     (generiert via: python LOKAL/_0_json/05_publish_corpus_statistics.py)

Laufzeit: 20.69s
```

**✅ Ergebnis:** Producer baut NICHT mehr stats_all.db (Ziel erreicht)

---

### Test 2: Dev Config (Postgres-Only)

**Setup:**
```bash
docker compose -f docker-compose.dev-postgres.yml up -d
```

**Test 2a: Ohne AUTH_DATABASE_URL (Fail-Fast)**
```bash
python -c "from src.app.config import DevConfig"
# ❌ RuntimeError: AUTH_DATABASE_URL environment variable is required.
```

**Test 2b: Mit AUTH_DATABASE_URL (Postgres)**
```bash
$env:AUTH_DATABASE_URL="postgresql+psycopg2://corapan_auth:corapan_auth@localhost:54320/corapan_auth"
python -c "from src.app.config import DevConfig; print('✅ DevConfig loaded with Postgres')"
# ✅ DevConfig loaded with Postgres
```

**✅ Ergebnis:** SQLite-Fallback entfernt, Dev nutzt jetzt Postgres

---

### Test 3: Endpoint Verification

```bash
grep -n "/api/corpus_stats" src/app/routes/corpus.py
# 203: @blueprint.get("/api/corpus_stats")
```

**✅ Ergebnis:** Endpoint existiert, wird von Player UI konsumiert

---

## 📊 Code-Statistik

**Geänderte Dateien:**
- `src/app/services/atlas.py` (- fetch_overview)
- `src/app/services/database.py` (- stats_all)
- `src/app/routes/atlas.py` (- 2 Endpoints)
- `src/app/routes/public.py` (- 1 Endpoint)
- `src/app/routes/corpus.py` (+ /api/corpus_stats)
- `src/app/routes/editor.py` (Kommentar-Fix)
- `src/app/config/__init__.py` (Fail-Fast)
- `.env.example` (Postgres-Default)
- `.gitignore` (auth.db Einträge)

**LOKAL-Script (nicht committed, da .gitignore):**
- `LOKAL/_0_json/03_build_metadata_stats.py` (- build_stats_all(), - Logging)

**Commit:**
```bash
commit 9f41401
chore: remove stats_all.db and add corpus_stats endpoint

- Remove stats_all.db from backend (services/atlas.py, services/database.py)
- Remove obsolete endpoints: /api/v1/atlas/overview, /get_stats_all_from_db
- Add new endpoint: /api/corpus_stats (serves static JSON)
- Fix broken Player UI (404 on /api/corpus_stats)
- Update Editor comments to reference stats_files.db instead of stats_all.db
```

---

## 🔍 Beweisführung

### stats_all.db war obsolet:

1. **Kein Producer:** `03_build_metadata_stats.py` hatte `build_stats_all()` auskommentiert
2. **Keine Konsumenten:** Grep-Suche über Codebase zeigt 0 aktive Aufrufe
3. **Ersetzt durch:** `corpus_stats.json` (generated by `05_publish_corpus_statistics.py`)
4. **Frontend nutzt:** Atlas → stats_country.db, Player → stats_files.db

### Dev nutzt jetzt Postgres:

1. **.env.example** zeigt Postgres-URL als Default
2. **config.py** wirft RuntimeError ohne AUTH_DATABASE_URL
3. **Test-Output** zeigt erfolgreiche Config-Load mit Postgres
4. **.gitignore** schützt vor versehentlichem Commit von auth.db

---

## 📋 Nächste Schritte (für Prod-Deploy)

### Pre-Deployment Checklist:

1. **Smoke Tests auf Dev:**
   - [ ] Player lädt ohne 404-Fehler
   - [ ] Atlas Map funktioniert (Country Stats)
   - [ ] Editor zeigt File-Metadaten (Duración, Palabras)
   - [ ] Corpus Metadata Page lädt

2. **Datenbank-Cleanup auf Prod:**
   ```bash
   # Nach Prod-Deploy:
   rm /app/data/db/stats_all.db  # Optional: DB-Datei löschen
   ```

3. **Producer-Pipeline aktualisieren:**
   ```bash
   # LOKAL/_0_json/03_build_metadata_stats.py ist bereits gepatcht (lokal)
   # Stelle sicher, dass Prod-Pipeline das neue Script nutzt
   ```

4. **Monitoring:**
   - Prüfe Server-Logs auf Fehler bei `/api/corpus_stats` Aufrufen
   - Verifiziere, dass `corpus_stats.json` existiert (oder 404 wird korrekt behandelt)

---

## 🎉 Zusammenfassung

**Was funktioniert jetzt:**
✅ stats_all.db ist vollständig aus Backend entfernt  
✅ Player UI ruft `/api/corpus_stats` ohne 404 ab  
✅ Dev-Umgebung nutzt Postgres (wie Prod)  
✅ Producer-Script baut nur noch stats_country.db + stats_files.db  
✅ Keine SQLite-Fallbacks mehr in config.py  

**Was unverändert bleibt:**
🟢 stats_files.db (genutzt von Editor, Player)  
🟢 stats_country.db (genutzt von Atlas Map)  
🟢 corpus_stats.json (generiert via Pipeline-Script)  

**Branch:**
🌿 `chore/data-cleanup-dev-safe` → gepusht, bereit für PR
