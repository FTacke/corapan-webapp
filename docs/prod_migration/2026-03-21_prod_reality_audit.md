# Prod Reality Audit und Cutover-Plan

Datum: 2026-03-21
Modus: read-only Analyse mit Dokumentation

## Kontext

Ziel dieses Runs ist die Beurteilung, ob ein sofortiger Push/Auto-Deploy aus dem jetzt stabilen Dev-/Repo-Stand gegen die aktuelle produktive Serverrealitaet verantwortbar ist.

Wichtig:

- Es geht nicht um weitere Dev-Umbauten.
- Bewertet wird, was auf dem bestehenden Prod-Server real passieren wuerde.
- Massgeblich sind beobachtete Live-Container, aktive Mounts, aktive Hostpfade, aktive Config-Pfade und die aktuell im Repo bzw. im laufenden Web-Container vorhandene Pfadlogik.

## Kurzfazit

Ein sofortiger Blind-Deploy ist aktuell **No-Go**.

Hauptgruende:

1. Die laufende Prod-BlackLab-Instanz liest weiterhin den Legacy-Indexpfad `/srv/webapps/corapan/data/blacklab_index`, waehrend die aktuelle stabile Publish-/Repo-Logik bereits auf die neue kanonische Struktur `/srv/webapps/corapan/data/blacklab/index` zeigt.
2. Die laufende Web-App benutzt bereits den neuen Resolver `.../data/blacklab/export/docmeta.jsonl`, aber der dafuer eingemountete Hostpfad `/srv/webapps/corapan/data/blacklab/export` ist derzeit leer.
3. Das bestehende Auto-Deploy (`scripts/deploy_prod.sh`) validiert zwar Container-Start und `/health`, aber **nicht** den BlackLab-Export-Mount, **nicht** die Existenz von `docmeta.jsonl` und **nicht** die inhaltliche Suchfunktion.
4. Ein Deploy kann daher formal erfolgreich sein, waehrend BlackLab-/Search-Metadaten in einer Alt-/Neu-Mischstruktur verbleiben oder weiter divergieren.

Konsequenz:

- Vor einem echten Deploy ist ein geplanter Prod-Cutover noetig.
- Insbesondere Export/docmeta und aktiver BlackLab-Index muessen serverseitig auf dieselbe kanonische Realitaet gebracht und verifiziert werden.

## Ist-Zustand

### 1. Aktive Compose-/Container-Definitionen

Beobachtet:

- `corapan-web-prod` und `corapan-db-prod` sind Compose-gemanagt.
- Compose-Labels zeigen auf `/srv/webapps/corapan/app/infra/docker-compose.prod.yml`.
- Compose-Projekt: `infra`.
- Compose-Version laut Labels: `2.37.1`.
- `corapan-blacklab` ist **nicht** Compose-gemanagt; am Container wurden keine `com.docker.compose.*`-Labels beobachtet.

Bewertung:

- Web und DB folgen dem aktuellen Compose-Deploymodell.
- BlackLab laeuft weiterhin separat/legacy ausserhalb dieses Deploy-Pfads.

### 2. Aktive Mounts

#### Web-Container `corapan-web-prod`

Beobachtet live:

- `/srv/webapps/corapan/runtime/corapan/data -> /app/data` (rw)
- `/srv/webapps/corapan/runtime/corapan/media -> /app/media` (rw)
- `/srv/webapps/corapan/runtime/corapan/logs -> /app/logs` (rw)
- `/srv/webapps/corapan/runtime/corapan/config -> /app/config` (rw)
- `/srv/webapps/corapan/data/blacklab/export -> /app/data/blacklab/export` (ro)

#### DB-Container `corapan-db-prod`

Beobachtet live:

- Docker-Volume `corapan_postgres_prod -> /var/lib/postgresql/data` (rw)

#### BlackLab-Container `corapan-blacklab`

Beobachtet live:

