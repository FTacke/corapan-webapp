---
title: "Build BlackLab Index from Corpus"
status: active
owner: devops
updated: "2025-11-10"
tags: [blacklab, indexing, deployment, how-to]
links:
  - ../concepts/blacklab-indexing.md
  - ../reference/blacklab-api-proxy.md
  - ../troubleshooting/blacklab-issues.md
---

# Build BlackLab Index from Corpus

## Ziel

Nach dieser Anleitung hast du:
- ✓ JSON-Korpus aus `media/transcripts` in TSV exportiert
- ✓ BlackLab-Index in `/data/blacklab_index` gebaut
- ✓ Index-Atomarität gewährleistet (kein Downtime bei Rebuild)
- ✓ Dokumetadaten für Facetierung verfügbar

## Voraussetzungen

- **System:** Linux/macOS mit bash (Windows: WSL2 oder Git Bash)
- **Java:** OpenJDK 11+ (`java -version`)
- **BlackLab Server:** Installiert (`apt-get install blacklab-server`)
- **Python:** 3.12+ mit dependencies (`pip install -r requirements.txt`)
- **Disk:** ≥2x Corpus-Größe (Export + Index)
- **Directories:** Prüfe dass `/data/` existiert:
  ```bash
  sudo mkdir -p /data/blacklab_index
  sudo mkdir -p /data/bl_input
  sudo chown $(whoami):$(whoami) /data/
  ```

## Schritte

### Schritt 1: Corpus-Check

Stelle sicher, dass JSON-Dateien vorhanden sind:

```bash
ls -la media/transcripts/ARG/ | head -5
# Output:
# -rw-r--r-- 1 user user 9M Aug 10 2023 2023-08-10_ARG_Mitre.json
# -rw-r--r-- 1 user user 3M Aug 12 2023 2023-08-12_ARG_Mitre.json
```

Anzahl Dateien prüfen:
```bash
find media/transcripts -name "*.json" -type f | wc -l
# Output: 1247 (example)
```

### Schritt 2: Export (Trockentest)

Führe Dry-Run durch (keine Dateien geschrieben):

```bash
make index-dry
# oder manuell:
python -m src.scripts.blacklab_index_creation \
  --in media/transcripts \
  --out /data/bl_input \
  --format tsv \
  --limit 3 \
  --dry-run
```

**Output sollte enthalten:**
```
[INFO] Found 1247 JSON files in media/transcripts
[INFO] DRY RUN: showing first 3 files...
[INFO]   2023-08-10_ARG_Mitre: 42 segments
[INFO]     - Buenos (buenos)
[INFO]     - Aires (aires)
```

### Schritt 3: Export (Vollständig)

Starte vollständigen Export mit 4 Worker-Threads:

```bash
make index
# oder manuell:
bash scripts/build_blacklab_index.sh tsv 4
```

**Dauer:** ~5–30 Minuten (je nach Corpus-Größe)

**Output sollte enthalten:**
```
[INFO] === BlackLab Index Build Started ===
[INFO] Format: tsv, Workers: 4
[INFO] Exporting JSON corpus to tsv format...
[INFO] Export complete: 1247 files
[INFO] Document metadata: 1247 entries
[INFO] Building BlackLab index...
[INFO] Index build successful
[INFO] Index size: 2.3G
[INFO] Estimated tokens: 42M
[INFO] === Build Complete ===
```

### Schritt 4: Validierung

Prüfe dass Index gebaut wurde:

```bash
ls -la /data/blacklab_index/
# Sollte enthalten: metadata.yaml, main/, ...
```

Prüfe Tokenzahl:
```bash
find /data/bl_input -name "*.tsv" -type f | \
  xargs wc -l | tail -1
# Output: 42123456 total (≈tokens)
```

## Rollback

Falls der Build schief ging:

```bash
# Index zurückstellen aus Backup
mv /data/blacklab_index /data/blacklab_index.broken
mv /data/blacklab_index.bak /data/blacklab_index

# Oder komplett neu starten (Export erneut)
rm -rf /data/blacklab_index /data/bl_input
make index
```

## CLI-Optionen (Exporter)

```bash
python -m src.scripts.blacklab_index_creation \
  --in <json-dir>              # Input (default: media/transcripts)
  --out <export-dir>           # Output TSV (default: /data/bl_input)
  --format tsv|wpl             # Format (default: tsv; WPL: später)
  --docmeta <file.jsonl>       # Metadata output (default: /data/bl_input/docmeta.jsonl)
  --workers <N>                # Threads (default: 4)
  --limit <N>                  # Nur erste N Dateien (für Tests)
  --dry-run                    # Nur zeigen, nicht schreiben
```

## Environment-Variablen

```bash
# Input-Verzeichnis überschreiben
CORAPAN_JSON_DIR=/custom/path make index

# Java Memory für Indexing
export _JAVA_OPTIONS="-Xmx4g"
bash scripts/build_blacklab_index.sh
```

## Troubleshooting

**Error: "IndexTool command not found"**
```bash
# Install BlackLab
apt-get install blacklab-server  # Debian/Ubuntu
```

**Error: "Insufficient disk space"**
- Check: `df -h /data/`
- Increase: Mount mit mehr Speicher, oder clean `/data/bl_input/*`

**Slow Export (>1 hour)**
```bash
# Increase workers
make index  # (uses 4 workers by default)
# Or: bash scripts/build_blacklab_index.sh tsv 8
```

## Siehe auch

- [BlackLab Indexing Architecture](../concepts/blacklab-indexing.md) - Konzepte & Design
- [BLF YAML Schema](../reference/blf-yaml-schema.md) - Index-Konfiguration
- [BlackLab Troubleshooting](../troubleshooting/blacklab-issues.md) - Fehler & Lösungen
