# Data Migration Plan (AS-IS Evidence + TO-BE Template)

Status: Draft (evidence collection only)
Owner: TBD
Last updated: 2026-01-18

Purpose
Define a migration plan for data and runtime assets. This document captures current-state evidence and provides a TO-BE template with open decisions.

Scope
In scope:
- Runtime statistics (corpus_stats.json + viz_*.png)
- Data directories under data/ and runtime/
- BlackLab index and exports
- Deployment sync scripts (data and statistics)
- Environment variables related to data and runtime

Out of scope:
- Frontend UI changes
- Auth schema changes (only note paths)

Evidence Collection (AS-IS)

1) Repo root and top-level directories

Evidence:
    Command:
        Get-ChildItem -Directory | Select-Object Name
    Output:
        Name
        ----
        .github
        .pytest_cache
        .ruff_cache
        .venv
        .vscode
        config
        data
        docs
        infra
        logs
        LOKAL
        media
        migrations
        node_modules
        reports
        runtime
        scripts
        src
        static
        templates
        tests
        tools

2) Runtime statistics location and files

Evidence:
    Command:
        Get-ChildItem .\runtime\corapan\data\public\statistics -ErrorAction SilentlyContinue | Select-Object Name
    Output:
        Name
        ----
        corpus_stats.json
        viz_ARG-CBA_resumen.png
        viz_ARG-CHU_resumen.png
        viz_ARG-SDE_resumen.png
        viz_ARG_resumen.png
        viz_BOL_resumen.png
        viz_CHL_resumen.png
        viz_COL_resumen.png
        viz_CRI_resumen.png
        viz_CUB_resumen.png
        viz_DOM_resumen.png
        viz_ECU_resumen.png
        viz_ESP-CAN_resumen.png
        viz_ESP-SEV_resumen.png
        viz_ESP_resumen.png
        viz_genero_profesionales.png
        viz_GTM_resumen.png
        viz_HND_resumen.png
        viz_MEX_resumen.png
        viz_modo_genero_profesionales.png
        viz_NIC_resumen.png
        viz_PAN_resumen.png
        viz_PER_resumen.png
        viz_PRY_resumen.png
        viz_SLV_resumen.png
        viz_total_corpus.png
        viz_URY_resumen.png
        viz_USA_resumen.png
        viz_VEN_resumen.png

3) data/ top-level directories

Evidence:
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

3.1) data/ inventory (non-BlackLab excerpts)

Evidence:
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

    Note: BlackLab-related paths are explicitly out of scope for this migration.

4) Git ignore status for runtime and data

Evidence:
    Command:
        git check-ignore -v .\runtime\corapan* 2>$null
    Output:
        .gitignore:154:/runtime/        ".\\runtime\\corapan*"

Evidence:
    Command:
        git check-ignore -v .\data* 2>$null
    Output:
        (no output)

5) Workspace status (untracked files)

Evidence:
    Command:
        git status -sb
    Output:
        ## work/current...origin/work/current
        ?? docs/problem/migration_devprod.md

6) LOKAL is a nested git repository

Evidence:
    Command:
        Test-Path .\LOKAL\.git
    Output:
        True

7) Docker compose references (ports, data mounts, BlackLab)

Evidence:
    Command:
        Get-ChildItem docker-compose*.yml, infra\docker-compose*.yml | Select-String -Pattern "blacklab|postgres|5432|8081|blacklab_index|db_public|data/db"
    Output:
        docker-compose.dev-postgres.yml:5:# Default auth DB URL: postgresql+psycopg://corapan_auth:corapan_auth@localhost:54320/corapan_auth
        docker-compose.dev-postgres.yml:16:      - "54320:5432"
        docker-compose.dev-postgres.yml:18:      - ./data/db/postgres_dev:/var/lib/postgresql/data
        docker-compose.dev-postgres.yml:35:    image: instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7
        docker-compose.dev-postgres.yml:38:      - "8081:8080"
        docker-compose.dev-postgres.yml:41:      - ./data/blacklab_index:/data/index/corapan:ro
        docker-compose.dev-postgres.yml:42:      - ./config/blacklab:/etc/blacklab:ro
        docker-compose.yml:27:      - ~/corapan/data/db:/app/data/db:ro
        infra/docker-compose.dev.yml:21:      - "54320:5432"
        infra/docker-compose.dev.yml:77:      - ./data/db:/app/data/db
        infra/docker-compose.dev.yml:91:    image: instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7
        infra/docker-compose.dev.yml:94:      - "8081:8080"
        infra/docker-compose.dev.yml:96:      - ./data/blacklab_index:/data/index/corapan:ro
        infra/docker-compose.dev.yml:97:      - ./config/blacklab:/etc/blacklab:ro
        infra/docker-compose.prod.yml:28:      - corapan_postgres_prod:/var/lib/postgresql/data
        infra/docker-compose.prod.yml:87:      - ~/corapan/data/db:/app/data/db:ro

