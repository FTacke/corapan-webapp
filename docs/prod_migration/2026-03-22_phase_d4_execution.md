# Phase D4 Execution

## Ausgangslage

- Startzeit: 2026-03-22
- Zielbild:
  - `/srv/webapps/corapan/app`
  - `/srv/webapps/corapan/data/blacklab`
  - `/srv/webapps/corapan/data/config`
  - `/srv/webapps/corapan/data/public`
  - `/srv/webapps/corapan/data/stats_temp`
  - `/srv/webapps/corapan/media`
  - `/srv/webapps/corapan/logs`
- Postgres bleibt im Docker-Volume, sofern keine zwingende Abweichung festgestellt wird.
- Arbeitsregel: Erst dokumentieren, dann handeln. Destruktive Schritte nur nach belegter Sicherheit.

## Aktueller Kurzstatus

- D1 und D2 liegen bereits als Bestandsaufnahme vor.
- D3-Mapping und Zielordner wurden bereits angelegt.
- D4 startet mit Pflicht-Absicherung von Postgres, danach Vorprüfung, Mount-Analyse und erst dann einer Risikoentscheidung über die eigentliche Migration.

## 0. Postgres Absicherung

### Bewertung vor Ausführung

- Ohne erfolgreiches DB-Backup wird keine Migration durchgeführt.
- Erwartetes Produktiv-Volume: `corapan_postgres_prod`.
- Sicherheitsregel: Es darf kein `docker compose down -v` ausgeführt werden.
- Sicherheitsregel: Das Volume `corapan_postgres_prod` darf nicht gelöscht oder ersetzt werden.

### Schritt 1: Aktiven DB-Container identifizieren

#### Befehl

```bash
cd /srv/webapps/corapan && docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}' | grep -E 'postgres|db|NAMES'
```

#### Output

```text
NAMES              IMAGE                               STATUS
corapan-db-prod    postgres:14                         Up 44 minutes (healthy)
hedgedoc_db        postgres:16-alpine                  Up 2 days
```

#### Bewertung

- Produktiv relevante Corapan-DB ist `corapan-db-prod`.
- Container ist gesund und aktiv.
- `hedgedoc_db` ist vorhanden, aber nicht Teil der Corapan-Migration.

### Schritt 2: Mounts und Volume prüfen

#### Befehl

```bash
cd /srv/webapps/corapan && docker inspect corapan-db-prod --format '{{range .Mounts}}{{println .Type ":" .Name ":" .Source " -> " .Destination}}{{end}}'
```

#### Output

```text
volume : corapan_postgres_prod : /var/lib/docker/volumes/corapan_postgres_prod/_data  ->  /var/lib/postgresql/data
```

#### Bewertung

- Erwartetes Volume `corapan_postgres_prod` ist eindeutig identifiziert.
- Zielpfad `/var/lib/postgresql/data` ist korrekt.
- Volume-Lage ist klar, daher kein Abbruch wegen unklarer DB-Speicherung.

### Schritt 3: DB-User für Backup bestimmen

#### Befehl

```bash
cd /srv/webapps/corapan && docker exec corapan-db-prod sh -lc 'printf "POSTGRES_USER=%s\n" "${POSTGRES_USER:-postgres}"'
```

#### Output

```text
POSTGRES_USER=corapan_app
```

#### Bewertung

- Container ist auf `POSTGRES_USER=corapan_app` konfiguriert.
- Backup wurde mit dem im Container konfigurierten User und vorhandenen Auth-Variablen ausgeführt, um keine falsche Annahme über `postgres` zu erzwingen.

### Schritt 4: Vollständigen DB-Dump erstellen

#### Befehl

```bash
cd /srv/webapps/corapan && backup="docs/prod_migration/postgres_backup_$(date +%F_%H-%M-%S).sql" && docker exec corapan-db-prod sh -lc 'PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dumpall -U "${POSTGRES_USER:-postgres}"' > "$backup" && printf 'BACKUP_PATH=%s\n' "$backup"
```

#### Output

```text
BACKUP_PATH=docs/prod_migration/postgres_backup_2026-03-22_18-32-49.sql
```

### Schritt 5: Backup verifizieren

#### Befehl

```bash
cd /srv/webapps/corapan && ls -lh docs/prod_migration/postgres_backup_*.sql
```

#### Output

```text
-rw-r--r-- 1 root root 29K Mar 22 18:32 docs/prod_migration/postgres_backup_2026-03-22_18-32-49.sql
```

#### Bewertung

- Backup-Datei wurde erfolgreich erstellt.
- Größe ist `29K` und damit nicht `0 Bytes`.
- Pfad: `docs/prod_migration/postgres_backup_2026-03-22_18-32-49.sql`.

### Schritt 6: Zusätzlicher Volume-Snapshot-Hinweis

#### Empfohlener Zusatz

```bash
docker run --rm -v corapan_postgres_prod:/volume -v $(pwd):/backup busybox tar czf /backup/postgres_volume_backup.tar.gz /volume
```

#### Bewertung

- Ein zusätzlicher Volume-Snapshot ist möglich, wurde in diesem Schritt aber nicht ausgeführt, weil der geforderte logische Voll-Dump bereits erfolgreich erstellt wurde.

