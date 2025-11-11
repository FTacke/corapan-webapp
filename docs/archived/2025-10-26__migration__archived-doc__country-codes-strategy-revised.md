# Strategie: Ländercode-Standardisierung von der Quelle aus

**Datum:** 19. Oktober 2025  
**Status:** Revidierte Strategie basierend auf Quellanalyse

---

## 🎯 KERNERKENNTNISSE

### Das System funktioniert so:

```
QUELLE (JSON-Files)
└─> media/transcripts/{FOLDER}/{YYYY-MM-DD}_{CODE}_{RADIO}.json
    └─> Metadaten INNERHALB des JSON: {"country": "Ländername", ...}
        └─> database_creation_v2.py liest beide
            └─> Erstellt DB-Tabellen:
                ├─> tokens.country_code      (aus Ordnername/Filename)
                ├─> stats_country.country    (aus JSON-Metadatum)
                └─> metadata.country         (aus JSON-Metadatum)
```

### ✅ Was IST konsistent:
- **Ordnername = Code im Filename** (100% übereinstimmend!)
- Struktur: `ARG/2023-08-10_ARG_Mitre.json` ✓

### ⚠️ Was NICHT konsistent ist:
- **Codes** (Ordner/Filename) ≠ **Namen** (JSON-Metadaten)
- **Codes** (ARG, ES-MAD) ≠ **Spaltennamen** (country vs. country_code)
- **Codes-Format:** Mixed Case (`ARG-Cba`) vs. Standards

---

## 📊 IST-ZUSTAND (Quelle: 132 JSON-Files)

### 1. Ordnerstruktur (`media/transcripts/`)
```
24 Ordner:
  - ARG, ARG-Cba, ARG-Cht, ARG-SdE
  - BOL, CHI, COL, CR, CUB, ECU
  - ES-CAN, ES-MAD, ES-SEV
  - GUA, HON, MEX, NIC, PAN, PAR, PER
  - RD, SAL, URU, VEN
```

### 2. Codes in Dateinamen (`YYYY-MM-DD_{CODE}_Radio.json`)
```
Identisch mit Ordnernamen (konsistent!)
  - ARG (8 files), ARG-Cba (3), ARG-Cht (3), ARG-SdE (3)
  - CHI (5), ES-MAD (6), ES-CAN (6), ES-SEV (6)
  - ... 24 verschiedene Codes
```

### 3. Metadaten INNERHALB der JSONs (`data['country']`)
```
NAMEN in Spanisch (nicht Codes!):
  - "Argentina" (8 files)
  - "Argentina/Córdoba" (3 files)
  - "Argentina/Chubut" (3 files)
  - "Argentina/Santiago del Estero" (3 files)
  - "Bolivia" (6 files)
  - "Chile" (5 files)
  - "España/Madrid" (6 files)
  - "España/Canarias" (6 files)
  - "España/Sevilla" (6 files)
  - ... 24 verschiedene Namen
```

### 4. Database Creation (`database_creation_v2.py`)

**Problem:** Script nutzt **BEIDE** Quellen inkonsistent:

```python
# FÜR tokens.country_code:
country_code = jf.parent.name  # ← Ordnername (CODE!)

# FÜR stats_country.country:
country_val = data.get("country", "")  # ← JSON-Metadatum (NAME!)

# FÜR metadata.country:
country = data.get('country','')  # ← JSON-Metadatum (NAME!)
```

**Resultat:**
- `tokens.country_code` = Codes (`ARG`, `ARG-Cba`, `ES-MAD`)
- `stats_country.country` = Namen (`Argentina`, `España/Madrid`)
- `metadata.country` = Namen (`Argentina`, `España/Madrid`)

---

## 🚨 KERNPROBLEM

### Die DB wird aus ZWEI inkonsistenten Quellen gefüllt:

