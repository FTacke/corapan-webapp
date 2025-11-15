# BlackLab Speaker Metadata Integration

**Problem:** Advanced Search zeigte keine speaker_type, sex, mode, discourse Metadaten, obwohl diese in Corpus Search funktionierten.

**Root Cause:** 
- Corpus Search liest Metadaten aus SQLite-Datenbank (`transcription.db`)
- Advanced Search nutzte nur `docmeta.jsonl` (enthielt nur country, radio, city, date)
- Speaker-Attribute waren **nicht** in `docmeta.jsonl` exportiert

**Lösung:** Erweitere BlackLab TSV-Export um speaker-Attribute als **Token-Level Annotationen**.

## Implementierung

### 1. Export-Script erweitert

**Datei:** `src/scripts/blacklab_index_creation.py`

#### Mapping-Funktion hinzugefügt

```python
def map_speaker_attributes(code: str) -> tuple[str, str, str, str]:
    """
    Map speaker_code to (speaker_type, sex, mode, discourse).
    Aligned with database_creation_v3.py for consistency.
    """
    mapping = {
        'lib-pm':  ('pro', 'm', 'libre', 'general'),
        'lib-pf':  ('pro', 'f', 'libre', 'general'),
        # ... weitere 12 Mappings
    }
    return mapping.get(code, ('', '', '', ''))
```

#### TokenFull Dataclass erweitert

```python
@dataclass
class TokenFull:
    # Existing fields...
    speaker_code: str = ""
    # NEW:
    speaker_type: str = ""
    sex: str = ""
    mode: str = ""
    discourse: str = ""
```

#### to_tsv_row() aktualisiert

TSV-Export enthält jetzt **21 Spalten** (vorher 17):

```
word, norm, lemma, pos, past_type, future_type, tense, mood,
person, number, aspect, tokid, start_ms, end_ms, sentence_id,
utterance_id, speaker_code, speaker_type, sex, mode, discourse
```

### 2. BlackLab-Konfiguration erweitert

**Datei:** `config/blacklab/corapan-tsv.blf.yaml`

Neue Annotationen hinzugefügt:

```yaml
- name: speaker_type
  displayName: "Speaker Type"
  description: "Speaker category (pro=politician, otro=other, n/a)"
  valuePath: speaker_type
  uiType: "select"

- name: sex
  displayName: "Sex"
  description: "Speaker sex (m=masculino, f=femenino, n/a)"
  valuePath: sex
  uiType: "select"

- name: mode
  displayName: "Register Mode"
  description: "Speech register (libre, lectura, pre, n/a)"
  valuePath: mode
  uiType: "select"

- name: discourse
  displayName: "Discourse Type"
  description: "Discourse category (general, tiempo, tránsito, foreign)"
  valuePath: discourse
  uiType: "select"
```

## Workflow

### Index neu bauen

```powershell
# 1. TSV-Export mit neuen Feldern
python -m src.scripts.blacklab_index_creation \
    --in media/transcripts \
    --out data/blacklab_export/tsv \
    --format tsv \
    --docmeta data/blacklab_export/docmeta.jsonl

# 2. BlackLab-Index erstellen
.\scripts\build_blacklab_index_v3.ps1 -Force
```

### Advanced API anpassen

**Datei:** `src/app/search/advanced_api.py`

In `datatable_data()` Funktion:

```python
# OLD: listvalues nur mit word, tokid, start_ms, end_ms, utterance_id
bls_params = {
    "listvalues": "word,tokid,start_ms,end_ms,utterance_id,speaker_type,sex,mode,discourse",
}

# In _hit_to_row():
match_info = hit.get("match", {})
speaker_type = match_info.get("speaker_type", [None])[0] if match_info.get("speaker_type") else ""
sex = match_info.get("sex", [None])[0] if match_info.get("sex") else ""
mode = match_info.get("mode", [None])[0] if match_info.get("mode") else ""
discourse = match_info.get("discourse", [None])[0] if match_info.get("discourse") else ""

row = {
    # ... existing fields
    "speaker_type": speaker_type,
    "sex": sex,
    "mode": mode,
    "discourse": discourse,
}
```

## Vorteile dieser Lösung

✅ **Single Source of Truth**: Beide APIs (Corpus + Advanced) nutzen dieselbe Datenquelle (JSON Transcripts)
✅ **Token-Level Precision**: Speaker-Attribute pro Token, nicht pro Dokument
✅ **Filterbar**: BlackLab kann per CQL filtern: `[speaker_type="pro" & sex="f"]`
✅ **Konsistenz**: Identisches Mapping wie in `database_creation_v3.py`
✅ **Wartbarkeit**: Ein Mapping-Dictionary für beide Export-Prozesse

## Datenfluss

```
JSON Transcripts
  └─ segment.speaker_code (z.B. "lib-pm")
      ├─ database_creation_v3.py
      │   └─ map_speaker_attributes()
      │       └─ SQLite tokens.speaker_type, .sex, .mode, .discourse
      │
      └─ blacklab_index_creation.py
          └─ map_speaker_attributes()
              └─ TSV speaker_type, sex, mode, discourse
                  └─ BlackLab Index Annotationen
                      └─ Advanced Search API (via listvalues)
```

## Testing

```bash
# 1. Verify TSV Export
head -1 data/blacklab_export/tsv/*.tsv | grep "speaker_type"

# 2. Query BlackLab directly
curl "http://localhost:8081/blacklab-server/corpora/corapan/hits?patt=[word='casa']&listvalues=speaker_type,sex,mode,discourse" | jq '.hits[0].match'

# 3. Test Advanced Search API
curl "http://localhost:8000/search/advanced/data?q=casa&mode=lemma&length=2" | jq '.data[0]'
```

## Änderungshistorie

- **2025-11-14**: Initiale Integration - speaker_type, sex, mode, discourse als Token-Annotationen
