# Documentation Changelog

Dokumentiert alle wesentlichen Änderungen an der CO.RA.PAN-Dokumentation.

---

## [2.2.0] - 2025-11-09: BlackLab Export + Documentation Cleanup

### Added

#### 🔨 BlackLab Export Infrastructure
- **`LOKAL/01 - Add New Transcriptions/03 update DB/blacklab_index_creation.py`** (900+ lines)
  - Export JSON v2 → BlackLab TSV/WPL
  - Idempotenz via Hash-Cache
  - Validierung: Pflichtfelder, leere Werte, NFC-Normalisierung
  - TSVWriter: Tabular format (empfohlen)
  - WPLWriter: Hierarchical structures (optional)
  - DocMetaWriter: JSONL metadata
  - CLI: `--root`, `--out`, `--docmeta`, `--format`, `--dry-run`, `--workers`

- **`LOKAL/01 - Add New Transcriptions/03 update DB/corapan-tsv.blf.yaml`** (280+ lines)
  - BlackLab format definition (TSV)
  - 17 Annotationen: word, norm, lemma, pos, tense, mood, person, number, aspect, tokid, start_ms, end_ms, sentence_id, utterance_id, speaker_code, past_type, future_type
  - 6 Metadaten: file_id, country_code, date, radio, city, audio_path
  - Sensitivity: word (sensitive), norm (insensitive)

- **`LOKAL/01 - Add New Transcriptions/03 update DB/corapan-wpl.blf.yaml`** (180+ lines)
  - BlackLab format definition (WPL with structures)
  - Inline tags: `<s>`, `<utt>`, `<doc>`
  - Strukturbasierte Suchen: `<s/> containing [lemma="hablar"]`

#### 📄 Documentation
- **`docs/how-to/blacklab-indexing.md`** (850+ lines)
  - Schritt-für-Schritt Guide: Export → Index → Validation
  - TSV vs. WPL Format
  - Inkrementelle Updates
  - Troubleshooting (6 häufige Probleme)
  - Quick-Tests: sensitiv/insensitiv, Morphologie, Timing, Metadaten
  - Performance-Tipps

- **`docs/reference/blacklab-configuration.md`** (600+ lines)
  - Vollständige `.blf.yaml` Referenz
  - Annotation-Spezifikationen (POS-Tags, Morph-Features)
  - Speaker-Code Schema
  - Metadaten-Felder
  - CQL-Query-Beispiele (15+ Patterns)
  - Autocomplete-Konfiguration
  - Forward-Indexes
  - Fehlerbehebung

### Changed

#### 🗂️ Documentation Reorganization
- **Moved to `archived/`** (historische Meta-Indices):
  - `CORPUS_SEARCH_DOCS_OVERVIEW.md` → `archived/corpus-search-docs-overview.md`
  - `JSON_ANNOTATION_V2_DOCUMENTATION_INDEX.md` → `archived/json-annotation-v2-documentation-index.md`

- **Moved to `migration/`** (Implementation Reports):
  - `JSON_ANNOTATION_V2_SUMMARY.md` → `migration/json-annotation-v2-implementation.md`
  - `EEUU-Standardisierung-Report.md` → `migration/eeuu-to-usa-standardization.md` (kebab-case)

- **Added Front-Matter** to all moved files (title, status, owner, updated, tags, links)

#### 📁 docs/ Root Cleanup
- **Before:** 7 files (inkl. 4 lose Dokumente)
- **After:** 3 files (nur index.md, CONTRIBUTING.md, CHANGELOG.md)

### Technical Details

#### BlackLab Export Features
- **Idempotenz:** Hash-basierte Change-Detection (`.hash_cache.jsonl`)
- **Validierung:** Pflichtfelder-Check bei Export (Abbruch wenn token_id/start_ms/end_ms fehlt)
- **NFC-Normalisierung:** Alle Strings werden normalisiert vor Export
- **Error-Logging:** `export_errors.jsonl` für fehlgeschlagene Dateien
- **Dry-Run:** Validierung ohne Dateischreibung (`--dry-run`)