```
Ordnername/Filename        JSON-Metadatum
  (CODE)                      (NAME)
    ↓                            ↓
ARG                    →    "Argentina"
ARG-Cba                →    "Argentina/Córdoba"
ES-MAD                 →    "España/Madrid"
CHI                    →    "Chile"
```

**→ DB-Spalten mischen Codes und Namen!**

---

## ✅ LÖSUNG: Single Source of Truth

### Prinzip: Codes in JSONs, Namen via Mapping

```
JSON-File sollte enthalten:
{
  "country_code": "ARG",           ← CODE (maschinenlesbar)
  "country_name": "Argentina",     ← NAME (menschenlesbar, optional)
  "country": "ARG",                ← Backwards compatibility
  ...
}
```

**Alternative (pragmatischer):**
- JSON behält `"country": "Argentina"` (Namen)
- `countries.py` mappt Namen → Codes
- DB speichert **nur** Codes (`country_code`)
- Display nutzt `code_to_name()` aus `countries.py`

---

## 📋 STRATEGIE: 3-Phasen-Ansatz

### Phase 1: Zentralisierung (JETZT)
**Ziel:** Alle Code↔Name-Mappings an EINER Stelle

✅ **`countries.py` als Single Source of Truth**
- Definiert ALLE gültigen Codes
- Mappt Codes ↔ Namen
- Unterscheidet national/regional
- Normalisiert Eingaben

```python
# countries.py enthält:
LOCATIONS = [
    Location('ARG', 'Argentina: Buenos Aires', 'national'),
    Location('ARG-CBA', 'Argentina: Córdoba', 'regional'),
    # ...
]

NAME_TO_CODE_MAP = {
    'Argentina': 'ARG',
    'Argentina/Córdoba': 'ARG-CBA',
    'España/Madrid': 'ESP',
    # ...
}
```

### Phase 2: DB-Creation anpassen (WICHTIG!)
**Ziel:** Alle DB-Spalten nutzen Codes, nicht Namen

**Änderungen an `database_creation_v2.py`:**

```python
# VORHER (inkonsistent):
country_val = data.get("country", "")  # ← NAME aus JSON
c.execute("INSERT INTO stats_country (country, ...) VALUES (?, ...)", 
          (country_val, ...))  # ← Speichert NAME

# NACHHER (konsistent):
from app.config.countries import name_to_code, normalize_country_code

# Variante A: Aus JSON-Name extrahieren
country_name = data.get("country", "")
country_code = name_to_code(country_name) or normalize_country_code(
    jf.parent.name  # Fallback: Ordnername
)

# Variante B: Ordnername als primäre Quelle
country_code = normalize_country_code(jf.parent.name)

# Beide Varianten speichern CODE:
c.execute("""
    INSERT INTO stats_country (country_code, country_name, ...)
    VALUES (?, ?, ...)
""", (country_code, country_name, ...))
```

**Wichtig:** Spalten umbenennen/ergänzen:
```sql
-- stats_country.db:
ALTER TABLE stats_country ADD COLUMN country_code TEXT;  -- NEU
-- 'country' behalten für Backwards Compatibility oder umbenennen

-- metadata.db:
ALTER TABLE metadata ADD COLUMN country_code TEXT;  -- NEU
```

### Phase 3: JSON-Metadaten vereinheitlichen (OPTIONAL, später)
**Ziel:** JSONs enthalten Codes statt Namen

**Variante A (minimaler Eingriff):**
- JSON-Feld `"country"` bleibt NAME
- Neue Feld `"country_code"` mit CODE
- Migration über Script

**Variante B (vollständig):**
- JSON-Feld `"country"` wird zu CODE
- Neues Feld `"country_name"` für Display

**Entscheidung:** Phase 3 ist OPTIONAL - countries.py Mapping reicht!

---

## 🔧 KONKRETE UMSETZUNG

### Schritt 1: `database_creation_v2.py` anpassen

**Datei:** `LOKAL/database/database_creation_v2.py`

