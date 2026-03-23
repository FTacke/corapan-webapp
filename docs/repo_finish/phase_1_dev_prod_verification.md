# Phase 1: Dev ≠ Prod Verifikation

**Status: NEIN. Dev ≠ Prod. Go-No-Jo für Phase 2: NO.**

---

## T1: Executive Summary

**Kritisch:** Die aktuelle lokale Dev-Umgebung entspricht **nicht** dem produktiven Zielzustand.

Es existieren:
- ✅ Teilweise korrekte Mounts (BlackLab-Index, Postgres-Daten)
- ❌ Konfigurationsduplizierung (config/blacklab UND webapp/config)
- ❌ Pfad-Dualität (Root-Level + webapp-Level docker-composes)
- ❌ **Kritisch: ENV-Variablen nicht gesetzt** (App kann nicht starten mit aktuellem Code)
- ❌ Docker-Compose Inkonsistenzen
- ⚠️ Wartbarkeits-Probleme durch parallele Strukturen

**Konsequenz:**
- Die lokale Dev-Umgebung ist nicht sauber
- Ein `docker compose up` würde fehlschlagen oder mit falschen Pfaden arbeiten
- Phase 2 (Repo-Restructuring) kann nicht sauber durchgeführt werden, solange Dev nicht = Prod ist

---

## T2: Strukturvergleich (Soll vs Ist)

### T2.1: Soll-Zustand (Prod)

```
/srv/webapps/corapan/
├── app/                    (versioniert: Git-Repo)
├── data/
│   ├── blacklab/
│   │   ├── index/
│   │   └── export/
│   ├── config/
│   ├── public/
│   └── stats_temp/
├── media/
├── logs/
└── passwords.env           (operativ, nicht versioniert)
```

**Prod Docker-Mounts (aus docker-compose.prod.yml):**
```yaml
web:
  volumes:
    - /srv/webapps/corapan/data:/app/data
    - /srv/webapps/corapan/media:/app/media
    - /srv/webapps/corapan/logs:/app/logs
    - /srv/webapps/corapan/data/config:/app/config
```

**DB Container:**
```yaml
db:
  volumes:
    - corapan_postgres_prod:/var/lib/postgresql/data
```

### T2.2: Ist-Zustand (Dev, lokal)

```
C:\dev\corapan\
├── webapp/                    ❌ MISMATCH: Heißt Prod "app", Dev heißt "webapp"
├── data/                      ✅ Vorhanden
│   ├── blacklab/
│   │   ├── index/             ✅ Korrekt
│   │   └── export/            ⚠️ Zusätzlich (Prod hat separaten Export-Mount)
│   ├── db/
│   │   ├── restricted/
│   │   └── postgres_dev/      ✅ Mounted
│   ├── public/                ✅ Vorhanden
│   └── stats_temp/            ✅ Vorhanden
├── media/                     ✅ Vorhanden
├── config/                    ❌ ABWEICHUNG: Liegt oben-level
│   └── blacklab/              ⚠️ Mounted von Docker
├── docs/                      ✅ Neu: Moved to root (OK)
├── maintenance_pipelines/     ✅ Vorhanden
└── [Weitere Verzeichnisse]
```

### T2.3: Kritische Struktur-Abweichungen

| Bereich | Soll (Prod) | Ist (Dev) | Status | Risiko |
|---------|------------|----------|--------|--------|
| App-Verzeichnis | `app/` | `webapp/` | Mismatch | **HOCH** |
| Config-Ort | `/data/config` | `C:\corapan\config` | Teilweise | **MITTEL** |
| BlackLab-Config | `/data/config/blacklab` | `webapp/config/blacklab` | Duplikat | **MITTEL** |
| Docker-Compose | Prod Root | Root + webapp | Duplikat | **MITTEL** |
| DB-Volume | `corapan_postgres_prod` | lokal gemounted | OK | – |

---

## T3: BlackLab Setup

### T3.1: Index-Pfade

**Prod Erwartet:**
```
/srv/webapps/corapan/data/blacklab/index/
→ mounted als: /data/index/corapan in Container
→ Corpus: "corapan"
```

**Dev Aktuell:**
```
C:\dev\corapan\data\blacklab\index/
→ mounted als: /data/index/corapan in Container
→ Corpus: "corapan"
✅ KORREKT
```

