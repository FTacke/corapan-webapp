# Repo Verification of Prod Cutover Plan

Datum: 2026-03-21
Welle: Uebergang 4 -> 5
Bezug:
- [2026-03-21_prod_reality_audit.md](2026-03-21_prod_reality_audit.md)
- [2026-03-21_cutover_recovery_plan.md](2026-03-21_cutover_recovery_plan.md)

## 1. Kurzfazit

Repo-seitig traegt der aktuelle Stand den Welle-4-Cutover-Plan nur teilweise.

Das Repo sabotiert den Plan nicht dadurch, dass es aktiv wieder auf Legacy-BlackLab-Pfade umbiegt. Die produktionsrelevanten BlackLab-Helfer zeigen bereits auf die kanonische Zielstruktur unter `/srv/webapps/corapan/data/blacklab`.

Die entscheidenden Schwaechen liegen an anderer Stelle:

- `scripts/deploy_prod.sh` deployt nicht strikt die vom Workflow gepinnte SHA, sondern resetet erneut auf `origin/main`
- `scripts/deploy_prod.sh` recreated den gesamten Compose-Stack und prueft danach nur Basis-Mounts plus `/health`
- diese Validierung ist fuer den definierten Cutover zu schwach, weil weder `docmeta.jsonl` noch die BlackLab-Suchfunktion fachlich geprueft werden
- `scripts/blacklab/run_bls_prod.sh` startet BlackLab auf dem richtigen kanonischen Pfad, validiert aber nur Root-Readiness statt Corpora- oder Hits-Funktion

Damit ist der Plan repo-seitig nicht unbrauchbar, aber vor dem naechsten Push noch nicht hart genug abgesichert.

## 2. Verifikation von `scripts/deploy_prod.sh`

### Beobachtet im Repo

Das Skript fuehrt tatsaechlich folgende Schritte aus:

1. Compose-Implementation auf dem Zielhost aufloesen
2. `git fetch origin`
3. `git reset --hard origin/main`
4. Legacy-Container `corapan-webapp` ggf. entfernen
5. `docker compose --env-file ... -f infra/docker-compose.prod.yml up -d --force-recreate --build`
6. pruefen, ob `corapan-web-prod` laeuft
7. nur diese Container-Ziel-Mounts pruefen:
   - `/app/data`
   - `/app/media`
   - `/app/logs`
   - `/app/config`
8. Write-Test in `/app/data/stats_temp`
9. `/health` mit Retries pruefen

Destruktive oder risikorelevante Operationen:

- `git reset --hard origin/main`
- `docker compose up -d --force-recreate --build`

Nicht beobachtet in `deploy_prod.sh`:

- kein `docker compose down`
- kein `docker rm` fuer DB oder Web ausser dem expliziten Legacy-Container
- kein direkter Eingriff in `data/blacklab/*`
- kein direkter Eingriff in `runtime/`, `config/`, `media/`-Hostpfade ausser deren Nutzung als Compose-Mountquellen
- kein direkter Eingriff in Datenvolumes oder Postgres-Volume-Loeschung

### Abgeleitetes Risiko

1. **SHA-Pinning wird unterlaufen**

Der echte Deploy-Workflow setzt vor dem Skript bereits auf `${GITHUB_SHA}` zurueck. `deploy_prod.sh` hebelt diese Festlegung anschliessend wieder aus und deployed stattdessen stumpf `origin/main`.

Fuer einen kontrollierten Cutover ist das riskant, weil die serverseitige Ausfuehrung damit nicht mehr exakt an die vom Workflow ausgeloeste SHA gebunden ist.

2. **Vollstack-Recreate statt enger Deploy-Reihenfolge**

Das Skript zieht nicht nur `web`, sondern den gesamten Compose-Stack mit `--force-recreate` hoch. Damit ist der operative Recovery-Pfad `db -> web` zwar repo-seitig moeglich, aber nicht die Logik des Standard-Deploys.

3. **Validierung zu schwach fuer Welle 4**

Der Welle-4-Plan verlangt vor und nach Deploy mehr als Basis-Health:

- `docmeta.jsonl` auf dem kanonischen Exportpfad muss existieren
- BlackLab muss `corapan` auf dem Corpora-Endpunkt liefern
- Search plus Metadaten muessen fachlich funktionieren

`deploy_prod.sh` prueft davon nichts.

4. **Kein aktiver Rueckfall auf Legacy-BlackLab-Pfade**

Positiv: das Skript selbst fasst BlackLab-Hostpfade nicht direkt an. Es kippt den Plan also nicht aktiv zurueck auf `blacklab_index` oder `blacklab_export`.

### Empfohlene Massnahme

- `deploy_prod.sh` vor dem naechsten Push anpassen:
  - kein zusaetzlicher `git reset --hard origin/main` innerhalb des Skripts
  - Preflight auf kanonische Export-/Index-Zielpfade ergaenzen
  - Post-Deploy-Fachchecks fuer `docmeta.jsonl`, `/health/auth`, `/health/bls` und Search+Metadaten ergaenzen

## 3. Verifikation der BlackLab-Produktionsskripte