#### Annotations Coverage
- **Word Forms:** word (sensitiv), norm (insensitiv), lemma
- **POS:** Universal Dependencies (17 Tags)
- **Morphologie:** tense, mood, person, number, aspect (spaCy-basiert)
- **Legacy:** past_type, future_type (Kompatibilität)
- **Identifiers:** tokid (Rücksprung zur App)
- **Timing:** start_ms, end_ms (Integer Millisekunden)
- **Structure:** sentence_id, utterance_id (Kontext-Rekonstruktion)
- **Speaker:** speaker_code (14 standardisierte Codes)

#### Index Performance
- Forward-Indexes für alle Annotationen
- RAM-Optimierung: `-Xmx8G` empfohlen
- Cache-Size konfigurierbar in `blacklab-server.yaml`

### Integration Points

#### Schritt B: BlackLab-Export
- ✅ Export-Script mit Validierung
- ✅ TSV/WPL Format-Konfiguration
- ✅ Idempotenz und Error-Handling
- ✅ Dokumentation (How-To + Reference)

#### Nächster Schritt: BlackLab-Integration
- [ ] BlackLab Server aufsetzen
- [ ] Index erstellen (`IndexTool create ...`)
- [ ] Frontend-Integration (`/busqueda-avanzada`)
- [ ] Autocomplete konfigurieren
- [ ] Rücksprung-Links implementieren (`tokid` → App-URL)

---

## [2.1.0] - 2025-11-08: JSON Annotation v2 & Tense Recognition

### Added

#### 📄 New Documentation Files
- **`reference/json-annotation-v2-specification.md`** (600+ lines)
  - Vollständige v2-Schema Spezifikation
  - Token-IDs, Satz-/Äußerungs-Hierarchie
  - Normalisierung (`norm`) Algorithmus
  - Vergangenheits- und Zukunftsformen-Erkennung
  - Idempotenz-Logik mit Metadaten
  - BlackLab-Export (flache Felder)
  - Validierungs- und Smoke-Tests

- **`how-to/json-annotation-workflow.md`** (400+ lines)
  - Praktische Schritt-für-Schritt Anleitung
  - Safe-Modus vs. Force-Modus
  - Validierungs-Checklist
  - Fehlerbehandlung und Troubleshooting
  - Performance-Tipps
  - Integration mit DB-Creation

#### 🔧 Script Updates
- **`annotation_json_in_media_v2.py`** - Neues v2-Annotations-Script
  - Stabile, hierarchische IDs (token_id, sentence_id, utterance_id)
  - Zeitstempel in Millisekunden (start_ms, end_ms)
  - Normalisierung für akzent-indifferente Suche
  - Idempotenz mit SHA1-Hash und Metadaten
  - Lemma-/morph-basierte Zeitformen-Erkennung (statt String-Listen)
  - Flexibles Gap-Handling für Klitika/Adverbien
  - Flache Felder für BlackLab (past_type, future_type)
  - Statistik-Sammlung und Validierung

### Changed

#### 🎯 Tense Recognition (Robustness)
- **Perfekt-Erkennung:**
  - ❌ **Entfernt:** String-basierte `head_text`-Listen (PRESENT_FORMS, etc.)
  - ✅ **Neu:** Lemma-basierte AUX-Suche (`lemma="haber"`)
  - ✅ **Gap-Handling:** Erlaubt bis zu 3 Zwischentokens (PRON, ADV, PART, etc.)
  - ✅ **Exklusionen:** Existential haber verhindert False Positives
  
- **Analytisches Futur:**
  - ❌ **Entfernt:** Festes 3-Token-Fenster
  - ✅ **Neu:** Flexibles Fenster mit Gap-Handling
  - ✅ **Lemma-Check:** `lemma="ir"` statt POS-only
  - ✅ **Exklusionen:** "ir a + NOUN" wird nicht markiert

