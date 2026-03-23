# CO.RA.PAN Metadata Export

This folder contains the metadata export script for generating FAIR/DFG-compliant metadata from CO.RA.PAN transcript files.

## Script: `export_metadata.py`

### Purpose

Generates standardized metadata files from transcript JSONs located in `media/transcripts/`. The output includes:

- **Recording-level metadata** (one record per transcript):
  - `corapan_recordings.tsv` - Tab-separated values
  - `corapan_recordings.json` - JSON array
  - `corapan_recordings.jsonld` - JSON-LD with schema.org context

- **Country-level metadata** (one file pair per country):
  - `corapan_recordings_{COUNTRY_CODE}.tsv` - Country-specific recordings (TSV)
  - `corapan_recordings_{COUNTRY_CODE}.json` - Country-specific recordings (JSON)

- **Corpus-level metadata**:
  - `corapan_corpus_metadata.json` - Corpus description
  - `corapan_corpus_metadata.jsonld` - JSON-LD version

- **TEI Headers**:
  - `tei/` - Individual TEI header files per recording
  - `tei_headers.zip` - ZIP archive of all TEI files

### Output Location

Files are written to versioned directories:
```
data/metadata/v2025-12-15/
├── corapan_recordings.tsv
├── corapan_recordings.json
├── corapan_recordings.jsonld
├── corapan_corpus_metadata.json
├── corapan_corpus_metadata.jsonld
├── corapan_recordings_ARG.tsv
├── corapan_recordings_ARG.json
├── corapan_recordings_ESP.tsv
├── corapan_recordings_ESP.json
├── corapan_recordings_MEX.tsv
├── corapan_recordings_MEX.json
├── ... (one pair per country)
├── tei_headers.zip
└── tei/
    ├── corapan_ARG_2023-08-10_mitre.xml
    └── ...
```

A `latest` symlink/directory is created pointing to the most recent version.

### Usage

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run export with version and date
python LOKAL/metadata/export_metadata.py --corpus-version v1.0 --release-date 2025-12-15

# Short form
python LOKAL/metadata/export_metadata.py -v v1.0 -d 2025-12-15
```

### CLI Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--corpus-version`, `-v` | Yes | Version identifier (e.g., `v1.0`, `v1.1`) |
| `--release-date`, `-d` | Yes | Release date in `YYYY-MM-DD` format |

### Record Schema

Each recording is exported with these fields:

| Field | Description |
|-------|-------------|
| `corapan_id` | Unique identifier: `corapan:{country}:{date}:{radio_id}` |
| `file_id` | Original file identifier from JSON |
| `filename` | Original filename |
| `date` | Recording date (YYYY-MM-DD) |
| `country_code_alpha3` | ISO 3166-1 alpha-3 country code |
| `country_code_alpha2` | ISO 3166-1 alpha-2 country code |
| `country_name` | Full country name in Spanish |
| `city` | Recording city |
| `radio` | Radio station name |
| `radio_id` | Standardized radio station ID |
| `duration_seconds` | Duration in seconds |
| `duration_hms` | Duration as HH:MM:SS |
| `words_transcribed` | Total word count |
| `language` | Language code (es-XX) |
| `modality` | `spoken_broadcast` |
| `revision` | Revision code from transcription |
| `annotation_method` | Annotation pipeline description |
| `annotation_schema` | Schema version (e.g., `corapan-ann/v3`) |
| `annotation_tool` | Tools used for annotation |
| `annotation_access` | `restricted` |
| `access_rights_data` | `restricted` |
| `access_rights_metadata` | `open` |
| `rights_statement_data` | Rights statement for data |
| `rights_statement_metadata` | Rights statement for metadata (CC-BY 4.0) |
| `source_stream_type` | `online_stream_download` |
| `institution` | `Philipps-Universität Marburg` |
| `corpus_version` | Version from CLI argument |
| `created_at` | Export timestamp (UTC, ISO-8601) |

### Adding New Radio Stations

If the script encounters a radio station not in the mapping, it will:
1. Generate a slug-based ID automatically
2. Log a warning message

To add the proper mapping, edit the `RADIO_TO_ID` dictionary in `export_metadata.py`:

```python
RADIO_TO_ID: dict[str, str] = {
    "Radio Mitre": "mitre",
    "New Radio Station": "newstation",  # Add here
    ...
}
```

### Integration with Webapp

The webapp reads metadata from `data/metadata/latest/` for:

1. **Global downloads** (corpus_metadata.html):
   - Links to TSV, JSON, JSON-LD, and TEI ZIP files

2. **Country-specific downloads** (via API):
   - `/corpus/metadata/country/{code}.tsv`
   - `/corpus/metadata/country/{code}.json`

### Related Files

- `src/app/routes/corpus.py` - API endpoints for metadata downloads
- `templates/pages/corpus_metadata.html` - UI template
- `static/js/modules/corpus-metadata.js` - JavaScript module
- `static/css/md3/components/corpus-metadata.css` - Styles
