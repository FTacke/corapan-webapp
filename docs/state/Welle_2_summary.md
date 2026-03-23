# Welle 2 Summary

Datum: 2026-03-20
Umgebung: Development lokal
Zielpfade:

- DATA_ROOT -> `C:\dev\corapan\data`
- MEDIA_ROOT -> `C:\dev\corapan\media`

## 7.1 Zusammenfassung

Gefixt wurde:

- die aktive Dev-Web-App faellt nicht mehr implizit auf `webapp/runtime/corapan` zurueck
- Atlas liest in Dev nicht mehr nur aus `metadata/latest/tei`, sondern nutzt kontrolliert `metadata/latest`, wenn dort die Recording-Dateien liegen
- `docmeta.jsonl` liegt jetzt zusaetzlich am kanonischen Dev-Pfad `C:\dev\corapan\data\blacklab_export\docmeta.jsonl`
- Advanced Search laedt seinen docmeta-Cache aus dem aktiven `DATA_ROOT`
- die aktiven Dev-Skripte `dev-start.ps1` und `dev-setup.ps1` verwenden nur noch den kanonischen Workspace-Root mit `data/` und `media/`
- `runtime/corapan` ist in den aktiven Dev-Resolvern und Dev-Skripten inaktiv

Verbleibende Legacy-Pfade:

- `C:\dev\corapan\webapp\config\blacklab` bleibt ACTIVE_LEGACY fuer den Dev-BlackLab-Container
- `C:\dev\corapan\webapp\data\blacklab_index` bleibt ACTIVE_LEGACY fuer den Dev-BlackLab-Container
- `C:\dev\corapan\webapp\data\blacklab_export` bleibt als Legacy-Quelle erhalten, wird von der Web-App aber nicht mehr benoetigt

## 7.2 Tabelle

| Bereich | Vorher | Nachher |
|--------|--------|---------|
| Dev-Runtime-Resolver | impliziter Dev-Fallback auf `webapp/runtime/corapan` in App-Code und Dev-Helfern | explizite ENV-Aufloesung, `runtime/corapan` in Dev abgelehnt |
| Atlas-Dateiliste | `latest/tei` gewann, obwohl `corapan_recordings*.json/tsv` in `latest/` lagen | kontrollierter Dev-Fallback `latest/tei -> latest`, `/api/v1/atlas/files` liefert Dateien |
| docmeta | nur unter `webapp/data/blacklab_export/docmeta.jsonl` vorhanden | zusaetzlich unter `C:\dev\corapan\data\blacklab_export\docmeta.jsonl`; Advanced Search liest aus `DATA_ROOT` |
| Dev-Start | konnte auf repo-lokales `runtime/corapan` ausweichen | verlangt kanonisches Geschwisterlayout `data/` + `media/` |
| Stats-Migrationshelfer | setzte ohne ENV repo-lokales `runtime/corapan` | verlangt explizites `CORAPAN_RUNTIME_ROOT` |
| Atlas-Route | leere Dev-Antworten konnten im Route-Cache haengen bleiben | leere Dev-Antworten werden nicht mehr festgeschrieben |

## 7.3 Offene Punkte

- `docker-compose.dev-postgres.yml` nutzt weiterhin repo-lokales `webapp/config/blacklab` und repo-lokales `webapp/data/blacklab_index`
- die BlackLab-Index-Struktur wurde bewusst nicht veraendert
- Produktionspfade wurden bewusst nicht angefasst
- bestehende Legacy-Daten unter `webapp/data/blacklab_export` wurden nicht geloescht
- eine bereits laufende alte Dev-Instanz auf Port `8000` kann alte Atlas-Antworten weiter ausliefern; die eindeutige Abschlussverifikation lief deshalb auf einem isolierten aktuellen Prozess auf Port `8001`

## 7.4 Risiken

- BlackLab selbst ist in Dev weiterhin an repo-lokale Legacy-Pfade gebunden; nur die Web-App ist fuer Welle 2 auf die kanonischen Dev-Pfade stabilisiert
- wenn alte lokale Serverprozesse weiterlaufen, koennen sie neue Path-Fixes verdecken
- `advanced_data` liefert weiterhin BLS-Dateinamen wie `/data/export/tsv/...`; die docmeta-Verifikation ist daher ueber den geladenen Cache und die enrichte Metadatenbasis belegt, nicht ueber eine vollstaendige Umformung jedes Dateinamens

## Verifikation

Automatisierte Tests:

- `pytest tests/test_atlas_files_endpoint.py tests/test_advanced_api_enrichment.py tests/test_advanced_api_docmeta_mapping.py tests/test_advanced_api_stats_csv.py tests/test_advanced_api_stats_json.py -q`
- Ergebnis: `8 passed`

Live-Verifikation auf isoliertem aktuellen Dev-Server (`127.0.0.1:8001`):

- `/media/full/2023-08-10_ARG_Mitre.mp3` -> `200`
  - belegter Pfad: `C:\dev\corapan\media\mp3-full\ARG\2023-08-10_ARG_Mitre.mp3`
- `/media/transcripts/2023-08-10_ARG_Mitre.json` -> `200`
  - belegter Pfad: `C:\dev\corapan\media\transcripts`
- `/api/v1/atlas/files` -> `200`, `146` Dateien
  - belegter Pfad: `C:\dev\corapan\data\public\metadata\latest`
  - Logbeleg: `Atlas metadata fallback active in dev: ... latest\tei has no recording files; using ... latest instead.`
- `/corpus/metadata` -> `200`
  - belegter Pfad: `C:\dev\corapan\data\public\metadata\latest`
- `/corpus/api/statistics/corpus_stats.json` -> `200`
  - belegter Pfad: `C:\dev\corapan\data\public\statistics`
- `/search/advanced/data?q=casa&mode=lemma&draw=1&start=0&length=1` -> `200`
  - BLS-Beleg: `BLS GET /corpora/corapan/hits: 200`
  - docmeta-Beleg: `advanced_api.DATA_ROOT / blacklab_export / docmeta.jsonl` zeigt auf `C:\dev\corapan\data\blacklab_export\docmeta.jsonl`, `docmeta_cache_len=146`

## Lessons Learned – Run 2026-03-20

- Problem:
  Dev konnte trotz kanonischer externer Struktur weiter implizit an repo-lokale Legacy-Pfade gebunden bleiben.
- Ursache:
  Der eigentliche Web-App-Pfad war schon extern, aber Resolver, Route-Caching und ein fehlendes externes `docmeta.jsonl` hielten Teile des Verhaltens inkonsistent.
- Fix:
  Implizite Dev-Fallbacks entfernt, Atlas-Fallback explizit gemacht, `docmeta.jsonl` an den kanonischen Dev-Pfad kopiert und die aktiven Dev-Skripte auf das Geschwisterlayout festgezogen.
- Neue Regel:
  Agenten und Skills muessen bei Dev-Verifikation entweder einen frischen Prozess oder einen isolierten Port verwenden, wenn alte Route-Caches oder alte lokale Prozesse einen Path-Fix verdecken koennen.