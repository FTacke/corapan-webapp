# Root Consistency Audit Cleanup 2026-03-20

## Was wurde geaendert

- Root-`.github`-Instructions auf echte Workspace-Pfade unter `webapp/` ausgerichtet
- nicht-produktive Root-Workflows fuer ein kuenftiges CORAPAN-Root-Modell mit `webapp/` als Arbeitsverzeichnis vorbereitet
- die alternative Dev-Compose-Datei unter `webapp/` auf Root-BlackLab-Config und Root-Postgres-Pfad korrigiert
- verbliebene Hilfsskripte mit Root-`.venv`- bzw. Root-`data/exports`-Logik synchronisiert
- gezielte Audit-Doku fuer Git-Root, `.venv`, `.github`, `webapp/data` und repo-lokale Runtime-Pfade erstellt

## Warum

Die Workspace-Struktur war nur teilweise kanonisiert: laufende Container und einige Hilfspfade zeigten weiterhin auf `webapp`-interne Altpfade, waehrend Root-`.github` bereits nach `CORAPAN/` verschoben war. Ziel dieses Runs war keine neue Umbauwelle, sondern die saubere Trennung zwischen wirklich aktiv, klar legacy und bereits bereinigbar.

## Umgebung

- nur Development / lokaler Workspace
- keine Aenderung an Produktivservern oder Deploy-Livezustand

## Operative Auswirkung

- neue Starts ueber die verbleibende `webapp/docker-compose.dev-postgres.yml` zeigen kuenftig auf Root-Config bzw. den kanonischen Root-Postgres-Zielpfad
- Root-`.github` passt besser zur realen Workspace-Logik, bleibt aber bis zu einer echten Git-Root-Migration ausserhalb des versionierten Repos
- inaktive Altinhalte aus `webapp/data/exports` wurden nach `data/exports` ueberfuehrt
- das historische BlackLab-Archiv aus `webapp/data/_legacy_blacklab_invalid` wurde nach `data/blacklab/quarantine/webapp_legacy_blacklab_invalid_20260320` ueberfuehrt
- `webapp/data` konnte nicht vollstaendig entfernt werden, weil der laufende Postgres-Container weiterhin `webapp/data/db/postgres_dev` nutzt

## Kompatibilitaet

- der produktive Deploy-Workflow unter Root-`.github/workflows/deploy.yml` wurde bewusst nicht umgebaut, weil er prod-spezifisch ist und das aktuelle Git-Root weiterhin `webapp/` bleibt
- repo-lokale `runtime/corapan`-Pfade wurden in diesem Run nicht pauschal geloescht; nur ihre aktive Nutzung wurde neu bewertet

## Follow-up

- echte Git-Root-Migration erst separat und bewusst angehen
- Postgres-Datenpfad von `webapp/data/db/postgres_dev` erst nach geplantem Container-Neustart und Verifikation auf den Root-Pfad final bereinigen
- legacy-venv erst entfernen, wenn der noch laufende Prozess aus `webapp/.venv` beendet ist