Touchpoints (AS-IS)

Python (src)
- Runtime stats path is derived from PUBLIC_STATS_DIR or CORAPAN_RUNTIME_ROOT. Evidence from search results in src/app/config/__init__.py and src/app/routes/corpus.py.
- Auth DB configured via AUTH_DATABASE_URL (src/app/config/__init__.py, src/app/extensions/sqlalchemy_ext.py).
- BlackLab base URL defaults to http://localhost:8081/blacklab-server (src/app/extensions/http_client.py). Proxy routes in src/app/routes/bls_proxy.py.

Evidence (selected snippets from search):
    Command:
        Get-ChildItem .\src -Recurse -Filter *.py | Select-String -Pattern "PUBLIC_STATS_DIR|CORAPAN_RUNTIME_ROOT|data/public/statistics|blacklab|AUTH_DATABASE_URL" -Context 2,2
    Output (excerpt):
        src\app\config\__init__.py:86:    _runtime_root = os.getenv("CORAPAN_RUNTIME_ROOT")
        src\app\config\__init__.py:87:    _explicit_stats_dir = os.getenv("PUBLIC_STATS_DIR")
        src\app\config\__init__.py:96:        PUBLIC_STATS_DIR = Path(_runtime_root) / "data" / "public" / "statistics"
        src\app\config\__init__.py:156:    AUTH_DATABASE_URL = os.getenv("AUTH_DATABASE_URL")
        src\app\extensions\http_client.py:30:    "BLS_BASE_URL", "http://localhost:8081/blacklab-server"
        src\app\routes\corpus.py:221:        stats_dir = Path(current_app.config['PUBLIC_STATS_DIR'])

Scripts (PowerShell + shell)
- Dev startup sets AUTH_DATABASE_URL and BLACKLAB_BASE_URL and references PUBLIC_STATS_DIR.
- Statistics migration helper derives CORAPAN_RUNTIME_ROOT and uses data/public/statistics as source.
- BlackLab build and run scripts reference data/blacklab_export and data/blacklab_index.
- Deployment sync scripts explicitly include/exclude blacklab_index and handle statistics directory.

Evidence (selected snippets from search):
    Command:
        Get-ChildItem .\scripts -Recurse -File | Where-Object { $_.Extension -in ".ps1", ".sh" } | Select-String -Pattern "PUBLIC_STATS_DIR|CORAPAN_RUNTIME_ROOT|data/public/statistics|blacklab|AUTH_DATABASE_URL" -Context 2,2
    Output (excerpt):
        scripts\dev-start.ps1:68:$statsFile = Join-Path $env:PUBLIC_STATS_DIR "corpus_stats.json"
        scripts\dev-start.ps1:102:$env:AUTH_DATABASE_URL = "postgresql+psycopg://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth"
        scripts\dev-start.ps1:109:$env:BLACKLAB_BASE_URL = "http://localhost:8081/blacklab-server"
        scripts\migrate_stats_to_runtime.ps1:15:$targetDir = Join-Path $env:CORAPAN_RUNTIME_ROOT "data\public\statistics"
        scripts\blacklab\build_blacklab_index.ps1:19:$TSV_SOURCE_DIR = "data\blacklab_export\tsv"
        scripts\blacklab\build_blacklab_index.ps1:21:$INDEX_TARGET_DIR = "data\blacklab_index"
        scripts\deploy_sync\sync_data.ps1:121:    "blacklab_export"
        scripts\deploy_sync\sync_data.ps1:179:# Remote location: /srv/webapps/corapan/data/public/statistics

LOKAL generators (Python) referencing repo data paths

Evidence:
    Command:
        Get-ChildItem .\LOKAL -Recurse -File -Filter *.py | Select-String -Pattern "data/db|data\\db|data/metadata|data\\metadata|data/exports|data\\exports|data/db_public|data\\db_public|data/public|data\\public"
    Output (excerpt):
        LOKAL\_0_json\03_build_metadata_stats.py:14:    data/db/stats_country.db        - Statistiken pro Land
        LOKAL\_0_json\03_build_metadata_stats.py:15:    data/db/stats_files.db          - Metadaten pro Datei
        LOKAL\_0_json\03_build_metadata_stats.py:520:  data/db_public/stats_all.db     - Globale Statistiken
        LOKAL\_1_metadata\export_metadata.py:15:Output is written to data/metadata/vYYYY-MM-DD/ with a "latest" symlink.
        LOKAL\_1_zenodo-repos\zenodo_metadata.py:6:Quelle:     data/metadata/latest/