### Beobachtet im Repo

#### `scripts/blacklab/run_bls_prod.sh`

Das Skript nimmt produktiv an:

- `INDEX_DIR=/srv/webapps/corapan/data/blacklab/index`
- `CONFIG_DIR=/srv/webapps/corapan/app/config/blacklab`
- Containername `corapan-blacklab`
- Docker-Netz `corapan-network-prod`

Damit passt die zentrale Pfadannahme des Skripts zum Welle-4-Cutover-Ziel.

Das Skript stoppt und entfernt den vorhandenen BlackLab-Container, startet ihn neu und prueft danach nur:

- ob der Container laeuft
- ob `http://localhost:8081/blacklab-server/` antwortet
- ob die Root-Antwort irgendwie `corapan` enthaelt

#### `scripts/blacklab/build_blacklab_index_prod.sh`

Dieses Skript ist absichtlich deaktiviert und bricht sofort ab. Das ist mit Welle 4 kompatibel, weil diese Welle gerade **keinen** produktiven Neu-Build vorsieht.

#### `scripts/deploy_sync/publish_blacklab_index.ps1`

Der Publisher nutzt ueber `scripts/deploy_sync/_lib/ssh.ps1` den kanonischen Remote-Root:

- `BlackLabDataRoot=/srv/webapps/corapan/data/blacklab`

Er validiert den hochgeladenen Index serverseitig gegen den Corpora-Endpunkt und fuehrt den atomaren Swap unter `.../data/blacklab/index` aus. Damit ist seine Pfadrealitaet bereits auf dem Zielmodell der Welle 4.

### Abgeleitetes Risiko

1. **`run_bls_prod.sh` ist pfadseitig kompatibel, validierungsseitig aber zu schwach**

Das Skript startet BlackLab auf dem richtigen Zielpfad, aber seine Erfolgskriterien sind schwacher als im Cutover-Plan:

- Root-Readiness statt `corpora/?outputformat=json`
- kein echter Hits-Test

2. **Veraltete Operator-Hinweise in `run_bls_prod.sh`**

Bei fehlendem Index verweist das Skript noch auf `build_blacklab_index_prod.sh first`, obwohl genau dieses Skript absichtlich deaktiviert ist. Das ist keine Pfad-Sabotage, aber ein produktionsrelevanter Fehlhinweis.

3. **Publisher und Cutover-Ziel sind konsistent**

Der bestehende Publisher kippt nicht in Altpfade. Im Gegenteil: er ist bereits auf `data/blacklab/index` ausgerichtet. Das ist fuer die Welle-4-Entscheidung positiv.

### Empfohlene Massnahme

- `run_bls_prod.sh` vor dem naechsten Push erweitern:
  - nach Start mindestens Corpora-Check gegen `/blacklab-server/corpora/?outputformat=json`
  - optional zusaetzlicher Hits-Smoke-Test gegen `corapan`
  - veralteten Hinweis auf `build_blacklab_index_prod.sh` entfernen oder auf den echten Publish-/Cutover-Weg korrigieren

## 4. Verifikation der Auth-/DB-Deploy-Annahmen

### Beobachtet im Repo

#### Compose- und Startup-Logik

In `infra/docker-compose.prod.yml` gilt produktiv:

- `db` ist PostgreSQL mit Healthcheck `pg_isready`
- `web` hat `depends_on: db: condition: service_healthy`
- `web` setzt `AUTH_DATABASE_URL` auf PostgreSQL innerhalb des Compose-Netzes
- `web` setzt zusaetzlich noch das Legacy-Env `DATABASE_URL`

Im Docker-Entrypoint gilt:

- ohne `AUTH_DATABASE_URL` startet die App nicht
- wenn `AUTH_DATABASE_URL` nicht mit `postgresql` beginnt, startet die App nicht
- der Entrypoint wartet mit `pg_isready` auf den DB-Host
- Tabellen werden initialisiert
- optional wird ein Initial-Admin angelegt

In `src/app/config/__init__.py` gilt:

- `AUTH_DATABASE_URL` ist Pflicht
- kein SQLite-Fallback fuer Auth/Core
- `BLS_CORPUS` ist Pflicht

In `src/app/routes/public.py` gilt:

- `/health` wird nur `200`, wenn Flask plus Auth-DB ok sind
- BlackLab darf fuer `/health` ausfallen und trotzdem bleibt der Status `degraded` mit HTTP `200`
- `/health/auth` ist ein separater harter Auth-Check
- `/health/bls` ist ein separater BlackLab-Diagnosepfad

#### Weitere Repo-Realitaet

`scripts/setup_prod_db.py` akzeptiert weiterhin `DATABASE_URL` oder `AUTH_DATABASE_URL` und beschreibt `DATABASE_URL` noch als legitime Quelle. Dieser Helper ist nicht Teil des aktiven Deploy-Pfads, bleibt aber eine repo-seitige Legacy-Realitaet.

### Abgeleitetes Risiko

1. **Recovery-Pfad `db -> web` ist repo-seitig plausibel**

Das Compose-`depends_on`, der PostgreSQL-Healthcheck und der Entrypoint-Wait machen den in Welle 4 beschriebenen Recovery-Weg technisch plausibel.

