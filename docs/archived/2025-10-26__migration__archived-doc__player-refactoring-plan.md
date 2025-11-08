# Player Refactoring Plan - Audio Fix + MD3 Design + Modularisierung

**Datum**: 16. Oktober 2025  
**Status**: 🔧 In Arbeit  
**Priorität**: 🔴 HOCH (Audio funktioniert nicht)

---

## 🎯 Ziele

1. ✅ **Audio-Abspielfunktionen reparieren**
2. 📦 **Code modularisieren** (IIFE → ES6 Modules)
3. 🎨 **Custom Player MD3-Design** überarbeiten
4. 🧪 **Testability** verbessern
5. 📝 **Wartbarkeit** erhöhen

---

## 🐛 Problem-Diagnose

### **Fehler**:
```
DOMException: The media resource indicated by the src attribute or assigned media provider object was not suitable.
```

### **Root Cause** (Vermutung):
- `visualAudioPlayer.src = audioFile` (Zeile 226)
- `audioFile` kommt von URL-Parameter: `?audio=...`
- Wahrscheinlich **falscher Pfad** oder **MEDIA_ENDPOINT nicht verwendet**
- `MEDIA_ENDPOINT = "/media"` wird definiert, aber nicht genutzt

### **Fix-Strategie**:
1. Audio-Pfad korrekt konstruieren mit `MEDIA_ENDPOINT`
2. Error Handling für fehlende Audio-Dateien
3. Console Logging für Debugging

---

## 📦 Phase 1: Audio-Fix (SOFORT)

### **Änderungen**:

#### `player_script.js` Zeile 226:
```javascript
// ❌ VORHER:
visualAudioPlayer.src = audioFile;

// ✅ NACHHER:
const audioPath = audioFile.startsWith('/') ? audioFile : `${MEDIA_ENDPOINT}/${audioFile}`;
visualAudioPlayer.src = audioPath;
console.log('[Audio] Loading:', audioPath);

visualAudioPlayer.addEventListener('error', (e) => {
  console.error('[Audio] Load failed:', audioPath, e);
  alert(`Audio konnte nicht geladen werden: ${audioPath}`);
});
```

#### Zeile 875-880 (DOMContentLoaded):
```javascript
// ✅ Verbesserte Logging:
console.log('[Player] Transcription File:', transcriptionFile);
console.log('[Player] Audio File:', audioFile);
console.log('[Player] Audio Path:', audioFile.startsWith('/') ? audioFile : `${MEDIA_ENDPOINT}/${audioFile}`);
```

---

## 📦 Phase 2: Modularisierung (NACH Audio-Fix)

### **Neue Struktur**:

```
static/js/modules/player/
├── config.js          # Konstanten (MEDIA_ENDPOINT, etc.)
├── audio.js           # Audio-Player Logik
├── transcription.js   # Transkript-Laden & Rendern
├── highlighting.js    # Wort/Buchstaben-Markierung
├── tokens.js          # Token Collector
├── export.js          # Download-Funktionen
├── tooltips.js        # Tooltip-Verhalten
├── utils.js           # Hilfsfunktionen (pad, formatTime, etc.)
└── index.js           # Haupt-Orchestrierung
```

### **Vorteile**:
- ✅ Separation of Concerns
- ✅ Testbarkeit (Unit Tests möglich)
- ✅ Wartbarkeit (kleinere Dateien)
- ✅ Wiederverwendbarkeit
- ✅ ES6 Modules statt IIFE

---

## 🎨 Phase 3: Custom Player MD3-Design

### **Aktueller Custom Player**:
```html
<div class="custom-audio-player">
  <audio id="visualAudioPlayer"></audio>
  <!-- Controls -->
</div>
```

### **MD3-Design-Prinzipien**:

#### **1. Farbschema**:
- ✅ Primary: `var(--md3-color-primary)` (#0a5981)
- ✅ Surface: `var(--md3-color-surface-container-low)`
- ✅ On-Surface: `var(--md3-color-on-surface)`
- ✅ Inverse: `var(--md3-color-inverse-surface)` für aktive Zustände

#### **2. Komponenten**:
- **Play/Pause Button**: MD3 FAB (Floating Action Button) Style
- **Progress Bar**: MD3 Linear Progress Indicator
- **Volume Slider**: MD3 Slider Component
- **Speed Control**: MD3 Chip mit Dropdown
- **Time Display**: MD3 Body-Medium Typography

#### **3. Spacing & Layout**:
- Padding: `var(--md3-space-4)` (16dp)
- Gap: `var(--md3-space-3)` (12dp)
- Border-Radius: `var(--md3-radius-medium)` (8dp)
- Elevation: `var(--md3-elevation-1)` (Subtle shadow)

#### **4. Interaktionen**:
- Hover: Opacity 0.9 + slight elevation increase
- Active: `var(--md3-color-primary-container)`
- Disabled: Opacity 0.38
- Transitions: `var(--md3-motion-duration-short-4)` (200ms)

---

## 🗓️ Zeitplan

### **Heute (16. Okt 2025)**:
- ✅ Phase 1: Audio-Fix implementieren
- ✅ Testen im Browser
- ✅ Phase 3: Custom Player MD3-Design (CSS-Updates)

### **Diese Woche**:
- 📦 Phase 2: Modularisierung (2-3 Stunden)
- 🧪 Unit Tests schreiben
- 📝 Dokumentation updaten

---

## 📋 Checklist

### **Audio-Fix**:
- [ ] Audio-Pfad mit MEDIA_ENDPOINT konstruieren
- [ ] Error Handling hinzufügen
- [ ] Console Logging verbessern
- [ ] Im Browser testen
- [ ] Verschiedene Audio-Formate testen

### **MD3-Design Custom Player**:
- [ ] Player-Container: Surface + Elevation
- [ ] Play/Pause Button: FAB-Style
- [ ] Progress Bar: MD3 Linear Progress
- [ ] Volume Control: MD3 Slider
- [ ] Speed Control: MD3 Chip
- [ ] Time Display: MD3 Typography
- [ ] Hover/Focus States
- [ ] Transitions

### **Modularisierung** (später):
- [ ] `config.js` erstellen
- [ ] `audio.js` extrahieren
- [ ] `transcription.js` extrahieren
- [ ] `highlighting.js` extrahieren
- [ ] `tokens.js` extrahieren
- [ ] `export.js` extrahieren
- [ ] `tooltips.js` extrahieren
- [ ] `utils.js` extrahieren
- [ ] `index.js` als Orchestrator
- [ ] Import/Export statements
- [ ] Alte player_script.js als _legacy markieren
- [ ] Tests schreiben

---

## 🎨 MD3 Custom Player - Design Mockup

```css
.custom-audio-player {
  background: var(--md3-color-surface-container-low);
  border: 1px solid var(--md3-color-outline-variant);
  border-radius: var(--md3-radius-large);
  padding: var(--md3-space-4);
  box-shadow: var(--md3-elevation-1);
  display: grid;
  gap: var(--md3-space-3);
  grid-template-areas:
    "play   progress  time"
    "volume speed     mute";
  grid-template-columns: auto 1fr auto;
  align-items: center;
}

.play-pause-btn {
  grid-area: play;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--md3-color-primary);
  color: var(--md3-color-on-primary);
  border: none;
  box-shadow: var(--md3-elevation-2);
  transition: all var(--md3-motion-duration-short-4) var(--md3-motion-easing-standard);
}

.play-pause-btn:hover {
  box-shadow: var(--md3-elevation-3);
  transform: scale(1.05);
}

.progress-bar {
  grid-area: progress;
  appearance: none;
  background: var(--md3-color-surface-container-highest);
  height: 4px;
  border-radius: 2px;
}

.progress-bar::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--md3-color-primary);
  box-shadow: var(--md3-elevation-1);
}

.time-display {
  grid-area: time;
  font-size: var(--md3-body-medium);
  color: var(--md3-color-on-surface);
  font-variant-numeric: tabular-nums;
}
```

---

## 📊 Code-Metriken

### **Vorher** (player_script.js):
- Zeilen: 1046
- Funktionen: ~25
- Module: 1 (Monolith)
- Testability: ⚠️ Schwierig
- Maintainability: ⚠️ Mittel

### **Nachher** (geplant):
- Zeilen: ~1100 (mit besserer Struktur)
- Funktionen: ~30
- Module: 9 (Separation of Concerns)
- Testability: ✅ Gut
- Maintainability: ✅ Sehr gut

---

## 🚀 Nächste Schritte

1. **Audio-Fix implementieren** (15 Min)
2. **Testen im Browser** (10 Min)
3. **Custom Player MD3-CSS** (45 Min)
4. **Dokumentation** (15 Min)

**Gesamt Heute**: ~90 Min

**Modularisierung später**: ~3 Stunden (separate Session)

---

## ✅ Erfolgs-Kriterien

- [ ] Audio spielt ab ohne Fehler
- [ ] Player hat elegantes MD3-Design
- [ ] Code ist modular und testbar
- [ ] Alle Features funktionieren wie vorher
- [ ] Performance ist gleich oder besser
- [ ] Browser-Kompatibilität erhalten
