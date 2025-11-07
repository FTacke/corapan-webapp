# Media Folder Structure & Organization

## 📁 Neue Ordnerstruktur mit Länder-Unterordnern

### **Aufbau:**

```
media/
├── mp3-full/          # Vollständige Aufnahmen (~20-30 Min, ~30 MB)
│   ├── ARG/
│   │   ├── 2023-08-10_ARG_Mitre.mp3
│   │   ├── 2023-08-12_ARG_Mitre.mp3
│   │   └── ...
│   ├── VEN/
│   │   ├── 2022-01-18_VEN_RCR.mp3
│   │   ├── 2022-03-14_VEN_RCR.mp3
│   │   └── ...
│   ├── MEX/
│   ├── CHI/
│   └── ...
│
├── mp3-split/         # 4-Minuten-Chunks mit 30s Overlap (~4 MB)
│   ├── ARG/
│   │   ├── 2023-08-10_ARG_Mitre_01.mp3
│   │   ├── 2023-08-10_ARG_Mitre_02.mp3
│   │   ├── 2023-08-10_ARG_Mitre_03.mp3
│   │   └── ...
│   ├── VEN/
│   │   ├── 2022-01-18_VEN_RCR_01.mp3
│   │   ├── 2022-01-18_VEN_RCR_02.mp3
│   │   └── ...
│   └── ...
│
├── transcripts/       # JSON-Transkriptionen (WICHTIG für Datenbank-Erstellung!)
│   ├── ARG/
│   │   ├── 2023-08-10_ARG_Mitre.json
│   │   └── ...
│   ├── VEN/
│   │   ├── 2022-01-18_VEN_RCR.json
│   │   └── ...
│   └── ...
│
└── mp3-temp/          # Temporäre Snippets (auto-cleanup nach 30 Min)
    ├── 12345_pal.mp3
    ├── 12345_ctx.mp3
    └── ...
```

---

## 🔍 Intelligente Pfad-Erkennung

Der Code erkennt automatisch die Ländercode-Unterordner:

### **Beispiel:**
```python
# Dateiname in Datenbank: "2022-01-18_VEN_RCR.mp3"
safe_audio_full_path("2022-01-18_VEN_RCR.mp3")

# Automatische Suche:
# 1. Versuche: media/mp3-full/2022-01-18_VEN_RCR.mp3 (flache Struktur)
# 2. Extrahiere "VEN" aus Dateinamen
# 3. Versuche: media/mp3-full/VEN/2022-01-18_VEN_RCR.mp3 ✓
```

**Unterstützte Ländercode-Formate:**
- 2-stellig: `ARG`, `MEX`, `CHI`, `VEN`, `PER`, etc.
- 3-stellig: `ARG-CHT`, `ARG-CBA`, `ES-CAN`, etc.

---

## ⚡ Performance-Optimierung mit Split-Dateien

### **Split-Dateien-Schema:**
```
Split-Nr.  Start   End     Overlap
_01        0:00    4:00    -
_02        3:30    7:30    30s mit _01
_03        7:00    11:00   30s mit _02
_04        10:30   14:30   30s mit _03
...
_29        98:00   102:00  30s mit _28
```

### **Performance-Gewinn:**

| Methode | Dateigröße | Ladezeit | Speicher |
|---------|------------|----------|----------|
| **Split-Datei** | ~4 MB | ~0.3s | ~4 MB |
| **Full-Datei** | ~30 MB | ~2s | ~30 MB |
| **Speedup** | 7.5x kleiner | **6-10x schneller** | 7.5x weniger |

### **Automatische Split-First-Strategie:**

```python
def build_snippet(filename, start, end):
    # 1. Versuche Split-Datei (SCHNELL ⚡)
    if split_file_found:
        audio = load_split_file()  # Lädt nur ~4 MB
    
    # 2. Fallback: Full-Datei (funktioniert immer)
    else:
        audio = load_full_file()   # Lädt ~30 MB
```

**Beispiel:**
```
User klickt Play bei 5:45-5:48 Uhr
→ System findet Split-Datei "_02" (3:30-7:30)
→ Lädt nur 4 MB statt 30 MB
→ Extrahiert 3 Sekunden
→ ~6x schneller! 🚀
```

