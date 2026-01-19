# Runtime Data Audit — Editor / Player / Metadata / Atlas

**Date:** 2026-01-18  
**Repo:** corapan-webapp  
**Scope:** /editor/, /corpus/player, /corpus/metadata, /atlas (inkl. Legacy)

---

## 1) Page → Requests Map (Frontend)

### /editor/ (Overview + Edit UI)
**Frontend sources:**
- Editor config + API endpoints: [templates/pages/editor.html](templates/pages/editor.html#L138-L152)
- Editor entry: [static/js/modules/editor/entry.js](static/js/modules/editor/entry.js#L1-L26)
- Media loads: [static/js/editor/editor-player.js](static/js/editor/editor-player.js#L20-L48)
- Save edits: [static/js/editor/word-editor.js](static/js/editor/word-editor.js#L360-L418)
- Bookmarks add/remove: [static/js/editor/bookmark-manager.js](static/js/editor/bookmark-manager.js#L200-L276)
- History + undo: [static/js/editor/history-panel.js](static/js/editor/history-panel.js#L20-L170)

**XHR / fetch / API requests:**
- GET /media/transcripts/<country>/<file>.json  
  Source: `EditorPlayer` uses `/media/transcripts/${transcriptFile}`.  
  Evidence: [static/js/editor/editor-player.js](static/js/editor/editor-player.js#L40-L48)
- GET /media/full/<country>/<file>.mp3  
  Source: `EditorPlayer` uses `/media/full/${audioFile}`.  
  Evidence: [static/js/editor/editor-player.js](static/js/editor/editor-player.js#L30-L37)
- POST /editor/save-edits  
  Source: `WordEditor.saveAllChanges()` posts to `apiEndpoints.saveEdits`.  
  Evidence: [static/js/editor/word-editor.js](static/js/editor/word-editor.js#L380-L412), [templates/pages/editor.html](templates/pages/editor.html#L145-L151)
- POST /editor/bookmarks/add  
  Source: `BookmarkManager.addBookmark()` posts to `apiEndpoints.addBookmark`.  
  Evidence: [static/js/editor/bookmark-manager.js](static/js/editor/bookmark-manager.js#L204-L221), [templates/pages/editor.html](templates/pages/editor.html#L146-L149)
- POST /editor/bookmarks/remove  
  Source: `BookmarkManager.removeBookmark()` posts to `apiEndpoints.removeBookmark`.  
  Evidence: [static/js/editor/bookmark-manager.js](static/js/editor/bookmark-manager.js#L260-L276), [templates/pages/editor.html](templates/pages/editor.html#L147-L149)
- GET /editor/history/<country>/<filename>  
  Source: `HistoryPanel.loadHistory()`.  
  Evidence: [static/js/editor/history-panel.js](static/js/editor/history-panel.js#L20-L58)
- POST /editor/undo  
  Source: `HistoryPanel.undoChange()`.  
  Evidence: [static/js/editor/history-panel.js](static/js/editor/history-panel.js#L120-L170)

**Configured but currently unused:**
- GET /editor/bookmarks/<country>/<filename> is provided in config but no frontend fetch found.  
  Evidence: [templates/pages/editor.html](templates/pages/editor.html#L146-L151)

**Data-relevant static assets:**
- Transcript JSON and MP3 served via /media (see above). No other data assets.

**Minimum response set consumed by UI:**
- /media/transcripts/* must include:  
  `segments[]` (with `words[]`, `text` or `word`, `start`, `end`, `token_id`),  
  `filename`, `country_display`, `radio`, `city`, `date`, `revision`.  
  Evidence: [static/js/player/modules/transcription.js](static/js/player/modules/transcription.js#L24-L150)
- /editor/save-edits response: `{ success: true }` + optional `message`.  
  Evidence: [static/js/editor/word-editor.js](static/js/editor/word-editor.js#L410-L440)
- /editor/bookmarks/add response: `{ success: true, bookmark: {...} }`.  
  Evidence: [static/js/editor/bookmark-manager.js](static/js/editor/bookmark-manager.js#L222-L238)
- /editor/history response: `{ success: true, history: [...] }`.  
  Evidence: [static/js/editor/history-panel.js](static/js/editor/history-panel.js#L52-L70)
- /editor/undo response: `{ success: true }`.  
  Evidence: [static/js/editor/history-panel.js](static/js/editor/history-panel.js#L150-L170)

---

### /corpus/player (Player Overview)
**Frontend sources:**
- Template: [templates/pages/player_overview.html](templates/pages/player_overview.html#L1-L56)
- Data loading + links: [static/js/modules/player-overview.js](static/js/modules/player-overview.js#L300-L452)
- Player URL builder: [static/js/modules/player-url.js](static/js/modules/player-url.js#L1-L12)

**XHR / fetch / API requests:**
- GET /api/v1/atlas/files  
  Evidence: [static/js/modules/player-overview.js](static/js/modules/player-overview.js#L410-L445)

**Navigation (not XHR):**
- GET /player?transcription=/media/transcripts/...&audio=/media/full/...  
  Evidence: [static/js/modules/player-overview.js](static/js/modules/player-overview.js#L300-L320), [static/js/modules/player-url.js](static/js/modules/player-url.js#L1-L12)

**Downstream data calls (player page flow):**
- GET /media/transcripts/<country>/<file>.json  
  Evidence: [static/js/player/modules/transcription.js](static/js/player/modules/transcription.js#L24-L88)
- GET /media/full/<country>/<file>.mp3  
  Evidence: [static/js/player/modules/audio.js](static/js/player/modules/audio.js#L26-L54)

**Minimum response set consumed by UI:**
- /api/v1/atlas/files must include:  
  `filename`, `country_code` (or code in `filename`), `radio`, `date`, `duration`, `word_count`.  
  Evidence: [static/js/modules/player-overview.js](static/js/modules/player-overview.js#L260-L365)
- /media/transcripts/*: see editor section (same player module).  
  Evidence: [static/js/player/modules/transcription.js](static/js/player/modules/transcription.js#L24-L150)

---

### /corpus/metadata
**Frontend sources:**
- Template: [templates/pages/corpus_metadata.html](templates/pages/corpus_metadata.html#L100-L188)
- JS module: [static/js/modules/corpus-metadata.js](static/js/modules/corpus-metadata.js#L1-L840)

**XHR / fetch / API requests:**
- GET /api/v1/atlas/files  
  Evidence: [static/js/modules/corpus-metadata.js](static/js/modules/corpus-metadata.js#L669-L690)

**Download endpoints (navigation):**
- GET /corpus/metadata/download/tsv  
- GET /corpus/metadata/download/json  
- GET /corpus/metadata/download/jsonld  
- GET /corpus/metadata/download/tei  
  Evidence: [templates/pages/corpus_metadata.html](templates/pages/corpus_metadata.html#L114-L127)
- GET /corpus/metadata/download/tsv/<country>  
- GET /corpus/metadata/download/json/<country>  
  Evidence: [static/js/modules/corpus-metadata.js](static/js/modules/corpus-metadata.js#L588-L600)

**Data-relevant static assets:**
- GET /corpus/api/statistics/viz_total_corpus.png  
- GET /corpus/api/statistics/viz_genero_profesionales.png  
- GET /corpus/api/statistics/viz_modo_genero_profesionales.png  
  Evidence: [templates/pages/corpus_metadata.html](templates/pages/corpus_metadata.html#L149-L186)
- GET /corpus/api/statistics/viz_<country>_resumen.png  
  Evidence: [static/js/modules/corpus-metadata.js](static/js/modules/corpus-metadata.js#L492-L499)

**Minimum response set consumed by UI:**
- /api/v1/atlas/files must include:  
  `filename`, `country_code` (or code in `filename`), `radio`, `date`, `duration`, `word_count`.  
  Evidence: [static/js/modules/corpus-metadata.js](static/js/modules/corpus-metadata.js#L430-L520)
- /corpus/metadata/download/* must serve the requested file (no JSON schema required).
- /corpus/api/statistics/* images must exist for displayed countries; failures hide cards.  
  Evidence: [static/js/modules/corpus-metadata.js](static/js/modules/corpus-metadata.js#L627-L641)

---

### /atlas
**Frontend sources:**
- Template: [templates/pages/atlas.html](templates/pages/atlas.html#L1-L33)
- Atlas module: [static/js/modules/atlas/index.js](static/js/modules/atlas/index.js#L1-L580)

**XHR / fetch / API requests:**
- GET /api/v1/atlas/countries  
  Evidence: [static/js/modules/atlas/index.js](static/js/modules/atlas/index.js#L500-L528)
- GET /api/v1/atlas/files  
  Evidence: [static/js/modules/atlas/index.js](static/js/modules/atlas/index.js#L530-L548)

**External data sources:**
- OpenStreetMap tiles: https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png  
  Evidence: [static/js/modules/atlas/index.js](static/js/modules/atlas/index.js#L488-L496)

**Data-relevant static assets:**
- Marker icons under /static/img/citymarkers/...  
  Evidence: [static/js/modules/atlas/index.js](static/js/modules/atlas/index.js#L206-L242)

**Minimum response set consumed by UI:**
- /api/v1/atlas/countries must include:  
  `country_code`, `total_word_count`, `total_duration`  
  Evidence: [static/js/modules/atlas/index.js](static/js/modules/atlas/index.js#L320-L370)
- /api/v1/atlas/files must include:  
  `country_code` (or code in `filename`), `radio`, `filename` (for fallback).  
  Evidence: [static/js/modules/atlas/index.js](static/js/modules/atlas/index.js#L310-L336)

---

## 2) Endpoint → Datenquelle (Backend)

### Atlas API
**/api/v1/atlas/countries**  
- Route: `countries()` in [src/app/routes/atlas.py](src/app/routes/atlas.py#L17-L23)  
- Service: `fetch_country_stats()` in [src/app/services/atlas.py](src/app/services/atlas.py#L17-L36)  
- Data source: SQLite DB `stats_country` via `open_db("stats_country")`  
  - DB path resolution: `CORAPAN_RUNTIME_ROOT` → `DATA_ROOT` → `DATA_ROOT/db/public/stats_country.db`  
  - Resolution code: [src/app/services/database.py](src/app/services/database.py#L12-L43)  
- Resolved path (pseudo-trace):  
  - If `CORAPAN_RUNTIME_ROOT` set: `${CORAPAN_RUNTIME_ROOT}/data/db/public/stats_country.db`  
  - Dev fallback: repo/runtime/corapan/data/db/public/stats_country.db  
- Public/restricted: **public** (stats DB)  
- Caching: Flask-Caching `@cache.cached(timeout=3600)`  
  - Evidence: [src/app/routes/atlas.py](src/app/routes/atlas.py#L17-L23)  
  - Cache key: default Flask-Caching key (request path + query string).

**/api/v1/atlas/files**  
- Route: `files()` in [src/app/routes/atlas.py](src/app/routes/atlas.py#L24-L30)  
- Service: `fetch_file_metadata()` in [src/app/services/atlas.py](src/app/services/atlas.py#L177-L210)  
- Data source: Filesystem (metadata exports)  
  - Root resolve: `CORAPAN_RUNTIME_ROOT` → `${CORAPAN_RUNTIME_ROOT}/data/public/metadata`  
    or dev fallback to repo/runtime/corapan/data/public/metadata.  
    Evidence: [src/app/services/atlas.py](src/app/services/atlas.py#L41-L58)  
  - Selected directory: `${metadata_root}/tei` (no `latest/` suffix).  
    Evidence: [src/app/services/atlas.py](src/app/services/atlas.py#L63-L70)  
  - Files read: `corapan_recordings*.json` or `corapan_recordings*.tsv` from that directory.  
    Evidence: [src/app/services/atlas.py](src/app/services/atlas.py#L106-L156)  
- Public/restricted: **public** (metadata exports)  
- Caching:  
  - Flask-Caching `@cache.cached(timeout=3600)`  
    Evidence: [src/app/routes/atlas.py](src/app/routes/atlas.py#L24-L30)  
  - In-process mtime cache `_FILES_CACHE` keyed by metadata dir mtime  
    Evidence: [src/app/services/atlas.py](src/app/services/atlas.py#L38-L207)

**/atlas/countries**, **/atlas/files** (legacy)  
- Route: redirects to v1 API  
  Evidence: [src/app/routes/atlas.py](src/app/routes/atlas.py#L50-L58)

---

### Corpus Metadata + Statistics
**/corpus/metadata/download/tsv|json|jsonld|tei**  
- Route: `metadata_download_*()` in [src/app/routes/corpus.py](src/app/routes/corpus.py#L421-L460)  
- Data source: Filesystem under `DATA_ROOT/public/metadata` (prefers `latest/` if present)  
  - Resolution: `DATA_ROOT` from `CORAPAN_RUNTIME_ROOT` or dev fallback.  
  - Evidence: [src/app/routes/corpus.py](src/app/routes/corpus.py#L112-L134), [src/app/config/__init__.py](src/app/config/__init__.py#L96-L118)
- Resolved path (pseudo-trace):  
  - If `CORAPAN_RUNTIME_ROOT` set: `${CORAPAN_RUNTIME_ROOT}/data/public/metadata/latest` when present, else `${CORAPAN_RUNTIME_ROOT}/data/public/metadata`  
  - Dev fallback: repo/runtime/corapan/data/public/metadata/latest when present, else repo/runtime/corapan/data/public/metadata  
- Public/restricted: **public**

**/corpus/metadata/download/tsv/<country>**, **/corpus/metadata/download/json/<country>**  
- Route: `metadata_country_tsv()` and `metadata_country_json()` in [src/app/routes/corpus.py](src/app/routes/corpus.py#L466-L535)  
- Data source: `corapan_recordings.json` from `DATA_ROOT/public/metadata/latest` if present, else `DATA_ROOT/public/metadata`  
  Evidence: [src/app/routes/corpus.py](src/app/routes/corpus.py#L122-L166)

**/corpus/api/statistics/<filename>**  
- Route: `serve_statistics()` in [src/app/routes/corpus.py](src/app/routes/corpus.py#L251-L334)  
- Data source: Filesystem under `PUBLIC_STATS_DIR`  
  - `PUBLIC_STATS_DIR` resolution: explicit env `PUBLIC_STATS_DIR` → else `${CORAPAN_RUNTIME_ROOT}/data/public/statistics` → dev fallback repo/runtime/corapan/data/public/statistics.  
  - Evidence: [src/app/config/__init__.py](src/app/config/__init__.py#L150-L206)
- Public/restricted: **public**
- Caching: response headers `Cache-Control: public, max-age=3600`  
  Evidence: [src/app/routes/corpus.py](src/app/routes/corpus.py#L307-L333)

**/corpus/api/** + **corpus_stats**  
- Route: `corpus_stats()` in [src/app/routes/corpus.py](src/app/routes/corpus.py#L204-L249)  
- Data source: `${PUBLIC_STATS_DIR}/corpus_stats.json`  
  Evidence: [src/app/routes/corpus.py](src/app/routes/corpus.py#L220-L247)
- Public/restricted: **public**
- Caching: response headers `Cache-Control: public, max-age=3600`  
  Evidence: [src/app/routes/corpus.py](src/app/routes/corpus.py#L242-L247)

---

### Player Page
**/player** (page render)  
- Route: `player_page()` in [src/app/routes/player.py](src/app/routes/player.py#L35-L125)  
- Data source: none (template render + URL normalization).  
- Side effects: normalizes `audio` param to include country segment if missing.  
  Evidence: [src/app/routes/player.py](src/app/routes/player.py#L68-L104)

**/media/transcripts/<filename>**  
- Route: `fetch_transcript()` in [src/app/routes/media.py](src/app/routes/media.py#L180-L239)  
- Data source: Filesystem under `TRANSCRIPTS_DIR` (`CORAPAN_MEDIA_ROOT/transcripts`).  
  Evidence: [src/app/config/__init__.py](src/app/config/__init__.py#L128-L144), [src/app/services/media_store.py](src/app/services/media_store.py#L34-L115)  
- Access: authenticated users or `ALLOW_PUBLIC_TRANSCRIPTS=true`.  
  Evidence: [src/app/routes/media.py](src/app/routes/media.py#L188-L201)
- Public/restricted: **restricted by auth** (unless explicitly enabled).

**/media/full/<filename>**  
- Route: `download_full()` in [src/app/routes/media.py](src/app/routes/media.py#L70-L118)  
- Data source: Filesystem under `AUDIO_FULL_DIR` (`CORAPAN_MEDIA_ROOT/mp3-full`).  
  Evidence: [src/app/config/__init__.py](src/app/config/__init__.py#L140-L144), [src/app/services/media_store.py](src/app/services/media_store.py#L28-L113)  
- Access: authenticated users or `ALLOW_PUBLIC_FULL_AUDIO=true`.  
  Evidence: [src/app/routes/media.py](src/app/routes/media.py#L78-L94)
- Public/restricted: **restricted by auth** (unless explicitly enabled).

- Caching for media: `send_file(..., conditional=True)` supports conditional requests.  
  Evidence: [src/app/routes/media.py](src/app/routes/media.py#L30-L63)

---

### Editor API
**/editor/** (overview)  
- Route: `overview()` in [src/app/routes/editor.py](src/app/routes/editor.py#L35-L81)  
- Data sources:  
  - Filesystem: `TRANSCRIPTS_DIR` country folders.  
  - SQLite stats DB: `stats_files.db` via `open_db("stats_files")`.  
  - Edit log: `${TRANSCRIPTS_DIR}/edit_log.jsonl`.  
  Evidence: [src/app/routes/editor.py](src/app/routes/editor.py#L19-L57), [src/app/routes/editor.py](src/app/routes/editor.py#L495-L557), [src/app/services/database.py](src/app/services/database.py#L38-L58)

**/editor/edit**  
- Route: `edit_file()` in [src/app/routes/editor.py](src/app/routes/editor.py#L82-L119)  
- Data source: Filesystem `TRANSCRIPTS_DIR` (validation only).  
  Evidence: [src/app/routes/editor.py](src/app/routes/editor.py#L92-L110)

**/editor/save-edits**  
- Route: `save_edits()` in [src/app/routes/editor.py](src/app/routes/editor.py#L120-L206)  
- Data sources:  
  - Transcripts JSON under `TRANSCRIPTS_DIR/<country>/<file>.json`  
  - Backup dir `${TRANSCRIPTS_DIR}/<country>/backup/` (original + diffs)  
  - Edit log `${TRANSCRIPTS_DIR}/edit_log.jsonl`  
  Evidence: [src/app/routes/editor.py](src/app/routes/editor.py#L145-L203), [src/app/routes/editor.py](src/app/routes/editor.py#L594-L633)

**/editor/bookmarks/add** and **/editor/bookmarks/remove**  
- Routes: `add_bookmark()` and `remove_bookmark()` in [src/app/routes/editor.py](src/app/routes/editor.py#L207-L339)  
- Data source: same transcript JSON file in `TRANSCRIPTS_DIR`.  

**/editor/history/<country>/<filename>**  
- Route: `get_history()` in [src/app/routes/editor.py](src/app/routes/editor.py#L340-L378)  
- Data source: `${TRANSCRIPTS_DIR}/<country>/backup/<stem>_diffs.jsonl`  

**/editor/undo**  
- Route: `undo_change()` in [src/app/routes/editor.py](src/app/routes/editor.py#L379-L463)  
- Data sources:  
  - `${TRANSCRIPTS_DIR}/<country>/backup/<stem>_original.json`  
  - `${TRANSCRIPTS_DIR}/<country>/backup/<stem>_diffs.jsonl`  
  - `${TRANSCRIPTS_DIR}/edit_log.jsonl`  

**/editor/bookmarks/<country>/<filename>**  
- Route: `get_bookmarks()` in [src/app/routes/editor.py](src/app/routes/editor.py#L464-L494)  
- Data source: transcript JSON file in `TRANSCRIPTS_DIR`.

---

## 3) Runtime-Data Contract (Soll-Zustand)

**Source of Truth Matrix**

| Data type | Runtime location | Public/Restricted | Evidence / Notes |
|---|---|---|---|
| Public corpus metadata exports (TSV/JSON/JSON-LD, TEI ZIP) | runtime/corapan/data/public/metadata/latest | Public | Used by metadata download endpoints. [src/app/routes/corpus.py](src/app/routes/corpus.py#L112-L166) |
| Atlas file metadata inputs (corapan_recordings*.json/tsv) | runtime/corapan/data/public/metadata/latest/tei | Public | Atlas reads from `metadata/latest/tei`. [src/app/services/atlas.py](src/app/services/atlas.py#L63-L156) |
| Public statistics images + corpus_stats.json | runtime/corapan/data/public/statistics | Public | `PUBLIC_STATS_DIR` resolution. [src/app/config/__init__.py](src/app/config/__init__.py#L150-L206) |
| Public stats DBs (stats_files.db, stats_country.db) | runtime/corapan/data/db/public | Public | SQLite stats DBs. [src/app/services/database.py](src/app/services/database.py#L38-L43) |
| Auth + analytics DBs | runtime/corapan/data/db/restricted | Restricted | Config points to restricted DBs. [src/app/config/__init__.py](src/app/config/__init__.py#L121-L125) |
| Media transcripts JSON | runtime/corapan/media/transcripts | Restricted (by auth flags) | Requires `CORAPAN_MEDIA_ROOT`. [src/app/config/__init__.py](src/app/config/__init__.py#L128-L144) |
| Media full MP3 | runtime/corapan/media/mp3-full | Restricted (by auth flags) | Same as above. |
| Media split + temp MP3 | runtime/corapan/media/mp3-split, mp3-temp | Restricted (temp may be public via flag) | Flags: `ALLOW_PUBLIC_TEMP_AUDIO`, `ALLOW_PUBLIC_FULL_AUDIO`. [src/app/config/__init__.py](src/app/config/__init__.py#L211-L217) |

---

## 4) Drift-/Altlasten-Liste (mit Priorisierung)

**P0 (muss vor Prod-Fix) — none found**

**P1 (should fix soon)**
- None (canonical runtime paths enforced).

**P2 (cleanup / deprecate)**
- None (legacy references removed).

---

## 5) Prod-Validation Plan

**Prereq:** Ensure auth cookies for protected endpoints (editor/media/player). For unauth tests, expect 401/303, not 500.

### Atlas API
- GET /api/v1/atlas/countries  
  - Expect: 200, JSON `{countries: [...]}`  
  - Minimal schema: each item has `country_code`, `total_word_count`, `total_duration`.
- GET /api/v1/atlas/files  
  - Expect: 200, JSON `{files: [...]}`  
  - Minimal schema: each item has `filename`, `country_code`, `radio`, `date`, `duration`, `word_count`.

### Corpus metadata
- GET /corpus/metadata/download/tsv  
  - Expect: 200, `text/tab-separated-values`.
- GET /corpus/metadata/download/json  
  - Expect: 200, JSON array or `{recordings: [...]}`.
- GET /corpus/metadata/download/jsonld  
  - Expect: 200, `application/ld+json`.
- GET /corpus/metadata/download/tei  
  - Expect: 200, `application/zip`.
- GET /corpus/api/statistics/viz_total_corpus.png  
  - Expect: 200, `image/png`.
- GET /corpus/api/statistics/viz_<country>_resumen.png  
  - Expect: 200 or 404 if not generated (must not 500).

### Player flow
- GET /corpus/player  
  - Unauth: 303 redirect to /login (or 204 + HX-Redirect for HTMX).  
  - Auth: 200 HTML page.
- GET /player?transcription=...&audio=...  
  - Unauth: 303 redirect to /login.  
  - Auth: 200 HTML page.
- GET /media/transcripts/<file>.json  
  - Unauth: 401 (unless `ALLOW_PUBLIC_TRANSCRIPTS=true`).  
  - Auth: 200 JSON.
- GET /media/full/<file>.mp3  
  - Unauth: 401 (unless `ALLOW_PUBLIC_FULL_AUDIO=true`).  
  - Auth: 200 audio/mpeg.

### Editor
- GET /editor/  
  - Unauth: 401.  
  - Auth (role editor/admin): 200 HTML page.
- POST /editor/save-edits  
  - Expect: 200 `{success:true}` for valid payload.
- GET /editor/history/<country>/<filename>  
  - Expect: 200 `{success:true, history:[...]}`.
- POST /editor/undo  
  - Expect: 200 `{success:true}`.

**Must-not-500 list:**  
`/api/v1/atlas/countries`, `/api/v1/atlas/files`, `/corpus/metadata`, `/corpus/metadata/download/*`, `/corpus/api/statistics/*`, `/corpus/player`, `/player`, `/media/transcripts/*`, `/media/full/*`, `/editor/*`.

---

## Bonus: Runtime Path Trace Script (optional)
A lightweight dev helper exists at [scripts/trace_runtime_paths.py](scripts/trace_runtime_paths.py). It prints resolved runtime paths and flags missing directories without leaking secrets.
