# Agent Governance Fundstellen

Date: 2026-03-20
Scope: pure repository inventory and classification breakdown
Relation: detailed evidence for docs/changes/2026-03-20-agent-governance-classification.md

This document breaks the classification overview down to concrete repository files and notable markers.

It is a documentation-only inventory.

It does not perform:
- cleanup
- deletion
- migration
- service execution
- runtime changes

## Active

### Canonical development stack

Files:
- docker-compose.dev-postgres.yml
- scripts/dev-setup.ps1
- scripts/dev-start.ps1

Relevant markers:
- docker-compose.dev-postgres.yml:2-3 documents start and stop via this compose file.
- scripts/dev-setup.ps1:75 sets AUTH_DATABASE_URL to the local Postgres DSN.
- scripts/dev-setup.ps1:189 starts services via docker compose -f docker-compose.dev-postgres.yml.
- scripts/dev-start.ps1:137 sets AUTH_DATABASE_URL to the local Postgres DSN.
- scripts/dev-start.ps1:178 starts missing services via docker compose -f docker-compose.dev-postgres.yml.

Why active:
- These files align with the observed running local stack based on docker-compose.dev-postgres.yml.
- They define the currently confirmed development workflow.

Role details:
- Compose file role: dev infrastructure stack for Postgres and BlackLab.
- dev-setup.ps1 role: first-time or full local setup path.
- dev-start.ps1 role: daily local app start path.

### Canonical production stack

Files:
- infra/docker-compose.prod.yml
- scripts/deploy_prod.sh
- .github/workflows/deploy.yml

Relevant markers:
- infra/docker-compose.prod.yml:58 sets AUTH_DATABASE_URL for the production app container.
- infra/docker-compose.prod.yml:84 sets BLS_BASE_URL for the production app container.
- infra/docker-compose.prod.yml:85 sets BLS_CORPUS to corapan.
- scripts/deploy_prod.sh:38 sets ENV_FILE to ${BASE_DIR}/config/passwords.env.
- scripts/deploy_prod.sh:39 sets COMPOSE_FILE to ${APP_DIR}/infra/docker-compose.prod.yml.
- scripts/deploy_prod.sh:89-90 starts the production stack via docker-compose and the canonical prod compose file.
- .github/workflows/deploy.yml:42 invokes bash scripts/deploy_prod.sh.

Why active:
- These files describe the confirmed production deployment path and mutually reference each other.

Role details:
- compose role: canonical production topology.
- deploy script role: canonical production rollout path.
- workflow role: automation entry point for the deploy script.

### Canonical auth/core database variable

Files:
- src/app/config/__init__.py
- src/app/extensions/sqlalchemy_ext.py
- .env.example
- infra/docker-compose.prod.yml

Relevant markers:
- src/app/config/__init__.py:235-243 requires AUTH_DATABASE_URL and fails fast when missing.
- src/app/extensions/sqlalchemy_ext.py:22-24 reads AUTH_DATABASE_URL and errors if it is not configured.
- .env.example:46 declares AUTH_DATABASE_URL as the auth database setting.
- infra/docker-compose.prod.yml:58 passes AUTH_DATABASE_URL into the production container.

Why active:
- These are the main current sources that wire the auth and core database through AUTH_DATABASE_URL.

Role details:
- variable: AUTH_DATABASE_URL
- function: init_engine in src/app/extensions/sqlalchemy_ext.py

### Canonical BlackLab base variable

Files:
- src/app/config/__init__.py
- src/app/extensions/http_client.py
- infra/docker-compose.prod.yml
- .env.example

Relevant markers:
- src/app/config/__init__.py:70-71 reads BLS_BASE_URL.
- src/app/extensions/http_client.py:33-34 reads BLS_BASE_URL.
- infra/docker-compose.prod.yml:84 sets BLS_BASE_URL for production.
- .env.example:60 declares BLS_BASE_URL as the BlackLab base URL setting.

Why active:
- These are the current primary code and config touchpoints for BlackLab base URL wiring.

Role details:
- variable: BLS_BASE_URL
- helper role: BlackLab HTTP client base URL source

### Production secret source retained in setup

Files:
- scripts/deploy_prod.sh
- .github/workflows/deploy.yml
- passwords.env.template

Relevant markers:
- scripts/deploy_prod.sh:38 points ENV_FILE to ${BASE_DIR}/config/passwords.env.
- .github/workflows/deploy.yml:19 documents passwords.env under /srv/webapps/corapan/config/.
- passwords.env.template:7-9 documents passwords.env creation and handling.

Why active:
- passwords.env remains part of the confirmed production deployment path, even though application-side auto-loading is deprecated.

Role details:
- file role: operator-managed production secret source

## Legacy

### Alternate development compose path

Files:
- infra/docker-compose.dev.yml

Relevant markers:
- infra/docker-compose.dev.yml:51 sets AUTH_DATABASE_URL.
- infra/docker-compose.dev.yml:52 also sets DATABASE_URL.
- infra/docker-compose.dev.yml:4-7 documents a full alternate dev workflow.

