# Body Overflow Hidden Scroll Jump Fix

**Problem:** Page scrollt nach oben wenn Login-Sheet geöffnet wird ❌  
**Root Cause:** `body.login-open { overflow: hidden }` setzt Scroll-Position zurück  
**Lösung:** `position: fixed` mit CSS Variable für Scroll-Offset ✅  

---

## Root Cause Analysis

### CSS: `body.login-open { overflow: hidden }`

Wenn `overflow: hidden` auf `<body>` gesetzt wird:
1. Browser verhindert Scrollen (gewünscht ✅)
2. Browser setzt Scroll-Position auf `0` zurück (Problem ❌)
3. Page "springt" nach oben
4. Login-Sheet öffnet sich, aber Seite ist oben

### Warum passiert das?

```css
/* layout.css - VORHER (problematisch) */
body.app-shell.login-open {
  overflow: hidden;  /* ← Verhindert Scroll ABER setzt Position zurück! */
}
```

Wenn `overflow` von `auto/scroll` zu `hidden` wechselt:
- Browser entfernt Scrollbar
- Scroll-Kontext wird "reset"
- `scrollY` wird auf `0` gesetzt
- **Visual Result:** Page springt nach oben

---

## Lösung: position: fixed + CSS Variable

### Konzept: Body "fixieren" an aktueller Scroll-Position

```css
/* layout.css - NACHHER (korrekt) */
body.app-shell.login-open {
  overflow: hidden;                /* Verhindert Scrollen */
  position: fixed;                 /* Fixiert Body */
  top: var(--scroll-lock-offset, 0);  /* Offset = negative scroll position */
  left: 0;
  right: 0;
}
```

### Wie funktioniert das?

1. **Vor Login-Open:**
   - Body: `position: static`, `scrollY: 500px`
   - User sieht Page bei Scroll-Position 500px

2. **Beim Login-Open:**
   ```javascript
   const scrollY = 500;  // Aktuelle Position
   body.style.setProperty('--scroll-lock-offset', '-500px');
   body.classList.add('login-open');
   ```
   - Body wird zu: `position: fixed; top: -500px;`
   - Visual: Page sieht aus als wäre sie bei 500px scroll
   - Aber: Body ist fixiert, kein Scrollen möglich

3. **Visual Result:**
   - ✅ Page bleibt an gleicher Position
   - ✅ Kein Sprung nach oben
   - ✅ Login-Sheet öffnet sich über aktuellem View

4. **Beim Login-Close:**
   ```javascript
   body.classList.remove('login-open');
   body.style.removeProperty('--scroll-lock-offset');
   window.scrollTo(0, 500);  // Restore
   ```
   - Body zurück zu: `position: static`
   - Scroll explizit zu 500px wiederherstellen

---

## Implementierung

### 1. CSS (layout.css)

```css
body.app-shell.login-open {
  /* Prevent scrolling while login sheet is open, but keep scroll position */
  overflow: hidden;
  /* Lock scroll position to prevent jump */
  position: fixed;
  top: var(--scroll-lock-offset, 0);
  left: 0;
  right: 0;
}
```

**Wichtig:**
- `position: fixed` fixiert Body im Viewport
- `top: var(--scroll-lock-offset)` positioniert Body so, dass es "an richtiger Stelle" erscheint
- `left: 0; right: 0;` verhindert horizontale Verschiebung

---

### 2. JavaScript (main.js)

```javascript
function openLogin() {
  const scrollY = window.scrollY || window.pageYOffset;
  console.log('[Main] Opening login, scroll position:', scrollY);
  
  // Lock body scroll position using CSS variable
  document.body.style.setProperty('--scroll-lock-offset', `-${scrollY}px`);
  
  loginSheet.hidden = false;
  document.body.classList.add('login-open');
  
  const input = loginSheet.querySelector('input[name="username"]');
  if (input) {
    input.focus({ preventScroll: true });
  }
}

function closeLogin() {
  console.log('[Main] Closing login, restoring scroll to:', scrollPositionBeforeLogin);
  
  loginSheet.hidden = true;
  document.body.classList.remove('login-open');
  
  // Remove scroll lock CSS variable
  document.body.style.removeProperty('--scroll-lock-offset');
  
  // Restore scroll position
  window.scrollTo(0, scrollPositionBeforeLogin);
}
```

