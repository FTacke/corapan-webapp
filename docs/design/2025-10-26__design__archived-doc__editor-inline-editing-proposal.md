# Editor System: Vollständiger Implementierungsplan

**Datum:** 25. Oktober 2025 (aktualisiert)  
**Status:** Implementation Ready  
**Für:** CO.RA.PAN Admin & Editor Rollen

---

## 1. Executive Summary

### ✅ Bewertung deines Ansatzes: **SEHR GUT**

Dein Ansatz ist **technisch sinnvoll und gut durchdacht**:

1. ✅ **Wort-für-Wort Editing**: Essenziell für die Erhaltung der Zeitstempel-Integrität
2. ✅ **Rollenbeschränkung**: Admin + Editor (nicht User)
3. ✅ **Backup-Mechanismus**: Kritisch für Datensicherheit
4. ✅ **Audit-Log**: Unerlässlich für Nachvollziehbarkeit
5. ✅ **Dedizierte Editor-Seite**: Eigene Übersicht mit File-Management
6. ✅ **Speaker-Editing**: Wichtig für Korrekturen
7. ✅ **Bookmark-Funktion**: Nützlich für längere Sessions

### 🎯 Empfehlung

**Eigene, maßgeschneiderte Lösung** für maximale Kontrolle und Sicherheit.

### 📊 Projekt-Kontext (vereinfacht Implementierung)

- ✅ **Nur 1 Editor aktiv**: Keine Concurrency-Probleme
- ✅ **Max. 10.000 Wörter/File**: Performance unkritisch
- ✅ **Kleines Team**: Einfacheres Undo-System möglich

---

## 2. Architektur-Überblick

### 2.1 System-Komponenten

```
┌─────────────────────────────────────────────────────────────────┐
│                      NAVIGATION (Navbar)                         │
│  [Inicio] [Proyecto] [Corpus] [Atlas] [Editor] ← NEU            │
│                                           ↑ nur für Admin/Editor │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            EDITOR OVERVIEW PAGE (/editor)                        │
├─────────────────────────────────────────────────────────────────┤
│  Länder-Tabs: [ARG] [BOL] [CHL] [COL] [CRI] [ECU] ...         │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Tabelle: ARG Files                                      │  │
│  ├────────────┬─────────┬─────────┬──────────┬──────────┬───┤  │
│  │ Filename   │ Duración│ Palabras│Last Edit │Last Editor│ Op│  │
│  ├────────────┼─────────┼─────────┼──────────┼──────────┼───┤  │
│  │ Mitre.json │ 2:34:12 │  8,432  │2025-10-20│  editor1 │[E]│  │
│  │ Radio10.j..│ 1:45:30 │  5,234  │unchanged │    -     │[E]│  │
│  └────────────┴─────────┴─────────┴──────────┴──────────┴───┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼ Click [E]dit
┌─────────────────────────────────────────────────────────────────┐
│              JSON EDITOR PAGE (/editor/edit)                     │
├─────────────────────────────────────────────────────────────────┤
│  ← Back to Overview           ARG/2023-08-10_Mitre.json         │
│                                                                  │
│  ┌───────────────────────┐  ┌─────────────────────────────────┐│
│  │  TRANSCRIPT (Edit)    │  │  SIDEBAR                        ││
│  │  =====================│  │  ==================              ││
│  │                       │  │  📋 Metadata                    ││
│  │  [Speaker: lib-pm ✏️] │  │  Country: ARG                   ││
│  │                       │  │  Date: 2023-08-10               ││
│  │  Word Word Word       │  │                                 ││
│  │  ^^^^                 │  │  🎯 Bookmarks                   ││
│  │  Doppelklick → Edit   │  │  [+] Add Bookmark               ││
│  │                       │  │  • Segment 5, 00:12:34          ││
│  │  [🔖] Bookmark here   │  │  • Segment 20, 00:45:12         ││
│  │                       │  │                                 ││
│  │                       │  │  ↩️ Undo History                ││
│  │                       │  │  [Undo] Last 5-15 actions       ││
│  │                       │  │  • Changed "hola" → "Hola" ↩️   ││
│  │                       │  │  • Speaker spk1 → lib-pm ↩️     ││
│  └───────────────────────┘  │                                 ││
│                              │  💾 Export                      ││
│  [Audio Player Controls]     │  [JSON] [TXT] [MP3]            ││
│                              └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Datenfluss

```
User (Admin/Editor)
  │
  ├─→ /editor (Overview)
  │   ├─→ Lädt: File-Liste aus Filesystem
  │   ├─→ Lädt: Duración/Palabras aus stats_all.db
  │   └─→ Lädt: Edit-History aus edit_log.jsonl
  │
  └─→ /editor/edit?file=ARG/xxx.json
      ├─→ Lädt: JSON-Datei
      ├─→ Lädt: Audio-Datei
      ├─→ Initialisiert: Editor-Module
      │   ├─ WordEditor (Inline-Edit)
      │   ├─ SpeakerEditor (Speaker-Name-Edit)
      │   ├─ BookmarkManager
      │   └─ UndoManager (Session-based)
      │
      └─→ User-Aktion: Edit Word
          ├─→ Frontend: Input-Validation
          ├─→ Backend: POST /api/transcript/update-word
          │   ├─ Backup erstellen
          │   ├─ JSON updaten
          │   ├─ Log schreiben
          │   └─ Undo-Stack speichern (Session)
          └─→ Frontend: UI-Update + Undo-Button
