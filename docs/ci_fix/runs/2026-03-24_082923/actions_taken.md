# Actions Taken

Code/Test:
- `app/src/app/__init__.py`
  - argon2-Versionsabfrage auf `importlib.metadata` umgestellt
  - Template-`now` auf timezone-aware Helper umgestellt
- `app/tests/test_privacy_page.py`
  - timezone-aware `now`-Helper eingefuehrt
- `app/tests/test_advanced_api_quick.py`
  - von impliziten Fast-Tests zu expliziten `live`-Smoke-Checks umgebaut
  - echte Assertions statt Rueckgabewerte
- `app/src/app/config/__init__.py`
  - operativen Statistik-Hinweis aus pytest-Imports herausgenommen
- `app/pyproject.toml`
  - gezielter pytest-Filter fuer bekannte Passlib-Deprecation
- `app/scripts/check_structure.py`
  - Allowlist fuer den aktuellen App-Root erweitert (`AGENTS.md`, `requirements*.in`, `requirements-dev.txt`, `uv.lock`, `tmp/`)
- `.github/workflows/ci.yml`
  - `migration-postgres` auf `tests/test_ci_auth_smoke.py` als reinen Auth-/Postgres-Smoke eingegrenzt
- `app/tests/test_advanced_datatables_results.py`
  - explizit als `live` und `data` klassifiziert

Governance/Dokumentation:
- Root-`AGENTS.md` neu angelegt
- `app/AGENTS.md` erweitert
- `.github/copilot-instructions.md` erweitert
- relevante Skillfiles fuer Config-Validierung und Change-Dokumentation erweitert
- `docs/ci_fix/agent_integration.md` neu angelegt