# Final Safe Prod Deploy Runbook

Datum: 2026-03-21
Status: operative Referenz fuer den naechsten echten produktiven Push
Verbindlich fuer: `webapp/` als Git-Quelle und `/srv/webapps/corapan/app` als Server-Ziel

## 1. Kurzfazit

Dieses Dokument ersetzt fuer den naechsten produktiven Push alle nebeneinanderstehenden Teilwahrheiten aus Audit, Cutover-Plan und Maintenance-Abstimmung.

Die finale operative Wahrheit lautet:

1. Der erste produktive Cutover ist ein einmaliger Server-Cutover auf die kanonischen BlackLab-Pfade unter `/srv/webapps/corapan/data/blacklab`.
2. Fuer diesen Erstlauf werden weder lokaler BlackLab-Export noch lokaler BlackLab-Publish als Teil des Pflichtablaufs verwendet.
3. Der komplette serverseitige Cutover muss vor dem Git-Push abgeschlossen sein.
4. Der Git-Push ist der Trigger fuer den eigentlichen Web-/DB-Deploy. Nach dem Push darf bis zum Abschluss der Verifikation nichts mehr parallel an BlackLab, Data oder Media laufen.
5. Der Routinebetrieb nach erfolgreichem Cutover folgt einem anderen Ablauf als der Erstlauf.

## 2. Geltungsbereich

### Erstlauf

Dies ist der einmalige initiale produktive Cutover fuer den naechsten echten Push.

Merkmale des Erstlaufs:

1. Produktiver BlackLab-Index wird von `/srv/webapps/corapan/data/blacklab_index` nach `/srv/webapps/corapan/data/blacklab/index` ueberfuehrt.
2. `docmeta.jsonl` und der Export-Baum werden aus der Legacy-Quelle `/srv/webapps/corapan/runtime/corapan/data/blacklab_export/` nach `/srv/webapps/corapan/data/blacklab/export/` kopiert.
3. Es erfolgt kein neuer lokaler Export- oder Publish-Lauf als Pflichtbestandteil dieses Runs.
4. `deploy_prod.sh` wird erst nach abgeschlossenem serverseitigem Cutover durch den Push ausgeloest.

### Folgeprozess

Dies ist der Ablauf fuer spaetere Routine-Deploys nach erfolgreich abgeschlossenem Erstlauf.

Merkmale des Folgeprozesses:

1. Die produktive BlackLab-Wahrheit bleibt `/srv/webapps/corapan/data/blacklab/index`.
2. Die produktive Export-Wahrheit bleibt `/srv/webapps/corapan/data/blacklab/export`.
3. Lokale Maintenance-Skripte werden nur nach Artefaktklasse eingesetzt und in fester Reihenfolge.
4. Auch im Routinebetrieb gilt: kein paralleler Export, Publish, Data-Deploy oder Media-Deploy waehrend des push-getriggerten Server-Deploys.

## 3. Phase A – Vorbereitung vor dem Push

### Erstlauf

1. Der Operator stellt lokal sicher, dass genau der freizugebende Commit im echten Repo `webapp/` vorliegt.
2. Der Operator fuehrt fuer den Erstlauf keine der folgenden lokalen Maintenance-Skripte aus:
   - `maintenance_pipelines/_1_blacklab/blacklab_export.py`
   - `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`
   - `maintenance_pipelines/_2_deploy/deploy_data.ps1`
   - `maintenance_pipelines/_2_deploy/deploy_media.ps1`
3. Der Operator bestaetigt, dass der Erstlauf kein lokales Neu-Building von BlackLab-Artefakten beinhaltet, sondern den serverseitigen Cutover der bereits produktiv verwendeten Legacy-Artefakte.
4. Vor dem Push muessen lokal folgende Vorbedingungen erfuellt sein:
   - der freizugebende Commit ist final
   - es gibt keinen zweiten Operator-Run fuer Export, Publish, Data oder Media
   - der Operator hat SSH-Zugriff auf den Produktivserver
   - der Operator verfuegt ueber gueltige Auth-Testdaten fuer den finalen Login- und Refresh-Smoke-Test