Why legacy:
- It is a plausible development path still present in the repo, but it is not the currently confirmed canonical dev stack.

Role details:
- compose role: alternate app-plus-db-plus-blacklab dev stack

### Legacy BlackLab variable naming

Files:
- scripts/dev-setup.ps1
- scripts/dev-start.ps1
- README.md

Relevant markers:
- scripts/dev-setup.ps1:82 sets BLACKLAB_BASE_URL.
- scripts/dev-start.ps1:146 sets BLACKLAB_BASE_URL.
- README.md:357 documents BLACKLAB_BASE_URL.

Why legacy:
- BLACKLAB_BASE_URL remains present as an older naming pattern, but the canonical governance variable is now BLS_BASE_URL.

Role details:
- variable: BLACKLAB_BASE_URL

### Legacy auth/core variable naming

Files:
- infra/docker-compose.dev.yml
- infra/docker-compose.prod.yml
- README.md

Relevant markers:
- infra/docker-compose.dev.yml:52 sets DATABASE_URL next to AUTH_DATABASE_URL.
- infra/docker-compose.prod.yml:59 sets DATABASE_URL next to AUTH_DATABASE_URL.
- README.md:272 still mentions DATABASE_URL as an expected secret example.

Why legacy:
- DATABASE_URL still appears in operational and documentation contexts, but is no longer the valid canonical variable for auth/core.

Role details:
- variable: DATABASE_URL

### Historical SQLite/dev-fallback documentation

Files:
- README.md
- docs/local_runtime_layout.md
- docs/architecture/configuration.md
- docs/architecture/overview.md
- docs/architecture/data-model.md

Relevant markers:
- README.md:50 describes PostgreSQL with SQLite fallback or quickstart.
- README.md:190 starts a SQLite development setup section.
- README.md:356 describes AUTH_DATABASE_URL as PostgreSQL or SQLite.
- docs/architecture/configuration.md:48 and 97 show SQLite defaults for AUTH_DATABASE_URL.
- docs/architecture/configuration.md:107-108 documents SQLite dev fallback explicitly.
- docs/architecture/overview.md:11 describes SQLite as a dev fallback.
- docs/architecture/data-model.md:8 describes PostgreSQL or SQLite in the same application model.

Why legacy:
- These documents preserve earlier or mixed narratives that do not match the current governance direction for auth/core data.

Role details:
- documentation role: historical setup guidance and architecture narrative

## Dangerous

### Auth fallback in container entrypoint

Files:
- scripts/docker-entrypoint.sh

Relevant markers:
- scripts/docker-entrypoint.sh:10 accepts either AUTH_DATABASE_URL or DATABASE_URL for PostgreSQL detection.
- scripts/docker-entrypoint.sh:46 falls back from AUTH_DATABASE_URL to DATABASE_URL to sqlite:///data/db/auth.db.

Why dangerous:
- This keeps both a legacy variable path and a forbidden SQLite auth fallback alive in a container bootstrap path.

Role details:
- script role: container bootstrap and DB initialization

### Auth migration script defaults to SQLite

Files:
- scripts/apply_auth_migration.py

Relevant markers:
- scripts/apply_auth_migration.py:4 documents SQLite as the default path.
- scripts/apply_auth_migration.py:25 defines DEFAULT_DB = ROOT / data / db / auth.db.
- scripts/apply_auth_migration.py:154-156 makes sqlite the default engine.
- scripts/apply_auth_migration.py:170-171 executes the SQLite migration path when the default engine is used.

Why dangerous:
- The script still defaults auth migration behavior to SQLite instead of forcing explicit PostgreSQL selection for auth/core.

Role details:
- script role: auth schema migration entry point

### Admin bootstrap script keeps SQLite fallback

Files:
- scripts/create_initial_admin.py

Relevant markers:
- scripts/create_initial_admin.py:34-35 defaults --db to data/db/auth.db.
- scripts/create_initial_admin.py:67-68 builds AUTH_DATABASE_URL from sqlite when the env var is absent.

Why dangerous:
- This preserves a forbidden SQLite fallback for an auth-related administrative workflow.

Role details:
- script role: initial admin bootstrap helper

### Password reset script keeps SQLite fallback

Files:
- scripts/reset_user_password.py

Relevant markers:
- scripts/reset_user_password.py:15 documents AUTH_DATABASE_URL defaulting to sqlite:///data/db/auth.db.
- scripts/reset_user_password.py:72-74 constructs that same SQLite fallback in code.

Why dangerous:
- This preserves a forbidden SQLite fallback for an auth-related recovery workflow.

Role details:
- script role: password reset helper for existing users

### Implicit BLS_CORPUS default to index

Files:
- src/app/config/__init__.py
- src/app/extensions/http_client.py
- scripts/dev-start.ps1

