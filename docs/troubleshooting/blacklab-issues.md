---
title: "BlackLab Server Troubleshooting"
status: active
owner: devops
updated: "2025-11-10"
tags: [blacklab, troubleshooting, debugging, errors]
links:
  - ../how-to/build-blacklab-index.md
  - ../reference/blacklab-api-proxy.md
  - ../concepts/blacklab-indexing.md
---

# BlackLab Server Troubleshooting

## Problem 1: BlackLab Server Won't Start

**Symptome:**
- `java: command not found`
- Error in `/logs/bls/server.log`
- Port 8081 unreachable

**Ursache:**
- Java not installed
- Wrong Java version
- Port already in use
- Insufficient memory

**Diagnose:**
```bash
# Check Java
java -version

# Check port
lsof -i :8081
ss -tlnp | grep 8081

# Check logs
tail -50 logs/bls/server.log
```

**Lösung:**

```bash
# Install Java (Ubuntu/Debian)
apt-get update && apt-get install -y openjdk-11-jre-headless

# Or use alternative port
bash scripts/run_bls.sh 8082 2g 512m

# Or kill process on port
lsof -i :8081 | grep -v COMMAND | awk '{print $2}' | xargs kill -9
```

---

## Problem 2: Proxy Returns 502 Bad Gateway

**Symptome:**
```json
{"error": "proxy_error", "message": "Connection refused: 127.0.0.1:8081"}
```

**Ursache:**
- BlackLab Server not running
- Proxy upstream URL incorrect
- Network/firewall issue

**Diagnose:**
```bash
# Check if BLS is running
curl -s http://127.0.0.1:8081/blacklab-server/ | jq .

# Check Flask app logs
tail -50 logs/app.log
```

**Lösung:**
```bash
# Start BLS
make bls

# Or verify upstream URL in src/app/routes/bls_proxy.py
grep BLS_UPSTREAM src/app/routes/bls_proxy.py
```

---

## Problem 3: Index Build Fails (Export Stage)

**Symptome:**
```
[ERROR] Export failed: no output files created
[ERROR] No valid tokens in 2023-08-10_ARG_Mitre.json
```

**Ursache:**
- JSON files not found
- Malformed JSON
- Missing mandatory token fields
- Encoding issues (not UTF-8)

**Diagnose:**
```bash
# Check if files exist
ls -la media/transcripts/ARG/ | head -3

# Check JSON structure
python -c "import json; json.load(open('media/transcripts/ARG/2023-08-10_ARG_Mitre.json', encoding='utf-8'))" && echo "OK"

# Check file encoding
file -i media/transcripts/ARG/2023-08-10_ARG_Mitre.json
# Should show: charset=utf-8

# Dry-run to see issues
python -m src.scripts.blacklab_index_creation --in media/transcripts --limit 1 --dry-run
```

**Lösung:**
```bash
# Fix encoding (convert to UTF-8)
iconv -f ISO-8859-1 -t UTF-8 input.json > output.json

# Check mandatory fields in sample
python << 'EOF'
import json
with open('media/transcripts/ARG/2023-08-10_ARG_Mitre.json', encoding='utf-8') as f:
    data = json.load(f)
    for seg in data.get('segments', [])[:1]:
        token = seg['words'][0]
        required = ['token_id', 'start_ms', 'end_ms', 'lemma', 'pos', 'norm', 'sentence_id', 'utterance_id']
        for field in required:
            if field not in token:
                print(f"MISSING: {field}")
EOF
```

---

## Problem 4: Insufficient Disk Space

**Symptome:**
```
Disk space error during export/indexing
No such file or directory
```

**Diagnose:**
```bash
df -h /data/
# Or check total usage
du -sh /data/blacklab_index
du -sh /data/bl_input
```

**Lösung:**
```bash
# Clean previous exports
rm -rf /data/bl_input/*

# Increase disk (add volume, mount)
# or reduce corpus size for testing
python -m src.scripts.blacklab_index_creation \
  --limit 100  # Process only first 100 files for testing
```

---

## Problem 5: Search Query Returns 0 Results

**Symptome:**
```bash
curl '/bls/api/v1/corpus/corapan/search?query=[word="hello"]'
# Result: "hits": 0
```

**Ursache:**
- Wrong index loaded (empty or outdated)
- Wrong corpus name
- Invalid CQL syntax
- Token not in corpus

