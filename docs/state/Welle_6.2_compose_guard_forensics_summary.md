# Welle 6.2 Compose Guard Forensics Summary

Datum: 2026-03-20
Umgebung: Production deploy path, read-only live forensics plus minimal workflow bootstrap hardening
Scope: forensische Klaerung des weiter auftretenden `KeyError: 'ContainerConfig'` und minimal-invasive Korrektur im direkten Deploy-Pfad

## Ergebnis in Kurzform

Der Compose-Guard aus Welle 6.1 hatte kein belegtes Erkennungsloch.

Der weiterhin auftretende Fehler entstand aus einem Bootstrap-Problem im Deploy-Pfad:

- der GitHub-Workflow fuehrte bereits den neuen Schritt aus:
  - `cd /srv/webapps/corapan/app`
  - `bash scripts/deploy_prod.sh`
- aber `scripts/deploy_prod.sh` wurde dabei zunaechst in der bereits auf dem Server liegenden Version gestartet
- erst innerhalb dieses Skripts erfolgt bisher `git fetch` und `git reset --hard origin/main`

Damit sind Aenderungen an `scripts/deploy_prod.sh` selbst nicht self-applying. Wenn die auf dem Server liegende Skriptversion noch alt ist, laeuft zuerst genau diese alte Version an. Die neue Guard-Logik greift dann fuer diesen Lauf noch nicht.

## Forensische Befunde

### 1. Hat die neue `scripts/deploy_prod.sh` den Server erreicht?

Ja, zum Pruefzeitpunkt lag in `/srv/webapps/corapan/app` die neue Guard-Version vor.

Belegt wurde live:

- `/srv/webapps/corapan/app/scripts/deploy_prod.sh` enthaelt `resolve_compose_cmd()`
- die Datei loggt `Compose command:` und `GitHub Actions:`
- der aktuelle Commit in `/srv/webapps/corapan/app` ist `3358ee6`

### 2. Welche Workflow-Datei lief in den Fehljobs wirklich?

Die Worker-Logs belegen fuer die Fehlruns am `2026-03-20 16:09:49Z` und `2026-03-20 16:25:28Z` den literal ausgefuehrten Run-Step:

```text
cd /srv/webapps/corapan/app
bash scripts/deploy_prod.sh
```

Das ist der neue direkte App-Pfad aus `.github/workflows/deploy.yml`, nicht der alte `${GITHUB_WORKSPACE}`-Pfad.

### 3. Existieren weitere alte Deploy-Artefakte?

Ja.

Im self-hosted Runner-Workspace lag parallel noch ein alter Checkout auf Commit `80cf287` mit:

- alter `.github/workflows/deploy.yml`
- altem `scripts/deploy_prod.sh`
- explizitem `docker-compose`-v1-Pfad

Diese Artefakte sind real und gefaehrlich als Drift-Indikator, aber die Worker-Logs der untersuchten Fehlruns zeigen nicht deren `${GITHUB_WORKSPACE}`-Aufruf, sondern den App-Pfad.

### 4. Trat der Fehler vor oder nach der neuen Compose-Pruefung auf?

Fuer die untersuchten Fehlruns liegt kein erhaltener Step-Console-Block mehr vor, der die eigentlichen `[INFO]`-Zeilen des Shell-Skripts zeigt. Deshalb ist kein direkter Beleg moeglich, ob `Compose command:` im Web-Console-Output erschien oder nicht.

Die Zeitachse macht den Fehlerpfad aber eindeutig genug:

- Guard-Commit `3358ee6` hat `CommitDate: 2026-03-20 16:25:14Z`
- ein fehlgeschlagener Deploy lief bereits `2026-03-20 16:25:28Z`
- der Workflow startet vor dem Skriptaufruf kein `git fetch` fuer `/srv/webapps/corapan/app`

Damit konnte dieser Lauf trotz neuem Workflow noch die vorher auf Disk liegende alte `scripts/deploy_prod.sh` starten.

### 5. Hat `resolve_compose_cmd()` ein Erkennungsloch?

Nicht belegt.

Die gepruefte Guard-Logik blockiert `docker-compose` v1 explizit und akzeptiert `docker-compose` nur bei als V2 erkennbarer Version. In den vorliegenden Befunden gibt es keinen Hinweis darauf, dass die neue Guard-Version gestartet wurde und Compose v1 dennoch durchgelassen hat.

### 6. Kommt der Fehler aus einem anderen Compose-Aufruf?

Im direkten neuen Deploy-Pfad ist kein alternativer Compose-Aufruf vor dem Start von `scripts/deploy_prod.sh` belegt.

Der relevante andere Compose-Pfad ist die alte on-disk-Version von `scripts/deploy_prod.sh` selbst. Genau darin liegt die eigentliche Bootstrap-Luecke.

## Root Cause

Der Deploy-Workflow aktualisierte bisher den Ziel-Checkout `/srv/webapps/corapan/app` nicht vor dem Aufruf von `scripts/deploy_prod.sh`.

Dadurch gilt:

- Workflow-Aenderungen wirken sofort, weil GitHub den neuen Workflow aus dem Push kennt
- Skriptaenderungen in `/srv/webapps/corapan/app/scripts/deploy_prod.sh` wirken nicht sicher im ersten Lauf, weil zuerst die bereits lokal vorhandene Skriptversion gestartet wird

Bei einem Fix, der genau in `scripts/deploy_prod.sh` liegt, entsteht damit ein klassisches Self-Update-Problem.

## Minimaler Fix

`.github/workflows/deploy.yml` wurde minimal erweitert:

```bash
cd /srv/webapps/corapan/app
git fetch --prune origin
git reset --hard "${GITHUB_SHA}"
bash scripts/deploy_prod.sh
```

Wirkung:

- der Ziel-Checkout wird vor dem Skriptstart deterministisch auf den Commit des ausloesenden Workflows gebracht
- die aktuelle `scripts/deploy_prod.sh` laeuft dadurch bereits im ersten betroffenen Deploy
- der Compose-Guard aus Welle 6.1 kann nicht mehr an einer alten on-disk-Skriptversion vorbeilaufen

## Was bewusst nicht geaendert wurde

- keine Compose-Datei
- keine Datenpfade
- keine PostgreSQL/Auth-Logik
- keine Analytics-Logik
- keine BlackLab-Logik
- keine Container-Bereinigung
- keine Runner-Service-Aenderung

## Restrisiko

- Der Fix beseitigt das Bootstrap-Problem fuer Deploy-Skript-Aenderungen.
- Er installiert nicht automatisch Docker Compose V2 auf dem Zielserver.
- Solange auf dem Host nur `docker-compose 1.29.2` existiert, wird ein korrekt aktualisierter Deploy nach Welle 6.1 nun frueh und explizit abbrechen statt spaet mit `KeyError: 'ContainerConfig'` zu scheitern.

## Verifikation

Read-only verifiziert:

- Worker-Logs enthalten fuer die Fehlruns den literalen Step-Inhalt `cd /srv/webapps/corapan/app` plus `bash scripts/deploy_prod.sh`
- `/srv/webapps/corapan/app` und der Runner-Workspace waren auf unterschiedlichen Commits
- der Runner-Workspace hing auf `80cf287`
- `/srv/webapps/corapan/app` stand auf `3358ee6`
- `3358ee6` wurde nur Sekunden vor dem letzten dokumentierten Fehlrun erzeugt

Statische Repo-Verifikation:

- Workflow zieht den Ziel-Checkout jetzt vor dem Skriptaufruf explizit auf `GITHUB_SHA`
- der direkte Deploy-Pfad bleibt auf `.github/workflows/deploy.yml` beschraenkt