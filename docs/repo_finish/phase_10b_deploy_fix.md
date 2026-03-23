# Phase 10b - Analyse Und Behebung Des Fehlgeschlagenen Deploy-Runs

Datum: 2026-03-23
Scope: Forensik und Minimalfix fuer den fehlgeschlagenen Produktions-Deploy mit Exit Code 127
Status: ROOT-CAUSE FIXED / SUCCESSFUL DEPLOY VERIFIED

## Kurzfazit

Der Exit-127-Fehler wurde auf einen Root-Lift-Pfadbruch im produktiven Deploy-Pfad eingegrenzt und minimal behoben.

- die fehlgeschlagenen Runs `#124` und `#125` brachen beide im Schritt `Deploy corapan app` nach wenigen Sekunden ab
- nach dem Root-Lift lag das echte Deploy-Skript nicht mehr unter `scripts/deploy_prod.sh`, sondern unter `app/scripts/deploy_prod.sh`
- der Workflow rief weiterhin den alten Pfad auf und erzeugte damit sehr wahrscheinlich den Exit `127`
- der Minimalfix wurde mit Commit `d12a713fc77bf58160f23e48908bdeabf2494793` nach `main` gepusht
- der neue Run `#126` (`23435131275`) lief nach dem Fix durch und endete erfolgreich
- die oeffentliche Produktion blieb gesund und eine echte Suche ueber `/search/advanced/data` funktionierte

Damit ist die konkrete `127`-Ursache des Root-Lift-Deploy-Pfads behoben und der reparierte Produktions-Deploy als erfolgreich verifiziert.

## 1. Fehlersymptom

Betroffener Run:

- Run `#125`
- Run-ID `23434738951`
- Job-ID `68169822024`
- Workflow: `Deploy to Production`
- Runner: `corapan-prod`
- Label: `self-hosted`

Beobachtetes Verhalten:

- Status: `failed`
- Dauer: etwa 9 Sekunden
- fehlgeschlagener Schritt: `Deploy corapan app`
- Folge: `Verify deployment` blieb aus bzw. wurde nicht erfolgreich ausgefuehrt
- sichtbare GitHub-Annotation: `Process completed with exit code 127.`

Der vorherige Run `#124` zeigte dasselbe Muster:

- Run-ID `23434090726`
- Job-ID `68167625028`
- Dauer: etwa 10 Sekunden
- gleicher fehlschlagender Schritt
- gleiche Exit-127-Annotation

## 2. Log-Analyse

### 2.1 Verfuegbare und nicht verfuegbare Logquellen

Aus dieser Umgebung waren vollstaendige Raw-Logs des Jobs nicht anonym abrufbar.

- GitHub Actions HTML zeigte Status, Steps und Dauer
- die Raw-Logs der Actions-API waren ohne Login nicht lesbar und lieferten `403`
- direkter SSH-Zugriff auf den Host stand hier nicht belastbar zur Verfuegung

Damit war keine vollstaendige Shell-Ausgabe des fehlschlagenden Kommandos sichtbar. Trotzdem reichte die Kombination aus Workflow, Job-Metadaten, Dateibaum und historischem Vergleich aus, um die reale Fehlerquelle einzugrenzen.

### 2.2 Exakt sichtbarer Fehlerkontext

Sicher belegt war:

- Fehlerort: Schritt `Deploy corapan app`
- Runner: self-hosted `corapan-prod`
- Fehlerklasse: Exit `127`
- Zeitpunkt: unmittelbar nach Start des Deploy-Schritts

Der Fehler trat also vor jeder spaeteren Verifikation auf. Das spricht fuer einen fruehen Pfad- oder Kommandoauflosungsfehler.

### 2.3 Historischer Vergleich

Der letzte erfolgreiche Produktions-Deploy vor dem Root-Lift war:

- Run-ID `23409436349`
- gleicher Runner `corapan-prod`

Damit war ein genereller Runner-Ausfall unwahrscheinlich. Die Abweichung musste im geaenderten Checkout- und Dateipfadmodell des Releases liegen.

## 3. Ursache

### 3.1 Root-Lift-Pfadbruch zwischen Checkout-Root und App-Subtree

Nach dem Root-Lift gilt auf dem Produktionshost:

- Git-Checkout-Root: `/srv/webapps/corapan/app`
- versionierter App-Subtree: `/srv/webapps/corapan/app/app`

Im neuen `main`-Stand existieren die produktiven Dateien unter:

- Deploy-Skript: `app/scripts/deploy_prod.sh`
- Compose-Datei: `app/infra/docker-compose.prod.yml`

Der Workflow rief jedoch weiter den alten Pfad auf:

```bash
cd /srv/webapps/corapan/app
git fetch --prune origin
git reset --hard "${GITHUB_SHA}"
bash scripts/deploy_prod.sh
```

Unter dem neuen Layout gibt es an dieser Stelle kein `scripts/deploy_prod.sh` mehr. Genau dieses Muster passt zu einem fruehen Exit `127` im Deploy-Schritt.

### 3.2 Runner-Umgebung

Direkte Vollforensik des Runners war ohne vollstaendige Logs nicht moeglich. Beobachtbar und durch Workflow plus Deploy-Skript abgesichert war jedoch:

- self-hosted Runner `corapan-prod`
- Bash-basierter Deploy-Job
- Linux-artige Zielpfade unter `/srv/webapps/...`
- `git` und `docker` muessen auf dem Runner verfuegbar sein, weil der Deploy-Pfad genau darauf basiert
- `app/scripts/deploy_prod.sh` prueft Compose-Verfuegbarkeit explizit ueber `docker compose` oder einen Compose-V2-kompatiblen Wrapper

Der relevante Ausfall passte nicht zu einer spaeteren Compose- oder Docker-Pruefung, sondern zu der veralteten Skriptpfad-Aufloesung direkt im Workflow.

## 4. Implementierter Fix

### 4.1 Workflow-Fix

In `.github/workflows/deploy.yml` wurde der Skriptaufruf minimal korrigiert.

Alt:

```bash
bash scripts/deploy_prod.sh
```

Neu:

```bash
bash app/scripts/deploy_prod.sh
```

### 4.2 Deploy-Skript-Fix

In `app/scripts/deploy_prod.sh` wurde das Root-Lift-Layout explizit modelliert.

Neu eingefuehrt:

```bash
CHECKOUT_DIR="${BASE_DIR}/app"
APP_DIR="${CHECKOUT_DIR}/app"
```

Wesentliche Wirkung:

- Git-Operationen laufen im Checkout-Root
- die Compose-Datei wird weiterhin im App-Subtree aufgeloest
- der Kommentar- und Usage-Text beschreibt nun ebenfalls das reale Layout

### 4.3 Commit und Push

Der Minimalfix wurde mit folgendem Commit nach `main` gepusht:

- Commit: `d12a713fc77bf58160f23e48908bdeabf2494793`
- Message: `Fix deploy path after root-lift checkout layout`

## 5. Neuer Deploy-Run

Der Push von `d12a713` loeste automatisch einen neuen Deploy-Run aus:

- Run `#126`
- Run-ID `23435131275`
- Job-ID `68171170952`
- Runner: `corapan-prod`

Final beobachtet:

- Gesamtstatus: `completed`
- Conclusion: `success`
- Laufzeit: von `2026-03-23T11:30:14Z` bis `2026-03-23T11:32:06Z`
- `Set up job`: erfolgreich abgeschlossen
- `Deploy corapan app`: erfolgreich abgeschlossen
- `Verify deployment`: erfolgreich abgeschlossen

Entscheidender Unterschied zu den Fehlruns `#124` und `#125`:

- der Job starb nicht mehr nach etwa 9 bis 10 Sekunden mit Exit `127`
- stattdessen lief der Deploy-Schritt weiter

Diese Abweichung war zuerst die zentrale Indikation fuer den behobenen Pfadfehler. Die spaetere API-Abfrage bestaetigte anschliessend den erfolgreichen Abschluss des gesamten Runs.

## 6. Ergebnis

### 6.1 Live-Health nach dem Fix

`https://corapan.hispanistica.com/health`

```json
{"checks":{"auth_db":{"backend":"postgresql","error":null,"ms":1,"ok":true},"blacklab":{"error":null,"ms":6,"ok":true,"url":"http://corapan-blacklab:8080/blacklab-server"},"flask":{"ms":0,"ok":true}},"service":"corapan-web","status":"healthy"}
```

`https://corapan.hispanistica.com/health/auth`

```json
{"backend":"postgresql","error":null,"ok":true}
```

`https://corapan.hispanistica.com/health/bls`

```json
{"error":null,"ok":true,"status_code":200,"url":"http://corapan-blacklab:8080/blacklab-server"}
```

### 6.2 Echte Suche

Die geforderte echte Suchverifikation wurde ueber den Live-Endpunkt ausgefuehrt:

- `/search/advanced/data?draw=1&start=0&length=1&query=de`

Beobachtetes Ergebnis:

- Anfrage lieferte ein reales JSON-Ergebnis
- BlackLab-Antwort enthielt Trefferstatistik `hits: 72035`
- mindestens ein echter Treffer wurde ausgegeben
- der erste Treffer enthielt Token `de`

Damit ist nicht nur die Startseite oder ein statischer Healthcheck verifiziert, sondern ein realer Suchpfad mit BlackLab-Anbindung.

## 7. Finaler Status

### Exit-127-Ursache

BEHOBEN

- die reale Root-Cause war ein veralteter Skriptpfad im Deploy-Workflow nach dem Root-Lift
- der Fix ist minimal, direkt und auf den Deploy-Pfad beschraenkt

### Produktionsfunktion aus HTTP-Sicht

GO

- Health-Endpunkte antworten gesund
- Auth-DB ist ok
- BlackLab ist ok
- echte Suche funktioniert

### Gesamt-Deploy-Run `#126`

GO

- der fruehe Exit-127-Fehler ist verschwunden
- der reparierte Run `23435131275` wurde als `completed` mit `conclusion: success` verifiziert
- der Produktions-Deploy blieb damit nicht nur stabil im Lauf, sondern schloss erfolgreich ab

### Gesamtbewertung Phase 10b

Phase 10b hat das geforderte Hauptziel erreicht:

- den fehlgeschlagenen Exit-127-Deploy exakt genug lokalisiert
- minimal repariert
- den Reparatureffekt am neuen Run sichtbar gemacht
- die oeffentliche Produktion inklusive echter Suche verifiziert

Offen bleibt aus Phase-10b-Sicht kein technischer Deploy-Blocker mehr. Die weitere Arbeit ist reine Abschluss- und Bereinigungsarbeit im Repository.