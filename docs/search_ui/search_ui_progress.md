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
