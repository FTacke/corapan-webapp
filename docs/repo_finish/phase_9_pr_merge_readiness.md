# Phase 9 - PR Merge Readiness

Datum: 2026-03-23
Workspace: `C:\dev\corapan`
Modus: finaler lokaler PR-/Merge-Readiness-Check fuer `root-lift-integration -> main`, ohne Merge, ohne Push nach `main`, ohne Deploy

## 1. Kurzurteil

Der Branch `root-lift-integration` ist nach dem finalen Readiness-Check **inhaltlich merge-faehig genug fuer einen spaeteren bewussten Release-Merge nach `main`**, sofern die unten genannte Pre-Merge-Checkliste unmittelbar vor dem echten Merge noch einmal bewusst abgearbeitet wird.

Wichtige Einordnung:

- der Branch ist aktuell **nur lokal** vorhanden
- `origin/root-lift-integration` existiert derzeit **nicht**
- es wurde in diesem Run **nicht** gepusht, **nicht** gemerged und **nicht** deployed

Fuer den eigentlichen Merge-Entscheid gilt damit:

### GO FUER SPAETEREN MERGE NACH `main` UNTER KLAREN VORBEDINGUNGEN

Nicht freigegeben ist ein unreflektierter Sofort-Merge ohne die finale Pre-/Post-Merge-Pruefung.

Zusatz aus diesem Run:

- der irrefuehrende lokale Upstream von `root-lift-integration` auf `origin/main` wurde entfernt
- `app/scripts/deploy_prod.sh` honoriert jetzt die vom Workflow gesetzte `GITHUB_SHA`, statt diese blind mit `origin/main` zu ueberschreiben
- `.github/workflows/ci.yml` erzeugt fuer CI jetzt `data/config` statt einer veralteten Root-`config`-Struktur

## 2. Branch- und Remote-Zustand

Geprueft wurden:

- aktueller lokaler Branch
- `main`
- `origin/main`
- `root-lift-integration`
- `origin/root-lift-integration`
- Arbeitsbaumstatus
- Upstream-Tracking

Ergebnis:

- aktueller Branch: `root-lift-integration`
- lokales `main`: `93e0e1a`
- `origin/main`: `9c819e6`
- lokales `root-lift-integration`: Integrationslinie auf Basis von `origin/main`
- `origin/root-lift-integration`: **nicht vorhanden**
- lokaler Upstream fuer `root-lift-integration`: **kein Upstream gesetzt**

Bewertung:

- der Branch-Zustand ist jetzt lokal eindeutig
- es gibt keine unklaren Staged-/Unstaged-/Untracked-Reste nach Abschluss dieses Runs
- fuer einen spaeteren PR muss `root-lift-integration` erst bewusst nach `origin` gepusht werden

Wichtige Git-Klassifikation:

- `root-lift-integration`: **active** lokaler Release-Kandidat
- `origin/root-lift-integration`: **noch nicht vorhanden**
- `root-lift-review`: **active review reference**, aber nicht mehr der spaetere Merge-Mechanismus

Hinweis:

- die verbindliche Phase-7-Referenz war auf dem aktuellen Branch nicht im Arbeitsbaum vorhanden und wurde deshalb gezielt via `git show root-lift-review:docs/repo_finish/phase_7_merge_strategy_check.md` geprueft

## 3. PR-Plausibilitaet

Verglichen wurde `root-lift-integration` gegen `origin/main`.

Gesamtumfang:

- `663 files changed`
- `54499 insertions`
- `2455 deletions`

Bewertung des Diffs:

- der Umfang ist gross, aber fuer einen Root-Lift dieser Art inhaltlich plausibel
- die grossen Bewegungen sind ueberwiegend logisch und werden von Git in vielen Faellen korrekt als Renames erkannt
- Kernmuster des Diffs:
  - Root-App-Dateien wurden nach `app/` verschoben
  - Root-Governance und Root-Workflows liegen jetzt unter `.github/`
  - Root-Wrapper und Root-Dokumentation bleiben bewusst am Repo-Root
  - `maintenance_pipelines/` bleibt Root-Bestandteil

