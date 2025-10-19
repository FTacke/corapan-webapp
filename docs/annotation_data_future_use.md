# Annotation Data Database - Zukunftsplanung

## 📊 Status: BEREIT aber NICHT AKTIV

Die `annotation_data.db` ist:
- ✅ Erstellt und aktuell (1.35M Einträge)
- ✅ Optimiert mit Index auf `token_id`
- ✅ Enthält linguistische Annotations
- ⚠️ **Wird aktuell NICHT von der Webapp genutzt**

---

## 🔍 Was ist drin?

### Spalten:
- `token_id` - Verknüpfung zu transcription.db
- `segment_index`, `token_index` - Position
- `lemma` - Grundform
- `pos` - Part-of-Speech Tag (NOUN, VERB, etc.)
- `dep` - Dependency Tag (ROOT, case, det, etc.)
- `head_text` - Syntaktisches Head
- `morph` - Morphologische Features (JSON)
- `neighbors_left`, `neighbors_right` - Kontext (JSON)
- **`foreign_word`** - Fremdwort-Flag (0 oder 1)

### Statistiken:
- Total: 1,351,207 Annotations
- Foreign words: 779
- Indexes: 2 (token_id + UNIQUE)

---

## 🚀 Zukünftige Verwendung

Diese DB wird wichtig für erweiterte Suchfunktionen:

### 1. **POS-Filter** (Part-of-Speech)
```sql
-- Finde alle Substantive
SELECT t.* FROM tokens t
JOIN annotations a ON a.token_id = t.token_id
WHERE a.pos = 'NOUN'
```

### 2. **Fremdwort-Suche**
```sql
-- Finde alle markierten Fremdwörter
SELECT t.* FROM tokens t
JOIN annotations a ON a.token_id = t.token_id
WHERE a.foreign_word = '1'
```

### 3. **Lemma-Suche** (bereits in tokens, aber hier mit POS)
```sql
-- Finde alle Formen von "hablar" mit POS-Info
SELECT t.text, a.pos, a.lemma FROM tokens t
JOIN annotations a ON a.token_id = t.token_id
WHERE a.lemma = 'hablar'
```

### 4. **Syntaktische Suche**
```sql
-- Finde alle ROOT-Verben
SELECT t.* FROM tokens t
JOIN annotations a ON a.token_id = t.token_id
WHERE a.pos = 'VERB' AND a.dep = 'ROOT'
```

### 5. **Morphologische Features**
```sql
-- Suche nach spezifischen morphologischen Eigenschaften
-- z.B. Verben im Präteritum
SELECT t.*, a.morph FROM tokens t
JOIN annotations a ON a.token_id = t.token_id
WHERE a.pos = 'VERB' 
  AND a.morph LIKE '%Tense=Past%'
```

---

## 🔧 Optimierungen (wenn aktiv genutzt)

Falls Sie erweiterte Suchen implementieren, sollten **weitere Indexes** erstellt werden:

```sql
-- POS-Suchen beschleunigen
CREATE INDEX idx_annotations_pos ON annotations(pos);

-- Fremdwort-Filter beschleunigen
CREATE INDEX idx_annotations_foreign ON annotations(foreign_word);

-- Lemma-Suchen beschleunigen
CREATE INDEX idx_annotations_lemma ON annotations(lemma);

-- Kombinierte Suchen
CREATE INDEX idx_annotations_pos_lemma ON annotations(pos, lemma);
CREATE INDEX idx_annotations_pos_dep ON annotations(pos, dep);
```

---

## ✅ Was jetzt tun?

### Aktuell:
- **Nichts!** Die DB ist bereit, wird aber nicht benötigt
- Wird automatisch bei `database_creation_v2.py` aktualisiert
- Nimmt ~100 MB Speicher (kein Problem)

### Später (bei erweiterter Suche):
1. Neue Service-Funktion: `src/app/services/annotation_search.py`
2. Erweiterte Suchfilter im UI: POS, Foreign Words, etc.
3. Zusätzliche Indexes erstellen (siehe oben)
4. JOIN mit transcription.db für kombinierte Queries

---

## 💡 Beispiel für zukünftige Implementierung

```python
# src/app/services/annotation_search.py

def search_by_pos(pos_tag: str, limit: int = 100):
    """Search tokens by Part-of-Speech tag."""
    with open_db("transcription") as trans_conn:
        # annotation_data.db anhängen
        trans_conn.execute("ATTACH 'data/db/annotation_data.db' AS ann")
        
        cursor = trans_conn.cursor()
        cursor.execute("""
            SELECT t.token_id, t.text, t.lemma, a.pos, a.dep
            FROM tokens t
            JOIN ann.annotations a ON a.token_id = t.token_id
            WHERE a.pos = ?
            LIMIT ?
        """, (pos_tag, limit))
        
        return cursor.fetchall()
```

---

## 📊 Speichernutzung

```
annotation_data.db: ~100 MB
transcription.db:   ~350 MB
-----------------------------------
Total:              ~450 MB
```

Bei JOIN-Queries werden beide DBs im RAM gehalten (empfohlen: 2+ GB RAM).

---

**Fazit:** Die DB ist **ready to use** aber aktuell nicht nötig. Wenn Sie erweiterte linguistische Suchen implementieren möchten, ist alles vorbereitet! 🎉

**Erstellt:** 18. Oktober 2025  
**Status:** OPTIONAL - Für zukünftige Features
