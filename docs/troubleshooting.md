# CO.RA.PAN - Troubleshooting Guide

Häufige Probleme und deren Lösungen für die CO.RA.PAN Web-Anwendung.

---

## 🔍 Performance-Probleme

### Problem: Suche ist langsam (> 1 Sekunde)

#### Diagnose 1: Indizes vorhanden?
```bash
sqlite3 data/db/transcription.db "PRAGMA index_list('tokens');"
```

**Erwartete Ausgabe:**
```
0|idx_tokens_token_id|1|u|0
1|idx_tokens_text|0|c|0
2|idx_tokens_lemma|0|c|0
3|idx_tokens_country_code|0|c|0
4|idx_tokens_speaker_type|0|c|0
5|idx_tokens_mode|0|c|0
6|idx_tokens_filename_id|0|c|0
```

**Falls leer:** Indizes erstellen
```bash
cd LOKAL\database
python database_creation_v2.py
```

#### Diagnose 2: ANALYZE ausgeführt?
```bash
sqlite3 data/db/transcription.db "SELECT COUNT(*) FROM sqlite_stat1;"
```

**Falls 0:** ANALYZE ausführen
```sql
sqlite3 data/db/transcription.db
ANALYZE;
.quit
```

#### Diagnose 3: Query nutzt Index?
```sql
sqlite3 data/db/transcription.db
EXPLAIN QUERY PLAN SELECT * FROM tokens WHERE text = 'casa';
.quit
```

**Sollte zeigen:**
```
SEARCH TABLE tokens USING INDEX idx_tokens_text (text=?)
```

**Falls "SCAN TABLE":** Index nicht genutzt
```sql
REINDEX;
ANALYZE;
```

---

### Problem: "de" oder "la" lädt endlos

**Ursache:** Client-Side DataTables lädt alle 80.000 Rows

**Lösung prüfen:**
```bash
# Prüfen ob Server-Side Script geladen wird
curl http://127.0.0.1:8000/corpus/ | findstr "corpus_datatables_serverside"
```

**Sollte zeigen:**
```html
<script src="/static/js/corpus_datatables_serverside.js"></script>
```

**Falls noch alte Version:**
```html
<!-- templates/pages/corpus.html, Zeile ~353 -->
<script src="{{ url_for('static', filename='js/corpus_datatables_serverside.js') }}"></script>
```

---

### Problem: Sortierung funktioniert nicht

**Diagnose:** Browser-Console öffnen (F12), "Network" Tab

**Klick auf Spaltenheader "País"**, sollte zeigen:
```
GET /corpus/search/datatables?...&order[0][column]=5&order[0][dir]=asc...
```

**Falls `order[0][column]=0` immer:** Frontend-Problem

**Lösung:** Cache leeren
```
Strg+Shift+R (Hard Reload)
```

**Falls Backend-Error 500:** `SUPPORTED_SORTS` prüfen

```python
# src/app/services/corpus_search.py
SUPPORTED_SORTS = {
    "country_code": "country_code",  # ← Muss existieren!
    "speaker_type": "speaker_type",
    "text": "text",
    # ...
}
```

---

## 🎵 Audio-Probleme

### Problem: Audio spielt nicht ab (Pal:/Ctx: Buttons)

#### Diagnose 1: Event-Binding
Browser-Console (F12):
```javascript
$('.audio-button').length
```

**Sollte zeigen:** Anzahl der Audio-Buttons (z.B. 50 bei 25 Zeilen)

**Falls 0:** Event-Binding fehlt

**Lösung:** `corpus_datatables_serverside.js` prüfen
```javascript
// Zeile ~375
function bindAudioEvents() {
    $('.audio-button').off('click').on('click', function(e) {
        // ...
    });
}
```

#### Diagnose 2: Media-Endpoint
```bash
curl http://127.0.0.1:8000/media/play_audio/2023-08-10_ARG_Mitre.mp3?start=1&end=2
```

**Sollte:** Audio-Datei zurückgeben (Content-Type: audio/mpeg)

**Falls 404:** Audio-Datei fehlt
```bash
# Prüfen ob Datei existiert
dir media\mp3-full\ARG\2023-08-10_ARG_Mitre.mp3
```

#### Diagnose 3: Authentifizierung
```javascript
// Browser-Console
allowTempMedia
```

**Sollte:** `true` zeigen

**Falls undefined:** JavaScript nicht geladen

---

### Problem: "Audio konnte nicht geladen werden"

**Ursache 1:** Datei nicht gefunden

**Lösung:**
```bash
# Alle MP3s auflisten
dir /s media\mp3-full\*.mp3
```

**Ursache 2:** Falscher Dateiname im Token

**Prüfen:**
```sql
sqlite3 data/db/transcription.db
SELECT DISTINCT filename FROM tokens LIMIT 10;
.quit
```

**Sollte zeigen:** `2023-08-10_ARG_Mitre.mp3` (MIT .mp3 Extension)

---

## 📄 Player-Probleme

### Problem: Klick auf Archivo-Icon öffnet nichts

#### Diagnose: Link-Struktur prüfen
Browser DevTools → Rechtsklick auf Icon → "Element untersuchen"