```

---

## 3. Komponenten-Details

### 3.1 Navigation (Navbar-Erweiterung)

**Datei:** `templates/partials/_navbar.html`

**Änderung:** Neuen Link "Editor" einfügen (nur für Admin/Editor sichtbar)

```jinja2
{% set nav_links = [
  {
    'label': 'Inicio',
    'href': url_for('public.landing_page'),
    'match': ['public.landing_page']
  },
  {
    'label': 'Proyecto',
    'href': url_for('public.proyecto_overview'),
    'match': ['public.proyecto_overview', 'public.proyecto_page'],
    'children': [...]
  },
  {
    'label': 'Corpus',
    'href': url_for('corpus.corpus_home'),
    'match': ['corpus.corpus_home', 'corpus.search']
  },
  {
    'label': 'Atlas',
    'href': url_for('public.atlas_page'),
    'match': ['public.atlas_page']
  },
  {# NEU: Editor-Link (nur für Admin + Editor) #}
  {% if is_authenticated and role_value in ['admin', 'editor'] %}
  {
    'label': 'Editor',
    'href': url_for('editor.overview'),
    'match': ['editor.overview', 'editor.edit_file'],
    'role_required': ['admin', 'editor']  # Dokumentation
  }
  {% endif %}
] %}
```

### 3.2 Editor Overview Page

**Route:** `src/app/routes/editor.py`

```python
"""Editor overview and management routes."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from flask import Blueprint, abort, g, render_template
from flask_jwt_extended import jwt_required

from ..auth import Role
from ..auth.decorators import require_role
from ..services.database import open_db

blueprint = Blueprint("editor", __name__, url_prefix="/editor")

MEDIA_DIR = Path(__file__).resolve().parents[3] / "media"
TRANSCRIPTS_DIR = MEDIA_DIR / "transcripts"
EDIT_LOG_FILE = MEDIA_DIR / "transcripts" / "edit_log.jsonl"


@blueprint.get("/")
@jwt_required()
@require_role(Role.EDITOR)
def overview():
    """
    Editor overview page: Liste aller Transcript-Files mit Metadata.
    
    Zeigt pro Land:
    - Filename
    - Duración (aus stats_all.db)
    - Palabras (aus stats_all.db)
    - Last Edited (aus edit_log.jsonl)
    - Last Editor (aus edit_log.jsonl)
    - Edit-Button
    """
    # 1. Lade alle JSON-Files aus media/transcripts/
    countries = ["ARG", "BOL", "CHL", "COL", "CRI", "ECU", "ESP", 
                 "GTM", "MEX", "PAN", "PER", "PRY", "URY", "USA", "VEN"]
    
    files_by_country = {}
    
    for country in countries:
        country_dir = TRANSCRIPTS_DIR / country
        if not country_dir.exists():
            continue
        
        files = []
        for json_file in sorted(country_dir.glob("*.json")):
            file_info = _get_file_info(country, json_file.name)
            files.append(file_info)
        
        if files:
            files_by_country[country] = files
    
    return render_template(
        "pages/editor_overview.html",
        files_by_country=files_by_country,
        countries=countries
    )


def _get_file_info(country: str, filename: str) -> dict:
    """
    Sammelt alle Metadaten für ein Transcript-File.
    
    Returns:
        {
            'country': 'ARG',
            'filename': '2023-08-10_ARG_Mitre.json',
            'duration': '02:34:12',
            'word_count': 8432,
            'last_edited': '2025-10-20 14:32:15' or None,
            'last_editor': 'editor_test' or None
        }
    """
    # Extrahiere basename ohne Extension für DB-Lookup
    mp3_filename = filename.replace(".json", ".mp3")
    
    # 2. Hole Duración und Palabras aus stats_all.db
    duration = None
    word_count = None
    
    try:
        with open_db("stats_all") as conn:
            cursor = conn.execute(
                "SELECT duracion_formateada, palabras FROM files WHERE nombre_archivo = ? AND pais = ?",
                (mp3_filename, country)
            )
            row = cursor.fetchone()
            if row:
                duration = row["duracion_formateada"]
                word_count = row["palabras"]
    except Exception as e:
        print(f"[Editor] Error loading stats for {filename}: {e}")
    
    # 3. Hole Last Edited aus edit_log.jsonl
    last_edited = None
    last_editor = None
    
    if EDIT_LOG_FILE.exists():
        try:
            # Lies Log rückwärts und finde letzten Eintrag für dieses File
            with EDIT_LOG_FILE.open("r", encoding="utf-8") as log:
                lines = log.readlines()
            
            for line in reversed(lines):
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get("file") == f"{country}/{filename}":
                    last_edited = entry.get("timestamp")
                    last_editor = entry.get("user")
                    break
        except Exception as e:
            print(f"[Editor] Error reading edit log: {e}")
    
    return {
        "country": country,
        "filename": filename,
        "duration": duration or "N/A",
        "word_count": word_count or 0,
        "last_edited": last_edited,
        "last_editor": last_editor
    }


@blueprint.get("/edit")
@jwt_required()
@require_role(Role.EDITOR)
def edit_file():
    """
    JSON Editor page (erweiterte Player-Seite).
    
    Query-Parameter:
    - file: Relativer Pfad, z.B. "ARG/2023-08-10_ARG_Mitre.json"
    """
    from flask import request
    
    file_path = request.args.get("file")
    if not file_path:
        abort(400, "Missing 'file' parameter")
    
    # Security: Path traversal prevention
    if ".." in file_path or file_path.startswith("/"):
        abort(400, "Invalid file path")
    
    # Verify file exists
    full_path = TRANSCRIPTS_DIR / file_path
    if not full_path.exists() or not full_path.is_file():
        abort(404, "File not found")
    
    # Extrahiere Audio-Pfad
    country = file_path.split("/")[0]
    mp3_filename = full_path.stem + ".mp3"
    audio_path = f"{country}/{mp3_filename}"
    
    return render_template(
        "pages/editor_edit.html",
        transcript_file=file_path,
        audio_file=audio_path,
        country=country,
        filename=full_path.name
    )
```

**Template:** `templates/pages/editor_overview.html`

```jinja2
{% extends "base.html" %}

{% block page_title %}Editor - CO.RA.PAN{% endblock %}

{% block extra_head %}
<style>
  .editor-overview {
    max-width: 1400px;
    margin: 2rem auto;
    padding: 0 1rem;
  }
  
  .country-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
  }
  
  .country-tab {
    padding: 0.5rem 1rem;
    border: 2px solid #ddd;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .country-tab:hover {
    background: #f0f0f0;
  }
  
  .country-tab.active {
    background: #667eea;
    color: white;
    border-color: #667eea;
  }
  
  .files-table {
    width: 100%;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    display: none;
  }
  
  .files-table.active {
    display: table;
  }
  
  .files-table th {
    background: #f8f9fa;
    padding: 1rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #dee2e6;
  }
  
  .files-table td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #e9ecef;
  }
  
  .files-table tr:hover {
    background: #f8f9fa;
  }
  
  .edit-btn {
    padding: 0.5rem 1rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
  }
  
  .edit-btn:hover {
    background: #5568d3;
  }
  
  .status-unchanged {
    color: #6c757d;
    font-style: italic;
  }
  
  .status-edited {
    color: #28a745;
  }
</style>
{% endblock %}

{% block content %}
<div class="editor-overview">
  <h1>Editor de Transcripciones</h1>
  <p class="subtitle">Gestionar y editar archivos JSON del corpus</p>
  
  <!-- Country Tabs -->
  <div class="country-tabs">
    {% for country in files_by_country.keys() %}
      <button class="country-tab {{ 'active' if loop.first else '' }}" 
              data-country="{{ country }}">
        {{ country }}
      </button>
    {% endfor %}
  </div>
  
  <!-- Files Tables (one per country) -->
  {% for country, files in files_by_country.items() %}
    <table class="files-table {{ 'active' if loop.first else '' }}" 
           data-country="{{ country }}">
      <thead>
        <tr>
          <th>Filename</th>
          <th>Duración</th>
          <th>Palabras</th>
          <th>Last Edited</th>
          <th>Last Editor</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        {% for file in files %}
          <tr>
            <td><strong>{{ file.filename }}</strong></td>
            <td>{{ file.duration }}</td>
            <td>{{ "{:,}".format(file.word_count) }}</td>
            <td>
              {% if file.last_edited %}
                <span class="status-edited">{{ file.last_edited[:19] }}</span>
              {% else %}
                <span class="status-unchanged">unchanged</span>
              {% endif %}
            </td>
            <td>
              {% if file.last_editor %}
                <span class="status-edited">{{ file.last_editor }}</span>
              {% else %}
                <span class="status-unchanged">-</span>
              {% endif %}
            </td>
            <td>
              <a href="{{ url_for('editor.edit_file', file=country + '/' + file.filename) }}" 
                 class="edit-btn">
                <i class="bi bi-pencil-square"></i> Edit
              </a>
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% endfor %}
</div>

<script>
  // Tab-Switching
  document.querySelectorAll('.country-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const country = tab.dataset.country;
      
      // Update active tab
      document.querySelectorAll('.country-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      // Show corresponding table
      document.querySelectorAll('.files-table').forEach(table => {
        table.classList.toggle('active', table.dataset.country === country);
      });
    });
  });
</script>
{% endblock %}
```

---

---

## 4. Editor-Funktionen (JSON Editor Page)

### 4.1 Undo-System (Session-basiert)

**Konzept:**
- Speichert die letzten **5-15 Aktionen** in der **Session** (nicht persistent)
- Bei Undo: Stellt vorherigen Zustand wieder her + erstellt Backup
- Einfach, weil nur 1 Editor gleichzeitig arbeitet

**Implementation: UndoManager**

```javascript
/**
 * UndoManager - Session-based undo for editor actions
 * @module player/undo-manager
 */

export default class UndoManager {
  constructor(maxHistory = 15) {
    this.maxHistory = maxHistory;
    this.history = [];  // [{type, data, timestamp}]
    this.currentIndex = -1;
  }

  /**
   * Add action to undo history
   */
  addAction(type, data) {
    // Remove any "redo" history after current position
    this.history = this.history.slice(0, this.currentIndex + 1);
    
    const action = {
      type,  // 'word', 'speaker', 'bookmark'
      data,  // {segmentIdx, wordIdx, oldValue, newValue, ...}
      timestamp: new Date().toISOString()
    };
    
    this.history.push(action);
    this.currentIndex++;
    
    // Limit history size
    if (this.history.length > this.maxHistory) {
      this.history.shift();
      this.currentIndex--;
    }
    
    this._updateUI();
  }

  /**
   * Undo last action
   */
  async undo() {
    if (!this.canUndo()) return;
    
    const action = this.history[this.currentIndex];
    this.currentIndex--;
    
    // Send undo request to backend
    await this._executeUndo(action);
    
    this._updateUI();
  }

  /**
   * Redo action
   */
  async redo() {
    if (!this.canRedo()) return;
    
    this.currentIndex++;
    const action = this.history[this.currentIndex];
    
    // Re-apply action
    await this._executeRedo(action);
    
    this._updateUI();
  }

  canUndo() {
    return this.currentIndex >= 0;
  }

  canRedo() {
    return this.currentIndex < this.history.length - 1;
  }

  /**
   * Execute undo (restore old value)
   */
  async _executeUndo(action) {
    switch (action.type) {
      case 'word':
        await this._undoWord(action.data);
        break;
      case 'speaker_reclassify':
        await this._undoSpeakerReclassify(action.data);
        break;
      // bookmarks sind nur lokal, kein Backend-Call nötig
    }
  }

  async _undoWord(data) {
    const response = await fetch('/api/transcript/update-word', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript_file: data.transcriptFile,
        token_id: data.tokenId,
        segment_index: data.segmentIdx,
        word_index: data.wordIdx,
        old_value: data.newValue,  // Swap!
        new_value: data.oldValue,  // Restore original
        is_undo: true  // Flag für Backend
      })
    });
    
    if (!response.ok) {
      throw new Error('Undo failed');
    }
    
    // Update UI
    const wordElement = document.querySelector(`[data-token-id="${data.tokenId}"]`);
    if (wordElement) {
      wordElement.textContent = data.oldValue;
      wordElement.classList.add('undone');
    }
  }

  async _undoSpeakerReclassify(data) {
    await fetch('/api/transcript/reclassify-segment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        transcript_file: data.transcriptFile,
        segment_index: data.segmentIndex,
        old_spkid: data.newSpkid,  // Swap!
        new_spkid: data.oldSpkid,  // Restore original
        is_undo: true
      })
    });
    
    // Update UI
    const label = document.querySelector(
      `.speaker-label[data-segment-index="${data.segmentIndex}"]`
    );
    if (label) {
      label.dataset.spkid = data.oldSpkid;
      label.textContent = data.oldName;
      label.classList.add('undone');
    }
  }

  /**
   * Update Undo/Redo UI
   */
  _updateUI() {
    const undoBtn = document.getElementById('undoBtn');
    const redoBtn = document.getElementById('redoBtn');
    const historyList = document.getElementById('undoHistory');
    
    if (undoBtn) {
      undoBtn.disabled = !this.canUndo();
    }
    
    if (redoBtn) {
      redoBtn.disabled = !this.canRedo();
    }
    
    // Show history (last 5 actions)
    if (historyList) {
      historyList.innerHTML = '';
      const recent = this.history.slice(-5).reverse();
      
      recent.forEach((action, idx) => {
        const isActive = (this.history.length - 1 - idx) <= this.currentIndex;
        const li = document.createElement('li');
        li.className = `undo-history-item ${isActive ? 'active' : 'inactive'}`;
        li.innerHTML = this._formatAction(action);
        
        if (isActive) {
          li.innerHTML += ` <button class="undo-btn-mini" data-action-idx="${this.history.length - 1 - idx}">↩️</button>`;
        }
        
        historyList.appendChild(li);
      });
    }
  }

  _formatAction(action) {
    switch (action.type) {
      case 'word':
        return `"${action.data.oldValue}" → "${action.data.newValue}"`;
      case 'speaker_reclassify':
        return `Segment ${action.data.segmentIndex}: ${action.data.oldName} → ${action.data.newName}`;
      default:
        return action.type;
    }
  }

  /**
   * Initialize UI event listeners
   */
  init() {
    const undoBtn = document.getElementById('undoBtn');
    const redoBtn = document.getElementById('redoBtn');
    
    if (undoBtn) {
      undoBtn.addEventListener('click', () => this.undo());
    }
    
    if (redoBtn) {
      redoBtn.addEventListener('click', () => this.redo());
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        this.undo();
      } else if (e.ctrlKey && (e.key === 'y' || (e.shiftKey && e.key === 'z'))) {
        e.preventDefault();
        this.redo();
      }
    });
  }
}
```

**Aufwand:** ⭐⭐ (mittel) - Session-basiert ist einfacher als persistentes Undo

---

### 4.2 Speaker Reclassification (Segment-Zuordnung ändern)

**Problem:** Ein Segment ist falsch klassifiziert:
```json
{
  "speakers": [
    {"spkid": "spk1", "name": "lib-pm"},
    {"spkid": "spk2", "name": "lec-pm"},
    {"spkid": "spk3", "name": "lib-pf"}
  ],
  "segments": [
    {
      "speaker": "spk1",  // ← Falsch! Sollte spk2 (lec-pm) sein
      "words": [...]
    },
    {
      "speaker": "spk1",  // ← Korrekt, bleibt spk1
      "words": [...]
    }
  ]
}
```

**Lösung:** 
1. User ändert Speaker-Label von "lib-pm" → "lec-pm"
2. Backend findet passende `spkid` für "lec-pm" (= spk2)
3. Segment wird von `spk1` → `spk2` reclassified
4. **Nur dieses eine Segment** wird geändert, alle anderen bleiben

**Frontend: SpeakerEditor**

```javascript
/**
 * SpeakerEditor - Reclassify segments to correct speakers
 * @module player/speaker-editor
 */

export default class SpeakerEditor {
  constructor(transcriptionData, undoManager) {
    this.data = transcriptionData;
    this.undoManager = undoManager;
    this.speakerMap = new Map();      // spkid → name
    this.nameToSpkidMap = new Map();  // name → spkid (für Lookup)
  }

  init() {
    // Build bidirectional maps
    this.data.speakers.forEach(speaker => {
      this.speakerMap.set(speaker.spkid, speaker.name);
      this.nameToSpkidMap.set(speaker.name, speaker.spkid);
    });
    
    // Make speaker labels editable
    this._makeLabelsEditable();
    
    // Show available speakers (optional: Dropdown)
    this._prepareDropdown();
  }

  _makeLabelsEditable() {
    document.querySelectorAll('.speaker-label').forEach(label => {
      label.addEventListener('dblclick', (e) => {
        this._startReclassify(e.target);
      });
      
      // Add edit icon
      const icon = document.createElement('i');
      icon.className = 'bi bi-pencil speaker-edit-icon';
      icon.title = 'Doppelklick zum Reclassify';
      label.appendChild(icon);
    });
  }

  _prepareDropdown() {
    // Liste aller verfügbaren Speaker-Namen für Autocomplete/Dropdown
    this.availableSpeakers = Array.from(this.nameToSpkidMap.keys()).sort();
  }

  _startReclassify(labelElement) {
    const currentSpkid = labelElement.dataset.spkid;
    const segmentIndex = labelElement.dataset.segmentIndex;
    const currentName = this.speakerMap.get(currentSpkid);
    
    // Option 1: Dropdown mit allen Speakern
    const select = document.createElement('select');
    select.className = 'speaker-reclassify-select';
    
    this.availableSpeakers.forEach(name => {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = name;
      option.selected = (name === currentName);
      select.appendChild(option);
    });
    
    // Option 2: Freitext (falls neuer Speaker)
    // const input = document.createElement('input');
    // input.type = 'text';
    // input.value = currentName;
    // input.list = 'speaker-datalist';
    
    labelElement.innerHTML = '';
    labelElement.appendChild(select);
    select.focus();
    
    // Save on change/blur
    const save = async () => {
      const newName = select.value.trim();
      
      if (newName && newName !== currentName) {
        await this._reclassifySegment(
          segmentIndex, 
          currentSpkid, 
          currentName, 
          newName
        );
      } else {
        // Restore
        labelElement.textContent = currentName;
        this._addEditIcon(labelElement);
      }
    };
    
    select.addEventListener('blur', save);
    select.addEventListener('change', save);
    select.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') save();
      if (e.key === 'Escape') {
        labelElement.textContent = currentName;
        this._addEditIcon(labelElement);
      }
    });
  }

  async _reclassifySegment(segmentIndex, oldSpkid, oldName, newName) {
    const transcriptFile = new URLSearchParams(window.location.search).get('file');
    
    // Find target spkid for new name
    const newSpkid = this.nameToSpkidMap.get(newName);
    
    if (!newSpkid) {
      alert(`Speaker "${newName}" nicht gefunden. Bitte aus Liste wählen.`);
      return;
    }
    
    try {
      const response = await fetch('/api/transcript/reclassify-segment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript_file: transcriptFile,
          segment_index: segmentIndex,
          old_spkid: oldSpkid,
          new_spkid: newSpkid
        })
      });
      
      if (!response.ok) throw new Error('Reclassification failed');
      
      // Update UI: nur dieses eine Label
      const label = document.querySelector(
        `.speaker-label[data-segment-index="${segmentIndex}"]`
      );
      if (label) {
        label.dataset.spkid = newSpkid;
        label.textContent = newName;
        this._addEditIcon(label);
        label.classList.add('reclassified');
      }
      
      // Add to undo history
      this.undoManager.addAction('speaker_reclassify', {
        transcriptFile,
        segmentIndex,
        oldSpkid,
        newSpkid,
        oldName,
        newName
      });
      
      this._showFeedback('success', `Segment reclassified: ${oldName} → ${newName}`);
      
    } catch (error) {
      console.error('[SpeakerEditor] Reclassification failed:', error);
      this._showFeedback('error', `Error: ${error.message}`);
    }
  }

  _addEditIcon(labelElement) {
    const icon = document.createElement('i');
    icon.className = 'bi bi-pencil speaker-edit-icon';
    icon.title = 'Doppelklick zum Reclassify';
    labelElement.appendChild(icon);
  }

  _showFeedback(type, message) {
    const event = new CustomEvent('editor-feedback', {
      detail: { type, message }
    });
    document.dispatchEvent(event);
  }
}
```

**Backend Route:**

```python
@blueprint.post("/reclassify-segment")
@jwt_required()
@require_role(Role.EDITOR)
def reclassify_segment():
    """
    Reclassify a single segment to a different speaker.
    Changes the segment's spkid, not the speaker definitions.
    
    Payload:
    {
        "transcript_file": "ARG/xxx.json",
        "segment_index": 0,
        "old_spkid": "spk1",
        "new_spkid": "spk2"
    }
    """
    data = request.get_json()
    transcript_file = data.get("transcript_file")
    segment_index = data.get("segment_index")
    old_spkid = data.get("old_spkid")
    new_spkid = data.get("new_spkid")
    
    if not all([transcript_file, old_spkid, new_spkid]) or segment_index is None:
        abort(400, "Missing required fields")
    
    # Security
    if ".." in transcript_file or transcript_file.startswith("/"):
        abort(400, "Invalid path")
    
    json_path = TRANSCRIPTS_DIR / transcript_file
    if not json_path.exists():
        abort(404, "File not found")
    
    # Load JSON
    with json_path.open("r", encoding="utf-8") as f:
        data_json = json.load(f)
    
    # Validate segment index
    if segment_index >= len(data_json.get("segments", [])):
        abort(400, "Invalid segment index")
    
    segment = data_json["segments"][segment_index]
    
    # Verify current spkid matches
    if segment.get("speaker") != old_spkid:
        abort(409, f"Segment speaker mismatch. Expected {old_spkid}, found {segment.get('speaker')}")
    
    # Verify new_spkid exists in speakers list
    valid_spkids = [s["spkid"] for s in data_json.get("speakers", [])]
    if new_spkid not in valid_spkids:
        abort(400, f"Invalid new_spkid: {new_spkid}")
    
    # Reclassify segment
    segment["speaker"] = new_spkid
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{json_path.stem}_backup_{timestamp}.json"
    backup_path = BACKUP_DIR / backup_filename
    shutil.copy2(json_path, backup_path)
    
    # Save
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data_json, f, ensure_ascii=False, indent=2)
    
    # Get speaker names for logging
    old_name = next((s["name"] for s in data_json["speakers"] if s["spkid"] == old_spkid), old_spkid)
    new_name = next((s["name"] for s in data_json["speakers"] if s["spkid"] == new_spkid), new_spkid)
    
    # Log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": g.user,
        "role": g.role.value,
        "file": transcript_file,
        "action": "reclassify_segment",
        "segment_index": segment_index,
        "old_spkid": old_spkid,
        "new_spkid": new_spkid,
        "old_name": old_name,
        "new_name": new_name,
        "backup_file": str(backup_path.relative_to(MEDIA_DIR))
    }
    
    with EDIT_LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    return jsonify({"success": True, "new_name": new_name})
```

---

### 4.3 Bookmark-System

**Konzept:**
- Nutzer kann während Editing Bookmarks setzen
- Bookmarks speichern: Segment-Index + Timestamp + optional Notiz
- Gespeichert in **localStorage** (persönlich, pro Browser)
- Alternative: Session-Storage (verloren nach Tab-Close)

**Frontend: BookmarkManager**

```javascript
/**
 * BookmarkManager - Save editing positions
 * @module player/bookmark-manager
 */

export default class BookmarkManager {
  constructor(transcriptFile) {
    this.transcriptFile = transcriptFile;
    this.bookmarks = [];
    this.storageKey = `corapan_bookmarks_${transcriptFile.replace(/\//g, '_')}`;
  }

  init() {
    this._loadBookmarks();
    this._setupUI();
  }

  _loadBookmarks() {
    const stored = localStorage.getItem(this.storageKey);
    this.bookmarks = stored ? JSON.parse(stored) : [];
  }

  _saveBookmarks() {
    localStorage.setItem(this.storageKey, JSON.stringify(this.bookmarks));
  }

  addBookmark(segmentIndex, timestamp, note = '') {
    const bookmark = {
      id: Date.now(),
      segmentIndex,
      timestamp,
      note,
      created: new Date().toISOString()
    };
    
    this.bookmarks.push(bookmark);
    this._saveBookmarks();
    this._updateUI();
  }

  removeBookmark(id) {
    this.bookmarks = this.bookmarks.filter(b => b.id !== id);
    this._saveBookmarks();
    this._updateUI();
  }

  jumpToBookmark(segmentIndex, timestamp) {
    // Scroll to segment
    const segmentElement = document.querySelector(`[data-segment-index="${segmentIndex}"]`);
    if (segmentElement) {
      segmentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    // Jump audio
    if (window.audioPlayer) {
      window.audioPlayer.seekTo(timestamp);
    }
  }

  _setupUI() {
    const addBtn = document.getElementById('addBookmarkBtn');
    const listContainer = document.getElementById('bookmarkList');
    
    if (addBtn) {
      addBtn.addEventListener('click', () => {
        const currentTime = window.audioPlayer?.getCurrentTime() || 0;
        const currentSegment = this._getCurrentSegmentIndex();
        const note = prompt('Notiz (optional):');
        
        this.addBookmark(currentSegment, currentTime, note || '');
      });
    }
    
    this._updateUI();
  }

  _updateUI() {
    const listContainer = document.getElementById('bookmarkList');
    if (!listContainer) return;
    
    listContainer.innerHTML = '';
    
    this.bookmarks.forEach(bookmark => {
      const item = document.createElement('div');
      item.className = 'bookmark-item';
      item.innerHTML = `
        <div class="bookmark-info">
          <strong>Segment ${bookmark.segmentIndex}</strong>
          <span>${this._formatTime(bookmark.timestamp)}</span>
          ${bookmark.note ? `<p class="bookmark-note">${bookmark.note}</p>` : ''}
        </div>
        <div class="bookmark-actions">
          <button class="btn-bookmark-jump" data-id="${bookmark.id}">
            <i class="bi bi-play-circle"></i>
          </button>
          <button class="btn-bookmark-delete" data-id="${bookmark.id}">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      `;
      
      // Jump
      item.querySelector('.btn-bookmark-jump').addEventListener('click', () => {
        this.jumpToBookmark(bookmark.segmentIndex, bookmark.timestamp);
      });
      
      // Delete
      item.querySelector('.btn-bookmark-delete').addEventListener('click', () => {
        if (confirm('Bookmark löschen?')) {
          this.removeBookmark(bookmark.id);
        }
      });
      
      listContainer.appendChild(item);
    });
  }

  _getCurrentSegmentIndex() {
    // Find currently visible segment
    const segments = document.querySelectorAll('[data-segment-index]');
    for (const segment of segments) {
      const rect = segment.getBoundingClientRect();
      if (rect.top >= 0 && rect.top < window.innerHeight / 2) {
        return parseInt(segment.dataset.segmentIndex);
      }
    }
    return 0;
  }

  _formatTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
}
```

**Aufwand:** ⭐ (niedrig) - localStorage ist simpel

---

---

## 5. Template: Editor Edit Page

**Datei:** `templates/pages/editor_edit.html`

```jinja2
{% extends "base.html" %}

{% block page_title %}Editor - {{ filename }} - CO.RA.PAN{% endblock %}

{% block extra_head %}
<!-- Editor modules -->
<script type="module" src="{{ url_for('static', filename='js/editor/editor-main.js') }}"></script>
<link rel="stylesheet" href="{{ url_for('static', filename='css/editor.css') }}">

<!-- Pass data to JavaScript -->
<script>
  window.USER_ROLE = "{{ g.role.value if g.role else 'guest' }}";
  window.TRANSCRIPT_FILE = "{{ transcript_file }}";
  window.AUDIO_FILE = "{{ audio_file }}";
</script>
{% endblock %}

{% block content %}
<div class="editor-page">
  <!-- Header -->
  <div class="editor-header">
    <a href="{{ url_for('editor.overview') }}" class="back-link">
      <i class="bi bi-chevron-left"></i> Volver al Overview
    </a>
    <h1 class="editor-title">
      <i class="bi bi-pencil-square"></i> {{ country }}/{{ filename }}
    </h1>
    <div class="editor-status" id="editorStatus">
      <span class="status-indicator"></span>
      <span class="status-text">Listo</span>
    </div>
  </div>

  <!-- Main Editor Container -->
  <div class="editor-container">
    <!-- Left: Transcript -->
    <div class="editor-transcript">
      <div id="transcriptionContainer"></div>
    </div>

    <!-- Right: Sidebar -->
    <aside class="editor-sidebar">
      <!-- Undo/Redo -->
      <div class="sidebar-section">
        <h5 class="sidebar-title">
          <i class="bi bi-arrow-counterclockwise"></i> Deshacer/Rehacer
        </h5>
        <div class="undo-controls">
          <button id="undoBtn" class="btn-undo" disabled>
            <i class="bi bi-arrow-counterclockwise"></i> Deshacer (Ctrl+Z)
          </button>
          <button id="redoBtn" class="btn-redo" disabled>
            <i class="bi bi-arrow-clockwise"></i> Rehacer (Ctrl+Y)
          </button>
        </div>
        <ul id="undoHistory" class="undo-history"></ul>
      </div>

      <!-- Bookmarks -->
      <div class="sidebar-section">
        <h5 class="sidebar-title">
          <i class="bi bi-bookmark"></i> Marcadores
        </h5>
        <button id="addBookmarkBtn" class="btn-primary">
          <i class="bi bi-bookmark-plus"></i> Agregar marcador
        </button>
        <div id="bookmarkList" class="bookmark-list"></div>
      </div>

      <!-- Metadata -->
      <div class="sidebar-section">
        <h5 class="sidebar-title">Metadatos</h5>
        <p class="sidebar-meta" id="countryInfo"></p>
        <p class="sidebar-meta" id="cityInfo"></p>
        <p class="sidebar-meta" id="radioInfo"></p>
        <p class="sidebar-meta" id="dateInfo"></p>
        <p class="sidebar-meta" id="revisionInfo"></p>
      </div>

      <!-- Export -->
      <div class="sidebar-section">
        <h5 class="sidebar-title">Exportar</h5>
        <div class="export-links">
          <a id="downloadMP3" class="download-link" title="Descargar MP3">
            <i class="bi bi-filetype-mp3"></i>
          </a>
          <a id="downloadJSON" class="download-link" title="Descargar JSON">
            <i class="bi bi-filetype-json"></i>
          </a>
          <a id="downloadTXT" class="download-link" title="Descargar TXT">
            <i class="bi bi-filetype-txt"></i>
          </a>
        </div>
      </div>
    </aside>
  </div>

  <!-- Audio Player (floating) -->
  <div class="custom-audio-player">
    <div class="player-controls">
      <div class="player-controls-top">
        <input type="range" id="progressBar" min="0" max="100" value="0" class="progress-bar">
        <div class="volume-control-container">
          <i id="muteBtn" class="fa-solid fa-volume-high volume-icon"></i>
          <input type="range" id="volumeControl" min="0" max="1" step="0.01" value="1.0" class="volume-control">
        </div>
      </div>
      
      <div class="player-controls-bottom">
        <div class="time-display" id="timeDisplay">0:00 / 0:00</div>
        
        <div class="play-container">
          <div class="skip-control" id="rewindBtn">
            <i class="fa-solid fa-rotate-left skip-icon"></i>
            <span class="skip-label">-3s</span>
          </div>
          
          <i id="playPauseBtn" class="bi bi-play-circle-fill play-icon"></i>
          
          <div class="skip-control" id="forwardBtn">
            <i class="fa-solid fa-rotate-right skip-icon"></i>
            <span class="skip-label">+3s</span>
          </div>
        </div>
        
        <div class="speed-control-container">
          <i class="bi bi-speedometer2 speed-icon"></i>
          <input type="range" id="speedControlSlider" min="0.5" max="2" step="0.1" value="1.0" class="speed-control">
          <div id="speedDisplay" class="speed-display">1.0x</div>
        </div>
      </div>
    </div>
  </div>

  <audio id="audioPlayer" preload="auto" style="display: none;"></audio>
</div>
{% endblock %}
```

---

## 6. Implementierungs-Roadmap

### Phase 1: Foundation (2-3 Tage)

**Ziel:** Editor-Navigation + Overview-Seite

- [ ] Navbar-Link "Editor" hinzufügen (nur Admin/Editor)
- [ ] Route `/editor` (Overview) erstellen
- [ ] Template `editor_overview.html` erstellen
- [ ] File-Liste aus Filesystem laden
- [ ] Duración/Palabras aus `stats_all.db` laden
- [ ] Edit-Log aus `edit_log.jsonl` parsen
- [ ] Tabellen mit Tabs implementieren
- [ ] Testing: Zugriffskontrolle (User darf nicht rein)

**Deliverables:**
- Funktionierende Overview-Seite
- Korrekte Daten aus DB + Filesystem

---

### Phase 2: Basic Editor (3-4 Tage)

**Ziel:** Word-Editing + Backend-Integration

- [ ] Route `/editor/edit?file=...` erstellen
- [ ] Template `editor_edit.html` (basiert auf `player.html`)
- [ ] Backend Route `/api/transcript/update-word`
- [ ] Frontend `WordEditor`-Modul
- [ ] Inline-Edit mit Doppelklick
- [ ] Validation (keine HTML, Sonderzeichen-Check)
- [ ] Backup-Erstellung automatisch
- [ ] Edit-Log schreiben (JSONL)
- [ ] Success/Error-Feedback (Toasts)
- [ ] Testing: Edit → Reload → Änderung sichtbar

**Deliverables:**
- Funktionierendes Word-Editing
- Backups + Logs werden erstellt

---

### Phase 3: Undo-System (2-3 Tage)

**Ziel:** Session-basiertes Undo/Redo

- [ ] `UndoManager`-Modul implementieren
- [ ] History-Array (max. 15 Einträge)
- [ ] Undo-Button + Keyboard-Shortcut (Ctrl+Z)
- [ ] Redo-Button + Shortcut (Ctrl+Y)
- [ ] History-Anzeige in Sidebar
- [ ] Backend: `is_undo`-Flag unterstützen
- [ ] Testing: Undo → Redo → Undo

**Deliverables:**
- Funktionierende Undo/Redo-Buttons
- Keyboard-Shortcuts

---

### Phase 4: Speaker Reclassification (1-2 Tage)

**Ziel:** Segmente korrekt zuordnen

- [ ] Backend Route `/api/transcript/reclassify-segment`
- [ ] Frontend `SpeakerEditor`-Modul
- [ ] Dropdown mit allen verfügbaren Speakern
- [ ] Doppelklick auf Speaker-Label
- [ ] Segment-spkid wird geändert (nicht global!)
- [ ] Undo-Integration
- [ ] Testing: Segment reclassify → nur dieses Segment ändert sich

**Deliverables:**
- Speaker-Reclassification funktioniert
- Undo für Reclassification

---

### Phase 5: Bookmarks (1 Tag)

**Ziel:** Lesezeichen für Editing-Positionen

- [ ] `BookmarkManager`-Modul implementieren
- [ ] localStorage für Bookmarks nutzen
- [ ] "Add Bookmark"-Button mit Notiz-Prompt
- [ ] Bookmark-Liste in Sidebar
- [ ] Jump-to-Bookmark-Funktion
- [ ] Delete-Bookmark-Funktion
- [ ] Testing: Bookmark → Reload → noch da?

**Deliverables:**
- Bookmark-System funktioniert
- Persistent über Reloads
- Freitext-Notizen funktionieren

---

### Phase 6: Admin-Dashboard (1-2 Tage)

**Ziel:** Edit-Log-Viewer für Admins

- [ ] Route `/admin/edit-log`
- [ ] Template `admin_edit_log.html`
- [ ] Log-Einträge aus `edit_log.jsonl` laden
- [ ] Tabelle mit Filterung:
  - Nach User
  - Nach Datei
  - Nach Datum
  - Nach Action-Type
- [ ] Detail-View für einzelne Edits
- [ ] Optional: Diff-View (Vorher/Nachher)
- [ ] Export-Funktion (CSV)

**Backend Route:**

```python
@admin_blueprint.get("/edit-log")
@jwt_required()
@require_role(Role.ADMIN)
def edit_log_viewer():
    """
    Admin-only: View edit history.
    
    Query params:
    - user: Filter by username
    - file: Filter by filename
    - date: Filter by date (YYYY-MM-DD)
    - action: Filter by action type
    - limit: Max entries (default: 100)
    """
    from flask import request
    
    filters = {
        'user': request.args.get('user'),
        'file': request.args.get('file'),
        'date': request.args.get('date'),
        'action': request.args.get('action'),
    }
    limit = int(request.args.get('limit', 100))
    
    logs = []
    
    if EDIT_LOG_FILE.exists():
        with EDIT_LOG_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                
                # Apply filters
                if filters['user'] and entry.get('user') != filters['user']:
                    continue
                if filters['file'] and filters['file'] not in entry.get('file', ''):
                    continue
                if filters['date'] and not entry.get('timestamp', '').startswith(filters['date']):
                    continue
                if filters['action'] and entry.get('action') != filters['action']:
                    continue
                
                logs.append(entry)
                
                if len(logs) >= limit:
                    break
    
    # Reverse (newest first)
    logs = list(reversed(logs[-limit:]))
    
    # Get unique values for filter dropdowns
    all_users = set()
    all_files = set()
    all_actions = set()
    
    if EDIT_LOG_FILE.exists():
        with EDIT_LOG_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                all_users.add(entry.get('user', ''))
                all_files.add(entry.get('file', ''))
                all_actions.add(entry.get('action', ''))
    
    return render_template(
        "admin/edit_log.html",
        logs=logs,
        filters=filters,
        all_users=sorted(all_users),
        all_files=sorted(all_files),
        all_actions=sorted(all_actions)
    )
```

**Template:** `templates/admin/edit_log.html`

```jinja2
{% extends "base.html" %}

{% block page_title %}Edit Log - Admin - CO.RA.PAN{% endblock %}

{% block content %}
<div class="admin-edit-log">
  <h1>Edit Log</h1>
  
  <!-- Filters -->
  <form method="get" class="log-filters">
    <select name="user">
      <option value="">All Users</option>
      {% for user in all_users %}
        <option value="{{ user }}" {{ 'selected' if filters.user == user else '' }}>
          {{ user }}
        </option>
      {% endfor %}
    </select>
    
    <select name="file">
      <option value="">All Files</option>
      {% for file in all_files %}
        <option value="{{ file }}" {{ 'selected' if filters.file == file else '' }}>
          {{ file }}
        </option>
      {% endfor %}
    </select>
    
    <select name="action">
      <option value="">All Actions</option>
      {% for action in all_actions %}
        <option value="{{ action }}" {{ 'selected' if filters.action == action else '' }}>
          {{ action }}
        </option>
      {% endfor %}
    </select>
    
    <input type="date" name="date" value="{{ filters.date or '' }}">
    
    <button type="submit">Filter</button>
    <a href="{{ url_for('admin.edit_log_viewer') }}">Reset</a>
  </form>
  
  <!-- Log Table -->
  <table class="log-table">
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>User</th>
        <th>File</th>
        <th>Action</th>
        <th>Details</th>
      </tr>
    </thead>
    <tbody>
      {% for log in logs %}
        <tr>
          <td>{{ log.timestamp[:19] }}</td>
          <td><strong>{{ log.user }}</strong> ({{ log.role }})</td>
          <td><code>{{ log.file }}</code></td>
          <td>
            <span class="action-badge action-{{ log.action }}">
              {{ log.action }}
            </span>
          </td>
          <td>
            {% if log.action == 'update_word' %}
              Token {{ log.token_id }}: "{{ log.old_value }}" → "{{ log.new_value }}"
            {% elif log.action == 'reclassify_segment' %}
              Segment {{ log.segment_index }}: {{ log.old_name }} ({{ log.old_spkid }}) → {{ log.new_name }} ({{ log.new_spkid }})
            {% endif %}
          </td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
  
  <p class="log-info">Showing {{ logs|length }} entries</p>
</div>
{% endblock %}
```

**Deliverables:**
- Admin-Dashboard mit Edit-Log
- Filterung funktioniert
- Export optional

---

### Phase 7: Polish & Testing (2 Tage)

**Ziel:** UX-Verbesserungen + Bug-Fixes

- [ ] CSS-Styling verfeinern
- [ ] Mobile-Responsiveness prüfen
- [ ] Loading-States bei Edits
- [ ] Error-Handling verbessern
- [ ] Edge-Cases testen:
  - Sehr lange Wörter
  - Sonderzeichen
  - Gleichzeitige Tabs (Browser-Test)
- [ ] Dokumentation für Editoren schreiben
- [ ] Admin-Dashboard: Edit-Log-Viewer (optional)

**Deliverables:**
- Polierte, produktionsreife Lösung
- User-Dokumentation

---

## 7. Technische Details

### 7.1 JSON-Struktur (zur Erinnerung)

```json
{
  "filename": "2023-08-10_ARG_Mitre.mp3",
  "country_code": "ARG",
  "city": "Buenos Aires",
  "radio": "Radio Mitre",
  "date": "2023-08-10",
  "revision": "YB",
  "speakers": [
    {"spkid": "spk1", "name": "lib-pm"},
    {"spkid": "spk2", "name": "lib-pf"}
  ],
  "segments": [
    {
      "speaker": "spk1",
      "words": [
        {
          "word": "hola",
          "start": 0.123,
          "end": 0.456,
          "token_id": "abc123",
          "confidence": 0.98
        }
      ]
    }
  ]
}
```

**Editierbar:**
- `word` (Wort-für-Wort, einzeln)
- `segments[].speaker` (Segment-Reclassification, einzeln)

**NICHT editierbar:**
- `start`, `end`, `token_id` (Zeitstempel!)
- `spkid` in `speakers[]` (IDs sind fix)
- `name` in `speakers[]` (Namen sind fix definiert)
- `speakers[]`-Array generell (nur Referenz, keine Änderungen)

---

### 7.2 Datenbank-Schema (stats_all.db)

**Tabelle: `files`**

```sql
CREATE TABLE files (
  id INTEGER PRIMARY KEY,
  pais TEXT,
  nombre_archivo TEXT,
  duracion_formateada TEXT,  -- "02:34:12"
  palabras INTEGER,
  ...
);
```

**Query:**
```sql
SELECT duracion_formateada, palabras 
FROM files 
WHERE nombre_archivo = '2023-08-10_ARG_Mitre.mp3' 
  AND pais = 'ARG'
```

---

### 7.3 Edit-Log-Format (edit_log.jsonl)

**Datei:** `media/transcripts/edit_log.jsonl`

**Format:** JSON Lines (ein JSON-Objekt pro Zeile)

```jsonl
{"timestamp":"2025-10-20T14:32:15","user":"editor_test","role":"editor","file":"ARG/Mitre.json","action":"update_word","token_id":"abc123","segment_index":0,"word_index":5,"old_value":"hola","new_value":"Hola","backup_file":"transcripts/json-backup/Mitre_backup_20251020_143215.json"}
{"timestamp":"2025-10-20T14:35:22","user":"admin","role":"admin","file":"ARG/Mitre.json","action":"update_speaker","spkid":"spk1","old_name":"lib-pm","new_name":"lib-pf","backup_file":"transcripts/json-backup/Mitre_backup_20251020_143522.json"}
```

**Vorteile:**
- Einfach zu appenden (keine JSON-Array-Mutation)
- Einfach rückwärts zu lesen
- Kann mit `tail -n 100` analysiert werden

---

### 7.4 Backup-Strategie

**Verzeichnis:** `media/transcripts/json-backup/`

**Naming:** `{original_stem}_backup_{timestamp}.json`

**Beispiel:** `2023-08-10_ARG_Mitre_backup_20251020_143215.json`

**Rotation:** Optional, später implementieren
```python
def cleanup_old_backups(max_backups_per_file=10):
    """Keeps only last N backups per file."""
    # ... siehe vorheriger Code
```

---

## 8. Sicherheits-Checkliste

### 8.1 Authentifizierung

- [x] JWT-Token erforderlich
- [x] Role-Check: Admin + Editor only
- [x] User wird blockiert

### 8.2 Input-Validation

- [ ] Path-Traversal-Schutz (`..` in Pfaden verbieten)
- [ ] HTML-Tag-Filtering in Wörtern
- [ ] Max. Wortlänge (z.B. 100 Zeichen)
- [ ] Sonderzeichen-Whitelist (je nach Korpus)

### 8.3 Concurrency

- [x] Kein Problem (nur 1 Editor aktiv)
- [x] Optimistic Locking (prüfe `old_value`)

### 8.4 Backup & Recovery

- [x] Automatische Backups bei jedem Edit
- [ ] Restore-Funktion (manuell oder UI)
- [ ] Backup-Rotation (optional)

---

## 9. FAQ

### Q: Wie undo ich einen Edit?

**A:** Zwei Wege:
1. **Undo-Button** in der Session (letzte 5-15 Edits)
2. **Backup-Restore** (manuell, falls Session abgelaufen)

### Q: Was passiert wenn ich den Browser schließe?

**A:** 
- **Undo-History:** Verloren (session-based)
- **Bookmarks:** Bleiben erhalten (localStorage)
- **Edits:** Permanent gespeichert

### Q: Kann ich mehrere Files gleichzeitig offen haben?

**A:** Ja, in verschiedenen Tabs. Jeder Tab hat eigene:
- Undo-History (getrennt)
- Bookmarks (getrennt, pro File)

### Q: Wie finde ich heraus wer was geändert hat?

**A:** Im Edit-Log (`edit_log.jsonl`) oder später im Admin-Dashboard.

### Q: Was wenn ich aus Versehen etwas lösche?

**A:**
1. Undo-Button (falls noch in Session)
2. Backup-Restore (Administrator)

---

## 10. Alternativen & Zukunft

### Kurzfristig (dieses System)

✅ **Perfekt für:**
- Kleine Teams (1-3 Editoren)
- <1000 Files
- Gelegentliche Edits

### Langfristig (bei Skalierung)

**Migration zu Datenbank:**
- PostgreSQL mit JSON-Columns
- Transaktionen & Row-Level-Locking
- Automatisches Rollback
- Multi-User-Editing

**Aufwand:** 3-4 Wochen (großes Refactoring)

**Wann nötig?**
- >10 Editoren gleichzeitig
- >10.000 Files
- Echzeit-Collaboration gewünscht

---

## 11. Zusammenfassung

### ✅ Was wir bauen

1. **Editor-Link** in Navbar (Admin + Editor only)
2. **Overview-Seite** mit File-Liste (Länder-Tabs, Edit-Status)
3. **JSON-Editor-Seite** (erweiterte Player-Seite)
   - Wort-für-Wort Inline-Editing
   - Speaker-Name-Editing
   - Bookmark-System
   - Undo/Redo (5-15 Aktionen)
4. **Backend-Routes**
   - `/api/transcript/update-word`
   - `/api/transcript/update-speaker`
5. **Automatische Backups** + **Edit-Log**

### 📊 Aufwand

| Phase | Aufwand | Kritisch? |
|-------|---------|-----------|
| 1. Foundation (Overview) | 2-3 Tage | ⭐⭐ |
| 2. Basic Editor (Words) | 3-4 Tage | ⭐⭐⭐ |
| 3. Undo-System (10 Aktionen) | 2-3 Tage | ⭐⭐ |
| 4. Speaker-Reclassification | 1-2 Tage | ⭐⭐ |
| 5. Bookmarks (mit Notizen) | 1 Tag | ⭐ |
| 6. Admin-Dashboard | 1-2 Tage | ⭐ |
| 7. Polish & Testing | 2 Tage | ⭐⭐ |
| **TOTAL** | **12-17 Tage** | |

**Realistisch:** 2.5-3.5 Wochen Entwicklung + Testing

---

## 12. Konfiguration (User-Entscheidungen)

### ✅ Festgelegte Werte

- **Undo-History:** 10 Aktionen (Session-basiert)
- **Backup-Rotation:** 10 Backups pro File (älteste werden gelöscht)
- **Admin-Dashboard:** Ja, Edit-Log-Viewer für Admins
- **Bookmark-Notizen:** Ja, Freitext-Notizen bei Bookmarks

### 🔧 Technische Details

**Speaker-Editing:**
- ✅ Korrekt implementiert als **Segment-Reclassification**
- Nur das editierte Segment ändert seine `spkid`
- Andere Segmente mit gleicher `spkid` bleiben unverändert
- `speakers[]`-Array bleibt komplett unverändert

---

## 12. Nächste Schritte

1. ✅ **Plan reviewed** → Feedback einholen
2. [ ] **Phase 1 starten:** Navbar + Overview
3. [ ] **Testing-Environment:** Backup der aktuellen JSONs
4. [ ] **Dokumentation:** Editor-Guidelines schreiben
5. [ ] **Deployment-Plan:** Staging → Production

---

**Bereit für Implementation?** Ich kann die einzelnen Dateien jetzt erstellen! 🚀

| Bibliothek | Warum nicht geeignet |
|------------|---------------------|
| **TinyMCE / CKEditor** | Rich-Text-Editoren; würden HTML-Formatierung einfügen und die JSON-Struktur zerstören |
| **Medium Editor** | Ähnliches Problem; fokussiert auf Absatz-basierte Bearbeitung |
| **Pell / Suneditor** | Zu mächtig; keine Kontrolle über einzelne Wort-Objekte |
| **Draft.js / Slate** | React-Frameworks; Overkill für deine Vanilla-JS-Implementierung |

#### ⚠️ **Teilweise geeignet, aber komplex**

| Bibliothek | Pro | Contra |
|------------|-----|--------|
| **contenteditable API (nativ)** | Standard-Browser-API, keine Dependencies | Muss komplett selbst implementiert werden |
| **editable.js** (livingdocsIO) | Minimalistisch, API-fokussiert | Veraltet (letztes Update vor Jahren) |

### 2.2 Deine JSON-Struktur (Herausforderungen)

```json
{
  "segments": [
    {
      "speaker": "spk1",
      "words": [
        {
          "word": "hola",
          "start": 0.123,
          "end": 0.456,
          "token_id": "abc123",
          "confidence": 0.98
        }
      ]
    }
  ]
}
```

**Kritische Anforderungen:**
1. Nur `"word"` darf editierbar sein
2. `start`, `end`, `token_id` müssen unverändert bleiben
3. Jedes Wort ist ein separates Objekt (nicht zusammenhängender Text)
4. Segment- und Speaker-Struktur muss erhalten bleiben

---

## 3. Empfohlene Implementierung: Custom Inline-Edit

### 3.1 Architektur-Überblick

```
┌─────────────────────────────────────────────────┐
│           Frontend (Player)                      │
├─────────────────────────────────────────────────┤
│  1. User Role Detection (JWT)                   │
│  2. Word Click Handler (Edit Mode)              │
│  3. Inline Input Field                          │
│  4. Validation & Submit                          │
└─────────────────┬───────────────────────────────┘
                  │ POST /api/transcript/update
                  ▼
┌─────────────────────────────────────────────────┐
│           Backend (Flask)                        │
├─────────────────────────────────────────────────┤
│  1. Auth: Require Editor Role                   │
│  2. Validate Word Update (no timestamp change)  │
│  3. Backup Original JSON                         │
│  4. Update JSON File                             │
│  5. Log Change (who, what, when)                │
└─────────────────────────────────────────────────┘
```

### 3.2 Frontend: Minimalistisches Inline-Editing

**Neues Modul:** `static/js/player/modules/editor.js`

```javascript
/**
 * Editor Module - Inline word editing for editors only
 * @module player/editor
 */

export default class EditorManager {
  constructor(transcriptionManager, audioPlayer) {
    this.transcription = transcriptionManager;
    this.audio = audioPlayer;
    this.isEditor = false;
    this.currentEditElement = null;
    this.originalValue = null;
  }

  /**
   * Initialize editor features if user is editor
   */
  init() {
    // Check user role from JWT (bereits im g object verfügbar)
    this.isEditor = this._checkEditorRole();
    
    if (!this.isEditor) {
      console.log('[Editor] User is not editor, inline editing disabled');
      return;
    }

    console.log('[Editor] Inline editing enabled for editor role');
    this._enableEditMode();
  }

  /**
   * Check if current user has editor role
   */
  _checkEditorRole() {
    // Role wird vom Backend im Template verfügbar gemacht
    // Alternativ: JWT-Token clientseitig parsen
    return window.USER_ROLE === 'editor' || window.USER_ROLE === 'admin';
  }

  /**
   * Enable edit mode for all word elements
   */
  _enableEditMode() {
    // Add visual indicator (z.B. Icon in Sidebar)
    this._showEditorIndicator();

    // Attach event listeners to all words
    document.addEventListener('dblclick', (e) => {
      const wordElement = e.target.closest('.word-token');
      if (wordElement && !wordElement.classList.contains('editing')) {
        this._startEdit(wordElement);
      }
    });
  }

  /**
   * Show visual indicator that edit mode is active
   */
  _showEditorIndicator() {
    const sidebar = document.querySelector('.player-sidebar');
    const indicator = document.createElement('div');
    indicator.className = 'editor-mode-indicator';
    indicator.innerHTML = `
      <i class="bi bi-pencil-square"></i>
      <span>Editor-Modus aktiv</span>
      <p class="hint">Doppelklick auf Wort zum Bearbeiten</p>
    `;
    sidebar.insertBefore(indicator, sidebar.firstChild);
  }

  /**
   * Start editing a word
   */
  _startEdit(wordElement) {
    // Prevent multiple edits
    if (this.currentEditElement) {
      this._cancelEdit();
    }

    // Pause audio during editing
    this.audio.pause();

    // Store original value
    this.originalValue = wordElement.textContent.trim();
    this.currentEditElement = wordElement;

    // Get word data
    const tokenId = wordElement.dataset.tokenId;
    const segmentIdx = wordElement.dataset.segmentIndex;
    const wordIdx = wordElement.dataset.wordIndex;

    // Create inline input
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'word-inline-edit';
    input.value = this.originalValue;
    input.dataset.tokenId = tokenId;
    input.dataset.segmentIndex = segmentIdx;
    input.dataset.wordIndex = wordIdx;

    // Replace element with input
    wordElement.classList.add('editing');
    wordElement.innerHTML = '';
    wordElement.appendChild(input);

    // Focus and select
    input.focus();
    input.select();

    // Event handlers
    input.addEventListener('blur', () => this._confirmEdit(input));
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        this._confirmEdit(input);
      } else if (e.key === 'Escape') {
        e.preventDefault();
        this._cancelEdit();
      }
    });
  }

  /**
   * Confirm and save edit
   */
  async _confirmEdit(input) {
    const newValue = input.value.trim();
    
    // No change
    if (newValue === this.originalValue) {
      this._cancelEdit();
      return;
    }

    // Validation
    if (!this._validateWord(newValue)) {
      alert('Ungültiger Wert. Nur Buchstaben, Zahlen und Grundzeichen erlaubt.');
      input.focus();
      return;
    }

    // Show loading state
    input.disabled = true;
    input.classList.add('saving');

    try {
      // Get transcript file from URL
      const urlParams = new URLSearchParams(window.location.search);
      const transcriptFile = urlParams.get('transcription');

      // Send update to backend
      const response = await fetch('/api/transcript/update-word', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // JWT token wird automatisch von Flask-JWT-Extended gehandhabt
        },
        body: JSON.stringify({
          transcript_file: transcriptFile,
          token_id: input.dataset.tokenId,
          segment_index: parseInt(input.dataset.segmentIndex),
          word_index: parseInt(input.dataset.wordIndex),
          old_value: this.originalValue,
          new_value: newValue
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Update fehlgeschlagen');
      }

      // Success: Update UI
      this.currentEditElement.classList.remove('editing');
      this.currentEditElement.textContent = newValue;
      this.currentEditElement.classList.add('edited');
      
      // Show success feedback
      this._showFeedback('success', 'Änderung gespeichert');

      // Reset state
      this.currentEditElement = null;
      this.originalValue = null;

    } catch (error) {
      console.error('[Editor] Update failed:', error);
      this._showFeedback('error', `Fehler: ${error.message}`);
      
      // Restore original value
      this._cancelEdit();
    }
  }

  /**
   * Cancel edit and restore original
   */
  _cancelEdit() {
    if (!this.currentEditElement) return;

    this.currentEditElement.classList.remove('editing');
    this.currentEditElement.textContent = this.originalValue;
    
    this.currentEditElement = null;
    this.originalValue = null;
  }

  /**
   * Validate word content
   */
  _validateWord(word) {
    // Keine leeren Strings
    if (!word || word.length === 0) return false;
    
    // Keine HTML-Tags
    if (/<[^>]*>/g.test(word)) return false;
    
    // Nur erlaubte Zeichen (Buchstaben, Zahlen, Grundzeichen)
    // Anpassen je nach Anforderungen des Korpus
    const allowedPattern = /^[\wáéíóúüñÁÉÍÓÚÜÑ¿?¡!.,;:\-'"]+$/;
    return allowedPattern.test(word);
  }

  /**
   * Show user feedback
   */
  _showFeedback(type, message) {
    const toast = document.createElement('div');
    toast.className = `editor-toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('show');
    }, 10);

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
}
```

### 3.3 Backend: Flask Route mit Sicherheit

**Neue Route:** `src/app/routes/transcript.py`

```python
"""Transcript editing routes (editor-only)."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from flask import Blueprint, abort, g, jsonify, request
from flask_jwt_extended import jwt_required

from ..auth import Role
from ..auth.decorators import require_role

blueprint = Blueprint("transcript", __name__, url_prefix="/api/transcript")

# Paths
MEDIA_DIR = Path(__file__).resolve().parents[3] / "media"
TRANSCRIPTS_DIR = MEDIA_DIR / "transcripts"
BACKUP_DIR = MEDIA_DIR / "transcripts" / "json-backup"
EDIT_LOG_FILE = MEDIA_DIR / "transcripts" / "edit_log.jsonl"

# Ensure directories exist
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


@blueprint.post("/update-word")
@jwt_required()
@require_role(Role.EDITOR)  # Nur Editor und Admin
def update_word():
    """
    Update a single word in a transcript JSON file.
    
    Expects JSON payload:
    {
        "transcript_file": "ARG/2023-08-10_ARG_Mitre.json",
        "token_id": "abc123",
        "segment_index": 0,
        "word_index": 5,
        "old_value": "hola",
        "new_value": "Hola"
    }
    
    Returns:
    {
        "success": true,
        "backup_file": "path/to/backup.json",
        "timestamp": "2025-10-25T12:34:56"
    }
    """
    try:
        # Parse request
        data = request.get_json()
        transcript_file = data.get("transcript_file")
        token_id = data.get("token_id")
        segment_idx = data.get("segment_index")
        word_idx = data.get("word_index")
        old_value = data.get("old_value")
        new_value = data.get("new_value")

        # Validation
        if not all([transcript_file, token_id, old_value, new_value]):
            abort(400, "Missing required fields")

        if segment_idx is None or word_idx is None:
            abort(400, "Missing segment or word index")

        # Security: Prevent path traversal
        if ".." in transcript_file or transcript_file.startswith("/"):
            abort(400, "Invalid transcript file path")

        # Construct file path
        json_path = TRANSCRIPTS_DIR / transcript_file
        
        if not json_path.exists() or not json_path.is_file():
            abort(404, "Transcript file not found")

        # Load JSON
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure
        if "segments" not in data or segment_idx >= len(data["segments"]):
            abort(400, "Invalid segment index")

        segment = data["segments"][segment_idx]
        if "words" not in segment or word_idx >= len(segment["words"]):
            abort(400, "Invalid word index")

        word_obj = segment["words"][word_idx]

        # Verify token_id matches (additional safety check)
        if word_obj.get("token_id") != token_id:
            abort(400, "Token ID mismatch")

        # Verify old value matches (prevent race conditions)
        if word_obj.get("word") != old_value:
            abort(409, f"Word was already changed. Expected '{old_value}', found '{word_obj.get('word')}'")

        # === BACKUP: Create timestamped backup ===
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{json_path.stem}_backup_{timestamp}.json"
        backup_path = BACKUP_DIR / backup_filename

        shutil.copy2(json_path, backup_path)

        # === UPDATE: Modify only the "word" field ===
        word_obj["word"] = new_value

        # Write updated JSON (with proper formatting)
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # === LOGGING: Append to edit log ===
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": g.user,  # From JWT
            "role": g.role.value,
            "file": transcript_file,
            "token_id": token_id,
            "segment_index": segment_idx,
            "word_index": word_idx,
            "old_value": old_value,
            "new_value": new_value,
            "backup_file": str(backup_path.relative_to(MEDIA_DIR))
        }

        with EDIT_LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return jsonify({
            "success": True,
            "backup_file": backup_filename,
            "timestamp": log_entry["timestamp"]
        })

    except Exception as e:
        # Log error
        print(f"[Transcript Update Error] {e}")
        abort(500, str(e))


