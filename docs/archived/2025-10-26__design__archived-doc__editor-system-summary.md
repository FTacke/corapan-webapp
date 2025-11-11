# Editor System - Schnell-Übersicht

**Stand:** 25. Oktober 2025  
**Vollständige Dokumentation:** → `EDITOR_INLINE_EDITING_PROPOSAL.md`

---

## 🎯 Was wird gebaut?

Ein **vollständiges Editor-System** für Admin + Editor zur Bearbeitung der Transkriptions-JSONs.

---

## 📦 Komponenten

### 1. Navigation
- Neuer Link **"Editor"** in Navbar
- Nur sichtbar für Admin + Editor

### 2. Overview-Seite (`/editor`)
- Länder-Tabs (ARG, BOL, CHL, ...)
- Tabelle pro Land mit:
  - Filename
  - Duración (aus DB)
  - Palabras (aus DB)
  - Last Edited (aus Log)
  - Last Editor (aus Log)
  - [Edit]-Button

### 3. JSON-Editor (`/editor/edit?file=...`)
- Basiert auf Player-Seite
- **Features:**
  - ✏️ Wort-für-Wort Inline-Editing (Doppelklick)
  - 👥 Speaker-Namen bearbeiten
  - 🔖 Bookmarks setzen (localStorage)
  - ↩️ Undo/Redo (5-15 Aktionen, Session)
  - 📋 Audio-Player integriert

### 4. Backend-Routes
- `POST /api/transcript/update-word` (Wort ändern)
- `POST /api/transcript/update-speaker` (Speaker-Name ändern)
- Automatische Backups + Edit-Log

---

## 🔒 Sicherheit

✅ JWT-basierte Authentifizierung  
✅ Role-Check (Admin + Editor only)  
✅ Path-Traversal-Schutz  
✅ Input-Validation (keine HTML-Tags)  
✅ Optimistic Locking (prüft old_value)  

---

## 💾 Datenfluss

```
User (Admin/Editor)
  │
  ├─→ /editor (Overview)
  │   └─→ Lädt Files + DB-Stats + Edit-Log
  │
  └─→ /editor/edit?file=ARG/xxx.json
      ├─→ Inline-Edit Wort
      │   ├─ Frontend: Validation
      │   ├─ Backend: Backup + Update + Log
      │   └─ Undo-Stack speichern
      │
      ├─→ Inline-Edit Speaker
      │   └─ Analog zu Wort
      │
      └─→ Bookmark setzen
          └─ localStorage (lokal)
```

---

## 🗂️ Datei-Struktur

```
src/app/routes/
  └─ editor.py              # Neue Routes

templates/pages/
  ├─ editor_overview.html   # File-Liste
  └─ editor_edit.html       # JSON-Editor

static/js/editor/
  ├─ editor-main.js         # Haupt-Controller
  └─ modules/
      ├─ word-editor.js     # Inline Word-Editing
      ├─ speaker-editor.js  # Speaker-Name-Editing
      ├─ undo-manager.js    # Undo/Redo
      └─ bookmark-manager.js # Bookmarks

static/css/
  └─ editor.css             # Styling

media/transcripts/
  ├─ json-backup/           # Automatische Backups
  └─ edit_log.jsonl         # Änderungs-Log
```

---

## ⏱️ Zeitplan

| Phase | Aufwand | Inhalt |
|-------|---------|--------|
| 1. Foundation | 2-3 Tage | Navbar + Overview |
| 2. Basic Editor | 3-4 Tage | Word-Editing + Backend |
| 3. Undo-System | 2-3 Tage | Undo/Redo + Shortcuts |
| 4. Speaker-Editing | 1-2 Tage | Speaker-Namen ändern |
| 5. Bookmarks | 1 Tag | Lesezeichen-System |
| 6. Polish | 2 Tage | Testing + UX |
| **TOTAL** | **11-15 Tage** | **~2-3 Wochen** |

---

## 💡 Antworten auf deine Fragen

### ✅ Concurrency
**Kein Problem!** Da nur 1 Editor gleichzeitig arbeitet:
- Keine Race-Conditions
- Einfaches Optimistic Locking (prüfe `old_value`)

### ✅ Performance
**Unkritisch!** Max. 10.000 Wörter/File:
- Frontend: Lazy-Loading (wie bisher im Player)
- Backend: Atomische Updates (nur 1 Wort)

### ✅ Undo-Funktion
**Machbar!** Session-basiert (5-15 Aktionen):
- ⭐⭐ Mittlerer Aufwand
- Speichert History in Session (nicht persistent)
- Keyboard-Shortcuts (Ctrl+Z, Ctrl+Y)
- Bei Browser-Close: History weg (Edits bleiben)

**Alternative (aufwendiger):**
- Persistent Undo in Datenbank → 3-4 Tage extra

### ✅ Speaker-Editing
**Lösbar!** Über spkid-Mapping:
- Ändert nur `speakers[].name`, nicht `spkid`
- Alle Referenzen bleiben intakt

### ✅ Bookmarks
**Einfach!** localStorage:
- ⭐ Niedriger Aufwand
- Pro File separat
- Persistent über Reloads

---

## 🚀 Start-Reihenfolge

1. **Navbar-Link** "Editor" einfügen
2. **Overview-Seite** mit File-Liste
3. **Backend-Route** für Word-Update
4. **Inline-Editing** im Frontend
5. **Undo-System** hinzufügen
6. **Speaker + Bookmarks** ergänzen

---

## 📚 Dokumentation

- **Vollständiger Plan:** `EDITOR_INLINE_EDITING_PROPOSAL.md`
- **Code-Beispiele:** Alle Module komplett dokumentiert
- **Testing-Checkliste:** In Proposal enthalten
- **FAQ:** Häufige Fragen beantwortet

---

## ❓ Offene Fragen

1. **Undo-History-Größe:** 5, 10 oder 15 Aktionen?
2. **Backup-Rotation:** Nach wie vielen Backups löschen? (Standard: 10)
3. **Admin-Dashboard:** Edit-Log-Viewer gewünscht? (optional, +1-2 Tage)

---

**Bereit für Implementation?** 🎉

Nächster Schritt: Phase 1 starten (Navbar + Overview)
