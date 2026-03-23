# 2026-03-23 - Phase 10b Deploy Path Fix

## Was passiert ist

- die fehlgeschlagenen Deploy-Runs `23434090726` und `23434738951` wurden auf einen Root-Lift-Pfadbruch im Produktions-Workflow eingegrenzt
- `.github/workflows/deploy.yml` rief noch `bash scripts/deploy_prod.sh` auf, obwohl das echte Skript nach dem Root-Lift unter `app/scripts/deploy_prod.sh` liegt
- `app/scripts/deploy_prod.sh` wurde auf das neue Checkout-Root plus App-Subtree-Modell umgestellt
- der Minimalfix wurde als Commit `d12a713` nach `main` gepusht

## Repo-Aenderungen

- `.github/workflows/deploy.yml`
  - Skriptaufruf von `bash scripts/deploy_prod.sh` auf `bash app/scripts/deploy_prod.sh` umgestellt
- `app/scripts/deploy_prod.sh`
  - `CHECKOUT_DIR` und `APP_DIR` getrennt modelliert
  - Git arbeitet im Checkout-Root, Compose-Datei bleibt im App-Subtree
  - Kommentar- und Usage-Text auf das reale Produktionslayout angepasst

## Verifikation

- neuer Deploy-Run `23435131275` wurde final als `completed` mit `conclusion: success` verifiziert
- der vorherige Sofort-Fehler mit Exit `127` trat nicht mehr auf
- `https://corapan.hispanistica.com/health` blieb `healthy`
- `https://corapan.hispanistica.com/health/auth` meldete PostgreSQL `ok`
- `https://corapan.hispanistica.com/health/bls` meldete BlackLab `ok`
- eine echte Suche ueber `/search/advanced/data?draw=1&start=0&length=1&query=de` lieferte reale Treffer

## Ergebnis

Der konkrete Exit-127-Fehler des Root-Lift-Deploy-Pfads ist behoben. Der reparierte Produktions-Deploy auf Run `23435131275` wurde erfolgreich abgeschlossen.