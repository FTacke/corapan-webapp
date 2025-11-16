# Search UI - Progress Log

This file records progress, changes and open items while wiring the Search UI to BlackLab.

## 2025-11-15 - Initial pass
- Created `search_ui_progress.md` and `search_ui_tests.md`.
- Located relevant code:
  - Templates: `templates/pages/corpus.html`, `templates/search/advanced.html`.
  - Backend: `src/app/routes/corpus.py`, `src/app/routes/search/advanced.py`, `src/app/services/corpus_search.py` (SQLite) and `src/app/search/cql.py` (CQL builder).
  - Advanced search already uses BlackLab via `get_http_client()` and `bls` proxy (`/bls/corapan/hits`).
  - Simple search currently queries local SQLite `search_tokens`.
- Observed inconsistencies to address:
  - UI `search_mode` values (text/text_exact/lemma_exact) vs CQL `mode` expected by `cql.build_cql` (forma/forma_exacta/lemma).
  - `build_filters` logic currently sets `radio='national'` only when `include_regional` is explicitly provided and false; need to interpret missing checkbox as false to match default behavior.
  - `PatternBuilder` JS builds CQL token blocks; we need to ensure `allow-manual-edit` controls override behavior.

## Next steps
- Implement `blacklab_search` service and wire `corpus.search`/`search_datatables` to call it for textual searches.
- Adjust `cql.build_filters` to handle `include_regional` defaulting to national-only (if unchecked).
- Add mapping for `search_mode` values to CQL `mode` and build proper contains/regex or exact CQL depending on input.

## 2025-11-15 - Implemented BlackLab search wrapper
- Added `src/app/services/blacklab_search.py` with `search_blacklab()` to query BlackLab and map hits to canonical DataTables format.
- Updated `corpus.search` and `search_datatables` to prefer BlackLab for text/lemma searches, falling back to SQLite for token-IDs or on errors.
- Adjusted `cql.build_filters` include_regional handling to default to national senders when not explicitly set to include regionals.
- Updated advanced `searchUI.js` to send `sensitive` flag and to adjust CQL preview to use `norm` when insensitive.

## Outstanding items
- Ensure the CQL translation respects 'contains' semantics for simple text searches (now using regex `.*value.*` by default for non-exact).
- Improve mapping of BlackLab hit metadata to `CANON_COLS` (filename, country, etc.) depending on `listvalues` availability.
- Add more test cases and perform manual testing with BlackLab running.

## Next steps
- Run manual tests in `docs/search_ui/search_ui_tests.md` against a running BlackLab Docker container.
- Extend `blacklab_search._hit_to_canonical()` mapping for edge cases (e.g., missing `word` arrays -> look up token entry in local DB if needed).
- Add server-side caching for repeated CQL queries (future performance optimization).

## Implemented fields and mapping
- Country field name: `country_code` (lowercase values in index)
- Radio station type mapped as: `radio` (metadata annotation)
- Sender-type granular codes: `speaker_code` used for speaker_type/sex/mode/discourse mapping

## How the País + Incluir emisoras regionales logic is represented
- Cases implemented in `src/app/routes/corpus.py` and `src/app/search/cql.py`:
  - No country selected + include_regional unchecked → `countries` set to national codes only in `corpus.search` (case 1).
  - No country selected + include_regional checked → `countries` set to national + regional codes (case 2).
  - Countries selected + include_regional unchecked → `countries` filtered to exclude regional codes (case 3).
  - Countries selected + include_regional checked → `countries` left as selected values (case 4).

Implementation details:
- `corpus.search` computes the `countries` list to pass into `SearchParams`.
- `build_filters()` (in `src/app/search/cql.py`) sets `radio="national"` when `include_regional` is not explicitly set to '1'. This enforces the default behavior.

- For integration with BlackLab, we use `build_cql_with_speaker_filter()` to merge token-level constraints with `speaker_code` and metadata constraints (country, radio, city, date), adding them to the first token.

## Pattern-Builder details
- Pattern builder generates `CQL tokens` for word, lemma, pos, with match types: `exact`, `contains` (`.*value.*`), `starts` (`value.*`), `ends` (`.*value`).
- Distance rule: `consecutive` -> space-separated tokens, `gap` -> `[]{0,N}` pattern.
- Distance N is clamped to 0..10 in JS and will be clamped server-side if needed.

## Completed verification steps
- `corpus.search` now prefers BlackLab for non-token-id textual searches and formats output as canonical columns for DataTables.
- Advanced `initTable` and `corpus` DataTables both expect object-mode (keys) now and are fed by the BlackLab service where possible.
- Frontend: `corpus/index.js` imports `corpusForm.js` (hidden input helper) and `CorpusSearchManager` sends `sensitive` and `include_regional` as explicit params.
- Frontend: `searchUI.js` (Advanced) sends `sensitive` flag and the CQL preview gets normalized to `norm` in case-insensitive mode (for non-manual edits) before searching.

## Open points
- Mapping CQL 'contains' semantics to BlackLab. For now, we will use regex `.*value.*` for text contains.
- How to handle `sensitive`/`ignore_accents` consistently across forms (mapping to `sensitive=0/1`).
- Format mapping from BlackLab hits to `CANON_COLS` to fill DataTables; may require adjusting `listvalues` parameters.

