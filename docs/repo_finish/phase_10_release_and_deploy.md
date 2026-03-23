# Phase 10 - Release And Deploy

Datum: 2026-03-23
Scope: realer Release von `root-lift-integration` nach `main`, echte Deploy-Ausloesung, Live-Beobachtung, Post-Deploy-Verifikation
Status: PARTIAL GO / NO-GO FOR DEPLOY COMPLETION

## Kurzfazit

Der Release nach `main` wurde real ausgefuehrt.

- `origin/main` wurde zuerst auf den echten Merge-Commit `87b9769` gesetzt
- danach wurde ein minimaler Follow-up-Fix `cc8e22e` direkt auf `main` nachgeschoben, um den fehlgeschlagenen Deploy-Pfad zu reparieren
- beide echten Deploy-Runs wurden von GitHub Actions ausgelost
- beide Deploy-Runs sind auf dem self-hosted Runner fehlgeschlagen
- die oeffentlich erreichbare Produktionsinstanz blieb waehrenddessen gesund und funktional erreichbar

Damit ist der Git-Release erfolgt, aber der produktive Rollout des neuen Standes nicht belastbar als erfolgreich verifiziert.

## Ziel

Phase 10 sollte vollstaendig liefern:

1. finaler Release nach `main`
2. automatische Deploy-Ausloesung
3. Beobachtung des Deploy-Runs
4. Verifikation von Server, Container, Health und Smoke-Pfaden
5. Abschlussbewertung ohne stille Annahmen

## Ausgangslage vor Phase 10

Vor Beginn dieser Phase war verifiziert:

- `root-lift-integration` haengt auf normaler Historie unter `origin/main`
- `root-lift-integration` war mergebar
- die release-kritischen Dateien waren lokal geprueft
- `root-lift-integration` war bereits auf `origin/root-lift-integration` gepusht

## Durchgefuehrte Schritte

### 1. Vergleich und Merge-Basis geprueft

GitHub erkannte `main...root-lift-integration` als normalen, automatisch mergebaren Vergleich.

Beobachtet wurde:

- 2 Commits auf der Integrationslinie
- automatische Mergebarkeit
- keine weitere Unrelated-History-Sperre

### 2. Reeller Merge-Commit fuer `main` erzeugt

Lokaler Release-Merge:

- Merge-Commit: `87b97691ac527546a6d69a687a23b42891b4e31a`
- Parents:
  - `9c819e6056bc7c54108c10978e829a3f948dc2b5` (`origin/main` vorher)
  - `75fa0e782b0685243048eb29fdd1b82aa1631baa` (`origin/root-lift-integration`)
- Merge-Message:
  - `Merge branch 'root-lift-integration' into main`

### 3. Release nach `origin/main`

Der Merge-Commit wurde real nach `origin/main` gepusht.

Belegt:

- `origin/main` wechselte von `9c819e6` auf `87b9769`

### 4. Erster echter Deploy-Run ausgelost

GitHub Actions Run:

- Deploy-Run `#124`
- URL: `https://github.com/FTacke/corapan-webapp/actions/runs/23434090726`
- Commit: `87b9769`

Ergebnis:

- Status: failed
- Dauer: 10s
- Job: `Deploy to marele.online.uni-marburg.de`
- Annotation: `Process completed with exit code 127`

Sichtbare Einordnung:

- Fehler im Schritt `Deploy corapan app`
- `Verify deployment` lief danach nicht sinnvoll an
- oeffentliche Web-Ansicht liefert keine vollstaendigen Logs ohne GitHub-Login

### 5. Minimaler Reparaturversuch auf `main`

Da der erste Deploy-Run real fehlgeschlagen war, wurde ein minimaler Follow-up-Fix direkt auf `main` gesetzt.

Commit:

- `cc8e22e5fa94fd99f47f62a2f3ef825ecb210182`
- Message: `Fix production deploy runner shell and remove debug dependency`

Inhalt:

- `.github/workflows/deploy.yml`
  - `shell: bash` fuer den self-hosted Deploy-Job explizit gesetzt
- `app/scripts/deploy_prod.sh`
  - temporaere Debug-Hilfszeilen mit `sha256sum` entfernt

### 6. Zweiter echter Deploy-Run ausgelost

GitHub Actions Run:

- Deploy-Run `#125`
- URL: `https://github.com/FTacke/corapan-webapp/actions/runs/23434738951`
- Commit: `cc8e22e`

Ergebnis:

- Status: failed
- Dauer: 9s
- Job: `Deploy to marele.online.uni-marburg.de`
- Annotation: `Process completed with exit code 127`

Wichtig:

- der Fehler blieb trotz explizitem `bash`-Shell-Default und entferntem Debug-Command bestehen
- damit ist die verbleibende `127`-Quelle sehr wahrscheinlich weiterhin innerhalb des real ausgefuehrten Deploy-Pfads auf dem Runner bzw. auf dem Server selbst zu suchen