- `/srv/webapps/corapan/data/blacklab_index -> /data/index/corapan` (ro)
- `/srv/webapps/corapan/app/config/blacklab -> /etc/blacklab` (ro)
- zusaetzlich internes Docker-Volume nach `/data` (rw)

Bewertung:

- Web-App und BlackLab haengen produktiv an unterschiedlichen Hostpfad-Realitaeten.
- Web-App ist bereits teils auf kanonische Exportstruktur gemountet.
- BlackLab ist weiterhin fest auf Legacy-Indexpfad verdrahtet.

### 3. Aktive Config-Pfade

Beobachtet:

- Web-Runtime-Config aktiv unter `/srv/webapps/corapan/runtime/corapan/config`, gemountet nach `/app/config`.
- BlackLab-Config aktiv unter `/srv/webapps/corapan/app/config/blacklab`, gemountet nach `/etc/blacklab`.
- BlackLab-Server-Logs zeigen weiter `Scanning collectionsDir: /data/index`.

Bewertung:

- Die Container-internen Zielpfade sind stabil.
- Der eigentliche Schaltpunkt liegt auf den Host-Mountquellen.

### 4. Aktiver BlackLab-Indexpfad

Beobachtet:

- Laufender BlackLab-Container mountet `/srv/webapps/corapan/data/blacklab_index -> /data/index/corapan`.
- Hostpfad `/srv/webapps/corapan/data/blacklab_index` enthaelt einen aktiven Indexbestand.
- Der neue kanonische Zielpfad `/srv/webapps/corapan/data/blacklab/index` existiert zwar, ist derzeit aber leer.

Bewertung:

- Der aktive Produktionsindex ist heute **nicht** unter `data/blacklab/index`, sondern weiterhin unter `data/blacklab_index`.

### 5. Aktive Auth-/DB-Pfade und Umgebungsvariablen

Beobachtet live im Web-/DB-Container:

- `AUTH_DATABASE_URL=postgresql+psycopg2://corapan_app:***@db:5432/corapan_auth`
- `DATABASE_URL=postgresql+psycopg2://corapan_app:***@db:5432/corapan_auth`
- `BLS_BASE_URL=http://corapan-blacklab:8080/blacklab-server`
- `BLS_CORPUS=corapan`
- `CORAPAN_RUNTIME_ROOT=/app`
- `CORAPAN_MEDIA_ROOT=/app/media`
- `PUBLIC_STATS_DIR=/app/data/public/statistics`
- `STATS_TEMP_DIR=/app/data/stats_temp`

Beobachtet live fuer DB-Storage:

- Postgres-Daten liegen im Docker-Volume `corapan_postgres_prod`.

Zusaetzliche Beobachtung:

- Im laufenden Web-Container sind `FLASK_SECRET_KEY` und `JWT_SECRET_KEY` auf Platzhalterwerte gesetzt (`CHANGE_ME_*`).

Bewertung:

- Auth/DB-Anbindung ist produktiv konsistent innerhalb des Compose-Stacks.
- Die Secret-Beobachtung ist ein separates operatives Sicherheitsproblem, aber nicht der primaere Cutover-Blocker dieses Runs.

### 6. Aktive Web-Pfadlogik im laufenden Container

Beobachtet im laufenden Web-Container:

- `src/app/runtime_paths.py` verwendet fuer `get_docmeta_path()`:

```python
return resolved_runtime_root / "data" / "blacklab" / "export" / "docmeta.jsonl"
```

- `advanced_api.py` laedt `docmeta.jsonl` direkt ueber `get_docmeta_path()` und cached die Daten beim Modulimport.

Zusatzbeobachtung im laufenden Web-Container:

- `/app/data/blacklab/export/` existiert, ist aber leer.
- `/app/data/blacklab/export/docmeta.jsonl` existiert **nicht**.
- Das alte Runtime-Legacy-Verzeichnis `/app/data/blacklab_export/docmeta.jsonl` existiert weiterhin und ist befuellt.

Bewertung:

