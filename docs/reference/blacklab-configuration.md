---
title: "BlackLab Configuration Reference"
status: active
owner: backend-team
updated: "2025-11-09"
tags: [blacklab, configuration, reference, blf-yaml, annotations]
links:
  - ../how-to/blacklab-indexing.md
  - ../concepts/corpus-search-architecture.md
---

# BlackLab Configuration Reference

Vollständige Referenz für CO.RA.PAN BlackLab Format-Konfigurationen (`.blf.yaml`).

---

## Übersicht

BlackLab Format-Dateien (`.blf.yaml`) definieren:
- Wie Eingabedateien geparst werden
- Welche Annotationen indiziert werden
- Welche Metadaten verfügbar sind
- Wie Suchen interpretiert werden

**Verfügbare Konfigurationen:**
- `corapan-tsv.blf.yaml` – TSV-Format (tabular, empfohlen)
- `corapan-wpl.blf.yaml` – WPL-Format (mit Strukturen)

---

## TSV-Konfiguration (`corapan-tsv.blf.yaml`)

### Grundstruktur

```yaml
displayName: "CO.RA.PAN Corpus (TSV)"
description: "CO.RA.PAN Spanish Radio Transcripts with linguistic annotations"

fileType: tabular

fileTypeOptions:
  type: tsv
  columnNames: true
```

**Parameter:**
- `fileType: tabular` – Tabellen-basiertes Format (CSV/TSV)
- `columnNames: true` – Erste Zeile enthält Spaltennamen

---

### Annotationen

#### Word Forms (Wortformen)

```yaml
annotations:
  - name: word
    displayName: "Word"
    description: "Original word form (case-sensitive)"
    valuePath: word
    sensitivity: sensitive
    uiType: "text"
```

**Sensitivity:**
- `sensitive` – Case/accent-sensitiv (exakte Suche)
- `insensitive` – Case/accent-insensitiv (normalisierte Suche)

**Verfügbare Word Forms:**
| Annotation | Sensitivity | Beschreibung |
|------------|-------------|--------------|
| `word`     | sensitive   | Original-Text (z.B. "México") |
| `norm`     | insensitive | Normalisiert (z.B. "mexico") |
| `lemma`    | sensitive   | Lemma (z.B. "cantar" für "cantó") |

---

#### Part-of-Speech (POS)

```yaml
- name: pos
  displayName: "POS"
  description: "Part-of-speech tag (Universal Dependencies)"
  valuePath: pos
  uiType: "pos"
  values:
    - NOUN
    - VERB
    - ADJ
    - ...
```

**Universal Dependencies POS Tags:**

| Tag | Beschreibung | Beispiel |
|-----|--------------|----------|
| `NOUN` | Substantiv | casa, gobierno |
| `VERB` | Verb | cantar, hablar |
| `ADJ` | Adjektiv | grande, bueno |
| `ADV` | Adverb | muy, bien |
| `PRON` | Pronomen | yo, él, que |
| `DET` | Determiner | el, una, este |
| `ADP` | Adposition | de, en, con |
| `CONJ` | Koordinierende Konjunktion | y, o, pero |
| `SCONJ` | Subordinierende Konjunktion | que, si, porque |
| `NUM` | Zahl | 5, dos, 2023 |
| `PROPN` | Eigenname | México, Juan |
| `AUX` | Hilfsverb | ser, haber |
| `PART` | Partikel | no, sí |
| `INTJ` | Interjektion | ah, oh |
| `PUNCT` | Interpunktion | . , ! |
| `SYM` | Symbol | €, @, # |
| `X` | Sonstiges | n/a |

---

#### Morphologie

**Legacy-Felder (für Kompatibilität):**

```yaml
- name: past_type
  displayName: "Past Type (Legacy)"
  valuePath: past_type
  uiType: "select"

- name: future_type
  displayName: "Future Type (Legacy)"
  valuePath: future_type
  uiType: "select"
```

**Neue spaCy-basierte Felder:**

```yaml
- name: tense
  displayName: "Tense"
  valuePath: tense
  uiType: "select"
  values:
    - Pres    # Present
    - Past    # Past
    - Fut     # Future
    - Imp     # Imperfect
    - ""      # Empty for non-verbs
```

**Morphologische Features:**

| Annotation | Werte | Beschreibung |
|------------|-------|--------------|
| `tense` | Pres, Past, Fut, Imp | Tempus |
| `mood` | Ind, Sub, Imp, Cnd | Modus (Indikativ, Subjunktiv, etc.) |
| `person` | 1, 2, 3 | Grammatische Person |
| `number` | Sing, Plur | Numerus (Singular/Plural) |
| `aspect` | Perf, Imp, Prog | Aspekt (Perfektiv, etc.) |