## Live-Verifikation der oeffentlichen Instanz

Unabhaengig vom gescheiterten Runner-Deploy wurde die oeffentlich erreichbare Produktion live geprueft.

### HTTP-Health

`https://corapan.hispanistica.com/health`

Antwort:

```json
{"checks":{"auth_db":{"backend":"postgresql","error":null,"ms":1,"ok":true},"blacklab":{"error":null,"ms":6,"ok":true,"url":"http://corapan-blacklab:8080/blacklab-server"},"flask":{"ms":0,"ok":true}},"service":"corapan-web","status":"healthy"}
```

Verifiziert:

- Flask erreichbar
- Auth-DB erreichbar
- Auth-Backend: PostgreSQL
- BlackLab erreichbar
- internes BLS-Ziel: `http://corapan-blacklab:8080/blacklab-server`

### Auth-Health

`https://corapan.hispanistica.com/health/auth`

Antwort:

```json
{"backend":"postgresql","error":null,"ok":true}
```

### BlackLab-Health

`https://corapan.hispanistica.com/health/bls`

Antwort:

```json
{"error":null,"ok":true,"status_code":200,"url":"http://corapan-blacklab:8080/blacklab-server"}
```

### Oeffentliche Seiten-Smoke-Checks

Erfolgreich geladen:

- `/`
- `/search/advanced`
- `/atlas`
- statisches Asset `/static/img/corapan_basic.png`

Damit ist die oeffentliche Instanz funktional erreichbar und liefert zentrale Seiten aus.

## Nicht voll verifizierbar

Folgende Punkte konnten in dieser Umgebung nicht abschliessend belegt werden:

- ob der neue Root-Lift-Stand bereits erfolgreich auf dem Server ausgerollt wurde
- welcher genaue Shell-Befehl im self-hosted Deploy-Run `127` liefert
- aktueller Container-Status direkt auf dem Host
- Mount-Liste direkt per `docker inspect` auf dem Server
- echte In-Container-Runtime-Variablen wie `CONFIG_ROOT` zur Laufzeit im frisch ausgerollten Container

## Warum diese Punkte offen bleiben

### 1. GitHub-Logs nicht voll lesbar ohne Login

Die oeffentlich sichtbare GitHub-Seite zeigt Run-Status, Annotation und Dauer, aber nicht die komplette Shell-Ausgabe des fehlgeschlagenen Deploy-Jobs.

### 2. Direkter SSH-Zugriff aus dieser Umgebung nicht moeglich

Ein read-only SSH-Versuch auf `marele.online.uni-marburg.de:22` endete mit Timeout. Damit war keine direkte Host-Forensik moeglich.

## Wahrscheinliche Lagebewertung

Die oeffentliche Site blieb gesund erreichbar, waehrend beide neuen Deploy-Runs sehr frueh scheiterten.

Das spricht stark fuer folgendes Bild:

- die bisherige Produktion blieb online
- der neue Release wurde in GitHub/Git erfolgreich auf `main` veroeffentlicht
- der automatische Rollout auf dem self-hosted Runner wurde aber nicht erfolgreich abgeschlossen

Diese Bewertung ist plausibel, aber mangels Server-Logzugriff nicht als Vollbeweis zu klassifizieren.

## Finale Bewertung

### Git-Release

GO

- `main` steht real auf dem neuen Stand
- der Integrationszweig wurde erfolgreich in die Hauptlinie ueberfuehrt

### Automatischer Deploy

NO-GO

- zwei reale Deploy-Runs wurden ausgelost
- beide scheiterten frueh mit Exit `127`
- produktiver Rollout des neuen Stands ist damit nicht als erfolgreich verifiziert

### Produktive Erreichbarkeit

GO

- die oeffentliche Instanz antwortet gesund
- Auth und BlackLab sind aus Sicht der HTTP-Healthchecks verfuegbar
- zentrale Seiten laden erfolgreich

## Abschlussstatus Phase 10

Phase 10 ist nur teilweise abgeschlossen.

Abgeschlossen:

- realer Merge nach `main`
- reale Deploy-Ausloesung
- Live-Beobachtung der Runs
- oeffentliche HTTP- und Seiten-Smoke-Checks

Nicht abgeschlossen:

- erfolgreicher automatischer Rollout auf dem self-hosted Runner
- vollstaendige Host-/Container-Forensik des fehlgeschlagenen Deploy-Pfads

## Unmittelbarer naechster operativer Bedarf

Zur endgueltigen Fertigstellung fehlt ein read-only Blick auf einen der folgenden Kanaele:

1. kompletter GitHub Actions Job-Log des Runs `23434738951`
2. direkter Serverzugriff auf den self-hosted Runner / Host

Erst damit laesst sich die verbleibende `127`-Quelle sicher klassifizieren und der automatische Rollout abschliessen.