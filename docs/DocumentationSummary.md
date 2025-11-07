# CO.RA.PAN - Documentation Summary

**Letzte Aktualisierung:** 2025-11-07  
**Version:** 1.0 (Post-Migration)  
**Status:** Production-Ready

---

## 📚 ÜBERSICHT

Diese Dokumentation fasst alle wichtigen Informationen zur CO.RA.PAN Web-Anwendung zusammen. Sie dient als zentrale Referenz für Entwickler, Administratoren und Maintainer.

---

## 🏗️ ARCHITEKTUR

### Backend (Flask 3.x)
- **Application Factory:** `src/app/__init__.py`
- **Blueprints:** Domain-basiert (public, auth, corpus, media, admin, atlas)
- **Authentifizierung:** JWT-based mit Cookie-Storage (HttpOnly, Secure)
- **Rollen:** admin, editor, user (hierarchisch)
- **Database:** SQLite mit optimierten Indizes
- **Media Services:** Audio-Streaming mit Snippet-Generierung

### Frontend
- **Templates:** Jinja2 (base.html + partials)
- **CSS:** Tailwind + Custom MD3 Design System
- **JavaScript:** ES Modules, gebündelt mit Vite
- **Features:** Server-Side DataTables, ECharts Stats, Leaflet Atlas

### Deployment
- **Container:** Docker (multi-stage build)
- **Orchestration:** docker-compose.yml
- **Mounts:** media/ und data/ als externe Volumes
- **Reverse Proxy:** nginx (Port 80/443 → 6000)

**Details:** Siehe `docs/architecture.md`

---

## 🔐 AUTHENTIFIZIERUNG

### JWT Cookie-Based Auth
- **Access Token:** 1 Stunde Gültigkeit
- **Refresh Token:** 7 Tage Gültigkeit
- **Cookie-Properties:** HttpOnly, Secure (Prod), SameSite=Lax

### Auth-Ready-Page (Race Condition Fix)
Nach Login erfolgt Redirect zu `/auth/ready` (nicht direkt zum Ziel):
1. `/auth/ready` pollt `/auth/session` bis Auth bestätigt
2. Retry-Logic: 10 Versuche à 150ms
3. Bei Erfolg: Redirect zum Zielseite
4. Bei Fehler: Redirect zu Login mit Error-Message

**Vorteil:** Keine Race-Condition zwischen Cookie-Setting und Page-Load

### Decorators
- `@jwt_required()` - Mandatory Auth (Redirect bei fehlendem Token)
- `@jwt_required(optional=True)` - Optional Auth (Route läuft immer, `g.user` gesetzt falls Auth)
- `@require_role(Role.ADMIN)` - Role-Based Access Control

**Details:** Siehe `docs/auth-flow.md`

---

## 🗄️ DATENBANK

### Transcription Database (`data/db/transcription.db`)
- **Tokens-Tabelle:** 1.35M Rows
- **Indizes:** 7 Performance-Indizes (text, lemma, country_code, etc.)
- **Query-Performance:** < 0.1s für typische Suchen
- **ANALYZE:** Query-Optimizer-Statistiken regelmäßig aktualisieren

### Annotation Database (`data/db/annotation_data.db`)
- **Status:** Erstellt aber nicht aktiv genutzt
- **Zweck:** Zukünftige erweiterte Suchen (POS, Morphologie, Syntax)
- **Spalten:** lemma, pos, dep, head_text, morph, foreign_word

### Wartung
```powershell
# Database neu erstellen (bei neuen Transkriptionen)
cd LOKAL\database
python database_creation_v2.py

# Health-Check
sqlite3 data\db\transcription.db "PRAGMA integrity_check;"
sqlite3 data\db\transcription.db "ANALYZE;"
```

**Details:** Siehe `docs/database_maintenance.md`

---

## 🎨 DESIGN-SYSTEM

### Farbpalette (Material Design 3)
- **Background:** `#c7d5d8` (Hellblau-Grau)
- **Surface:** `#eaf3f5` (Cards, Interactive Shells)
- **Accent:** `#2f5f73` (Borders, Primary Buttons)
- **Text:** `#244652` (Primary), `#3a6070` (Muted)

### Typography
- **Display:** Arial Narrow, Helvetica Neue Condensed
- **Body:** Arial, 16px base size
- **Monospace:** JetBrains Mono / Fira Mono

### Komponenten
- `.card` - Standard-Kartencontainer
- `.badge` - Status/Tag-Badges
- `.btn`, `.btn-primary` - Button-Styles
- `.md3-chip`, `.md3-chip--active` - Filter-Chips

### Responsive Breakpoints
- **Mobile:** < 600px (Grid-Layout für Speaker-Namen)
- **Tablet:** 600px - 900px
- **Desktop:** > 900px

**Details:** Siehe `docs/design-system.md`

---

## 📁 MEDIA-VERWALTUNG