**Beispiele:**

```cql
# Verb im Präsens Indikativ, 3. Person Singular
[pos="VERB" & tense="Pres" & mood="Ind" & person="3" & number="Sing"]

# Perfecto Compuesto (Legacy)
[past_type="PerfectoCompuesto"]
```

---

#### Identifiers & Timing

```yaml
- name: tokid
  displayName: "Token ID"
  valuePath: tokid
  uiType: "text"

- name: start_ms
  displayName: "Start Time (ms)"
  valuePath: start_ms
  uiType: "numeric"

- name: end_ms
  displayName: "End Time (ms)"
  valuePath: end_ms
  uiType: "numeric"
```

**Verwendung:**

- `tokid` – Eindeutige Token-ID für Rücksprung zur App
- `start_ms`/`end_ms` – Zeitstempel für Audio-Sync

**Beispiel-Response:**

```json
{
  "hits": [{
    "tokid": "ARGabc123def",
    "start_ms": 15430,
    "end_ms": 15680
  }]
}
```

**App-Link:**
```
https://corapan.example.com/token/ARGabc123def
```

---

#### Strukturelle IDs

```yaml
- name: sentence_id
  displayName: "Sentence ID"
  valuePath: sentence_id
  uiType: "text"

- name: utterance_id
  displayName: "Utterance ID"
  valuePath: utterance_id
  uiType: "text"
```

**Verwendung:**

In TSV-Format: Für App-seitige Kontext-Rekonstruktion
```python
# Satz zusammenbauen
sentence_tokens = df[df['sentence_id'] == 'ARG_2023-08-10_Mitre:0:s1']
context = ' '.join(sentence_tokens['word'])
```

In WPL-Format: Für strukturbasierte Suchen
```cql
# Innerhalb eines Satzes
<s/> containing [lemma="hablar"]
```

---

#### Speaker

```yaml
- name: speaker_code
  displayName: "Speaker Code"
  valuePath: speaker_code
  uiType: "select"
  values:
    - lib-pm    # libre, politician, masculine
    - lib-pf    # libre, politician, feminine
    - ...
```

**Speaker-Code Schema:**

Format: `{mode}-{role}{sex}`

| Code | Mode | Role | Sex | Beschreibung |
|------|------|------|-----|--------------|
| `lib-pm` | libre | politician | masculine | Freie Rede, Politiker, männlich |
| `lib-pf` | libre | politician | feminine | Freie Rede, Politiker, weiblich |
| `lib-om` | libre | other | masculine | Freie Rede, andere, männlich |
| `lib-of` | libre | other | feminine | Freie Rede, andere, weiblich |
| `lec-pm` | lectura | politician | masculine | Vorlesen, Politiker, männlich |
| `lec-pf` | lectura | politician | feminine | Vorlesen, Politiker, weiblich |
| `pre-pm` | preparado | politician | masculine | Vorbereitet, Politiker, männlich |
| `pre-pf` | preparado | politician | feminine | Vorbereitet, Politiker, weiblich |
| `tie-pm` | tiempo | politician | masculine | Zeitansage |
| `traf-pm` | tránsito | politician | masculine | Verkehrsmeldung |
| `foreign` | n/a | n/a | n/a | Fremdsprache |
| `none` | n/a | n/a | n/a | Kein Speaker |

**Beispiel-Suche:**

```cql
# Nur freie Rede von Politikern (männlich)
[speaker_code="lib-pm"]

# Alle freien Reden (männlich + weiblich)
[speaker_code="lib-p[mf]"]
```

---

### Metadaten

```yaml
metadata:
  fields:
    - name: file_id
      displayName: "File ID"
      type: "text"
      valuePath: "@doc"
```

**Quelle:** `exports/docmeta.jsonl`

```json
{"doc": "ARG_2023-08-10_ARG_Mitre", "country_code": "ARG", "date": "2023-08-10", ...}
```

**Verfügbare Metadaten:**

| Field | Type | Beschreibung | Beispiel |
|-------|------|--------------|----------|
| `file_id` | text | Eindeutige Datei-ID | ARG_2023-08-10_ARG_Mitre |
| `country_code` | text | ISO-Ländercode | ARG, MEX, ESP |
| `date` | text | Aufnahmedatum (YYYY-MM-DD) | 2023-08-10 |
| `radio` | text | Radiosender | Radio Mitre |
| `city` | text | Stadt | Buenos Aires |
| `audio_path` | text | MP3-Datei | 2023-08-10_ARG_Mitre.mp3 |

