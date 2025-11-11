---
title: "BlackLab Indexing Architecture"
status: active
owner: backend-team
updated: "2025-11-10"
tags: [blacklab, indexing, search, architecture]
links:
  - ../reference/blacklab-api-proxy.md
  - ../reference/blf-yaml-schema.md
  - ../how-to/build-blacklab-index.md
---

# BlackLab Indexing Architecture

## Problem

CO.RA.PAN corpus contains millions of tokens across 24+ countries/radio stations. Users need fast, precise linguistic search across the entire corpus with support for word forms, lemmas, POS tags, and grammatical annotations. Full-text SQL queries are too slow; a specialized full-text index is required.

## Kontext

**BlackLab Server** (from Dutch Language Institute) provides:
- Fast full-text indexing (Lucene-based)
- CQL query syntax (Corpus Query Language)
- Structured token/metadata search
- Web API with JSON responses

CO.RA.PAN JSON v2 corpus structure (per transcript):
```
{
  "country_code": "ARG",
  "date": "2023-08-10",
  "radio": "Radio Mitre",
  "city": "Buenos Aires",
  "segments": [
    {
      "words": [
        {
          "token_id": "ARGcafb6f8ac",
          "start_ms": 1410,
          "end_ms": 1460,
          "text": "5",
          "lemma": "5",
          "pos": "NUM",
          "norm": "5",
          "sentence_id": "ARG_...:0:s0",
          "utterance_id": "ARG_...:0",
          "past_type": "",
          "future_type": ""
        },
        ...
      ]
    }
  ]
}
```

## Lösung / Konzept

### Three-Stage Pipeline

```
┌─────────────────┐
│  JSON Corpus    │
│  media/...      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 1. EXPORT                       │
│ → Flatten to TSV/WPL            │
│ → Generate docmeta.jsonl        │
│ → Hash-based idempotency        │
│ Output: /data/bl_input/         │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 2. INDEX BUILD                  │
│ → IndexTool create              │
│ → Lucene indexing               │
│ → Atomic filesystem switch      │
│ Output: /data/blacklab_index/   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ 3. PROXY                        │
│ → Flask /bls/** route           │
│ → httpx connection pooling      │
│ → Streaming responses           │
│ Access: http://localhost:8000/  │
└─────────────────────────────────┘
```

### Stage 1: Export (JSON → TSV + Docmeta)

**Tool:** `src/scripts/blacklab_index_creation.py`

**Transformation:**
- Each JSON transcript → 1 TSV file
- Headers: `word norm lemma pos past_type future_type tense mood person number aspect tokid start_ms end_ms sentence_id utterance_id speaker_code`
- Mandatory fields: `token_id, start_ms, end_ms, lemma, pos, norm, sentence_id, utterance_id`
- Optional fields: empty strings if missing
- Unicode: NFKC normalization
- Idempotency: hash over content fields; skip if unchanged

**Docmeta:** (separate JSON Lines file)
```json
{"doc": "2023-08-10_ARG_Mitre", "country_code": "ARG", "date": "2023-08-10", "radio": "Radio Mitre", "city": "Buenos Aires", "audio_path": "2023-08-10_ARG_Mitre.mp3"}
```

### Stage 2: Index Build

**Config:** `config/blacklab/corapan.blf.yaml`

**Mapping:** TSV columns → BlackLab annotations
- `word` → displayed form
- `norm` → normalized search form
- `lemma` → lemma search
- `pos` → POS tag search
- `start_ms`, `end_ms` → audio alignment
- `sentence_id`, `utterance_id` → structural grouping
- Metadata fields: `file_id, country_code, date, radio, city, audio_path`

**Atomic Switch:** (prevents corruption during rebuild)
1. Build into `/data/blacklab_index.new`
2. Backup current → `/data/blacklab_index.bak`
3. Activate: `/data/blacklab_index.new` → `/data/blacklab_index`

### Stage 3: Proxy

**Route:** `/bls/**` (mapped to `http://127.0.0.1:8081/blacklab-server/**`)

**Features:**
- Single httpx.Client singleton (connection pooling)
- Hop-by-hop header removal (RFC 7230)
- Streaming 64KB chunks (large result sets)
- 180s read timeout
- Error responses as JSON with `code` field

## Alternativen

### 1. Full SQL Search
- ❌ Too slow for 10M+ tokens
- ❌ Complex JOIN queries
- ✅ Used: metadata filtering in app-layer

### 2. Elasticsearch
- ✅ Faster than SQL
- ❌ Extra deployment complexity
- ❌ Heavier infrastructure
- ✅ Could replace BLS in future (protocol change)

### 3. Whoosh (Python)
- ✅ Pure Python, easier packaging
- ❌ Less mature than BlackLab/Lucene
- ❌ No web API out-of-box
- ✅ Good for single-node, small corpus

## Siehe auch

- [BlackLab API Proxy](../reference/blacklab-api-proxy.md) - HTTP proxy implementation
- [BLF YAML Schema](../reference/blf-yaml-schema.md) - Index configuration reference
- [Build BlackLab Index (How-To)](../how-to/build-blacklab-index.md) - Step-by-step guide
- [BlackLab Troubleshooting](../troubleshooting/blacklab-issues.md) - Common errors & solutions
