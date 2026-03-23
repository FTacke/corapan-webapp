# BlackLab Target Architecture And Migration Plan 2026-03-20

Datum: 2026-03-20
Umgebung: Produktionsnahe Ziel- und Migrationsplanung auf Basis vorhandener read-only Forensik
Scope: verbindliches BlackLab-Zielbild und umsetzbarer Migrationsplan ohne Live-Eingriff in diesem Run

## 1. Anlass / Entscheidung

Die vorhandenen State- und Forensik-Dokumente belegen fuer BlackLab weiterhin eine gemischte Produktionsrealitaet:

- der laufende BlackLab-Container liest den aktiven Suchindex top-level aus `/srv/webapps/corapan/data/blacklab_index`
- die Web-App liest `docmeta.jsonl` aus `/srv/webapps/corapan/runtime/corapan/data/blacklab_export/docmeta.jsonl`
- `runtime/corapan` ist laut [docs/state/instance-structure-unification-plan.md](instance-structure-unification-plan.md) Legacy und nicht Zielmodell
- `app/config/blacklab` ist produktive Konfiguration, aber kein Teil des BlackLab-Datenbaums

Damit besteht fuer BlackLab aktuell keine einheitliche operative Wahrheit. Diese Datei legt deshalb das verbindliche BlackLab-Zielbild fest und beschreibt die Migrationsreihenfolge von der heutigen gemischten Realitaet auf genau eine kanonische Datenstruktur.

Primaerbasis fuer diese Entscheidung sind:

- [docs/state/Welle_4_prod_inventory_summary.md](Welle_4_prod_inventory_summary.md)
- [docs/state/Welle_5_consumer_matrix_summary.md](Welle_5_consumer_matrix_summary.md)
- [docs/state/Welle_6_blacklab_writer_fix_summary.md](Welle_6_blacklab_writer_fix_summary.md)
- [docs/state/blacklab-path-inventory-2026-03-20.md](blacklab-path-inventory-2026-03-20.md)
- [docs/state/export-forensik-final.md](export-forensik-final.md)
- [docs/state/storage-cleanup-execution-2026-03-20-wave-d.md](storage-cleanup-execution-2026-03-20-wave-d.md)
- [docs/state/post-deploy-diagnostics-2026-03-20.md](post-deploy-diagnostics-2026-03-20.md)

## 2. Verbindliches Zielbild

Der kanonische BlackLab-Zielpfad fuer CORAPAN ist ausschliesslich:

```text
/srv/webapps/corapan/data/
  blacklab/
    index/
    export/
    backups/
    quarantine/
```

Verbindliche Festlegungen:

- `data/blacklab/index` ist der einzige kanonische produktive Hostpfad fuer den live gelesenen BlackLab-Index.
- `data/blacklab/export` ist der einzige kanonische Hostpfad fuer TSV-, Metadata- und `docmeta`-Exportartefakte fuer BlackLab.
- `data/blacklab/backups` ist der einzige kanonische Hostpfad fuer BlackLab-Backups.
- `data/blacklab/quarantine` ist der einzige kanonische Hostpfad fuer fehlerhafte, leftover- oder bad-Artefakte.
- `runtime/corapan/data/blacklab_export` ist nur Uebergangsrealitaet und nicht Ziel.
- `runtime/corapan/data/blacklab_index` ist kein Zielpfad.
- `app/config/blacklab` bleibt Konfiguration und ist nicht Teil des Datenbaums.

Es gibt fuer BlackLab kuenftig keine parallele Wahrheit mehr zwischen `runtime/corapan/data/*` und `data/*`.

## 3. Aktueller Ist-Zustand

### 3.1 Sicher belegte Live-Realitaet

Aus [docs/state/blacklab-path-inventory-2026-03-20.md](blacklab-path-inventory-2026-03-20.md) und [docs/state/Welle_4_prod_inventory_summary.md](Welle_4_prod_inventory_summary.md) ergibt sich:

- aktiver Live-Leser fuer den BlackLab-Index:
  - `/srv/webapps/corapan/data/blacklab_index`
- aktive BlackLab-Konfiguration:
  - `/srv/webapps/corapan/app/config/blacklab`
- aktiver Web-App-`docmeta`-Pfad:
  - `/srv/webapps/corapan/runtime/corapan/data/blacklab_export/docmeta.jsonl`