**Beispiel-Filter:**

```bash
# Nur Argentinien
curl ".../hits?patt=[lemma=\"gobierno\"]&filter=country_code:ARG"

# Nur 2023
curl ".../hits?patt=[lemma=\"gobierno\"]&filter=date:2023-*"

# Nur Radio Mitre
curl ".../hits?patt=[lemma=\"gobierno\"]&filter=radio:\"Radio Mitre\""
```

---

## WPL-Konfiguration (`corapan-wpl.blf.yaml`)

### Grundstruktur

```yaml
displayName: "CO.RA.PAN Corpus (WPL with structures)"
fileType: text
```

**Unterschiede zu TSV:**
- `fileType: text` (nicht `tabular`)
- Inline-Tags für Strukturen (`<s>`, `<utt>`, `<doc>`)
- Annotationen als Attribute (`@word`, `@lemma`)

---

### Inline-Tags

```yaml
inlineTags:
  - path: .//s
    displayName: "Sentence"
    mapAttributes:
      - from: id
        to: sentence_id
      - from: start_ms
        to: sent_start_ms
      - from: end_ms
        to: sent_end_ms
  
  - path: .//utt
    displayName: "Utterance"
    mapAttributes:
      - from: id
        to: utterance_id
      - from: start_ms
        to: utt_start_ms
      - from: end_ms
        to: utt_end_ms
      - from: speaker_code
        to: speaker_code
```

**WPL-Beispiel:**

```xml
<doc id="ARG_2023-08-10_ARG_Mitre">
<utt id="ARG_2023-08-10_ARG_Mitre:0" start_ms="1410" end_ms="2640" speaker_code="lib-pm">
<s id="ARG_2023-08-10_ARG_Mitre:0:s0" start_ms="1410" end_ms="1650">
5       word="5" norm="5" lemma="5" pos="NUM" ...
de      word="de" norm="de" lemma="de" pos="ADP" ...
</s>
</utt>
</doc>
```

---

### Strukturbasierte Suchen

**Mit WPL-Format möglich:**

```cql
# Innerhalb eines Satzes
<s/> containing [lemma="hablar"]

# Innerhalb einer Äußerung
<utt/> containing [lemma="hablar" & speaker_code="lib-pm"]

# Satzanfang
[pos="VERB"] within <s/> :: firsttoken

# Satzende
[pos="PUNCT" & word="."] within <s/> :: lasttoken
```

**Ohne WPL (TSV):**
- Struktursuchen nicht möglich
- Kontext muss App-seitig via `sentence_id` rekonstruiert werden

---

### Annotationen (WPL)

```yaml
annotations:
  - name: word
    valuePath: "@word"    # Attribut-Syntax
    sensitivity: sensitive
```

**Unterschied zu TSV:**
- `valuePath: word` → `valuePath: "@word"`
- Sonst identisch

---

## CQL-Query-Beispiele

### Einfache Suchen

```cql
# Exakte Wortform
[word="México"]

# Lemma
[lemma="cantar"]

# POS
[pos="VERB"]

# Kombiniert
[lemma="cantar" & pos="VERB"]
```

---

### Morphologie

```cql
# Verb im Präsens
[pos="VERB" & tense="Pres"]

# Subjunktiv
[pos="VERB" & mood="Sub"]

# 3. Person Singular
[pos="VERB" & person="3" & number="Sing"]

# Legacy: Perfecto Compuesto
[past_type="PerfectoCompuesto"]
```

---

### Phrasen

```cql
# Verb + Determiner + Substantiv
[pos="VERB"] [pos="DET"] [pos="NOUN"]

# Lemma-basiert
[lemma="cantar"] [pos="DET"] [pos="NOUN"]

# Mit Abstand (0-2 Wörter)
[lemma="cantar"] []{0,2} [pos="NOUN"]
```

---

### Case/Accent-Insensitiv

```cql
# Sensitiv (word): nur "México"
[word="México"]

# Insensitiv (norm): "México", "mexico", "MÉXICO"
[norm="mexico"]

# Lemma mit norm
[lemma="cantar" & norm=".*"]
```

---

### Metadaten-Filter

```cql
# Query + Metadaten-Filter (via API)
patt=[lemma="gobierno"]&filter=country_code:ARG

# Mehrere Filter
patt=[lemma="gobierno"]&filter=country_code:ARG AND date:2023-*

# Speaker-Filter
patt=[word=".*"]&filter=speaker_code:lib-pm
```