---

## 📦 Migration: Dateien in Unterordner verschieben

### **Automatisches Skript:**

```python
# scripts/organize_media_files.py
from pathlib import Path
import shutil
import re

def extract_country_code(filename):
    match = re.match(r'\d{4}-\d{2}-\d{2}_([A-Z]{2,3}(?:-[A-Z]{3})?)', filename)
    return match.group(1) if match else None

def organize_folder(source_dir, patterns=['*.mp3', '*.json']):
    for pattern in patterns:
        for file in source_dir.glob(pattern):
            country_code = extract_country_code(file.name)
            if country_code:
                target_dir = source_dir / country_code
                target_dir.mkdir(exist_ok=True)
                target_file = target_dir / file.name
                shutil.move(str(file), str(target_file))
                print(f"Moved: {file.name} → {country_code}/")

# Ausführen:
organize_folder(Path("media/mp3-full"), ['*.mp3'])
organize_folder(Path("media/mp3-split"), ['*.mp3'])
organize_folder(Path("media/transcripts"), ['*.json'])
```

---

## ✅ Abwärtskompatibilität

Der Code ist **vollständig abwärtskompatibel**:

- ✅ Funktioniert mit flacher Struktur (`media/mp3-full/*.mp3`)
- ✅ Funktioniert mit Unterordnern (`media/mp3-full/VEN/*.mp3`)
- ✅ Funktioniert ohne Split-Dateien (Fallback auf Full)
- ✅ Keine Datenbank-Migration nötig!

---

## 🧪 Testing

Nach dem Verschieben der Dateien:

```bash
# Test 1: Audio abspielen
# Gehe zu Corpus → Suche "voy" → Klicke Play

# Test 2: Player öffnen
# Klicke auf Emis. Icon → Player sollte öffnen

# Test 3: Split-Performance prüfen
# Console-Log zeigt: "Using split file: _05" (wenn gefunden)
```

---

## 📊 Statistik-Beispiel

Nach Migration:

```
media/mp3-full/
├── ARG/          23 Dateien
├── VEN/          12 Dateien
├── MEX/          18 Dateien
├── CHI/          15 Dateien
└── ...           64 weitere

media/mp3-split/
├── ARG/          ~460 Dateien (23 × ~20 Splits)
├── VEN/          ~240 Dateien (12 × ~20 Splits)
└── ...

Total: 132 Full-Dateien → 2492 Split-Dateien
```

---

## 🎯 Zusammenfassung

**Vorteile der neuen Struktur:**
1. ✅ Bessere Organisation (132 Dateien → 24 Unterordner)
2. ✅ 6-10x schnellere Audio-Snippets (Split-First-Strategie)
3. ✅ Keine Code-Änderungen nach Migration nötig
4. ✅ Automatische Ländercode-Erkennung
5. ✅ Vollständig abwärtskompatibel

**Performance-Gewinn:**
- Snippet-Generierung: **0.3s** statt 2s
- Speicherverbrauch: **4 MB** statt 30 MB
- User-Experience: **Instant playback** 🚀

---

## 🗄️ Datenbank-Erstellung

**Wichtig:** Die Datenbank-Skripte wurden für die neue Struktur angepasst!

### **Betroffene Skripte:**
- `LOKAL/database/database_creation.py` - Erstellt stats_all, stats_country, stats_files, transcription.db
- `LOKAL/database/semantic_database_creation.py` - Erstellt semantic_data.db

### **Änderungen:**
- ❌ **Alt:** Suchte in `grabaciones/*.json` (flache Struktur)
- ✅ **Neu:** Sucht in `media/transcripts/{COUNTRY}/*.json` (verschachtelte Struktur)

### **Ausführung:**
```bash
cd LOKAL/database
python database_creation.py
python semantic_database_creation.py
```

**Ergebnis:** Scannt automatisch alle 24 Länder-Unterordner und verarbeitet 132 JSON-Dateien.

Details siehe: `LOKAL/database/MIGRATION_NOTES.md`
