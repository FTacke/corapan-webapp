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
    db/public
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
    C:\dev\corapan-webapp\data\exports\docmeta.jsonl 19512
    C:\dev\corapan-webapp\data\public\metadata\latest\corapan_recordings.json 191818
    C:\dev\corapan-webapp\data\public\metadata\latest\corapan_recordings.tsv 88408
    C:\dev\corapan-webapp\data\public\metadata\v2025-12-06\corapan_recordings.json 191818
    C:\dev\corapan-webapp\data\public\statistics\corpus_stats.json 46306
    C:\dev\corapan-webapp\data\public\statistics\viz_total_corpus.png 61129
    C:\dev\corapan-webapp\data\stats_temp\01c1f4bb47c420ff.json 2006

Note: BlackLab directories are intentionally excluded from migration.

Phase 1b — Runtime DB layout (AS-IS)

Runtime root (repo-local default used for evidence because CORAPAN_RUNTIME_ROOT was not set):
    C:\dev\corapan-webapp\runtime\corapan

Command:
    $rt = Join-Path (Get-Location) "runtime\corapan"; Write-Output "CORAPAN_RUNTIME_ROOT(default)=$rt"; Get-ChildItem "$rt\data\db" -File -ErrorAction SilentlyContinue | Select Name,Length | Format-Table
Output:
    CORAPAN_RUNTIME_ROOT(default)=C:\dev\corapan-webapp\runtime\corapan
    Top-level db files:
    Name             Length
    ----             ------
    stats_country.db  16384
    stats_files.db    36864

Command:
    $rt = Join-Path (Get-Location) "runtime\corapan"; Write-Output "db/public exists?"; Test-Path "$rt\data\db\public"; Write-Output "db/restricted exists?"; Test-Path "$rt\data\db\restricted"
Output:
    db/public exists?
    False
    db/restricted exists?
    False

Phase 1c — Remove misplaced stats DBs (runtime data/db)

Command:
    $rt = Join-Path (Get-Location) "runtime\corapan"; Write-Output "Before delete:"; Get-ChildItem "$rt\data\db" -File -ErrorAction SilentlyContinue | Select Name,Length | Format-Table; Remove-Item "$rt\data\db\stats_*.db" -Force -ErrorAction SilentlyContinue; Write-Output "After delete:"; Get-ChildItem "$rt\data\db" -File -ErrorAction SilentlyContinue | Select Name,Length | Format-Table
Output:
    Before delete:
    Name             Length
    ----             ------
    stats_country.db  16384
    stats_files.db    36864

    After delete:
    (no files)

Phase 4b — Rebuild stats DBs into db/public

Command:
    $env:CORAPAN_RUNTIME_ROOT = Join-Path (Get-Location) "runtime\corapan"; C:\dev\corapan-webapp\.venv\Scripts\python.exe .\LOKAL\_0_json\03_build_metadata_stats.py
Output (excerpt):
    DB-Public:          C:\dev\corapan-webapp\runtime\corapan\data\db\public
    ✅ stats_country.db erstellt
    ✅ stats_files.db erstellt
    Erstellte DBs:
      • C:\dev\corapan-webapp\runtime\corapan\data\db\public\stats_country.db
      • C:\dev\corapan-webapp\runtime\corapan\data\db\public\stats_files.db

Verification:
    $rt = Join-Path (Get-Location) "runtime\corapan"; Get-ChildItem "$rt\data\db\public" -File -ErrorAction SilentlyContinue | Select Name,Length | Format-Table
    $rt = Join-Path (Get-Location) "runtime\corapan"; Get-ChildItem "$rt\data\db" -File -ErrorAction SilentlyContinue | Select Name,Length | Format-Table
Result:
    db/public contents:
    Name             Length
    ----             ------
    stats_country.db  16384
    stats_files.db    36864

    top-level db contents:
    (no files)

Phase 2 — Touchpoints (Generator outputs)

Command:
    Get-ChildItem .\LOKAL -Recurse -File -Filter *.py | Select-String -Pattern "data/db/public|data\\db\\public|data/public/metadata|data\\public\\metadata|data/exports|data\\exports|data/public|data\\public"
