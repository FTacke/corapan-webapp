# Prod Cutover Decision & Recovery Plan

Datum: 2026-03-21
Welle: 4 - Wiederherstellbarkeit absichern + Entscheidungsreife herstellen
Bezug: baut auf [2026-03-21_prod_reality_audit.md](2026-03-21_prod_reality_audit.md) auf und ersetzt keine dortigen Beobachtungen

## 1. Kurzfazit

Dieser Run trifft die fuer den naechsten produktiven Deploy verbindlichen Entscheidungen.

Entscheidungslage:

- Es erfolgt **kein weiterer Legacy-Betrieb** fuer BlackLab.
- Es erfolgt **ein echter Prod-Cutover auf die kanonische Struktur** unter `/srv/webapps/corapan/data/blacklab`.
- `docmeta.jsonl` wird **nicht** neu erzeugt und **nicht** verschoben, sondern aus der aktuell gueltigen Legacy-Quelle **kanonisch kopiert**.
- Der Deploy ist erst dann freigegeben, wenn die hier definierten Vorbedingungen und Validierungen vollstaendig gruen sind.

Operative Leitlinie:

- Der aktuelle Legacy-Indexpfad `/srv/webapps/corapan/data/blacklab_index` bleibt fuer diese Welle als **Rollback-Anker unveraendert erhalten**.
- Das bestehende Deploy-Modell bleibt unveraendert:
  - Git-Quelle: `webapp/`
  - Server-Ziel: `/srv/webapps/corapan/app`

## 2. Getroffene Entscheidungen

### 2.1 BlackLab

Verbindliche Entscheidung:

- **Cutover auf `/srv/webapps/corapan/data/blacklab/index` in dieser Welle.**

Begruendung:

- Die stabile Repo-/Publish-Logik arbeitet bereits mit `data/blacklab/index`.
- Der laufende Legacy-Pfad `blacklab_index` ist die Hauptquelle fuer Produktionsdivergenz.
- Weiterbetrieb im Legacy-Modus wuerde den naechsten Deploy erneut in eine Alt-/Neu-Mischrealitaet laufen lassen.

Konkrete Umsetzung:

- Der aktuell produktive Legacy-Index wird **nicht** verschoben.
- Er wird **vor dem Deploy** nach `/srv/webapps/corapan/data/blacklab/index` gespiegelt.
- Danach wird `corapan-blacklab` mit dem bestehenden Startskript [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh) auf den neuen kanonischen Pfad gestartet.

Verbindliche Regel:

- Waehend BlackLab auf einem Indexpfad laeuft, wird auf genau diesem aktiven Pfad **weder publisht noch rsynct noch manuell ersetzt**.

### 2.2 `docmeta.jsonl`

Verbindliche Entscheidung:

- **Kanonische Quellinstanz fuer diese Welle ist die aktuell produktiv befuellte Legacy-Datei**:

```text
/srv/webapps/corapan/runtime/corapan/data/blacklab_export/docmeta.jsonl
```

- Fuer den Cutover wird **der gesamte Export-Baum** aus der Legacy-Quelle nach `/srv/webapps/corapan/data/blacklab/export/` kopiert.
- Es wird **nichts migriert oder geloescht**; die Legacy-Quelle bleibt fuer Rollback und Vergleich bestehen.
- Es wird **nichts neu erzeugt**, solange nicht explizit ein separater Export-Neubau geplant ist.

Begruendung:

- Die Web-App erwartet bereits `/app/data/blacklab/export/docmeta.jsonl`.
- Der dafuer live gemountete Hostpfad ist leer.
- Die Legacy-Quelle enthaelt den produktiv verwendbaren Stand und ist damit die risikoaermste Sofortquelle.

Verbindliche Zielregel:

- Nach dieser Welle ist die produktive Web-Quelle fuer `docmeta.jsonl` ausschliesslich:

```text
/srv/webapps/corapan/data/blacklab/export/docmeta.jsonl
```

### 2.3 Deploy-Validierung

Verbindliche Entscheidung:

- Ein Deploy gilt erst dann als erfolgreich, wenn **alle** der folgenden Gruppen gruen sind:
  1. Datei- und Pfadchecks
  2. Servicechecks
  3. Fachchecks fuer Search plus Metadaten
  4. Auth/Postgres-Checks

