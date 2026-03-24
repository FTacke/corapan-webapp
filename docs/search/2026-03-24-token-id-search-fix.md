# Token-ID Search Fix

## Problem

Im Reiter `Token` auf `/search/advanced` lief die Suche nach existierenden Token-IDs leer, obwohl die IDs im Index vorhanden sind. Betroffen waren sowohl Dev als auch Prod.

Beispiel-IDs:

- `PER1101faa0f`
- `URY5bbf88c76`

## Betroffene Stellen

- `app/templates/search/advanced.html`
  - Token-Reiter-UI
- `app/static/js/modules/search/token-tab.js`
  - Token-ID-Erfassung und Request-Aufbau im Frontend
- `app/static/js/modules/search/initTokenTable.js`
  - POST an `/search/advanced/token/search`
- `app/src/app/search/advanced_api.py`
  - Token-Suchendpunkt und CQL-Erzeugung
- `app/config/blacklab/corapan-json.blf.yaml`
- `app/config/blacklab/corapan-tsv.blf.yaml`
  - Index-Feld `tokid` ist explizit `sensitive`

## Reproduktion

### Codepfad

1. Im Token-Reiter wurde jede eingegebene Token-ID in `token-tab.js` per `trim().toLowerCase()` normalisiert.
2. `initTokenTable.js` sendete genau diese lowercased IDs als `token_ids_raw` an `/search/advanced/token/search`.
3. Der Backend-Endpunkt baute daraus eine CQL wie `[tokid="per1101faa0f"]`.
4. BlackLab suchte auf dem Feld `tokid`, das im BLF mit `sensitivity: sensitive` konfiguriert ist.
5. Ergebnis: lowercased Query gegen case-sensitive Indexfeld lieferte `0` Treffer.

### Laufzeitbeleg

Gegen die lokale Dev-Umgebung (`http://localhost:8000` / `http://localhost:8081`) wurde geprüft:

- `PER1101faa0f` über den Flask-Endpunkt: `1` Treffer
- `per1101faa0f` über den Flask-Endpunkt: `0` Treffer
- `PER1101faa0f` direkt gegen BlackLab auf `tokid`: `1` Treffer
- `per1101faa0f` direkt gegen BlackLab auf `tokid`: `0` Treffer
- `URY5bbf88c76` verhielt sich identisch (`1` vs. `0`)

Damit ist belegt: das Backend und BlackLab funktionieren mit Original-Case, aber die Token-Reiter-UI zerstörte die Schreibweise vor dem Request.

## Root Cause

### Primärursache

`app/static/js/modules/search/token-tab.js` lowercasete Token-IDs beim Einlesen. Das war mit der aktuellen Index-Realität nicht mehr kompatibel.

- Frontend-Annahme: Token-IDs dürfen normalisiert werden
- Tatsächliche Index-Realität: `tokid` ist case-sensitive und muss exakt abgefragt werden

### Nebenbefunde

- Der Backend-Endpunkt selbst lowercaset Token-IDs nicht.
- Die Anzeige der Token-IDs aus BlackLab blieb bereits korrekt case-preserving.
- Die Token-Suche verwendete schon das richtige Feld `tokid`; das Problem war nicht der Feldname, sondern die zerstörte Groß-/Kleinschreibung vor dem Request.

## Umgesetzter Fix

1. In `app/static/js/modules/search/token-tab.js` wurde die Token-ID-Normalisierung von `trim().toLowerCase()` auf reines `trim()` geändert.
2. In `app/src/app/search/advanced_api.py` wurde die Token-ID-Verarbeitung in testbare Helper ausgelagert:
   - `_parse_token_ids_raw()`
   - `_build_token_search_cql()`
3. Die CQL-Erzeugung bleibt exakt-case-preserving und baut weiterhin Queries auf `tokid`.

Der Fix behebt die Ursache direkt und ändert nicht die Anzeige der Token-IDs aus dem Index.

## Testabdeckung / Durchgeführte Prüfungen

Automatisierte Tests:

- `app/tests/test_advanced_api_token_search.py`
  - prüft case-preserving Splitten von `token_ids_raw`
  - prüft exakte CQL-Erzeugung für mehrere Token-IDs
  - prüft, dass `/search/advanced/token/search` `tokid` mit Original-Case an BlackLab übergibt
- `app/tests/test_token_id_case_preservation.py`
  - prüft weiterhin, dass gemappte Treffer ihre Token-ID-Schreibweise unverändert behalten

Ausgeführt:

- `pytest tests/test_advanced_api_token_search.py tests/test_token_id_case_preservation.py -q`
  - Ergebnis: `5 passed`

Zusätzliche Laufzeitprüfung:

- Lokale Dev-Probe gegen Flask und BlackLab mit exakter vs. lowercased Token-ID
- Ergebnis: nur Original-Case liefert Treffer

## Manuelle Testschritte

1. `/search/advanced` öffnen.
2. Reiter `Token` wählen.
3. `PER1101faa0f` eingeben, hinzufügen und `Visualizar` auslösen.
4. Erwartung: mindestens `1` Treffer.
5. `URY5bbf88c76` eingeben, hinzufügen und `Visualizar` auslösen.
6. Erwartung: mindestens `1` Treffer.
7. Gegenprobe: dieselben IDs komplett lowercased eingeben.
8. Erwartung: `0` Treffer, solange der Index `tokid` case-sensitive führt.

## Risiken / Offene Punkte

- Für diesen Bug ist kein weiterer Backend-Fix erforderlich, solange `tokid` im Index bewusst `sensitive` bleibt.
- Falls später erneut eine case-insensitive Token-Suche gewünscht ist, muss das bewusst als Produkt- und Index-Entscheidung umgesetzt werden. Das darf nicht durch stilles Frontend-Lowercasing simuliert werden.
- Playwright ist in der aktuellen lokalen Umgebung nicht verfügbar (`node`/`npx` fehlen), daher wurde der Regressionstest hier als Python-Test auf Query-Erzeugungs-Ebene ergänzt. Ein zusätzlicher Browser-Test wäre sinnvoll, sobald die JS-Testumgebung lokal oder in CI verfügbar ist.