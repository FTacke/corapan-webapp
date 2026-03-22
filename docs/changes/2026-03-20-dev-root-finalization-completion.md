# Dev Root Finalization Completion 2026-03-20

## Was wurde geaendert

- der aktive Dev-Postgres-Datenpfad wurde von `webapp/data/db/postgres_dev` nach `data/db/restricted/postgres_dev` migriert
- die kanonische Root-Compose-Datei mountet Postgres jetzt aus `data/db/restricted/postgres_dev`
- die alte webapp-venv wurde nach Prozessbereinigung vollstaendig entfernt
- die letzte aktive Dev-Compose-Referenz auf repo-lokale `runtime/corapan/media` wurde auf Root-`media` umgestellt
- die freigegebenen Legacy-Pfade `webapp/data`, `webapp/runtime` und `data/blacklab_export.duplicate_20260320` wurden physisch entfernt

## Warum

Nach den vorangegangenen Audits waren nur noch drei operative Blocker offen: der alte Postgres-Mount unter `webapp/data`, ein laufender Altprozess aus der webapp-venv und eine letzte Dev-Compose-Referenz auf repo-lokale Runtime-Media. Diese Welle beseitigt genau diese Restblocker ohne weiteren Strukturumbau auf Verdacht.

## Umgebung

- nur Development / lokaler Workspace
- keine Produktivserver geaendert

## Operative Auswirkung

- Dev-Postgres liest jetzt live aus dem Root-Pfad `data/db/restricted/postgres_dev`
- aktive Dev-Laufzeit nutzt keine Pfade mehr unter `webapp/data` oder `webapp/runtime`
- es existiert kein laufender Prozess mehr aus `webapp/.venv`

## Kompatibilitaet

- BlackLab blieb waehrend der Umstellung aktiv und gesund
- die App wurde nach der Migration erneut gestartet und Health/Auth/BLS erfolgreich validiert
- das echte Git-Root bleibt weiterhin `webapp/.git`; dieser Governance-Restpunkt ist bewusst nicht in derselben Welle migriert worden

## Follow-up

- Git-Root separat und bewusst von `webapp/` auf `CORAPAN/` heben