---
title: "Authentication Troubleshooting"
status: active
owner: backend-team
updated: "2025-11-07"
tags: [authentication, troubleshooting, jwt, debugging]
links:
  - ../concepts/authentication-flow.md
  - ../reference/api-auth-endpoints.md
---

# Authentication Troubleshooting

Bekannte Authentifizierungsprobleme und deren Lösungen.

---

## Problem 1: "Token has expired" auf öffentlichen Seiten

**Symptome:**
- User sieht "Tu sesión ha expirado" auf Seiten wie `/corpus` (sollten öffentlich sein)
- Redirect-Loop: Login → Corpus → Login

**Ursache:**
`@jwt_required(optional=True)` triggert Error-Handler auch bei expired tokens, statt diese zu ignorieren.

**Lösung:**
JWT-Error-Handler müssen optional-Routes erkennen:

```python
# src/app/extensions/__init__.py
OPTIONAL_AUTH_ROUTES = ['/corpus/', '/media/', '/auth/session', '/auth/logout']

@jwt_manager.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    # Check if current route is optional-auth
    if any(request.path.startswith(route) for route in OPTIONAL_AUTH_ROUTES):
        # Return None to allow route to proceed without auth
        return None
    
    # For mandatory-auth routes, redirect to login
    flash("Tu sesión ha expirado...", "warning")
    return redirect(request.referrer or url_for("public.landing_page") + "?showlogin=1")
```

**Status:** ✅ Behoben (seit Nov 2024)

---

## Problem 2: 401 Unauthorized statt Login-Redirect

**Symptome:**
- User sieht Werkzeug-Fehlerseite "401 Unauthorized" statt Login-Formular
- Keine Flash-Message sichtbar

**Ursache:**
Error-Handler verwendete `abort(401)`, was eine Werkzeug-Exception wirft.

**Lösung:**
Error-Handler müssen direkt `redirect()` zurückgeben:

```python
# ❌ FALSCH
@jwt_manager.unauthorized_loader
def unauthorized_callback(error):
    flash("Por favor, inicia sesión.", "info")
    abort(401)  # ← Wirft Exception

# ✅ RICHTIG
@jwt_manager.unauthorized_loader
def unauthorized_callback(error):
    flash("Por favor, inicia sesión.", "info")
    return redirect(url_for("public.landing_page") + "?showlogin=1")
```

**Status:** ✅ Behoben (seit Nov 2024)

---

## Problem 3: Login-Buttons reagieren nicht nach Logout

**Symptome:**
- Nach Logout auf gleicher Seite bleiben → Login-Buttons öffnen nichts
- Console-Error: "Cannot read property 'classList' of null"

**Ursache:**
`data-auth="true"` bleibt im DOM, obwohl User ausgeloggt ist (kein Page-Reload).

**Aktueller Status:** ⚠️ **TEILWEISE GELÖST**

**Workaround:**
Logout redirected immer zur Landing Page (erzwingt Page-Reload):

```python
# src/app/routes/auth.py
@blueprint.post("/auth/logout")
def logout():
    response = redirect(url_for("public.landing_page"))
    unset_jwt_cookies(response)
    flash("Has cerrado sesión correctamente.", "success")
    return response
```

**TODO: Logout-Fix**

**Option A: Immer Page-Reload** (aktuell implementiert)

**Option B: Client-Side Logout mit Page-Reload**
```javascript
// In main.js: Logout-Form mit Fetch + Reload
logoutForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await fetch('/auth/logout', { method: 'POST', credentials: 'same-origin' });
    window.location.reload(); // Force reload to update data-auth
});
```

**Empfehlung:** Option B - User bleibt auf aktueller Seite, aber Page wird reloaded.

---

## Problem 4: Return-URL geht verloren

**Symptome:**
- User klickt auf Player-Link → Login → landet auf Landing Page statt Player
- Query-Parameter verschwinden

**Ursache 1: sessionStorage inconsistent**

**Lösung:**
Server-Side-Session als Fallback:

```python
# src/app/routes/auth.py
def save_return_url(url):
    """Save return URL to server-side session"""
    session[RETURN_URL_SESSION_KEY] = url

@blueprint.post("/auth/login")
def login():
    # ... validate ...
    
    # Get return URL from session (server-side fallback)
    return_url = session.pop(RETURN_URL_SESSION_KEY, None)
    
    # Or from form (client-side)
    if not return_url:
        return_url = request.form.get("return_url")
    
    ready_url = url_for("auth.auth_ready", next=return_url or "/")
    # ...
```

**Ursache 2: Query-Parameter werden encoding-escaped**

**Lösung:**
`urllib.parse.quote()` für URLs verwenden:

```python
from urllib.parse import quote
return_url = quote(request.url, safe=':/?#[]@!$&\'()*+,;=')
```

