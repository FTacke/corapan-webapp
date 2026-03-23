# Phase D5 Cleanup

## Ausgangslage

- Startzeit: 2026-03-22
- Ziel des Cleanup-Runs: Nach erfolgreichem D4-Cutover nur noch nicht mehr produktiv genutzte Altlasten entfernen.
- Arbeitsregel: Erst prüfen und dokumentieren, dann löschen. Unklare Pfade werden nicht entfernt.

## Cleanup-Zielbild

- `/srv/webapps/corapan/app`
- `/srv/webapps/corapan/data/blacklab`
- `/srv/webapps/corapan/data/config`
- `/srv/webapps/corapan/data/public`
- `/srv/webapps/corapan/data/stats_temp`
- `/srv/webapps/corapan/media`
- `/srv/webapps/corapan/logs`
- keine produktive Nutzung mehr von `runtime/corapan/*`
- keine aktiven Legacy-`blacklab_index*`-Pfade mehr

## Vorgehen

1. Ausgangslage und aktive Mounts dokumentieren.
2. Löschkandidaten einzeln prüfen und klassifizieren.
3. Sicherheitsprüfung vor destruktiven Schritten durchführen.
4. Nur eindeutig obsolete Pfade entfernen.
5. Danach erneut Struktur, Mounts, Status und Logs verifizieren.

## Vor dem Cleanup: aktive Mounts

### Web (`corapan-web-prod`)

```text
/srv/webapps/corapan/data
/srv/webapps/corapan/data/config
/srv/webapps/corapan/logs
/srv/webapps/corapan/media
```

### BlackLab (`corapan-blacklab`)

```text
/srv/webapps/corapan/app/config/blacklab
/srv/webapps/corapan/data/blacklab/index
/var/lib/docker/volumes/27c67b7bc8d3e70f1f2cf682bb9017ad4fec4b321121f43ef66b8e7abd76eb96/_data
```

### Bewertung

- Kein aktiver Container-Mount zeigt mehr auf `runtime/corapan/*`.
- Kein aktiver Container-Mount zeigt auf `data/blacklab_index` oder auf eines der `blacklab_index.*`-Legacy-Verzeichnisse.
- Produktiv aktiv sind nur noch die kanonischen Pfade unter `/srv/webapps/corapan/data`, `/srv/webapps/corapan/media` und `/srv/webapps/corapan/logs`.

## Vor dem Cleanup: Kandidatenklassifikation

```text
/srv/webapps/corapan/runtime/corapan                                     non-empty   451M
/srv/webapps/corapan/data/blacklab_index                                  empty       0
/srv/webapps/corapan/data/blacklab_index.bad_2026-01-19_104135            non-empty   279M
/srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_003920            non-empty   279M
/srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558   empty       0
```

### Zusätzliche Inhaltsprüfung

- `runtime/corapan` ist nicht nur formal belegt, sondern enthält weiterhin Altbestände wie `exports/`, `docmeta.jsonl`, `data/blacklab_index`, `data/public`, `data/stats_temp` und weitere Restdaten.
- `data/blacklab_index.bad_2026-01-19_104135` enthält 75 Dateien.
- `data/blacklab_index.bak_2026-01-16_003920` enthält 74 Dateien.

## Vor dem Cleanup: Service- und Logprüfung

### Containerstatus

- `corapan-web-prod`: healthy
- `corapan-db-prod`: healthy
- `corapan-blacklab`: running

### Web-Health

```json
{"checks":{"auth_db":{"backend":"postgresql","error":null,"ms":10,"ok":true},"blacklab":{"error":null,"ms":42,"ok":true,"url":"http://corapan-blacklab:8080/blacklab-server"},"flask":{"ms":0,"ok":true}},"service":"corapan-web","status":"healthy"}
```

### Logbewertung

- Web-Logs zeigen normalen Live-Traffic, erfolgreiche `200`/`206`-Antworten sowie wiederholte erfolgreiche `/health`-Checks.
- BlackLab-Logs zeigen reguläre Requests gegen `/data/index` und erfolgreiche Query-Verarbeitung mit normalen Suchzeiten.
- PostgreSQL-Logs zeigen regulären Start und `database system is ready to accept connections`.
- In den Web-Logs erscheint weiterhin ein bereits bestehender Anwendungsfehler `Error in build_sentence_context: invalid literal for int() with base 10: ''`. Dieser Fehler ist nicht neu durch D4/D5 entstanden und liefert keinen Hinweis auf falsche Mounts oder eine laufende Nutzung der Legacy-Pfade.

