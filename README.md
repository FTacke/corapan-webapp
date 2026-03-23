# CO.RA.PAN Workspace Root

This repository root represents the system-level workspace for CO.RA.PAN.

Canonical target structure:

```text
corapan/
  app/                     # versioned application/deploy repository
  data/                    # runtime data, not versioned
    config/                # canonical runtime web config
  media/                   # runtime media, not versioned
  logs/                    # runtime logs, not versioned
  docs/                    # architecture, migration, and operations docs
  maintenance_pipelines/   # operator-facing export/deploy orchestration
  .github/                 # root-level governance and future workflow truth
  .gitignore
  README.md
```

## Runtime Contract

- Runtime web config lives under `data/config`.
- Versioned BlackLab config lives under `app/config/blacklab`.
- Runtime data, media, and logs are intentionally outside the versioned app tree.
- Production app code runs from `/srv/webapps/corapan/app`.
- Production runtime data lives under `/srv/webapps/corapan/data`.

## Root vs App

Root contains workspace-level and operator-level concerns:

- `docs/`
- `maintenance_pipelines/`
- `.github/`
- top-level dev wrappers such as `scripts/dev-start.ps1`
- root-level development compose such as `docker-compose.dev-postgres.yml`

`app/` contains the versioned application and deploy implementation:

- Flask application source
- templates and static assets
- Dockerfile and infra compose files
- deploy scripts
- migrations and tests
- versioned BlackLab config under `app/config/blacklab`

## Current Transition State

The workspace is being prepared for a root-lift from the historical `webapp/` repo root to `corapan/` with the application renamed to `app/`.

Until that migration is completed:

- the active versioned app/deploy repo still exists under `webapp/`
- the current versioned CI/deploy truth remains under `webapp/.github/workflows`
- root-level wrappers and maintenance resolvers are being prepared to work with either `app/` or `webapp/`

## Dev Entry Points

Canonical local development entry points are rooted at `corapan/`:

- `docker-compose.dev-postgres.yml`
- `scripts/dev-setup.ps1`
- `scripts/dev-start.ps1`

These wrappers resolve the active app implementation from `app/` first and `webapp/` second during the transition.