---

## Advanced DataTables Flow (Stand 2025-11-16)

### Overview
The Advanced Search DataTables component uses server-side processing to fetch results from BlackLab through the Flask backend.

### Request Flow
1. **Frontend (DataTables)**: `static/js/modules/advanced/initTable.js`
   - Initializes DataTables with `serverSide: true`
   - AJAX URL: `/search/advanced/data?q=...&mode=...&sensitive=...&...`
   - Sends pagination params: `draw`, `start`, `length`
   - Sends search params: `q`, `mode`, `sensitive`, filter arrays

2. **Backend Route**: `src/app/search/advanced_api.py` → `@bp.route("/data")`
   - Extracts DataTables parameters (`draw`, `start`, `length`)
   - Extracts search/filter parameters
   - Calls `build_cql_with_speaker_filter()` to construct CQL pattern
   - Calls `build_filters()` and `filters_to_blacklab_query()` for metadata
   - Makes request to BlackLab Server: `/bls/corpora/corapan/hits`

3. **BlackLab Query**: Via `_make_bls_request()`
   - Tries CQL param names: `patt`, `cql`, `cql_query`
   - Includes `listvalues` for token metadata fields
   - Returns JSON with `hits`, `summary`, `docInfos`

4. **Hit Mapping**: `src/app/services/blacklab_search.py` → `_hit_to_canonical()`
   - Maps BlackLab hit structure to canonical DataTables keys
   - Extracts KWIC context: `context_left`, `text`, `context_right`
   - Extracts metadata: `country_code`, `speaker_type`, `sex`, `mode`, `discourse`
   - Extracts audio info: `start_ms`, `end_ms`, `filename`, `token_id`

5. **Enrichment**: `advanced_api.py` → `_enrich_hits_with_docmeta()`
   - Enriches hits with docmeta.jsonl data (country, radio, date)
   - Maps speaker_code to attributes if metadata missing
   - Ensures all canonical fields are populated

6. **Response Format**: Returns JSON to DataTables
   ```json
   {
     "draw": 1,
     "recordsTotal": 1234,
     "recordsFiltered": 1234,
     "data": [
       {
         "token_id": "2022-01-18_VEN_RCR_0001",
         "filename": "2022-01-18_VEN_RCR",
         "country_code": "ven",
         "speaker_type": "pro",
         "sex": "m",
         "mode": "pre",
         "discourse": "general",
         "radio": "rcr",
         "date": "2022-01-18",
         "text": "casa",
         "context_left": "vivo en mi",
         "context_right": "desde hace años",
         "start_ms": 1234,
         "end_ms": 2345,
         "lemma": "casa"
       }
     ]
   }
   ```

### DataTables Column Mapping
The frontend `initTable.js` defines column mappings (lines 92-209):
- Column 0: Row number (computed)
- Column 1: `context_left` → KWIC left context
- Column 2: `text` → KWIC match (highlighted)
- Column 3: `context_right` → KWIC right context
- Column 4: Audio buttons (computed from `start_ms`, `end_ms`, `filename`)
- Column 5: `country_code` → País
- Column 6: `speaker_type` → Hablante
- Column 7: `sex` → Sexo
- Column 8: `mode` → Modo
- Column 9: `discourse` → Discurso
- Column 10: `token_id` → Token ID
- Column 11: `filename` → File link (with player icon)

### Key Functions
- **CQL Building**: `build_cql_with_speaker_filter()` in `cql.py`
- **Hit Mapping**: `_hit_to_canonical()` in `blacklab_search.py`
- **Enrichment**: `_enrich_hits_with_docmeta()` in `advanced_api.py`
- **DataTables Init**: `initAdvancedTable()` in `initTable.js`

---

## Display Case vs. Norm Case (Stand 2025-11-16)

### Current Implementation
The codebase currently stores all data in lowercase/normalized form:
- `country_code`: lowercase (e.g., `"ven"`, `"esp"`)
- `speaker_code`: lowercase (e.g., `"lib-pf"`, `"lec-pm"`)
- Token text (`text`): preserves original case from BlackLab index

### Display Rules
1. **Internal Codes (lowercase)**:
   - `country_code`, `speaker_code`, `radio`, `city` are stored lowercase
   - Used for filtering and CQL constraints
   - Not intended for direct display

2. **Token Text (original case)**:
   - `text`, `context_left`, `context_right` preserve original case from source
   - BlackLab returns tokens as they appear in the index
   - No forced lowercasing applied

3. **Display Fields (to be implemented)**:
   - For UI display, consider adding display-specific fields:
     - `country_label`: uppercase or full name (e.g., `"VEN"` or `"Venezuela"`)
     - `speaker_type_label`: formatted label (e.g., `"Profesional"` instead of `"pro"`)
   - Alternative: Format in DataTables column renderer (client-side)

### Current Status
- **No separate display fields yet**: All fields use internal lowercase codes
- **DataTables renders as-is**: Column renderers in `initTable.js` display values directly
- **Case preservation**: Token text correctly preserves original case from index

### Recommendations
- Add display formatting in DataTables column renderers (client-side, no backend changes)
- Or add separate `*_label` fields in `_hit_to_canonical()` for server-side formatting
- Ensure no pauschal lowercasing of token text anywhere in the pipeline
