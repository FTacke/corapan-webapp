---
title: "Authentication Flow Overview"
status: active
owner: backend-team
updated: "2025-11-07"
tags: [authentication, jwt, security, architecture]
links:
  - ../reference/api-auth-endpoints.md
  - ../troubleshooting/auth-issues.md
  - ../operations/deployment.md
---

# Authentication Flow Overview

## Übersicht

Die CO.RA.PAN Webapp verwendet **JWT-basierte Authentifizierung** mit Cookie-basierten Tokens und einer **deterministischen Auth-Ready-Seite** zur Vermeidung von Race Conditions.

### Authentifizierungsstufen

1. **Öffentlich (keine Auth erforderlich)**
   - Landing Page (`/`)
   - Projekt-Seiten (`/proyecto/*`)
   - Atlas-Übersicht (`/atlas`)
   - Impressum/Privacy

2. **Optional Auth (Enhanced für eingeloggte User)**
   - Corpus (`/corpus`) - Suche öffentlich, aber mehr Features für Auth-User
   - Media-Endpoints (`/media/full/*`, `/media/temp/*`) - Config-gesteuert

3. **Mandatory Auth (Login erforderlich)**
   - Player (`/player`) - **Immer Auth erforderlich**
   - Editor (`/editor/*`) - Nur für Editor/Admin
   - Admin (`/admin/*`) - Nur für Admin
   - Atlas File-Details (`/get_stats_files_from_db`) - Auth erforderlich

---

## Cookie-basierte Authentifizierung

### Cookie-Konfiguration

Die Webapp nutzt **HttpOnly-Cookies** für JWT-Tokens:

- **Access Token**: `access_token_cookie` (1 Stunde Gültigkeit)
- **Refresh Token**: `refresh_token_cookie` (7 Tage Gültigkeit)
- **Cookie-Eigenschaften**:
  - `HttpOnly=True` (nicht via JavaScript lesbar)
  - `Secure=True` (nur HTTPS in Production, HTTP in Dev)
  - `SameSite=Lax` (erlaubt Cookies bei same-site Redirects)
  - `Path=/` (Cookie wird mit **allen** Requests gesendet)

### Warum Cookie-basiert?

- **Automatisch**: Browser sendet Cookies mit jedem Request
- **Sicher**: HttpOnly verhindert XSS-Angriffe
- **Persistent**: Refresh-Token ermöglicht Auto-Login für 7 Tage

---

## Login-Flow mit Auth-Ready-Page

### Problem: Cookie-Timing Race Condition

Nach dem POST-Login-Request muss der Browser:
1. Die Response mit `Set-Cookie` verarbeiten
2. Cookies in den Cookie-Store schreiben
3. Zum Player redirecten
4. Player-Request mit Cookies senden

**Problem**: Browser kann Player-Seite laden, bevor Cookies vollständig verfügbar sind → Player zeigt leere Seite → Manual Refresh erforderlich.

### Lösung: `/auth/ready` Intermediate Page

**1. Login setzt Cookies und redirected zu `/auth/ready`**

```python
@blueprint.post("/auth/login")
def login():
    # ... validate credentials ...
    
    # Create tokens
    access_token = issue_token(username, role)
    refresh_token = create_refresh_token(identity=username)
    
    # Redirect to /auth/ready with 303 (POST->GET)
    ready_url = url_for("auth.auth_ready", next=return_url)
    response = make_response(redirect(ready_url, 303))
    
    # Set cookies in this response
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    
    return response
```

**Wichtig**: `303 See Other` statt `302 Found` verhindert Cookie-Edge-Cases.

**2. `/auth/ready` pollt `/auth/session` bis Auth bestätigt**

Die Ready-Seite ist eine **minimale HTML-Seite mit JavaScript**:

```javascript
// /auth/ready page JavaScript
(async () => {
  for (let i = 0; i < 10; i++) {
    const response = await fetch('/auth/session', {
      credentials: 'same-origin',
      cache: 'no-store'
    });
    
    if (response.ok) {
      // Auth confirmed - redirect to target page
      location.replace(nextUrl);
      return;
    }
    
    // Wait 150ms before retry
    await new Promise(r => setTimeout(r, 150));
  }
  
  // Failed after 10 attempts
  location.href = '/?showlogin=1&e=auth';
})();
```

**3. `/auth/session` verifiziert Token**

```python
@blueprint.get("/auth/session")
@jwt_required(optional=True)
def check_session():
    user = getattr(g, "user", None)
    if user:
        return jsonify({"authenticated": True, "user": user}), 200
    else:
        return jsonify({"authenticated": False}), 401
```

**Vorteile dieser Lösung:**

✅ **Deterministisch**: Kein Race-Condition mehr  
✅ **Kein Heuristik**: Polling statt feste Delays  
✅ **Robust**: Funktioniert über verschiedene Browser/Devices  
✅ **Transparent**: User sieht kurz "Autenticando..." (< 300ms meist)  

---

## Login-Szenarien

### Scenario 1: User klickt auf Player-Link vom Atlas aus (nicht eingeloggt)

1. **User klickt auf Player-Link**
   - JavaScript: `handlePlayerLinkClick()` in `atlas/index.js`
   - Prüft: `isUserAuthenticated()` → false
   - Speichert Ziel-URL: `sessionStorage.setItem('_player_redirect_after_login', playerUrl)`
   - Öffnet Login-Sheet: `openLoginSheet()`

