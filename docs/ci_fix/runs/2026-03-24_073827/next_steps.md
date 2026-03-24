# Next Steps

1. Aendere den Branch-Stand remote und starte die aktualisierte GitHub-CI.
2. Verifiziere `fast-checks`, `auth-hash-compat` und `migration-postgres` als erste Pflichtgates.
3. Starte `playwright-e2e` manuell per `workflow_dispatch` und pruefe, ob der Postgres-basierte E2E-Seed stabil ist.
4. Wenn `migration-postgres` bei `tests/test_advanced_datatables_results.py` nicht sauber skippt, entscheide zwischen BlackLab-Service im Job oder expliziter `live`-Markierung.
5. Bereinige nachgelagerte Testwarnungen (`advanced_api_quick` return-Werte, Deprecation-Warnungen) in einem Folge-Run.

Blocker:
- kein lokaler Docker-Daemon fuer vollstaendige Postgres-/Playwright-Repros
- kein `gh` fuer direkte Run-Abfrage oder gezieltes Rerun

Offene Entscheidungen:
- Soll `playwright-e2e` kuenftig nur manuell bleiben oder spaeter als nightly laufen?
- Soll `md3-lint` rein optional bleiben oder bei PRs gegen UI-Pfade weiterhin verpflichtend sein?
- Soll der historische SQLite-E2E-Helfer spaeter komplett aus Scripts/Makefile entfernt werden?
