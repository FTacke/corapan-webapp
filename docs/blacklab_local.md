# BlackLab: Local Index Build vs. Server Build (Repo Facts)

## Goal
This repo contains both production and local/index build and run scripts for BlackLab; this document summarizes those repo facts for a local-build vs. server-build decision. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L1-L36), [scripts/blacklab/build_blacklab_index.ps1](scripts/blacklab/build_blacklab_index.ps1#L1-L27), [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L1-L22), [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L1-L36)

## Current BlackLab Integration (Repo Evidence)
### Docker image / container / ports
- Production run script uses image instituutnederlandsetaal/blacklab:latest with container name corapan-blacklab and port 8081 → 8080. Evidence: [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L26-L29)
- Dev compose uses the same image and port mapping 8081 → 8080 for the BlackLab service. Evidence: [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml#L90-L100)
- Dev-postgres compose also uses image instituutnederlandsetaal/blacklab:latest and 8081 → 8080. Evidence: [docker-compose.dev-postgres.yml](docker-compose.dev-postgres.yml#L28-L36)

### Index mount path (host → container)
- Production run mounts index to /data/index/corapan (read-only). Evidence: [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L109-L115)
- Dev compose mounts ./data/blacklab_index to /data/index/corapan. Evidence: [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml#L96-L97)
- Dev-postgres compose does the same and documents that /data/index/corapan maps to corpus “corapan”. Evidence: [docker-compose.dev-postgres.yml](docker-compose.dev-postgres.yml#L34-L36)
- BlackLab server config allows indexes under /data/index. Evidence: [config/blacklab/blacklab-server.yaml](config/blacklab/blacklab-server.yaml#L10-L12)

### Config mount path (host → container)
- Production run mounts config dir to /etc/blacklab. Evidence: [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L114-L115)
- Dev compose mounts ./config/blacklab to /etc/blacklab and sets BLACKLAB_CONFIG_DIR. Evidence: [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml#L96-L100)
- Dev-postgres compose does the same. Evidence: [docker-compose.dev-postgres.yml](docker-compose.dev-postgres.yml#L36-L39)

### Application endpoint usage (how the webapp calls BlackLab)
- Default BLS base URL is http://localhost:8081/blacklab-server (env var BLS_BASE_URL). Evidence: [src/app/extensions/http_client.py](src/app/extensions/http_client.py#L4-L30)
- Proxy blueprint is /bls and upstream is http://127.0.0.1:8081/blacklab-server/. Evidence: [src/app/routes/bls_proxy.py](src/app/routes/bls_proxy.py#L14-L17)
- Example env values include BLACKLAB_BASE_URL and BLACKLAB_SERVER_URL pointing to http://localhost:8081/blacklab-server. Evidence: [.env.example](.env.example#L58-L89)

## Index Layout & Swap Strategy
### Active index path and any symlink strategy
- Production path is /srv/webapps/corapan/data/blacklab_index and staging path is /srv/webapps/corapan/data/blacklab_index.new. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L24-L31)
- Local/dev paths use data/blacklab_index and data/blacklab_index.new. Evidence: [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L14-L18), [scripts/blacklab/build_blacklab_index.ps1](scripts/blacklab/build_blacklab_index.ps1#L18-L21)

### Staging index (.new) and cleanup behavior
- Production build creates blacklab_index.new and swaps it into blacklab_index after validation. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L171-L203), [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L471-L489)
- Local script uses blacklab_index.new and swaps to blacklab_index after build. Evidence: [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L16-L18), [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L187-L197)

### Rollback / rescue / leftover conventions
- Production build makes a timestamped backup (blacklab_index.bak_<timestamp>), and attempts rollback on swap failure. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L471-L502)
- Local script uses a non-timestamped backup (blacklab_index.bak). Evidence: [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L187-L197)

## Build Pipeline (as implemented)
### Inputs
- Production build expects TSV in /srv/webapps/corapan/data/tsv and metadata in /srv/webapps/corapan/data/metadata. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L9-L13)
- Local build input corpus is media/transcripts, with exports in data/blacklab_export/tsv. Evidence: [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L14-L16)
- The export tool defaults to input media/transcripts and output data/blacklab_export/tsv + docmeta.jsonl. Evidence: [src/scripts/blacklab_index_creation.py](src/scripts/blacklab_index_creation.py#L6-L10), [src/scripts/blacklab_index_creation.py](src/scripts/blacklab_index_creation.py#L548-L563)
- JSON preprocessing (optional) reads from media/transcripts and writes data/blacklab_export/json_ready with a top-level tokens array. Evidence: [scripts/blacklab/prepare_json_for_blacklab.py](scripts/blacklab/prepare_json_for_blacklab.py#L4-L11), [scripts/blacklab/prepare_json_for_blacklab.py](scripts/blacklab/prepare_json_for_blacklab.py#L116-L116)

### Build steps
- Production build uses Docker IndexTool with /data/export (TSV + metadata) and /data/index for output. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L186-L203)
- Local Docker build (PowerShell) uses data/blacklab_export/tsv, docmeta.jsonl, and config/blacklab/corapan-tsv.blf.yaml, and calls IndexTool inside the image with --linked-file-dir /data/export/metadata. Evidence: [scripts/blacklab/build_blacklab_index.ps1](scripts/blacklab/build_blacklab_index.ps1#L17-L22), [scripts/blacklab/build_blacklab_index.ps1](scripts/blacklab/build_blacklab_index.ps1#L198-L227)
- Local shell build uses IndexTool directly (system-installed) and passes --linked-file-dir for metadata. Evidence: [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L140-L171)

### Validation steps (what is checked, how, endpoints/files)
- Production pre-validation checks: non-empty index dir, file count, size, and presence of *.blfi.* files. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L220-L259)
- Production post-validation starts a temporary container and checks http://localhost:<port>/blacklab-server/ plus corpora/corpus endpoints for corpus “corapan”. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L286-L325)

### Swap / publish steps
- Production swap: timestamped backup then move blacklab_index.new → blacklab_index with rollback if needed. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L471-L502)
- Local swap: blacklab_index.new → blacklab_index and backup to blacklab_index.bak. Evidence: [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L187-L197)

## Compatibility Requirements (hard constraints)
### BlackLab version / image expectations
- The repo uses image instituutnederlandsetaal/blacklab:latest in prod run script, prod build script, and dev compose. Evidence: [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L26-L29), [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L35-L35), [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml#L91-L94)
- BlackLab server config indicates configVersion: 2 and comments reference BlackLab 5.0.0-SNAPSHOT. Evidence: [config/blacklab/blacklab-server.yaml](config/blacklab/blacklab-server.yaml#L3-L12)

### Java heap settings
- Production build uses JAVA_XMX/JAVA_XMS for IndexTool in Docker. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L41-L43), [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L196-L203)
- Dev compose sets JAVA_OPTS for BlackLab container. Evidence: [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml#L98-L101)

### Config usage
- The TSV BLF config is in config/blacklab/corapan-tsv.blf.yaml and is referenced by build scripts. Evidence: [config/blacklab/corapan-tsv.blf.yaml](config/blacklab/corapan-tsv.blf.yaml#L1-L32), [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L32-L32)
- The TSV BLF config expects linked JSON metadata via --linked-file-dir and sets tokid sensitivity to sensitive. Evidence: [config/blacklab/corapan-tsv.blf.yaml](config/blacklab/corapan-tsv.blf.yaml#L16-L17), [config/blacklab/corapan-tsv.blf.yaml](config/blacklab/corapan-tsv.blf.yaml#L115-L119)

## What Must Match Between Dev and Prod
- Same BlackLab image tag (repo uses instituutnederlandsetaal/blacklab:latest in prod/dev scripts). Evidence: [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L26-L29), [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml#L91-L94)
- Same BlackLab config directory mounted to /etc/blacklab. Evidence: [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L114-L115), [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml#L96-L100)
- Same index layout: /data/index/corapan in the container, with server indexLocations set to /data/index. Evidence: [infra/docker-compose.dev.yml](infra/docker-compose.dev.yml#L96-L97), [config/blacklab/blacklab-server.yaml](config/blacklab/blacklab-server.yaml#L10-L12)
- Same metadata linkage strategy (linked-file-dir /data/export/metadata) when building TSV indexes. Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L196-L203), [scripts/blacklab/build_blacklab_index.ps1](scripts/blacklab/build_blacklab_index.ps1#L220-L227)

## Local Build Feasibility (Repo View)
### Likely feasible if
- You can run the Docker-based local build script that uses the same BlackLab image and config and indexes data/blacklab_export/tsv with linked metadata. Evidence: [scripts/blacklab/build_blacklab_index.ps1](scripts/blacklab/build_blacklab_index.ps1#L17-L22), [scripts/blacklab/build_blacklab_index.ps1](scripts/blacklab/build_blacklab_index.ps1#L198-L227)
- Or you can generate TSV exports from media/transcripts and then run the local shell build (IndexTool). Evidence: [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L14-L16), [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L88-L90), [scripts/blacklab/build_blacklab_index.sh](scripts/blacklab/build_blacklab_index.sh#L140-L171)

### Blockers / unknowns (repo-only)
- data/ and media/ (including data/blacklab_index and media/transcripts) are gitignored, so local build requires external data not present in the repo. Evidence: [.gitignore](.gitignore#L86-L91)
- Production build expects TSV and metadata at /srv/webapps/corapan/data/tsv and /srv/webapps/corapan/data/metadata (paths outside repo). Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L9-L13)

## Open Questions for Server Check (to verify)
1. Which exact image digest is running for instituutnederlandsetaal/blacklab:latest? (Repo references only the tag.) Evidence: [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L26-L29)
2. Does production mount the same config directory contents as config/blacklab (and the same corapan-tsv.blf.yaml)? Evidence: [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L114-L115), [config/blacklab/corapan-tsv.blf.yaml](config/blacklab/corapan-tsv.blf.yaml#L1-L32)
3. Is the active index path /srv/webapps/corapan/data/blacklab_index and is swap/backup done as in the prod build script? Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L24-L31), [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L471-L502)
4. Are TSV inputs and metadata present at /srv/webapps/corapan/data/tsv and /srv/webapps/corapan/data/metadata? Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L9-L13)
5. Is BlackLab reachable at http://localhost:8081/blacklab-server in production (as the scripts and default app config assume)? Evidence: [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh#L28-L29), [src/app/extensions/http_client.py](src/app/extensions/http_client.py#L27-L30)
6. Is corpus ID “corapan” present in the running index (used during validation and mount layout)? Evidence: [scripts/blacklab/build_blacklab_index_prod.sh](scripts/blacklab/build_blacklab_index_prod.sh#L324-L325), [docker-compose.dev-postgres.yml](docker-compose.dev-postgres.yml#L34-L36)
