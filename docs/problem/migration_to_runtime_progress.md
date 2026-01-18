# Migration to Runtime Progress Log

Status: In progress
Owner: TBD
Last updated: 2026-01-18

Scope
- Make non-BlackLab generated artifacts write to runtime when `CORAPAN_RUNTIME_ROOT` is set.
- BlackLab is explicitly out of scope.

Phase 1 — Inventory (AS-IS)

Command:
    Get-ChildItem .\data -Directory | Select-Object Name
Output:
    Name
    ----
    blacklab_export
    blacklab_index
    blacklab_index.backup
    blacklab_index.backup_20260114_232911
    blacklab_index.bad_20260117_000048
    blacklab_index.new.bad_20260117_000404
    blacklab_index.testbuild
    blacklab_index.testbuild.bak_20260117_005855
    counters
    db
    db_public
    exports
    metadata
    public
    stats_temp

Command:
    Get-ChildItem .\data -Recurse -Depth 2 -File | Select-Object FullName,Length | Sort-Object FullName
Output (excerpt, non-BlackLab):
    C:\dev\corapan-webapp\data\counters\auth_login_failure.json 125
    C:\dev\corapan-webapp\data\counters\auth_login_success.json 129
    C:\dev\corapan-webapp\data\counters\counter_access.json 110
    C:\dev\corapan-webapp\data\counters\counter_search.json 20
    C:\dev\corapan-webapp\data\counters\counter_visits.json 130
    C:\dev\corapan-webapp\data\db\auth.db 94208
    C:\dev\corapan-webapp\data\db\auth_e2e.db 36864
    C:\dev\corapan-webapp\data\db\stats_country.db 16384
    C:\dev\corapan-webapp\data\db\stats_files.db 40960
    C:\dev\corapan-webapp\data\db_public\stats_all.db 8192
    C:\dev\corapan-webapp\data\exports\docmeta.jsonl 19512
    C:\dev\corapan-webapp\data\metadata\latest\corapan_recordings.json 191818
    C:\dev\corapan-webapp\data\metadata\latest\corapan_recordings.tsv 88408
    C:\dev\corapan-webapp\data\metadata\v2025-12-06\corapan_recordings.json 191818
    C:\dev\corapan-webapp\data\public\statistics\corpus_stats.json 46306
    C:\dev\corapan-webapp\data\public\statistics\viz_total_corpus.png 61129
    C:\dev\corapan-webapp\data\stats_temp\01c1f4bb47c420ff.json 2006

Note: BlackLab directories are intentionally excluded from migration.

Phase 2 — Touchpoints (Generator outputs)

Command:
    Get-ChildItem .\LOKAL -Recurse -File -Filter *.py | Select-String -Pattern "data/db|data\\db|data/metadata|data\\metadata|data/exports|data\\exports|data/db_public|data\\db_public|data/public|data\\public"
Output (excerpt):
    LOKAL\_0_json\03_build_metadata_stats.py:14:    data/db/stats_country.db        - Statistiken pro Land
    LOKAL\_0_json\03_build_metadata_stats.py:15:    data/db/stats_files.db          - Metadaten pro Datei
    LOKAL\_0_json\03_build_metadata_stats.py:520:  data/db_public/stats_all.db     - Globale Statistiken
    LOKAL\_1_metadata\export_metadata.py:15:Output is written to data/metadata/vYYYY-MM-DD/ with a "latest" symlink.
    LOKAL\_1_zenodo-repos\zenodo_metadata.py:6:Quelle:     data/metadata/latest/

Command:
    Select-String -Path .\scripts\dev-start.ps1, .\scripts\migrate_stats_to_runtime.ps1, .\scripts\deploy_sync\sync_data.ps1 -Pattern "CORAPAN_RUNTIME_ROOT|PUBLIC_STATS_DIR|data\\public\\statistics|data\\db|data\\metadata|data\\exports|data\\db_public|data\\counters" -Context 2,2
Output (excerpt):
    scripts\dev-start.ps1:36-50 sets CORAPAN_RUNTIME_ROOT and derives PUBLIC_STATS_DIR
    scripts\migrate_stats_to_runtime.ps1:14-15 uses runtime/data/public/statistics
    scripts\deploy_sync\sync_data.ps1:233-238 references PUBLIC_STATS_DIR or repo data/public/statistics

Phase 3 — Minimal runtime-aware outputs (non-BlackLab)

Changes applied:
- [LOKAL/_0_json/03_build_metadata_stats.py](LOKAL/_0_json/03_build_metadata_stats.py): DB output now uses runtime data root when CORAPAN_RUNTIME_ROOT is set.
- [LOKAL/_1_metadata/export_metadata.py](LOKAL/_1_metadata/export_metadata.py): Metadata output now uses runtime data root when CORAPAN_RUNTIME_ROOT is set.

