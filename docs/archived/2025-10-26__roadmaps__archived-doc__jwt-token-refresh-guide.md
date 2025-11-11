# JWT Token Refresh - Implementierungs-Guide

**Datum:** 19. Oktober 2025  
**Status:** Konzept & Empfehlung

---

## ❓ Deine Frage: Braucht Token-Refresh ein Dialogfeld?

### Kurze Antwort: **NEIN** ❌

Token-Refresh läuft **automatisch im Hintergrund** ohne User-Interaktion. Es gibt **kein Dialogfeld** zu designen!

---

## 🔄 Wie funktioniert Token-Refresh?

### Aktuelles System (OHNE Refresh)
```
User loggt ein → JWT Cookie (3h) → Cookie abgelaufen → User muss neu einloggen
```

**Problem:** User wird nach 3 Stunden automatisch ausgeloggt, auch wenn er aktiv arbeitet.

---

### Empfohlenes System (MIT Refresh)

#### Zwei Token-Typen:

**1. Access Token (Kurze Laufzeit: 15-30 Min)**
- Wird für API-Requests verwendet
- Kurze Laufzeit = höhere Sicherheit
- Bei Ablauf: Automatischer Refresh

**2. Refresh Token (Lange Laufzeit: 7-30 Tage)**
- Wird NUR zum Erneuern des Access Tokens verwendet
- Liegt sicher im HTTP-only Cookie
- Bei Ablauf: User muss neu einloggen

#### Flow:
```
1. User loggt ein
   → Access Token (30 Min) + Refresh Token (7 Tage)

2. User arbeitet mit der App
   → Access Token wird bei jedem Request geprüft

3. Access Token läuft ab (nach 30 Min)
   → Frontend merkt: 401 Unauthorized
   → Automatischer Background-Request mit Refresh Token
   → Neue Access Token wird ausgestellt
   → Original-Request wird wiederholt
   → User merkt NICHTS ✅

4. Refresh Token läuft ab (nach 7 Tagen)
   → Login-Dialog erscheint
```

---

## 💻 Implementierung

### Backend (Flask)

#### 1. Config erweitern (`src/app/config.py`)
```python
class BaseConfig:
    # ... existing config ...
    
    # Access Token: 30 Minuten
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    
    # Refresh Token: 7 Tage
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Separate Cookie-Namen
    JWT_ACCESS_COOKIE_NAME = "corapan_access_token"
    JWT_REFRESH_COOKIE_NAME = "corapan_refresh_token"
    
    # Refresh-Cookie Path (nur für Refresh-Endpoint)
    JWT_REFRESH_COOKIE_PATH = "/auth/refresh"
```

#### 2. Neue Route für Refresh (`src/app/routes/auth.py`)
```python
@blueprint.post("/refresh")
@jwt_required(refresh=True)
def refresh() -> Response:
    """
    Refresh endpoint - erneuert Access Token.
    Läuft automatisch im Hintergrund, KEIN User-Dialog!
    """
    # Hole User-Info aus Refresh Token
    current_user = get_jwt_identity()
    
    # TODO: Optional - prüfe ob User noch aktiv ist
    # if not user_is_active(current_user):
    #     return jsonify({'error': 'User deactivated'}), 401
    
    # Erstelle neuen Access Token
    new_access_token = create_access_token(identity=current_user)
    
    # Setze neuen Access Token als Cookie
    response = jsonify({'msg': 'Token refreshed'})
    set_access_cookies(response, new_access_token)
    
    return response
```

#### 3. Login-Endpoint anpassen
```python
@blueprint.post("/login")
@limiter.limit("5 per minute")
def login() -> Response:
    # ... validation ...
    
    # Erstelle BEIDE Tokens
    access_token = create_access_token(
        identity=username,
        additional_claims={'role': credential.role.value}
    )
    refresh_token = create_refresh_token(identity=username)
    
    response = redirect(referrer)
    
    # Setze BEIDE Cookies
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    
    return response
```