5. Vor dem Push muessen serverseitig folgende Artefakte vorhanden oder vorbereitbar sein:
   - `/srv/webapps/corapan/config/passwords.env`
   - `/srv/webapps/corapan/app/config/blacklab/blacklab-server.yaml`
   - `/srv/webapps/corapan/data/blacklab/`
   - `/srv/webapps/corapan/runtime/corapan/data/blacklab_export/`
   - `/srv/webapps/corapan/data/blacklab_index/`
6. Vor dem Push muessen serverseitig folgende Zustaende geprueft werden:

```bash
test -f /srv/webapps/corapan/config/passwords.env
test -f /srv/webapps/corapan/app/config/blacklab/blacklab-server.yaml
test -s /srv/webapps/corapan/runtime/corapan/data/blacklab_export/docmeta.jsonl
find /srv/webapps/corapan/data/blacklab_index -mindepth 1 -maxdepth 1 | grep -q .
```

### Folgeprozess

Der Folgeprozess haengt von der Art der zu veroefentlichenden Artefakte ab.

1. Wenn nur App-Code deployt wird, laufen vor dem Push keine Maintenance-Skripte.
2. Wenn neue BlackLab-Inhalte veroefentlicht werden muessen, laufen vor dem Push zwingend und seriell:
   1. `maintenance_pipelines/_1_blacklab/blacklab_export.py`
   2. `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`
3. Wenn nur Runtime-Daten oder Media nachgezogen werden muessen, laufen `deploy_data.ps1` und `deploy_media.ps1` nicht vor dem Push, sondern erst nach erfolgreichem Deploy und erfolgreicher Phase D.
4. Auch im Folgeprozess gilt: kein Parallelbetrieb zwischen BlackLab-Publish und dem push-getriggerten App-Deploy.

## 4. Phase B – Push-Freigabe

### Erstlauf

Der Push ist erst freigegeben, wenn alle folgenden Bedingungen gleichzeitig erfuellt sind:

1. Die gesamte Phase A ist abgeschlossen.
2. Der serverseitige Erstlauf-Cutover aus Phase C.1 bis Phase C.3 ist vollstaendig abgeschlossen.
3. BlackLab laeuft vor dem Push bereits auf `/srv/webapps/corapan/data/blacklab/index`.
4. Der kanonische Exportpfad `/srv/webapps/corapan/data/blacklab/export/docmeta.jsonl` ist befuellt.
5. Der Legacy-Indexpfad `/srv/webapps/corapan/data/blacklab_index` bleibt unveraendert als Rollback-Anker erhalten.
6. Die Legacy-Exportquelle `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` bleibt unveraendert als Rollback-Anker erhalten.
7. Der Predeploy-Commit-Marker wurde serverseitig geschrieben.

Der Push bleibt No-Go, wenn einer der folgenden Punkte zutrifft:

1. `docmeta.jsonl` fehlt am kanonischen Exportpfad.
2. BlackLab laeuft weiterhin auf dem Legacy-Pfad `blacklab_index`.
3. Der neue kanonische Indexpfad ist leer oder nicht validierbar.
4. Es existiert kein `PREDEPLOY_SHA`-Marker.
5. Ein Maintenance-Skript laeuft noch oder soll parallel zum Deploy-Fenster gestartet werden.

### Folgeprozess

Der Push ist im Routinebetrieb nur dann freigegeben, wenn die zur Release-Art gehoerenden Pflichtschritte abgeschlossen sind:

1. App-only-Release: keine zusaetzlichen Maintenance-Schritte offen.
2. App plus BlackLab-Release: Export und Publish sind vor dem Push erfolgreich abgeschlossen.
3. Data- oder Media-Nachzuege sind fuer nachgelagerte Ausfuehrung vorgemerkt, aber noch nicht gestartet.