---

### 3. JavaScript (atlas/index.js)

```javascript
function openLoginSheet() {
  if (loginSheet) {
    const scrollY = window.scrollY || window.pageYOffset;
    console.log('[Atlas] Opening login sheet, saved scroll:', scrollY);
    
    // Lock body scroll position
    document.body.style.setProperty('--scroll-lock-offset', `-${scrollY}px`);
    
    loginSheet.hidden = false;
    document.body.classList.add('login-open');
    
    const input = loginSheet.querySelector('input[name="username"]');
    if (input) {
      input.focus({ preventScroll: true });
    }
  }
}
```

---

## Debug Logs

Hinzugefügte Console-Logs für Troubleshooting:

```javascript
// main.js
console.log('[Main] Opening login, scroll position:', scrollY);
console.log('[Main] Login opened, scroll locked at:', scrollY);
console.log('[Main] Closing login, restoring scroll to:', scrollY);

// atlas/index.js
console.log('[Atlas] openLoginSheet called, scroll position:', window.scrollY);
console.log('[Atlas] Opening login sheet, saved scroll:', scrollY);
console.log('[Atlas] Player link clicked, preventing default');
console.log('[Atlas] Filename:', filename, 'Auth:', isAuthenticated);
```

Diese Logs helfen bei Debugging:
- Zeigen wann Funktionen aufgerufen werden
- Zeigen aktuelle Scroll-Positionen
- Zeigen ob Auth-Check funktioniert

---

## Wichtige Ergänzungen

### event.stopPropagation()

```javascript
link.addEventListener('click', (event) => {
  event.preventDefault();
  event.stopPropagation(); // ✅ Verhindert Event-Bubbling
  // ...
});
```

**Warum wichtig:**
- Verhindert, dass Click-Event zu Parent-Elementen "bubbled"
- Parent könnte eigene Click-Handler haben (z.B. `<tr>` Click)
- Extra Sicherheit gegen unerwünschte Navigations

---

## Testing

### Browser Console Checks:

```javascript
// 1. Prüfen ob CSS Variable gesetzt wird:
window.getComputedStyle(document.body).getPropertyValue('--scroll-lock-offset');

// 2. Prüfen ob Body fixiert ist:
window.getComputedStyle(document.body).position;  // Sollte 'fixed' sein wenn Login offen

// 3. Prüfen aktuelle Scroll-Position:
window.scrollY;
```

### Manual Test:
1. Atlas-Seite öffnen
2. Nach unten scrollen (z.B. zu Mitte der Seite)
3. Auf Player-Link klicken
4. **Erwarte:**
   - ✅ Login-Sheet öffnet sich
   - ✅ **KEIN** Sprung nach oben
   - ✅ Seite bleibt visuell an gleicher Position
   - ✅ Console zeigt Logs mit korrekter Scroll-Position
5. Login schließen
6. **Erwarte:**
   - ✅ Scroll-Position wiederhergestellt

---

## Browser-Kompatibilität

### CSS Custom Properties (CSS Variables):
- ✅ Chrome 49+ (2016)
- ✅ Firefox 31+ (2014)
- ✅ Safari 9.1+ (2016)
- ✅ Edge 15+ (2017)

### position: fixed:
- ✅ Alle modernen Browser
- ✅ IE6+ (sehr alt)

### setProperty/removeProperty:
- ✅ Alle modernen Browser

---

## Zusammenfassung

**3 Fixes kombiniert:**

1. **Hash → Query Parameter** (`?showlogin=1`)
   - Verhindert Browser-Scroll zu Hash-Anchor

2. **javascript:void(0)** (statt `href="#"`)
   - Verhindert Link-Navigation

3. **position: fixed + CSS Variable** (dieser Fix)
   - Verhindert Scroll-Jump durch `overflow: hidden`

**Resultat:** Login-Sheet öffnet sich **komplett ohne Bewegung** ✅

---

**Datum:** 2025-10-19  
**Dateien:**
- `static/css/layout.css` (CSS Fix)
- `static/js/main.js` (JS Scroll Lock)
- `static/js/modules/atlas/index.js` (JS Scroll Lock + Debug Logs)  
**Status:** ✅ IMPLEMENTIERT