Open Questions / TODOs
- TODO: confirm production runtime root and whether statistics must live under /srv/webapps/corapan/data/public/statistics.
- TODO: confirm authoritative source of statistics in prod (runtime vs repo data/public/statistics).
- TODO: decide retention/cleanup policy for blacklab_index.backup, blacklab_index.bad, blacklab_index.testbuild.
- TODO: determine migration handling for nested LOKAL repo (separate repo ownership and change process).
- TODO: confirm whether deployment sync should move stats source from repo data/public/statistics to runtime path consistently.

TO-BE Migration Template

1) Objectives
- Define single source of truth for statistics and runtime assets.
- Ensure dev and prod align on runtime paths and environment configuration.
- Avoid accidental sync of non-source data (temporary, backup, or generated).

2) Target State (proposed)
- Runtime root is the authoritative location for generated statistics.
- data/ contains build inputs and source artifacts only (as decided).
- Deploy scripts explicitly sync only source-of-truth directories.

3) Proposed Changes (fill in)
- Change list:
  - TODO: set or standardize CORAPAN_RUNTIME_ROOT in dev and prod
  - TODO: update sync scripts to read statistics from runtime path (if needed)
  - TODO: clarify or remove legacy repo data/public/statistics references
  - TODO: document operator workflow for generating and deploying stats

4) Migration Steps (draft)
- Step 1: Inventory existing runtime and data/public/statistics on dev and prod
- Step 2: Confirm which directory is authoritative
- Step 3: Move or regenerate statistics into target runtime path
- Step 4: Update environment variables and deployment sync (if required)
- Step 5: Validate app endpoints and data availability

5) Validation
- App config loads PUBLIC_STATS_DIR without error
- /corpus/api/statistics/corpus_stats.json returns expected JSON
- /corpus/api/statistics/viz_total_corpus.png returns expected image
- /health reports auth_db ok and blacklab ok/degraded as expected

6) Rollback Plan
- Keep previous statistics directory intact until validation passes
- Revert env vars to previous values
- Re-run sync using last known good source directory

7) Risks and Mitigations
- Risk: Syncing backup or testbuild indexes to production
  - Mitigation: Keep exclusions in sync scripts and add explicit allowlist
- Risk: Nested LOKAL repo changes not tracked with main repo
  - Mitigation: Document change process and separate release tracking

8) Ownership and Timeline
- Owners: TODO
- Target date: TODO
- Reviewers: TODO

Implementation Status (DEV, non-BlackLab)
- Runtime-aware outputs added:
    - [LOKAL/_0_json/03_build_metadata_stats.py](LOKAL/_0_json/03_build_metadata_stats.py) now resolves DB output under `${CORAPAN_RUNTIME_ROOT}/data` when set.
    - [LOKAL/_1_metadata/export_metadata.py](LOKAL/_1_metadata/export_metadata.py) now resolves metadata output under `${CORAPAN_RUNTIME_ROOT}/data` when set.
- Statistics generator already writes to runtime via PUBLIC_STATS_DIR/CORAPAN_RUNTIME_ROOT.

Target Runtime Layout (DEV/PROD) — Non-BlackLab

runtime/corapan/data
    public/statistics/          # generated (safe to regenerate)
    metadata/
        latest/                   # alias to current release
        vYYYY-MM-DD/              # versioned exports
    db/
        public/                   # regenerable stats DBs (if used)
            stats_files.db
            stats_country.db
            stats_all.db (optional; deprecated if unused)
        restricted/               # prod-owned, never synced
            auth.db
    counters/                   # prod-owned, never synced
    tmp/                        # ephemeral, never synced
        stats_temp/
        cache/

Class Rules
1) Regenerable (may be generated in DEV and synced):
     - data/public/statistics/*
     - data/metadata/v*/
     - data/db/public/* (only if actually used)

2) Prod-owned (never regenerate or sync from DEV):
     - data/db/restricted/* (auth)
     - data/counters/*

3) Ephemeral (never sync):
     - data/tmp/** (including stats_temp, cache)

Proposed Mapping (repo data → runtime data)
- data/public/statistics → runtime/data/public/statistics (one-time migrate or regenerate)
- data/metadata/* → runtime/data/metadata/* (one-time migrate or regenerate)
- data/db/*.db → runtime/data/db/public/*.db (only if these DBs are still used)
- data/counters/* → do not migrate (prod-owned)
- data/stats_temp → runtime/data/tmp/stats_temp (ephemeral) or delete