### T3.2: Export-Pfade

**Prod:**
```
/srv/webapps/corapan/data/blacklab/export/
→ Separate Liste in docker-compose
→ Nicht im Dev-docker-compose vorhanden
```

**Dev:**
```
C:\dev\corapan\data\blacklab\export/
✅ Physisch vorhanden
⚠️ Aber: NICHT in docker-compose.dev-postgres.yml gemounted
→ Könnte zu Datenverlust führen
```

**Risiko:** Export-Daten werden nicht automatisch persistiert.

### T3.3: BlackLab Config

**Prod Erwartet:**
```
/srv/webapps/corapan/data/config/blacklab/
→ Mounted nach: /etc/blacklab
```

**Dev Aktuell:**
```
C:\dev\corapan\webapp\config\blacklab/
→ Mounted nach: /etc/blacklab
✅ Funktional OK
❌ Aber FALSCH GELEGEN (sollte unter data/config sein)
```

**Problem:** Bei Umbenennung `webapp` → `app` muß dieser Pfad auch angepasst werden.

### T3.4: BLS_CORPUS Variable

**Prod:**
```
BLS_CORPUS: corapan
(aus docker-compose.prod.yml)
```

**Dev:**
```
Nicht in docker-compose.dev-postgres.yml vorhanden
→ Code wird Fallback auf ENV-Variable prüfen
→ Falls nicht gesetzt: FEHLER (Guard im Code)
```

**Status:** ⚠️ MISMATCH

---

## T4: Docker/Mount Analyse

### T4.1: Aktive Dev-Container

```
corapan_auth_db (Postgres:15)
  Mounts:
    C:\dev\corapan\data\db\restricted\postgres_dev:/var/lib/postgresql/data      ✅
    C:\dev\corapan\webapp:/app                                                    ✅

blacklab-server-v3 (BlackLab)
  Mounts:
    C:\dev\corapan\data\blacklab\index:/data/index/corapan                        ✅
    C:\dev\corapan\webapp\config\blacklab:/etc/blacklab                           ⚠️
```

### T4.2: Docker-Compose Dateien — Duplikate Erkannt

**Datei 1: `C:\dev\corapan\docker-compose.dev-postgres.yml`**
```yaml
version: nicht angegeben (implizit default)
services:
  corapan_auth_db:
    volumes:
      - ./data/db/restricted/postgres_dev:/var/lib/postgresql/data      ✅ Relativ zu Root
      - ./webapp:/app:ro                                                 ✅ Relativ zu Root
  blacklab-server-v3:
    volumes:
      - ./data/blacklab/index:/data/index/corapan:ro                     ✅
      - ./config/blacklab:/etc/blacklab:ro                              ❌ Sollte data/config
```

**Datei 2: `C:\dev\corapan\webapp\docker-compose.dev-postgres.yml`**
```yaml
services:
  corapan_auth_db:
    volumes:
      - ../data/db/restricted/postgres_dev:/var/lib/postgresql/data     ✅ Relativ zu webapp
      - .:/app:ro                                                        ⚠️ Mounts webapp selbst
  blacklab-server-v3:
    volumes:
      - ../data/blacklab/index:/data/index/corapan:ro                    ✅
      - ../config/blacklab:/etc/blacklab:ro                             ❌
```

**Problem:**
1. Zwei unterschiedliche Dateien mit unterschiedlichen Relativen Pfaden
2. Unklar, welche derzeit verwendet wird
3. `# Start with: docker compose -f docker-compose.dev-postgres.yml up -d` → Welche Datei wird geladen?

**Aktuelle Realität:** Root-Level-Compose wird verwendet (basierend auf laufenden Container-Inspects), aber es existiert Verwirrung.

### T4.3: Prod-Compose vs Dev-Compose Unterschiede

| Aspect | Prod | Dev (Root) | Dev (webapp) | Status |
|--------|------|-----------|--------------|--------|
| Container-Namen | `corapan-db-prod`, `corapan-web-prod` | `corapan_auth_db` (underscore) | underscore | Mismatch |
| Postgres User | `corapan_app` | `corapan_auth` | `corapan_auth` | Unterschiedliche DB |
| Postgres DB | `corapan_auth` | `corapan_auth` | `corapan_auth` | ✅ Same |
| BlackLab Corpus | `BLS_CORPUS: corapan` | Nicht gesetzt | Nicht gesetzt | ⚠️ **CRITICAL** |
| Environment VARS | Prod-optimiert (FLASK_ENV=production, etc.) | Dev-minimal | Dev-minimal | ⚠️ |

