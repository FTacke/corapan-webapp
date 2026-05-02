# 2026-05-02 Health Rate-Limit Exemption

## What Changed

- `/health` is now explicitly exempt from the global Flask-Limiter rules.
- `/ready` is also explicitly exempt from the global Flask-Limiter rules.
- Health route tests now verify that repeated requests stay at 200 instead of turning into 429 responses.
- A control test still confirms that a normal rate-limited auth route returns 429 after its limit is exceeded.

## Why

The Docker liveness probe for `corapan-web-prod` calls `/health` on a fixed cadence. Because the route was still inside the global rate-limit bucket, the probe could eventually receive 429 responses and mark the container unhealthy even while the app and user-facing routes were working.

## Affected Scope

- Flask public routes in `app/src/app/routes/public.py`
- health/readiness tests in `app/tests/test_auth_flow.py`

## Operational Impact

- Docker healthchecks can call `/health` repeatedly without consuming rate-limit budget.
- Internal readiness checks can call `/ready` without being tripped by the global limiter.
- Regular authenticated or public routes that use Flask-Limiter remain rate-limited.

## Compatibility Notes

- The response payloads for `/health` and `/ready` did not change.
- No auth, corpus, UI, analytics, or deployment wiring was changed.

## Follow-Up

- Keep `/health` reserved for liveness and `/ready` for dependency readiness.