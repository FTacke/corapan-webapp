# 🎨 Mobile Layout v2 - Änderungen

**Update**: 17. Oktober 2025, 10:45 Uhr

---

## 📋 User-Feedback → Implementierung

### **1. Speaker Names: ÜBER Text, sehr klein**

**User**: "speakername je über dem Text und noch kleiner; so nimmt der text die gesamte verfügbare breite ein"

**Änderung**:
```css
/* VORHER (v1): Grid Layout - Name LINKS */
.speaker-turn {
  display: grid !important;
  grid-template-columns: auto 1fr !important; /* Name: 90px, Text: Rest */
}

.speaker-name {
  font-size: 0.75rem !important; /* 12px */
  max-width: 90px !important;
}

/* NACHHER (v2): Flex Column - Name OBEN */
.speaker-turn {
  display: flex !important;
  flex-direction: column !important; /* Vertikal! */
  gap: 0 !important; /* Kein Gap */
}

.speaker-name {
  font-size: 0.65rem !important; /* 10.4px - SEHR KLEIN */
  display: inline-block !important; /* Nur so breit wie Text */
  margin-bottom: 0.25rem !important;
}
```

**Visuell**:
```
VORHER (v1):              NACHHER (v2):
┌──────┬─────────────┐    ┌──────────────────┐
│ LIB- │ Claro pero  │    │ LIB-PF           │  ← Klein, oben
│ PF   │ sirve como  │    │ Claro pero sirve │  ← Volle Breite!
│      │ ...         │    │ como ...         │
└──────┴─────────────┘    └──────────────────┘
```

---

### **2. Speaker-Time: AUSGEBLENDET**

**User**: "speaker-time kann mobile ganz ausgeblendet werden"

**Änderung**:
```css
/* VORHER: Sichtbar */
.speaker-time {
  font-size: 0.7rem !important;
  display: block;
}

/* NACHHER: Komplett weg */
.speaker-time {
  display: none !important;
}
```

**Effekt**: 
- Mehr vertikaler Platz
- Fokus auf Textinhalt
- Zeit nur im Player sichtbar

---

### **3. Zeilenabstand: VIEL KOMPAKTER**

**User**: "Zeilenabstand viel geringer (scheint irgendwo blockiert zu werden, prüfe, wo das geregelt, geblockt wird)"

**Problem gefunden**:
```css
/* components.css (Desktop) - BLOCKIERT Mobile! */
.speaker-text {
  line-height: 1.3; /* Desktop */
}

.word {
  display: inline-flex !important; /* Macht Zeilenabstand größer! */
  align-items: center !important;
  min-height: 44px; /* Touch target = mehr Höhe */
}
```

**Lösung**:
```css
/* player-mobile.css - ÜBERSCHREIBT Desktop */
@media (max-width: 600px) {
  /* CSS Override am Anfang der Datei */
  .speaker-turn,
  .speaker-content,
  .speaker-text,
  .word {
    line-height: 1.35 !important; /* Override desktop 1.3/1.7 */
  }

  /* Word: inline statt flex */
  .word {
    font-size: 1.125rem !important;
    line-height: 1.35 !important; /* KOMPAKT! */
    padding: 0.15rem 0.1rem !important; /* MINIMAL */
    display: inline !important; /* Nicht flex! */
  }
}
```

**Vergleich**:
| Element | Desktop | v1 Mobile | v2 Mobile |
|---------|---------|-----------|-----------|
| line-height | 1.3 | 1.65 | **1.35** ✅ |
| word display | inline | inline-flex | **inline** ✅ |
| word padding | 0.1/0.2 | 0.375/0.25 | **0.15/0.1** ✅ |
| word min-height | - | 44px | **removed** ✅ |

---

### **4. Player: Lautstärke AUSGEBLENDET**

**User**: "die lautstärkeregelung kann mobile deaktiviert bleiben"

**Änderung**:
```css
/* VORHER: Sichtbar */
.mobile-layout .volume-container {
  display: flex !important;
  flex: 1 !important;
}

/* NACHHER: Versteckt */
.mobile-layout .volume-container {
  display: none !important;
}

/* Speed-Control: Volle Breite */
.mobile-layout .speed-control {
  width: 100% !important;
  justify-content: center !important;
}
```

**Visuell**:
```
VORHER (v1):
┌────────────────────────────────┐
│ ▶ ━━━━━━━━━━━━ 02:45 / 08:32  │  ← Zeile 1
│ 🔊 ━━━ 1.0x  -3s  +3s         │  ← Zeile 2
└────────────────────────────────┘

NACHHER (v2):
┌────────────────────────────────┐
│ ▶ ━━━━━━━━━━━━ 02:45 / 08:32  │  ← Zeile 1
│        1.0x  -3s  +3s          │  ← Zeile 2 (zentriert)
└────────────────────────────────┘
```

---

### **5. Player: Hintergrund VOLLE BREITE**

**User**: "der playerhintergrund sollte sauber über die gesamte breite gehen. scheinbar gibt es dort auch css-widersprüche"

**CSS-Widersprüche gefunden**:

1. **Problem: Container Padding**
```css
/* components.css (Desktop) */
.player-container {
  padding: clamp(1.5rem, 4vw, 2.5rem); /* Padding = Gap links/rechts! */
}
```