---

## T5: Auth / Datenbank Setup

### T5.1: Postgres Container

**Prod:**
```yaml
POSTGRES_USER: corapan_app
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  (from env/passwords.env)
POSTGRES_DB: corapan_auth
Volume: docker-named `corapan_postgres_prod`
Network: `corapan-network-prod`
```

**Dev:**
```yaml
POSTGRES_USER: corapan_auth                               ❌ UNTERSCHIED: corapan_auth vs corapan_app
POSTGRES_PASSWORD: corapan_auth                           ❌ Hardcodiert, nicht aus ENV
POSTGRES_DB: corapan_auth                                 ✅ Same
Volume: Local mountpoint `./data/db/restricted/postgres_dev`  ✅
Network: Default (bridge)                                 ✅
```

**Problem:**
- Dev und Prod nutzen unterschiedliche Postgres-User
- Migrations/Scripts müssen ggf. beides unterstützen (oder Dev muß gepflegt werden)
- Hardcodiertes Password ist ein Security-Anti-Pattern (aber für Dev OK)

### T5.2: Authentication Database URL

**Prod erwartete Umgebungsvariablen:**
```
AUTH_DATABASE_URL=postgresql+psycopg2://corapan_app:${POSTGRES_PASSWORD}@db:5432/corapan_auth
DATABASE_URL=postgresql+psycopg2://corapan_app:${POSTGRES_PASSWORD}@db:5432/corapan_auth
```

**Dev Aktuell:**
```
⚠️ NICHT GESETZT
→ Code prüft auf CORAPAN_RUNTIME_ROOT und CORAPAN_MEDIA_ROOT
→ Falls nicht gesetzt: Code schmeißt RuntimeError
```

**Kritisch:** Der Code in `runtime_paths.py` erfordert zwingend:
```python
runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")
if not runtime_root or not runtime_root.strip():
    raise RuntimeError(
        "CORAPAN_RUNTIME_ROOT environment variable is required..."
    )
```

**Status:** ❌ **App wird aktuell nicht starten können**

---

## T6: Media / Audio Setup

### T6.1: Media-Verzeichnisstruktur

**Prod Erwartet:**
```
/srv/webapps/corapan/media/
→ Mounted als: /app/media im Container
→ ENV: CORAPAN_MEDIA_ROOT=/app/media
```

**Dev Aktuell:**
```
C:\dev\corapan\media/
  ├── mp3-full/
  ├── mp3-split/
  ├── mp3-temp/
  └── transcripts/
✅ Physisch vorhanden
❌ NICHT gemountet in Dev-Docker-Compose
```

**Problem:**
1. Media wird nicht vom Container aus erreicht
2. `CORAPAN_MEDIA_ROOT` nicht gesetzt → App scheitert
3. Keine Persistierung für temporäre Extraktion

### T6.2: Audio Playback Backend

**Code-References:**
```python
from services.media_store import ...  # Uses runtime_media_root
from services.corpus import ...        # Uses media paths
```

Code erwartet `CORAPAN_MEDIA_ROOT` ENV-Variable → wird nicht gesetzt → ❌

---

## T7: Harte Abweichungen + Maßnahmen

### A1: Webapp → App Umbenennung (Blockiert für Phase 2)

| Problem | Impact | Priority |
|---------|--------|----------|
| `webapp/` sollte `app/` sein | Docker-Pfade, Skripte, Doku müssen angepasst werden | HIGH |
| Aber nicht allein durchführen | Würde Docker-Pfade brechen | CRITICAL |

**Maßnahme:**
- Phase 2 ERST durchführen
- Dabei wird `webapp/` → `app/` erfolgen

### A2: Fehlende ENV-Variablen (CRITICAL)

