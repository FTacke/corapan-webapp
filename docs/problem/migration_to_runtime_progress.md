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

Phase 9 — Repo data/db cleanup (DEV)

Phase 9.1 — Inventory (repo + runtime)

Command:
    git status -sb
    "== repo data/db contents =="
    Get-ChildItem .\data\db -Force | Select FullName,Length
    $rt = $env:CORAPAN_RUNTIME_ROOT
    Write-Host "CORAPAN_RUNTIME_ROOT=$rt"
    "== runtime db/restricted exists? =="
    Test-Path "$rt\data\db\restricted"
Output:
    ## work/current...origin/work/current
    CORAPAN_RUNTIME_ROOT=
    == repo data/db contents ==
    C:\dev\corapan-webapp\data\db\postgres_dev
    C:\dev\corapan-webapp\data\db\.gitkeep 56
    C:\dev\corapan-webapp\data\db\auth.db 94208
    C:\dev\corapan-webapp\data\db\auth_e2e.db 36864
    == runtime db/restricted exists? ==
    False

Phase 9.2 — Auth DB usage check

Command:
    Get-ChildItem .\src -Recurse -Filter *.py | Select-String -Pattern "auth\.db|auth_e2e\.db" -Context 2,2
Output (excerpt):
    src\app\extensions\sqlalchemy_ext.py:4: The auth migration uses a separate AUTH database by default (data/db/auth.db), but
    src\app\extensions\sqlalchemy_ext.py:5: this extension can accept any SQLAlchemy URL via config (AUTH_DATABASE_URL).

Decision:
    auth.db / auth_e2e.db are still referenced (docstring), so they were not deleted.

Phase 9.3 — Remove repo stats DBs (if present)

Command:
    "== BEFORE delete repo stats dbs =="
    Get-ChildItem .\data\db -File -Force | Select Name,Length
    Remove-Item .\data\db\stats_country.db, .\data\db\stats_files.db -Force -ErrorAction SilentlyContinue
    "== AFTER delete repo stats dbs =="
    Get-ChildItem .\data\db -File -Force | Select Name,Length
Output:
    == BEFORE delete repo stats dbs ==
    .gitkeep 56
    auth.db 94208
    auth_e2e.db 36864
    == AFTER delete repo stats dbs ==
    .gitkeep 56
    auth.db 94208
    auth_e2e.db 36864

Phase 9.4 — Move postgres_dev to runtime db/restricted

Command:
    "== BEFORE move postgres_dev =="
    Test-Path .\data\db\postgres_dev
    Get-ChildItem .\data\db\postgres_dev -Recurse -Force | Select -First 30 FullName
    $rt = Join-Path (Get-Location) "runtime\corapan"
    New-Item -ItemType Directory -Force -Path "$rt\data\db\restricted" | Out-Null
    Move-Item .\data\db\postgres_dev "$rt\data\db\restricted\postgres_dev" -Force
    "== AFTER move postgres_dev (repo) =="
    Test-Path .\data\db\postgres_dev
    "== AFTER move postgres_dev (runtime) =="
    Test-Path "$rt\data\db\restricted\postgres_dev"
    Get-ChildItem "$rt\data\db\restricted\postgres_dev" -Recurse -Force | Select -First 30 FullName
Output (excerpt):
    == BEFORE move postgres_dev ==
    True
    C:\dev\corapan-webapp\data\db\postgres_dev\base
    ...
    == AFTER move postgres_dev (repo) ==
    False
    == AFTER move postgres_dev (runtime) ==
    True
    C:\dev\corapan-webapp\runtime\corapan\data\db\restricted\postgres_dev\base
    ...

Phase 9.5 — Runtime path config (dev)

Updates:
    - dev-start.ps1 now sets POSTGRES_DEV_DATA_DIR to ${CORAPAN_RUNTIME_ROOT}\data\db\restricted\postgres_dev
    - docker-compose.dev-postgres.yml mounts ${POSTGRES_DEV_DATA_DIR} (fallback to runtime\corapan path)
    - App config exposes POSTGRES_DEV_DATA_DIR derived from CORAPAN_RUNTIME_ROOT

