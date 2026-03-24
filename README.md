# CO.RA.PAN

CO.RA.PAN is the repository root for the corpus web application, its runtime contract, and the shared governance around local development, deployment, and repository maintenance.

This root is intentionally small:

- `app/` contains the versioned application and deploy implementation
- `.github/` contains the active repository governance and CI/deploy workflows
- `docs/` contains the canonical maintainer documentation
- `scripts/` contains the root development entry points
- `data/` and `media/` are runtime state and are not the versioned source of truth
- `maintenance_pipelines/` is a separate operational subtree and is not part of the template-cleanup surface

## Canonical Entry Points

Local development is rooted at `CORAPAN/`, not inside `app/`.

Use these files as the canonical development path:

- `scripts/dev-setup.ps1`
- `scripts/dev-start.ps1`
- `docker-compose.dev-postgres.yml`

Use these files as the canonical production path:

- `app/infra/docker-compose.prod.yml`
- `app/scripts/deploy_prod.sh`
- `.github/workflows/deploy.yml`

## Runtime Contract

- `data/config/` is the runtime configuration root
- `app/config/blacklab/` is the versioned BlackLab configuration source
- `AUTH_DATABASE_URL` is the only valid auth/core database variable
- `BLS_BASE_URL` is the canonical BlackLab base URL variable
- `BLS_CORPUS` must always be set explicitly
- runtime data lives under `data/`
- runtime media lives under `media/`
- operator-managed secrets stay outside Git in `passwords.env`

## Dependency Story

The Python toolchain is standardized on `requirements.in`/`requirements.txt` and `requirements-dev.in`/`requirements-dev.txt`, generated with `uv pip compile` and consumed by `uv pip sync` or `pip install -r` as appropriate.

Node is used only for Playwright end-to-end tests through `app/package.json` and `app/package-lock.json`.

There is no parallel Poetry or `uv sync` lockfile workflow.

## Documentation Map

Start with [docs/index.md](docs/index.md).

The canonical maintainer docs are:

- [docs/architecture/overview.md](docs/architecture/overview.md)
- [docs/architecture/template-customization.md](docs/architecture/template-customization.md)
- [docs/operations/local-dev.md](docs/operations/local-dev.md)
- [docs/operations/production.md](docs/operations/production.md)
- [docs/blacklab/README.md](docs/blacklab/README.md)
- [docs/adr/README.md](docs/adr/README.md)

## Licensing and Citation

The software in this repository is released under the MIT License. See [app/LICENSE](app/LICENSE), [app/CITATION.cff](app/CITATION.cff), and [app/CHANGELOG.md](app/CHANGELOG.md).