#### 4. Logout-Endpoint anpassen
```python
@blueprint.post("/logout")
@jwt_required(optional=True)
def logout() -> Response:
    response = redirect(referrer)
    
    # Lösche BEIDE Cookies
    unset_jwt_cookies(response)
    
    return response
```

---

### Frontend (JavaScript)

#### Automatischer Token-Refresh bei 401

**Variante A: Axios Interceptor (wenn du Axios nutzt)**
```javascript
// static/js/modules/auth/token-refresh.js
import axios from 'axios';

// Response Interceptor
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    // Wenn 401 und noch nicht versucht zu refreshen
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Refresh Token Request
        await axios.post('/auth/refresh', {}, {
          withCredentials: true  // Wichtig: Cookies mitsenden
        });
        
        // Original-Request wiederholen
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh fehlgeschlagen → Logout
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

**Variante B: Fetch Wrapper (aktuelles System)**
```javascript
// static/js/modules/auth/fetch-with-refresh.js

async function fetchWithRefresh(url, options = {}) {
  // Erste Anfrage
  let response = await fetch(url, {
    ...options,
    credentials: 'same-origin'  // Wichtig: Cookies mitsenden
  });
  
  // Wenn 401: Versuche Token-Refresh
  if (response.status === 401) {
    const refreshResponse = await fetch('/auth/refresh', {
      method: 'POST',
      credentials: 'same-origin'
    });
    
    if (refreshResponse.ok) {
      // Refresh erfolgreich → Original-Request wiederholen
      response = await fetch(url, {
        ...options,
        credentials: 'same-origin'
      });
    } else {
      // Refresh fehlgeschlagen → Redirect zu Login
      window.location.href = '/login';
      throw new Error('Session expired');
    }
  }
  
  return response;
}

// Export für globale Nutzung
window.fetchWithRefresh = fetchWithRefresh;
```

**Verwendung in anderen Modulen:**
```javascript
// Statt fetch():
const response = await fetch('/admin/metrics', { credentials: 'same-origin' });

// Mit Auto-Refresh:
const response = await fetchWithRefresh('/admin/metrics');
```

---

## 🔒 Sicherheits-Features

### 1. Token Rotation (Empfohlen)
Bei jedem Refresh wird auch ein **neuer Refresh Token** ausgegeben:
```python
@blueprint.post("/refresh")
@jwt_required(refresh=True)
def refresh() -> Response:
    current_user = get_jwt_identity()
    
    # Neue BEIDE Tokens
    new_access_token = create_access_token(identity=current_user)
    new_refresh_token = create_refresh_token(identity=current_user)
    
    response = jsonify({'msg': 'Token refreshed'})
    set_access_cookies(response, new_access_token)
    set_refresh_cookies(response, new_refresh_token)  # Auch Refresh rotieren!
    
    return response
```

**Vorteil:** Wenn ein Refresh Token gestohlen wird, ist er nach einem Refresh ungültig.

### 2. Refresh Token Blacklist (Optional)
```python
# In-Memory-Set für gestohlene Tokens
REVOKED_TOKENS = set()

@blueprint.post("/refresh")
@jwt_required(refresh=True)
def refresh() -> Response:
    jti = get_jwt()['jti']  # Unique Token ID
    
    if jti in REVOKED_TOKENS:
        return jsonify({'error': 'Token revoked'}), 401
    
    # ... Token erneuern ...
    
    # Alten Token auf Blacklist
    REVOKED_TOKENS.add(jti)
    
    return response
```

### 3. User Activity Tracking
```python
# Nur refreshen wenn User aktiv war
LAST_ACTIVITY = {}  # {username: datetime}