#### 📊 Schema Extensions
- **Token-Felder erweitert:**
  - `token_id`: Eindeutige ID (Format: `{file}:{utt}:{sent}:{token}`)
  - `sentence_id`: Satz-Zuordnung
  - `utterance_id`: Äußerungs-Zuordnung
  - `start_ms`, `end_ms`: Millisekunden (Integer)
  - `norm`: Normalisierte Suchform
  - `past_type`: Flaches Perfekt-Label
  - `future_type`: Flaches Futur-Label

- **Segment-Felder erweitert:**
  - `utt_start_ms`: Äußerungs-Start (ms)
  - `utt_end_ms`: Äußerungs-Ende (ms)

- **Metadaten-Objekt:**
  - `ann_meta.version`: Schema-Version (`corapan-ann/v2`)
  - `ann_meta.text_hash`: SHA1 über alle Token-Texte
  - `ann_meta.required`: Liste der Pflichtfelder
  - `ann_meta.timestamp`: ISO-8601 Zeitstempel

### Improved

#### 🔄 Idempotenz
- **Intelligenter Skip-Check:**
  - Prüft Schema-Version
  - Vergleicht Content-Hash
  - Validiert alle Required Fields
  - Nur neu annotieren bei Änderungen

#### 📈 Validation
- **Automatische Statistiken:**
  - Zeitformen-Häufigkeit nach Lauf
  - Sample-basierte Auswertung
  - Prozentuale Verteilung

- **Smoke-Tests dokumentiert:**
  - "ha cantado" → PerfectoCompuesto
  - "había cantado" → Pluscuamperfecto
  - "voy a cantar" → analyticalFuture
  - "ir a Madrid" → kein Label

### Technical Details

**Performance:**
- v2 Overhead: +7% Laufzeit (Gap-Handling)
- Dateigröße: +47% (IDs + norm + flache Felder)
- Idempotenz verhindert unnötige Re-Runs

**Compatibility:**
- v1-Dateien werden automatisch migriert
- Alte Annotations-Felder werden überschrieben
- Backup empfohlen vor Migration

---

## [2.0.0] - 2025-11-07: "Docs as Code" Reorganization

### Major Changes

#### 🗂️ Structure Overhaul
- **Introduced 8-category taxonomy**: `concepts/`, `how-to/`, `reference/`, `operations/`, `design/`, `decisions/`, `migration/`, `troubleshooting/`, `archived/`
- **Created master index**: `docs/index.md` with navigation by category and task
- **Archived obsolete docs**: 5 completed analysis files moved to `archived/`

#### 📝 Front-Matter Metadata
- **Added YAML front-matter** to all 25 active documentation files
- **Schema**: `title`, `status`, `owner`, `updated`, `tags`, `links`
- **Enables**: Searchability, status tracking, ownership clarity

#### 📄 File Organization
**Moved** (15 files):
- `architecture.md` → `concepts/architecture.md`
- `token-input-multi-paste.md` → `how-to/token-input-usage.md`
- `database_maintenance.md` → `reference/database-maintenance.md`
- `media-folder-structure.md` → `reference/media-folder-structure.md`
- `deployment.md` → `operations/deployment.md`
- `gitlab-setup.md` → `operations/gitlab-setup.md`
- `git-security-checklist.md` → `operations/git-security-checklist.md`
- `mobile-speaker-layout.md` → `design/mobile-speaker-layout.md`
- `stats-interactive-features.md` → `design/stats-interactive-features.md`
- `roadmap.md` → `decisions/roadmap.md`
- 5 analysis docs → `archived/` (CleaningUp.md, DeleteObsoleteDocumentation.md, etc.)

**Split** (3 large files → 11 total):
1. `auth-flow.md` (466 lines) → 3 files:
   - `concepts/authentication-flow.md` (Overview & Login-Szenarien)
   - `reference/api-auth-endpoints.md` (API-Dokumentation)
   - `troubleshooting/auth-issues.md` (Bekannte Probleme)