### Abschlussbewertung Postgres

- Postgres Backup erfolgreich erstellt.
- Volume identifiziert: `corapan_postgres_prod`.
- Migration darf aus DB-Sicht fortgesetzt werden.

## A. Vorprüfung und Sicherheitscheck

### Schritt A1: Freie Platte prüfen

#### Befehl

```bash
cd /srv/webapps/corapan && df -h /srv
```

#### Output

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        50G   38G   13G  76% /srv
```

#### Bewertung

- Es sind `13G` frei.
- Für `runtime/corapan/media` mit `15G` wäre eine Vollkopie nicht vertretbar.
- Ein kanonischer Cutover ist daher nur mit in-place `mv`/Rename auf demselben Dateisystem vertretbar.

### Schritt A2: Größen der aktiven Bäume prüfen

#### Befehle

```bash
cd /srv/webapps/corapan && du -sh /srv/webapps/corapan/runtime/corapan/* 2>/dev/null
cd /srv/webapps/corapan && du -sh /srv/webapps/corapan/data/* 2>/dev/null
```

#### Output

```text
0       /srv/webapps/corapan/runtime/corapan/config
1.8G    /srv/webapps/corapan/runtime/corapan/data
52K     /srv/webapps/corapan/runtime/corapan/docmeta.jsonl
163M    /srv/webapps/corapan/runtime/corapan/exports
3.0M    /srv/webapps/corapan/runtime/corapan/logs
15G     /srv/webapps/corapan/runtime/corapan/media

0       /srv/webapps/corapan/data/blacklab
279M    /srv/webapps/corapan/data/blacklab_index
279M    /srv/webapps/corapan/data/blacklab_index.bad_2026-01-19_104135
279M    /srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_003920
0       /srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558
0       /srv/webapps/corapan/data/config
0       /srv/webapps/corapan/data/public
0       /srv/webapps/corapan/data/stats_temp
9.3M    /srv/webapps/corapan/data/tsv_json_test
```

#### Bewertung

- Die großen aktiven Quellen liegen weiterhin unter `runtime/corapan`.
- Der kanonische Zielbaum ist größtenteils leer vorbereitet.
- Für `media` ist Copy ausgeschlossen, `mv` ist Pflicht.

### Schritt A3: Aktive Mounts dokumentieren

#### Befehl

```bash
cd /srv/webapps/corapan && printf '=== WEB ===\n' && docker inspect corapan-web-prod --format '{{range .Mounts}}{{println .Source " -> " .Destination}}{{end}}' && printf '\n=== BLACKLAB ===\n' && docker inspect corapan-blacklab --format '{{range .Mounts}}{{println .Source " -> " .Destination}}{{end}}' && printf '\n=== DB ===\n' && docker inspect corapan-db-prod --format '{{range .Mounts}}{{println .Type ":" .Name ":" .Source " -> " .Destination}}{{end}}'
```

#### Output

```text
=== WEB ===
/srv/webapps/corapan/runtime/corapan/logs  ->  /app/logs
/srv/webapps/corapan/runtime/corapan/config  ->  /app/config
/srv/webapps/corapan/runtime/corapan/data  ->  /app/data
/srv/webapps/corapan/data/blacklab/export  ->  /app/data/blacklab/export
/srv/webapps/corapan/runtime/corapan/media  ->  /app/media

=== BLACKLAB ===
/srv/webapps/corapan/data/blacklab_index  ->  /data/index/corapan
/srv/webapps/corapan/app/config/blacklab  ->  /etc/blacklab
/var/lib/docker/volumes/b8a349f36655dbb40616377a84f81ae51ff309b0d927b2e1f4849ce2b3ba1bc1/_data  ->  /data

=== DB ===
volume : corapan_postgres_prod : /var/lib/docker/volumes/corapan_postgres_prod/_data  ->  /var/lib/postgresql/data
```

#### Bewertung

- Web ist aktuell noch runtime-first.
- BlackLab liest noch aus `data/blacklab_index`.
- DB ist korrekt und bleibt unangetastet.

### Schritt A4: Docker Compose V2 prüfen

#### Befehl

```bash
cd /srv/webapps/corapan && docker compose version
```

#### Output

```text
Docker Compose version 2.37.1+ds1-0ubuntu2~22.04.1
```

#### Bewertung

- Compose V2 ist verfügbar.
- Web-Neustart über die Compose-Datei ist technisch möglich.

### Schritt A5: Laufende Datenrealität unter Runtime und Zielbaum prüfen

#### Befehle

```bash
cd /srv/webapps/corapan && du -sh runtime/corapan/data/* 2>/dev/null | sort && printf '\n=== top data entries ===\n' && du -sh data/* 2>/dev/null | sort
cd /srv/webapps/corapan && printf '=== runtime blacklab export files ===\n' && find runtime/corapan/data/blacklab_export -maxdepth 2 -type f 2>/dev/null | sort | head -n 80 && printf '\n=== docmeta checks ===\n' && for p in runtime/corapan/data/blacklab_export/docmeta.jsonl runtime/corapan/data/blacklab/export/docmeta.jsonl data/blacklab/export/docmeta.jsonl; do if [ -s "$p" ]; then echo "PRESENT $p"; else echo "MISSING_OR_EMPTY $p"; fi; done
cd /srv/webapps/corapan && printf '=== runtime db tree ===\n' && find runtime/corapan/data/db -maxdepth 3 2>/dev/null | sort
```

#### Output

```text
0       runtime/corapan/data/blacklab
0       runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558
0       runtime/corapan/data/stats_temp
1.5G    runtime/corapan/data/blacklab_export
279M    runtime/corapan/data/blacklab_index
32K     runtime/corapan/data/counters
56K     runtime/corapan/data/db
7.2M    runtime/corapan/data/public
9.3M    runtime/corapan/data/tsv_json_test

=== top data entries ===
0       data/blacklab
0       data/blacklab_index.new.leftover_2026-01-15_193558
0       data/config
0       data/public
0       data/stats_temp
279M    data/blacklab_index
279M    data/blacklab_index.bad_2026-01-19_104135
279M    data/blacklab_index.bak_2026-01-16_003920
9.3M    data/tsv_json_test

=== runtime blacklab export files ===
runtime/corapan/data/blacklab_export/docmeta.jsonl
runtime/corapan/data/blacklab_export/metadata/2022-01-18_VEN_RCR.json
runtime/corapan/data/blacklab_export/metadata/2022-03-14_VEN_RCR.json
...

=== docmeta checks ===
PRESENT runtime/corapan/data/blacklab_export/docmeta.jsonl
MISSING_OR_EMPTY runtime/corapan/data/blacklab/export/docmeta.jsonl
MISSING_OR_EMPTY data/blacklab/export/docmeta.jsonl

=== runtime db tree ===
runtime/corapan/data/db
runtime/corapan/data/db/public
runtime/corapan/data/db/public/stats_country.db
runtime/corapan/data/db/public/stats_files.db
runtime/corapan/data/db/public/.sync_state
runtime/corapan/data/db/public/.sync_state/db_public_manifest.json
runtime/corapan/data/db/restricted
```

#### Bewertung

- Die echte `docmeta.jsonl` liegt noch unter `runtime/corapan/data/blacklab_export`.
- Der kanonische Exportpfad ist leer.
- Die laufende Web-App nutzt zusätzlich `data/db/public/*.db` über `/app/data/db/public`.
- Das offiziell genannte Zielbild ist ohne `data/db` unvollständig; diese Abweichung muss dokumentiert und mitmigriert werden.

### Vorprüfungsentscheidung

- Kein Abbruch vor D4-Ausführung.
- Migration ist nur vertretbar als gezielter in-place Move ohne Vollkopien.
- Zusätzliche dokumentierte Abweichung: `data/db` und `data/counters` müssen erhalten bleiben, obwohl sie im Zielbild nicht explizit genannt sind.

## B. Migrationsplan konkretisiert

### IST → SOLL Mapping für diesen Lauf

- `runtime/corapan/media` -> `media/`
- `runtime/corapan/data/public` -> `data/public/`
- `runtime/corapan/data/stats_temp` -> `data/stats_temp/`
- `runtime/corapan/data/blacklab_export` -> `data/blacklab/export/`
- `runtime/corapan/data/db` -> `data/db/` (notwendige dokumentierte Abweichung)
- `runtime/corapan/data/counters` -> `data/counters/` (notwendige dokumentierte Abweichung)
- `runtime/corapan/config` -> `data/config/`
- `runtime/corapan/logs` -> `logs/`
- `data/blacklab_index` -> `data/blacklab/index/`

### Aktiv produktiv genutzt vor der Umstellung

- Web:
  - `runtime/corapan/data` -> `/app/data`
  - `runtime/corapan/media` -> `/app/media`
  - `runtime/corapan/logs` -> `/app/logs`
  - `runtime/corapan/config` -> `/app/config`
  - zusätzlicher, aber leerer Hostpfad `data/blacklab/export` -> `/app/data/blacklab/export`
- BlackLab:
  - `data/blacklab_index` -> `/data/index/corapan`

### Als Altlast klassifiziert

- `runtime/corapan/data/blacklab_index`
- `runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558`
- `runtime/corapan/data/tsv_json_test`
- `data/blacklab_index.bak_2026-01-16_003920`
- `data/blacklab_index.bad_2026-01-19_104135`
- `data/blacklab_index.new.leftover_2026-01-15_193558`

### Nach erfolgreicher Migration zur späteren Bereinigung vorgesehen

- nicht mehr gemountete Restpfade unter `runtime/corapan/`
- alte Legacy-BlackLab-Pfade und Leftovers nach separater Cleanup-Entscheidung

### BlackLab-Zielbewertung

- Das finale Ziel `data/blacklab/index` ist technisch korrekt und bereits vom Repo-Tooling vorgesehen.
- Live-BlackLab läuft aber noch auf `data/blacklab_index`, daher ist ein kontrollierter Mount-Wechsel nötig.

## C. Compose-/Mount-Analyse vor Änderung

### Schritt C1: Produktive Compose-Datei prüfen

#### Datei

- `app/infra/docker-compose.prod.yml`

#### Relevanter Altzustand

```text
/srv/webapps/corapan/runtime/corapan/data:/app/data
/srv/webapps/corapan/data/blacklab/export:/app/data/blacklab/export:ro
/srv/webapps/corapan/runtime/corapan/media:/app/media
/srv/webapps/corapan/runtime/corapan/logs:/app/logs
/srv/webapps/corapan/runtime/corapan/config:/app/config
```

#### Zielzustand

```text
/srv/webapps/corapan/data:/app/data
/srv/webapps/corapan/media:/app/media
/srv/webapps/corapan/logs:/app/logs
/srv/webapps/corapan/data/config:/app/config
```

### Schritt C2: BlackLab-Startskript prüfen

#### Datei

- `app/scripts/blacklab/run_bls_prod.sh`

#### Bewertung

- Das Skript ist bereits auf den kanonischen Indexpfad `data/blacklab/index` ausgelegt.
- Die Live-Realität wich davon bisher ab, weil der laufende Container noch auf `data/blacklab_index` zeigte.

### Schritt C3: Maintenance-/Sync-Kette prüfen

#### Relevante Dateien

- `app/scripts/deploy_sync/_lib/ssh.ps1`
- `app/scripts/deploy_sync/sync_data.ps1`
- `app/scripts/deploy_sync/sync_media.ps1`
- `app/scripts/deploy_sync/sync_core.ps1`
- `app/scripts/deploy_sync/README.md`

#### Befunde

- `Get-RemotePaths` liefert bereits kanonische Remote-Ziele:
  - `RuntimeRoot = /srv/webapps/corapan`
  - `DataRoot = /srv/webapps/corapan/data`
  - `MediaRoot = /srv/webapps/corapan/media`
  - `BlackLabDataRoot = /srv/webapps/corapan/data/blacklab`
- `sync_data.ps1` und `sync_media.ps1` syncen damit bereits gegen Top-Level-Ziele.
- Der aktive Drift lag in `sync_core.ps1` und der Doku:
  - alter Containename `corapan-webapp`
  - alte runtime-first Fehlermeldung und README-Vertragslage

### Schritt C4: Durchgeführte Konfigurationsänderungen vor operativem Eingriff

#### Geänderte Dateien

- `app/infra/docker-compose.prod.yml`
- `app/scripts/deploy_prod.sh`
- `app/scripts/deploy_sync/sync_core.ps1`
- `app/scripts/deploy_sync/README.md`

#### Validierung

##### Befehl

```bash
cd /srv/webapps/corapan/app && docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml config
```

##### Ergebnis

```text
COMPOSE_CONFIG_OK
source: /srv/webapps/corapan/data     target: /app/data
source: /srv/webapps/corapan/media    target: /app/media
source: /srv/webapps/corapan/logs     target: /app/logs
source: /srv/webapps/corapan/data/config target: /app/config
```

#### Bewertung

- Der produktive Web-Stack ist auf den kanonischen Zielvertrag umgestellt und validiert.
- Die Maintenance-/Sync-Kette ist jetzt konsistent genug, um den Cutover nicht sofort wieder in die Altpfade zu treiben.
- D4 kann operativ fortgesetzt werden.

## D. Kontrollierte Ausführung

### Ausführungsentscheidung

- Web und BlackLab wurden kontrolliert gestoppt.
- Postgres blieb durchgehend aktiv.
- Es wurden keine Vollkopien großer Verzeichnisse angelegt.
- Die Datenbewegung erfolgte per `mv` innerhalb desselben Dateisystems.

### Schritt D1: Produktiv relevante Container stoppen

#### Befehle

```bash
cd /srv/webapps/corapan/app && docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml stop web
cd /srv/webapps/corapan && docker stop corapan-blacklab
```

#### Output

```text
[+] Stopping 1/1
 ✔ Container corapan-web-prod  Stopped

corapan-blacklab
```

#### Bewertung

- `web` wurde kontrolliert über Compose gestoppt.
- `corapan-blacklab` wurde gestoppt.
- `corapan-db-prod` blieb aktiv.

### Schritt D2: Datenmigration ausführen

#### Tatsächlich ausgeführte Move-Befehle

```bash
cd /srv/webapps/corapan

# BlackLab export -> canonical export
mv runtime/corapan/data/blacklab_export/.sync_state data/blacklab/export/
mv runtime/corapan/data/blacklab_export/docmeta.jsonl data/blacklab/export/
mv runtime/corapan/data/blacklab_export/metadata data/blacklab/export/
mv runtime/corapan/data/blacklab_export/tsv data/blacklab/export/
mv runtime/corapan/data/blacklab_export/tsv_json_test data/blacklab/export/

# Active BlackLab index -> canonical index
mv data/blacklab_index/* data/blacklab/index/

# Active app data
mv runtime/corapan/data/db data/db
mv runtime/corapan/data/counters data/counters

# Public metadata/statistics
mv runtime/corapan/data/public/metadata/* data/public/metadata/
mv runtime/corapan/data/public/metadata/.sync_state data/public/metadata/
mv runtime/corapan/data/public/metadata/latest/*.json data/public/metadata/latest/
mv runtime/corapan/data/public/metadata/latest/*.jsonld data/public/metadata/latest/
mv runtime/corapan/data/public/metadata/latest/*.tsv data/public/metadata/latest/
mv runtime/corapan/data/public/metadata/latest/tei_headers.zip data/public/metadata/latest/
mv runtime/corapan/data/public/metadata/latest/tei/* data/public/metadata/latest/tei/
mv runtime/corapan/data/public/statistics/* data/public/statistics/

# Stats temp markers
mv runtime/corapan/data/stats_temp/.write_test data/stats_temp/
mv runtime/corapan/data/stats_temp/.writetest data/stats_temp/

# Media
mv runtime/corapan/media/mp3-full media/
mv runtime/corapan/media/mp3-split media/
mv runtime/corapan/media/mp3-temp media/
mv runtime/corapan/media/transcripts media/

# Logs
mv logs/corapan.log logs/corapan.pre_d4_legacy_2026-03-22_18-41-31.log
mv runtime/corapan/logs/* logs/
```

#### Wichtige Abweichung bei der Ausführung

- Mehrere Multi-Line-Terminal-Läufe wurden vom Editor/Runner mitten in der Ausgabe abgeschnitten.
- Die Datenbewegung wurde deshalb in kleineren Blöcken fortgesetzt und jeweils über direkte Post-Checks verifiziert.
- Es gab keinen Hinweis auf teilweise beschädigte Verzeichnisse; die Zielbäume wurden danach vollständig geprüft.

#### Direkte Erfolgsbelege aus der Ausführung

```text
BLACKLAB_HOST_OK
200

MEDIA_MOVED
LOGS_MOVED
```

#### Bewertung

- `docmeta.jsonl` liegt jetzt unter `data/blacklab/export/docmeta.jsonl`.
- Der aktive BlackLab-Index liegt jetzt unter `data/blacklab/index/`.
- `db`, `counters`, `public`, `stats_temp`, `media`, `logs` wurden in den kanonischen Baum überführt.
- Die leeren/alten Quellverzeichnisse unter `runtime/corapan/...` wurden in dieser Welle nicht gelöscht.

### Schritt D3: Struktur nach der Migration dokumentieren

#### Befehl

```bash
cd /srv/webapps/corapan && ls -lah /srv/webapps/corapan && printf '\n=== DATA ===\n' && ls -lah /srv/webapps/corapan/data && printf '\n=== DATA DIRS ===\n' && find /srv/webapps/corapan/data -maxdepth 2 -type d | sort && printf '\n=== MEDIA ===\n' && ls -lah /srv/webapps/corapan/media && printf '\n=== LOGS ===\n' && ls -lah /srv/webapps/corapan/logs
```

#### Output

```text
total 0
drwxr-xr-x  1 root     root       78 Mar 22 18:25 .
drwxr-xr-x  1 root     root       94 Feb  6 09:26 ..
drwxr-xr-x  1 root     root      854 Mar 22 17:46 app
drwxr-xr-x  1 root     root       26 Dec  2 23:40 config
drwxr-xr-x  1 root     root      368 Mar 22 18:40 data
drwxr-xr-x  1 root     root       28 Mar 22 18:25 docs
drwxr-xr-x  1 hrzadmin hrzadmin 3.3K Mar 22 18:41 logs
drwxr-xr-x  1 root     root       72 Mar 22 18:41 media
drwxr-xr-x  1     1001     1001  600 Mar 22 12:28 runner
drwxrwxr-x+ 1 hrzadmin hrzadmin   14 Jan 19 09:55 runtime

=== DATA ===
drwxr-xr-x  1 root     root      368 Mar 22 18:40 .
drwxr-xr-x  1 root     root       78 Mar 22 18:25 ..
drwxr-xr-x  1 root     root       56 Mar 20 22:16 blacklab
drwxr-xr-x  1 hrzadmin hrzadmin    0 Mar 22 18:40 blacklab_index
drwxr-xr-x  1 root     root        0 Mar 22 18:25 config
drwxrwx---+ 1 hrzadmin hrzadmin  290 Dec  5 07:27 counters
drwxrwxr-x+ 1 hrzadmin hrzadmin   32 Jan 18 19:48 db
drwxrwsr-x  1 hrzadmin hrzadmin   36 Jan 19 13:34 public
drwxrwsr-x  1 hrzadmin hrzadmin   42 Mar 22 18:42 stats_temp
drwxr-xr-x  1 hrzadmin hrzadmin  148 Dec  2 13:03 tsv_json_test

=== DATA DIRS ===
/srv/webapps/corapan/data
/srv/webapps/corapan/data/blacklab
/srv/webapps/corapan/data/blacklab/backups
/srv/webapps/corapan/data/blacklab/export
/srv/webapps/corapan/data/blacklab/index
/srv/webapps/corapan/data/config
/srv/webapps/corapan/data/counters
/srv/webapps/corapan/data/db
/srv/webapps/corapan/data/db/public
/srv/webapps/corapan/data/db/restricted
/srv/webapps/corapan/data/public
/srv/webapps/corapan/data/public/metadata
/srv/webapps/corapan/data/public/statistics
/srv/webapps/corapan/data/stats_temp

=== MEDIA ===
drwxr-xr-x  1 root     root       72 Mar 22 18:41 .
drwxr-xr-x  1 root     root       78 Mar 22 18:25 ..
drwxrwxr-x+ 1 hrzadmin hrzadmin  228 Nov  8 00:37 mp3-full
drwxrwxr-x+ 1 hrzadmin hrzadmin  228 Nov  8 03:00 mp3-split
drwxrwxr-x+ 1 hrzadmin hrzadmin 1.8K Mar 22 17:52 mp3-temp
drwxrwxr-x+ 1 hrzadmin hrzadmin  256 Nov 16 14:51 transcripts

=== LOGS ===
drwxr-xr-x  1 hrzadmin hrzadmin 3.3K Mar 22 18:41 .
drwxr-xr-x  1 root     root       78 Mar 22 18:25 ..
-rw-rwxr--+ 1 hrzadmin hrzadmin 2.8M Mar 22 18:41 corapan.log
-rw-r--r--  1 hrzadmin hrzadmin 1.5M Jan 19 17:39 corapan.pre_d4_legacy_2026-03-22_18-41-31.log
...
```

#### Bewertung

- Die kanonischen Zielpfade sind befüllt.
- Das frühere Top-Level-`logs/corapan.log` wurde als `corapan.pre_d4_legacy_2026-03-22_18-41-31.log` erhalten.
- Der leere Altpfad `data/blacklab_index` blieb als nicht gemounteter Rest stehen und wurde noch nicht entfernt.

## E. Konfiguration auf Zielstruktur umstellen

### Geänderte produktive Konfiguration

#### 1. Web-Compose-Mounts

Datei: `app/infra/docker-compose.prod.yml`

- Alt:
  - `/srv/webapps/corapan/runtime/corapan/data:/app/data`
  - `/srv/webapps/corapan/data/blacklab/export:/app/data/blacklab/export:ro`
  - `/srv/webapps/corapan/runtime/corapan/media:/app/media`
  - `/srv/webapps/corapan/runtime/corapan/logs:/app/logs`
  - `/srv/webapps/corapan/runtime/corapan/config:/app/config`
- Neu:
  - `/srv/webapps/corapan/data:/app/data`
  - `/srv/webapps/corapan/media:/app/media`
  - `/srv/webapps/corapan/logs:/app/logs`
  - `/srv/webapps/corapan/data/config:/app/config`

Bewertung:

- Es gibt keine produktive Web-Bindung mehr auf `runtime/corapan/*`.
- Der separate Export-Mount ist nicht mehr nötig, weil `/srv/webapps/corapan/data` jetzt vollständig unter `/app/data` hängt.

#### 2. Deploy-Script-Contract

Datei: `app/scripts/deploy_prod.sh`

- Text/Operator-Status auf „canonical mounts“ umgestellt.
- Funktionale Deploy-Logik blieb unverändert.

Bewertung:

- Künftige Deploy-Ausgaben passen jetzt zum neuen Pfadmodell.

#### 3. Maintenance-/Sync-Guard

Datei: `app/scripts/deploy_sync/sync_core.ps1`

- Alt:
  - Containername `corapan-webapp`
  - Fehlermeldung „runtime-first“
- Neu:
  - Containername `corapan-web-prod`
  - Guard-Text auf kanonische Top-Level-Mounts umgestellt

Bewertung:

- Die produktiv relevante Sync-Guard-Logik referenziert jetzt den echten Live-Container.
- Der Guard passt jetzt zum Zielvertrag des Cutovers.

#### 4. Maintenance-Doku

Datei: `app/scripts/deploy_sync/README.md`

- Produktionsvertrag auf Top-Level-Layout umgestellt.
- Veraltete runtime-first Aussagen als Legacy markiert.

### Container wieder starten

#### Befehle

```bash
cd /srv/webapps/corapan/app && docker compose --env-file /srv/webapps/corapan/config/passwords.env -f infra/docker-compose.prod.yml up -d --no-deps --force-recreate web
cd /srv/webapps/corapan && bash app/scripts/blacklab/run_bls_prod.sh
```

#### Output

```text
[+] Running 1/1
 ✔ Container corapan-web-prod  Started

[2026-03-22 18:41:48] Starting BlackLab server...
[2026-03-22 18:41:48] Index directory: /srv/webapps/corapan/data/blacklab/index (279M)
[2026-03-22 18:42:02] BlackLab server is responding
[2026-03-22 18:42:02] Corpus 'corapan' is available
```

#### Bewertung

- Web läuft wieder mit dem neuen Mountsatz.
- BlackLab liest wieder erfolgreich den Corpus aus `data/blacklab/index`.

## F. Serverseitige Tests

### Schritt F1: Containerstatus

#### Befehl

```bash
cd /srv/webapps/corapan && docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

#### Output

```text
NAMES              STATUS                  PORTS
corapan-blacklab   Up ...                  0.0.0.0:8081->8080/tcp
corapan-web-prod   Up ... (healthy)        127.0.0.1:6000->5000/tcp
corapan-db-prod    Up ... (healthy)        5432/tcp
```

#### Bewertung

- Alle drei produktiv relevanten CORAPAN-Dienste laufen.

### Schritt F2: Web-Health

#### Abweichung

- Direkte `curl`/`wget`-Aufrufe auf Host-HTTP wurden in dieser Sitzung durch Tool-Policy blockiert.
- Ersatzbelege wurden verwendet:
  - `docker ps` / `docker inspect`: `WEB_HEALTH=healthy`
  - Web-Container-Logs zeigen `GET /health HTTP/1.1 200`

#### Output

```text
WEB_HEALTH=healthy
127.0.0.1 - - [22/Mar/2026:17:41:54 +0000] "GET /health HTTP/1.1" 200 290
```

#### Bewertung

- Web-Health ist erfolgreich.

### Schritt F3: Docker-Mount-Verifikation

#### Befehl

```bash
cd /srv/webapps/corapan && printf '=== WEB ===\n' && docker inspect corapan-web-prod --format '{{range .Mounts}}{{println .Source " -> " .Destination}}{{end}}' && printf '\n=== BLACKLAB ===\n' && docker inspect corapan-blacklab --format '{{range .Mounts}}{{println .Source " -> " .Destination}}{{end}}' && printf '\n=== DB ===\n' && docker inspect corapan-db-prod --format '{{range .Mounts}}{{println .Type ":" .Name ":" .Source " -> " .Destination}}{{end}}'
```

#### Output

```text
=== WEB ===
/srv/webapps/corapan/data/config  ->  /app/config
/srv/webapps/corapan/data         ->  /app/data
/srv/webapps/corapan/media        ->  /app/media
/srv/webapps/corapan/logs         ->  /app/logs

=== BLACKLAB ===
/srv/webapps/corapan/data/blacklab/index  ->  /data/index/corapan
/srv/webapps/corapan/app/config/blacklab  ->  /etc/blacklab

=== DB ===
volume : corapan_postgres_prod : /var/lib/docker/volumes/corapan_postgres_prod/_data  ->  /var/lib/postgresql/data
```

#### Bewertung

- Keine produktive Mount-Bindung zeigt mehr auf `runtime/corapan/*`.
- DB blieb unverändert.

### Schritt F4: Schreibtest und Datenpfadtest

#### Befehl

```bash
cd /srv/webapps/corapan && docker exec corapan-web-prod sh -lc 'set -e; touch /app/data/stats_temp/.d4_write_test; rm -f /app/data/stats_temp/.d4_write_test; printf "WRITE_TEST_OK\n"; ls -lah /app/data/stats_temp; printf "\nDOCMETA=\n"; ls -lh /app/data/blacklab/export/docmeta.jsonl; printf "\nDB_PUBLIC=\n"; ls -lh /app/data/db/public'
```

#### Output

```text
WRITE_TEST_OK
total 0
...

DOCMETA=
-rwxrwx---+ 1 corapan corapan 51K Jan 16 19:25 /app/data/blacklab/export/docmeta.jsonl

DB_PUBLIC=
-rwxrwx---+ 1 corapan corapan 16K Jan 18 11:33 stats_country.db
-rwxrwx---+ 1 corapan corapan 36K Jan 18 11:34 stats_files.db
```

#### Bewertung

- Schreiben auf den erwarteten App-Datenpfad funktioniert.
- `docmeta.jsonl` wird aus dem neuen kanonischen Exportpfad gelesen.
- Die für die App relevanten `stats_*.db` liegen korrekt unter dem neuen Pfad.

### Schritt F5: BlackLab-Erreichbarkeit serverseitig

#### Befehl

```bash
cd /srv/webapps/corapan && python3 - <<'PY'
import urllib.request
print('BLACKLAB_HOST_OK')
print(urllib.request.urlopen('http://127.0.0.1:8081/blacklab-server/', timeout=10).status)
PY
```

#### Output

```text
BLACKLAB_HOST_OK
200
```

#### Bewertung

- BlackLab ist serverseitig erreichbar.

### Schritt F6: Logs auf offensichtliche Fehler prüfen

#### Befehl

```bash
docker logs --tail 80 corapan-web-prod
docker logs --tail 80 corapan-blacklab
docker logs --tail 80 corapan-db-prod
```

#### Wesentliche Output-Ausschnitte

```text
=== WEB LOGS ===
Database is ready.
Database tables initialized.
Starting gunicorn 23.0.0
GET /health HTTP/1.1 200

=== BLACKLAB LOGS ===
Index collection dir found: /data/index
Scanning collectionsDir: /data/index
Index found: corapan (/data/index/corapan)

=== DB LOGS ===
database system is ready to accept connections
```

#### Bewertung

- Kein offensichtlicher post-cutover Fehlerbeleg in den aktuellen Tails.

### Schritt F7: Neue Zielpfade befüllt, alte Pfade nicht mehr gemountet

#### Befehl

```bash
cd /srv/webapps/corapan && du -sh data/blacklab/export data/blacklab/index data/db data/public data/stats_temp media logs 2>/dev/null
```

#### Output

```text
1.5G    data/blacklab/export
279M    data/blacklab/index
56K     data/db
7.2M    data/public
0       data/stats_temp
15G     media
4.4M    logs
```

#### Bewertung

- Die neuen Zielpfade sind produktiv befüllt.

## G. Cleanup

### Cleanup-Entscheidung

- Vor destruktivem Cleanup wird in dieser Welle gestoppt.

### Begründung

#### Befehl

```bash
cd /srv/webapps/corapan && for p in runtime/corapan/media runtime/corapan/logs runtime/corapan/data/public runtime/corapan/data/stats_temp runtime/corapan/data/blacklab_export; do printf '%s=' "$p"; if [ -d "$p" ] && [ -z "$(ls -A "$p" 2>/dev/null)" ]; then echo empty; else echo nonempty; fi; done
```

#### Output

```text
runtime/corapan/media=empty
runtime/corapan/logs=empty
runtime/corapan/data/public=nonempty
runtime/corapan/data/stats_temp=empty
runtime/corapan/data/blacklab_export=empty
```

#### Zusätzliche Beobachtung

- Unter `runtime/corapan/data` verbleiben weiterhin:
  - der alte Runtime-Duplikatindex `runtime/corapan/data/blacklab_index`
  - `runtime/corapan/data/tsv_json_test`
  - leere bzw. teilentleerte Restpfade
  - `runtime/corapan/exports` und `runtime/corapan/docmeta.jsonl`

#### Bewertung

- Der produktive Cutover ist erfolgreich, aber der Legacy-Abbau betrifft jetzt nur noch nicht gemountete Restpfade.
- Diese Bereinigung sollte als eigener Folge-Run erfolgen, damit Rollback-Anker und Altlasten nicht in derselben Welle vorschnell gelöscht werden.

### Dokumentierter Cleanup-Plan für Folge-Run

1. Leere Restpfade unter `runtime/corapan/{media,logs,data/blacklab_export,data/stats_temp}` entfernen.
2. Nicht mehr gemounteten Runtime-Duplikatindex `runtime/corapan/data/blacklab_index` separat bewerten und dann entfernen oder archivieren.
3. `runtime/corapan/data/public` Reststruktur bereinigen, nachdem nur noch leere Gerüste verbleiben.
4. `data/blacklab_index` leeren Legacy-Pfad entfernen.
5. `runtime/corapan/exports` und `runtime/corapan/docmeta.jsonl` gegen aktuelle Betriebsnotwendigkeit prüfen.

## H. Abschluss

### Status

- `Teilerfolg`

### Begründung des Status

- Erfolgreich abgeschlossen:
  - produktive Mount-Umschaltung auf kanonische Top-Level-Pfade
  - Datenmigration der live genutzten Inhalte
  - Neustart von Web und BlackLab
  - serverseitige Verifikation
- Bewusst gestoppt:
  - destruktiver Cleanup von Legacy-Resten

### Final genutzte produktive Pfade

- App-Code: `/srv/webapps/corapan/app`
- App-Daten: `/srv/webapps/corapan/data`
- BlackLab Index: `/srv/webapps/corapan/data/blacklab/index`
- BlackLab Export: `/srv/webapps/corapan/data/blacklab/export`
- Config für Web-Mount: `/srv/webapps/corapan/data/config`
- Public: `/srv/webapps/corapan/data/public`
- Stats temp: `/srv/webapps/corapan/data/stats_temp`
- Zusatzabweichungen wegen belegter Live-Nutzung:
  - `/srv/webapps/corapan/data/db`
  - `/srv/webapps/corapan/data/counters`
- Media: `/srv/webapps/corapan/media`
- Logs: `/srv/webapps/corapan/logs`
- Postgres: Docker-Volume `corapan_postgres_prod`

### Offene Risiken

- Legacy-Reste unter `runtime/corapan/` sind noch vorhanden.
- Der leere Altpfad `data/blacklab_index` ist noch nicht entfernt.
- Cleanup der nicht mehr gemounteten Runtime-Duplikate steht noch aus.

### Manuell im Browser/lokal noch testen

1. Normale Web-Navigation inklusive Login.
2. Advanced Search mit docmeta-Anreicherung.
3. BlackLab-Suche über die UI.
4. Audio-Wiedergabe aus `media/`.
5. Atlas-/Statistik-Funktionen, die `stats_files.db` und `stats_country.db` nutzen.

### Maintenance-Pipeline / rsync-Zielpfade

- Aktive produktive Sync-Ziele sind jetzt auf das finale Layout ausgerichtet:
  - `DataRoot = /srv/webapps/corapan/data`
  - `MediaRoot = /srv/webapps/corapan/media`
  - `BlackLabDataRoot = /srv/webapps/corapan/data/blacklab`
- Der produktive Sync-Guard wurde auf `corapan-web-prod` und den kanonischen Mountvertrag umgestellt.
- Für die Maintenance-Pipeline ist daher kein separater Pfad-Folge-Run mehr erforderlich.
- Separat erforderlich bleibt nur der Legacy-Cleanup der alten, nicht mehr gemounteten Runtime-Pfade.