#### Verbindliche Datei- und Pfadchecks

Diese Checks muessen vor dem eigentlichen Deploy erfolgreich sein:

```bash
test -f /srv/webapps/corapan/config/passwords.env
test -f /srv/webapps/corapan/app/config/blacklab/blacklab-server.yaml
test -s /srv/webapps/corapan/data/blacklab/export/docmeta.jsonl
find /srv/webapps/corapan/data/blacklab/index -mindepth 1 -maxdepth 1 | grep -q .
```

#### Verbindliche Servicechecks

Diese Checks muessen nach Cutover und nach Deploy erfolgreich sein:

```bash
curl -fsS http://127.0.0.1:8081/blacklab-server/corpora/?outputformat=json | grep -q '"corapan"'
curl -fsS http://127.0.0.1:6000/health
curl -fsS http://127.0.0.1:6000/health/auth
curl -fsS http://127.0.0.1:6000/health/bls
docker inspect corapan-web-prod --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker inspect corapan-db-prod --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker inspect corapan-blacklab --format '{{.State.Status}}'
```

#### Verbindlicher Fachcheck Search plus Metadaten

Der Deploy ist nur gruen, wenn die Web-App die kanonische `docmeta.jsonl` wirklich nutzt und eine echte Suchanfrage Metadaten anreichert.

1. Dateinachweis im laufenden Web-Container:

```bash
docker exec corapan-web-prod test -s /app/data/blacklab/export/docmeta.jsonl
```

2. Search-Smoke-Test mit Metadatenpruefung:

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

### 2.4 Was nicht Teil dieser Welle ist

- Kein neuer Index-Build
- Kein sofortiger produktiver Einsatz von `publish_blacklab_index.ps1` fuer neuen Inhalt
- Keine Loeschung des Legacy-Indexpfads
- Keine Aenderung am Deploy-Zielpfad `/srv/webapps/corapan/app`

## 3. Auth/Postgres Recovery-Plan

Dieser Abschnitt ist der minimale reale Recovery-Pfad, wenn Auth oder Postgres nach Cutover oder Deploy stoert.

### 3.1 Erkennen, dass Auth/DB kaputt ist

Ein Auth/Postgres-Problem liegt vor, wenn **mindestens einer** der folgenden Punkte zutrifft:

```bash
curl -fsS http://127.0.0.1:6000/health/auth
docker inspect corapan-db-prod --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker exec corapan-db-prod pg_isready -U corapan_app -d corapan_auth
```

Fehlerbild:

- `/health/auth` liefert kein `{"ok": true, "backend": "postgresql"}`
- `corapan-db-prod` ist nicht `running healthy`
- `pg_isready` liefert kein positives Ergebnis
- Login gegen `/auth/login` erzeugt 5xx oder keine Session-Cookies

### 3.2 Minimaler Recovery-Pfad fuer Postgres

Verbindliche Regeln:

- Das Docker-Volume `corapan_postgres_prod` wird **nicht geloescht**.
- Es wird **kein** `docker compose down -v` verwendet.
- BlackLab ist fuer Postgres-Recovery nicht relevant und bleibt unberuehrt, solange kein separater BLS-Fehler vorliegt.

#### Recovery-Schritte

1. In das App-Verzeichnis wechseln:

```bash
cd /srv/webapps/corapan/app
```

2. Nur die DB sauber hochziehen:

```bash
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d db
```

3. Warten, bis Postgres healthy ist:

```bash
until docker inspect corapan-db-prod --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' | grep -qx healthy; do sleep 2; done
docker exec corapan-db-prod pg_isready -U corapan_app -d corapan_auth
```

4. Danach erst Web hochziehen bzw. neu anbinden:

```bash
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d web
```

5. Auth-Diagnostik pruefen:

```bash
curl -fsS http://127.0.0.1:6000/health/auth
curl -fsS http://127.0.0.1:6000/health
```

### 3.3 Verifikation, dass Auth wieder funktioniert

Voraussetzung:

- Es existiert ein bekannter produktiver Operator-Account mit Benutzername und Passwort.

