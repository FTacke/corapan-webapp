# Post-Refactor Validation Report

Datum: 2026-03-25

Scope:
- praktische Validierung und Härtung der refaktorierten lokalen Produktions-Sync-Strecke
- keine produktiven Zielpfade für Data/Media-Tests
- keine Container-Starts/-Stops, keine Deploys, keine Migrationsläufe
- BlackLab nur read-only geprüft, soweit ohne lokales `index.build` möglich

## A. Executive Summary

Die refaktorierte Struktur ist nach praktischer Validierung für Data und Media jetzt lauffähig und belastbar genug, um als aktive lokale Sync-Strecke weitergeführt zu werden.

Praktisch belegt wurden:

- neue Task-Einstiege für Data und Media funktionieren im DryRun
- Logging-Vertrag mit JSON-Summaries wird für Data, Media und BlackLab erfüllt
- Guard-Verhalten für leere Quellen und unplausible Zielpfade greift
- echter Live-Transfer über repo-gebundenes cwRSync funktioniert wieder
- `scp -O` funktioniert weiterhin als Fallback
- Media-Einzelfall mit nur einer Datei läuft jetzt korrekt und erkennt im zweiten Lauf `NoChange`

Wesentliche Restbefunde:

- BlackLab-DryRun ist lokal weiterhin durch fehlendes `data/blacklab/quarantine/index.build` blockiert
- der produktive BlackLab-Hits-Endpoint liefert aktuell HTTP 500, weil dem laufenden Container die BlackLab-Server-Konfiguration unter `/etc/blacklab` fehlt
- der DryRun-Summary-Vertrag ist erfüllt, bildet aber erwartete Änderungen nicht tief aus; er ist als Minimalvertrag, nicht als Voll-Audit, zu lesen

## B. Teststrategie und Repräsentativität

Ziel war kein Vollsync produktiver Bestände, sondern ein praktischer Repo-naher Nachweis der refaktorierten Kernpfade mit kleinen, kontrollierten und aussagekräftigen Stichproben.

Verwendete Nachweisarten:

- DryRun über die neuen Task-Einstiege
- direkte Guard-Tests auf Core-Ebene
- isolierte Live-Transfers nach `/srv/webapps/corapan/tmp_sync_test/post_refactor_validation*`
- read-only BlackLab-Prüfungen über SSH und HTTP gegen die laufende Produktion

Bewusst ausgewählte Repräsentanten:

- Data: drei kleine Metadaten-Dateien aus `data/public/metadata`
- Media/Transcripts: drei reale Transcript-Dateien aus `media/transcripts`
- Media/Audio: eine 85,3-MB-Datei `medium.mp3` als Ein-Datei- und Resume-relevanter Pfadvertreter
- BlackLab: DryRun-Wiring plus produktiver Hits-Check statt vollständigem Publish

Nicht vollständig getestet wurde:

- ein echter produktiver Data-Sync
- ein echter produktiver Media-Sync
- ein vollständiger lokaler BlackLab-Publish mit neuem Staging-Index
- ein erneuter manueller Abbruch-/Resume-Test mit sehr großer Datei, weil die Resume-Semantik bereits im vorangehenden Live-Validierungsbericht belegt wurde und der Refactor die `--partial`-Flags nicht entfernt hat

## C. Data-Lane Validierung

DryRun über den refaktorierten Task-Einstieg:

- `app/scripts/deploy_sync/tasks/sync_data.ps1 -DryRun`
- Ergebnis: erfolgreich
- Pre-Sync-Mount-Guard lief durch
- Zielwurzeln wurden korrekt als `/srv/webapps/corapan/data` ausgewiesen
- Statistik-Sonderpfad wurde genau einmal ausgeführt

Praktischer DryRun-Befund für Statistik-Dateien:

- Quelle: `data/public/statistics`
- `viz_*.png`: 28 Dateien
- plus `corpus_stats.json`
- Gesamt: 29 allowlist-basierte Upload-Dateien

Isolierter Live-Test des gemeinsamen Core-Pfads:

- lokale Quelle: repräsentative Teilmenge unter `tmp/post-refactor-validation-b/data/public/metadata`
- Remote-Ziel: `/srv/webapps/corapan/tmp_sync_test/post_refactor_validation2/data/metadata`
- Ergebnis: erfolgreicher Live-Transfer über `rsync-cwrsync`
- Ergebnisobjekt: `Transport=rsync-cwrsync`, `FallbackUsed=false`

Bewertung:

- neue Task-Verkabelung funktioniert
- Data-Lane bleibt scope-stabil
- Statistik-Upload driftet nicht erneut in einen zweiten Orchestrator-Pfad ab

## D. Media-Lane Validierung

DryRun über den refaktorierten Task-Einstieg:

- `app/scripts/deploy_sync/tasks/sync_media.ps1 -DryRun`
- Ergebnis: erfolgreich
- Zielwurzeln wurden korrekt als `/srv/webapps/corapan/media` ausgewiesen
- relevante Unterziele: `transcripts`, `mp3-full`, `mp3-split`

Isolierter Live-Test für `transcripts`:

- lokale Quelle: drei reale Transcript-Dateien
- Remote-Ziel: `/srv/webapps/corapan/tmp_sync_test/post_refactor_validation2/media/transcripts`
- Ergebnis: erfolgreicher Live-Transfer über `rsync-cwrsync`
- Ergebnisobjekt: `Transport=rsync-cwrsync`, `FallbackUsed=false`

Isolierter Live-Test für `mp3-full`:

- lokale Quelle: eine 85,3-MB-Datei `medium.mp3`
- Remote-Ziel: `/srv/webapps/corapan/tmp_sync_test/post_refactor_validation3/media/mp3-full`
- erster Lauf: erfolgreicher Transfer über `rsync-cwrsync`
- zweiter Lauf mit `-SkipIfNoChanges`: erfolgreicher No-Change-Lauf, `NoChange=true`

Bewertung:

- Media-Lane läuft auch praktisch über den refaktorierten Core-Pfad
- der Ein-Datei-Fall ist jetzt korrekt behandelt
- `--partial` bleibt im aktiven rsync-Pfad erhalten und wurde nicht aus der Transportlogik entfernt

## E. BlackLab-Lane Validierung

DryRun über den refaktorierten Wrapper-/Task-Pfad:

- `maintenance_pipelines/_2_deploy/publish_blacklab.ps1 -SkipExport -SkipBuild -DryRun`
- Task-Wiring erreicht den refaktorierten Publish-Pfad korrekt
- JSON-Summary wird auch auf Fehlerpfaden geschrieben

Lokaler Blocker:

- `data/blacklab/quarantine/index.build` fehlt lokal
- damit ist ein vollständiger BlackLab-DryRun aktuell nicht möglich
- dieser Blocker betrifft die lokale Vorbedingung, nicht das Task-Wiring

Read-only Produktionsprüfung des Hits-Pfads:

- geprüfte URL-Form: `http://127.0.0.1:8081/blacklab-server/corpora/corapan/hits?patt=%5Bword%3D%22casa%22%5D&number=1`
- Ergebnis: HTTP 500
- Response und Container-Logs zeigen keinen Query-Fehler, sondern Konfigurationsfehler
- Fehlerbild: `Couldn't find blacklab-server.(json|yaml) in BlackLab config dir /etc/blacklab`

Bewertung:

- die neue Hits-Query-Validierung im Publish-Script ist richtig verschärft und deckt einen realen Produktionsfehler auf
- BlackLab ist damit nicht nur lokal am fehlenden `index.build` blockiert, sondern operativ zusätzlich durch fehlende Laufzeitkonfiguration im aktiven Container belastet

## F. Guard-Validierung

Direkt getestete Guards:

- Empty-Source-Guard
- Remote-Path-Plausibility-Guard

Belegte Ergebnisse:

- leere Quelle `tmp/sync-validation/src-empty` wurde korrekt abgelehnt
- Fehlermeldung: `Empty source guard test: C:\dev\corapan\tmp\sync-validation\src-empty`
- unplausibler Zielpfad `/tmp/not-corapan` wurde korrekt abgelehnt
- Fehlermeldung: `Refusing implausible remote path: /tmp/not-corapan`

