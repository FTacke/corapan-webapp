# Player Link Reload Fix - Summary

**Problem:** Atlas-Seite lädt neu beim Klick auf Player-Link ❌  
**Root Cause:** `<a href="#">` verursacht Page-Navigation  
**Fix:** `href="#"` → `href="javascript:void(0)"` ✅  

---

## Was wurde geändert?

**Datei:** `static/js/modules/atlas/index.js`  
**Zeile:** 195

```javascript
// ❌ VORHER (verursacht Reload/Scroll):
<a href="#" data-action="open-player" ...>

// ✅ NACHHER (keine Navigation):
<a href="javascript:void(0)" data-action="open-player" ...>
```

---

## Warum funktioniert das?

### `href="#"` (PROBLEM):
- Browser navigiert zu `#` anchor
- Scroll nach oben ODER Page-Reload
- Passiert VOR `preventDefault()`
- Timing-Issue

### `href="javascript:void(0)"` (LÖSUNG):
- Browser führt `void(0)` aus → macht nichts
- Keine Navigation, kein Scroll
- Event-Handler funktioniert normal
- Standard-Konvention

---

## Kombination aller Fixes

### 1. Hash → Query Parameter
```python
# Backend: src/app/routes/player.py
redirect(f"{referrer}?showlogin=1")  # Statt #login
```

### 2. preventScroll
```javascript
// Frontend: static/js/main.js
input.focus({ preventScroll: true });
```

### 3. javascript:void(0)
```javascript
// Frontend: static/js/modules/atlas/index.js
href="javascript:void(0)"  // Statt href="#"
```

---

## Erwartetes Verhalten

**Komplett-Flow:**
1. User scrollt auf Atlas-Seite runter
2. Klickt Player-Link
3. **Link macht nichts** (javascript:void(0))
4. Event-Handler wird ausgeführt
5. Prüft: User nicht eingeloggt
6. `openLoginSheet()` aufgerufen
7. Scroll-Position gespeichert
8. Login-Sheet öffnet mit `preventScroll`
9. **Seite bleibt an gleicher Position!** ✅

**Nach Login:**
1. Form Submit zu `/auth/login`
2. Backend: `redirect("/?showlogin=1")` (Query-Param)
3. Browser lädt `/` (KEINE Hash-Navigation)
4. JavaScript erkennt `?showlogin=1`
5. Öffnet Login-Sheet
6. Entfernt Query-Param aus URL
7. **Seite scrollt NICHT** ✅

---

## Test-Checklist

### Im Browser testen:
- [ ] Atlas-Seite öffnen
- [ ] Nach unten scrollen (zu Stadt-Tabelle)
- [ ] Auf Player-Link klicken
- [ ] **Erwarte:** Login-Sheet öffnet, **KEIN** Scroll
- [ ] **Erwarte:** Browser Console **KEINE** Errors
- [ ] Login eingeben
- [ ] **Erwarte:** Redirect zu Player funktioniert

---

## Alle geänderten Dateien

### Backend (3):
1. `src/app/__init__.py` - 401 Handler
2. `src/app/routes/auth.py` - redirect_to_login
3. `src/app/routes/player.py` - player_page

### Frontend (2):
1. `static/js/main.js` - openLogin + preventScroll
2. `static/js/modules/atlas/index.js` - javascript:void(0)

---

## Status

✅ **Hash → Query Parameter** (behoben)  
✅ **preventScroll implementiert** (behoben)  
✅ **href="#" → href="javascript:void(0)"** (behoben)  
⏳ **Browser-Test erforderlich**

---

**Das Login-Sheet sollte sich jetzt sanft über den aktuellen View legen, ohne jegliche Scroll-Bewegung oder Page-Reload!** 🎉