Besonders plausible Rename-/Strukturmuster:

- `config/blacklab/... -> app/config/blacklab/...`
- `infra/... -> app/infra/...`
- `scripts/... -> app/scripts/...`
- `src/... -> app/src/...`
- `static/... -> app/static/...`
- `templates/... -> app/templates/...`
- `tests/... -> app/tests/...`
- `tools/... -> app/tools/...`

Keine Hinweise auf unerwartete Massenverluste in den Kernbestaenden wurden im Diff-Stichprobencheck gefunden.

Manuell besonders anzusehen vor dem echten Merge:

- `.github/workflows/deploy.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/md3-lint.yml`
- `app/scripts/deploy_prod.sh`
- `docker-compose.dev-postgres.yml`
- `README.md`
- `app/README.md`
- `maintenance_pipelines/_2_deploy/*.ps1`

Urteil zur PR-Plausibilitaet:

- **ja**, der PR ist inhaltlich plausibel
- die Hauptlast des Reviews liegt nicht mehr in chaotischer Historie, sondern in bewusster Freigabe eines grossen, aber logisch aufgebauten Struktur-Diffs

## 4. Release-Kernpfade

### a) Deploy-/Runner-Vertrag

Geprueft:

- `.github/workflows/deploy.yml`
- `app/scripts/deploy_prod.sh`

Zustand:

- Workflow deployt weiterhin nur bei `push` auf `main`
- Workflow arbeitet im Server-Checkout unter `/srv/webapps/corapan/app`
- alte `webapp`-Pfadannahme ist im aktiven Deploy-Vertrag entfernt
- `deploy_prod.sh` nutzt `BASE_DIR=/srv/webapps/corapan` und `APP_DIR=${BASE_DIR}/app`
- in diesem Run wurde ein echter Release-Haertungsfix umgesetzt:
  - wenn `GITHUB_SHA` vorhanden ist, resetet `deploy_prod.sh` jetzt auf genau diese SHA statt auf `origin/main`
  - fuer manuelle Aufrufe ausserhalb von GitHub Actions bleibt `origin/main` als Fallback erhalten

Risiko:

- verbleibend mittel, weil Deploy weiterhin ein realer Release-Schritt auf Self-Hosted Runner ist
- technisch aber jetzt sauberer und besser an den Workflow gebunden als zuvor

Merge-blockierend:

- **nein**

### b) App-/Runtime-Struktur

Geprueft:

- `app/`
- `app/src/app/runtime_paths.py`
- `app/src/app/config/__init__.py`
- Root-/App-Struktur im Arbeitsbaum

Zustand:

- `app/` ist der operative versionierte Anwendungsteilbaum
- `data/config` ist die kanonische Runtime-Web-Config
- `app/config/blacklab` ist die versionierte BlackLab-Konfiguration
- `CONFIG_ROOT` wird aktiv als `get_data_root() / "config"` aufgeloest
- keine aktive Root-`config`-Annahme ist mehr im zentralen Runtime-Codepfad vorhanden

Klassifikation konkurrierender Pfade:

- `C:\dev\corapan\data\config`: **active**
- `C:\dev\corapan\app\config\blacklab`: **active**
- `C:\dev\corapan\config`: **legacy/dangerous**
- `app/data`, `app/runtime`: **legacy/dangerous** fuer lokale Runtime-Annahmen

Risiko:

- niedrig

Merge-blockierend:

- **nein**

### c) Dev-/Compose-Vertrag

Geprueft:

- `docker-compose.dev-postgres.yml`
- Root-Wrapper `scripts/dev-start.ps1` und `scripts/dev-setup.ps1`
- `app/scripts/dev-start.ps1`
- minimaler `create_app('development')`-Check

