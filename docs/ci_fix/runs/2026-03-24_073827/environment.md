# Environment

- Branch: `main`
- Commit SHA: `9bc9782954feefb6804a84c4391151ac8a9aeaec`
- GitHub Run ID: `unavailable (no gh CLI / no direct Actions access on this host)`
- Workflow URL: `unavailable`
- Lokales OS: Windows
- Lokales Python: `3.12.10`
- Lokales Node: `unavailable (node executable not installed on this host)`
- Lokaler Docker-Status: `daemon unavailable` (`dockerDesktopLinuxEngine` pipe not found)
- GitHub CLI: `unavailable`

Relevante lokale Repro-Variablen ohne Secrets:
- `FLASK_ENV=testing`
- `FLASK_SECRET_KEY=test-key`
- `JWT_SECRET_KEY=test-jwt-key`
- `AUTH_HASH_ALGO=argon2` fuer die servicefreie Repro
- `BLS_CORPUS=corapan`
- `CORAPAN_RUNTIME_ROOT=c:/dev/corapan/tmp/ci-runtime`
- `CORAPAN_MEDIA_ROOT=c:/dev/corapan/tmp/ci-runtime/media`
- `CORAPAN_DATA_ROOT=c:/dev/corapan/tmp/ci-runtime/data`
- `AUTH_DATABASE_URL=postgresql+psycopg2://corapan_auth:corapan_auth@localhost:54320/corapan_auth` fuer lokale Service-Simulation ohne laufenden Container

Lokale vs. CI-Unterschiede:
- lokal kein `gh`, daher keine echten GitHub-Run-IDs oder Remote-Logs
- lokal kein laufender Docker-Daemon, daher kein vollstaendiger Postgres-/Playwright-End-to-End-Check
- GitHub Actions laeuft auf `ubuntu-latest`; die angepassten Workflows nutzen dort Python- und Node-Setups ueber Actions statt lokale Installationen