Zusatzhärtung:

- isolierte Testpfade unter `/srv/webapps/corapan/tmp_sync_test` sind jetzt nur per `CORAPAN_SYNC_ALLOW_TEST_PATHS=1` zulässig
- produktive Standardpfade bleiben dadurch die Default-Erwartung

## G. Logging-Vertrag

Geprüfte Summary-Dateien:

- `app/scripts/deploy_sync/_logs/data_20260325_145622.json`
- `app/scripts/deploy_sync/_logs/media_20260325_145623.json`
- `app/scripts/deploy_sync/_logs/blacklab_20260325_145052.json`

Alle drei Summaries enthalten die dokumentierten Pflichtfelder:

- `lane`
- `source`
- `target`
- `transport`
- `dryRun`
- `exitCode`
- `noChange`
- `changeCount`
- `deleteCount`
- `fallbackUsed`

Bewertung:

- der Minimalvertrag aus `docs/rsync/logging_contract.md` ist praktisch belegt
- DryRun- und Fehlerpfade schreiben belastbare JSON-Summaries
- Wrapper-Transcripts bleiben weiterhin ergänzend sinnvoll, ersetzen die JSON-Summaries aber nicht

## H. Transport- und Fallback-Verhalten

Standardtransport:

- nach Korrektur der Repo-Root-Auflösung nutzt der Live-Pfad wieder repo-gebundenes cwRSync unter `app/tools/cwrsync/bin/`
- praktisch belegt für Data-Metadata, Media-Transcripts und Media-`mp3-full`

Separat validierter Fallback:

- `Invoke-SCP` nutzt weiterhin `scp -O`
- praktischer Test nach `/srv/webapps/corapan/tmp_sync_test/post_refactor_validation3/scp/` erfolgreich
- Ergebnisbestätigung: `SCP_OK`

Nicht als Standard behandelt:

- `tar|ssh` bleibt BlackLab-spezifisch und ist nicht Standard für Data oder Media
- `tar-base64-legacy` blieb als Kompatibilitätsfallback im Code erhalten, wurde nach Wiederherstellung des cwRSync-Pfads aber nicht mehr als Standardpfad gewählt

## I. Praktisch gefundene und behobene Defekte

Während der Validierung wurden echte Post-Refactor-Fehler gefunden und behoben:

1. Parserfehler in `core/guards.ps1`
- Ursache: fehlerhafte String-Interpolation in der Throw-Nachricht
- Wirkung: Data- und Media-Tasks brachen sofort ab

2. falscher lokaler BlackLab-Staging-Pfad
- Ursache: falsche Repo-/Workspace-Root-Auflösung
- Wirkung: BlackLab suchte `app/data/...` statt `data/...`

3. falsche Mount-Erwartung im Runtime-Guard
- Ursache: Guard erwartete `/srv/webapps/corapan/config -> /app/config`
- reale Produktion mountet `/srv/webapps/corapan/data/config -> /app/config`

4. fragiler `docker inspect`-Mount-Parser
- Ursache: textbasierte Parsing-Logik und fehlerhafte JSON-Array-Behandlung
- Wirkung: reale Mounts wurden als fehlend klassifiziert

5. historisch harter SSH-Key-Default
- Ursache: lokaler Default `~/.ssh/marele` war auf der realen Maschine nicht vorhanden
- Wirkung: praktische Ausführung scheiterte vor dem eigentlichen Transport

6. falsche Tool-Root-Auflösung in `sync_core.ps1`
- Ursache: `sync_core.ps1` löste auf Workspace-Root statt App-Root auf
- Wirkung: cwRSync wurde unter `C:\dev\corapan\tools\...` gesucht und nicht gefunden

7. Ein-Datei-Manifest-Bug
- Ursache: Manifest-Funktionen kollabierten Ein-Element-Arrays zu Einzelobjekten
- Wirkung: `Count`-basierte Diff-Logik brach bei `mp3-full` mit nur einer Datei

Bewertung:

- diese Defekte waren echte Laufzeitfehler
- sie wurden nicht nur dokumentiert, sondern bis zum praktischen Erfolgsnachweis korrigiert

## J. Legacy-Klassifikation

### A. Aktiv kanonisch behalten

- `app/scripts/deploy_sync/core/*`
- `app/scripts/deploy_sync/tasks/*`
- `app/scripts/deploy_sync/sync_data.ps1`
- `app/scripts/deploy_sync/sync_media.ps1`
- `app/scripts/deploy_sync/publish_blacklab_index.ps1`
- `maintenance_pipelines/_2_deploy/deploy_data.ps1`
- `maintenance_pipelines/_2_deploy/deploy_media.ps1`
- `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`
- `docs/rsync/README.md`
- `docs/rsync/transport_matrix.md`
- `docs/rsync/safety_contract.md`
- `docs/rsync/logging_contract.md`
- `docs/rsync/refactor_implementation_report.md`
- `docs/rsync/post_refactor_validation_report.md`

### B. Übergangsweise behalten

- `app/scripts/deploy_sync/_lib/ssh.ps1`
- `app/scripts/deploy_sync/sync_core.ps1`
- `app/scripts/deploy_sync/legacy/20260116_211115/*`

Begründung:

- `_lib/ssh.ps1` bleibt noch Brücke für aktive Skripte
- `sync_core.ps1` bleibt die noch aktive Implementierung hinter den Task-Einstiegen
- `legacy/20260116_211115/*` sollte erst nach einem weiteren stabilen Zyklus archivarisch verschoben werden, nicht mitten im Härtungsfenster

### C. Später archivieren

- ältere oder widersprüchliche Sync-Analyseartefakte, sobald ihr Inhalt vollständig in `docs/rsync/README.md`, `refactor_implementation_report.md` und diesem Bericht aufgegangen ist
- historische Wrapper-Dokumente, die nur noch Übergangskontext liefern

### D. Später entfernen

- harte historische SSH-Key-Annahmen in Doku, sobald eine parametrisierte Known-Hosts-/Identity-Regel sauber dokumentiert und operatorseitig belegt ist
- Altpfadannahmen, die `app/data` oder generische Workspace-`tools` implizieren
- Legacy-Reste nur dann, wenn mindestens ein weiterer stabiler Validierungszyklus ohne Rückgriff auf sie gelaufen ist

## K. Skill- und Governance-Folgerungen

Aus dieser Validierung folgen zwei dauerhafte Regeln:

1. Änderungen an Sync-Lanes dürfen nicht nur per statischer Code-Lektüre beurteilt werden.
2. Legacy-Rückbau ist erst zulässig, wenn der refaktorierte Standardpfad praktisch bewiesen und der Fallback-Vertrag noch intakt ist.

Konkret nachgezogen wurden:

- Dokumentation des Post-Refactor-Nachweises in `docs/rsync/`
- Ergänzung der Governance, dass Sync-Lane-Arbeiten den Skill `server-sync-production-lanes` verwenden müssen
- Ergänzung des Skills um Mindestvalidierung nach Änderungen an Transport, Guards oder Task-Verkabelung

## L. Gesamturteil und nächste Schwelle

Gesamturteil:

- Data und Media sind nach dieser Härtungsrunde praktisch validiert
- der refaktorierte Standardpfad ist jetzt nicht nur strukturell, sondern auch operativ nachgewiesen
- `scp -O` bleibt als funktionierender Fallback erhalten
- BlackLab ist scriptseitig besser abgesichert, aber aktuell von zwei operativen Vorbedingungen abhängig:
  - lokalem `data/blacklab/quarantine/index.build`
  - einer funktionsfähigen Produktionskonfiguration unter `/etc/blacklab`

Die nächste sinnvolle Freigabeschwelle ist nicht weiterer Refactor, sondern ein kleiner stabiler Betriebszyklus:

- mindestens ein normaler Data-Lauf
- mindestens ein normaler Media-Lauf
- und danach erst Bewertung, welche Übergangsartefakte tatsächlich aus B nach C oder D verschoben werden dürfen