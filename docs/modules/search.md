# Suche (Search) Modul

**Scope:** Korpussuche via BlackLab Server  
**Source-of-truth:** `src/app/routes/corpus.py`, `src/app/search/`

## Übersicht

Das Such-Modul bietet:
- **Einfache Suche:** Wortformen, Lemmata
- **Erweiterte Suche:** CQL (Corpus Query Language) + Pattern Builder
- **Filter:** Metadaten (Land, Region, Sprecher, Geschlecht, etc.)
- **Export:** CSV/TSV (Streaming für große Datenmengen)
- **KWIC:** Key Word in Context Ansicht

**Routes:**
- `/search` — Einfache Suche
- `/search/advanced` — Erweiterte Suche (CQL)
- `/search/results` — KWIC-Ansicht (htmx-powered)
- `/search/export` — CSV/TSV Export

**Backend:** BlackLab Server (Lucene-basiert, Docker)

---

## BlackLab Integration

**BlackLab Server URL:** `http://blacklab:8080/blacklab-server/`

**Korpus:** `corapan` (Index-Name)

**Proxy:**
```python
# src/app/routes/bls_proxy.py
@bls_proxy_bp.route("/api/blacklab/<path:subpath>", methods=["GET", "POST"])
@jwt_required()
def proxy_blacklab(subpath):
    blacklab_url = f"http://blacklab:8080/blacklab-server/{subpath}"
    response = requests.request(
        method=request.method,
        url=blacklab_url,
        params=request.args,
        json=request.json
    )
    return response.json(), response.status_code
```

---

## Einfache Suche

**Route:** `GET /search`

**Form:**
```html
<form action="/search/results" method="GET">
  <input name="query" placeholder="Suchbegriff" required>
  <select name="search_type">
    <option value="word">Wortform</option>
    <option value="lemma">Lemma</option>
    <option value="pos">POS-Tag</option>
  </select>
  <button type="submit">Suchen</button>
</form>
```

**Backend:**
```python
# src/app/routes/corpus.py
@corpus_bp.route("/results", methods=["GET"])
@jwt_required()
def results():
    query = request.args.get("query")
    search_type = request.args.get("search_type", "word")
    
    # CQL-Query generieren
    if search_type == "word":
        cql_query = f'[word="{query}"]'
    elif search_type == "lemma":
        cql_query = f'[lemma="{query}"]'
    elif search_type == "pos":
        cql_query = f'[pos="{query}"]'
    
    # BlackLab Query
    results = blacklab_search(cql_query)
    
    return render_template("search/results.html", results=results)
```

---

## Erweiterte Suche (CQL)

**Route:** `GET /search/advanced`

**Pattern Builder:**
```javascript
// Pattern-Builder UI (JavaScript)
// Nutzer wählt: [lemma="casa"] [pos="V.*"]
// Generiert CQL: [lemma="casa"] [pos="V.*"]
```

**CQL-Beispiele:**
```cql
# Einfach
[word="casa"]

# Regex
[word="cas.*"]

# POS-Tag
[pos="N.*"]

# Sequenz
[lemma="ser"] [pos="ADJ"]

# Optional
[word="muy"]? [pos="ADJ"]

# Repetition
[pos="DET"] [pos="ADJ"]+ [pos="N"]
```

**Backend:**
```python
@corpus_bp.route("/advanced", methods=["POST"])
@jwt_required()
def advanced_search():
    cql_query = request.json.get("cql")
    filters = request.json.get("filters", {})
    
    # BlackLab API Call
    results = blacklab_search(cql_query, filters)
    
    return jsonify(results)
```

---

## Filter

**Metadaten-Filter:**
- **Land:** Dropdown (alle Länder im Korpus)
- **Region:** Dropdown (abhängig von Land)
- **Sprecher:** Dropdown (alle Sprecher)
- **Geschlecht:** Radio (m/w/divers)
- **Alter:** Range-Slider
- **Bildung:** Dropdown

**Implementierung:**
```python
def blacklab_search(cql, filters=None):
    params = {
        "patt": cql,
        "outputformat": "json",
        "number": 100,  # Results per page
    }
    
    # Filter hinzufügen
    if filters:
        if "country" in filters:
            params["filter"] = f'doc.country:"{filters["country"]}"'
    
    response = requests.get(
        "http://blacklab:8080/blacklab-server/corapan/hits",
        params=params
    )
    return response.json()
```

---

## KWIC-Ansicht

**Template:** `templates/search/results.html`

```html
<table class="kwic-table">
  <thead>
    <tr>
      <th>Links</th>
      <th>Match</th>
      <th>Rechts</th>
      <th>Dokument</th>
    </tr>
  </thead>
  <tbody>
    {% for hit in results.hits %}
    <tr>
      <td class="left-context">{{ hit.left }}</td>
      <td class="match"><strong>{{ hit.match }}</strong></td>
      <td class="right-context">{{ hit.right }}</td>
      <td><a href="/audio/{{ hit.doc_id }}/{{ hit.seg_id }}">{{ hit.doc_id }}</a></td>
    </tr>
    {% endfor %}
  </tbody>
</table>
```

---

## Export

**Route:** `GET /search/export?format=csv`

**Streaming (für große Datenmengen):**
```python
@corpus_bp.route("/export", methods=["GET"])
@jwt_required()
def export():
    query = request.args.get("query")
    format = request.args.get("format", "csv")
    
    def generate():
        # Header
        yield "left,match,right,doc_id,seg_id\n"
        
        # Rows (paginate BlackLab results)
        page = 0
        while True:
            results = blacklab_search(query, page=page, pagesize=1000)
            if not results["hits"]:
                break
            
            for hit in results["hits"]:
                yield f'"{hit["left"]}","{hit["match"]}","{hit["right"]}","{hit["doc_id"]}","{hit["seg_id"]}"\n'
            
            page += 1
    
    return Response(
        stream_with_context(generate()),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=export.{format}"}
    )
```

---

## Extension Points

**Neue Suchtypen:**
- Phonetische Suche (Soundex, Metaphone)
- N-Gramm-Suche
- Kolloikationsanalyse

**Neue Filter:**
- Zeitraum (Aufnahmedatum)
- Thema/Genre
- Sprecher-Eigenschaften (Dialekt, L1, etc.)

**Visualisierungen:**
- Wortwolken
- Frequenz-Diagramme (ECharts)
- Kollokations-Netzwerke (D3.js)

---

## Projekt-spezifische Annahmen

- **Korpus:** CO.RA.PAN (Spanisch, Oral)
- **Index:** BlackLab, Lucene-basiert
- **Annotationen:** Lemma, POS-Tag (TreeTagger)
- **Audio:** Segmentiert (1 MP3 pro Segment)
- **Metadaten:** In BlackLab-Index (nicht in SQL)
