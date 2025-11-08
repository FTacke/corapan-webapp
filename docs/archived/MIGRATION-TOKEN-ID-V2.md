# Token ID Migration to v2 - Deterministic System

## Übersicht

Das Token-ID-System wurde auf ein **deterministisches, re-run-stabiles Verfahren** umgestellt, das unabhängig von der Verarbeitungsreihenfolge immer identische IDs erzeugt.

## Hauptänderungen

### 1. Deterministische ID-Berechnung

**Alte Methode (v1):**
- Hash basierend auf: `date`, `start`, `end`, `text[:3]`
- Adaptive Verlängerung bei Kollisionen während der Verarbeitung
- **Reihenfolgenabhängig**: unterschiedliche Verarbeitungsreihenfolge → unterschiedliche IDs

**Neue Methode (v2):**
- Hash basierend auf: `country_code`, `date`, `start`, `end`
- **Kein Text mehr**: reproduzierbar auch bei Textänderungen
- **Reihenfolgenunabhängig**: globale Präfixlängen-Berechnung
- Zeitwerte kanonisiert: `f"{float(x):.2f}"` (2 Dezimalstellen)

### 2. ID-Format

```
{COUNTRY_CODE_NO_HYPHENS}{HASH_PREFIX}
```

**Beispiele:**
- `ESPCAN9a4b2c3d1` (9 Hex-Zeichen, Standard)
- `ARGBA10f3e4d5c2a` (10 Hex bei Kollision)
- `MEX12a1b2c3d4e5f6` (12 Hex in seltenen Fällen)

**Ländercode-Normalisierung:**
- Bindestriche entfernt: `ESP-CAN` → `ESPCAN`
- Uppercase: `espcan` → `ESPCAN`
- Getrimmt

### 3. Minimale Präfixlängen-Algorithmus

**Ordnungsunabhängiges Verfahren:**

1. **Digest-Berechnung** für alle Tokens:
   ```python
   composite = f"{country_code_normalized}|{date_iso}|{start:.2f}|{end:.2f}"
   digest = md5(composite.encode("utf-8")).hexdigest()  # 32 Hex
   ```

2. **Bucketing mit iterativer Verlängerung**:
   - Start: `k=9` Hex-Zeichen
   - Gruppiere nach `digest[:k]`
   - Für alle Buckets mit >1 Token: erhöhe `k` um +1
   - Wiederhole bis alle Präfixe eindeutig
   - Fallback: max `k=12`

3. **Eigenschaften**:
   - ✅ Deterministisch
   - ✅ Minimal notwendige Länge
   - ✅ Keine Reihenfolgenabhängigkeit

### 4. Migration Mode

**Steuerung über globale Variable:**

```python
MIGRATE_V2 = False  # Normal: preserve existing IDs
MIGRATE_V2 = True   # Migration: overwrite all IDs
```

**Verhalten:**

| Modus | Existierende token_id | Verhalten |
|-------|----------------------|-----------|
| `False` | vorhanden | ✅ ID übernehmen (unverändert) |
| `False` | fehlt | ✅ v2-ID berechnen und schreiben |
| `True` | vorhanden | 🔄 v2-ID berechnen und **überschreiben** |
| `True` | fehlt | 🔄 v2-ID berechnen und schreiben |

### 5. JSON als Source of Truth

- JSON-Dateien enthalten `token_id` direkt im `word`-Objekt
- Bei `MIGRATE_V2=False` werden vorhandene IDs respektiert
- Nur bei fehlenden IDs oder Migration werden neue IDs generiert

### 6. Deterministische Traversal-Order

```python
# Länderordner alphabetisch sortiert
countries = sorted([d for d in TRANSCRIPTS_DIR.iterdir() if d.is_dir()], 
                  key=lambda p: p.name)

# JSON-Dateien pro Land alphabetisch sortiert
country_files = sorted(country_dir.glob("*.json"), 
                      key=lambda p: p.name)
```

## Migration-Prozess

### Einmalige Migration (alle IDs überschreiben)

1. **Vorbereitung:**
   ```python
   # In database_creation_v2.py
   MIGRATE_V2 = True  # ⚠️ Aktivieren
   ```

2. **Ausführung:**
   ```bash
   python database_creation_v2.py
   ```

3. **Was passiert:**
   - Alle JSONs werden gelesen
   - Alle Tokens erhalten neue v2-IDs (unabhängig von bestehenden IDs)
   - JSONs werden mit neuen IDs überschrieben
   - DBs werden frisch angelegt und befüllt

4. **Nach Migration:**
   ```python
   MIGRATE_V2 = False  # ⚠️ Deaktivieren!
   ```

### Normale Ausführung (nach Migration)

```python
MIGRATE_V2 = False  # Standard-Modus
```

- Vorhandene `token_id` in JSONs werden übernommen
- Nur neue Tokens (ohne ID) erhalten v2-IDs
- Wiederholte Läufe sind **idempotent**

## Validierung

Das Script prüft automatisch:

1. **Eindeutigkeit**: Alle `token_id` sind unique
2. **Statistik**: Verteilung der Präfixlängen
   ```
   Prefix length distribution:
      9 hex: 145,234 tokens (92.3%)
      10 hex: 11,456 tokens (7.3%)
      11 hex: 623 tokens (0.4%)
      12 hex: 12 tokens (0.0%)
   ```

3. **Fehlerbehandlung**: 
   - Wenn `k > 12`: RuntimeError mit Details zu kollidierenden Keys
   - Duplikate werden erkannt und geloggt

## Vorteile des neuen Systems