### Verbindliche Aufloesung des Push-vs-Deploy-Widerspruchs

Es gibt im aktuellen Modell keinen sicheren manuellen Operator-Zwischenraum zwischen Git-Push und Server-Deploy, weil der Push den Deploy ausloest.

Deshalb gilt verbindlich:

1. Alles, was vor `deploy_prod.sh` abgeschlossen sein muss, muss vor dem Push erledigt sein.
2. Nach dem Push werden keine serverseitigen Cutover-Schritte, keine Maintenance-Skripte und keine BlackLab-Eingriffe mehr gestartet.

## 5. Phase C – Server-Cutover / Deploy

### Erstlauf

#### C.1 Vor dem Push den Predeploy-Marker sichern

```bash
cd /srv/webapps/corapan/app
PREDEPLOY_SHA="$(git rev-parse HEAD)"
echo "$PREDEPLOY_SHA" | tee /srv/webapps/corapan/logs/predeploy_sha_2026-03-21.txt
```

#### C.2 Vor dem Push die kanonischen Zielpfade vorbereiten

```bash
chown -R hrzadmin:hrzadmin /srv/webapps/corapan/data/blacklab
chmod 755 /srv/webapps/corapan/data/blacklab
chmod 755 /srv/webapps/corapan/data/blacklab/index
chmod 770 /srv/webapps/corapan/data/blacklab/export
chmod 755 /srv/webapps/corapan/data/blacklab/backups
chmod 770 /srv/webapps/corapan/data/blacklab/quarantine

rsync -aH --delete /srv/webapps/corapan/runtime/corapan/data/blacklab_export/ /srv/webapps/corapan/data/blacklab/export/
test -s /srv/webapps/corapan/data/blacklab/export/docmeta.jsonl

rsync -aH --delete /srv/webapps/corapan/data/blacklab_index/ /srv/webapps/corapan/data/blacklab/index/
find /srv/webapps/corapan/data/blacklab/index -mindepth 1 -maxdepth 1 | grep -q .
```

#### C.3 Vor dem Push BlackLab stoppen und final auf den kanonischen Pfad umstellen

```bash
docker stop corapan-blacklab || true
docker rm corapan-blacklab || true
rsync -aH --delete /srv/webapps/corapan/data/blacklab_index/ /srv/webapps/corapan/data/blacklab/index/
bash /srv/webapps/corapan/app/scripts/blacklab/run_bls_prod.sh
curl -fsS http://127.0.0.1:8081/blacklab-server/corpora/?outputformat=json | grep -q '"corapan"'
```

Ab diesem Punkt gilt verbindlich:

1. `/srv/webapps/corapan/data/blacklab/index` ist die einzige aktive produktive Index-Wahrheit.
2. Es erfolgt kein Schreibzugriff mehr auf diesen Pfad bis zum vollstaendigen Abschluss von Phase D.
3. `publish_blacklab.ps1`, `deploy_data.ps1` und `deploy_media.ps1` bleiben gesperrt.

#### C.4 Erst nach erfolgreichem BlackLab-Cutover den Git-Push ausfuehren

Der Operator fuehrt jetzt den Push des freigegebenen Commits aus.

Der Push ist im aktuellen Modell der Trigger fuer den eigentlichen Web-/DB-Deploy.

#### C.5 Nach dem Push keine Parallelaktion mehr starten

Waehend der Deploy laeuft, ist verboten:

1. BlackLab erneut zu stoppen oder umzubiegen.
2. irgendein Maintenance-Skript zu starten.
3. Data- oder Media-Syncs anzustossen.
4. auf `/srv/webapps/corapan/data/blacklab/index` oder `/srv/webapps/corapan/data/blacklab/export` zu schreiben.

#### C.6 Der eigentliche App-Deploy besteht im push-getriggerten Lauf von `deploy_prod.sh`