- Die laufende Web-App ist bereits auf den neuen kanonischen Exportpfad ausgerichtet.
- Die produktive Hostseite liefert fuer genau diesen Pfad derzeit aber noch keinen Inhalt.
- Das System befindet sich damit bereits in einer beobachtbaren Zwischenrealitaet.

## Abweichungen zu Dev bzw. zum stabilen Repo-Verhalten

### Uebereinstimmungen

- Dev-BlackLab-Compose nutzt bereits `./data/blacklab/index -> /data/index/corapan:ro`.
- Repo-/Dev-Tooling nutzt fuer BlackLab-Export und docmeta bereits `data/blacklab/export/...`.
- Die aktuelle Web-Codebasis und der laufende Web-Container erwarten denselben kanonischen docmeta-Pfad.
- `BLS_BASE_URL` und `BLS_CORPUS` sind in Prod konsistent gesetzt.

### Nicht-Uebereinstimmungen

1. **Aktiver Prod-BlackLab-Indexpfad**

- Dev/stabiles Repo: `data/blacklab/index`
- Live-Prod: `/srv/webapps/corapan/data/blacklab_index`

2. **Index-Publish-Ziel vs. Live-BlackLab**

- `scripts/deploy_sync/_lib/ssh.ps1` setzt `BlackLabDataRoot=/srv/webapps/corapan/data/blacklab`.
- `scripts/deploy_sync/publish_blacklab_index.ps1` publisht nach `.../data/blacklab/index`, `.../backups`, `.../quarantine`.
- Live-BlackLab liest aber weiterhin `.../data/blacklab_index`.

3. **Export/docmeta-Quelle**

- Repo-/laufender Web-Code erwartet `/app/data/blacklab/export/docmeta.jsonl`.
- Der dafuer gemountete Hostpfad `/srv/webapps/corapan/data/blacklab/export` ist leer.
- Die echte, befuellte Altquelle liegt noch unter `/srv/webapps/corapan/runtime/corapan/data/blacklab_export/docmeta.jsonl`.

4. **Deploy-Validierung**

- `scripts/deploy_prod.sh` prueft nur `/app/data`, `/app/media`, `/app/logs`, `/app/config` und den Health-Endpunkt.
- Es prueft **nicht** den BlackLab-Export-Mount `/app/data/blacklab/export`.
- Es prueft **nicht** die Existenz von `docmeta.jsonl`.
- Es prueft **nicht** die fachliche Suchfunktion gegen BlackLab.

### Wo ein Deploy jetzt in eine laufende Altstruktur schreiben oder an ihr vorbeilaufen wuerde

1. Ein normaler Web-Deploy baut und startet die Web-App auf Basis des kanonischen Exportpfads, waehrend die befuellten Exportdaten noch im Legacy-Runtime-Pfad liegen.
2. Ein BlackLab-Index-Publish aus dem stabilen Dev-/Repo-Stand schreibt in die neue Struktur `/srv/webapps/corapan/data/blacklab/index`, aber der laufende Prod-BlackLab-Container liest weiter aus `/srv/webapps/corapan/data/blacklab_index`.
3. Ergebnis: App-, Publish- und Live-BlackLab koennen parallel erfolgreich erscheinen, ohne dieselbe Datenrealitaet zu benutzen.

## Was bei blindem Deploy wahrscheinlich brechen oder falsch laufen wuerde

1. **Advanced-Search-Metadaten / docmeta-Anreicherung**

- Sehr wahrscheinlich fachlich defekt oder unvollstaendig, weil `docmeta.jsonl` am neuen aktiven Web-Pfad fehlt.
- Der Deploy wuerde das nicht erkennen, weil `_health` darauf nicht prueft.

2. **BlackLab-Index-Publish nach Deploy**

- Ein Publish in die neue kanonische Struktur wuerde am laufenden Legacy-BlackLab vorbeipublizieren.
- Der Operator koennte also einen erfolgreichen Publish sehen, waehrend Prod weiterhin den alten Index aus `blacklab_index` bedient.

3. **Alt-/Neu-Divergenz**