Verbindlicher Login-Smoke-Test:

```bash
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
```

Verbindlicher Refresh-Smoke-Test:

```bash
curl -fsS -b /tmp/corapan_auth_cookies.txt -c /tmp/corapan_auth_cookies.txt -X POST http://127.0.0.1:6000/auth/refresh
```

Wenn einer dieser Tests fehlschlaegt:

- Deploy-Ergebnis ist **No-Go**
- zuerst DB wiederherstellen
- danach Web erneut hochziehen

## 4. Cutover-Ablauf

Dieser Ablauf ist ohne Interpretation auszufuehren.

### 4.1 VOR Deploy

#### A. Pre-Deploy Marker sichern

Den aktuellen Web-Commit sichern:

```bash
cd /srv/webapps/corapan/app
PREDEPLOY_SHA="$(git rev-parse HEAD)"
echo "$PREDEPLOY_SHA" | tee /srv/webapps/corapan/logs/predeploy_sha_2026-03-21.txt
```

#### B. Zielrechte herstellen

```bash
chown -R hrzadmin:hrzadmin /srv/webapps/corapan/data/blacklab
chmod 755 /srv/webapps/corapan/data/blacklab
chmod 755 /srv/webapps/corapan/data/blacklab/index
chmod 770 /srv/webapps/corapan/data/blacklab/export
chmod 755 /srv/webapps/corapan/data/blacklab/backups
chmod 770 /srv/webapps/corapan/data/blacklab/quarantine
```

#### C. Export-Baum aus Legacy in die kanonische Struktur kopieren

```bash
rsync -aH --delete /srv/webapps/corapan/runtime/corapan/data/blacklab_export/ /srv/webapps/corapan/data/blacklab/export/
test -s /srv/webapps/corapan/data/blacklab/export/docmeta.jsonl
```

#### D. Aktiven Legacy-Index in den kanonischen Pfad vorsynchronisieren

```bash
rsync -aH --delete /srv/webapps/corapan/data/blacklab_index/ /srv/webapps/corapan/data/blacklab/index/
find /srv/webapps/corapan/data/blacklab/index -mindepth 1 -maxdepth 1 | grep -q .
```

#### E. Vorab-Datei-Checks erzwingen

```bash
test -f /srv/webapps/corapan/config/passwords.env
test -f /srv/webapps/corapan/app/config/blacklab/blacklab-server.yaml
test -s /srv/webapps/corapan/data/blacklab/export/docmeta.jsonl
find /srv/webapps/corapan/data/blacklab/index -mindepth 1 -maxdepth 1 | grep -q .
```

### 4.2 WAEHREND Deploy

#### A. Maintenance-Fenster betreten

Verbindliche Regel:

- Ab diesem Punkt **kein** gleichzeitiger Index-Publish.
- `publish_blacklab_index.ps1` wird waehrend dieses Fensters **nicht** ausgefuehrt.

#### B. BlackLab stoppen, bevor der aktive Indexpfad umgestellt wird

```bash
docker stop corapan-blacklab || true
docker rm corapan-blacklab || true
```

#### C. Finalen Index-Abgleich auf den kanonischen Pfad ausfuehren

```bash
rsync -aH --delete /srv/webapps/corapan/data/blacklab_index/ /srv/webapps/corapan/data/blacklab/index/
```

Verbindliche Regel:

- Ab hier ist `/srv/webapps/corapan/data/blacklab/index` der einzige aktive Zielindex fuer diese Welle.
- Ab hier erfolgt **kein Schreibzugriff** mehr auf diesen Pfad, bis BlackLab erfolgreich laeuft.

#### D. BlackLab auf dem kanonischen Pfad starten

```bash
bash /srv/webapps/corapan/app/scripts/blacklab/run_bls_prod.sh
curl -fsS http://127.0.0.1:8081/blacklab-server/corpora/?outputformat=json | grep -q '"corapan"'
```

#### E. Erst danach Web/DB deployen

```bash
cd /srv/webapps/corapan/app
bash scripts/deploy_prod.sh
```

### 4.3 NACH Deploy

#### A. Technische Checks

