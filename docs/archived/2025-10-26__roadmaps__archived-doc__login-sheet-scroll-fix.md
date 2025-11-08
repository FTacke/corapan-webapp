# Login Sheet Scroll Fix

**Datum:** 2025-10-19  
**Problem:** Login-Sheet scrollt Seite nach oben beim Öffnen  
**Status:** ✅ BEHOBEN

---

## Problem

Wenn ein unauthentifizierter User auf einen geschützten Link klickt (z.B. Player-Link im Atlas):
1. Backend redirectet mit `#login` Hash
2. Browser scrollt automatisch nach oben (Hash-Anchor-Verhalten)
3. Login-Sheet öffnet sich
4. User sieht "Bewegung" hinter dem Login-Sheet

**Erwünschtes Verhalten:** Login-Sheet legt sich über aktuelle View ohne Scroll-Bewegung

---

## Root Cause

Hash-Anchors (`#login`) triggern automatisches Browser-Scroll-Verhalten **vor** JavaScript-Ausführung:

```python
# VORHER (problematisch):
return redirect(f"{referrer}#login")  # ❌ Browser scrollt zu #login
```

Der Browser scrollt zum Hash-Anchor, noch bevor JavaScript das Login-Sheet öffnen kann.

---

## Lösung

### 1. Backend: Query-Parameter statt Hash

**Geänderte Dateien:**
- `src/app/__init__.py` (401 Error Handler)
- `src/app/routes/auth.py` (redirect_to_login)
- `src/app/routes/player.py` (player_page)

**Änderung:**
```python
# VORHER:
return redirect(f"{referrer}#login")  # ❌ Scrollt nach oben

# NACHHER:
separator = '&' if '?' in referrer else '?'
return redirect(f"{referrer}{separator}showlogin=1")  # ✅ Kein Scroll
```

Query-Parameter triggern **kein** automatisches Scroll-Verhalten.

---

### 2. Frontend: Query-Parameter Detection + Scroll Prevention

**Geänderte Datei:** `static/js/main.js`

**Änderungen:**

#### A) openLogin() - Scroll-Prevention
```javascript
function openLogin() {
  if (!loginSheet) return;
  
  // Save current scroll position
  scrollPositionBeforeLogin = window.scrollY || window.pageYOffset;
  
  loginSheet.hidden = false;
  document.body.classList.add('login-open');
  previouslyFocusedForLogin = document.activeElement;
  
  // Focus input WITHOUT scrolling
  const input = loginSheet.querySelector('input[name="username"]');
  if (input) {
    input.focus({ preventScroll: true });  // ✅ Kein Scroll beim Focus
  }
  
  // Restore scroll position (safety)
  window.scrollTo(0, scrollPositionBeforeLogin);
}
```

#### B) URL Parameter Detection
```javascript
// VORHER:
if (window.location.hash === '#login') {  // ❌ Hash-basiert
  openLogin();
  history.replaceState(null, '', window.location.pathname);
}

// NACHHER:
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has('showlogin')) {  // ✅ Query-Parameter
  // Clean URL (remove showlogin param)
  urlParams.delete('showlogin');
  const newSearch = urlParams.toString();
  const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '');
  history.replaceState(null, '', newUrl);
  
  // Open login (scroll preserved)
  openLogin();
}
```

---

### 3. Atlas Module: Scroll-Prevention

**Geänderte Datei:** `static/js/modules/atlas/index.js`

```javascript
function openLoginSheet() {
  if (loginSheet) {
    // Save scroll position
    const scrollY = window.scrollY || window.pageYOffset;
    
    loginSheet.hidden = false;
    document.body.classList.add('login-open');
    
    // Focus WITHOUT scroll
    const input = loginSheet.querySelector('input[name="username"]');
    if (input) {
      input.focus({ preventScroll: true });  // ✅ Kein Scroll
    }
    
    // Restore scroll (safety)
    window.scrollTo(0, scrollY);
  } else if (loginButtons.length) {
    // Use global handler
    loginButtons[0].dispatchEvent(new Event('click', { bubbles: true }));
  }
}
```

---

## Verbesserungen

### 1. Kein automatisches Scroll mehr
- Query-Parameter (`?showlogin=1`) statt Hash (`#login`)
- Browser scrollt nicht automatisch

### 2. Explizite Scroll-Prevention
- `input.focus({ preventScroll: true })` verhindert Scroll-to-focused-element
- Scroll-Position wird gespeichert und wiederhergestellt

### 3. Clean URLs
- Query-Parameter wird nach Öffnen des Login-Sheets aus URL entfernt
- URL bleibt sauber: `/atlas` statt `/atlas?showlogin=1`

---

## Testing

### Manueller Test:
1. Auf Atlas-Seite navigieren (`/atlas`)
2. Nach unten scrollen (z.B. zu einer Stadt-Tabelle)
3. Auf Player-Link klicken (ohne eingeloggt zu sein)
4. **Erwarte:**
   - ✅ Login-Sheet öffnet sich
   - ✅ **Keine** Scroll-Bewegung
   - ✅ Seite bleibt an gleicher Position hinter Login-Sheet
5. Login mit gültigen Credentials
6. **Erwarte:**
   - ✅ Redirect zu Player mit korrektem Audio/Transcript

### Erwartetes Verhalten:
- Login-Sheet erscheint als Overlay über aktuellem View
- Keine sichtbare Bewegung/Scroll der Hintergrund-Seite
- Nach Login: Redirect zur intended URL (Player)

---

## Technische Details

### Browser Scroll-to-Anchor:
- Hash-Anchors (`#id`) triggern `scrollIntoView()` automatisch
- Passiert **vor** JavaScript execution
- **Nicht** mit JavaScript preventbar

### Query-Parameter:
- **Kein** automatisches Scroll-Verhalten
- Können mit JavaScript gelesen/modifiziert werden
- Ideal für "soft state" wie "Login öffnen"

### focus({ preventScroll: true }):
- Modern Browser Feature (Chrome 64+, Firefox 68+, Safari 15.4+)
- Verhindert automatisches Scroll-to-focused-element
- Fallback: `window.scrollTo()` nach Focus

---

## Dateien geändert

### Backend (3 Dateien):
1. `src/app/__init__.py` - 401 Error Handler
2. `src/app/routes/auth.py` - redirect_to_login()
3. `src/app/routes/player.py` - player_page()

### Frontend (2 Dateien):
1. `static/js/main.js` - openLogin(), URL parameter detection
2. `static/js/modules/atlas/index.js` - openLoginSheet()

---

## Lessons Learned

1. **Hash-Anchors sind nicht ideal für UI-State**
   - Browser scrollt automatisch (unpreventable)
   - Query-Parameter sind besser für "soft state"

2. **preventScroll ist wichtig für Overlays**
   - `element.focus()` scrollt standardmäßig
   - `{ preventScroll: true }` verhindert das

3. **Scroll-Position explizit managen**
   - Bei Overlays Scroll-Position speichern
   - Nach Actions wiederherstellen
   - Defensive Programmierung: Mehrfach sicherstellen

---

**Status:** ✅ KOMPLETT IMPLEMENTIERT  
**Testing:** ⏳ Manueller Browser-Test erforderlich  
**Nächste Schritte:** Im Browser testen (Atlas → Scroll → Player-Link klicken)