Zustand:

- Root-Compose mountet `./app:/app:ro`
- Root-Compose mountet `./app/config/blacklab:/etc/blacklab:ro`
- Root-Wrapper delegieren sauber an `app/scripts/...`
- `app/scripts/dev-start.ps1` setzt den kanonischen Dev-Runtime-Vertrag auf Workspace-Root + `data/` + `media/`
- `docker compose -f docker-compose.dev-postgres.yml config` rendert erfolgreich
- `create_app('development')` startet mit kanonischen Dev-Variablen erfolgreich
- bestaetigt wurden erneut:
  - `RUNTIME_ROOT = C:\dev\corapan`
  - `CONFIG_ROOT = C:\dev\corapan\data\config`
  - `MEDIA_ROOT = C:\dev\corapan\media`

Zusaetzlicher Workflow-Fix aus diesem Run:

- `.github/workflows/ci.yml` erzeugt fuer CI jetzt `data/config` statt einer veralteten Root-`config`-Struktur

Risiko:

- niedrig bis mittel, weil CI historisch nicht voll belastbar ist
- der reale lokale Dev-Vertrag ist aber konsistent und lauffaehig

Merge-blockierend:

- **nein**

### d) Maintenance-Pipelines

Geprueft:

- `maintenance_pipelines/_2_deploy/README.md`
- `maintenance_pipelines/_2_deploy/README_STATISTICS_DEPLOY.md`
- `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`
- `maintenance_pipelines/_2_deploy/deploy_data.ps1`
- `maintenance_pipelines/_2_deploy/deploy_media.ps1`
- Nested-Git-Indikatoren (`app/.git`, `maintenance_pipelines/.git`, `.gitmodules`)

Zustand:

- kein Nested Git
- keine Submodules
- Orchestratoren loesen standardmaessig `<workspace>/app` auf
- Remote-Zielpfade zeigen auf `/srv/webapps/corapan/...`
- Legacy-Alias `WebappRepoPath` ist weiter vorhanden, aber explizit als Kompatibilitaetsalias und nicht als operativer Zielpfad

Restbefunde:

- einige Kommentare/Bezeichner sprechen noch von `webapp repo`, obwohl die echte Pfadauflosung bereits `app/` nutzt
- das ist unschoen, aber aktuell eher Benennungsdrift als echte Pfadfehlfunktion

Risiko:

- mittel im Bereich Dokumentations-/Kommentarhygiene
- niedrig fuer den aktiven technischen Pfad

Merge-blockierend:

- **nein**

## 5. Root-vs-App-Dokumentation

Geprueft:

- `README.md`
- `app/README.md`

Bewertung:

- Root-README repraesentiert das Gesamtprojekt jetzt ausreichend
- `app/README.md` bleibt sinnvoll technisch fokussiert
- die Rollen von Root-Repo und App-Subtree sind klar getrennt

Keine merge-blockierenden Restfehler gefunden in:

- Root-/App-Rollenbeschreibung
- Runtime-/Deploy-Grundvertrag
- Repo-Struktur-Erklaerung

Manuell kurz gegenzulesen vor dem echten Merge:

- Release-/Deploy-Hinweis in `app/README.md`
- Root-README-Abschnitt zu Runtime and Deploy Contract

Nicht-blockierende Dokumentationsdrift ausserhalb der beiden READMEs:

- `docs/operations/local-dev.md` enthaelt noch alte Port- und Pfadbeispiele
- `docs/operations/production.md` enthaelt noch veraltete Hinweise zu `data/blacklab_export` sowie alte Quellpfad-Referenzen
- `docs/local_runtime_layout.md` ist fuer den heutigen Root-Lift-Vertrag deutlich ueberholt und sollte bis zu einer spaeteren Bereinigung als **legacy/dangerous** behandelt werden