### Ordnerstruktur (mit Länder-Unterordnern)
```
media/
├── mp3-full/       # Vollständige Aufnahmen (~30 MB, 20-30 Min)
│   ├── ARG/
│   ├── VEN/
│   └── ...
├── mp3-split/      # 4-Min-Chunks mit 30s Overlap (~4 MB)
│   ├── ARG/
│   └── ...
├── transcripts/    # JSON-Transkriptionen
│   ├── ARG/
│   └── ...
└── mp3-temp/       # Temporäre Snippets (Auto-Cleanup nach 30 Min)
```

### Split-First-Strategie
1. **Zuerst:** Split-Datei suchen (Performance: ~6x schneller)
2. **Fallback:** Full-Datei verwenden (funktioniert immer)

### Intelligente Pfad-Erkennung
- Extrahiert Ländercode aus Dateinamen (`2022-01-18_VEN_RCR.mp3` → `VEN`)
- Sucht automatisch in entsprechendem Unterordner
- Abwärtskompatibel mit flacher Struktur

**Details:** Siehe `docs/media-folder-structure.md`

---

## 📱 MOBILE OPTIMIERUNG

### Speaker-Layout (< 600px)
- **Grid-Layout:** Speaker-Name links (auto-width), Text rechts (1fr)
- **Speaker-Name:** Klein (0.7rem), max 80px breit, Ellipsis bei Overflow
- **Transkript:** Normal groß (1rem), Touch-Targets mind. 44px

### Simplified Player
- **Höhe:** 60px (kompakt)
- **Controls:** Play/Pause, Progress-Bar, Time-Display
- **Position:** Fixed bottom

**Details:** Siehe `docs/mobile-speaker-layout.md`

---

## 📊 STATISTIKEN

### Features
1. **Country-Filter:** Dropdown zur Filterung nach Land
2. **Display-Mode:** Toggle zwischen Absolut/Prozent
3. **5 Dimensionen:** Country, Speaker-Type, Sexo, Modo, Discourse
4. **Cache:** 120s TTL, separate Keys pro Filter-Kombination

### Interaktivität
- ECharts-basierte Bar-Charts
- Click-to-Drill-Down (geplant)
- Export als CSV/JSON (geplant)

**Details:** Siehe `docs/stats-interactive-features.md`

---

## 🚀 DEPLOYMENT

### Production Server Setup
1. **Git Clone:** Repository auf Server clonen
2. **Verzeichnisse erstellen:** media/, data/, config/, logs/, backups/
3. **Dateien kopieren:** Media, DB, Config (scp)
4. **Update-Script:** `chmod +x update.sh`
5. **Erstes Deployment:** `./update.sh --no-backup`
6. **nginx konfigurieren:** Reverse Proxy auf Port 6000

### Auto-Update-Script
```bash
./update.sh              # Normales Update (mit Backup)
./update.sh --no-backup  # Schneller (ohne Backup)
./update.sh --force      # Force rebuild (Cache ignorieren)
```

**Script-Funktionen:**
- ✅ Backup von Counters
- ✅ Git Pull
- ✅ Docker Image rebuild
- ✅ Container restart
- ✅ Health Check

### Backup-Strategie
```bash
./backup.sh              # Nur Counters (schnell)
./backup.sh --full       # Alles inkl. Media (langsam)
./backup.sh --db-only    # DB + Counters
```

**Retention:** 30 Tage, danach automatische Löschung

**Details:** Siehe `docs/DEPLOYMENT.md` (Root-Verzeichnis)

---

## 🛠️ TROUBLESHOOTING

### Performance-Probleme

**Problem:** Suche langsam (> 1s)
- **Diagnose:** Indizes vorhanden? `PRAGMA index_list('tokens')`
- **Lösung:** `database_creation_v2.py` ausführen

**Problem:** "de" oder "la" lädt endlos
- **Ursache:** Client-Side DataTables (80k Rows)
- **Lösung:** Server-Side Script prüfen (`corpus_datatables_serverside.js`)

### Audio-Probleme

**Problem:** Audio spielt nicht ab
- **Diagnose 1:** Event-Binding prüfen (`$('.audio-button').length`)
- **Diagnose 2:** Media-Endpoint testen (curl)
- **Diagnose 3:** Auth-Status prüfen (`allowTempMedia`)

**Problem:** "Audio konnte nicht geladen werden"
- **Ursache:** Datei nicht gefunden oder falscher Dateiname
- **Lösung:** Dateiexistenz prüfen, DB-Query auf filename

### Player-Probleme

**Problem:** Klick auf Archivo-Icon öffnet nichts
- **Diagnose:** Link-Struktur in DevTools prüfen
- **Lösung:** Player-Link-Generierung in Template prüfen

**Details:** Siehe `docs/troubleshooting.md`

---

## 🔧 ENTWICKLUNG

### Lokale Entwicklung
```powershell
# Virtual Environment
python -m venv .venv
.\.venv\Scripts\activate

# Dependencies
pip install -r requirements.txt
pip install -e .
npm install

# Frontend Build (optional)
npm run build

# App starten
$env:FLASK_ENV="development"
python -m src.app.main
```

**URL:** http://localhost:8000

### Test-Accounts
- **admin:** admin / 0000
- **editor:** editor_test / 1111
- **user:** user_test / 2222