2. **Problem: Box-Sizing**
```css
/* Fehlte: box-sizing */
.custom-audio-player {
  width: 100%; /* 100% + padding = overflow! */
}
```

3. **Problem: Fixed Position Constraints**
```css
/* Nicht eindeutig */
.custom-audio-player {
  left: 0;
  right: 0; /* SOLLTE volle Breite sein, aber... */
  width: 100%; /* ...conflicts mit padding */
}
```

**Lösung**:
```css
/* player-mobile.css - CLEAN FULL-WIDTH */
.mobile-layout .custom-audio-player {
  /* Viewport Units für echte volle Breite */
  width: 100vw !important;
  max-width: 100vw !important;
  
  /* Fixed Position ohne Gaps */
  position: fixed !important;
  bottom: 0 !important;
  left: 0 !important;
  right: 0 !important;
  margin: 0 !important;
  
  /* Box-Sizing: padding INNERHALB der width */
  box-sizing: border-box !important;
  
  /* Padding nur innen */
  padding: var(--md3-space-3) var(--md3-space-2) !important;
  
  /* Kein border-radius */
  border-radius: 0 !important;
}

/* Container: Auch volle Breite */
.mobile-layout .player-container {
  width: 100% !important;
  max-width: 100% !important;
  margin: 0 !important;
  padding: var(--md3-space-2) !important;
  box-sizing: border-box !important;
}
```

**Test-Formel**:
```
width: 100vw (z.B. 390px iPhone)
+ padding-left: 8px
+ padding-right: 8px
+ box-sizing: border-box
= Total width: 390px ✅ (padding innen!)

OHNE box-sizing:
= Total width: 390px + 8px + 8px = 406px ❌ (Horizontal Scroll!)
```

---

## 📊 Vorher/Nachher Vergleich

### **Speaker Names:**
| Metric | v1 | v2 |
|--------|----|----|
| Layout | Grid (auto/1fr) | **Flex Column** ✅ |
| Position | Links | **Oben** ✅ |
| Font Size | 0.75rem (12px) | **0.65rem (10.4px)** ✅ |
| Width | max-width: 90px | **inline-block (auto)** ✅ |
| Text Width | ~300px | **~390px (100%)** ✅ |

### **Speaker-Time:**
| Metric | v1 | v2 |
|--------|----|----|
| Display | Sichtbar (0.7rem) | **display: none** ✅ |
| Vertical Space | ~20px | **0px** ✅ |

### **Zeilenabstand:**
| Metric | v1 | v2 |
|--------|----|----|
| line-height | 1.65 | **1.35** ✅ |
| word display | inline-flex | **inline** ✅ |
| word padding | 6px 4px | **2.4px 1.6px** ✅ |
| Gap zwischen Turns | 16px (space-4) | **8px (space-2)** ✅ |

### **Player:**
| Metric | v1 | v2 |
|--------|----|----|
| Volume Control | Sichtbar | **display: none** ✅ |
| Width | 100% (mit gap) | **100vw (absolut)** ✅ |
| box-sizing | - | **border-box** ✅ |
| Horizontal Scroll | ⚠️ Ja | **❌ Nein** ✅ |

---

## 🧪 Test-Checklist v2

### **Speaker Layout:**
- [ ] Name erscheint **OBEN** (nicht links)
- [ ] Name ist **0.65rem** (sehr klein)
- [ ] Name ist **inline-block** (nur so breit wie nötig)
- [ ] Text nutzt **100% Breite** (keine Spalte)
- [ ] Speaker-Time ist **NICHT sichtbar**

### **Zeilenabstand:**
- [ ] Text ist **kompakt** (line-height 1.35)
- [ ] Gap zwischen Turns ist **klein** (8px)
- [ ] Kein **übermäßiger Whitespace**

### **Player:**
- [ ] Lautstärke-Control **NICHT sichtbar**
- [ ] Speed-Control **zentriert** (volle Breite)
- [ ] Hintergrund geht **EXAKT bis Rand** (kein Gap)
- [ ] **Kein horizontaler Scroll** (100vw + box-sizing)

### **Visuell:**
- [ ] Maximaler Platz für Text
- [ ] Kompakte Darstellung
- [ ] Keine CSS-Widersprüche
- [ ] Sauberer Rand-zu-Rand Player

---

## 🚀 Deploy v2

**Status**: ✅ **Bereit zum Testen**

**Geänderte Dateien**:
- `static/css/player-mobile.css` (5 Edits)
- `docs/MOBILE_LAYOUT_HOTFIX.md` (Update)

**Test-Kommando**:
```bash
# Hard-Refresh
Strg + Shift + R
```

**Test-Device**: Chrome DevTools → iPhone 12 (390px)

**Erwartetes Ergebnis**:
```
┌────────────────────────────────────┐
│ LIB-PF                   ← Oben, klein
│ Claro pero sirve como a modo de    ← Volle Breite!
│ reclamo también porque yo le pido, │
│ pero él no, no me estaría          │
│ habilitando ninguna propiedad.     │
│                                    │
│ LIB-PM                             │
│ (.) ¿no? (.) [Claro] (.)          │
│                                    │
├────────────────────────────────────┤
│ ▶  ━━━━━━━━━━━━  00:12 / 05:47   │  ← Rand-zu-Rand!
│       1.0x  -3s  +3s               │
└────────────────────────────────────┘
```