Phase 4 — Dev-start checks

- [scripts/dev-start.ps1](scripts/dev-start.ps1) already sets CORAPAN_RUNTIME_ROOT and PUBLIC_STATS_DIR for runtime stats.

Phase 5 — End-to-End Run (evidence)

Commands:
- Remove-Item "$env:CORAPAN_RUNTIME_ROOT\data\db" -Recurse -Force -ErrorAction SilentlyContinue
- Remove-Item "$env:CORAPAN_RUNTIME_ROOT\data\metadata" -Recurse -Force -ErrorAction SilentlyContinue
- Remove-Item "$env:CORAPAN_RUNTIME_ROOT\data\public\statistics" -Recurse -Force -ErrorAction SilentlyContinue
- C:/dev/corapan-webapp/.venv/Scripts/python.exe .\LOKAL\_0_json\03_build_metadata_stats.py
- C:/dev/corapan-webapp/.venv/Scripts/python.exe .\LOKAL\_1_metadata\export_metadata.py --corpus-version v2026-01-18 --release-date 2026-01-18
- C:/dev/corapan-webapp/.venv/Scripts/python.exe .\LOKAL\_0_json\05_publish_corpus_statistics.py

Output (excerpt):
- 03_build_metadata_stats.py
    - DB-Verzeichnis: C:\dev\corapan-webapp\runtime\corapan\data\db
    - DB-Public: C:\dev\corapan-webapp\runtime\corapan\data\db_public
    - ✅ stats_country.db erstellt
    - ✅ stats_files.db erstellt

- export_metadata.py
    - Metadata Root: C:\dev\corapan-webapp\runtime\corapan\data\metadata
    - Written: ...\runtime\corapan\data\metadata\v2026-01-18\corapan_recordings.tsv
    - Written: ...\runtime\corapan\data\metadata\v2026-01-18\corapan_recordings.json
    - Written: ...\runtime\corapan\data\metadata\v2026-01-18\corapan_corpus_metadata.json
    - 'latest' updated: Yes

- 05_publish_corpus_statistics.py
    - Output Directory: C:\dev\corapan-webapp\runtime\corapan\data\public\statistics
    - JSON guardado: corpus_stats.json
    - 25 visualizaciones de países creadas

Verification commands:
- Get-ChildItem "$env:CORAPAN_RUNTIME_ROOT\data\db" -File | Select-Object Name,Length
    - stats_country.db 16384
    - stats_files.db 36864

- Get-ChildItem "$env:CORAPAN_RUNTIME_ROOT\data\metadata" -Directory | Select-Object Name
    - latest
    - v2026-01-18

- Get-ChildItem "$env:CORAPAN_RUNTIME_ROOT\data\public\statistics" -File | Select-Object Name
    - corpus_stats.json
    - viz_ARG-CBA_resumen.png
    - viz_ARG-CHU_resumen.png
    - viz_ARG-SDE_resumen.png
    - viz_ARG_resumen.png
    - viz_BOL_resumen.png
    - viz_CHL_resumen.png
    - viz_COL_resumen.png
    - viz_CRI_resumen.png
    - viz_CUB_resumen.png
    - viz_DOM_resumen.png
    - viz_ECU_resumen.png
    - viz_ESP-CAN_resumen.png
    - viz_ESP-SEV_resumen.png
    - viz_ESP_resumen.png
    - viz_genero_profesionales.png
    - viz_GTM_resumen.png
    - viz_HND_resumen.png
    - viz_MEX_resumen.png
    - viz_modo_genero_profesionales.png
    - viz_NIC_resumen.png
    - viz_PAN_resumen.png
    - viz_PER_resumen.png
    - viz_PRY_resumen.png
    - viz_SLV_resumen.png
    - viz_total_corpus.png
    - viz_URY_resumen.png
    - viz_USA_resumen.png
    - viz_VEN_resumen.png

- Get-ChildItem "$env:CORAPAN_RUNTIME_ROOT\data\db_public" -File
    - (no output; stats_all.db is deprecated and not generated)

Phase 6 — Dev server smoke (evidence)

Commands:
- Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
- powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1
- Start-Sleep 3
- curl.exe --max-time 3 http://127.0.0.1:8000/
- curl.exe --max-time 3 http://127.0.0.1:8000/health

Output:
- dev-start.ps1 reported server start and logs at:
    - [dev-server.log](dev-server.log)
    - [dev-server.err.log](dev-server.err.log)

- curl.exe result:
    - curl: (7) Failed to connect to 127.0.0.1 port 8000 after 2030 ms: Could not connect to server

Notes:
- dev-server.err.log shows Flask running on http://127.0.0.1:8000:
    - "* Running on http://127.0.0.1:8000"
- TODO: investigate local connectivity issue (firewall or binding delay) if needed.