2. **Kein stiller SQLite-Rueckfall im aktiven Produktionsstart**

Der aktive Produktionspfad startet nicht ohne `AUTH_DATABASE_URL` und akzeptiert dort nicht still `sqlite`. Das steht im Einklang mit dem Recovery-Plan.

3. **Legacy-Variable `DATABASE_URL` bleibt als Nebenrealitaet im Repo vorhanden**

Im aktiven Deploy-Pfad ist das kein unmittelbarer Bruch, weil `AUTH_DATABASE_URL` gesetzt und aktiv benutzt wird. Es bleibt aber eine unnötige Verwechslungsquelle in Compose und Hilfsskripten.

4. **`/health` allein ist kein ausreichender Produktionsbeweis fuer BlackLab**

Weil `/health` bei ausgefallener BlackLab-Anbindung weiterhin `200 degraded` liefern darf, traegt dieser Check den fachlichen Teil des Cutovers nicht.

### Empfohlene Massnahme

- kein zwingender Repo-Eingriff am Auth-Startup noetig
- aber Deploy-Validierung muss `health/auth` explizit pruefen und fuer den BlackLab-Teil ueber `/health` hinausgehen
- `DATABASE_URL` als Legacy in produktionsnahen Hilfsskripten spaeter bereinigen; fuer den naechsten Push ist das kein harter Blocker

## 5. Repo-seitige Bruchstellen gegenueber dem Welle-4-Plan

### Beobachtet im Repo

1. `scripts/deploy_prod.sh` resetet hart auf `origin/main` statt die im Workflow gesetzte SHA unveraendert zu deployen.
2. `scripts/deploy_prod.sh` validiert weder `docmeta.jsonl` noch BlackLab-Corpora noch Search+Metadaten.
3. `scripts/deploy_prod.sh` recreated den gesamten Compose-Stack statt den im Recovery-Plan beschriebenen selektiven `db -> web`-Pfad als Standard zu nutzen.
4. `scripts/blacklab/run_bls_prod.sh` nutzt den richtigen Zielpfad, prueft aber nur Root-Readiness.
5. `scripts/blacklab/run_bls_prod.sh` enthaelt einen falschen Operator-Hinweis auf das deaktivierte `build_blacklab_index_prod.sh`.

### Abgeleitetes Risiko

- Der Cutover kann operatorisch korrekt vorbereitet sein und trotzdem repo-seitig mit zu schwacher Gruen-Pruefung als erfolgreich gelten.
- Ein erfolgreicher Deploy kann fachlich defekt bleiben, wenn Export/docmeta oder BlackLab-Suche nach dem Cutover nicht wirklich funktionieren.
- Das SHA-Modell fuer einen kontrollierten Push/Deploy ist derzeit unnötig aufgeweicht.

### Empfohlene Massnahme

- die genannten Punkte vor dem naechsten Push repo-seitig haerten

## 6. Konkrete Massnahmen vor dem naechsten Push

Nur die direkt aus der Verifikation folgenden Massnahmen:

1. **`deploy_prod.sh` anpassen**
   - den internen `git reset --hard origin/main` entfernen oder auf die bereits gesetzte Deploy-SHA umstellen

2. **Preflight-Checks in `deploy_prod.sh` ergaenzen**
   - `test -s /srv/webapps/corapan/data/blacklab/export/docmeta.jsonl`
   - nicht-leeren kanonischen Indexpfad pruefen
   - BlackLab-Config-Datei pruefen

3. **Post-Deploy-Smoke-Tests in `deploy_prod.sh` ergaenzen**
   - `curl -fsS http://127.0.0.1:6000/health/auth`
   - `curl -fsS http://127.0.0.1:6000/health/bls`
   - `curl -fsS http://127.0.0.1:8081/blacklab-server/corpora/?outputformat=json | grep -q '"corapan"'`
   - Search+docmeta-Smoke-Test gemäss Welle-4-Plan

4. **`run_bls_prod.sh` haerten**
   - Corpora-Check statt nur Root-Readiness
   - Operator-Hinweis auf den echten Cutover-/Publish-Weg korrigieren

5. **Runbook/Doku ergaenzen oder angleichen**
   - klarstellen, dass `deploy_prod.sh` allein den Welle-4-Fachnachweis nicht fuehrt, solange die obigen Checks fehlen

## 7. Kompatibilitaetsurteil

**bedingt kompatibel**

Begruendung:

- Die repo-seitigen Produktionspfade fuer BlackLab sind bereits auf das kanonische Zielmodell ausgerichtet.
- Auth/Postgres verhalten sich repo-seitig fail-fast und ohne stillen SQLite-Rueckfall.
- Aber `deploy_prod.sh` ist fuer den Welle-4-Cutover noch zu schwach und deployt nicht strikt die Workflow-SHA.

Solange diese zwei Klassen von Problemen nicht behoben sind,

- **traegt** das Repo den Cutover nicht sauber genug,
- **sabotiert** ihn aber auch nicht aktiv durch Rueckfall auf Legacy-Pfade.