| Eigenschaft | v1 (alt) | v2 (neu) |
|-------------|----------|----------|
| Reproduzierbar | ❌ Nein | ✅ Ja |
| Reihenfolgenunabhängig | ❌ Nein | ✅ Ja |
| Minimale ID-Länge | ⚠️ Adaptiv | ✅ Optimal |
| Re-run stabil | ❌ Nein | ✅ Ja |
| Text-unabhängig | ❌ Nein | ✅ Ja |
| Migration-fähig | ❌ Nein | ✅ Ja |

## Technische Details

### Hash-Composite

```python
def make_digest(cc, date_iso, start, end):
    cc_normalized = cc.replace("-", "").upper().strip()
    st2 = f"{float(start):.2f}"  # Kanonisiert: 2 Dezimalen
    et2 = f"{float(end):.2f}"  # Kanonisiert: 2 Dezimalen
    composite = f"{cc_normalized}|{date_iso}|{st2}|{et2}"
    digest = hashlib.md5(composite.encode("utf-8")).hexdigest()
    return cc_normalized, digest
```

### Präfixlängen-Zuweisung

```python
def assign_min_unique_prefix_lengths(digests, k_start=9, k_max=12):
    n = len(digests)
    k = [k_start] * n
    unresolved = set(range(n))
    
    while unresolved:
        buckets = defaultdict(list)
        for i in unresolved:
            buckets[digests[i][:k[i]]].append(i)
        
        clashes = [idxs for idxs in buckets.values() if len(idxs) > 1]
        if not clashes:
            break
        
        next_unresolved = set()
        for idxs in clashes:
            for i in idxs:
                k[i] += 1
                if k[i] > k_max:
                    raise RuntimeError(f"Exceeded k_max={k_max}")
                next_unresolved.add(i)
        
        unresolved = next_unresolved
    
    return k
```

## Akzeptanzkriterien

✅ **Erreicht:**

1. ✅ Wiederholte Läufe erzeugen identische IDs
2. ✅ Reihenfolge der Verarbeitung hat keinen Effekt
3. ✅ IDs so kurz wie möglich (9 Hex Standard)
4. ✅ Nur bei Kollisionen 10-12 Hex
5. ✅ Keine Bindestriche im Ländercode
6. ✅ Migration überschreibt alte IDs einmalig
7. ✅ JSON als Single Source of Truth
8. ✅ Deterministische Dateireihenfolge
9. ✅ Kanonisierte Zeitformate

## Troubleshooting

### Problem: "Hash prefix exceeded 12 hex"

**Ursache:** Zu viele Tokens mit identischen Metadaten (country, date, start, end)

**Lösung:**
- Prüfe die geloggten kollidierenden Keys
- Prüfe ob Zeitstempel korrekt kanonisiert sind
- Falls legitim: erhöhe `k_max` in `assign_min_unique_prefix_lengths()`

### Problem: IDs ändern sich bei jedem Lauf

**Ursache:** `MIGRATE_V2 = True` ist noch aktiviert

**Lösung:** Setze `MIGRATE_V2 = False` nach einmaliger Migration

### Problem: Duplikate in token_id

**Ursache:** Bug im Präfixlängen-Algorithmus oder Hash-Kollisionen

**Lösung:** Script bricht mit Fehlermeldung ab und loggt betroffene IDs

## Performance

**Vier-Phasen-Verarbeitung:**

1. **Phase 1:** Token-Sammlung (schnell, I/O-bound)
2. **Phase 2:** Digest & Präfixlängen (CPU-intensiv, O(n log n))
3. **Phase 3:** JSON-Updates (I/O-bound, nur bei Änderungen)
4. **Phase 4:** DB-Insertion (I/O-bound, batched)

**Typische Laufzeit:**
- ~150.000 Tokens: 2-4 Minuten
- Präfixberechnung: <5 Sekunden
- Indexes & ANALYZE: ~20 Sekunden

## Beispiel-Output

```
================================================================================
4/4 --> Creating transcription.db & annotation_data.db (Deterministic IDs)
================================================================================
Migration Mode: ✅ DISABLED - Preserving existing IDs
================================================================================

📊 Phase 1: Collecting all tokens...
  Collecting: 50/157 files (45,234 tokens so far)
  Collecting: 100/157 files (92,456 tokens so far)
  Collecting: 157/157 files (157,325 tokens so far)

✅ Collected 157,325 valid tokens from 157 files

🔨 Phase 2: Computing deterministic token IDs...
  Computing minimal unique prefix lengths...

📊 Token ID Statistics:
   Total tokens: 157,325
   Unique IDs: 157,325
   Prefix length distribution:
      9 hex: 145,234 tokens (92.3%)
      10 hex: 11,456 tokens (7.3%)
      11 hex: 623 tokens (0.4%)
      12 hex: 12 tokens (0.0%)
   Min prefix: 9 hex
   Max prefix: 12 hex
   Median prefix: 9 hex

💾 Phase 3: Writing token IDs to JSON files...
✅ Modified 23 JSON files
   New IDs written: 1,234
   Existing IDs preserved: 156,091

🗄️  Phase 4: Creating databases...
  Inserting tokens into databases...
    Inserted 50,000/157,325 tokens
    Inserted 100,000/157,325 tokens
    Inserted 157,325/157,325 tokens

✅ Inserted 157,325 tokens into both databases

🔨 Creating performance indexes...
  Creating idx_tokens_text...
  Creating idx_tokens_lemma...
  [...]
✅ Created 7 indexes in 18.45s

📊 Running ANALYZE for query optimizer...
✅ ANALYZE completed in 2.34s

================================================================================
✅ Deterministic token ID generation complete!
================================================================================
```

## Weiteres Vorgehen

1. ✅ Script ist fertig implementiert
2. ⚠️ **Einmalige Migration durchführen** mit `MIGRATE_V2 = True`
3. ✅ Danach `MIGRATE_V2 = False` setzen
4. ✅ In Zukunft: normale Läufe sind idempotent