2. **User loggt sich ein**
   - Login-Form submittet via `main.js`
   - Prüft: `sessionStorage.getItem('_player_redirect_after_login')`
   - **Falls vorhanden**: Login via Fetch-API, dann Client-Side-Redirect
   - **Falls nicht vorhanden**: Normaler Form-Submit, Backend redirected

3. **Backend-Login** (`/auth/login`)
   - Validiert Credentials
   - Erstellt JWT Access Token (1h) + Refresh Token (7 Tage)
   - Setzt Cookies: `access_token_cookie`, `refresh_token_cookie`
   - Redirected zu: Gespeicherte Return-URL **oder** Referrer **oder** Landing Page

4. **Nach Login**
   - Browser navigiert zu Player mit allen Query-Parametern
   - JWT-Cookie wird automatisch mitgeschickt
   - `@jwt_required()` prüft Token → OK → Player lädt

### Scenario 2: User versucht direkt auf Player zuzugreifen (nicht eingeloggt)

1. **User navigiert zu** `/player?transcription=...&audio=...`
   - Flask: `@jwt_required()` prüft Token → Keiner vorhanden
   - `unauthorized_callback` wird aufgerufen
   - **Return-URL wird gespeichert**: `save_return_url(request.url)`
   - Redirect zu Referrer mit `?showlogin=1`

2. **Browser wird redirected**
   - Zu: `/atlas?showlogin=1` (oder woher der User kam)
   - JavaScript: `main.js` erkennt `?showlogin=1` → öffnet Login-Sheet
   - Return-URL ist **bereits in Session gespeichert** (Server-Side)

3. **User loggt sich ein**
   - Login-Form submittet **normal** (kein sessionStorage erforderlich)
   - Backend holt Return-URL aus Session: `session.pop(RETURN_URL_SESSION_KEY)`
   - Redirected zu: `/player?transcription=...&audio=...` (Original-URL)

### Scenario 3: Token ist abgelaufen

1. **User mit abgelaufenem Token navigiert zu Player**
   - Flask: `@jwt_required()` prüft Token → Abgelaufen
   - `expired_token_callback` wird aufgerufen
   - Return-URL wird gespeichert
   - Redirect mit `?showlogin=1` + Flash-Message: "Tu sesión ha expirado..."

2. **Rest wie Scenario 2**

---

## Logout-Flow

### Standard-Logout

1. **User klickt auf Logout-Button**
   - Form submittet POST zu `/auth/logout`
   - Backend: `unset_jwt_cookies()` löscht alle JWT-Cookies
   - Redirect zu Landing Page (`/`)

2. **Browser landet auf Landing Page**
   - Alle JWT-Cookies gelöscht
   - User ist ausgeloggt
   - Login-Buttons funktionieren

### Problem: Logout ohne Page-Reload

**NICHT IMPLEMENTIERT** - Logout macht immer Redirect zur Landing Page.
Wenn User auf gleicher Seite bleiben soll:
- Client-Side: Cookies manuell löschen + UI aktualisieren
- **ODER**: Page-Reload erzwingen

---

## DOM Data Attributes

### `[data-element="top-app-bar"]` → `data-auth="true/false"`
- **Zweck**: JavaScript kann Auth-Status prüfen
- **Gesetzt von**: Template `base.html` (Jinja)
- **Geprüft von**: `isUserAuthenticated()` in `atlas/index.js`, `corpus/audio.js`

### `[data-action="open-login"]`
- **Zweck**: Öffnet Login-Sheet
- **Event-Handler**: `main.js`

### `[data-action="close-login"]`
- **Zweck**: Schließt Login-Sheet
- **Event-Handler**: `main.js`

### `[data-action="open-player"]`
- **Zweck**: Player-Link mit Auth-Check (Atlas)
- **Event-Handler**: `handlePlayerLinkClick()` in `atlas/index.js`

---

## Session Storage Keys

### `_player_redirect_after_login`
- **Verwendet von**: Atlas, Corpus Player-Links
- **Zweck**: Client-Side-Redirect nach Login
- **Scope**: sessionStorage (nur aktueller Tab)
- **Cleanup**: Nach erfolgreichem Login automatisch gelöscht

### `_return_url_after_login` (Server-Side Session)
- **Verwendet von**: Flask-Backend (`auth.py`)
- **Zweck**: Server-Side-Redirect nach Login
- **Scope**: Flask-Session (Cookie-basiert)
- **Cleanup**: Nach Login automatisch `session.pop()`

---

## Code-Referenzen

### Backend
- **Auth-Routes**: `src/app/routes/auth.py`
- **JWT-Config**: `src/app/config/__init__.py`
- **JWT-Handlers**: `src/app/extensions/__init__.py`
- **Error-Handlers**: `src/app/__init__.py`

### Frontend
- **Login-Sheet**: `templates/partials/status_banner.html`
- **Main Login-Logic**: `static/js/main.js`
- **Atlas Player-Links**: `static/js/modules/atlas/index.js`
- **Corpus Player-Links**: `static/js/modules/corpus/audio.js`

### Templates
- **Auth-Status**: `templates/base.html` → `data-auth="{{ 'true' if g.user else 'false' }}"`
- **Login-Buttons**: `templates/partials/_navbar.html`, `_navigation_drawer.html`

---

## Siehe auch

- [API Auth Endpoints](../reference/api-auth-endpoints.md) - Technische API-Details
- [Auth Troubleshooting](../troubleshooting/auth-issues.md) - Bekannte Probleme & Lösungen
- [Deployment](../operations/deployment.md) - Production-Konfiguration
