# 2026-03-24 Footer Release Version

Scope:
- App-Implementierung unter `app/`
- Root-Deploy-Workflow unter `.github/workflows/`

Geaendert:
- zentrale App-Konfiguration liest `APP_VERSION` aus der Umgebung und normalisiert optional ein einzelnes fuehrendes `v`
- Release-Link wird aus derselben Version als `.../releases/tag/vX.Y.Z` gebaut
- Footer rendert eine zweite, dezente Zeile unter dem Copyright mit klickbarer Versionsangabe
- Produktionsdeploy gibt `APP_VERSION` statisch pro Rollout an den Container weiter
- lokaler Dev-Start dokumentiert und signalisiert, ob die Footer-Version aktiv ist

Warum:
- die Webapp soll die deployte Version sichtbar machen, ohne bei jedem Request GitHub live abzufragen
- `APP_VERSION` bleibt die einzige Laufzeitquelle fuer die Anzeige und den Release-Link

Auswirkung:
- wenn `APP_VERSION=1.1.0` gesetzt ist, zeigt der Footer `v1.1.0` und verlinkt auf das GitHub-Release `v1.1.0`
- wenn `APP_VERSION` fehlt, bleibt die Footer-Zeile bewusst ausgeblendet; die App bleibt nutzbar

Release-Konvention:
- interne Laufzeitvariable: `APP_VERSION=1.1.0`
- Git-Tag und GitHub Release: `v1.1.0`
- der Deploy-Pfad bevorzugt einen explizit gesetzten `APP_VERSION`-Wert und faellt sonst auf einen exakten `v*`-Tag auf dem deployten Commit zurueck

Lokaler Test:
- PowerShell: `$env:APP_VERSION = "1.1.0"`
- danach `./scripts/dev-start.ps1` im Workspace-Root oder `./scripts/dev-start.ps1` unter `app/`

Kompatibilitaet:
- kein Runtime-Call zur GitHub-API
- keine harte Template-Version
- kein Default-Release-Link ohne gesetzte Version