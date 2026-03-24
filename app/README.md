# CO.RA.PAN Web App

This directory contains the versioned application and deploy implementation.

The repository root remains the canonical local development entry point. Use [../README.md](../README.md) and [../docs/operations/local-dev.md](../docs/operations/local-dev.md) for the root workflow.

## What Lives Here

- Flask backend under `src/app/`
- Jinja templates under `templates/`
- static assets under `static/`
- SQL migrations under `migrations/`
- app scripts and deploy helpers under `scripts/`
- app-specific compose files under `infra/`

## Local Development

Use the root wrappers for normal work:

```powershell
cd ..
.\scripts\dev-setup.ps1
.\scripts\dev-start.ps1
```

The active local dev contract is:

- root `docker-compose.dev-postgres.yml`
- root `scripts/dev-setup.ps1`
- root `scripts/dev-start.ps1`

## Dependency Story

Python:

- source files: `requirements.in`, `requirements-dev.in`
- compiled locks: `requirements.txt`, `requirements-dev.txt`
- compile tool: `uv pip compile`
- install or sync tools: `pip install -r ...` or `uv pip sync ...`

Node:

- `package.json` and `package-lock.json` exist only for Playwright

Update the Python lockfiles with:

```powershell
.\scripts\refresh-lockfiles.ps1
```

## Runtime and Env Variables

The application expects explicit runtime boundaries:

- `AUTH_DATABASE_URL`
- `BLS_BASE_URL`
- `BLS_CORPUS`
- `CORAPAN_RUNTIME_ROOT`
- `CORAPAN_MEDIA_ROOT`

Use `.env.example` for local examples and `passwords.env.template` for production secret structure. Do not commit `.env` or `passwords.env`.

## Tests and Quality

```powershell
pytest
ruff check src tests
ruff format src tests
```

The default pytest configuration excludes `live`, `e2e`, and `data` tests from the fast path.

## Related Docs

- [../docs/architecture/overview.md](../docs/architecture/overview.md)
- [../docs/architecture/template-customization.md](../docs/architecture/template-customization.md)
- [../docs/operations/local-dev.md](../docs/operations/local-dev.md)
- [../docs/operations/production.md](../docs/operations/production.md)
- [../docs/blacklab/README.md](../docs/blacklab/README.md)
- [CHANGELOG.md](CHANGELOG.md)

For deploy behavior, secrets handling, and production runtime expectations, use [../docs/operations/production.md](../docs/operations/production.md).