#### Änderung 1: Import hinzufügen
```python
# Zeile ~28, nach anderen Importen:
import sys
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from app.config.countries import (
    normalize_country_code, 
    name_to_code, 
    code_to_name,
    get_location
)
```

#### Änderung 2: `run_stats_country()` anpassen
```python
def run_stats_country():
    # ...
    c.execute('''
        CREATE TABLE stats_country (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT UNIQUE,        -- CODE (neu!)
            country_name TEXT,                -- NAME (optional)
            total_word_count INTEGER,
            total_duration_country TEXT
        )
    ''')

    # ...
    for jf in json_files:
        # Strategie: Ordnername ist primäre Quelle (bereits Codes!)
        country_code = normalize_country_code(jf.parent.name)
        
        # Optional: Name aus JSON für Display
        country_name_from_json = data.get('country', '')
        
        # Falls JSON keinen Namen hat, aus code generieren
        if not country_name_from_json:
            country_name_from_json = code_to_name(country_code)
        
        # ...
        c.execute('''
            INSERT INTO stats_country 
            (country_code, country_name, total_word_count, total_duration_country)
            VALUES (?, ?, ?, ?)
        ''', (country_code, country_name_from_json, wc, dur_str))
```

#### Änderung 3: `run_stats_files()` anpassen
```python
def run_stats_files():
    # ...
    c.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            country_code TEXT,     -- CODE (statt country!)
            country_name TEXT,     -- NAME (optional)
            radio TEXT,
            date TEXT,
            revision TEXT,
            word_count INTEGER,
            duration TEXT
        )
    ''')

    # ...
    for jf in json_files:
        # Code aus Ordnername
        country_code = normalize_country_code(jf.parent.name)
        
        # Name aus JSON
        country_name = data.get('country', '')
        
        # ...
        c.execute('''
            INSERT INTO metadata 
            (filename, country_code, country_name, radio, date, ...)
            VALUES (?, ?, ?, ?, ?, ...)
        ''', (basef, country_code, country_name, radio, date, ...))
```

#### Änderung 4: `run_transcription_db()` - tokens table
```python
def run_transcription_db():
    # Tokens-Tabelle ist bereits korrekt! Nutzt Ordnername als country_code
    # Nur Normalisierung hinzufügen:
    
    country_code = normalize_country_code(jf.parent.name)
    
    # Rest bleibt gleich
```

### Schritt 2: Ordner/Dateinamen normalisieren (KRITISCH!)

**BEVOR du DB neu erstellst:**

```python
# Script: LOKAL/database/normalize_source_codes.py

from pathlib import Path
from app.config.countries import normalize_country_code

transcripts_dir = Path("media/transcripts")

# 1. Ordner umbenennen
for folder in transcripts_dir.iterdir():
    if not folder.is_dir():
        continue
    
    old_name = folder.name
    new_name = normalize_country_code(old_name)
    
    if old_name != new_name:
        new_path = folder.parent / new_name
        print(f"Rename: {old_name} → {new_name}")
        folder.rename(new_path)

# 2. Dateinamen anpassen
for json_file in transcripts_dir.glob("**/*.json"):
    parts = json_file.stem.split('_')
    if len(parts) >= 2:
        date, old_code, *rest = parts
        new_code = normalize_country_code(old_code)
        
        if old_code != new_code:
            new_name = f"{date}_{new_code}_{'_'.join(rest)}.json"
            new_path = json_file.parent / new_name
            print(f"Rename: {json_file.name} → {new_name}")
            json_file.rename(new_path)
```

**Wichtig:** Backup erstellen VORHER!

### Schritt 3: DB neu erstellen

```bash
# Backup alte DBs
cp data/db/*.db data/db/backup_$(date +%Y%m%d)/

# DB neu erstellen mit angepasstem Script
python LOKAL/database/database_creation_v2.py
```

### Schritt 4: Backend-Services anpassen

**Alle Services, die auf `country` statt `country_code` zugreifen:**