- produktiv paralleler Runtime-Indexbaum ohne belegten Live-Leser:
  - `/srv/webapps/corapan/runtime/corapan/data/blacklab_index`

### 3.2 Aktualisierung durch spaetere Forensik

Die aelteren Wellen 4 und 5 klassifizierten `/srv/webapps/corapan/data/blacklab_export` noch als vorhanden und unklar oder ungenutzt. Diese Realitaet wurde spaeter durch die gezielte Abschlussforensik und Wave D aktualisiert:

- [docs/state/export-forensik-final.md](export-forensik-final.md) klassifiziert `/srv/webapps/corapan/data/blacklab_export` als `UNUSED`
- [docs/state/storage-cleanup-execution-2026-03-20-wave-d.md](storage-cleanup-execution-2026-03-20-wave-d.md) dokumentiert die gezielte Entfernung genau dieses Pfads

Damit gilt fuer den Ist-Zustand am Ende dieser Dokumentationsbasis:

- top-level `blacklab_export` ist nicht mehr vorhanden
- runtime `blacklab_export` bleibt aktiv fuer die Web-App
- top-level `blacklab_index` bleibt der aktive BlackLab-Leserpfad

### 3.3 Bekannte Altartefakte

Aus [docs/state/blacklab-path-inventory-2026-03-20.md](blacklab-path-inventory-2026-03-20.md) sind fuer BlackLab zusaetzlich belegt:

- top-level Backups:
  - `/srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_003920`
- top-level Quarantaene-/Fehlerpfade:
  - `/srv/webapps/corapan/data/blacklab_index.bad_2026-01-19_104135`
  - `/srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558`
- runtime-Duplikate derselben Klassen:
  - `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bak_2026-01-16_003920`
  - `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bad_2026-01-19_104135`
  - `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558`

## 4. Soll-Ist-Mapping