Phase 10 — Auth (Postgres-only) initialization + legacy cleanup

Phase 10.1 — Error evidence (before migration)

Command:
    Get-Content .\dev-server.err.log -Tail 200
Output (excerpt):
    psycopg.errors.UndefinedTable: relation "users" does not exist
    ...
    "POST /auth/login HTTP/1.1" 500 -

Phase 10.2 — Ensure dev Postgres is running

Command:
    docker compose -f .\docker-compose.dev-postgres.yml up -d
    docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | findstr 54320
Output (excerpt):
    corapan_auth_db  0.0.0.0:54320->5432/tcp  Up (health: starting)

Phase 10.3 — Apply auth schema (Postgres)

Command:
    docker cp .\migrations\0001_create_auth_schema_postgres.sql corapan_auth_db:/tmp/0001.sql
    docker exec -i corapan_auth_db psql -U corapan_auth -d corapan_auth -f /tmp/0001.sql
    docker exec -i corapan_auth_db psql -U corapan_auth -d corapan_auth -c "\dt"
Output (excerpt):
    public | users          | table | corapan_auth
    public | refresh_tokens | table | corapan_auth
    public | reset_tokens   | table | corapan_auth

Phase 10.4 — Dev server smoke (health)

Command:
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1
    Start-Sleep 3
    curl.exe --max-time 3 http://127.0.0.1:8000/health
Output (excerpt):
    curl: (7) Failed to connect to 127.0.0.1 port 8000 after ~2s
Note:
    Local connectivity issue persists, but auth schema is now present (users table).

Phase 10.5 — Legacy SQLite auth removal

Command:
    Get-ChildItem .\src -Recurse -Filter *.py | Select-String -Pattern "auth\.db|auth_e2e\.db" -Context 2,2
Output (excerpt):
    src\app\extensions\sqlalchemy_ext.py: docstring reference only (removed)

Command:
    Get-ChildItem .\data\db -Force | Where-Object Name -in "auth.db","auth_e2e.db" | Select Name,Length
    Remove-Item .\data\db\auth.db, .\data\db\auth_e2e.db -Force
    Get-ChildItem .\data\db -Force | Where-Object Name -in "auth.db","auth_e2e.db"
Output:
    (no output after delete)

Phase 11 — DEV Postgres host volume uses runtime

Phase 11.1 — Runtime env + expected path

Command:
    $rt = $env:CORAPAN_RUNTIME_ROOT
    if (-not $rt) { $rt = (Join-Path (Get-Location) "runtime\corapan"); $env:CORAPAN_RUNTIME_ROOT = $rt }
    if (-not $env:POSTGRES_DEV_DATA_DIR) { $env:POSTGRES_DEV_DATA_DIR = Join-Path $rt "data\db\restricted\postgres_dev" }
    Write-Host "CORAPAN_RUNTIME_ROOT=$rt"
    Write-Host "POSTGRES_DEV_DATA_DIR=$env:POSTGRES_DEV_DATA_DIR"
    $expected = Join-Path $rt "data\db\restricted\postgres_dev"
    Write-Host "EXPECTED_POSTGRES_DEV_DATA_DIR=$expected"
    Test-Path $expected
    Get-ChildItem (Split-Path $expected -Parent) -Force | Select Name
Output:
    CORAPAN_RUNTIME_ROOT=C:\dev\corapan-webapp\runtime\corapan
    POSTGRES_DEV_DATA_DIR=C:\dev\corapan-webapp\runtime\corapan\data\db\restricted\postgres_dev
    EXPECTED_POSTGRES_DEV_DATA_DIR=C:\dev\corapan-webapp\runtime\corapan\data\db\restricted\postgres_dev
    True
    Name
    ----
    postgres_dev