@blueprint.post("/refresh")
@jwt_required(refresh=True)
def refresh() -> Response:
    current_user = get_jwt_identity()
    last_active = LAST_ACTIVITY.get(current_user)
    
    if last_active:
        # Wenn >1h inaktiv: Kein Refresh
        if datetime.utcnow() - last_active > timedelta(hours=1):
            return jsonify({'error': 'Inactive session'}), 401
    
    # ... Token erneuern ...
```

---

## 📱 User Experience

### Was der User merkt:

#### ✅ MIT Token-Refresh (Empfohlen)
```
User arbeitet 2 Stunden am Corpus
→ Access Token läuft alle 30 Min ab
→ Automatischer Refresh im Hintergrund
→ User merkt NICHTS
→ User wird nach 7 Tagen (Refresh-Ablauf) ausgeloggt
```

#### ❌ OHNE Token-Refresh (Aktuell)
```
User arbeitet 3+ Stunden am Corpus
→ Access Token läuft ab
→ User wird mitten in der Arbeit ausgeloggt
→ Frustration 😠
```

---

## 🎯 Implementierungs-Priorität

### Phase 2 KURZFRISTIG: JWT Refresh Token (1 Tag)

**Backend (4-5h):**
1. Config erweitern (JWT_REFRESH_TOKEN_EXPIRES)
2. `/auth/refresh` Route erstellen
3. Login/Logout anpassen
4. Tests schreiben

**Frontend (2-3h):**
5. `fetchWithRefresh` Helper erstellen
6. In bestehende API-Calls integrieren
7. Error-Handling testen

**Testing (1-2h):**
8. Access Token Ablauf simulieren
9. Refresh Token Ablauf simulieren
10. Network-Fehler testen

---

## 🚀 Migration von bestehendem Code

### Dashboard Metrics (Beispiel)
```javascript
// VORHER:
async function loadMetrics() {
  const response = await fetch('/admin/metrics', { 
    credentials: 'same-origin' 
  });
  const data = await response.json();
  // ...
}

// NACHHER:
async function loadMetrics() {
  const response = await fetchWithRefresh('/admin/metrics');
  const data = await response.json();
  // ...
}
```

**Das war's!** Alle anderen Stellen analog anpassen.

---

## 📊 Token-Laufzeiten Empfehlung

| Token-Typ | Laufzeit | Grund |
|-----------|----------|-------|
| Access Token | 15-30 Min | Kurz = Sicher, wird oft refreshed |
| Refresh Token | 7 Tage | User bleibt 1 Woche eingeloggt |
| Remember Me (Optional) | 30 Tage | Für "Angemeldet bleiben" |

**Für CO.RA.PAN empfohlen:**
- Access: **30 Minuten** (Balance zwischen Sicherheit & UX)
- Refresh: **7 Tage** (User loggt sich max. wöchentlich ein)

---

## ❓ FAQ

**Q: Muss ich jetzt alle API-Calls anpassen?**  
A: Ja, aber einfach: `fetch()` → `fetchWithRefresh()`. Das war's!

**Q: Was wenn der Refresh-Request auch 401 gibt?**  
A: Dann ist der Refresh Token abgelaufen → Redirect zu Login.

**Q: Brauche ich eine Datenbank für Tokens?**  
A: Nein, JWT sind stateless. Optional: Blacklist für gestohlene Tokens.

**Q: Funktioniert das mit JWT-Cookies?**  
A: Ja, perfekt! Cookies werden automatisch bei `/auth/refresh` mitgesendet.

**Q: Sieht der User einen Loading-Spinner?**  
A: Nein (außer dein Original-Request dauert lange). Refresh ist <100ms.

---

## 📝 Zusammenfassung

✅ **Token-Refresh braucht KEIN Dialogfeld**  
✅ **Läuft automatisch im Hintergrund**  
✅ **User merkt nichts**  
✅ **Implementierung: ~1 Tag**  
✅ **Massiv verbesserte User Experience**

**Next Step:** Implementiere Phase 2 KURZFRISTIG aus `SECURITY_MODERNIZATION_ROADMAP.md`!
