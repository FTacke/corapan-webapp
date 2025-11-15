# Search UI - Systematic Test Cases

The following table lists systematic test scenarios covering Simple + Advanced search, metadata filters, opciones, and pattern-builder.

Each test includes:
- Test Name
- UI Inputs
- Expected CQL (approx.)
- Expected behavior / result (verbal)
- Last test run status

---

## Example Sentence
> "El alcalde Carlos Fernando Galán, en la ceremonia de posesión del nuevo comandante de la Policía de Bogotá, advirtió que más de mil mujeres están en peligro de ser asesinadas por razones de género en la capital del país."

---

Test Cases

1) Simple Search - Lema
- UI: Mode: `Lema`, Query: `alcalde`, `ignore_accents` unchecked
- Expected CQL: `[lemma="alcalde"]`
- Expected: The sentence above should be matched (alcalde lemma present), test with `sensitive=1` and `sensitive=0`.
- Status: Not run

2) Simple Search - Forma (contains)
- UI: Mode: `Forma`, Query: `alcalde`, `ignore_accents` unchecked
- Expected CQL: `[word=".*alcalde.*"]`
- Expected: Sentence matches; case- and accent-variant handling when `sensitive=1` vs `sensitive=0`.
- Status: Not run

3) Simple Search - Forma Exacta
- UI: Mode: `Forma exacta`, Query: `Alcalde` (capital A), `ignore_accents` unchecked
- Expected CQL: `[word="Alcalde"]`
- Expected: Only matches when exact case and accents match (sensitive=1); with sensitive=0 this will match normalized form only.
- Status: Not run

4) Pattern: "más de mil mujeres" with POS
- UI: Pattern builder: Token1: 'más' (POS=ADV?), Token2: 'de' (word), Token3: 'mil' (POS=NUM?), Token4: 'mujeres' (lemma=mujer, POS=NOUN), Distance: Justo seguidas
- Expected CQL: `[word="más"] [word="de"] [pos="NUM"] [lemma="mujer"]` (or similar)
- Expected: Sentence matches using token POS constraints; distance rule `Justo seguidas`.
- Status: Not run

5) Pattern: "alcalde … advirtió" distance N
- UI: Token1: lemma=alcalde, Token2: lemma=advertir, Distance: Hasta N palabras entre medias; N=50
- Expected CQL: `[lemma="alcalde"] []{0,50} [lemma="advertir"]`
- Expected: Sentence matches within same sentence up to N=50.
- Status: Not run

6) Metadata + Text Combined - País + Emisoras regionales
- UI: País: `COL`, include_regional unchecked, Mode: Lema, Query: `mujer`
- Expected: CQL includes country_code="col" and radio types filtered to national only
- Expected: Matches in national senders of `COL` only when `include_regional` unchecked; when checked include regional senders only for `COL`.
- Status: Not run

9) País default (Todos los países) + include_regional unchecked
- UI: No País selected, include_regional unchecked, Mode: Forma, Query: 'radioStationExample' (example)
- Expected CQL: CQL pattern with `country_code` set to national codes only OR include additional `radio="national"` filter
- Expected: Search returns only national senders across all countries, no regional codes in results.
- Status: Not run

10) País selected + include_regional unchecked
- UI: País selected: `ESP`, include_regional unchecked, Mode: Lema `mujer`
- Expected: Search returns only national senders for `ESP`, excluding regional stations like `ESP-CAN`, `ESP-SEV`.
- Status: Not run

7) Opciones - Ignore accents/case
- UI: Mode: `Forma`, Query: `mujer`, ignore_accents checked
- Expected: Use `norm` field (case/diacritics removed) or regex `.*` approach for insensitive searches (sensitive=0)
- Expected: Matches for 'mujér', 'Mujer', etc.
- Status: Not run

8) Pattern/Template: Adjetivo + Sustantivo template
- UI: Use template, adjust tokens for 'más de mil...', map to pattern
- Expected: Template populates token rows and generated CQL should find adjective+noun sequences.

---

## How to run tests (manual)
- Start BlackLab Docker: `.\	ools\start_blacklab_docker_v3.ps1 -Detach`
- Run the Flask app locally `flask run` or via `scripts/start-server.ps1`.
- Use the Advanced Search GUI and the Corpus UI to run the UI flows listed.

Keep this file updated with manual test results (pass/fail + date per case).
- Status: Not run

---

Notes
- These tests should be executed manually against a running BlackLab instance (Docker) or using test fixtures that emulate BlackLab responses.
- Add new cases for corner behaviour and edge-case CQL.