| Variable | Status | Erforderlicher Wert |
|----------|--------|-------------------|
| CORAPAN_RUNTIME_ROOT | ❌ Nicht gesetzt | `C:\dev\corapan` (Dev) oder `/app` (Prod) |
| CORAPAN_MEDIA_ROOT | ❌ Nicht gesetzt | `C:\dev\corapan\media` (Dev) oder `/app/media` (Prod) |
| FLASK_ENV | ❌ Nicht gesetzt | `development` (Dev) oder `production` (Prod) |
| AUTH_DATABASE_URL | ❌ Nicht gesetzt | postgresql://... |
| POSTGRES_PASSWORD | ❌ Nicht gesetzt | [secure random] |
| FLASK_SECRET_KEY | ❌ Nicht gesetzt | [secure random] |

**Maßnahme:**
Vor Phase 2: `.env.development.local` erstellen und laden

### A3: Config-Duplikation

| Path | Status | Issue |
|------|--------|-------|
| `C:\dev\corapan\config\blacklab/` | ✅ Vorhanden | War als separates Repo-Top-Level gedacht |
| `C:\dev\corapan\webapp\config\blacklab/` | ✅ Vorhanden, gemountet | Docker nutzt diese |
| `C:\dev\corapan\webapp\config/` | ✅ Vorhanden | Alte Webapp-lokale Configs |

**Frage:** Welche Config ist aktiv?

**Maßnahme:**
Vor Phase 2: Konfigurationsquellen konsolidieren
- Option 1: `data/config/` als canonical (wie Prod)
- Option 2: `app/config/` als canonical (in App verlegen)

### A4: Docker-Compose Duplikation

**Aktuell existieren:**
1. `C:\dev\corapan\docker-compose.dev-postgres.yml`
2. `C:\dev\corapan\webapp\docker-compose.dev-postgres.yml`

**Problemzirkel:**
- Unklar, welche wird verwendet
- Keine zentralisierte Dev-Orchestrierung
- Phase 2 macht Umzug von `webapp/` schwieriger

**Maßnahme:**
Vor Phase 2: Eine definitive docker-compose.dev-postgres.yml unter `C:\dev\corapan/`

### A5: BlackLab Export nicht persistent

**Dev-Status:**
```
C:\dev\corapan\data\blacklab\export/ existiert lokal
Aber: Nicht in docker-compose.yml gemountet
```

**Risiko:**
- Wenn Docker-Volume neu erstellt wird: Export-Daten weg
- Prod hat separaten Export-Mount

**Maßnahme:**
Add to dev docker-compose:
```yaml
volumes:
  - ./data/blacklab/export:/data/export
```

### A6: BLS_CORPUS nicht gesetzt

**Prod:**
```
BLS_CORPUS: corapan
```

**Dev:**
```
Nicht in docker-compose vorhanden
```

**Maßnahme:**
Add BLS_CORPUS to dev docker-compose environment:
```yaml
environment:
  BLS_CORPUS: corapan
```

---

## T8: Gesamtbewertung

### Saubere Aspekte ✅

| Aspekt | Status |
|--------|--------|
| BlackLab-Index unter data/blacklab/index/ | ✅ Korrekt |
| Postgres im Docker-Volume | ✅ Korrekt |
| Verzeichnisse data/, media/ Top-Level | ✅ Korrekt |
| .github, docs auf Root-Level | ✅ Korrekt |
| maintenance_pipelines extern | ✅ Korrekt |

### Problematische Aspekte ❌

| Aspekt | Severity |
|--------|----------|
| webapp/ statt app/ | HIGH |
| config/ Duplikation + falscher Ort | HIGH |
| ENV-Variablen nicht gesetzt | CRITICAL |
| Docker-Compose Duplikation | MEDIUM |
| BlackLab Export nicht gemountet | MEDIUM |
| BLS_CORPUS nicht in Dev-Compose | MEDIUM |

---

## T9: Fazit – Go / No-Go für Phase 2

### Status: **NO-GO ⛔**

**Gründe:**

1. **Kritisch — ENV-Variablen:**
   - `CORAPAN_RUNTIME_ROOT` nicht gesetzt
   - `CORAPAN_MEDIA_ROOT` nicht gesetzt
   - Code wird werfen → App läuft nicht
   - Phase 2 macht dies nicht einfacher

2. **Blockiert — webapp/ vs app/ Mismatch:**
   - Kann nicht sauber repariert werden OHNE Phase 2
   - Phase 2 ist aber nicht abhängig von Phase 1 Success
   - Aber: Phase 1 sollte zuerst saubergemacht werden