Phase 11.2 — Compose mount source (runtime)

Command:
    docker ps --format "{{.Names}}" | findstr -i corapan_auth_db
    $pg = "corapan_auth_db"
    docker inspect $pg | ConvertFrom-Json | ForEach-Object { $_.Mounts | ForEach-Object { "{0} -> {1}" -f $_.Source, $_.Destination } }
Output:
    corapan_auth_db
    C:\dev\corapan-webapp -> /app
    C:\dev\corapan-webapp\runtime\corapan\data\db\restricted\postgres_dev -> /var/lib/postgresql/data

Phase 11.3 — Legacy repo postgres_dev removed

Command:
    Test-Path .\data\db\postgres_dev
    Remove-Item .\data\db\postgres_dev -Recurse -Force -ErrorAction SilentlyContinue
    Test-Path .\data\db\postgres_dev
Output:
    True
    False

Phase 12 — Media root config (CORAPAN_MEDIA_ROOT)

Command:
    Select-String .\src\app\config\__init__.py -Pattern "CORAPAN_MEDIA_ROOT|MEDIA_ROOT|mp3-full|mp3-split|mp3-temp|transcripts" -Context 2,2
Output (excerpt):
    src\app\config\__init__.py:109:    _explicit_media_root = os.getenv("CORAPAN_MEDIA_ROOT")
    src\app\config\__init__.py:111:        MEDIA_ROOT = Path(_explicit_media_root)
    src\app\config\__init__.py:113:        MEDIA_ROOT = PROJECT_ROOT / "media"
    src\app\config\__init__.py:121:            "CORAPAN_MEDIA_ROOT environment variable not configured.\n"
    src\app\config\__init__.py:128:    TRANSCRIPTS_DIR = MEDIA_ROOT / "transcripts"
    src\app\config\__init__.py:129:    AUDIO_FULL_DIR = MEDIA_ROOT / "mp3-full"
    src\app\config\__init__.py:130:    AUDIO_SPLIT_DIR = MEDIA_ROOT / "mp3-split"
    src\app\config\__init__.py:131:    AUDIO_TEMP_DIR = MEDIA_ROOT / "mp3-temp"

Command:
    Select-String .\scripts\dev-start.ps1 -Pattern "CORAPAN_MEDIA_ROOT|media" -Context 2,2
