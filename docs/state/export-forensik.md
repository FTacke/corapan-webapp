# Export-Forensik Status 2026-03-20

## Ergebnis

- Runtime-Export: `/srv/webapps/corapan/runtime/corapan/data/blacklab_export`
  - Klassifikation: `ACTIVE_CANONICAL`, `READ_TARGET`, `WRITE_TARGET`
- Top-Level-Export: `/srv/webapps/corapan/data/blacklab_export`
  - Klassifikation: `UNCLEAR`

## Belegte Kernaussagen

1. Die Web-App liest `docmeta.jsonl` über `get_docmeta_path()` und `advanced_api` aus dem Runtime-Root.
2. Produktiv ist `CORAPAN_RUNTIME_ROOT=/app`; `/srv/webapps/corapan/runtime/corapan/data` ist nach `/app/data` gemountet.
3. Der exakte Host-Lesepfad der Web-App ist daher `/srv/webapps/corapan/runtime/corapan/data/blacklab_export/docmeta.jsonl`.
4. `sync_data.ps1` deployt `blacklab_export` nach `/srv/webapps/corapan/runtime/corapan/data/blacklab_export`.
5. BlackLab-Live-Betrieb nutzt den Top-Level-Index unter `/srv/webapps/corapan/data/blacklab_index`, nicht den Export.
6. Für `/srv/webapps/corapan/data/blacklab_export` ist im erlaubten Scope kein realer Leser und kein realer Schreiber belegt.

## Writer-Kette

Belastbar belegt ist nur diese Produktionskette:

- lokaler Sync-Quellpfad: `<CORAPAN_RUNTIME_ROOT>/data/blacklab_export`
- Deploy-Skript: `scripts/deploy_sync/sync_data.ps1`
- Remote-Ziel: `/srv/webapps/corapan/runtime/corapan/data/blacklab_export`

Nicht belegt ist eine direkte Produktions-Writer-Kette auf `/srv/webapps/corapan/data/blacklab_export`.

## Entscheidung

- Runtime-Export: nicht löschbar
- Top-Level-Export: bedingt löschbar, und wenn ein Pfad zuerst geprüft wird, dann dieser

## Fehlende Bedingung

Vor einer Löschfreigabe des Top-Level-Exports fehlt noch:

- ein letzter gezielter Ausschluss, dass kein externer Legacy-/Ops-Job außerhalb des hier erlaubten Scopes `/srv/webapps/corapan/data/blacklab_export` nutzt

## Verweis

Details: `docs/blacklab-export-usage-forensics-2026-03-20.md`