3. **Wartbarkeit — Duplikationen:**
   - Zwei docker-compose.dev-postgres.yml
   - config/ an zwei Orten
   - Unklar, welche Config ist "active"
   - Dies wird bei Phase 2-Repo-Umstrukturierung kompliziert

### Empfohlene Sequenz

1. **ERST: Kleine Dev-Fixes (vor Phase 2)**
   - Erstelle `.env.development.local` mit erforderlichen Variablen
   - Setze ENV-Variablen lokal korrekt
   - Teste, ob App startet
   - Konsolidiere docker-compose zu einer Single Source of Truth
   - Konsolidiere config/ an EINEN Ort

2. **DANN: Phase 2 Repo Finalization**
   - Umbenenne webapp/ → app/
   - Passe alle Referenzen an
   - Integriere Root-Level Repo (Git)
   - Rename success

3. **OPTIONAL: Nach Phase 2**
   - Spiegelung auf Prod prüfen

### Was blockiert Phase 2 NICHT

- Das Verschieben von `docs/` nach Root: ✅ Fertig
- Das Definieren von Zielstruktur: ✅ Klar
- Der Code selbst: ✅ Guards sind in place

---

## T10: Konkrete Nächste Schritte (Prerequisite für Phase 2)

### Schritt 1: `.env.development.local` erstellen

**Datei:** `C:\dev\corapan\.env.development.local` (NICHT versioniert)

```bash
# Runtime Paths (Dev)
CORAPAN_RUNTIME_ROOT=C:\dev\corapan
CORAPAN_MEDIA_ROOT=C:\dev\corapan\media

# Flask
FLASK_ENV=development
FLASK_SECRET_KEY=dev-secret-key-change-in-prod-12345678901234567890

# Datenbank
AUTH_DATABASE_URL=postgresql+psycopg://corapan_auth:corapan_auth@localhost:54320/corapan_auth
POSTGRES_PASSWORD=corapan_auth

# JWT
JWT_SECRET_KEY=dev-jwt-key-change-in-prod-abc123def456

# BlackLab
BLS_BASE_URL=http://localhost:8081/blacklab-server
BLS_CORPUS=corapan

# Admin Init (nur für erste Bootstriap)
START_ADMIN_USERNAME=admin
START_ADMIN_PASSWORD=admin-password
```

### Schritt 2: Docker-Compose konsolidieren

**Halte nur:** `C:\dev\corapan\docker-compose.dev-postgres.yml`

**Die Datei sollte haben:**
```yaml
services:
  corapan_auth_db:
    volumes:
      - ./data/db/restricted/postgres_dev:/var/lib/postgresql/data

  blacklab-server-v3:
    volumes:
      - ./data/blacklab/index:/data/index/corapan:ro
      - ./data/config/blacklab:/etc/blacklab:ro    # Update: data/ nicht webapp/
      - ./data/blacklab/export:/data/export        # Add: Export persistent
    environment:
      BLS_CORPUS: corapan                           # Add: Corpus name
```

### Schritt 3: Config konsolidieren

**Quelle der Wahrheit:** `C:\dev\corapan\data\config/`

- Verschiebe `webapp/config/blacklab/*` nach `data/config/blacklab/`
- Lösche `config/` am Root-Level (war temporär)
- Update docker-compose zu `./data/config/blacklab`

### Schritt 4: Testen

```bash
Set-Location C:\dev\corapan
# Load env
$env:CORAPAN_RUNTIME_ROOT = 'C:\dev\corapan'
$env:CORAPAN_MEDIA_ROOT = 'C:\dev\corapan\media'
$env:FLASK_ENV = 'development'

# Test Docker
docker compose -f docker-compose.dev-postgres.yml up -d

# Test App (if you can start Flask locally)
cd webapp
python src/run.py
```

**Expected:**
- `corapan_auth_db` startet und ist healthy
- `blacklab-server-v3` startet und ist healthy
- App kann starten (oder mit sauberer Error meldung crashen, nicht wegen ENV Variablen)

---

## Referenzen

- Prod-Migrationsdoku: `docs/prod_migration/2026-03-22_phase_d4_execution.md`
- Repo-Finalisierungsplan: `docs/repo_finish/repo_finish.md`
- DevOps-Richtlinien: `.github/instructions/devops.instructions.md`

---

**Datum:** 2026-03-23  
**Status:** NO-GO für Phase 2 (bis Prerequisite-Fixes durchgeführt)
