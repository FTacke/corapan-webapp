# Next Steps

1. Git-Stand committen und nach `origin/main` pushen.
2. Den neuen GitHub-Run fuer `fast-checks`, `auth-hash-compat` und `migration-postgres` auswerten.
3. `playwright-e2e` gezielt per `workflow_dispatch` starten und separat bewerten.
4. Falls `tests/test_advanced_datatables_results.py` im Postgres-Smoke nicht robust skippt, den Test klar als service-/live-gebunden klassifizieren oder den Job gezielt um den benoetigten Service erweitern.
5. Danach `docs/ci_fix/STATUS.md` von gelb auf gruen umstellen, soweit die Remote-Runs dies belegen.