**Status:** ✅ Behoben

---

## Problem 5: Player lädt ohne Audio/Transcription

**Symptome:**
- Nach Login redirected zu Player → "Transcription not found"
- URL korrekt, aber Parameter fehlen im Backend

**Ursache:**
`/auth/ready` redirected zu URL ohne Query-Parameter.

**Diagnose:**
```javascript
// Browser-Console auf /auth/ready
console.log(nextUrl);  // Sollte zeigen: /player?transcription=...&audio=...
```

**Sollte zeigen:** Komplette URL mit allen Query-Parametern

**Falls Query-Parameter fehlen:**

**Lösung:**
`url_for()` mit `_external=False` (default) verwendet **relative URLs**:

```python
# ✅ RICHTIG
ready_url = url_for("auth.auth_ready", next=return_url)
# next=/player?transcription=...&audio=... (wird automatisch URL-encoded)
```

**Status:** ✅ Behoben

---

## Problem 6: Cookies werden nicht gesetzt (CORS)

**Symptome:**
- Login erfolgreich, aber `/auth/session` zeigt "authenticated: false"
- Browser-Console: "Set-Cookie was blocked because..." oder "Cross-Origin..."

**Ursache:**
Absolute URLs mit verschiedenen Hosts/Ports:
- `http://127.0.0.1:8000` vs `http://localhost:8000` = **Cross-Origin**

**Lösung:**
Immer relative URLs oder `location.origin`:

```javascript
// ❌ FALSCH
await fetch('http://127.0.0.1:8000/auth/session');

// ✅ RICHTIG
await fetch('/auth/session', {
  credentials: 'same-origin',
  cache: 'no-store'
});
```

**Status:** ✅ Behoben

---

## Problem 7: "Auth Ready" bleibt hängen ("Autenticando...")

**Symptome:**
- Nach Login bleibt User auf `/auth/ready` Seite
- Spinner dreht sich endlos
- Nach 10 Sekunden: Redirect zu Landing Page mit `?e=auth`

**Diagnose:**
Browser-Console (F12) → Network-Tab → `/auth/session` Requests:

**Sollte zeigen:**
```
GET /auth/session → 200 OK
{"authenticated": true, "user": {...}}
```

**Falls 401:**
Cookies wurden nicht gesetzt oder nicht gesendet.

**Lösung 1: Cookies prüfen**
Browser DevTools → Application → Cookies → `http://127.0.0.1:8000`

**Sollte zeigen:**
- `access_token_cookie` (HttpOnly, SameSite=Lax)
- `refresh_token_cookie` (HttpOnly, SameSite=Lax)

**Falls Cookies fehlen:**
- Backend setzt Cookies nicht korrekt (`set_access_cookies()` fehlt)
- Browser blockiert Third-Party-Cookies (Check Browser-Settings)

**Lösung 2: fetch() prüfen**
```javascript
// /auth/ready page
const response = await fetch('/auth/session', {
  credentials: 'same-origin',  // ← MUSS vorhanden sein
  cache: 'no-store'
});
```

**Status:** ✅ Robust (seit Nov 2024)

---

## Debugging-Checkliste

### Backend-Debugging

```python
# src/app/routes/auth.py
import logging

@blueprint.post("/auth/login")
def login():
    logging.debug(f"Login attempt: {request.form.get('username')}")
    logging.debug(f"Return URL: {session.get(RETURN_URL_SESSION_KEY)}")
    # ...
    logging.debug(f"Redirecting to: {ready_url}")
```

**Logs prüfen:**
```bash
Get-Content logs/application.log -Wait -Tail 50
```

---

### Frontend-Debugging

```javascript
// Browser-Console
// Check auth status
document.querySelector('[data-element="top-app-bar"]').dataset.auth

// Check sessionStorage
sessionStorage.getItem('_player_redirect_after_login')

// Check cookies (nur sichtbare)
document.cookie

// Simulate login redirect
location.href = '/player?transcription=/media/transcripts/file.json&audio=/media/full/file.mp3';
```

---

### Cookie-Debugging

```bash
# Mit curl Cookies prüfen
curl -v -X POST http://127.0.0.1:8000/auth/login \
  -d "username=admin&password=test" \
  -c cookies.txt

# Cookies anzeigen
type cookies.txt

# Mit Cookies Request machen
curl -v -b cookies.txt http://127.0.0.1:8000/auth/session
```

**Sollte zeigen:**
```
Set-Cookie: access_token_cookie=...
Set-Cookie: refresh_token_cookie=...
```

---

## Siehe auch

- [Authentication Flow Overview](../concepts/authentication-flow.md) - Konzeptuelle Übersicht
- [API Auth Endpoints](../reference/api-auth-endpoints.md) - API-Dokumentation
