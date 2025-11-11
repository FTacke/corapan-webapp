# Migration: Datenbank-Skripte für neue Media-Struktur angepasst

**Datum:** 16. Oktober 2025

## 📋 Zusammenfassung

Die Datenbank-Erstellungsskripte wurden vollständig für die neue Ordnerstruktur `media/transcripts/{COUNTRY}/` angepasst.

## ✅ Angepasste Dateien

### 1. **LOKAL/database/database_creation.py**
**Betroffene Funktionen:**
- `run_stats_all()` - Gesamtstatistik
- `run_stats_country()` - Statistik pro Land
- `run_stats_files()` - Metadaten pro Datei  
- `run_transcription()` - Token-Datenbank

**Änderung:**
```python
# ALT
folder = 'grabaciones'
json_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.json')]

# NEU
transcripts_dir = os.path.join('..', '..', 'media', 'transcripts')
json_files = []
if os.path.exists(transcripts_dir):
    for country_dir in os.listdir(transcripts_dir):
        country_path = os.path.join(transcripts_dir, country_dir)
        if os.path.isdir(country_path):
            for f in os.listdir(country_path):
                if f.endswith('.json'):
                    json_files.append(os.path.join(country_path, f))
```

### 2. **LOKAL/database/semantic_database_creation.py**
**Betroffene Funktion:**
- `main()` - Semantische Analyse

**Änderung:** Gleiche Pfad-Logik wie oben

## 📊 Verifikation

**Test erfolgreich:**
```
✓ 132 JSON-Dateien gefunden
✓ 24 Länder-Unterordner durchsucht:
  - ARG (8), ARG-Cba (3), ARG-Cht (3), ARG-SdE (3)
  - BOL (6), CHI (5), COL (6), CR (6), CUB (6)
  - ECU (6), ES-CAN (6), ES-MAD (6), ES-SEV (6)
  - GUA (6), HON (6), MEX (6), NIC (6), PAN (6)
  - PAR (6), PER (4), RD (6), SAL (6), URU (4), VEN (6)
```

## 🔧 Verwendung

**Ausführung aus Hauptverzeichnis:**
```bash
cd LOKAL/database
python database_creation.py
python semantic_database_creation.py
```

**Wichtig:** Skripte müssen aus `LOKAL/database/` ausgeführt werden, da sie relative Pfade verwenden (`../../media/transcripts/`).

## ⚠️ Breaking Changes

**Keine!** Die Skripte funktionieren:
- ✅ Mit der neuen Struktur (`media/transcripts/{COUNTRY}/`)
- ✅ Auch wenn `media/transcripts/` nicht existiert (leere Datenbanken)
- ✅ Mit allen Ländercode-Varianten (ARG, ES-MAD, ARG-Cba, etc.)

## 📝 Dokumentation

Details siehe:
- `LOKAL/database/MIGRATION_NOTES.md` - Technische Details
- `docs/media-folder-structure.md` - Ordnerstruktur-Dokumentation
