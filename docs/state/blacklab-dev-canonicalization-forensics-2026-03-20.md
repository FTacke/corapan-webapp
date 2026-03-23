# BlackLab Dev Canonicalization Forensics 2026-03-20

Datum: 2026-03-20
Umgebung: Development / Repository only
Scope: Dev-Skripte, Dev-Compose, Tests, direkt betroffene Dev-Doku und lokaler Repo-Datenbaum

## 1. Ziel

Dev soll lokal nur noch das kanonische BlackLab-Zielbild als Sollstruktur verwenden:

- `data/blacklab/index`
- `data/blacklab/export`
- `data/blacklab/backups`
- `data/blacklab/quarantine`

Kein Prod-Cutover, keine Produktivpfade, keine Annahme eines bereits erfolgten Server-Swaps.

## 2. Forensik

### Kanonische aktive Referenzen

- `src/app/runtime_paths.py`
  - `get_docmeta_path()` liest `data/blacklab/export/docmeta.jsonl`
- `src/scripts/blacklab_index_creation.py`
  - Export-Defaults zeigen auf `data/blacklab/export/*`
- `scripts/blacklab/build_blacklab_index.ps1`
  - benutzt `data/blacklab/{export,index,backups,quarantine}`
- `scripts/blacklab/build_blacklab_index.sh`
  - benutzt denselben kanonischen Baum
- `docker-compose.dev-postgres.yml`
  - mountet `./data/blacklab/index:/data/index/corapan:ro`

### Legacy im lokalen Repo-Datenbaum

Beim forensischen Check von `data/` wurden noch folgende Altartefakte gefunden:

- `data/blacklab_export/`
- `data/blacklab_index/`
- `data/blacklab_index.backup/`
- `data/blacklab_index.backup_*`
- `data/blacklab_index.bad_*`
- `data/blacklab_index.new.bad_*`
- `data/blacklab_index.testbuild/`
- `data/blacklab_index.testbuild.bak_*`

Diese Pfade sind lokaler Legacy-Zustand aus frueheren Builds und nicht mehr die Quelle der Wahrheit.

### Unklare oder gemischte Referenzen

- `infra/docker-compose.dev.yml`
  - bleibt als alternative, nicht-kanonische Dev-Compose bestehen
  - enthaelt weiterhin repo-lokale Runtime-Mount-Fallbacks fuer Media
  - wurde in diesem Run nicht zum kanonischen Dev-Startpfad erhoben

### Tote oder historische Referenzen

- `scripts/deploy_sync/legacy/**`
  - historische Publish-Dokumentation und alte Remote-Pfade
- diverse historische State-/Audit-Dokumente unter `docs/state/`, `docs/data_cleanup/`, `docs/blacklab/`
  - enthalten bewusst historische Pfade als Forensik oder Postmortem-Kontext

## 3. Umgesetzte Bereinigung

- Repo-Skelett fuer `data/blacklab/{index,export,backups,quarantine}` angelegt und via `.gitkeep` verankert
- `.gitignore` so erweitert, dass nur das kanonische BlackLab-Skelett im Repo sichtbar bleibt, nicht die Artefakte
- expliziten lokalen Migrationshelfer hinzugefuegt:
  - `scripts/blacklab/migrate_legacy_blacklab_dev_layout.ps1`
- `scripts/dev-start.ps1` und `scripts/dev-setup.ps1` haerten den Start jetzt gegen ein un-migriertes Legacy-Layout
- aktive Tests und Debug-Skripte auf kanonische Pfade bzw. `BLS_CORPUS=corapan` umgestellt
- direkt betroffene Dev-Doku auf kanonische Pfade und korrekte Script-Pfade aktualisiert

## 4. Bewusst nicht umgestellt

- keine Aenderung an produktiven Serverpfaden oder Prod-Mounts
- kein automatischer Move lokaler Daten bei Dev-Start
- kein harter Umbau von `infra/docker-compose.dev.yml` auf kanonische Runtime-Semantik, weil diese Datei nicht der kanonische Dev-Startpfad ist

## 5. Ergebnis

Im aktiven Dev-Code und in den aktiven Dev-Skripten gilt jetzt ausschliesslich `data/blacklab/*` als Sollbild. Verbleibende Altpfade sind lokaler Legacy-Datenzustand oder historische Dokumentation und wurden entsprechend begrenzt.