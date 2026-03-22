# Welle 3 Summary

Datum: 2026-03-20
Umgebung: Development lokal
Scope: zentrale Resolver, Pfadauflosung im App-Code, Debug-Logging, Legacy-Klassifikation fuer verbleibende BlackLab-Pfade

## 8.1 Zusammenfassung

Vereinheitlicht wurden die zentralen Resolver in `src/app/runtime_paths.py`.

Die kanonischen Getter sind jetzt:

- `get_runtime_root()`
- `get_data_root()`
- `get_media_root()`
- `get_config_root()`
- `get_stats_dir()`
- `get_stats_temp_dir()`
- `get_metadata_dir()`
- zusaetzlich fuer abgeleitete Pfade: `get_logs_dir()`, `get_docmeta_path()`, `get_audio_full_dir()`, `get_audio_split_dir()`, `get_audio_temp_dir()`, `get_transcripts_dir()`

Diese Getter sind jetzt die zentrale Quelle fuer die kanonische Struktur:

- `C:\dev\corapan\data`
- `C:\dev\corapan\media`
- `C:\dev\corapan\config`
- `C:\dev\corapan\data\public\metadata\latest`
- `C:\dev\corapan\data\public\statistics`

Im App-Code wurden die letzten moduleigenen Pfadableitungen fuer Metadata, Statistics, SQLite-Seitendatenbanken, Audio/Transcript-Unterordner und docmeta auf diese Getter umgestellt.

## 8.2 Entfernte Inkonsistenzen

Vor Welle 3 gab es noch diese impliziten oder konkurrierenden Pfadquellen:

- `corpus.py` leitete Metadaten indirekt aus `DATA_ROOT` plus relativen Segmenten her und bevorzugte dabei mehrere moegliche Metadata-Orte
- `corpus.py` griff fuer Statistics direkt auf `current_app.config["PUBLIC_STATS_DIR"]` zu
- `atlas.py` hatte eine separate Metadata-Logik mit `latest/tei -> latest`
- `advanced_api.py` nutzte ein importzeitlich gebundenes `DATA_ROOT` aus `services.database`
- `services.database.py` und `routes.stats.py` hielten eigene abgeleitete Runtime-Konstanten
- `__init__.py` schrieb Logs noch relativ unter das Repo statt ueber den zentralen Runtime-Kontext

Nach Welle 3 gilt:

- Metadata wird deterministisch ueber `get_metadata_dir()` auf `data/public/metadata/latest` aufgeloest
- Statistics werden deterministisch ueber `get_stats_dir()` und `get_stats_temp_dir()` aufgeloest
- docmeta wird deterministisch ueber `get_docmeta_path()` aufgeloest
- die SQLite-Seitendatenbanken lesen ihre Basis ausschliesslich ueber `get_data_root()`
- die App-Logs nutzen den zentralen Runtime-Logpfad `get_logs_dir()`

## Vorher/Nachher

| Bereich | Vorher | Nachher |
|--------|--------|---------|
| Runtime-Resolver | `resolve_*` plus moduleigene Ableitungen | zentraler `get_*`-Resolver-Satz als einzige kanonische Quelle |
| Metadata | `DATA_ROOT` + relative Segmente, Atlas-Sonderlogik | `get_metadata_dir()` -> `data/public/metadata/latest` |
| Statistics | direkte Config-Zugriffe und lokale Cache-Konstanten | `get_stats_dir()` und `get_stats_temp_dir()` |
| docmeta | importzeitlich gebundenes `DATA_ROOT` | `get_docmeta_path()` |
| Media-Unterpfade | teils Config-Fallback, teils lokale Ableitung | zentrale Media-Unterpfad-Getter |
| Logging | repo-relativer Logpfad im App-Setup | zentraler Runtime-Logpfad |

## 8.3 Verbleibende Legacy-Zugriffe

Verbleibende repo-lokale Pfade wurden nicht entfernt, sondern explizit als `ACTIVE_LEGACY` markiert, weil sie BlackLab betreffen und ausserhalb des Scopes dieser Welle liegen:

- `docker-compose.dev-postgres.yml`
  - `./data/blacklab_index:/data/index/corapan:ro`
  - `./config/blacklab:/etc/blacklab:ro`
- `src/scripts/blacklab_index_creation.py`
  - `media/transcripts`
  - `data/blacklab_export/tsv`
  - `data/blacklab_export/docmeta.jsonl`