```python
# VORHER:
cursor.execute("SELECT country FROM stats_country")

# NACHHER:
cursor.execute("SELECT country_code, country_name FROM stats_country")

# Oder mit automatischem Fallback:
cursor.execute("""
    SELECT 
        COALESCE(country_code, country) as country_code,
        country_name
    FROM stats_country
""")
```

### Schritt 5: Frontend anpassen

- Templates: Bereits Codes verwenden ✓
- JavaScript: Codes normalisieren
- Atlas: `cityList` mit normalisierten Codes

---

## 🎨 ZENTRALE REFERENZ: `countries.py`

### Keine Funktionen wie `extract_country_code()` mehr nötig!

**VORHER:**
```python
# media_store.py
def extract_country_code(filename: str) -> Optional[str]:
    match = re.match(r'\d{4}-\d{2}-\d{2}_([A-Z]{2,3}(?:-[A-Za-z]{3})?)', filename)
    # ... komplexe Logik
```

**NACHHER:**
```python
# Alles nutzt countries.py
from app.config.countries import normalize_country_code

code = normalize_country_code(filename.split('_')[1])
# Fertig! Keine Regex mehr nötig.
```

### Alle Services importieren aus `countries.py`:

```python
# corpus_search.py
from app.config.countries import normalize_country_code, is_valid_code

def search(..., countries: list[str]):
    normalized = [normalize_country_code(c) for c in countries]
    # ...

# atlas.py
from app.config.countries import code_to_name, get_national_capitals

def fetch_country_stats():
    # DB gibt Codes zurück
    codes = cursor.fetchall()
    # Konvertiere für Display
    return [{'code': c, 'name': code_to_name(c)} for c in codes]
```

---

## ✅ VORTEILE DIESER STRATEGIE

### 1. Keine DB-Migration nötig!
- DB wird neu erstellt → automatisch korrekt
- Kein komplexes UPDATE-Script

### 2. Quelle bleibt einfach
- Ordner/Dateinamen werden normalisiert
- JSONs können Namen behalten (werden gemappt)

### 3. Ein System für alles
- `countries.py` = zentrale Wahrheit
- Alle anderen Module importieren davon
- Keine Duplikation von Mappings

### 4. Zukunftssicher
- Neues Land hinzufügen? → Eintrag in `countries.py`
- DB neu erstellen → automatisch dabei

### 5. Backwards Compatible
- Alte Codes werden automatisch normalisiert
- Legacy-Map ermöglicht Übergangszeit

---

## 🚫 WAS NICHT TUN

### ❌ NICHT: DB direkt migrieren
- Daten kommen aus JSONs
- DB ändern = temporär, bei nächster Erstellung überschrieben

### ❌ NICHT: JSON-Metadaten im Bulk ändern
- 132 Files manuell editieren = fehleranfällig
- Besser: Mapping in countries.py

### ❌ NICHT: Mehrere Code-Extraktions-Funktionen
- Eine Quelle: `countries.py`
- Eine Funktion: `normalize_country_code()`

---

## 📋 CHECKLISTE: Reihenfolge der Schritte

### Vorbereitung (einmalig):
- [x] `countries.py` erstellen ✓
- [ ] `countries.py` testen (Import, Funktionen)
- [ ] Backup von `media/transcripts/` erstellen
- [ ] Backup von `data/db/*.db` erstellen

### Phase 1: Quellen normalisieren
- [ ] Script erstellen: `normalize_source_codes.py`
- [ ] Dry-Run testen (nur Ausgabe, keine Änderungen)
- [ ] Ausführen: Ordner umbenennen (`ARG-Cba` → `ARG-CBA`)
- [ ] Ausführen: Dateien umbenennen
- [ ] Prüfen: `ES-MAD` → neue Entscheidung?
  - Option A: `ESP` (ohne Ordner-Umzug)
  - Option B: `ES-MAD` beibehalten (mit Mapping)

