# 2026-04-28 Optional GoatCounter In Global Layout

## What Changed

- added optional `GOATCOUNTER_URL` config support in the Flask app config and shared Jinja context
- rendered GoatCounter exactly once in `app/templates/base.html` when `GOATCOUNTER_URL` is set
- extended the production compose environment pass-through so the container can receive `GOATCOUNTER_URL`
- extended the CSP header conditionally so GoatCounter can load `https://gc.zgo.at/count.js` and send events to the configured GoatCounter origin

## Why

The repository already has its own analytics flow for anonymous first-party usage tracking. GoatCounter was requested as an additional, optional third-party pageview tracker without changing, replacing, or merging the existing analytics implementation.

## Existing Analytics Left Unchanged

- frontend analytics bootstrap remains in `app/static/js/main.js`
- analytics event transport remains in `app/static/js/modules/analytics.js`
- analytics backend endpoints remain in `app/src/app/routes/analytics.py`

No existing analytics code path was removed, rewritten, or disabled.

## Affected Scope

- shared Flask config and Jinja context
- global base template used by normal rendered pages
- production compose environment wiring under `app/infra/docker-compose.prod.yml`

## Operational Impact

- dev and test stay off by default because `GOATCOUNTER_URL` is unset unless explicitly provided
- production can enable GoatCounter by setting `GOATCOUNTER_URL=https://corapan.goatcounter.com/count`
- for the canonical production Docker Compose path, set `GOATCOUNTER_URL` in the operator-managed environment source consumed by deploys, then restart the web stack
- if a systemd-managed deployment exists outside the canonical compose path, the service environment can use:

  `Environment="GOATCOUNTER_URL=https://corapan.goatcounter.com/count"`

  followed by:

  `sudo systemctl daemon-reload`

  `sudo systemctl restart <corapan-service>`

## Compatibility Notes

- GoatCounter is only rendered when configured, so local dev and tests do not emit third-party traffic by default
- CSP allowances are only widened when GoatCounter is enabled
- no Nginx, database, BlackLab, auth, or first-party analytics behavior changed

## Follow-Up

- set `GOATCOUNTER_URL` in the active production environment source before the next deploy if GoatCounter should be enabled on `https://corapan.hispanistica.com`