Der Runbook-Operator behandelt `deploy_prod.sh` als den automatisch gestarteten Web-/DB-Deploy.

Weil `deploy_prod.sh` selbst die fachlichen BlackLab- und docmeta-Pruefungen nicht ausreichend abdeckt, endet Phase C nicht mit einem erfolgreichen Skriptlauf, sondern erst mit gruener Phase D.

### Folgeprozess

Im Routinebetrieb gilt fuer die Server-Sequenz:

1. Wenn ein BlackLab-Publish Teil des Releases ist, muss er vor dem Push bereits abgeschlossen sein.
2. Der Push loest den Web-/DB-Deploy aus.
3. Waehend des Deploys bleibt jede weitere Maintenance-Aktion gesperrt.
4. Erst nach erfolgreicher Phase D duerfen `deploy_data.ps1` und `deploy_media.ps1` laufen, wenn fuer dieses Release Runtime-Daten oder Media nachgezogen werden muessen.

## 6. Phase D – Post-Deploy-Verifikation

### Erstlauf

Alle folgenden Checks sind Pflicht. Ein einzelner Fehler macht das Ergebnis No-Go.

#### D.1 Technische Checks

```bash
curl -fsS http://127.0.0.1:6000/health
curl -fsS http://127.0.0.1:6000/health/auth
curl -fsS http://127.0.0.1:6000/health/bls
docker inspect corapan-web-prod --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker inspect corapan-db-prod --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker inspect corapan-blacklab --format '{{.State.Status}}'
docker exec corapan-web-prod test -s /app/data/blacklab/export/docmeta.jsonl
```

#### D.2 Fachliche Checks fuer Search plus Metadaten

```bash
curl -fsS 'http://127.0.0.1:6000/search/advanced/data?draw=1&start=0&length=1&q=los' | python3 -c '
import sys, json
payload = json.load(sys.stdin)
assert payload.get("data"), "no search results"
row = payload["data"][0]
assert row.get("country_code"), "country_code missing"
assert row.get("date"), "date missing"
assert "radio" in row, "radio field missing"
print("search+docmeta OK")
'
```

#### D.3 Auth- und Postgres-Checks

```bash
docker exec corapan-db-prod pg_isready -U corapan_app -d corapan_auth
curl -fsS http://127.0.0.1:6000/health/auth

rm -f /tmp/corapan_auth_headers.txt /tmp/corapan_auth_cookies.txt
curl -sS -D /tmp/corapan_auth_headers.txt -o /dev/null \
  -c /tmp/corapan_auth_cookies.txt \
  -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=${OPERATOR_USER}" \
  --data-urlencode "password=${OPERATOR_PASSWORD}" \
  http://127.0.0.1:6000/auth/login
grep -Eq 'HTTP/1\.[01] 303|HTTP/2 303' /tmp/corapan_auth_headers.txt
grep -qi 'set-cookie: refreshToken=' /tmp/corapan_auth_headers.txt
curl -fsS -b /tmp/corapan_auth_cookies.txt -c /tmp/corapan_auth_cookies.txt -X POST http://127.0.0.1:6000/auth/refresh
```

#### D.4 BlackLab- und docmeta-Konsistenz

```bash
curl -fsS http://127.0.0.1:8081/blacklab-server/corpora/?outputformat=json | grep -q '"corapan"'
docker exec corapan-web-prod test -s /app/data/blacklab/export/docmeta.jsonl
test -s /srv/webapps/corapan/data/blacklab/export/docmeta.jsonl
find /srv/webapps/corapan/data/blacklab/index -mindepth 1 -maxdepth 1 | grep -q .
```

### Folgeprozess

Auch im Routinebetrieb bleibt die gleiche Phase D Pflicht.

Ergaenzende Regel:

1. Wenn nach Phase D noch `deploy_data.ps1` oder `deploy_media.ps1` laufen muessen, ist nach jedem dieser Schritte mindestens der technische Health-Check und ein fachlicher Search-Smoke-Test erneut auszufuehren.

## 7. Phase E – Abbruch / Rollback

### Erstlauf

#### E.1 Sofortabbruch vor dem Push

Vor dem Push wird sofort abgebrochen, wenn einer der folgenden Punkte fehlschlaegt:

1. die Kopie von Legacy-Export nach `/srv/webapps/corapan/data/blacklab/export/`
2. der Vorsync oder Finalsync des Legacy-Index nach `/srv/webapps/corapan/data/blacklab/index`
3. der Start von BlackLab auf dem kanonischen Pfad
4. der Corpora-Check gegen `corapan`

In diesem Fall gilt:

1. Es wird nicht gepusht.
2. BlackLab wird sofort auf die Legacy-Realitaet zurueckgesetzt.
3. Weder `deploy_prod.sh` noch irgendein Maintenance-Skript wird gestartet.

#### E.2 Schneller BlackLab-Rollback auf die Legacy-Realitaet

```bash
docker stop corapan-blacklab || true
docker rm corapan-blacklab || true
docker run -d \
  --name corapan-blacklab \
  --restart unless-stopped \
  --network corapan-network-prod \
  -p 8081:8080 \
  -e JAVA_TOOL_OPTIONS='-Xmx2g -Xms512m' \
  -v /srv/webapps/corapan/data/blacklab_index:/data/index/corapan:ro \
  -v /srv/webapps/corapan/app/config/blacklab:/etc/blacklab:ro \
  instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7
curl -fsS http://127.0.0.1:8081/blacklab-server/corpora/?outputformat=json | grep -q '"corapan"'
```

#### E.3 Abbruch nach dem Push oder nach fehlgeschlagenem Deploy

Wenn der Push bereits erfolgt ist und Phase D fehlschlaegt, wird sofort in dieser Reihenfolge zurueckgerollt:

1. BlackLab-Rollback auf den Legacy-Index, falls BlackLab oder Search fachlich fehlschlagen.
2. Web-Rollback auf den Vordeploy-Commit.
3. Postgres-Recovery nur dann, wenn Auth/DB fehlschlagen.

#### E.4 Schneller Web-Rollback auf den Vordeploy-Commit

```bash
cd /srv/webapps/corapan/app
git reset --hard "$(cat /srv/webapps/corapan/logs/predeploy_sha_2026-03-21.txt)"
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d --force-recreate --build db web

curl -fsS http://127.0.0.1:6000/health
curl -fsS http://127.0.0.1:6000/health/auth
docker exec corapan-web-prod test -s /app/data/blacklab/export/docmeta.jsonl
```

#### E.5 Postgres-Recovery nur fuer Auth/DB-Stoerungen

```bash
cd /srv/webapps/corapan/app
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d db
until docker inspect corapan-db-prod --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' | grep -qx healthy; do sleep 2; done
docker exec corapan-db-prod pg_isready -U corapan_app -d corapan_auth
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d web
curl -fsS http://127.0.0.1:6000/health/auth
```

### Folgeprozess

Im Routinebetrieb gelten dieselben Rollback-Regeln.

Zusaetzliche verbindliche Regel:

1. Wenn ein Routine-Release einen neuen BlackLab-Publish enthaelt und Phase D scheitert, wird nicht erneut publisht, bevor der Rollback sauber abgeschlossen und der Fehler klassifiziert wurde.

### Unantastbare Daten im Abbruch- und Rollback-Fall

Folgende Daten duerfen in keinem Abbruch- oder Rollback-Fall geloescht oder blind ersetzt werden:

1. Docker-Volume `corapan_postgres_prod`
2. Legacy-Indexpfad `/srv/webapps/corapan/data/blacklab_index`
3. Legacy-Exportquelle `/srv/webapps/corapan/runtime/corapan/data/blacklab_export`