| Aktueller Pfad | Aktueller Status | Zielpfad | Migrationsregel |
|---|---|---|---|
| `/srv/webapps/corapan/data/blacklab_index` | live | `/srv/webapps/corapan/data/blacklab/index` | aktiver Live-Index spaeter dorthin umhaengen; erst nach Repo- und Mount-Vorbereitung |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index` | duplicate, legacy | kein dauerhafter Zielpfad | erst Schreiber abschalten, dann Runtime-Duplikat kontrolliert abbauen |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` | live fuer Web-App, aber Legacy als Ort | `/srv/webapps/corapan/data/blacklab/export` | Web-App- und Build-/Deploy-Verbrauch auf Zielpfad migrieren |
| `/srv/webapps/corapan/data/blacklab_export` | bereits entfernt in Wave D | `/srv/webapps/corapan/data/blacklab/export` | kein Live-Move mehr; Zielpfad neu aus aktiver Runtime-Exportrealitaet herstellen |
| `/srv/webapps/corapan/data/blacklab_index.bak_*` | backup | `/srv/webapps/corapan/data/blacklab/backups/` | als Backup-Bestand uebernehmen |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bak_*` | duplicate backup, legacy | `/srv/webapps/corapan/data/blacklab/backups/` oder spaeter verwerfen | erst pruefen, ob inhaltlich redundant; keine automatische Uebernahme |
| `/srv/webapps/corapan/data/blacklab_index.bad_*` | quarantine | `/srv/webapps/corapan/data/blacklab/quarantine/` | als Fehlerartefakte in Quarantaene ueberfuehren |
| `/srv/webapps/corapan/data/blacklab_index.new.leftover_*` | leftover / failed staging | `/srv/webapps/corapan/data/blacklab/quarantine/` | nicht als Backup behandeln; als Quarantaene klassifizieren |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bad_*` | duplicate quarantine, legacy | `/srv/webapps/corapan/data/blacklab/quarantine/` oder spaeter verwerfen | erst Redundanz gegen Top-Level pruefen |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.new.leftover_*` | duplicate leftover, legacy | `/srv/webapps/corapan/data/blacklab/quarantine/` oder spaeter verwerfen | erst Redundanz gegen Top-Level pruefen |
| `/srv/webapps/corapan/app/config/blacklab` | live config | kein Datenzielpfad | bleibt Konfigurationspfad ausserhalb des BlackLab-Datenbaums |

## 5. Pfadklassifikation

### live

- `/srv/webapps/corapan/data/blacklab_index`
- `/srv/webapps/corapan/app/config/blacklab`
- `/srv/webapps/corapan/runtime/corapan/data/blacklab_export`

### legacy

- `/srv/webapps/corapan/runtime/corapan/data/blacklab_index`
- `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bak_*`
- `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bad_*`
- `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.new.leftover_*`
- `/srv/webapps/corapan/runtime/corapan/data/blacklab_export`

Hinweis:
`runtime/corapan/data/blacklab_export` ist funktional noch aktiv, bleibt aber in dieser Zielarchitektur trotzdem `legacy`, weil der Pfad nicht zum Zielmodell gehoert.

### duplicate

- `/srv/webapps/corapan/runtime/corapan/data/blacklab_index`
- Runtime-Backup-/bad-/leftover-Duplikate zu den Top-Level-Artefakten

### backup

- `/srv/webapps/corapan/data/blacklab_index.bak_*`
- zusaetzlich vorhandene `blacklab_index.backup_*` oder `blacklab_index.backup`-Varianten, falls sie bei der eigentlichen Migrationswelle noch vorhanden sind

### quarantine

- `/srv/webapps/corapan/data/blacklab_index.bad_*`
- `/srv/webapps/corapan/data/blacklab_index.new.leftover_*`
- zusaetzlich vorhandene `blacklab_index.new.bad_*` oder inhaltsgleiche Fehlpfade, falls sie bei der eigentlichen Migrationswelle noch vorhanden sind

## 6. No-Go-Bereiche

Folgende Bereiche sind fuer die BlackLab-Migration nicht umzudeuten oder still mitzuziehen:

- `/srv/webapps/corapan/app/config/blacklab`
  - bleibt Konfiguration
- `/srv/webapps/corapan/config/passwords.env`
  - bleibt Secrets-/Deploy-Sonderzone
- PostgreSQL/Auth-Volumes und DB-Pfade
- Analytics- und Stats-Kernpfade der Web-App
- allgemeine Runtime-Mounts ausserhalb der expliziten BlackLab-Export-/Index-Thematik
- das interne anonyme Docker-Volume auf Containerpfad `/data`

No-Go-Regeln:

- kein stiller Fallback auf `runtime/corapan/data/blacklab_*`
- keine zweite parallele BlackLab-Wahrheit nach Zielumschaltung
- keine Vermischung von Konfiguration und Datenbaum
- kein Server-Umbau vor vorherigen Repo-Anpassungen

## 7. Migrationsreihenfolge in Wellen

### Welle BL-0 - Zielmodell einfrieren

Ziel:
Das Zielmodell `data/blacklab/{index,export,backups,quarantine}` verbindlich dokumentieren.

Inhalt:

- diese Datei als verbindliche Planungsgrundlage nutzen
- `runtime/corapan` fuer BlackLab explizit als Legacy festhalten
- `app/config/blacklab` explizit als ausserhalb des Datenbaums festhalten

Stop-Kriterium:

- keine widerspruechliche Zielbeschreibung in `docs/state`

### Welle BL-1 - Repo-Pfade auf Zielstruktur vorbereiten

Ziel:
Alle Repo-seitigen BlackLab-Writer, Builder und Leser auf das kuenftige Zielmodell vorbereiten, ohne den Server noch umzubauen.

Inhalt:

- Export-Vorstufe auf `data/blacklab/export` umstellen
- lokaler Builder auf `data/blacklab/index` plus saubere Backup-/Quarantaene-Ziele umstellen
- Web-App-`docmeta`-Pfad fuer kuenftig `data/blacklab/export/docmeta.jsonl` vorbereiten
- Retention-/Publish-Skripte auf `data/blacklab/backups` und `data/blacklab/quarantine` vorbereiten

Stop-Kriterium:

- es gibt im Repo keinen BlackLab-Default mehr auf `runtime/corapan/data/blacklab_*`

### Welle BL-2 - Zielverzeichnisse auf dem Server anlegen

Ziel:
Die neue Hoststruktur unter `/srv/webapps/corapan/data/blacklab` anlegen, ohne den Live-Leser umzuschalten.

Inhalt:

- `index/`, `export/`, `backups/`, `quarantine/` anlegen
- noch keine Loeschung und keine Umhaengung des aktiven Live-Indexpfads

Stop-Kriterium:

- Zielverzeichnisse existieren mit dokumentierter Berechtigungs- und Ownership-Realitaet

### Welle BL-3 - Export- und docmeta-Verbrauch auf Zielpfad migrieren

Ziel:
Die aktive `docmeta`-Realitaet von runtime nach `data/blacklab/export` verschieben.

Inhalt:

- `runtime/corapan/data/blacklab_export` inhaltlich kontrolliert nach `data/blacklab/export` ueberfuehren
- Web-App- und Deploy-Verbrauch auf den Zielpfad umstellen
- pruefen, dass `docmeta.jsonl` und Export-Inputs nur noch an einer kanonischen Stelle liegen

Stop-Kriterium:

- Web-App liest `docmeta` ausschliesslich aus `data/blacklab/export`

### Welle BL-4 - Live-Indexpfad auf Zielstruktur umverdrahten

Ziel:
Den aktiven BlackLab-Leserpfad von `data/blacklab_index` auf `data/blacklab/index` ueberfuehren.

Inhalt:

- BlackLab-Mount und zugehoerige Pfadannahmen auf den Zielindex umstellen
- aktiven Index nach `data/blacklab/index` uebernehmen
- sicherstellen, dass Standard-Publish direkt in die neue Struktur schreibt

Stop-Kriterium:

- laufender BlackLab-Container liest nur noch `data/blacklab/index`

### Welle BL-5 - Backups und Quarantaene konsolidieren

Ziel:
Historische Backup- und Fehlerartefakte in die Zielstruktur uebernehmen und vereinheitlichen.

Inhalt:

- `*.bak_*`, `*.backup_*`, `*.backup` -> `data/blacklab/backups/`
- `*.bad_*`, `*.new.bad_*`, `*.new.leftover_*` -> `data/blacklab/quarantine/`
- Retention-Regeln nur noch gegen diese Zielverzeichnisse laufen lassen

Stop-Kriterium:

- keine verstreuten BlackLab-Backup- oder Quarantaene-Verzeichnisse mehr ausserhalb von `data/blacklab/*`

### Welle BL-6 - Legacy abschalten

Ziel:
Die alten Runtime- und Top-Level-Altpfade ausserhalb des Zielmodells kontrolliert ausser Betrieb nehmen.

Inhalt:

- `runtime/corapan/data/blacklab_index` als Legacy entfernen oder dauerhaft blockieren
- `runtime/corapan/data/blacklab_export` entfernen, sobald kein Leser und kein Deploy-Ziel mehr uebrig ist
- nur nach vollstaendiger Verifikation und ohne Parallelbetrieb

Stop-Kriterium:

- genau eine operative BlackLab-Datenwurzel bleibt uebrig: `data/blacklab/*`

## 8. Rollback-Prinzip

Rollback darf nie ueber implizite Parallelpfade erfolgen.

Verbindliche Regeln:

- Rollback muss immer auf expliziten, dokumentierten Backup-Artefakten beruhen
- `backups/` ist der einzige vorgesehene Rollback-Bereich fuer Index-Snapshots
- `quarantine/` ist kein Rollback-Bereich, sondern Fehlerablage
- Runtime-Duplikate sind kein zulassiger stiller Rueckfallpfad
- ein Rollback muss denselben aktiven Leserpfad wiederherstellen, nicht eine zweite Wahrheit aktivieren

## 9. Repo-Aenderungen, die vor Server-Umbau noetig sind

Pflicht vor dem ersten Server-Umbau:

1. BlackLab-Exportdefaults im Repo von `data/blacklab_export` auf `data/blacklab/export` umstellen.
2. Lokale Builder- und Stagingpfade von `data/blacklab_index*` auf `data/blacklab/index` plus klare Backup-/Quarantaene-Ziele umstellen.
3. Web-App-`docmeta`-Verbrauch von `runtime/corapan/data/blacklab_export/docmeta.jsonl` auf den kuenftigen Zielpfad `data/blacklab/export/docmeta.jsonl` vorbereiten.
4. Publish- und Retention-Skripte auf `data/blacklab/backups` und `data/blacklab/quarantine` ausrichten.
5. Alle Repo-Dokumente und Betriebsanleitungen, die noch `blacklab_index`, `blacklab_export`, `blacklab_index.backup*` oder `blacklab_index.bad*` als kanonische Struktur behandeln, auf das Zielmodell umstellen.
6. Alle stillen oder impliziten BlackLab-Fallbacks auf Runtime-Pfade entfernen.

Diese Repo-Aenderungen sind Voraussetzung, weil sonst ein Server-Umbau erneut parallele Wahrheiten oder verdeckte Rueckfallpfade erzeugen wuerde.

## 10. Server-Aenderungen, die spaeter noetig sind

Nach Abschluss der Repo-Vorbereitung werden spaeter noetig:

1. Zielverzeichnisse unter `/srv/webapps/corapan/data/blacklab/` anlegen.
2. Aktive Export-/`docmeta`-Artefakte in den Ziel-Exportpfad ueberfuehren.
3. Aktiven Live-Index in den Ziel-Indexpfad ueberfuehren.
4. BlackLab-Mounts und zugehoerige Server-Konfiguration auf den Ziel-Indexpfad umstellen.
5. Verstreute Backup- und Quarantaene-Artefakte unter `backups/` und `quarantine/` konsolidieren.
6. Runtime-Legacy-Pfade erst nach positiver Endverifikation ausser Betrieb nehmen.

Nicht Teil dieser spaeteren Server-Aenderungen:

- kein Umzug von `app/config/blacklab` in den Datenbaum
- kein Mischen von BlackLab-Datenmigration mit PostgreSQL/Auth/Analytics-Aenderungen

## 11. Verifikationsplan nach jeder Welle

### Nach BL-0

- pruefen, dass dieses Zielbild in `docs/state` konsistent ist
- pruefen, dass `runtime/corapan` fuer BlackLab nirgends als Zielmodell dokumentiert bleibt

### Nach BL-1

- Repo-Suche: keine BlackLab-Defaults mehr auf `runtime/corapan/data/blacklab_*`
- Repo-Suche: keine kanonische Doku mehr auf alte Einzelpfade statt `data/blacklab/*`

### Nach BL-2

- Hostinventur: `index/`, `export/`, `backups/`, `quarantine/` existieren
- noch kein Live-Leser auf den neuen Indexpfad, solange BL-4 nicht freigegeben ist

### Nach BL-3

- Web-App-`docmeta`-Verbrauch liest erfolgreich aus `data/blacklab/export/docmeta.jsonl`
- kein aktiver Leser und kein Deploy-Ziel mehr auf `runtime/corapan/data/blacklab_export`

### Nach BL-4

- `docker inspect` und BlackLab-Logs belegen den neuen Live-Leserpfad `data/blacklab/index`
- BlackLab-Queries gegen `BLS_BASE_URL` liefern weiterhin erfolgreiche Treffer

### Nach BL-5

- verstreute `bak`, `backup`, `bad`, `new.bad` und `leftover`-Artefakte sind nur noch unter `backups/` oder `quarantine/` vorhanden
- Retention-Helfer pruefen nur noch die Zielverzeichnisse

### Nach BL-6

- keine aktive BlackLab-Reader-/Writer-/Deploy-Realitaet mehr auf `runtime/corapan/data/blacklab_*`
- kein zweiter paralleler BlackLab-Datenbaum mehr ausserhalb von `data/blacklab/*`

## 12. Executive Summary

Die vorhandene Forensik belegt fuer BlackLab derzeit genau zwei aktive Wahrheiten, die nicht zusammenpassen: Der Suchindex wird live top-level aus `/srv/webapps/corapan/data/blacklab_index` gelesen, waehrend die Web-App `docmeta` aus `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` liest. Das ist kein Zielmodell, sondern eine Uebergangsrealitaet mit parallelen Pfaden.

Das verbindliche Zielbild fuer CORAPAN lautet daher ausschliesslich `data/blacklab/{index,export,backups,quarantine}` unter `/srv/webapps/corapan/data/`. `runtime/corapan` bleibt fuer BlackLab Legacy, `app/config/blacklab` bleibt Konfiguration ausserhalb des Datenbaums.

Die Migration muss in getrennten Wellen erfolgen: erst Repo-Pfade und Defaults vereinheitlichen, dann Zielverzeichnisse auf dem Server anlegen, danach Export/docmeta migrieren, erst spaeter den Live-Indexpfad umhaengen und zuletzt Legacy abbauen. Ohne diese Reihenfolge wuerde erneut eine verdeckte Parallelrealitaet entstehen.