```bash
curl -fsS http://127.0.0.1:6000/health
curl -fsS http://127.0.0.1:6000/health/auth
curl -fsS http://127.0.0.1:6000/health/bls
docker inspect corapan-web-prod --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker inspect corapan-db-prod --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker inspect corapan-blacklab --format '{{.State.Status}}'
docker exec corapan-web-prod test -s /app/data/blacklab/export/docmeta.jsonl
```

#### B. Fachchecks Search plus Metadaten

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

#### C. Auth/DB-Verifikation

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

## 5. Rollback-Plan

### 5.1 Grundprinzip

Rollback muss schnell sein und darf keine produktiven Dauerzustandsdaten zerstoeren.

Deshalb gelten diese Verbote:

- `corapan_postgres_prod` nicht loeschen
- kein `docker compose down -v`
- Legacy-Pfad `/srv/webapps/corapan/data/blacklab_index` nicht loeschen
- Legacy-Exportquelle `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` nicht loeschen

### 5.2 Schneller BlackLab-Rollback auf die Legacy-Realitaet

Wenn der neue kanonische BlackLab-Start fehlschlaegt oder fachlich falsch antwortet:

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

### 5.3 Schneller Web-Rollback auf den Vordeploy-Commit

Wichtig:

- `scripts/deploy_prod.sh` ist **kein** schneller Rollback-Mechanismus, solange `origin/main` noch auf dem fehlerhaften Commit steht, weil das Skript immer `git reset --hard origin/main` ausfuehrt.

Deshalb fuer Sofort-Rollback:

```bash
cd /srv/webapps/corapan/app
git reset --hard "$(cat /srv/webapps/corapan/logs/predeploy_sha_2026-03-21.txt)"
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d --force-recreate --build db web
```

Danach sofort pruefen:

```bash
curl -fsS http://127.0.0.1:6000/health
curl -fsS http://127.0.0.1:6000/health/auth
docker exec corapan-web-prod test -s /app/data/blacklab/export/docmeta.jsonl
```

### 5.4 Postgres-Rollback / Recovery

Wenn nur Auth/DB stoert, aber BlackLab und Web-Code an sich korrekt sind:

```bash
cd /srv/webapps/corapan/app
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d db
until docker inspect corapan-db-prod --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' | grep -qx healthy; do sleep 2; done
docker exec corapan-db-prod pg_isready -U corapan_app -d corapan_auth
docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d web
curl -fsS http://127.0.0.1:6000/health/auth
```

## 6. Go/No-Go

### GO nur wenn alle folgenden Bedingungen erfuellt sind

1. `/srv/webapps/corapan/data/blacklab/export/docmeta.jsonl` existiert und ist nicht leer.
2. `/srv/webapps/corapan/data/blacklab/index` ist befuellt.
3. `corapan-blacklab` antwortet nach Start von [scripts/blacklab/run_bls_prod.sh](scripts/blacklab/run_bls_prod.sh) mit Corpus `corapan`.
4. `scripts/deploy_prod.sh` laeuft durch.
5. `/health`, `/health/auth`, `/health/bls` sind gruen.
6. Der Search-Smoke-Test liefert Treffer und Metadatenfelder.
7. Der Auth-Login- und Refresh-Smoke-Test ist gruen.

### NO-GO wenn einer der folgenden Punkte offen bleibt

1. `docmeta.jsonl` fehlt am kanonischen Exportpfad.
2. BlackLab laeuft weiter auf `blacklab_index`, waehrend Web und Tooling bereits auf `data/blacklab/*` zeigen.
3. Der neue kanonische Indexpfad ist leer oder nicht validierbar.
4. Search liefert keine Metadatenanreicherung.
5. `/health/auth` oder Login/Refresh schlagen fehl.
6. Ein Rollback-Anker fehlt:
   - kein `PREDEPLOY_SHA`
   - Legacy-Indexpfad wurde veraendert oder geloescht
   - Postgres-Volume wurde angetastet

## Schlussentscheidung

Die Freigabe fuer den naechsten produktiven Push lautet:

- **NO-GO**, solange der hier definierte Cutover nicht vorab umgesetzt und geprueft ist.
- **GO**, sobald der Cutover exakt nach diesem Plan durchgefuehrt wurde und alle Gate-Checks gruen sind.