- Web-App, Exportdaten und BlackLab-Index wuerden in zwei verschiedenen Pfadsystemen weiterdriften.
- Das ist genau die Klasse von Zustand, in der spaeter unsaubere Indexbehandlung oder falsche Rollbacks reale Schaeden verursachen.

4. **Deploy-Erfolg trotz fachlichem Fehlerbild**

- `deploy_prod.sh` kann mit gruener Health-Pruefung enden, obwohl Search-Metadaten oder BlackLab-Datenkopplung falsch sind.

## Welche Punkte aktuell eher unkritisch sind

1. **Auth/DB innerhalb des Compose-Stacks**

- Web und DB sind auf demselben Compose-Netz `corapan-network-prod`.
- `AUTH_DATABASE_URL` zeigt auf den Compose-Service `db`.
- Die Daten liegen in `corapan_postgres_prod` und ueberleben Container-Recreates.
- Risiko bei reinem Web/DB-Recreate daher vergleichsweise niedrig, solange keine Migrations- oder Schema-Aenderung mitkommt.

2. **Web-Runtime-Basis ausserhalb BlackLab**

- Die Basis-Mounts fuer `/app/data`, `/app/media`, `/app/logs`, `/app/config` sind live konsistent und werden vom Deploy explizit geprueft.

3. **BLS-Basis-URL und Corpusname**

- `BLS_BASE_URL=http://corapan-blacklab:8080/blacklab-server` und `BLS_CORPUS=corapan` sind produktiv konsistent.
- Das Problem liegt nicht in URL/Corpusname, sondern im Hostpfad des Index und in der Export/docmeta-Quelle.

## Risikoanalyse

### 1. Auth/DB

Risikoklasse: **mittel**

Begruendung:

- Grundsaetzlich konsistente Compose-Realitaet mit persistentem Docker-Volume.
- `deploy_prod.sh` recreatet jedoch den gesamten Compose-Stack und damit auch den DB-Container.
- Solange keine Migrationswelle Teil des Deploys ist, ist die Wahrscheinlichkeit eines Bruchs begrenzt.
- Offene Security-Auffaelligkeit: Platzhalter-Secrets in Prod.

### 2. BlackLab/Index

Risikoklasse: **hoch**

Begruendung:

- Live-BlackLab liest Legacy-Pfad `blacklab_index`.
- Repo-/Publish-Welt schreibt bereits in `data/blacklab/index`.
- Ein Index-Swap an laufender Instanz darf nicht blind erfolgen.
- Bei jeder Umschaltung oder jedem Ueberschreiben gilt: kein aktiver Index darf waehrend laufendem BlackLab unsauber ersetzt werden.

### 3. Config/Runtime-Root

Risikoklasse: **hoch**

Begruendung:

- `CORAPAN_RUNTIME_ROOT=/app` ist konsistent.
- Der laufende Code erwartet `data/blacklab/export/docmeta.jsonl` unter diesem Root.
- Die dazu gemountete Hostquelle ist derzeit leer.
- Damit liegt bereits jetzt eine produktive Fehlkopplung am Pfadresolver vor.

### 4. Docker-/Mount-Logik

Risikoklasse: **hoch**

Begruendung:

- Web und DB sind Compose-gemanagt, BlackLab nicht.
- Ein Auto-Deploy aktualisiert Web/DB, aber nicht den separaten BlackLab-Container.
- Die neue Exportstruktur ist im Web bereits gemountet; die neue Indexstruktur ist fuer BlackLab noch nicht aktiv.
- Dadurch entsteht eine echte Mischrealitaet ueber zwei Orchestrierungsmodi hinweg.

### 5. Deploy-Skripte / Restart-Reihenfolge

Risikoklasse: **hoch**

Begruendung:

- `deploy_prod.sh` prueft nur oberflaechliche Container-/Health-Aspekte.
- `publish_blacklab_index.ps1` validiert den neuen Index in einem temporären Container und fuehrt dann einen atomaren Swap unter `data/blacklab/index` aus.
- Diese Publish-Logik greift aber erst dann auf den echten Live-Search-Dienst, wenn BlackLab auch wirklich aus `data/blacklab/index` liest.
- Eine sichere Reihenfolge fuer Index-Cutover und App-Deploy ist daher zwingend.