Es verbleiben damit in Welle 3 nur noch BlackLab-bezogene repo-lokale Legacy-Zugriffe.

## 8.4 Risiken

- Die BlackLab-Container- und Exportpfade sind bewusst noch nicht vereinheitlicht; sie bleiben `ACTIVE_LEGACY` bis zu einer separaten BlackLab-Welle.
- Template- und Static-Pfade bleiben weiterhin code-root-bezogen, nicht runtime-root-bezogen. Das ist fuer diese Welle akzeptiert, weil sie keine operative Datenstruktur darstellen.
- `CONFIG_ROOT` wird nun zentral aufgeloest und geloggt, wird aber von der Web-App selbst weiterhin kaum genutzt; die aktive Dev-BlackLab-Konfiguration bleibt repo-lokal und bewusst ausserhalb des App-Resolvers.

## 7. Verifikation

Automatisierte Regression:

- `pytest tests/test_runtime_paths.py tests/test_corpus_paths.py tests/test_media_routes.py tests/test_atlas_files_endpoint.py tests/test_advanced_api_enrichment.py tests/test_advanced_api_docmeta_mapping.py tests/test_advanced_api_stats_csv.py tests/test_advanced_api_stats_json.py -q`
- Ergebnis: `15 passed`

Verifikation gegen die aktuelle App-Fabrik mit explizitem kanonischem Dev-Env:

- `/media/full/2023-08-10_ARG_Mitre.mp3` -> `200`
  - belegter Pfad: `C:\dev\corapan\media\mp3-full\ARG\2023-08-10_ARG_Mitre.mp3`
- `/media/transcripts/2023-08-10_ARG_Mitre.json` -> `200`
  - belegter Pfad: `C:\dev\corapan\media\transcripts\ARG\2023-08-10_ARG_Mitre.json`
- `/api/v1/atlas/files` -> `200`
  - belegter Pfad: `C:\dev\corapan\data\public\metadata\latest`
- `/corpus/metadata` -> `200`
  - die Seite selbst ist statisch; die zugehoerigen Download-Pfade verwenden denselben zentralen Metadata-Resolver
- `/corpus/metadata/download/json` -> `200`
  - belegter Pfad: `C:\dev\corapan\data\public\metadata\latest\corapan_recordings.json`
- `/corpus/api/statistics/corpus_stats.json` -> `200`
  - belegter Pfad: `C:\dev\corapan\data\public\statistics\corpus_stats.json`
- `/search/advanced/data?q=casa&mode=lemma&draw=1&start=0&length=1` -> `200`
  - BLS-Beleg: `BLS GET /corpora/corapan/hits: 200`
  - docmeta-Beleg: `C:\dev\corapan\data\blacklab_export\docmeta.jsonl` (`exists=True`, `146` Eintraege)

Initialisierungs-Logging belegt ausserdem die zentralen Resolverwerte:

- `DATA_ROOT=c:\dev\corapan\data`
- `MEDIA_ROOT=c:\dev\corapan\media`
- `CONFIG_ROOT=c:\dev\corapan\config`
- `METADATA_DIR=c:\dev\corapan\data\public\metadata\latest`
- `STATS_DIR=c:\dev\corapan\data\public\statistics`

## Lessons Learned – Run 2026-03-20

- Problem:
  Nach Welle 2 waren die kanonischen Dev-Pfade zwar weitgehend aktiv, aber einzelne Module hielten noch eigene Pfadableitungen oder importzeitlich gebundene Konstanten.
- Ursache:
  Der Resolver war noch kein vollstaendiger Single Point of Truth; Metadata-, Statistics-, docmeta- und Log-Pfade wurden teilweise ausserhalb des zentralen Runtime-Moduls zusammengesetzt.
- Fix:
  Ein zentraler `get_*`-Resolver-Satz wurde eingefuehrt und die verbliebenen App-Call-Sites darauf umgestellt. Verbleibende repo-lokale BlackLab-Pfade wurden explizit als `ACTIVE_LEGACY` markiert statt verdeckt bestehen zu bleiben.
- Regel:
  Resolver duerfen nie implizite Strukturannahmen enthalten. Jeder operative Datenpfad muss ueber einen zentralen Resolver laufen oder explizit als `ACTIVE_LEGACY` klassifiziert sein.