# Editor System - Update & Klärungen

**Datum:** 25. Oktober 2025  
**Status:** Ready for Implementation

---

## ✅ User-Entscheidungen (bestätigt)

1. **Undo-History:** 10 Aktionen
2. **Backup-Rotation:** 10 Backups pro File
3. **Admin-Dashboard:** Ja (Edit-Log-Viewer)
4. **Bookmark-Notizen:** Ja (Freitext)

---

## 🔴 WICHTIGE KLÄRUNG: Speaker-Editing

### Problem erkannt & korrigiert

**Mein ursprüngliches (falsches) Verständnis:**
- Speaker-Namen global ändern
- Wenn `spk1` → `lib-pm` heißt, dann Namen in `speakers[]` ändern
- Alle Segmente mit `spk1` zeigen neuen Namen

**Korrektes Verständnis (nach User-Feedback):**
- **Segment-Reclassification**, nicht Name-Editing
- Wenn Segment falsch klassifiziert ist (`lib-pm` statt `lec-pm`)
- Dann `segments[i].speaker` von `spk1` → `spk2` ändern
- `speakers[]`-Array bleibt **komplett unverändert**

---

## 📝 Technische Umsetzung

### Szenario-Beispiel

**Ausgangssituation:**
```json
{
  "speakers": [
    {"spkid": "spk1", "name": "lib-pm"},
    {"spkid": "spk2", "name": "lec-pm"},
    {"spkid": "spk3", "name": "lib-pf"}
  ],
  "segments": [
    {
      "speaker": "spk1",  // ← Falsch! Sollte spk2 sein
      "words": [...]
    },
    {
      "speaker": "spk1",  // ← Korrekt, bleibt spk1
      "words": [...]
    }
  ]
}
```

**User-Aktion:**
1. Doppelklick auf Speaker-Label bei Segment 0 (zeigt "lib-pm")
2. Dropdown öffnet sich mit allen verfügbaren Speakern
3. User wählt "lec-pm"

**Backend-Logik:**
1. Lookup: `"lec-pm"` → `spkid = "spk2"`
2. Update: `segments[0].speaker = "spk2"`
3. Backup + Log
4. Response: `{"success": true, "new_name": "lec-pm"}`

**Resultat:**
```json
{
  "speakers": [
    {"spkid": "spk1", "name": "lib-pm"},  // Unverändert
    {"spkid": "spk2", "name": "lec-pm"},  // Unverändert
    {"spkid": "spk3", "name": "lib-pf"}   // Unverändert
  ],
  "segments": [
    {
      "speaker": "spk2",  // ← Geändert!
      "words": [...]
    },
    {
      "speaker": "spk1",  // ← Unverändert!
      "words": [...]
    }
  ]
}
```

---

## 🔧 Implementation-Details

### Frontend: SpeakerEditor

**Feature:**
- Doppelklick auf Speaker-Label
- **Dropdown** mit allen verfügbaren Speakern (nicht Freitext)
- Bei Auswahl: Backend-Call zum Reclassify
- Nur das eine Label ändert sich

**Wichtig:**
- Maps aufbauen: `spkid → name` UND `name → spkid`
- Dropdown verhindert ungültige Speaker-Namen
- Optional: Freitext-Input mit Autocomplete (falls neuer Speaker)

### Backend: `/api/transcript/reclassify-segment`

**Endpoint:** `POST /api/transcript/reclassify-segment`

**Payload:**
```json
{
  "transcript_file": "ARG/xxx.json",
  "segment_index": 0,
  "old_spkid": "spk1",
  "new_spkid": "spk2"
}
```

**Validierung:**
- Segment existiert?
- Aktueller `spkid` stimmt mit `old_spkid` überein?
- Neuer `spkid` existiert in `speakers[]`?

**Aktion:**
- `segments[segment_index].speaker = new_spkid`
- Backup erstellen
- Log schreiben (mit Namen für Lesbarkeit)

---

## 📊 Edit-Log-Format (aktualisiert)

**Action: `reclassify_segment`**

```jsonl
{
  "timestamp": "2025-10-25T14:32:15",
  "user": "editor_test",
  "role": "editor",
  "file": "ARG/Mitre.json",
  "action": "reclassify_segment",
  "segment_index": 0,
  "old_spkid": "spk1",
  "new_spkid": "spk2",
  "old_name": "lib-pm",
  "new_name": "lec-pm",
  "backup_file": "transcripts/json-backup/Mitre_backup_20251025_143215.json"
}
```

**Vorteile:**
- Speichert `spkid` (technisch korrekt)
- Speichert `name` (für Lesbarkeit)
- Admin kann Log verstehen ohne JSON zu öffnen

---

## ↩️ Undo für Speaker-Reclassification

**Undo-Action:**
```javascript
{
  type: 'speaker_reclassify',
  data: {
    transcriptFile: 'ARG/xxx.json',
    segmentIndex: 0,
    oldSpkid: 'spk1',
    newSpkid: 'spk2',
    oldName: 'lib-pm',
    newName: 'lec-pm'
  }
}
```