---

### Mit Strukturen (nur WPL)

```cql
# Verb am Satzanfang
[pos="VERB"] within <s/> :: firsttoken

# Satz mit bestimmtem Wort
<s/> containing [lemma="hablar"]

# Äußerung mit mehreren Wörtern
<utt/> containing ([lemma="hablar"] []{0,5} [lemma="gobierno"])
```

---

## Autocomplete-Konfiguration

Für BlackLab-Frontend:

```yaml
# In blacklab-server.yaml oder corpus-frontend.json
autocomplete:
  - annotation: word
    sensitivity: sensitive
    maxItems: 50
  
  - annotation: norm
    sensitivity: insensitive
    maxItems: 50
  
  - annotation: lemma
    sensitivity: sensitive
    maxItems: 50
```

**Verwendung:**
- `word` – Exakte Vorschläge (case-sensitiv)
- `norm` – Indifferente Vorschläge (häufiger genutzt)
- `lemma` – Lemma-Vorschläge

---

## Forward-Indexes

**Automatisch erstellt für:**
- Alle Annotationen in `.blf.yaml`
- Alle Metadaten-Felder

**Performance-Hinweis:**
Forward-Indexes ermöglichen:
- Schnelle Aggregationen (`facets`)
- Kontext-Anzeige
- `listvalues`-Abfragen

**Deaktivieren (falls nicht benötigt):**

```yaml
- name: tokid
  forwardIndex: false  # Spart Speicherplatz
```

---

## Fehlerbehebung

### Problem: Annotation nicht durchsuchbar

**Symptom:**
```cql
[lemma="hablar"]
# → 0 Treffer
```

**Diagnose:**

1. Prüfe `.blf.yaml`:
   ```yaml
   - name: lemma
     valuePath: lemma  # MUSS mit TSV-Spaltenname oder WPL-Attribut übereinstimmen
   ```

2. Prüfe Eingabedatei:
   ```bash
   head -n 5 exports/tsv/ARG_2023-08-10_ARG_Mitre.tsv
   # Spalte "lemma" vorhanden und befüllt?
   ```

3. Index neu erstellen

---

### Problem: Metadaten fehlen

**Symptom:**
```bash
curl ".../docs/ARG_2023-08-10_ARG_Mitre"
# → "country_code": null
```

**Diagnose:**

1. Prüfe `docmeta.jsonl`:
   ```bash
   grep "ARG_2023-08-10_ARG_Mitre" exports/docmeta.jsonl
   # → {"doc": "ARG_2023-08-10_ARG_Mitre", "country_code": "ARG", ...}
   ```

2. Prüfe `blacklab-server.yaml`:
   ```yaml
   metadata:
     documentFormat: jsonlines
     path: "exports/docmeta.jsonl"  # Pfad korrekt (relativ oder absolut)?
   ```

3. BlackLab-Server neu starten

---

### Problem: Struktursuchen funktionieren nicht

**Symptom:**
```cql
<s/> containing [lemma="hablar"]
# → Error: "Unknown span type: s"
```

**Ursache:** TSV-Format verwendet (keine Strukturen)

**Lösung:**
1. WPL-Export verwenden:
   ```bash
   python blacklab_index_creation.py --format wpl
   ```

2. Index mit `corapan-wpl.blf.yaml` neu erstellen

---

## Performance-Tuning

### RAM-Einstellungen

```bash
# Mehr Heap für große Indices
java -Xmx8G -jar blacklab.jar create ...
```

### Forward-Index selektiv

```yaml
# Nur für häufig genutzte Annotationen
- name: word
  forwardIndex: true

- name: tokid
  forwardIndex: false  # Spart Speicher, wenn nur für Rücksprung genutzt
```

### Cache-Größe

```yaml
# In blacklab-server.yaml
cacheSize:
  maxNumberOfJobs: 100
  maxSizePerJob: 10000
  maxTotalJobs: 200
```

---

## Siehe auch

- [BlackLab Indexing Guide](../how-to/blacklab-indexing.md) - Schritt-für-Schritt-Anleitung
- [Corpus Search Architecture](../concepts/corpus-search-architecture.md) - Gesamtarchitektur
- [BlackLab Official Docs](https://inl.github.io/BlackLab/) - Externe BlackLab-Dokumentation
- [CQL Documentation](https://inl.github.io/BlackLab/corpus-query-language.html) - Query-Syntax
