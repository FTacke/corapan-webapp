# 2026-05-01 Health and Readiness Split

## What Changed

- `/health` is now a liveness-only endpoint that confirms the Flask app responds and returns a minimal JSON payload.
- `/ready` is a new readiness endpoint that checks the auth database and BlackLab separately.
- Auth DB failures now produce `unhealthy`; BlackLab failures produce `degraded` so the service can stay up while search is impaired.
- Readiness failures now log the failing subcheck, exception class, redacted message, and elapsed time or timeout.
- Auth DB startup logging no longer prints the full engine URL.

## Why

The previous `/health` route mixed liveness and readiness concerns. That allowed transient dependency issues to surface as Docker `health=unhealthy` even when the app itself was still responding and user-facing HTTP routes were reachable.

## Affected Scope

- Flask public routes in `app/src/app/routes/public.py`
- auth DB startup logging in `app/src/app/__init__.py`
- health/readiness tests in `app/tests/test_auth_flow.py`
- Docker liveness probe comments in `app/Dockerfile`, `app/infra/docker-compose.dev.yml`, and `app/infra/docker-compose.prod.yml`

## Operational Impact

- Docker healthchecks continue to use `/health`, but that endpoint is now a true liveness probe.
- Production deployments can watch `/ready` for dependency state without conflating it with container liveness.
- BlackLab outages now surface as degraded readiness instead of container death.
- Auth DB outages still fail readiness and remain operationally critical.

## Compatibility Notes

- Existing Docker healthcheck wiring stays on `/health`, so no compose or runtime reconfiguration is required to adopt the split.
- Existing diagnostic endpoints `/health/auth` and `/health/bls` remain available.
- The response shape of `/health` changed intentionally; any external consumer expecting dependency details should switch to `/ready`.

## Follow-Up

- Point any external readiness monitors at `/ready` if they need dependency state.
- Keep `/health` reserved for liveness-only checks.