### Phase 2: DB-Creation anpassen
- [ ] `database_creation_v2.py` anpassen (Import)
- [ ] `run_stats_country()` ändern (country_code statt country)
- [ ] `run_stats_files()` ändern (country_code hinzufügen)
- [ ] `run_transcription_db()` prüfen (bereits korrekt?)
- [ ] Test: DB neu erstellen auf Kopie der Daten

### Phase 3: DB neu erstellen
- [ ] Backup der alten DBs
- [ ] `python LOKAL/database/database_creation_v2.py` ausführen
- [ ] Validieren: Spalten korrekt?
- [ ] Validieren: Codes statt Namen?
- [ ] Validieren: Counts korrekt?

### Phase 4: Backend anpassen
- [ ] `atlas.py`: country → country_code
- [ ] `corpus_search.py`: `normalize_country_code()` nutzen
- [ ] `media_store.py`: Simplify mit `countries.py`
- [ ] Alle Services testen

### Phase 5: Frontend
- [ ] `corpus.html`: Codes normalisieren (MAYÚSCULAS)
- [ ] `atlas_script.js`: `cityList` mit normalisierten Codes
- [ ] CSS: Icons für national/regional

### Phase 6: Testing
- [ ] Corpus-Suche mit verschiedenen Ländern
- [ ] Atlas-Karte lädt korrekt
- [ ] Export CSV hat korrekte Codes
- [ ] Player lädt Audio (Pfade korrekt)

---

## 🔑 ENTSCHEIDUNGEN ERFORDERLICH

### 1. ES-MAD Problem lösen?

**Option A: Umbenennen zu ESP**
- Ordner: `ES-MAD/` → `ESP/`
- Files: `2023-XX-XX_ES-MAD_...` → `2023-XX-XX_ESP_...`
- ✅ Konzeptionell korrekt (national = ohne Suffix)
- ❌ Großer Aufwand (alle Files umbenennen)

**Option B: ES-MAD beibehalten + Mapping**
- Ordner: `ES-MAD/` bleibt
- Mapping: `LEGACY_CODE_MAP['ES-MAD'] = 'ESP'`
- ✅ Kein File-Rename nötig
- ❌ Inkonsistent (Format suggeriert Regional)

**Empfehlung:** **Option A** - jetzt einmal richtig machen!

### 2. ISO-3166 Strikt durchsetzen?

**CHI → CHL, CR → CRI, SAL → SLV, ...**

**Option A: Ja, migrieren**
- ✅ International standardisiert
- ❌ Alle Files umbenennen

**Option B: Nein, Legacy-Map nutzen**
- ✅ Kein File-Rename
- ❌ Non-standard Codes

**Empfehlung:** **Option B** - zu aufwändig für geringen Nutzen

### 3. JSON-Metadaten ändern?

**Option A: Ja, Codes in JSON speichern**
- JSON: `"country": "ARG"` statt `"Argentina"`
- ✅ Konsistent mit Dateinamen
- ❌ 132 Files editieren

**Option B: Nein, Namen beibehalten**
- JSON: `"country": "Argentina"` bleibt
- Mapping: `name_to_code()` in `countries.py`
- ✅ Kein JSON-Edit nötig
- ❌ Zwei Darstellungen (Name vs. Code)

**Empfehlung:** **Option B** - Mapping reicht!

---

## 📝 NÄCHSTE SCHRITTE (Konkret)

### HEUTE:
1. Entscheidungen treffen (siehe oben)
2. Script `normalize_source_codes.py` erstellen
3. Dry-Run auf Backup testen

### MORGEN:
1. Quellen normalisieren (Ordner/Files umbenennen)
2. `database_creation_v2.py` anpassen
3. DB neu erstellen

### ÜBERMORGEN:
1. Backend-Services anpassen
2. Frontend anpassen
3. Testing

---

**Fragen? Unklarheiten?**

Diese Strategie basiert jetzt auf der **echten Quelle** (JSON-Files),
nicht auf der abgeleiteten DB. Viel pragmatischer! 🎯
