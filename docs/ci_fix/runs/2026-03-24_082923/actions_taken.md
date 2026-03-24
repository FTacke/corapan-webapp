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

Governance/Dokumentation:
- Root-`AGENTS.md` neu angelegt
- `app/AGENTS.md` erweitert
- `.github/copilot-instructions.md` erweitert
- relevante Skillfiles fuer Config-Validierung und Change-Dokumentation erweitert
- `docs/ci_fix/agent_integration.md` neu angelegt