### Passwörter neu generieren
```powershell
python LOKAL\security\hash_passwords_v2.py
```

**Details:** Siehe `startme.md` (Root-Verzeichnis)

---

## 📋 CI/CD

### GitLab Pipeline
1. **Test:** Python Tests, Linting, Frontend Build
2. **Build:** Docker Image → Registry
3. **Deploy:** Staging (manuell)

### Branch Protection
- **main:** Protected, requires approval + passing pipeline
- **Feature Branches:** PRs mit Review

### Labels
- `status::*` - todo, in-progress, review, blocked
- `type::*` - bug, feature, enhancement, documentation
- `priority::*` - high, medium, low
- `component::*` - backend, frontend, database, infrastructure

**Details:** Siehe `docs/gitlab-setup.md`

---

## 🔒 SICHERHEIT

### Secrets Management
- ❌ NIEMALS in Git: `passwords.env`, `config/keys/`, `*.key`, `*.pem`
- ✅ In Git: `passwords.env.template`, `.gitignore`
- ✅ Server: Environment-Variables oder gemountete Files

### .gitignore Coverage
- Secrets & Credentials
- Media-Dateien (zu groß)
- Build-Artefakte (node_modules, .venv, __pycache__)
- Logs & Temporäre Dateien
- Lokale Entwicklung (LOKAL/, .vscode/)

### Security Checks (vor Git Push)
```powershell
# Keine Secrets im Status
git status | Select-String "passwords.env"

# Gitignore funktioniert
git check-ignore passwords.env
git check-ignore config/keys/
```

**Details:** Siehe `GIT_SECURITY_CHECKLIST.md` (Root-Verzeichnis)

---

## 📖 WEITERE DOKUMENTATION

### Im Root-Verzeichnis
- **README.md** - Projekt-Übersicht und Feature-Liste
- **startme.md** - Quick-Start-Commands für lokale Entwicklung (LOKAL, nicht in Git)

### In docs/
- **architecture.md** - Technische Architektur
- **auth-flow.md** - Authentifizierungs-Flow
- **database_maintenance.md** - DB-Wartung und Optimierung
- **deployment.md** - Detaillierter Deployment-Guide (versetzt aus Root)
- **design-system.md** - Design-Tokens und Komponenten
- **git-security-checklist.md** - Security-Best-Practices für Git (versetzt aus Root)
- **gitlab-setup.md** - CI/CD und Repository-Konfiguration
- **media-folder-structure.md** - Media-Verwaltung
- **mobile-speaker-layout.md** - Mobile-Optimierung
- **roadmap.md** - Entwicklungs-Roadmap
- **stats-interactive-features.md** - Stats-Feature Dokumentation
- **token-input-multi-paste.md** - Token-Input Feature Dokumentation
- **troubleshooting.md** - Fehlerdiagnose und Lösungen

### In LOKAL/
- **LOKAL/records/README.md** - Regeln für Process-Records
- **LOKAL/records/PROCESS_LOG.md** - Prozess-Historie
- **LOKAL/00 - Md3-design/** - Design-System-Dokumentation
- **LOKAL/01 - Add New Transcriptions/** - Maintenance-Scripts
- **LOKAL/02 - Add New Users (Security)/** - User-Management
- **LOKAL/03 - Analysis Scripts (tense)/** - Analyse-Tools

---

## 🎯 ROADMAP

### Phase 1: Authentication Hardening
- RSA Key Management
- Credential Rotation
- Integration Tests

### Phase 2: Corpus Enrichment
- Multi-Token Queries
- Saved Searches
- Export Options

### Phase 3: Atlas Experience
- Map Markers per Location
- Drill-Down Cards
- CSV/JSON Exports

### Phase 4: Media Services
- mp3-temp Toggle Persistence
- Transcript/Audio Checksum Validation
- Admin UI Controls

### Phase 5: Observability
- Daily Aggregates
- Sparkline Charts
- Structured Logs

### Phase 6: CI/CD & Quality
- Ruff, mypy, pytest, ESLint
- Pre-commit Hooks
- Full Test Matrix

**Details:** Siehe `docs/roadmap.md`

---

## 📞 KONTAKT & SUPPORT

**Maintainer:** Felix Tacke (felix.tacke@uni-marburg.de)  
**Repository:** git@gitlab.uni-marburg.de:tackef/corapan-new.git  
**Issues:** GitLab Issue-Tracker

---

## 📄 CHANGELOG

### Version 1.0 (2025-11-07)
- ✅ Migration abgeschlossen
- ✅ MD3 Design-System implementiert
- ✅ JWT-Authentication mit /auth/ready
- ✅ Server-Side DataTables
- ✅ Stats-Feature mit Country-Filter
- ✅ Split-Audio-Optimierung
- ✅ Mobile-Optimierung (Speaker-Layout)
- ✅ Auto-Update-Script für Deployment
- ✅ Umfassende Dokumentation

---

*Diese Dokumentation wird regelmäßig aktualisiert. Bei Fragen oder Problemen bitte Issue im GitLab erstellen.*
