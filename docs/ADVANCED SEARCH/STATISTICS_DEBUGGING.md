# Statistics Debugging & Implementation Report

## Problem Description
The advanced search statistics were showing:
1. Empty counts for speaker metadata (Sex, Mode, Discourse).
2. Incorrect labels (hash strings like `ven74a1bdb4c`) in some charts.
3. Inconsistency between DataTables results and Statistics.

## Root Cause Analysis
1. **Missing Index Fields**: The BlackLab index was missing `speaker_sex`, `speaker_mode`, and `speaker_discourse` fields because the TSV export script (`blacklab_index_creation.py`) was not exporting them from the source JSON files.
2. **Field Name Mismatch**: The API was querying `speaker_sex` but the index (when it had data) might have used `sex` in some versions.
3. **Frontend Mapping**: The "hash strings" were likely `token_id`s or `utterance_id`s being returned when the expected metadata fields were missing or misconfigured.

## Solution Implemented

### 1. Backend (Index Generation)
* Modified `LOKAL/01 - Add New Transcriptions/03b build blacklab_index/blacklab_index_creation.py` to explicitly export:
  * `speaker_sex`
  * `speaker_mode`
  * `speaker_discourse`
  * `country_scope`, `country_parent_code`, `country_region_code`
* Rebuilt the BlackLab index using the updated TSV files.

### 2. Backend (API)
* Updated `src/app/search/advanced_api.py` to use robust aggregation with fallback logic:
  ```python
  by_sex = aggregate_dimension("speaker_sex", "sex")
  by_mode = aggregate_dimension("speaker_mode", "mode")
  by_discourse = aggregate_dimension("speaker_discourse", "discourse")
  ```
* Ensured API response keys match Frontend expectations (`by_sexo`, `by_modo`).

### 3. Verification
* **API Response**: Now returns populated counts for all dimensions.
  * `by_sexo`: m, f
  * `by_modo`: lectura, libre, pre, n/a
  * `by_discourse`: general, tiempo
  * `by_country`: Correct country codes (e.g., "ven", "arg")
* **Data Consistency**: Total hits match between DataTables and Stats.

## Technical Details

### API Endpoint
* **URL**: `GET /search/advanced/stats`
* **Parameters**: Same as DataTables (`q`, `patt`, filters...)
* **Response Format**:
  ```json
  {
    "total_hits": 1496423,
    "by_country": [{"key": "ven", "n": 3000, "p": 0.002}, ...],
    "by_sexo": [{"key": "m", "n": 1638, "p": 0.546}, ...],
    ...
  }
  ```

### Frontend Integration
* **File**: `static/js/modules/stats/initStatsTabAdvanced.js`
* **Mapping**:
  * `data.by_country` -> Country Chart
  * `data.by_sexo` -> Sex Chart
  * `data.by_modo` -> Mode Chart

## Future Maintenance
* If adding new metadata fields, ensure they are:
  1. Present in JSON source.
  2. Exported in `blacklab_index_creation.py`.
  3. Defined in `config/blacklab/corapan-tsv.blf.yaml`.
  4. Aggregated in `advanced_api.py`.
