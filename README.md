# CO.RA.PAN

CO.RA.PAN, the Corpus Radiofonico Panhispanico, is a research infrastructure for searching, listening to, and analyzing a pan-Hispanic radio corpus of professionally produced spoken Spanish.

This repository is the system-level root for the project. It contains the versioned web application under `app/`, the operator-facing maintenance and deployment helpers, the architecture and operations documentation, and the root-level workflow/governance files that define the repository contract.

## Project Purpose

CO.RA.PAN combines:

- a curated metadata model for radio material from across the Spanish-speaking world
- aligned transcripts and audio assets
- BlackLab-backed corpus search
- statistical publishing workflows
- a web application for search, playback, exploration, and administration

The repository therefore represents more than a single Flask app. It is the GitHub root for the whole operational workspace around the corpus.

## Repository Structure

```text
corapan/
  app/                     # versioned application and deploy implementation
  data/                    # runtime data, not versioned
    config/                # canonical runtime web config
  media/                   # runtime media, not versioned
  logs/                    # runtime logs, not versioned
  maintenance_pipelines/   # export, deploy, and publishing helpers
  docs/                    # architecture, operations, migration, and change docs
  scripts/                 # root-level dev wrappers and helpers
  .github/                 # active repository governance and CI/deploy workflows
  docker-compose.dev-postgres.yml
  .gitignore
  .python-version
  README.md
```

## Root vs App

The root repository contains the workspace-level truth:

- repository workflows under `.github/`
- system and operations documentation under `docs/`
- maintenance orchestration under `maintenance_pipelines/`
- canonical local dev entry points under `scripts/`
- the root development compose file `docker-compose.dev-postgres.yml`

The application subtree under `app/` contains the implementation-specific truth:

- Flask backend and templates
- static assets and frontend modules
- application tests and migrations
- deploy scripts and infra compose files
- versioned BlackLab configuration under `app/config/blacklab`
- app-local dependency manifests and build tooling

For application-specific setup and feature details, see [app/README.md](app/README.md).

## Runtime and Deploy Contract

- Runtime web configuration lives under `data/config`.
- Versioned BlackLab configuration lives under `app/config/blacklab`.
- Runtime data, media, and logs remain outside the versioned app tree.
- Local development is rooted at the workspace root, not inside `app/` alone.
- Production application code runs from `/srv/webapps/corapan/app`.
- Production runtime data lives under `/srv/webapps/corapan/data`.
- Production media lives under `/srv/webapps/corapan/media`.
- Operator-managed secrets remain outside Git, with `passwords.env` managed on the server side.

## Canonical Local Entry Points

Use the root-level wrappers for normal local development:

- `scripts/dev-setup.ps1`
- `scripts/dev-start.ps1`
- `docker-compose.dev-postgres.yml`

These root entry points reflect the intended workspace contract after the root lift.

## Documentation Guide

- Architecture and system decisions: [docs/architecture](docs/architecture)
- Operations and runtime procedures: [docs/operations](docs/operations)
- Change history: [docs/changes](docs/changes)
- Root-lift and migration forensics: [docs/repo_finish](docs/repo_finish)

## Data and Licensing

The software in this repository is versioned. Corpus data, media, transcripts, and derived runtime artifacts are not part of the Git-tracked repository and remain governed by separate legal and operational constraints.

See [app/LICENSE](app/LICENSE) and [app/CITATION.cff](app/CITATION.cff) for software licensing and citation details.