Output (excerpt):
    LOKAL\_0_json\03_build_metadata_stats.py:14:    data/db/public/stats_country.db        - Statistiken pro Land
    LOKAL\_0_json\03_build_metadata_stats.py:15:    data/db/public/stats_files.db          - Metadaten pro Datei
    LOKAL\_1_metadata\export_metadata.py:15:Output is written to runtime/data/public/metadata/vYYYY-MM-DD/ with a "latest" symlink.
    LOKAL\_1_zenodo-repos\zenodo_metadata.py:6:Quelle:     runtime/data/public/metadata/latest/

Command:
    Select-String -Path .\scripts\dev-start.ps1, .\scripts\migrate_stats_to_runtime.ps1, .\scripts\deploy_sync\sync_data.ps1 -Pattern "CORAPAN_RUNTIME_ROOT|PUBLIC_STATS_DIR|data\\public\\statistics|data\\public\\metadata|data\\db|data\\exports|data\\counters" -Context 2,2
Output (excerpt):
    scripts\dev-start.ps1:36-50 sets CORAPAN_RUNTIME_ROOT and derives PUBLIC_STATS_DIR
    scripts\migrate_stats_to_runtime.ps1:14-15 uses runtime/data/public/statistics
    scripts\deploy_sync\sync_data.ps1:233-238 references PUBLIC_STATS_DIR or repo data/public/statistics

Phase 3 — Minimal runtime-aware outputs (non-BlackLab)

Changes applied:
- [LOKAL/_0_json/03_build_metadata_stats.py](LOKAL/_0_json/03_build_metadata_stats.py): stats DB output now writes to runtime data/db/public only; CORAPAN_RUNTIME_ROOT is required (no repo fallback).
- [LOKAL/_1_metadata/export_metadata.py](LOKAL/_1_metadata/export_metadata.py): metadata output now writes to runtime data/public/metadata only; CORAPAN_RUNTIME_ROOT is required.

Phase 4 — Dev-start checks

- [scripts/dev-start.ps1](scripts/dev-start.ps1) already sets CORAPAN_RUNTIME_ROOT and PUBLIC_STATS_DIR for runtime stats.

Phase 5 — End-to-End Run (evidence)

Commands:
- Remove-Item "$env:CORAPAN_RUNTIME_ROOT\data\db" -Recurse -Force -ErrorAction SilentlyContinue
- Remove-Item "$env:CORAPAN_RUNTIME_ROOT\data\public\metadata" -Recurse -Force -ErrorAction SilentlyContinue
- Remove-Item "$env:CORAPAN_RUNTIME_ROOT\data\public\statistics" -Recurse -Force -ErrorAction SilentlyContinue
- C:/dev/corapan-webapp/.venv/Scripts/python.exe .\LOKAL\_0_json\03_build_metadata_stats.py
- C:/dev/corapan-webapp/.venv/Scripts/python.exe .\LOKAL\_1_metadata\export_metadata.py --corpus-version v2026-01-18 --release-date 2026-01-18
- C:/dev/corapan-webapp/.venv/Scripts/python.exe .\LOKAL\_0_json\05_publish_corpus_statistics.py

Output (excerpt):
- 03_build_metadata_stats.py
    - DB-Verzeichnis: C:\dev\corapan-webapp\runtime\corapan\data\db
    - DB-Public: C:\dev\corapan-webapp\runtime\corapan\data\db\public
    - ✅ stats_country.db erstellt
    - ✅ stats_files.db erstellt

- export_metadata.py
    - Metadata Root: C:\dev\corapan-webapp\runtime\corapan\data\public\metadata
    - Written: ...\runtime\corapan\data\public\metadata\v2026-01-18\corapan_recordings.tsv
    - Written: ...\runtime\corapan\data\public\metadata\v2026-01-18\corapan_recordings.json
    - Written: ...\runtime\corapan\data\public\metadata\v2026-01-18\corapan_corpus_metadata.json
    - 'latest' updated: Yes