**Undo ausführen:**
- Backend-Call mit vertauschten Werten (`old` ↔ `new`)
- UI-Update: Label zurücksetzen
- Neues Backup + Log mit `is_undo: true`

---

## 🎨 UI-Design (Speaker-Reclassification)

**Dropdown-Variante (empfohlen):**
```
┌─────────────────────────────────────┐
│  Segment 0                          │
│  ┌──────────────┐                   │
│  │ lib-pm ▼     │ ← Doppelklick     │
│  └──────────────┘                   │
│                                     │
│  ↓ Öffnet Dropdown                  │
│                                     │
│  ┌──────────────┐                   │
│  │ lib-pm       │ (aktuell)         │
│  │ lec-pm       │ ← User wählt      │
│  │ lib-pf       │                   │
│  │ lib-of       │                   │
│  │ pre-pm       │                   │
│  │ ...          │                   │
│  └──────────────┘                   │
└─────────────────────────────────────┘
```

**Alternative: Freitext mit Autocomplete**
- Für den Fall dass neue Speaker hinzugefügt werden sollen
- Komplexer, aber flexibler

---

## ⚠️ Edge-Cases

### 1. Was wenn Speaker-Name nicht in Liste?

**Problem:** User gibt "lec-pf" ein, aber existiert nicht in `speakers[]`

**Lösung A (Dropdown):**
- Nicht möglich, da nur existierende Speaker wählbar

**Lösung B (Freitext):**
- Validation: Name muss in `speakers[]` existieren
- Error: "Speaker 'lec-pf' nicht gefunden"
- Vorschlag: Ähnliche Namen anzeigen

### 2. Was wenn mehrere `spkid` gleichen Namen haben?

**Problem:** 
```json
{"spkid": "spk1", "name": "lib-pm"}
{"spkid": "spk15", "name": "lib-pm"}
```

**Lösung:**
- Name-to-spkid-Map nimmt **ersten** Treffer
- Oder: Dropdown zeigt `lib-pm (spk1)` und `lib-pm (spk15)`
- Backend prüft ob `new_spkid` valide ist

**Empfehlung:** Dropdown mit `name (spkid)` für Klarheit

---

## 📋 Testing-Checkliste (Speaker-Reclassification)

- [ ] Segment reclassify: spk1 → spk2
- [ ] UI aktualisiert nur dieses eine Label
- [ ] Andere Segmente mit spk1 bleiben unverändert
- [ ] Backup wird erstellt
- [ ] Log-Eintrag ist korrekt
- [ ] Undo funktioniert
- [ ] Invalid spkid wird abgelehnt
- [ ] Segment-Index out of bounds → Fehler
- [ ] Reload-Test: Änderung persistent

---

## 🚀 Implementierungs-Reihenfolge (aktualisiert)

### Phase 4: Speaker-Reclassification (1-2 Tage)

1. **Backend-Route** `/api/transcript/reclassify-segment`
   - Input-Validation
   - spkid-Lookup
   - Segment-Update
   - Backup + Log

2. **Frontend-Modul** `SpeakerEditor`
   - Bidirectional Maps (`spkid ↔ name`)
   - Dropdown mit allen Speakern
   - Doppelklick-Handler
   - Backend-Call
   - UI-Update (nur dieses Label)

3. **Undo-Integration**
   - Action-Type: `speaker_reclassify`
   - Undo-Handler in `UndoManager`
   - UI-Feedback

4. **Testing**
   - Unit-Tests (Backend)
   - Integration-Tests (Frontend)
   - Edge-Cases

---

## ✅ Zusammenfassung

### Was geändert wurde

| Aspekt | Alt (falsch) | Neu (korrekt) |
|--------|--------------|---------------|
| **Funktion** | Speaker-Namen global ändern | Segment-Reclassification |
| **Was ändert sich** | `speakers[].name` | `segments[].speaker` (spkid) |
| **Scope** | Alle Segmente mit spkid | Nur das editierte Segment |
| **UI** | Inline-Input (Freitext) | Dropdown (alle Speaker) |
| **Backend-Route** | `/update-speaker` | `/reclassify-segment` |
| **Undo-Type** | `speaker` | `speaker_reclassify` |

### Was gleich bleibt

- ✅ Automatische Backups
- ✅ Edit-Log (JSONL)
- ✅ Undo-System (10 Aktionen)
- ✅ Rolle-basierte Zugriffskontrolle
- ✅ Zeitstempel bleiben unverändert

---

## 📚 Nächste Schritte

1. ✅ **Plan aktualisiert** (dieses Dokument)
2. [ ] **Review** durch Team
3. [ ] **Phase 1 starten:** Navbar + Overview
4. [ ] **Prototyp testen:** Speaker-Reclassification mit 1 File
5. [ ] **Feedback einholen** nach Phase 4

---

**Dokumentation aktualisiert!** Alle Änderungen sind im Haupt-Plan `EDITOR_INLINE_EDITING_PROPOSAL.md` eingepflegt. 🎉

**Ready for Implementation!** 🚀
