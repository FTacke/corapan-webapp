# Statusbericht: BlackLab + Advanced Search Integration (14.11.2025)

## 1. Zielsetzung
Das Ziel der aktuellen Arbeit war, die neue BlackLab‑5.x‑Instanz (JSON → TSV → Index) stabil mit dem Flask-basierten Advanced Search Frontend zu verbinden. Dieses Dokument hält fest, welche Teile bereits verlässlich funktionieren, welche Unterschiede zur einfachen Corpus-Suche bestehen und welche offenen Punkte noch angegangen werden müssen.

## 2. Erreichte Ergebnisse
| Bereich | Quelle | Resultat | Kommentar |
| --- | --- | --- | --- |
| **Index & Datenpipeline** | `LOKAL/.../blacklab_index_creation.py` + `scripts/build_blacklab_index_v3.ps1` | ✅ Token-Annotationen gespeichert | TSV-Export enthält `word`, `norm`, `lemma`, `pos`, morphologische Features, Zeitstempel, Speaker-Code; BlackLab erstellt Index mit 1.488.019 Tokens. |
| **BlackLab 5.x Server** | `scripts/start_blacklab_docker_v3.ps1` + `config/blacklab/blacklab-server.yaml` | ✅ Läuft auf Port 8081 | `configVersion 2`, korrekte `annotatedFields`, Mount auf `/data/index/corapan`. |
| **API-Integration** | `src/app/search/advanced_api.py` | ✅ liefert left/match/right + metadata | `listvalues` enthält `word` und `utterance_id`, Ergebnisverarbeitung mappt `before/after` zu `left/right`. |
| **Metadaten (docmeta)** | `data/blacklab_export/docmeta.jsonl` → `_DOCMETA_CACHE` | ⚠️ teilweise | `country`, `radio`, `date`, `city` gefüllt, `speaker_type`, `sex`, `mode`, `discourse` bleiben leer, weil sie im Export nicht zur Verfügung stehen. |
| **Filter & CQL** | `src/app/search/cql.py` & `filters_to_blacklab_query` | ⚠️ noch nicht funktionsfähig | Filterparameter führen aktuell zu `recordsTotal=0`; die Übersetzung in CQL muss überarbeitet werden. |
| **Feldkonsistenz zu Simple Search** | Vergleich Corpus UI (Simple Search) vs. Advanced Search API | ⚠️ Unterschiede | Advanced Search liefert `file_id`, Simple Search nutzt `filename`; die resultierenden `listvalues` und Metadatenschlüssel sind unterschiedlich. |

## 3. Beobachtete Limitierungen
1. **Leere Spalten (`hablante`, `sexo`, `modo`, `discurso`)** – Diese Felder kommen aus den Transkript-JSON-Dateien nicht in den Docmeta Export. Bis sie exportiert werden, bleiben die Spalten in Advanced Search leer (bzw. als `""`).
2. **Filter führen zu 0 Treffern** – Solange `filters_to_blacklab_query` keine gültige CQL‑Kombination aus den Parametern `country`, `mode`, `discourse`, `sex`, `speaker_type` erzeugt, liefert die API keine Treffer mehr. Das betrifft aktuell sämtliche Filterkategorien.
3. **Metadaten widersprechen Corpus UI** – Während Simple Search `filename` (=eigentlicher Dateiname der Transkriptquelle) ausgibt, verwendet Advanced Search das aus Docmeta stammende `file_id`. Auch die zusätzlichen Hilfsfelder (`country_code`, `date`, `radio`, `city`) sind teilweise unterschiedlich benannt bzw. formatiert.
4. **POS-Suche liefert keine Ergebnisse** – Obwohl BlackLab über CQL `[pos="VERB"]` Treffer liefert, liefert das Advanced Search API `recordsTotal=0` für `mode=pos`. Ursache noch unklar (eventuell Filter/Sensitivitäts-Handling oder fehlende Parametrisierung im Frontend).

## 4. Empfohlene nächste Schritte
- **Filter-CQL-Generator überarbeiten**: `filters_to_blacklab_query` muss gezielt CQL wie `[country_code="VEN"]` oder `[pos="VERB"]` produzieren, ohne das Pattern mit `mode` zu überlagern. Ein kleiner Log-Auszug pro Filter-Query hilft bei der Validierung.
- **Docmeta erweitern**: `hablante`, `sexo`, `modo`, `discurso` sollten entweder direkt im Export aufgenommen oder über eine separate Datei (z. B. `docmeta_enriched.jsonl`) ergänzt werden.`
- **Feldnamen aus Simple Search übernehmen**: Für die Felder `filename`/`file_id` und `country`/`country_code` sollte ein Mapping definiert werden, damit die beiden UIs dieselben Spalten liefern.
- **POS-Mode debuggen**: Untersuchen, welche CQL tatsächlich abgesendet wird (Logging in `_make_bls_request` einbauen) und ob `mode=pos` im Frontend korrekt übergeben wird. Eine direkte Abfrage mit `mode=pos` sollte im Browser das gleiche Resultat wie `[pos="VERB"]` zeigen.
- **Testfälle dokumentieren**: Beispiele wie `q=casa` (lemma), `q=crisis` (`mode=forma`) und `mode=pos=VERB` dokumentieren, um Regressionen leichter zu erkennen.

Mit diesen Informationen kann das Team gezielt weiterarbeiten, um alle Filter und zusätzlichen Spalten abzustimmen.