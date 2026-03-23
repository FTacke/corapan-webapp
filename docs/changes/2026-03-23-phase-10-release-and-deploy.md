# 2026-03-23 - Phase 10 Release And Deploy Execution

## Was passiert ist

- `root-lift-integration` wurde real nach `main` ueberfuehrt
- Merge-Commit `87b9769` wurde nach `origin/main` gepusht
- der automatische Deploy-Run `23434090726` wurde ausgelost und schlug mit Exit `127` fehl
- anschliessend wurde der minimale Follow-up-Fix `cc8e22e` auf `main` gepusht
- der zweite Deploy-Run `23434738951` wurde ausgelost und schlug ebenfalls mit Exit `127` fehl

## Repo-Aenderungen waehrend Phase 10

- `.github/workflows/deploy.yml`
  - self-hosted Deploy-Job auf explizites `bash` gestellt
- `app/scripts/deploy_prod.sh`
  - temporaere Debug-Abhaengigkeit entfernt

## Beobachteter Produktionszustand

- `https://corapan.hispanistica.com/health` meldete weiter `healthy`
- `https://corapan.hispanistica.com/health/auth` meldete PostgreSQL `ok`
- `https://corapan.hispanistica.com/health/bls` meldete BlackLab `ok`
- Startseite, Advanced Search, Atlas und statische Assets waren erreichbar

## Ergebnis

Der Git-Release ist erfolgt, aber der automatische Rollout auf dem self-hosted Runner ist in Phase 10 nicht erfolgreich abgeschlossen worden.

## Offener Rest

Die verbleibende `127`-Quelle im Deploy-Pfad muss mit vollstaendigen Job-Logs oder direktem Serverzugriff forensisch geklaert werden.