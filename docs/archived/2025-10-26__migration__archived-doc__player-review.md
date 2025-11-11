# Player Review - Funktionen & Design

## Datum: 16. Oktober 2025

---

## ✅ FUNKTIONALITÄTSPRÜFUNG

### 1. Audio-Player Grundfunktionen
**Status: ✅ Vollständig implementiert**

- **Play/Pause**: `playPauseBtn` mit Bootstrap Icons (bi-play-circle-fill / bi-pause-circle-fill)
- **Vor-/Zurückspulen**: ±3 Sekunden mit `rewindBtn` und `forwardBtn`
- **Fortschrittsanzeige**: `progressBar` (Range-Input 0-100)
- **Lautstärkeregelung**: `volumeControl` mit Mute-Button (`muteBtn`)
- **Geschwindigkeitsregelung**: `speedControlSlider` (0.5x - 2.0x)
- **Zeitanzeige**: `timeDisplay` zeigt aktuelle/gesamte Zeit (MM:SS Format)

**Tastenkombinationen:**
- `CTRL + SPACE`: Play/Pause
- `CTRL + ,`: -3 Sekunden
- `CTRL + .`: +3 Sekunden
- `Click`: Einzelnes Wort abspielen
- `CTRL + Click`: Ab Wort abspielen

### 2. Buchstabenmarkierung (Letter Highlighting)
**Status: ✅ Vollständig implementiert**

**Funktion: `markLetters()` (Zeile 651-697)**
- Markiert Buchstaben/Sequenzen im Transkript
- Drei Modi:
  - **Exact**: Normale Buchstabensuche
  - **Separator** (`_`): Nur am Wortende (vor Leerzeichen)
  - **Punctuation** (`#`): Nur vor Satzzeichen (.,;!?)

**Funktion: `markWordLetters()` (Zeile 699-730)**
- Wendet `<span class="highlight">` auf gefundene Matches an
- Regex-basierte Suche, ignoriert bereits vorhandenes HTML
- Zählt Matches pro Suchbegriff

**Reset-Funktionalität:**
- `resetMarkings()`: Entfernt alle Markierungen
- `resetMarkingByLetters()`: Entfernt spezifische Markierung
- Individuelle Reset-Buttons mit Match-Count-Anzeige

**CSS-Klassen:**
- `.highlight`: rgba(255, 215, 0, 0.5) - Gelbe Markierung mit 600 font-weight

### 3. Wort-Highlighting während Wiedergabe
**Status: ✅ Optimiert mit requestAnimationFrame**

**Funktion: `updateWordsHighlight()` (Zeile 970-1017)**
- Nutzt `requestAnimationFrame` für flüssige Animation
- Markiert aktives Wort mit `.playing` Klasse
- Preview-Effekt für Wörter in derselben Gruppe (`.playing-preview`)
- Verzögerte Entmarkierung (DEACTIVATE_DELAY: 0.35s) für flüssigeren Übergang
- Auto-Scroll zum aktuell gesprochenen Wort

**CSS-Klassen:**
- `.word.playing`: rgba(5, 60, 150, 0.2) - Blaue Markierung, font-weight 600
- `.word.playing-preview`: rgba(5, 60, 150, 0.08) - Leichte Preview-Markierung

### 4. Token-ID Sammler
**Status: ✅ Vollständig implementiert**

- `addTokenId()`: Fügt Token-ID hinzu (keine Duplikate)
- `updateTokenCollectorDisplay()`: Zeigt IDs kommasepariert
- `copyTokenListToClipboard()`: Kopiert IDs in Zwischenablage
- `resetTokenCollector()`: Löscht alle gesammelten IDs
- Auto-Resize der Textarea bei vielen IDs

### 5. Tooltip-System
**Status: ✅ Implementiert**

- `toggleTooltip()`: Zeigt/versteckt Hilfetexte
- Wird für Wort-Tooltips genutzt (POS, Lemma, Morph, Dep)
- Integration mit `formatMorphLeipzig()` aus `morph_formatter.js`

### 6. Download-Funktionen
**Status: ✅ Vollständig implementiert**

- MP3-Download: `createDownloadLink('downloadMp3', audioFile, 'mp3')`
- JSON-Download: `createDownloadLink('downloadJson', transcriptionFile, 'json')`
- TXT-Download: `downloadTxtFile()` - Erstellt Textdatei mit Metadaten + Transkript

### 7. Weitere Features
- **Scroll-to-Top Button**: Erscheint nach 100px Scroll
- **Footer-Statistik**: `loadFooterStats()` lädt Gesamtstatistiken
- **Speaker-Blocks**: Transkript organisiert nach Sprecher mit Zeitstempeln
- **Metadaten-Anzeige**: Land, Stadt, Radio, Datum, Revision

---

## 🎨 DESIGN & MD3-KOMPATIBILITÄT

### Aktuelle Probleme:

#### 1. **Sidebar zu breit**
**Problem:**
```css
/* components.css Zeile 3626 */
@media (min-width: 1000px) {
  .player-container {
    grid-template-columns: minmax(0, 2.5fr) minmax(0, 1fr);
  }
}
```
Das Verhältnis 2.5:1 macht die Sidebar relativ groß (ca. 28.6% der Breite).

**Empfehlung:** Verhältnis auf 3:1 oder 3.5:1 ändern (ca. 25% oder 22% Sidebar)

#### 2. **Keine MD3-Token Verwendung**
Die Sidebar nutzt aktuell ältere Token statt MD3-System:

**Aktuell:**
```css
.sidebar-section {
  padding: 1.0rem;
  background: rgba(234, 243, 245, 0.5);
  border: 0px solid rgba(47, 95, 115, 0.25);
  border-radius: var(--radius-md);
}
```

**MD3-konform wäre:**
```css
.sidebar-section {
  padding: var(--md3-space-4);
  background: var(--md3-color-surface-container-low);
  border: 1px solid var(--md3-color-outline-variant);
  border-radius: var(--md3-radius-medium);
  box-shadow: var(--md3-elevation-1);
}
```

#### 3. **Audio Player nicht MD3-konform**
```css
.custom-audio-player {
  background: rgba(234, 243, 245, 0.95);
  border-top: 1px solid var(--color-border);
}
```

**MD3-konform:**
```css
.custom-audio-player {
  background: var(--md3-color-surface-container);
  border-top: 1px solid var(--md3-color-outline);
  box-shadow: var(--md3-elevation-3);
}
```

#### 4. **Inkonsistente Farben**
- Player nutzt: `var(--color-accent)` (#2f5f73)
- MD3 definiert: `var(--md3-color-primary)` (#0a5981)

Buttons, Icons und Hervorhebungen sollten einheitlich MD3-Primary verwenden.

#### 5. **Spacing nicht MD3-konform**
Viele hartcodierte Werte statt MD3-Spacing-System:
- `padding: 1.0rem` → `padding: var(--md3-space-4)`
- `gap: 1.2rem` → `gap: var(--md3-space-5)`
- `margin-bottom: 0.75rem` → `margin-bottom: var(--md3-space-3)`

---

## 📝 EMPFOHLENE ÄNDERUNGEN

### Priorität 1: Layout-Anpassungen

1. **Sidebar schmaler machen:**
```css
@media (min-width: 1000px) {
  .player-container {
    grid-template-columns: minmax(0, 3.5fr) minmax(0, 1fr);
  }
}
```

2. **Sidebar Padding reduzieren:**
```css
.sidebar-section {
  padding: var(--md3-space-3) var(--md3-space-4);  /* 12px 16px statt 16px 16px */
}
```

3. **Sidebar-Titel kleiner:**
```css
.sidebar-title {
  font-size: var(--md3-label-small);  /* 0.6875rem statt 0.8rem */
  margin: 0 0 var(--md3-space-3) 0;    /* 12px statt 16px */
}
```

### Priorität 2: MD3-Token Migration

1. **Farben umstellen:**
   - `--color-accent` → `--md3-color-primary`
   - `--color-surface` → `--md3-color-surface-container-low`
   - `--color-border` → `--md3-color-outline-variant`

2. **Spacing standardisieren:**
   - Alle `padding`, `margin`, `gap` auf MD3-Space-Token
   - Alle `border-radius` auf MD3-Radius-Token

3. **Elevation hinzufügen:**
   - Sidebar-Sections: `box-shadow: var(--md3-elevation-1)`
   - Audio Player: `box-shadow: var(--md3-elevation-3)`

### Priorität 3: Typografie

```css
.sidebar-title {
  font-size: var(--md3-label-medium);
  line-height: var(--md3-lineheight-label);
  letter-spacing: var(--md3-tracking-wider);
}

.sidebar-meta {
  font-size: var(--md3-body-medium);
  line-height: var(--md3-lineheight-body);
}
```

---

## ✅ ZUSAMMENFASSUNG

### Was funktioniert perfekt:
- ✅ Alle Audio-Player-Funktionen
- ✅ Buchstabenmarkierung (3 Modi)
- ✅ Wort-Highlighting mit Animation
- ✅ Token-ID Sammler
- ✅ Download-Funktionen
- ✅ Keyboard-Shortcuts
- ✅ Tooltips & Metadaten

### Was verbessert werden sollte:
- ⚠️ Sidebar zu breit (aktuell ~28.6%, sollte ~22% sein)
- ⚠️ Keine MD3-Token Verwendung
- ⚠️ Inkonsistente Farbpalette
- ⚠️ Hardcodierte Spacing-Werte

### Code-Qualität:
- ✅ Keine Fehler in ESLint/Browser Console
- ✅ Saubere Modularisierung
- ✅ Gute Kommentierung
- ✅ Performance-optimiert (requestAnimationFrame)

---

## 🔧 NÄCHSTE SCHRITTE

1. CSS-Überarbeitung für Sidebar-Breite
2. Migration zu MD3-Tokens
3. Konsistente Farbpalette implementieren
4. Responsive Breakpoints testen
5. Accessibility-Check (ARIA-Labels)