Verboten sind:

1. `docker compose down -v`
2. Loeschen des Legacy-Indexpfads
3. Loeschen der Legacy-Exportquelle
4. gleichzeitiger Schreibzugriff auf den aktiven BlackLab-Index waehrend BlackLab laeuft

## 8. Verbindliche Operator-Regeln

1. Der Erstlauf ist kein lokaler Export- oder Publish-Run, sondern ein serverseitiger Cutover der bereits produktiv verwendeten Legacy-Artefakte.
2. Fuer den Erstlauf bleiben alle vier Maintenance-Skripte gesperrt.
3. Im Routinebetrieb gilt die Maintenance-Reihenfolge strikt und seriell:
   1. `maintenance_pipelines/_1_blacklab/blacklab_export.py`
   2. `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`
   3. `maintenance_pipelines/_2_deploy/deploy_data.ps1`
   4. `maintenance_pipelines/_2_deploy/deploy_media.ps1`
4. Im Routinebetrieb duerfen Schritt 1 und 2 nur vor dem Push laufen.
5. Im Routinebetrieb duerfen Schritt 3 und 4 nur nach erfolgreicher Phase D laufen.
6. Zwischen Push und Abschluss von Phase D sind keine Maintenance-Skripte erlaubt.
7. BlackLab darf nie auf einem Pfad laufen, waehrend derselbe aktive Pfad gleichzeitig neu beschrieben oder ersetzt wird.
8. `deploy_prod.sh` ist nicht die fachliche Freigabe, sondern nur der technische Web-/DB-Deploy-Schritt. Die Freigabe entsteht erst durch gruene Phase D.
9. Der Erstlauf ist nur dann beendet, wenn BlackLab, docmeta, Search, Auth und Postgres gleichzeitig gruene Ergebnisse liefern.
10. Nach erfolgreichem Erstlauf ist `/srv/webapps/corapan/data/blacklab/index` die einzige produktive BlackLab-Index-Wahrheit.
11. Nach erfolgreichem Erstlauf ist `/srv/webapps/corapan/data/blacklab/export/docmeta.jsonl` die einzige produktive Export-Wahrheit fuer die Web-App.

## 9. Klare Go/No-Go-Freigabe

### Go fuer den initialen produktiven Cutover nur wenn

1. Phase A vollstaendig abgeschlossen ist.
2. Phase C.1 bis Phase C.3 vor dem Push erfolgreich abgeschlossen sind.
3. BlackLab vor dem Push bereits auf `/srv/webapps/corapan/data/blacklab/index` laeuft.
4. Der Push danach erfolgreich den Web-/DB-Deploy ausloest.
5. Phase D ohne Fehler abgeschlossen wird.

### No-Go fuer den initialen produktiven Cutover wenn

1. vor dem Push noch irgendein serverseitiger Cutover-Schritt offen ist.
2. `docmeta.jsonl` nicht am kanonischen Exportpfad liegt.
3. BlackLab nicht auf `data/blacklab/index` umgestellt ist.
4. irgendein Maintenance-Skript noch parallel laufen soll.
5. Phase D nicht vollstaendig gruen ist.

### Go fuer spaetere Routine-Deploys nur wenn

1. der Erstlauf erfolgreich abgeschlossen wurde.
2. die Maintenance-Schritte der jeweiligen Release-Art in der richtigen Phase gelaufen sind.
3. zwischen Push und Abschluss von Phase D keine Parallelaktion erfolgt ist.
4. Phase D vollstaendig gruen ist.

### Schlussfreigabe

Die Freigabe fuer den naechsten echten produktiven Push lautet:

1. No-Go, solange der serverseitige Erstlauf-Cutover nicht vor dem Push abgeschlossen ist.
2. Go genau dann, wenn dieser Runbook-Ablauf ohne Abweichung ausgefuehrt wurde und Phase D vollstaendig gruen ist.