**Diagnose:**
```bash
# Check corpus status
curl -s http://127.0.0.1:8081/blacklab-server/ | jq '.indices'

# Check corpus details
curl -s 'http://127.0.0.1:8081/blacklab-server/api/v1/corpus/corapan' | \
  jq '{name, documentCount, tokenCount}'

# Check query syntax (BLS debug UI)
# Or test simple query
curl -G -s 'http://127.0.0.1:8081/blacklab-server/api/v1/corpus/corapan/search' \
  --data-urlencode 'query=[word="*"]' \
  --data-urlencode 'first=0' \
  --data-urlencode 'number=1' | jq '.hits'
```

**Lösung:**
```bash
# Check if index is loaded
ls -la /data/blacklab_index/
# Should have metadata.yaml, main/, etc.

# Rebuild index
make index

# Use correct CQL syntax
# Simple: [word="FORM"]
# Lemma: [lemma="LEMMA"]
# POS: [pos="NOUN"]
```

---

## Problem 6: Proxy Streaming Hangs (Large Results)

**Symptome:**
- Query works but response is very slow
- Connection times out after 3+ minutes
- Partial JSON received

**Ursache:**
- Read timeout too short (180s default)
- Very large result set (millions of matches)
- Network latency

**Diagnose:**
```bash
# Check timeout setting in src/app/routes/bls_proxy.py
grep "read=" src/app/routes/bls_proxy.py

# Monitor streaming
curl -N -v 'http://localhost:8000/bls/api/v1/corpus/corapan/search?query=...' \
  2>&1 | head -100
```

**Lösung:**
```bash
# Increase read timeout in bls_proxy.py
# Current: read=180.0  →  Change to: read=300.0

# Or limit results
curl -G 'http://localhost:8000/bls/api/v1/corpus/corapan/search' \
  --data-urlencode 'query=[word="the"]' \
  --data-urlencode 'number=100'  # Limit to 100 results
```

---

## Problem 7: Unicode/Diacritics Not Working

**Symptome:**
- Search for "México" returns no results
- Search for "mexico" works
- Accented characters lost

**Ursache:**
- Sensitivity setting wrong in blf.yaml
- Export not normalizing Unicode (NFKC)
- TSV encoding issue

**Diagnose:**
```bash
# Check blf.yaml sensitivity
grep -A2 "norm:" config/blacklab/corapan.blf.yaml
# Should have: sensitivity: INSENSITIVE_DIACRITICS

# Check TSV file encoding
file -i /data/bl_input/ARG_2023-08-10_ARG_Mitre.tsv
# Should be: UTF-8

# Check if NFKC normalization ran
python << 'EOF'
import unicodedata
word = "México"
normalized = unicodedata.normalize("NFKC", word)
print(f"Original: {word}")
print(f"Normalized: {normalized}")
print(f"Same? {word == normalized}")
EOF
```

**Lösung:**
```bash
# Fix blf.yaml
sed -i 's/sensitivity: SENSITIVE/sensitivity: INSENSITIVE_DIACRITICS/g' \
  config/blacklab/corapan.blf.yaml

# Rebuild index
make index

# Or try both forms in search
curl -G 'http://localhost:8000/bls/api/v1/corpus/corapan/search' \
  --data-urlencode 'query=[norm="mexico"]'
```

---

## Problem 8: IndexTool Not Found

**Symptome:**
```
[ERROR] IndexTool command not found
```

**Ursache:**
- BlackLab Server not installed
- IndexTool not in PATH

**Diagnose:**
```bash
which IndexTool
type IndexTool

# Or find manually
find /opt /usr -name IndexTool 2>/dev/null
```

**Lösung:**
```bash
# Install BlackLab
apt-get install blacklab-server

# Or add to PATH
export PATH=$PATH:/opt/blacklab-server/bin
```

---

## Problem 9: Docmeta Fields Missing

**Symptome:**
- Search results don't have `country_code`, `date`, etc.
- Filtering by country not working

**Ursache:**
- docmeta.jsonl not created
- docmeta fields not in blf.yaml
- Docmeta-Index mapping wrong

**Diagnose:**
```bash
# Check docmeta file
wc -l /data/bl_input/docmeta.jsonl
head -3 /data/bl_input/docmeta.jsonl

# Check blf.yaml metadata
grep -A10 "metadata:" config/blacklab/corapan.blf.yaml
```

**Lösung:**
```bash
# Re-export with docmeta
python -m src.scripts.blacklab_index_creation \
  --in media/transcripts \
  --out /data/bl_input \
  --docmeta /data/bl_input/docmeta.jsonl

# Rebuild index
make index
```

---

## Siehe auch

- [Build BlackLab Index (How-To)](../how-to/build-blacklab-index.md) - Step-by-step guide
- [BlackLab API Proxy Reference](../reference/blacklab-api-proxy.md) - API documentation
- [BlackLab Indexing Architecture](../concepts/blacklab-indexing.md) - Design overview