**Sollte zeigen:**
```html
<a href="/player?transcription=/media/transcripts/2023-08-10_ARG_Mitre.json&audio=/media/full/2023-08-10_ARG_Mitre.mp3&token_id=ARG001" class="player-link">
  <i class="fa-regular fa-file"></i>
</a>
```

**Falls `href="#"` oder falsch:** Frontend-Rendering-Problem

**Lösung:** `corpus_datatables_serverside.js` Zeile ~313-343 prüfen
```javascript
const base = filename.trim().replace(/\.mp3$/i, '');
const transcriptionPath = `${MEDIA_ENDPOINT}/transcripts/${base}.json`;
const audioPath = `${MEDIA_ENDPOINT}/full/${base}.mp3`;
```

#### Diagnose: Player-Route
```bash
curl http://127.0.0.1:8000/player?transcription=/media/transcripts/2023-08-10_ARG_Mitre.json&audio=/media/full/2023-08-10_ARG_Mitre.mp3&token_id=ARG001
```

**Sollte:** HTML-Seite zurückgeben (200 OK)

**Falls 400 Bad Request:** Parameter fehlen

**Falls 404:** Route nicht registriert
```python
# src/app/main.py prüfen
from .routes import player
app.register_blueprint(player.blueprint)
```

---

### Problem: Player öffnet, aber "Transcription not found"

**Ursache:** JSON-Datei fehlt

**Prüfen:**
```bash
dir media\transcripts\ARG\2023-08-10_ARG_Mitre.json
```

**Falls nicht gefunden:**
- JSON-Datei fehlt in `media/transcripts/`
- Pfad-Struktur falsch (sollte nach Land unterteilt sein)

**Lösung:**
```bash
# Transcript-Struktur prüfen
dir /s media\transcripts\*.json | findstr ARG
```

---

## 🗄️ Datenbank-Probleme

### Problem: "Database is locked"

**Ursache:** Server läuft noch (WAL-Modus)

**Lösung:**
```powershell
# Alle Python-Prozesse stoppen
Get-Process -Name python | Where-Object { $_.Path -like "*CO.RA.PAN*" } | Stop-Process -Force

# WAL-Dateien löschen
cd data\db
del transcription.db-wal
del transcription.db-shm
```

---

### Problem: "No such table: tokens"

**Ursache:** Datenbank nicht erstellt oder beschädigt

**Lösung:**
```bash
cd LOKAL\database
python database_creation_v2.py
```

---

### Problem: Datenbank sehr groß (> 500 MB)

**Diagnose:**
```sql
sqlite3 data/db/transcription.db
SELECT page_count * page_size / 1024.0 / 1024.0 AS size_mb 
FROM pragma_page_count(), pragma_page_size();
.quit
```

**Sollte:** ~350 MB sein

**Falls > 500 MB:** VACUUM ausführen
```sql
sqlite3 data/db/transcription.db
VACUUM;
.quit
```

**⚠️ Dauer:** Kann 5-10 Minuten dauern!

---

## 🌐 Server-Probleme

### Problem: Server startet nicht

#### Error: "Address already in use"

**Lösung:**
```powershell
# Port 8000 freigeben
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

#### Error: "ModuleNotFoundError: No module named 'flask'"

**Lösung:**
```bash
.\.venv\Scripts\activate
pip install -r requirements.txt
```

#### Error: "Failed to find application in module 'src.app.main'"

**Lösung:**
```powershell
# Korrekte Umgebungsvariable setzen
$env:FLASK_APP="src.app.main"
.\.venv\Scripts\python.exe -m flask run --port=8000
```

---

### Problem: 500 Internal Server Error bei Search

**Diagnose:** Logs prüfen
```bash
# In separatem Terminal
Get-Content logs/application.log -Wait -Tail 50
```

**Häufige Fehler:**

#### TypeError: 'Counter' object is not callable
```python
# FALSCH:
counter_search()

# RICHTIG:
counter_search.increment()
```

#### TypeError: 'NoneType' object is not iterable
```python
# FALSCH:
def _normalise(values):
    return [v.strip() for v in values]

# RICHTIG:
def _normalise(values):
    if values is None:
        return []
    return [v.strip() for v in values if v]
```

---

## 🎨 Frontend-Probleme

### Problem: DataTable zeigt "No data available"

**Diagnose:** Browser Console (F12)

**Sollte zeigen:**
```
DataTable (Server-Side) initialized
```

**Falls Error:** AJAX-Request fehlgeschlagen

**Network-Tab prüfen:**
```
GET /corpus/search/datatables?...
Status: 200 OK
```

**Falls 500:** Backend-Problem (siehe oben)

**Falls 404:** Route nicht registriert
```python
# src/app/routes/corpus.py
@blueprint.get("/corpus/search/datatables")
def search_datatables():
    # ...