## Löschentscheidung vor Ausführung

### Eindeutig löschbar

- `data/blacklab_index`
	- leer
	- nicht gemountet
	- produktiver BlackLab-Pfad ist bereits `data/blacklab/index`
- `data/blacklab_index.new.leftover_2026-01-15_193558`
	- leer
	- nicht gemountet
	- als historischer Leftover-Pfad ohne Inhalt eindeutig obsolet

### Nicht gelöscht in D5

- `runtime/corapan`
	- nicht gemountet, aber weiterhin inhaltlich umfangreich
	- enthält noch Altbestände, die als zusätzliche Rollback-/Forensik-Referenz betrachtet werden müssen
	- ohne gesonderte Freigabe kein sicherer Kandidat für vollständige Entfernung
- `data/blacklab_index.bad_2026-01-19_104135`
	- nicht gemountet, aber nicht leer
	- historischer Backup-/Fehlerstand; daher in D5 bewusst konservativ beibehalten
- `data/blacklab_index.bak_2026-01-16_003920`
	- nicht gemountet, aber nicht leer
	- historischer Backup-Stand; daher in D5 bewusst konservativ beibehalten

## Cleanup-Ausführung

Es werden nur die beiden leeren und eindeutig obsoleten Legacy-Verzeichnisse entfernt.

### Ausgeführter Schritt

```text
entfernt:
- /srv/webapps/corapan/data/blacklab_index
- /srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558
```

### Direktprüfung nach der Entfernung

```text
runtime/corapan EXISTS 451M
data/blacklab_index ABSENT
data/blacklab_index.bad_2026-01-19_104135 EXISTS 279M
data/blacklab_index.bak_2026-01-16_003920 EXISTS 279M
data/blacklab_index.new.leftover_2026-01-15_193558 ABSENT
```

## Nach dem Cleanup: Verifikation

### Containerstatus

- `corapan-web-prod`: Up, healthy
- `corapan-db-prod`: Up, healthy
- `corapan-blacklab`: Up, running

### Mounts nach dem Cleanup

#### Web (`corapan-web-prod`)

```text
/srv/webapps/corapan/data
/srv/webapps/corapan/data/config
/srv/webapps/corapan/logs
/srv/webapps/corapan/media
```

#### BlackLab (`corapan-blacklab`)

```text
/srv/webapps/corapan/app/config/blacklab
/srv/webapps/corapan/data/blacklab/index
/var/lib/docker/volumes/27c67b7bc8d3e70f1f2cf682bb9017ad4fec4b321121f43ef66b8e7abd76eb96/_data
```

### Health nach dem Cleanup

```text
WEB_HEALTH=healthy
BLACKLAB_STATUS=running
DB_HEALTH=healthy
```

```json
{"checks":{"auth_db":{"backend":"postgresql","error":null,"ms":1,"ok":true},"blacklab":{"error":null,"ms":77,"ok":true,"url":"http://corapan-blacklab:8080/blacklab-server"},"flask":{"ms":0,"ok":true}},"service":"corapan-web","status":"healthy"}
```

### Logprüfung nach dem Cleanup

- Web-Logs zeigen weiterhin normalen Live-Traffic, Audio-Auslieferung und erfolgreiche `/health`-Checks.
- BlackLab-Logs zeigen weiterhin periodische Requests und Scans auf dem kanonischen Pfad `/data/index`.
- PostgreSQL-Logs zeigen keine neuen Auffälligkeiten; der Dienst bleibt betriebsbereit.
- Es wurden durch das D5-Cleanup keine neuen mount-, datei- oder startbezogenen Fehler sichtbar.

## Abschlussbewertung D5

- D5 wurde erfolgreich und konservativ ausgeführt.
- Entfernt wurden ausschließlich zwei leere, ungemountete und eindeutig obsolete Legacy-Verzeichnisse.
- Nicht entfernt wurden `runtime/corapan`, `data/blacklab_index.bad_2026-01-19_104135` und `data/blacklab_index.bak_2026-01-16_003920`, weil diese weiterhin inhaltlich belegt sind und ohne separate Freigabe als historische Referenz-/Rollback-Bestände behandelt werden sollten.
- Der produktive Betrieb blieb während des gesamten Cleanup-Runs stabil.

## Ergebnis

Der produktive Cutover aus D4 bleibt intakt. Das D5-Cleanup hat die eindeutig leeren Altlasten entfernt und gleichzeitig die noch inhaltlich belegten Legacy-Bestände bewusst unangetastet gelassen.