## Kontrollierter Prod-Cutover-/Deploy-Plan

### Vor Deploy vorzubereiten

1. **Export/docmeta kanonisch befuellen**

- `/srv/webapps/corapan/data/blacklab/export` muss vor dem Deploy den produktiv gueltigen Exportstand enthalten.
- Minimal erforderlich: `docmeta.jsonl` und die benoetigten Export-/Metadatenartefakte.
- Vorher kein Go fuer Web-Deploy.

2. **Index-Cutover-Entscheidung explizit treffen**

- Entweder:
  - Kompatibilitaetsmodus: Live-BlackLab bleibt vorerst auf `blacklab_index`, dann darf aber **kein** neues Repo-Publish als produktiv wirksamer Index-Deploy missverstanden werden.
- Oder:
  - echter Cutover: Live-BlackLab wird sauber auf `/srv/webapps/corapan/data/blacklab/index` umgestellt.

3. **Rechte und Besitz normalisieren**

- `data/blacklab/index`, `data/blacklab/export`, `data/blacklab/backups`, `data/blacklab/quarantine` muessen mit den fuer BlackLab/Web benoetigten Rechten vorbereitet sein.
- Aktuelle Empfehlung aus der Server-Prep-Doku:
  - `index` -> `hrzadmin:hrzadmin 755`
  - `export` -> `hrzadmin:hrzadmin 770`
  - `backups` -> `hrzadmin:hrzadmin 755`
  - `quarantine` -> `hrzadmin:hrzadmin 770`

4. **Deploy-Fenster und BlackLab-Stopp vorbereiten**

- Falls der aktive Indexpfad umgestellt oder ein aktiver Index physisch verschoben/ersetzt wird, muss `corapan-blacklab` vorher gestoppt werden.
- Ein laufender Index darf nicht unter einer laufenden BlackLab-Instanz ueberschrieben oder umgehangen werden.

5. **Vorab-Checks definieren**

- Existiert `/srv/webapps/corapan/data/blacklab/export/docmeta.jsonl`?
- Ist `/srv/webapps/corapan/data/blacklab/index` vollstaendig und validierbar?
- Ist der geplante aktive BlackLab-Mountpfad eindeutig dokumentiert?
- Ist klar, ob der Run nur Web-Deploy oder auch BlackLab-Cutover umfasst?

### Was erst waehrend Deploy passieren darf

#### Empfohlene sichere Reihenfolge

1. Wartungsfenster oeffnen.
2. Falls Indexpfad umgestellt oder aktiver Index ersetzt wird: `corapan-blacklab` stoppen.
3. Aktiven Indexpfad eindeutig auf die Zielrealitaet festlegen.
   - Kein paralleles Arbeiten mit `blacklab_index` und `data/blacklab/index` als angeblich gleichwertig produktiv.
4. Falls echter Cutover: BlackLab-Startlogik/Mountquelle auf `/srv/webapps/corapan/data/blacklab/index` umstellen.
5. BlackLab starten und verifizieren:
   - `curl http://127.0.0.1:8081/blacklab-server/corpora/?outputformat=json`
   - Corpus `corapan` vorhanden
   - Log zeigt Scans gegen `/data/index`
6. Erst danach Web-App per `scripts/deploy_prod.sh` deployen.
7. Direkt nach Web-Deploy fachliche Suchpruefungen ausfuehren, nicht nur `/health`.

### Wo BlackLab gestoppt werden muss

BlackLab muss gestoppt werden, wenn einer der folgenden Punkte eintritt:

- der aktive Indexpfad von `blacklab_index` auf `data/blacklab/index` umgestellt wird
- der aktive Index physisch verschoben, ersetzt oder rollbackt wird
- ein laufender Indexbestand im aktiven Hostpfad ueberschrieben werden koennte