Diese drei Dokumente sind fuer den Merge nicht als harte Blocker gewertet worden, weil die aktiven Compose-/Script-/Codepfade korrekt sind und die kanonischen READMEs den Vertragskern bereits tragen.

## 6. Operative Altpfad-Reste

Gezielt durchsucht wurden aktive bzw. release-relevante Bereiche:

- Workflows
- Deploy-Skripte
- Root- und App-Skripte
- zentrale Runtime-/Config-Codepfade
- Maintenance-Orchestratoren
- zentrale operative Docs

Ergebnis und Klassifikation:

1. `app/scripts/deploy_prod.sh`
   - Befund: vorheriges Ruecksetzen auf `origin/main` unterlief die Workflow-SHA
   - Risiko: falsche oder nicht exakt gepinnte Release-SHA auf dem Runner
   - merge-blockierend: **ja**, vor diesem Run
   - Status: **direkt gefixt**

2. `.github/workflows/ci.yml`
   - Befund: CI erzeugte noch eine veraltete Root-`config`-Struktur statt `data/config`
   - Risiko: Drift zwischen CI-Minimalruntime und kanonischem Runtime-Vertrag
   - merge-blockierend: **nein**, aber release-nah und unnötig riskant
   - Status: **direkt gefixt**

3. `docs/operations/local-dev.md`
   - Befund: alte Ports und alte BlackLab-Pfadbeispiele (`blacklab_export`, `blacklab_index`)
   - Risiko: Dev-Dokumentationsdrift
   - merge-blockierend: **nein**
   - Status: bewusst offengelassen fuer spaetere gezielte Doku-Bereinigung

4. `docs/operations/production.md`
   - Befund: noch alte `data/blacklab_export`-Hinweise und alte Quellpfad-Referenzen
   - Risiko: operative Doku kann an einzelnen Stellen den heutigen BlackLab-Vertrag unscharf erklaeren
   - merge-blockierend: **nein**
   - Status: bewusst offengelassen; vor echtem Release-Merge manuell kurz gegenlesen

5. `docs/local_runtime_layout.md`
   - Befund: stark vor-Root-Lift gepraegt (`corapan-webapp`, alte Runtime-Layouts, alte BlackLab-Unterstruktur)
   - Risiko: gefaehrlich, wenn dieses Dokument als aktive Anleitung statt als Altmaterial gelesen wird
   - merge-blockierend: **nein**, solange es nicht als kanonische Wahrheit verwendet wird
   - Status: bewusst offengelassen; als **legacy/dangerous** klassifiziert

6. `maintenance_pipelines/_2_deploy/*.ps1` und `README.md`
   - Befund: Legacy-Alias `WebappRepoPath` und einzelne Kommentar-/Benennungsreste
   - Risiko: gering, da echte Default-Aufloesung auf `app/` zeigt
   - merge-blockierend: **nein**
   - Status: bewusst offengelassen

## 7. Minimaler Release-Check

Durchgefuehrt wurden ohne Deploy:

```powershell
docker compose -f docker-compose.dev-postgres.yml config
```

und ein minimaler App-Factory-Check mit den kanonischen Dev-Werten aus `scripts/dev-start.ps1`.

Ergebnis:

- Compose-Render erfolgreich
- `create_app('development')` erfolgreich
- Auth-DB-Verbindung erfolgreich verifiziert
- keine offensichtlichen Runtime-Fehler im minimalen Startup

Bestaetigt:

- `CONFIG_ROOT = C:\dev\corapan\data\config`
- App-Factory startet
- `RUNTIME_ROOT = C:\dev\corapan`
- `MEDIA_ROOT = C:\dev\corapan\media`

Damit ist der lokale Minimal-Release-Check fuer den Integrationsstand bestanden.

## 8. Merge-Checkliste

### Unmittelbar VOR dem Merge nach main pruefen:

- `root-lift-integration` bewusst nach `origin` pushen und PR gegen `main` oeffnen
- GitHub PR `Files changed` fuer diese Dateien manuell durchsehen:
  - `.github/workflows/deploy.yml`
  - `.github/workflows/ci.yml`
  - `app/scripts/deploy_prod.sh`
  - `docker-compose.dev-postgres.yml`
  - `README.md`
  - `app/README.md`
  - `maintenance_pipelines/_2_deploy/*.ps1`
- bestaetigen, dass der PR-Zielstand weiterhin `app/` als operative Wahrheit zeigt und kein `webapp/` zurueckkehrt
- bestaetigen, dass `origin/main` weiterhin der bewusst akzeptierte Deploy-Trigger ist
- bestaetigen, dass fuer den Merge-Zeitpunkt der produktive Deploy organisatorisch zulaessig ist

### Unmittelbar NACH dem Merge nach main pruefen:

- GitHub Actions Deploy-Run auf dem Self-Hosted Runner beobachten
- bestaetigen, dass der Deploy auf der gemergten SHA laeuft
- Container `corapan-web-prod` muss laufen
- Mount-Ziele pruefen:
  - `/app/data`
  - `/app/media`
  - `/app/logs`
  - `/app/config`
- Health-Endpunkte pruefen:
  - `/health`
  - `/health/auth`
  - `/health/bls`
- zusaetzlich echten BlackLab-Hits-Smoke-Test gegen `corapan` ausfuehren, nicht nur Root-Readiness
- App-Startseite, Login und mindestens eine Suche fachlich pruefen

## 9. Go / No-Go fuer Merge nach `main`

### GO FUER MERGE NACH `main`

mit folgenden Vorbedingungen:

- `root-lift-integration` wird bewusst nach `origin` gepusht
- der PR gegen `main` wird vor dem Merge manuell auf die oben genannten Kern-Dateien gegengelesen
- der Merge-Zeitpunkt wird als echter Release-Zeitpunkt akzeptiert
- die Post-Merge-Pruefung wird unmittelbar danach aktiv durchgefuehrt

Keine harten Restblocker wurden nach den in diesem Run umgesetzten Fixes mehr gefunden.

Nicht als Blocker, aber als Rest-Risiko bewertet:

- aktive Dokumentationsdrift in einzelnen operativen Docs ausserhalb der kanonischen READMEs
- historisch nur bedingt belastbare CI-Ampel
- der Branch liegt derzeit noch nur lokal und muss fuer einen echten PR erst gepusht werden

---

## Zusatz: Exakt gepruefte Branches und Refs

- aktueller Branch: `root-lift-integration`
- `main`
- `origin/main`
- `root-lift-integration`
- `origin/root-lift-integration`
- Referenz fuer Strategievergleich zusaetzlich: `root-lift-review` / `origin/root-lift-review`

## Zusatz: Push-Status von `root-lift-integration`

- `root-lift-integration` ist aktuell **noch nicht gepusht**
- `origin/root-lift-integration` existiert derzeit **nicht**

## Zusatz: Besonders merge-relevante Dateien

- `.github/workflows/deploy.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/md3-lint.yml`
- `app/scripts/deploy_prod.sh`
- `docker-compose.dev-postgres.yml`
- `README.md`
- `app/README.md`
- `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`
- `maintenance_pipelines/_2_deploy/deploy_data.ps1`
- `maintenance_pipelines/_2_deploy/deploy_media.ps1`

## Zusatz: Zwingende manuelle Kontrolle vor und nach Merge

Vor dem Merge:

- PR-Files-Changed fuer die genannten Kern-Dateien pruefen
- Deploy-Fenster bewusst freigeben
- bestaetigen, dass `main`-Merge jetzt wirklich den Produktiv-Release ausloesen darf

Nach dem Merge:

- Deploy-Run verfolgen
- Container-/Mount-/Health-Pruefung
- echter BlackLab-Hits-Smoke-Test
- kurze fachliche App-Pruefung (Login, Suche, Startseite)