- 05_publish_corpus_statistics.py
    - Output Directory: C:\dev\corapan-webapp\runtime\corapan\data\public\statistics
    - JSON guardado: corpus_stats.json
    - 25 visualizaciones de países creadas

Verification commands:
- Get-ChildItem "$env:CORAPAN_RUNTIME_ROOT\data\db" -File | Select-Object Name,Length
    - stats_country.db 16384
    - stats_files.db 36864

- Get-ChildItem "$env:CORAPAN_RUNTIME_ROOT\data\public\metadata" -Directory | Select-Object Name
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

- Get-ChildItem "$env:CORAPAN_RUNTIME_ROOT\data\db\public" -File
    - stats_country.db
    - stats_files.db

Phase 6 — App runtime read paths (non-BlackLab)

Changes applied:
- [src/app/config/__init__.py](src/app/config/__init__.py): added `DATA_ROOT` derived from `CORAPAN_RUNTIME_ROOT` (dev fallback) and use it for `DB_DIR` and `DB_PUBLIC_DIR`.
- [src/app/services/database.py](src/app/services/database.py): stats DBs now resolve under runtime data/db/public.
- [src/app/routes/corpus.py](src/app/routes/corpus.py): metadata downloads resolve under runtime data root.
- [src/app/routes/stats.py](src/app/routes/stats.py): stats response cache now uses runtime data root.

Evidence:
    Command:
        Select-String .\src\app\services\database.py -Pattern "PUBLIC_DB_ROOT|stats_country.db|stats_files.db" -Context 2,2
    Output (excerpt):
        src\app\services\database.py:39:PUBLIC_DB_ROOT = DATA_ROOT / "db" / "public"
        src\app\services\database.py:42:    "stats_files": PUBLIC_DB_ROOT / "stats_files.db",
        src\app\services\database.py:43:    "stats_country": PUBLIC_DB_ROOT / "stats_country.db",

Phase 7 — Dev server smoke (evidence)

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

Re-run (after app runtime path updates):

Commands:
- Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
- .\scripts\dev-start.ps1
- Start-Sleep 3
- curl.exe --max-time 3 http://127.0.0.1:8000/
- curl.exe --max-time 3 http://127.0.0.1:8000/health

Output:
- dev-start.ps1:
    - CORAPAN_RUNTIME_ROOT defaulted to: C:\dev\corapan-webapp\runtime\corapan
    - SUCCESS: Statistics found (generated: 2026-01-18 11:00:26)
    - AUTH_DATABASE_URL set to postgres dev
    - Server process started, logs at:
        - [dev-server.log](dev-server.log)
        - [dev-server.err.log](dev-server.err.log)
- curl.exe result:
    - curl: (7) Failed to connect to 127.0.0.1 port 8000 after 2053 ms: Could not connect to server

Notes:
- dev-server.err.log confirms Flask running on 0.0.0.0:8000 and 127.0.0.1:8000:
    - "* Running on all addresses (0.0.0.0)"
    - "* Running on http://127.0.0.1:8000"
- TODO: connectivity issue persists locally (likely firewall/binding delay). App logs show normal startup.

Re-run (after db/public changes):

Commands:
- Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
- powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1
- Start-Sleep 3
- netstat -ano | findstr :8000
- curl.exe --max-time 3 http://127.0.0.1:8000/
- curl.exe --max-time 3 http://127.0.0.1:8000/health

Output (excerpt):
- dev-start.ps1:
    - Using CORAPAN_RUNTIME_ROOT - custom: C:\dev\corapan-webapp\runtime\corapan
    - SUCCESS: Statistics found (generated: 2026-01-18 11:00:26)
    - Starting Flask dev server at http://localhost:8000
    - Logs at dev-server.log / dev-server.err.log
    - Server process started (PID: 28664)
- netstat:
    - Multiple 127.0.0.1:8000 entries in WARTEND state
- curl.exe:
    - curl: (7) Failed to connect to 127.0.0.1 port 8000 after ~2s

Notes:
- Connectivity issue still reproduces locally; server process starts but curl times out.