@blueprint.get("/edit-log")
@jwt_required()
@require_role(Role.EDITOR)
def get_edit_log():
    """
    Retrieve edit log (last 100 entries).
    Only for editors and admins.
    """
    if not EDIT_LOG_FILE.exists():
        return jsonify({"logs": []})

    # Read last 100 lines
    with EDIT_LOG_FILE.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        last_100 = lines[-100:]

    logs = [json.loads(line) for line in last_100 if line.strip()]
    return jsonify({"logs": logs})
```

### 3.4 Integration in Player

**Änderungen in `templates/pages/player.html`:**

```html
{% block extra_head %}
<!-- New modular player -->
<script type="module" src="{{ url_for('static', filename='js/player/player-main.js') }}"></script>

<!-- Pass user role to JavaScript -->
<script>
  window.USER_ROLE = "{{ g.role.value if g.role else 'guest' }}";
</script>
{% endblock %}
```

**Änderungen in `static/js/player/player-main.js`:**

```javascript
import EditorManager from './modules/editor.js';

class PlayerController {
  constructor() {
    // ... existing modules
    this.editor = null;  // NEW
  }

  async init() {
    // ... existing initialization

    // Initialize transcription first
    this.transcription = new TranscriptionManager(
      this.audio,
      this.tokens,
      this.highlighting
    );
    await this.transcription.init(this.transcriptionFile, this.audioFile);

    // NEW: Initialize editor module (only for editors)
    this.editor = new EditorManager(this.transcription, this.audio);
    this.editor.init();

    // ... rest of initialization
  }
}
```

**Änderungen in `src/app/routes/__init__.py`:**

```python
from . import transcript  # NEW

