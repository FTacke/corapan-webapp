# 2026-03-24 Footer Release Version

Scope:
- App-Implementierung unter `app/`
- Root-Deploy-Workflow unter `.github/workflows/`

Geaendert:
- zentrale App-Konfiguration liest primär statisch injizierte Release-Metadaten `APP_RELEASE_TAG` und `APP_RELEASE_URL`
- sichtbare Footer-Version wird aus dem Release-Tag `vX.Y.Z` zu `X.Y.Z` normalisiert
- Footer rendert eine zweite, dezente Zeile unter dem Copyright mit klickbarer Versionsangabe
- Produktionsdeploy fragt beim Deploy genau einmal das aktuelle offizielle GitHub-Release ab und gibt Tag/URL statisch an den Container weiter
- lokaler Dev-Start fragt beim Start genau einmal dasselbe Release ab und macht das Verhalten nachvollziehbar testbar

Warum:
- die Webapp soll im Footer immer auf das letzte offizielle GitHub-Release zeigen, ohne bei Seitenaufrufen GitHub live abzufragen
- das Release wird nur im Start-/Deploy-Pfad aufgeloest und danach statisch verwendet

Auswirkung:
- wenn das aktuelle GitHub-Release z. B. `v1.0.1` ist, zeigt der Footer `v1.0.1` und verlinkt auf genau dieses Release
- wenn ein neues GitHub-Release nach einem bereits laufenden Deploy angelegt wird, bleibt die alte Anzeige bestehen, bis erneut deployt oder lokal neu gestartet wird
- wenn das Release beim Start/Deploy nicht aufgeloest werden kann, bleibt die Footer-Zeile bewusst ausgeblendet; die App bleibt nutzbar

Release-Konvention:
- Git-Tag und GitHub Release bleiben `vX.Y.Z`
- die App erhaelt statisch `APP_RELEASE_TAG=vX.Y.Z` und `APP_RELEASE_URL=https://github.com/.../releases/tag/vX.Y.Z`
- die sichtbare Footer-Version wird daraus als `vX.Y.Z` gerendert

Lokaler Test:
- `./scripts/dev-start.ps1` oder `./scripts/dev-setup.ps1` fragen beim Start genau einmal das aktuelle GitHub-Release ab
- nach einem neu angelegten GitHub-Release ist ein neuer lokaler Start noetig, damit sich die Footer-Anzeige aktualisiert

Forensik der bisherigen Unsichtbarkeit:
- Dev war bewusst leer, weil `app/scripts/dev-start.ps1` und `app/scripts/dev-setup.ps1` nur bei explizit gesetztem `APP_VERSION` etwas angezeigt haben
- Prod blieb auf Push-Deploys leer, weil `.github/workflows/deploy.yml` den Wert nur als manuellen Input uebergab und `app/scripts/deploy_prod.sh` sonst nur einen exakten `v*`-Tag auf dem gerade deployten Commit akzeptierte
- dieses Modell passte nicht zur realen Release-Praxis des Repos, in der Releases spaeter fuer einen bereits deployten Stand angelegt werden

Kompatibilitaet:
- kein Runtime-Call zur GitHub-API
- keine harte Template-Version
- kein Default-Release-Link ohne erfolgreich aufgeloestes offizielles Release