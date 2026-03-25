# Operational Cycle 1

Datum: 2026-03-25

Scope:
- erster kontrollierter realer Betriebszyklus der refaktorierten Sync-Strecke
- produktive Zielpfade fuer Data und Media
- keine strukturellen Aenderungen waehrend des Laufs
- BlackLab nur beobachtet, nicht aktiv ausgefuehrt

## A. Ablauf Data

Ausgefuehrt wurde der normale refaktorierte Task-Einstieg:

- `app/scripts/deploy_sync/tasks/sync_data.ps1`

Beobachteter Lauf:

- Quelle: `C:\dev\corapan\data`
- Ziel: `/srv/webapps/corapan/data`
- Modus: Delta-Sync
- Start laut Summary: `2026-03-25T15:12:01.0691636+01:00`
- Ende laut Summary: `2026-03-25T15:12:45.9607128+01:00`
- Exit-Code: `1`

Positiv bestaetigt:

- Runtime-first-Mount-Guard schlug nicht unerwartet an
- Scope blieb auf die vorgesehenen Data-Pfade beschraenkt
- der Lauf verwendete repo-gebundenes cwRSync
- der Statistik-Upload erschien genau einmal als eigener Block
- geschuetzte Produktivdaten wurden weiterhin nicht direkt synchronisiert

Tatsaechlich bearbeitete Bereiche im Lauf:

- `data/db/public`
- `data/public/metadata`
- `data/exports`
- selektive Stats-DB-Behandlung
- einmaliger Block `Statistics Files`

Auffaelligkeit:

- der Kernlauf fuer `db/public`, `public/metadata` und `exports` lief durch
- der Lauf scheiterte erst im Statistik-Upload mit:
  `Es wurde kein Positionsparameter gefunden, der das Argument "/srv/webapps/corapan/data/public/statistics\/corpus_stats.json /srv/webapps/corapan/data/public/statistics\/viz_*.png 2>/dev/null || true'" akzeptiert.`

Einordnung:

- der Data-Lauf war operativ nicht voll erfolgreich
- der Fehler lag nicht in Guard, Mount-Verifikation oder cwRSync-Grundpfad, sondern im Statistik-Nachgangspfad nach dem eigentlichen Uploadblock

## B. Ablauf Media

Ausgefuehrt wurde der normale refaktorierte Task-Einstieg:

- `app/scripts/deploy_sync/tasks/sync_media.ps1`

Beobachteter Lauf:

- Quelle: `C:\dev\corapan\media`
- Ziel: `/srv/webapps/corapan/media`
- Modus: Delta-Sync
- Start laut Summary: `2026-03-25T15:12:54.7686443+01:00`
- Ende laut Summary: `2026-03-25T15:13:12.5586903+01:00`
- Exit-Code: `0`

Beobachtete Teilbereiche:

- `media/transcripts`
- `media/mp3-full`
- `media/mp3-split`

Positiv bestaetigt:

- cwRSync wurde im echten Produktionslauf verwendet
- kein Fallback wurde benoetigt
- grosse Baeume liefen stabil durch
- Laufzeit war plausibel fuer einen NoChange-nahen Delta-Lauf
- Ownership-Nachlauf lief erfolgreich

Beobachtete Laufzeiten im Terminal:

- `transcripts`: `00:00`
- `mp3-full`: `00:00`
- `mp3-split`: `00:03`
- Gesamtlauf laut Summary: rund `18` Sekunden

Operative Interpretation:

- die Lane wirkte stabil
- der Standardtransport ist im echten Betrieb wieder der korrekte cwRSync-Pfad
- grosse Dateien bzw. grosse Verzeichnisbaeume verursachten keinen instabilen Lauf

## C. Logging-Auswertung

Gepruefte Summaries:

- `app/scripts/deploy_sync/_logs/data_20260325_151201.json`
- `app/scripts/deploy_sync/_logs/media_20260325_151254.json`

Positiv:

- beide JSON-Summaries wurden geschrieben
- Pflichtfelder sind vorhanden:
  - `lane`
  - `source`
  - `target`
  - `transport`
  - `dryRun`
  - `startTime`
  - `endTime`
  - `exitCode`
  - `noChange`
  - `changeCount`
  - `deleteCount`
  - `fallbackUsed`

Data-Summary:

- `exitCode=1`
- `transport=rsync-cwrsync`
- `fallbackUsed=false`
- `changeCount=559`
- `deleteCount=53`

Media-Summary:

- `exitCode=0`
- `transport=rsync-cwrsync`
- `fallbackUsed=false`
- `changeCount=3080`
- `deleteCount=0`
- `noChange=false`

Bewertung der Nachvollziehbarkeit:

- die Feldstruktur stimmt
- die inhaltliche Deutung von `changeCount`, `deleteCount` und `noChange` ist im echten Betriebslauf derzeit nicht belastbar genug

Konkrete Beobachtungen dazu:

- im Media-Lauf zeigten die Diff-Zusammenfassungen fuer alle drei Verzeichnisse `Neu: 0, Geaendert: 0, Geloescht: 0`
- trotzdem meldet die Lane-Summary `changeCount=3080` und `noChange=false`
- im Data-Lauf zeigt die Konsole keinen expliziten Delete-Vorgang, die Summary aber `deleteCount=53`

Schluss:

- das Logging ist als Struktur vorhanden und funktionsfaehig
- die Zaehllogik fuer Laufmetriken ist fuer echte NoChange- oder Near-NoChange-Laeufe noch nicht sauber interpretierbar

## D. Auffaelligkeiten

1. Data-Lauf scheitert im Statistik-Nachgangspfad

- der Statistik-Upload wurde genau einmal angestossen
- Upload von `corpus_stats.json` und den `viz_*.png`-Dateien lief sichtbar an
- der Fehler trat danach im Nachgangspfad auf und beendete die Lane mit Exit-Code `1`

2. Summary-Metriken sind nicht konsistent genug

- Media-Summary markiert den Lauf nicht als `NoChange`, obwohl der beobachtete Diff davor genau darauf hindeutet
- Data-Summary meldet Deletes, die im sichtbaren Lauf nicht belegt sind

3. Keine unerwarteten Guard-Abbrueche

- Mount-Guard griff nicht falsch an
- Pfad-Scope wirkte kontrolliert
- keine falschen lokalen oder remote Zielpfade wurden angezeigt

4. Keine Transport-Regression

- cwRSync war im realen Lauf aktiv
- kein Rueckfall auf `tar-base64-legacy`
- kein Rueckfall auf `scp -O`

## E. Stabile Teile

Im ersten echten Betriebszyklus stabil belegt:

- Task-Einstiege delegieren korrekt in die aktive Implementierung
- Mount-Validierung blockiert den echten Produktionslauf nicht mehr faelschlich
- repo-gebundener cwRSync-Pfad funktioniert im Realbetrieb
- Media-Lane ist operativ lauffaehig
- grosse Media-Verzeichnisbaeume laufen ohne sichtbare Instabilitaet
- JSON-Summaries werden auch im echten Produktionslauf geschrieben

## F. Offene Probleme

1. Data-Lane nicht voll erfolgreich

- der Statistik-Nachgangspfad verursacht weiterhin einen echten Laufzeitfehler
- dadurch ist der erste reale Data-Zyklus nicht voll gruener Betriebsnachweis

2. NoChange- und Count-Auswertung noch nicht belastbar

- `changeCount`
- `deleteCount`
- `noChange`

sind in den Lane-Summaries aktuell nicht praezise genug, um reale Betriebslaeufe allein daraus sauber zu interpretieren

3. Legacy-Bewertung nur vorbereitbar, noch nicht freigabereif

Im ersten echten Zyklus wurden offensichtlich nicht benoetigt:

- `tar-base64-legacy` als Transportpfad
- `scp -O` als Fallback
- Force-Modi
- isolierte Testpfad-Freigabe `CORAPAN_SYNC_ALLOW_TEST_PATHS`
- BlackLab-bezogene Publish-Pfade

Weiterhin implizit genutzt wurden:

- Task-Wrapper unter `app/scripts/deploy_sync/tasks/`
- die weiterhin aktive Implementierung `sync_data.ps1` und `sync_media.ps1`
- `sync_core.ps1`
- `_lib/ssh.ps1`
- JSON-Summary-Logging unter `app/scripts/deploy_sync/_logs/`

Vorbereitung fuer spaeteren Legacy-Abbau:

- kein Fallback wurde in diesem Zyklus praktisch benoetigt
- trotzdem darf daraus noch kein Rueckbau abgeleitet werden, weil der Data-Lauf nicht voll erfolgreich war und die Summary-Metriken noch Interpretationsluecken haben
- ein gezielter Legacy-Abbau ist erst nach einem voll erfolgreichen Data-Zyklus und sauberer Laufmetrik-Auswertung sinnvoll vorbereitet