def register_blueprints(app):
    """Register all route blueprints."""
    app.register_blueprint(public.blueprint)
    app.register_blueprint(auth.blueprint)
    app.register_blueprint(player.blueprint)
    app.register_blueprint(corpus.blueprint)
    app.register_blueprint(atlas.blueprint)
    app.register_blueprint(media.blueprint)
    app.register_blueprint(admin.blueprint)
    app.register_blueprint(transcript.blueprint)  # NEW
```

### 3.5 CSS für Inline-Editing

**Neue Datei:** `static/css/editor.css`

```css
/* Editor Mode Indicator */
.editor-mode-indicator {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  animation: slideIn 0.3s ease-out;
}

.editor-mode-indicator i {
  font-size: 1.5rem;
}

.editor-mode-indicator .hint {
  font-size: 0.85rem;
  opacity: 0.9;
  margin: 0.25rem 0 0 0;
}

/* Word in Edit Mode */
.word-token.editing {
  background: #fff3cd;
  border: 2px solid #ffc107;
  border-radius: 4px;
  padding: 0;
  display: inline-block;
}

.word-inline-edit {
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: inherit;
  padding: 2px 4px;
  outline: none;
  width: auto;
  min-width: 50px;
}

.word-inline-edit.saving {
  background: #e9ecef;
  cursor: wait;
}