2. `design-system.md` (200 lines) → 4 files:
   - `design/design-system-overview.md` (Philosophie & Layout)
   - `design/design-tokens.md` (CSS Custom Properties)
   - `design/material-design-3.md` (MD3-Implementierung)
   - `design/accessibility.md` (WCAG-Konformität)

3. `troubleshooting.md` (638 lines) → 4 files:
   - `troubleshooting/docker-issues.md` (Server & Deployment)
   - `troubleshooting/database-issues.md` (DB Performance)
   - `troubleshooting/auth-issues.md` (Login & Token - merged with auth-flow split)
   - `troubleshooting/frontend-issues.md` (UI & DataTables)

#### 🔗 Link Updates
- **Fixed ~40 internal links** across all documentation
- **Converted to relative paths**: `../reference/database-maintenance.md`
- **Updated README.md**: Links point to new locations

#### 📋 New Documentation
- **`docs/index.md`**: Master navigation index
- **`decisions/ADR-0001-docs-reorganization.md`**: Architecture Decision Record
- **`docs/CHANGELOG.md`**: This file

#### 🗄️ Archived Planning Documents
- `PLAN.md` → `docs/archived/PLAN.md`
- `QUALITY_REPORT.md` → `docs/archived/QUALITY_REPORT.md`

### Git Commits
- Single atomic commit: `docs: Reorganize documentation (Docs as Code) - ADR-0001`
- Used `git mv` to preserve file history

### Impact
- **25 active files** with front-matter
- **9 new directories** for clear taxonomy
- **~1,300 lines** split from 3 monolithic files
- **0 broken links** (validated post-migration)

---

## [1.2.0] - 2024-11-06: Root Directory Cleanup

### Changes
- **Moved** `DEPLOYMENT.md` → `docs/deployment.md`
- **Moved** `GIT_SECURITY_CHECKLIST.md` → `docs/git-security-checklist.md`
- **Removed** test credentials from `startme.md`
- **Updated** README.md with "Key Resources" section

### Commits
- `f123f41`: Reorganize root directory, remove test credentials
- `d171a69`: Add cleanup completion report

---

## [1.1.0] - 2024-11-05: Obsolete Documentation Cleanup

### Changes
- **Archived** `docs/bug-report-auth-session.md` → `LOKAL/records/archived_docs/bugs/`
- **Verified** Token-Input feature (ACTIVE) - kept `docs/token-input-multi-paste.md`
- **Verified** Migration Token-ID v2 (COMPLETE) - archived to `LOKAL/records/archived_docs/migration/`
- **Created** analysis documents: `CleaningUp.md`, `DeleteObsoleteDocumentation.md`, `DocumentationSummary.md`

### Commits
- `94a3f4b`: Archive bug report, remove archived docs
- `4e1ae34`: Update DeleteObsoleteDocumentation.md

---

## [1.0.0] - 2024-10 and earlier

### Initial Documentation
- Flat `docs/` structure with 18 files
- No front-matter metadata
- Mixed naming conventions (CAPS, lowercase, kebab-case)
- Large monolithic files (`troubleshooting.md`, `auth-flow.md`)

---

## Future Roadmap

### Planned Improvements
- [ ] **Auto-generated API docs** (Sphinx/pdoc3 for Python docstrings)
- [ ] **Link checker CI** (Validate internal links on every commit)
- [ ] **MkDocs integration** (Optional: Generate static site from Markdown)
- [ ] **Search functionality** (Algolia DocSearch or local lunr.js)
- [ ] **Dark mode support** (Front-matter flag: `theme: auto|light|dark`)

### Maintenance Guidelines
- **New docs**: Always include front-matter
- **Large files (>400 lines)**: Consider splitting by logical domain
- **Links**: Always use relative paths
- **Archive**: Move completed/obsolete docs to `archived/` (don't delete)
- **ADRs**: Document significant architecture decisions in `decisions/`

---

**Last Updated:** 2025-11-07  
**Contributors:** Felix Tacke
