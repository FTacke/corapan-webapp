---
title: "BlackLab API Proxy Reference"
status: active
owner: backend-team
updated: "2025-11-10"
tags: [blacklab, api, proxy, reference]
links:
  - ../concepts/blacklab-indexing.md
  - ../how-to/build-blacklab-index.md
  - ../troubleshooting/blacklab-issues.md
---

# BlackLab API Proxy Reference

Alle BlackLab Server API-Requests werden durch Flask-Proxy geroutet: `/bls/**`

## Pfadvertrag

| Upstream Path | Proxy Path | Methode |
|---|---|---|
| `http://127.0.0.1:8081/blacklab-server/` | `/bls/` | GET |
| `http://127.0.0.1:8081/blacklab-server/api/v1/corpus/corapan/search` | `/bls/api/v1/corpus/corapan/search` | GET/POST |
| `http://127.0.0.1:8081/blacklab-server/api/v1/corpus/corapan/docs/FILE_ID` | `/bls/api/v1/corpus/corapan/docs/FILE_ID` | GET |
| *Alle Sub-Pfade* | `/bls/**` | GET/POST/PUT/DELETE/PATCH |

## API Endpoints

### Health Check

```bash
curl -s http://localhost:8000/bls/ | jq .
```

**Response:**
```json
{
  "version": "4.0.0",
  "blacklabVersion": "4.0",
  "indices": {
    "corapan": {
      "displayName": "CO.RA.PAN Corpus",
      "status": "available"
    }
  }
}
```

---

### Search Query

```bash
# Simple term search
curl 'http://localhost:8000/bls/api/v1/corpus/corapan/search' \
  -G \
  --data-urlencode 'query=[lemma="be"]' \
  --data-urlencode 'outputformat=json' \
  --data-urlencode 'first=0' \
  --data-urlencode 'number=10'
```

**Query Parameter:**

| Parameter | Typ | Beschreibung | Beispiel |
|---|---|---|---|
| `query` | CQL | Corpus Query Language | `[lemma="ser"]` |
| `outputformat` | json/csv/xml | Output format | `json` |
| `first` | int | Resultat-Offset | `0` |
| `number` | int | Limit | `10` |
| `filter` | Lucene | Metadata filter | `country_code:ARG AND date:[2023-08-01 TO 2023-08-31]` |
| `groupby` | str | Group results | `country_code` |

**Response:**
```json
{
  "hits": 1234567,
  "results": [
    {
      "docPid": "ARG_2023-08-10_ARG_Mitre",
      "start": 5,
      "end": 6,
      "left": [{"word": "el"}],
      "match": [{"word": "día", "lemma": "día", "pos": "NOUN"}],
      "right": [{"word": "es"}],
      "tokens": [
        {
          "word": "día",
          "lemma": "día",
          "pos": "NOUN",
          "start_ms": 5000,
          "end_ms": 5500
        }
      ]
    }
  ]
}
```

---

### CQL Query Syntax

**Basic:**
```
[word="palabra"]              # Exact word match
[lemma="andar"]              # Lemma search
[pos="VERB"]                 # POS tag
[norm="mexico"]              # Normalized form
```

**Combinations:**
```
[pos="ADJ"] [pos="NOUN"]     # Sequence: Adj + Noun
[word=".*or"] 0 3 [word=".*"]  # Wildcard: *or, with 0-3 words between
[pos="VERB"] [norm="se"] [pos="VERB"]  # Reflexive verbs
```

**Repetition:**
```
[pos="DET"]?                 # Optional (0-1)
[pos="ADJ"]+                 # 1 or more
[pos="ADJ"]*                 # 0 or more
[pos="ADJ"]{2,4}             # 2-4 times
```

**Case/Diacritics:**
```
query=[word="México"]        # Default: case/diacritic-insensitive
```

---

### Document Retrieval

```bash
curl 'http://localhost:8000/bls/api/v1/corpus/corapan/docs/ARG_2023-08-10_ARG_Mitre' \
  -G \
  --data-urlencode 'outputformat=json'
```

**Response:**
```json
{
  "doc": {
    "pid": "ARG_2023-08-10_ARG_Mitre",
    "lengthInTokens": 42123,
    "metadata": {
      "file_id": "ARG_2023-08-10_ARG_Mitre",
      "country_code": "ARG",
      "date": "2023-08-10",
      "radio": "Radio Mitre",
      "city": "Buenos Aires",
      "audio_path": "2023-08-10_ARG_Mitre.mp3"
    }
  }
}
```

---

### Corpus Metadata

```bash
curl 'http://localhost:8000/bls/api/v1/corpus/corapan' | jq '.
```

**Response:**
```json
{
  "name": "corapan",
  "displayName": "CO.RA.PAN Corpus",
  "documentCount": 1247,
  "tokenCount": 42123456,
  "annotatedFields": {
    "contents": {
      "annotations": [
        {"name": "word"},
        {"name": "lemma"},
        {"name": "pos"},
        {"name": "start_ms"},
        {"name": "end_ms"},
        ...
      ]
    }
  }
}
```

---

## Timeouts & Limits

| Parameter | Standard | Max |
|---|---|---|
| Connection Timeout | 10s | — |
| Read Timeout | 180s | — |
| Query Result Limit | 100,000 | — |
| Request Size | Unlimited | Depends on HTTP server |

---

## Error Responses

### 502 Bad Gateway (Proxy Error)

```json
{
  "error": "proxy_error",
  "message": "Connection refused: 127.0.0.1:8081"
}
```

**Lösungen:**
- Prüfe: `curl http://127.0.0.1:8081/blacklab-server/`
- Start BLS: `make bls`

### 404 Not Found

```json
{
  "error": "not_found",
  "message": "BlackLab resource not found"
}
```

**Lösungen:**
- Prüfe Spelling der Query
- Prüfe Corpus-Name: `/bls/api/v1/corpus/corapan/...`

### 400 Bad Request

```json
{
  "error": "invalid_query",
  "message": "Invalid CQL query: ..."
}
```

**Lösungen:**
- Prüfe CQL-Syntax
- Teste: `/bls/debug` (Debug-Dashboard)

---

## Best Practices

### 1. Pagination

```bash
# Get first 100 results
curl '...search' -G --data-urlencode 'first=0' --data-urlencode 'number=100'

# Get next 100
curl '...search' -G --data-urlencode 'first=100' --data-urlencode 'number=100'
```

### 2. Metadata Filtering

```bash
# ARG only
curl '...search' -G --data-urlencode 'filter=country_code:ARG'

# Date range
curl '...search' -G --data-urlencode 'filter=date:[2023-08-01 TO 2023-12-31]'

# Combined
curl '...search' -G --data-urlencode 'filter=country_code:MEX AND date:[2023-08-* TO 2023-09-*]'
```

### 3. Streaming Large Results

```bash
# Response is streamed in 64KB chunks
# Safe for millions of results
curl -N 'http://localhost:8000/bls/api/v1/corpus/corapan/search?query=...'
```

---

## Siehe auch

- [BlackLab Indexing Architecture](../concepts/blacklab-indexing.md) - Design & concepts
- [Build BlackLab Index (How-To)](../how-to/build-blacklab-index.md) - Index creation
- [BlackLab Troubleshooting](../troubleshooting/blacklab-issues.md) - Common issues