/* Edited Words (visual indicator) */
.word-token.edited {
  background: #d4edda;
  border-bottom: 2px solid #28a745;
  position: relative;
}

.word-token.edited::after {
  content: '✓';
  position: absolute;
  top: -8px;
  right: -8px;
  background: #28a745;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  animation: fadeInCheck 0.5s ease-out forwards;
}

/* Toast Notifications */
.editor-toast {
  position: fixed;
  bottom: 80px;
  right: 20px;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transform: translateY(100px);
  opacity: 0;
  transition: all 0.3s ease-out;
  z-index: 10000;
}

.editor-toast.show {
  transform: translateY(0);
  opacity: 1;
}

.toast-success {
  background: #28a745;
}

.toast-error {
  background: #dc3545;
}

/* Animations */
@keyframes slideIn {
  from {
    transform: translateX(-20px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes fadeInCheck {
  0% {
    opacity: 0;
    transform: scale(0);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}
```

**In `templates/base.html` einbinden:**

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/editor.css') }}">
```

---

## 4. Sicherheitsmaßnahmen

### 4.1 Authentifizierung & Autorisierung

✅ **Bereits implementiert:**
- JWT-basierte Authentifizierung
- Role-based Access Control (Admin, Editor, User)
- `@require_role(Role.EDITOR)` Decorator

### 4.2 Zusätzliche Sicherheit

```python
# In src/app/routes/transcript.py

# Rate Limiting (optional, via Flask-Limiter)
from flask_limiter import Limiter
limiter = Limiter(key_func=lambda: g.user)

@blueprint.post("/update-word")
@limiter.limit("10 per minute")  # Max 10 edits pro Minute
@jwt_required()
@require_role(Role.EDITOR)
def update_word():
    # ...
```

### 4.3 Backup-Rotation (Speicherplatz-Management)

```python
def cleanup_old_backups(max_backups_per_file=10):
    """Keep only the last N backups per transcript file."""
    import glob
    
    for transcript_file in TRANSCRIPTS_DIR.glob("**/*.json"):
        stem = transcript_file.stem
        backups = sorted(
            BACKUP_DIR.glob(f"{stem}_backup_*.json"),
            key=lambda p: p.stat().st_mtime
        )
        
        # Delete oldest backups if more than max_backups_per_file
        if len(backups) > max_backups_per_file:
            for old_backup in backups[:-max_backups_per_file]:
                old_backup.unlink()
                print(f"Deleted old backup: {old_backup.name}")
```

---

## 5. Testing-Checkliste

### 5.1 Frontend Tests

- [ ] Doppelklick aktiviert Edit-Modus
- [ ] ESC bricht Edit ab ohne zu speichern
- [ ] Enter speichert Änderung
- [ ] Blur (Fokus verlieren) speichert Änderung
- [ ] Validation verhindert ungültige Eingaben
- [ ] Success/Error-Feedback wird angezeigt
- [ ] Edited-Marker erscheint nach erfolgreichem Edit
- [ ] Audio pausiert während Edit

### 5.2 Backend Tests

```python
# tests/test_transcript_editing.py

def test_update_word_as_editor(client, editor_token):
    """Editor kann Wort ändern"""
    response = client.post(
        '/api/transcript/update-word',
        headers={'Authorization': f'Bearer {editor_token}'},
        json={
            'transcript_file': 'ARG/test.json',
            'token_id': 'token_001',
            'segment_index': 0,
            'word_index': 0,
            'old_value': 'hola',
            'new_value': 'Hola'
        }
    )
    assert response.status_code == 200
    assert response.json['success'] is True

def test_update_word_as_user_forbidden(client, user_token):
    """User darf Wort NICHT ändern"""
    response = client.post(
        '/api/transcript/update-word',
        headers={'Authorization': f'Bearer {user_token}'},
        json={...}
    )
    assert response.status_code == 403

def test_backup_created(client, editor_token):
    """Backup wird erstellt"""
    # ... test implementation

def test_log_entry_created(client, editor_token):
    """Log-Eintrag wird erstellt"""
    # ... test implementation
```

---

## 6. Roadmap

### Phase 1: MVP (2-3 Tage)
- ✅ Backend Route mit Backup & Logging
- ✅ Frontend: Inline-Editing für einzelne Wörter
- ✅ Rolle-Check (nur Editor)

### Phase 2: UX-Verbesserungen (1-2 Tage)
- Keyboard-Navigation (Tab durch Wörter)
- Bulk-Edit-Modus (mehrere Wörter markieren)
- Edit-History in Sidebar anzeigen

### Phase 3: Admin-Tools (1-2 Tage)
- Edit-Log-Viewer im Admin-Dashboard
- Backup-Restore-Funktion
- Diff-View (Vorher/Nachher-Vergleich)

---

## 7. Kritik & Alternativen

### 7.1 Potenzielle Probleme

1. **Concurrency:** Was passiert, wenn zwei Editoren gleichzeitig dieselbe Datei bearbeiten?
   - **Lösung:** Optimistic Locking (prüfe `old_value` vor Update)
   - **Alternative:** File-Locking-Mechanismus (komplexer)

2. **Performance:** Große JSON-Dateien (200K+ Zeilen) können langsam werden
   - **Lösung:** Lazy Loading im Frontend
   - **Alternative:** JSON in Datenbank migrieren (großer Aufwand)

3. **Undo/Redo:** Keine eingebaute Undo-Funktion
   - **Lösung:** Backups sind das Undo-System
   - **Alternative:** Change-Stack im Frontend (komplex)

### 7.2 Alternative Ansätze

**Ansatz A: Separate Admin-Oberfläche** (NICHT empfohlen)
- Eigene Edit-Seite außerhalb des Players
- ❌ Schlechte UX: kein Kontext, kein Audio-Sync

**Ansatz B: Vollständiger JSON-Editor** (Overkill)
- Monaco Editor oder Ace Editor einbinden
- ❌ Zu mächtig, Risiko von Strukturzerstörung

**Ansatz C: Datenbank-Migration** (Langfristiges Ziel)
- JSON in PostgreSQL/MongoDB migrieren
- ✅ Bessere Concurrency, Transaktionen, Rollback
- ❌ Großer Refactoring-Aufwand

---

## 8. Fazit & Empfehlung

### ✅ Dein Ansatz ist RICHTIG!

**Umsetzen mit:**
1. Custom Inline-Editing (contenteditable + eigene Logik)
2. Backend Route mit stricter Validation
3. Automatische Backups + JSONL-Log
4. Rolle-basierte Zugriffskontrolle

**Zeitaufwand:** 3-5 Tage für MVP + Testing

**Wartbarkeit:** ⭐⭐⭐⭐⭐ (100% unter deiner Kontrolle)

**Skalierbarkeit:** ⭐⭐⭐ (ausreichend für <10 Editor, <1000 Files)

---

## 9. Nächste Schritte

1. **Prototyp testen** mit einem einzelnen JSON-File
2. **Backup-Strategie** mit Team absprechen (max. Backups pro File?)
3. **Undo-Workflow** definieren (wie werden Backups wiederhergestellt?)
4. **Dokumentation** für Editoren schreiben (Editing-Guidelines)

---

**Fragen? Anpassungen?** Dieses Dokument ist als Startpunkt gedacht und kann iterativ verfeinert werden.