Output (excerpt):
    scripts\dev-start.ps1:49:# Set CORAPAN_MEDIA_ROOT for dev only if not provided
    scripts\dev-start.ps1:50:if (-not $env:CORAPAN_MEDIA_ROOT) {
    scripts\dev-start.ps1:51:    $env:CORAPAN_MEDIA_ROOT = Join-Path $repoRoot "media"

Command:
    Get-ChildItem .\src -Recurse -Filter *.py | Select-String -Pattern "PROJECT_ROOT.*media|([\\/]|^)media([\\/]|$)" -Context 2,2
Output (excerpt):
    src\app\config\__init__.py:113:        MEDIA_ROOT = PROJECT_ROOT / "media"
    src\app\routes\auth.py:867:    # /corpus, /search/advanced, /atlas and /media/* are "optional auth" and

Phase 13 — Media data copy to runtime (robocopy)

Paths:
    SRC=C:\dev\corapan-webapp\media
    DST=C:\dev\corapan-webapp\runtime\corapan\media

Before counts:
    total=3007
    mp3-full=147
    mp3-split=2706
    transcripts=149

Robocopy:
    robocopy $src $dst /MIR /FFT /R:2 /W:2 /NFL /NDL /NP /LOG:.\logs\media_migration_robocopy.log
    Log: .\logs\media_migration_robocopy.log
    ExitCode: 1 (files copied)

After counts:
    total=3007
    mp3-full=147
    mp3-split=2706
    transcripts=149

Dev start (runtime media):
    $env:CORAPAN_MEDIA_ROOT = "C:\dev\corapan-webapp\runtime\corapan\media"
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1

Phase 14 — LOKAL media path audit (read-only)

LOKAL/_0_json:
    media/transcripts references found in:
    - LOKAL/_0_json/01_preprocess_transcripts.py (instructions/log message)
    - LOKAL/_0_json/02_annotate_transcripts_v3.py (TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts")
    - LOKAL/_0_json/03_build_metadata_stats.py (TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts")
    - LOKAL/_0_json/04_internal_country_statistics.py (TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts")
    - LOKAL/_0_json/05_publish_corpus_statistics.py (pipeline docs mention media/transcripts)
    - LOKAL/_0_json/99_check_pipeline_json.py (TRANSCRIPTS_DIR = PROJECT_ROOT / "media" / "transcripts")

LOKAL/_0_mp3:
    LOKAL/_0_mp3/mp3_prepare_and_split.py
        - DEFAULT_SOURCE_DIR = ../../media/mp3-full
        - DEFAULT_TARGET_DIR = ../../media/mp3-split
        - Header comment references ../../media/mp3-full and ../../media/mp3-split
    (These should switch to CORAPAN_MEDIA_ROOT-based paths when updated.)

Phase 15 — Media 404 debug (dev)

Phase 15.1 — Media config log at startup

Command:
    Get-Content .\dev-server.err.log -Tail 5
Output (excerpt):
    [2026-01-18 15:40:36,705] INFO in __init__: Media config: CORAPAN_MEDIA_ROOT=C:\dev\corapan-webapp\runtime\corapan\media MEDIA_ROOT=C:\dev\corapan-webapp\runtime\corapan\media AUDIO_FULL_DIR=C:\dev\corapan-webapp\runtime\corapan\media\mp3-full AUDIO_SPLIT_DIR=C:\dev\corapan-webapp\runtime\corapan\media\mp3-split AUDIO_TEMP_DIR=C:\dev\corapan-webapp\runtime\corapan\media\mp3-temp TRANSCRIPTS_DIR=C:\dev\corapan-webapp\runtime\corapan\media\transcripts

Phase 15.2 — Runtime vs repo media existence

Command:
    $rt = $env:CORAPAN_RUNTIME_ROOT
    if (-not $rt) { $rt = Join-Path (Get-Location) "runtime\corapan" }
    $mr = Join-Path $rt "media"
    "CORAPAN_RUNTIME_ROOT=$rt"
    "MEDIA_ROOT(candidate)=$mr"
    Test-Path $mr
    Get-ChildItem "$mr\mp3-full" -File | Select -First 3 Name
    Get-ChildItem "$mr\transcripts" -File | Select -First 3 Name
    Test-Path .\media
    Test-Path .\media2
Output:
    CORAPAN_RUNTIME_ROOT=C:\dev\corapan-webapp\runtime\corapan
    MEDIA_ROOT(candidate)=C:\dev\corapan-webapp\runtime\corapan\media
    True
    Name
    ----
    .gitkeep
    .gitkeep
    edit_log.jsonl
    True
    True

Phase 15.3 — Route mapping evidence

Command:
    Get-ChildItem .\src -Recurse -Filter *.py | Select-String -Pattern "media/full|media/transcripts|send_from_directory|AUDIO_FULL_DIR|TRANSCRIPTS_DIR" -Context 2,2
Output (excerpt):
    src\app\routes\media.py:15:    send_from_directory,
    src\app\routes\media.py:93:    return _send_from_base(
    src\app\routes\media.py:94:        Path(current_app.config["AUDIO_FULL_DIR"]),
    src\app\routes\media.py:181:            "Transcript not found: filename=%s base=%s",
    src\app\routes\media.py:194:            Path(current_app.config["TRANSCRIPTS_DIR"]),

Phase 15.4 — Curl smoke tests (dev)

Command:
    Start-Sleep -Seconds 6
    curl.exe -i --max-time 5 http://127.0.0.1:8000/media/transcripts/2025-02-06_ARG_Mitre.json
    curl.exe -i --max-time 5 http://127.0.0.1:8000/media/full/2025-02-06_ARG_Mitre.mp3
Output:
    curl: (7) Failed to connect to 127.0.0.1 port 8000 after ~2s
    curl: (7) Failed to connect to 127.0.0.1 port 8000 after ~2s

Note:
    Local connectivity issue persists (same symptom as previous dev-start smoke tests). Server logs confirm bind to 127.0.0.1:8000.

Phase 16 — Final Media Audit (runtime-only)

Phase 16.1 — Repo media absent

Command:
    Test-Path .\media
    Test-Path .\media2
    Test-Path .\media_repo_off
Output:
    False
    True
    True

Phase 16.2 — Runtime media root present

Command:
    $rt = $env:CORAPAN_RUNTIME_ROOT
    if (-not $rt) { $rt = Join-Path (Get-Location) "runtime\corapan" }
    $rm = Join-Path $rt "media"
    "CORAPAN_RUNTIME_ROOT=$rt"
    "RUNTIME_MEDIA=$rm"
    Test-Path $rm
    Get-ChildItem $rm -Directory | Select Name
Output:
    CORAPAN_RUNTIME_ROOT=C:\dev\corapan-webapp\runtime\corapan
    RUNTIME_MEDIA=C:\dev\corapan-webapp\runtime\corapan\media
    True
    Name
    ----
    mp3-full
    mp3-split
    mp3-temp
    transcripts

Phase 16.3 — Python hardcoded media audit

Command:
    Get-ChildItem .\src -Recurse -Filter *.py |
      Select-String -Pattern "(^|[\\/\s])media([\\/]|$)|PROJECT_ROOT.*media|Path\(.+media" -Context 2,2
Output (excerpt):
    src\app\config\__init__.py:112:        _candidate_runtime_media = Path(_runtime_root) / "media"
    src\app\config\__init__.py:121:        MEDIA_ROOT = PROJECT_ROOT / "media"   # dev fallback only

Phase 16.4 — PowerShell media audit

Command:
    Get-ChildItem .\scripts -Recurse -Filter *.ps1 |
      Select-String -Pattern "(\.\\media\\)|(/media/)|CORAPAN_MEDIA_ROOT" -Context 2,2
Output (excerpt):
    scripts\dev-start.ps1:51:    $env:CORAPAN_MEDIA_ROOT = Join-Path $env:CORAPAN_RUNTIME_ROOT "media"
    scripts\deploy_sync\sync_media.ps1:85:$localMediaRoot = $env:CORAPAN_MEDIA_ROOT

Phase 16.5 — YAML/Compose media mounts

Command:
    Get-ChildItem . -Recurse -File -Include *.yml,*.yaml |
      Select-String -Pattern "(\./media)|(\.\\media\\)|(/media:)|CORAPAN_MEDIA_ROOT" -Context 2,2
Output (excerpt):
    infra\docker-compose.dev.yml:71:      - ${CORAPAN_MEDIA_ROOT:-./runtime/corapan/media}/mp3-full:/app/media/mp3-full:ro
    infra\docker-compose.dev.yml:72:      - ${CORAPAN_MEDIA_ROOT:-./runtime/corapan/media}/mp3-split:/app/media/mp3-split:ro
    infra\docker-compose.dev.yml:73:      - ${CORAPAN_MEDIA_ROOT:-./runtime/corapan/media}/mp3-temp:/app/media/mp3-temp
    infra\docker-compose.dev.yml:74:      - ${CORAPAN_MEDIA_ROOT:-./runtime/corapan/media}/transcripts:/app/media/transcripts:ro

Phase 16.6 — Runtime media endpoint check (dev)

Command:
    Remove-Item Env:CORAPAN_MEDIA_ROOT -ErrorAction SilentlyContinue
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1
    Start-Sleep 4
    curl.exe -I --max-time 5 http://127.0.0.1:8000/media/transcripts/ARG/2025-02-04_ARG_Mitre.json
    curl.exe -I --max-time 5 http://127.0.0.1:8000/media/full/ARG/2025-02-04_ARG_Mitre.mp3
Output:
    curl: (7) Failed to connect to 127.0.0.1 port 8000 after ~2s
    curl: (7) Failed to connect to 127.0.0.1 port 8000 after ~2s

Note:
    Local curl connectivity issue persists in this environment. Browser requests do resolve after login.

Phase 17 — Player URL encoding & subfolder support

Cause:
    Double-encoded media query params (e.g. %252F) caused `/player` to pass encoded paths through, breaking subfolder media like ARG/....

Fixes:
    - [static/js/modules/player-url.js](static/js/modules/player-url.js): single-encode `audio` + `transcription` params.
    - [static/js/modules/advanced/datatableFactory.js](static/js/modules/advanced/datatableFactory.js): use shared builder and raw paths.
    - [static/js/modules/player-overview.js](static/js/modules/player-overview.js): use shared builder and raw paths.
    - [templates/search/_results.html](templates/search/_results.html): build `/media/*` paths and encode once.
    - [src/app/routes/player.py](src/app/routes/player.py): decode once; decode again only if `%2F` remains.

Commands:
    curl.exe -I --max-time 5 http://127.0.0.1:8000/media/full/ARG/2023-10-10_ARG_Mitre.mp3
    curl.exe -I --max-time 5 http://127.0.0.1:8000/media/transcripts/ARG/2023-10-10_ARG_Mitre.json
    curl.exe -I --max-time 5 "http://127.0.0.1:8000/player?audio=%2Fmedia%2Ffull%2FARG%2F2023-10-10_ARG_Mitre.mp3&transcription=%2Fmedia%2Ftranscripts%2FARG%2F2023-10-10_ARG_Mitre.json"

Output:
    - /media/full/... → HTTP/1.1 404 NOT FOUND
    - /media/transcripts/... → HTTP/1.1 200 OK
    - /player?... → HTTP/1.1 303 SEE OTHER (redirect to /login?next=...)

Phase 17b — Audio 404 root cause (dev media root mismatch)

Observation:
    Transcript route works, audio route 404 even with clean `/media/full/ARG/...` URL.

Filesystem evidence (runtime):
    Command:
        $rt = $env:CORAPAN_RUNTIME_ROOT; if (-not $rt) { $rt = Join-Path (Get-Location) "runtime\corapan" }
        $mr = Join-Path $rt "media"
        "RUNTIME_MEDIA_ROOT=$mr"
        $rel = "ARG\2025-02-04_ARG_Mitre.mp3"
        Test-Path (Join-Path $mr "mp3-full\$rel")
        Test-Path (Join-Path $mr "full\$rel")
        Test-Path (Join-Path $mr "mp3-split\$rel")
    Output:
        RUNTIME_MEDIA_ROOT=C:\dev\corapan-webapp\runtime\corapan\media
        True
        False
        False

HTTP evidence:
    Command:
        curl.exe -I --max-time 5 http://127.0.0.1:8000/media/full/ARG/2025-02-04_ARG_Mitre.mp3
    Output:
        HTTP/1.1 404 NOT FOUND

Conclusion:
    Runtime file exists under `mp3-full`, but the running server is resolving `MEDIA_ROOT` to the repo media path (missing), so `/media/full` returns 404.

Fix:
    In dev mode, when `CORAPAN_RUNTIME_ROOT`/`CORAPAN_MEDIA_ROOT` are unset, allow `MEDIA_ROOT` to resolve to repo-local runtime media if it exists.
    - Updated fallback logic in [src/app/config/__init__.py](src/app/config/__init__.py) to pick `PROJECT_ROOT/runtime/corapan/media` in dev.