### Wo kein laufender Index ueberschrieben werden darf

- Nicht den aktuell von `corapan-blacklab` gemounteten Hostpfad ueberschreiben, solange der Container laeuft.
- Heute konkret: `/srv/webapps/corapan/data/blacklab_index` darf im laufenden Betrieb nicht blind ersetzt werden.
- Nach einem echten Cutover gilt dasselbe fuer `/srv/webapps/corapan/data/blacklab/index`.

### Was nach Deploy verifiziert werden muss

1. **Web-Grundgesundheit**

- `/health` antwortet
- Container `corapan-web-prod` healthy

2. **Auth/DB**

- Login / Token-Flow mindestens smoke-testen
- DB-Container laeuft stabil auf `corapan_postgres_prod`

3. **BlackLab**

- `corapan-blacklab` laeuft
- Corpus `corapan` ist erreichbar
- keine offensichtlichen Index-/Mount-Fehler in den Logs

4. **docmeta / Advanced Search**

- `docker exec corapan-web-prod test -f /app/data/blacklab/export/docmeta.jsonl`
- mindestens eine Advanced-Search-Abfrage mit Metadatenanreicherung pruefen
- sicherstellen, dass Search nicht nur Treffer liefert, sondern auch die erwarteten Dokumentmetadaten

5. **Pfadkonsistenz**

- dokumentieren, welcher Hostpfad jetzt wirklich produktiv ist
- keine Mischrealitaet aus altem und neuem Index-/Exportpfad unbeobachtet stehen lassen

## Go/No-Go-Einschaetzung

### Status

**No-Go fuer sofortigen Blind-Deploy**

### Begruendung

- Der aktive Prod-BlackLab-Index ist noch legacy.
- Die aktive Web-Codebasis erwartet bereits den neuen kanonischen docmeta-Pfad.
- Der neue Exportpfad ist auf Hostseite leer.
- Der bestehende Deploy prueft die kritischen Search-/docmeta-Aspekte nicht.

### Go waere erst vertretbar, wenn mindestens Folgendes vorab erledigt ist

1. `/srv/webapps/corapan/data/blacklab/export/docmeta.jsonl` ist vorhanden und fachlich gueltig.
2. Der produktive BlackLab-Indexpfad ist bewusst entschieden und dokumentiert.
3. Falls auf kanonische Struktur umgestellt wird: BlackLab-Mount/Startrealitaet ist vor dem Deploy sauber umgestellt und verifiziert.
4. Es gibt einen klaren Rollback fuer Index und Web.
5. Post-Deploy-Suchtests sind Teil des Deploy-Fensters und nicht optional.

## Massnahmen / Empfehlungen

1. Blind-Deploy jetzt nicht freigeben.
2. Zuerst einen geplanten Prod-Cutover fuer BlackLab-Export und aktiven Indexpfad durchfuehren.
3. `deploy_prod.sh` spaeter um BlackLab-/docmeta-spezifische Sanity-Checks erweitern.
4. `publish_blacklab_index.ps1` erst dann als produktiv wirksamen Publisher verwenden, wenn Live-BlackLab wirklich aus `data/blacklab/index` liest.
5. Die Platzhalter-Secrets in Prod separat zeitnah korrigieren.

## Offene Fragen / Unsicherheiten

1. Ob der aktuelle Prod-Betrieb die fehlende docmeta-Datei am neuen Pfad bereits fachlich spürbar degradiert oder ob dieser Fehler bislang unbemerkt toleriert wurde.
2. Ob im echten Auto-Deploy ausser `scripts/deploy_prod.sh` noch weitere Server-Schritte automatisch ausgeloe st werden.
3. Ob der BlackLab-Cutover im selben Wartungsfenster wie der Web-Deploy erfolgen soll oder als vorgeschaltete eigene Prod-Welle.
4. Ob die beobachteten Platzhalter-Secrets in Prod bewusst temporär sind oder ein realer Fehlzustand.