Relevant markers:
- src/app/config/__init__.py:73 defaults BLS_CORPUS to index.
- src/app/extensions/http_client.py:38 defaults BLS_CORPUS to index.
- scripts/dev-start.ps1:148-149 sets BLS_CORPUS to index if missing.

Why dangerous:
- These paths violate the rule that BLS_CORPUS must always be explicit and never guessed.
- They can silently point the app at the wrong BlackLab corpus.

Role details:
- variable: BLS_CORPUS
- helper role: build_bls_corpus_path in src/app/extensions/http_client.py

### Mixed auth variable usage in runtime wiring

Files:
- infra/docker-compose.dev.yml
- infra/docker-compose.prod.yml
- scripts/docker-entrypoint.sh

Relevant markers:
- infra/docker-compose.dev.yml:51-52 sets AUTH_DATABASE_URL and DATABASE_URL together.
- infra/docker-compose.prod.yml:58-59 sets AUTH_DATABASE_URL and DATABASE_URL together.
- scripts/docker-entrypoint.sh:10 and 46 consume both variable names.

Why dangerous:
- Parallel variable usage obscures the real source of truth for auth and core DB access.

Role details:
- variables: AUTH_DATABASE_URL and DATABASE_URL

### Conflicting development guidance in docs and helper surfaces

Files:
- README.md
- docs/architecture/configuration.md
- docs/operations/local-dev.md
- Makefile

Relevant markers:
- README.md:190 and 356 continue to document SQLite auth usage.
- docs/architecture/configuration.md:107-108 and 167 continue to document SQLite defaults and fallback.
- docs/operations/local-dev.md:70 documents a different local Postgres DSN shape than the canonical dev scripts.
- Makefile:84-89 defines dev-sqlite and sqlite-auth helper targets.

Why dangerous:
- These paths make it easy for agents or operators to choose a non-canonical or forbidden auth path.

Role details:
- script role: Makefile convenience targets
- documentation role: competing dev setup guidance

## Redundant

### Parallel dev stack definitions

Files:
- docker-compose.dev-postgres.yml
- infra/docker-compose.dev.yml

Relevant markers:
- docker-compose.dev-postgres.yml defines a DB-plus-BlackLab dev stack.
- infra/docker-compose.dev.yml defines an app-plus-DB-plus-BlackLab dev stack.

Why redundant:
- Both files define overlapping development entry points and duplicate environment wiring decisions.

Role details:
- compose role: duplicate dev topology definitions

### Parallel BlackLab base URL names

Files:
- src/app/config/__init__.py
- src/app/extensions/http_client.py
- scripts/dev-setup.ps1
- scripts/dev-start.ps1
- README.md

Relevant markers:
- src/app/config/__init__.py:70-71 uses BLS_BASE_URL.
- src/app/extensions/http_client.py:33-34 uses BLS_BASE_URL.
- scripts/dev-setup.ps1:82 uses BLACKLAB_BASE_URL.
- scripts/dev-start.ps1:146-147 set both BLACKLAB_BASE_URL and BLS_BASE_URL.
- README.md:142 documents BLS_BASE_URL while README.md:357 documents BLACKLAB_BASE_URL.

Why redundant:
- The repository still contains two naming systems for the same BlackLab base URL responsibility.

Role details:
- variables: BLS_BASE_URL and BLACKLAB_BASE_URL

### Parallel auth/core database names

Files:
- infra/docker-compose.dev.yml
- infra/docker-compose.prod.yml
- scripts/docker-entrypoint.sh

Relevant markers:
- infra/docker-compose.dev.yml:51-52 sets both AUTH_DATABASE_URL and DATABASE_URL.
- infra/docker-compose.prod.yml:58-59 sets both AUTH_DATABASE_URL and DATABASE_URL.
- scripts/docker-entrypoint.sh:10 and 46 still interpret both names.

Why redundant:
- Two variable names are still used for the same auth/core database target.

Role details:
- variables: AUTH_DATABASE_URL and DATABASE_URL

### Overlapping setup and source-of-truth narratives

Files:
- README.md
- startme.md
- docs/index.md
- docs/general_audit.md
- docs/architecture/configuration.md
- docs/operations/production.md

Relevant markers:
- README.md mixes historical setup, production notes, and legacy references.
- startme.md provides a streamlined local startup narrative.
- docs/index.md acts as a broad documentation entry point.
- docs/general_audit.md collects repository-wide audit evidence.
- docs/architecture/configuration.md and docs/operations/production.md both document operational configuration.

Why redundant:
- These documents overlap in setup and configuration coverage and can diverge when not kept aligned.

Role details:
- documentation role: overlapping operator and developer guidance

## Cross-Category Note

The same file may appear in more than one category.

Example:
- scripts/dev-start.ps1 is active as part of the canonical dev workflow
- scripts/dev-start.ps1 is also dangerous at lines 148-149 because it defaults BLS_CORPUS to index

This is intentional.
Classification is applied to concrete behaviors and roles, not only to whole files.