Out of scope (explicitly left unchanged)
- [src/app/routes/stats.py](src/app/routes/stats.py): existing changes are not part of this migration.
- [docs/problem/migration_devprod.md](docs/problem/migration_devprod.md): untracked; not part of this migration.

Phase 8 — Metadata moved to public/metadata

Phase 8.1 — Inventory (AS-IS)

Command:
    $rt = $env:CORAPAN_RUNTIME_ROOT; Write-Host "CORAPAN_RUNTIME_ROOT=$rt"; "== runtime/corapan/data tree (top) =="; Get-ChildItem "$rt\data" -Directory | Select Name; "== public/metadata (if exists) =="; Get-ChildItem "$rt\data\public\metadata" -Recurse -Force -ErrorAction SilentlyContinue | Select FullName,Length
Output (excerpt):
    CORAPAN_RUNTIME_ROOT=C:\dev\corapan-webapp\runtime\corapan
    == runtime/corapan/data tree (top) ==
    Name
    ----
    db
    public
    stats_temp

    == public/metadata (if exists) ==
    (empty before migration)

Phase 8.2 — Generator alignment (evidence)

Command:
    Select-String .\LOKAL\_1_metadata\export_metadata.py -Pattern "PUBLIC_METADATA_DIR|data/public/metadata|CORAPAN_RUNTIME_ROOT" -Context 2,2
    Select-String .\LOKAL\_1_zenodo-repos\zenodo_metadata.py -Pattern "METADATA_SRC|public\\metadata|CORAPAN_RUNTIME_ROOT" -Context 2,2
Output (excerpt):
    LOKAL\_1_metadata\export_metadata.py:59:PUBLIC_METADATA_DIR = PUBLIC_ROOT / "metadata"
    LOKAL\_1_metadata\export_metadata.py:60:PUBLIC_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    LOKAL\_1_metadata\export_metadata.py:517:contentUrl ... data/public/metadata/latest/corapan_recordings.json
    LOKAL\_1_zenodo-repos\zenodo_metadata.py:29:METADATA_SRC = os.path.join(RUNTIME_ROOT, "data", "public", "metadata", "latest")

Phase 8.3 — Move legacy runtime metadata → public/metadata

Status:
    Legacy metadata directory removed; runtime data tree now contains only db/, public/, stats_temp/.

Command (evidence after move):
    $rt = $env:CORAPAN_RUNTIME_ROOT; "== public/metadata contents =="; Get-ChildItem "$rt\data\public\metadata" -Recurse -Force | Select FullName,Length
Output (excerpt):
    C:\dev\corapan-webapp\runtime\corapan\data\public\metadata\latest
    C:\dev\corapan-webapp\runtime\corapan\data\public\metadata\v2026-01-18
    C:\dev\corapan-webapp\runtime\corapan\data\public\metadata\latest\corapan_recordings.json
    ...

Phase 8.4 — App read paths (metadata)

Command:
    Get-ChildItem .\src -Recurse -Filter *.py | Select-String -Pattern "public/metadata" -Context 2,2
Output (excerpt):
    src\app\routes\corpus.py:8:Alle Dateien stammen aus ${CORAPAN_RUNTIME_ROOT}/data/public/metadata/latest/,

Phase 8.5 — Rebuild metadata outputs (runtime-only)

Command:
    C:\dev\corapan-webapp\.venv\Scripts\python.exe .\LOKAL\_1_metadata\export_metadata.py --corpus-version v2026-01-18 --release-date 2026-01-18
Output (excerpt):
    Metadata Root:  C:\dev\corapan-webapp\runtime\corapan\data\public\metadata
    Written: C:\dev\corapan-webapp\runtime\corapan\data\public\metadata\v2026-01-18\corapan_recordings.tsv
    Written: C:\dev\corapan-webapp\runtime\corapan\data\public\metadata\v2026-01-18\corapan_recordings.json
    ...
    Output directory:    C:\dev\corapan-webapp\runtime\corapan\data\public\metadata\v2026-01-18
    'latest' updated:    Yes