```

---

### Problem: Spalten zeigen falsche Daten

**Diagnose:** Backend-Array prüfen

```python
# src/app/routes/corpus.py, Zeile ~218
data.append([
    idx,                        # 0: #
    item["context_left"],       # 1: Ctx.←
    item["text"],               # 2: Palabra
    item["context_right"],      # 3: Ctx.→
    item["audio_available"],    # 4: Audio
    item["country_code"],       # 5: País  ← WICHTIG!
    # ...
])
```

**Frontend-Mapping prüfen:**
```javascript
// static/js/corpus_datatables_serverside.js, Zeile ~233
columns: [
    { data: 0 },  // #
    { data: 1 },  // Ctx.←
    { data: 2 },  // Palabra
    // ...
    { data: 5 },  // País ← Muss mit Backend übereinstimmen!
]
```

---

## 🔄 Export-Probleme

### Problem: Export-Buttons fehlen

**Lösung:** Buttons.js laden
```html
<!-- templates/pages/corpus.html -->
<script src="https://cdn.datatables.net/buttons/2.3.6/js/dataTables.buttons.min.js"></script>
```

---

### Problem: Excel-Export zeigt Audio-Spalte

**Lösung:** exportOptions anpassen
```javascript
// static/js/corpus_datatables_serverside.js, Zeile ~186
buttons: [
    {
        extend: 'excel',
        exportOptions: {
            columns: [0,1,2,3,5,6,7,8,9,10,11]  // Skip column 4 (Audio)
        }
    }
]
```

---

## 📱 Mobile/Browser-Probleme

### Problem: Tabelle auf Handy zu breit

**Lösung:** Responsive Extension aktivieren
```javascript
$('#corpus-table').DataTable({
    responsive: true,
    scrollX: true,  // Horizontal Scrolling
    // ...
});
```

---

### Problem: Icons werden nicht angezeigt

**Ursache:** Font Awesome nicht geladen

**Lösung:**
```html
<!-- templates/base.html -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
```

---

## 🛠️ Debug-Modus aktivieren

### Flask Debug Mode
```powershell
$env:FLASK_DEBUG="1"
.\.venv\Scripts\python.exe -m flask run --port=8000
```

**Zeigt:**
- Detaillierte Error-Messages
- Auto-Reload bei Code-Änderungen
- Interactive Debugger im Browser

**⚠️ NUR für Development!**

---

### SQL-Queries loggen

```python
# src/app/services/corpus_search.py
import logging

def search_tokens(params: SearchParams):
    # ...
    logging.debug(f"SQL Query: {data_sql}")
    logging.debug(f"Bindings: {bindings_for_data}")
    cursor.execute(data_sql, bindings_for_data)
```

**In Console:**
```bash
# Logging-Level setzen
$env:FLASK_LOG_LEVEL="DEBUG"
```

---

## 📞 Letzte Rettung: Clean Reset

Wenn nichts hilft:

```bash
# 1. Server stoppen
Get-Process -Name python | Stop-Process -Force

# 2. Backup erstellen
copy data\db\transcription.db data\db\transcription_emergency_backup.db

# 3. Datenbank neu erstellen
cd LOKAL\database
python database_creation_v2.py

# 4. Cache leeren
# Browser: Strg+Shift+Delete → Alles löschen

# 5. Server neu starten
cd ..\..
$env:FLASK_APP="src.app.main"
.\.venv\Scripts\python.exe -m flask run --port=8000

# 6. Hard Reload
# Browser: Strg+Shift+R
```

---

## 📊 Health Check Script

```python
# health_check.py
import sqlite3
import requests
from pathlib import Path

def check_database():
    """Datenbank-Status prüfen"""
    db = Path("data/db/transcription.db")
    if not db.exists():
        print("❌ Datenbank nicht gefunden!")
        return False
    
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    
    # Indizes prüfen
    cursor.execute("PRAGMA index_list('tokens')")
    indices = cursor.fetchall()
    if len(indices) < 7:
        print(f"⚠️  Nur {len(indices)}/7 Indizes gefunden!")
        return False
    
    print("✅ Datenbank OK")
    return True

def check_server():
    """Server erreichbar?"""
    try:
        r = requests.get("http://127.0.0.1:8000", timeout=5)
        if r.status_code == 200:
            print("✅ Server läuft")
            return True
    except:
        print("❌ Server nicht erreichbar!")
        return False

def check_search():
    """Search-Endpoint testen"""
    try:
        r = requests.get(
            "http://127.0.0.1:8000/corpus/search/datatables",
            params={
                "query": "test",
                "search_mode": "text",
                "start": 0,
                "length": 25,
                "draw": 1
            },
            timeout=10
        )
        if r.status_code == 200:
            print("✅ Search-Endpoint OK")
            return True
        else:
            print(f"⚠️  Search-Endpoint: Status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Search-Endpoint Fehler: {e}")
        return False

if __name__ == "__main__":
    print("🔍 CO.RA.PAN Health Check\n")
    
    db_ok = check_database()
    server_ok = check_server()
    search_ok = check_search() if server_ok else False
    
    print(f"\n{'✅' if all([db_ok, server_ok, search_ok]) else '❌'} Gesamtstatus")
```

**Ausführen:**
```bash
python health_check.py
```

---

**Letzte Aktualisierung:** 18. Oktober 2025  
**Bei weiteren Problemen:** Logs in `logs/application.log` prüfen
