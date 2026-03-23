# Sicherheit & Authentication

**Scope:** Auth-Flow, Sessions, JWT, CSRF, Rollen  
**Source-of-truth:** `src/app/auth/`, `src/app/config/__init__.py`, `src/app/__init__.py`

## Auth-Architektur

### Überblick

Die Anwendung nutzt **JWT-basierte Authentication** mit folgenden Komponenten:

```
┌─────────────────────────────────────────────────────────────┐
│  Authentication System                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │ JWT Tokens      │  │ Database         │  │ Middleware│ │
│  │ - Access Token  │  │ - users          │  │ - Auth    │ │
│  │ - Refresh Token │  │ - refresh_tokens │  │ - CSRF    │ │
│  │ - CSRF Token    │  │ - reset_tokens   │  │ - Role    │ │
│  └─────────────────┘  └──────────────────┘  └───────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Technologie:**
- **Flask-JWT-Extended:** JWT-Token-Verwaltung
- **SQLAlchemy:** User-Datenbank (PostgreSQL/SQLite)
- **Argon2:** Password Hashing (Fallback: bcrypt)
- **Cookies + Headers:** Token-Transport (Dual Mode)

---

## Datenmodell

### User Table

**Datei:** `src/app/auth/models.py`

```python
class User(Base):
    __tablename__ = "users"
    
    # Identity
    id: str                      # UUID (Primary Key)
    username: str                # Unique, Required
    email: str | None            # Optional
    password_hash: str           # Argon2/bcrypt Hash
    
    # Role & Status
    role: str                    # "user", "editor", "admin"
    is_active: bool              # Account enabled?
    must_reset_password: bool    # Force password change?
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
    
    # Access Control
    access_expires_at: datetime | None  # Temporary access expiry
    valid_from: datetime | None         # Account not valid before
    
    # Security
    login_failed_count: int             # Failed login attempts
    locked_until: datetime | None       # Temporary lock after too many failures
    
    # Soft Delete (DSGVO)
    deleted_at: datetime | None
    deletion_requested_at: datetime | None
    
    # UI
    display_name: str | None
```

**Migration:** `migrations/0001_create_auth_schema_postgres.sql`

### Refresh Tokens

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    token_id: str                # UUID (Primary Key)
    user_id: str                 # Foreign Key → users
    token_hash: str              # SHA-256 Hash des Tokens
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None  # Manual Revocation
    user_agent: str | None       # Browser/Client Info
    ip_address: str | None       # IP bei Erstellung
    replaced_by: str | None      # Token Rotation (ID des neuen Tokens)
```

**Rotation:** Jeder Refresh erzeugt neues Token, altes wird revoked.

---

## Authentication Flow

### 1. Login

**Request:** `POST /auth/login`

```json
{
  "username": "admin",
  "password": "secure-password"
}
```

**Server-Side (Pseudocode):**
```python
# src/app/auth/services.py → authenticate_user()
user = db.query(User).filter_by(username=username).first()

# 1. Check: User existiert?
if not user or user.deleted_at:
    return {"error": "Invalid credentials"}

# 2. Check: Account gesperrt?
if user.locked_until and user.locked_until > now():
    return {"error": "Account temporarily locked"}

# 3. Check: Passwort korrekt?
if not verify_password(password, user.password_hash):
    user.login_failed_count += 1
    if user.login_failed_count >= 5:
        user.locked_until = now() + timedelta(minutes=15)
    return {"error": "Invalid credentials"}

# 4. Check: Account aktiv?
if not user.is_active:
    return {"error": "Account disabled"}

# 5. Success: Token generieren
access_token = create_access_token(identity=user.username, 
                                    additional_claims={"role": user.role})
refresh_token = create_refresh_token(identity=user.username)

# 6. Refresh Token in DB speichern
save_refresh_token(user.id, refresh_token)

# 7. Tokens in Cookies setzen
set_access_cookies(response, access_token)
set_refresh_cookies(response, refresh_token)

# 8. Audit-Log
user.last_login_at = now()
user.login_failed_count = 0
db.commit()
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "username": "admin",
    "role": "admin",
    "display_name": "Administrator"
  }
}
```

**Cookies gesetzt:**
- `access_token_cookie` (HTTPOnly, Secure, SameSite=Lax)
- `refresh_token_cookie` (HTTPOnly, Secure, SameSite=Lax)
- `csrf_access_token` (nicht HTTPOnly, für JS-Access)
- `csrf_refresh_token` (nicht HTTPOnly)

---

### 2. Geschützte Routes

**Request:** `GET /admin/users` (mit Cookies)

**Server-Side:**
```python
# src/app/__init__.py → before_request Hook
@app.before_request
def _set_auth_context():
    # Skip für Static Assets
    if request.path.startswith("/static/"):
        return
    
    # JWT aus Cookie/Header lesen (optional=True → keine Exception wenn fehlt)
    verify_jwt_in_request(optional=True)
    
    # Identity extrahieren
    g.user = get_jwt_identity()  # z.B. "admin"
    
    # Role aus JWT Claims
    jwt_data = get_jwt()
    g.role = Role[jwt_data.get("role", "user")] if g.user else None
```

**Route Handler:**
```python
# src/app/routes/admin_users.py
from ..auth import require_role, Role

@admin_users_bp.route("/users")
@require_role(Role.admin)  # Custom Decorator
def list_users():
    # Nur erreichbar wenn g.role == Role.admin
    users = auth_services.list_all_users()
    return render_template("admin/users.html", users=users)
```

**Decorator-Implementierung:**
```python
# src/app/auth/decorators.py
def require_role(required_role: Role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. JWT prüfen (wirft 401 wenn fehlt/ungültig)
            verify_jwt_in_request()
            
            # 2. Role aus g.role oder JWT Claims
            user_role = g.role or Role[get_jwt().get("role", "user")]
            
            # 3. Role-Check
            if user_role.value < required_role.value:
                abort(403)  # Forbidden
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

---

### 3. Token Refresh

**Problem:** Access Token läuft ab (Default: 1h)

**Lösung:** Automatischer Refresh via JavaScript

**Client-Side:**
```javascript
// static/js/auth-setup.js
async function refreshAccessToken() {
  const response = await fetch("/auth/refresh", {
    method: "POST",
    headers: {
      "X-CSRF-TOKEN": getCookie("csrf_refresh_token")
    }
  });
  
  if (response.ok) {
    console.log("Access token refreshed");
  } else {
    window.location.href = "/auth/login";
  }
}

// Alle 50 Minuten refreshen (Access Token: 60min)
setInterval(refreshAccessToken, 50 * 60 * 1000);
```

**Server-Side:**
```python
# src/app/routes/auth.py
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)  # Erfordert Refresh Token
def refresh():
    current_user = get_jwt_identity()
    
    # Neues Access Token generieren
    access_token = create_access_token(identity=current_user)
    
    # In Cookie setzen
    response = jsonify({"message": "Token refreshed"})
    set_access_cookies(response, access_token)
    
    return response, 200
```

**Token Rotation:**
```python
# Optional: Refresh Token rotieren (erhöhte Sicherheit)
new_refresh_token = create_refresh_token(identity=current_user)
set_refresh_cookies(response, new_refresh_token)

# Altes Token in DB als "replaced" markieren
old_token_id = get_jwt()["jti"]
revoke_refresh_token(old_token_id, replaced_by=new_refresh_token_id)
```

---

### 4. Logout

**Request:** `POST /auth/logout`

**Server-Side:**
```python
# src/app/routes/auth.py
@auth_bp.route("/logout", methods=["POST"])
def logout():
    # Optional: Refresh Token in DB revoken
    if request.cookies.get("refresh_token_cookie"):
        try:
            verify_jwt_in_request(refresh=True)
            token_id = get_jwt()["jti"]
            revoke_refresh_token(token_id)
        except:
            pass  # Token ungültig, egal
    
    # Cookies löschen
    response = jsonify({"message": "Logged out"})
    unset_jwt_cookies(response)
    
    return response, 200
```

**Client-Side:**
```javascript
// static/js/logout.js
async function logout() {
  await fetch("/auth/logout", {
    method: "POST",
    headers: {
      "X-CSRF-TOKEN": getCookie("csrf_access_token")
    }
  });
  
  window.location.href = "/";
}
```

---

## Rollen-System

### Rollen-Hierarchie

```python
# src/app/auth/__init__.py
class Role(Enum):
    user = 1      # Basis-User (Lesezugriff)
    editor = 2    # Editor (kann Transkripte bearbeiten)
    admin = 3     # Admin (volle Kontrolle)
```

**Hierarchie:** `admin > editor > user`

### Zugriffsmatrix

| Feature | User | Editor | Admin | Route |
|---------|------|--------|-------|-------|
| **Public** |
| Startseite | ✅ | ✅ | ✅ | `/` |
| Impressum, Privacy | ✅ | ✅ | ✅ | `/impressum`, `/privacy` |
| Login | ✅ | ✅ | ✅ | `/auth/login` |
| **Search** |
| Korpussuche | ✅ | ✅ | ✅ | `/search` |
| CQL/Advanced | ✅ | ✅ | ✅ | `/search/advanced` |
| Export | ✅ | ✅ | ✅ | `/stats/export` |
| **Audio** |
| Player | ✅ | ✅ | ✅ | `/audio/<doc>/<seg>` |
| **Visualisierung** |
| Atlas | ✅ | ✅ | ✅ | `/atlas` |
| Stats | ✅ | ✅ | ✅ | `/stats` |
| **Editor** |
| JSON-Editor | ❌ | ✅ | ✅ | `/editor` |
| Transkript bearbeiten | ❌ | ✅ | ✅ | `/editor/save` |
| **Admin** |
| User Management | ❌ | ❌ | ✅ | `/admin/users` |
| Analytics Dashboard | ❌ | ❌ | ✅ | `/analytics/dashboard` |
| Audit Logs | ❌ | ❌ | ✅ | `/admin/logs` |

**Implementierung:**
```python
# Öffentlich (keine Decorator)
@public_bp.route("/")
def index():
    ...

# User (implizit via @jwt_required)
@corpus_bp.route("/search")
@jwt_required()
def search():
    ...

# Editor
@editor_bp.route("/")
@require_role(Role.editor)
def editor_index():
    ...

# Admin
@admin_users_bp.route("/users")
@require_role(Role.admin)
def list_users():
    ...
```

---

## CSRF Protection

### Forms (POST)

**Template:**
```jinja2
<form method="POST" action="/auth/login">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <input type="text" name="username">
  <input type="password" name="password">
  <button type="submit">Login</button>
</form>
```

**Server-Side:**
```python
# Flask-WTF (optional) oder manuell
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

### AJAX (with JWT)

**Client-Side:**
```javascript
fetch("/api/data", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-TOKEN": getCookie("csrf_access_token")
  },
  body: JSON.stringify({...})
})
```

**Server-Side:**
```python
# Flask-JWT-Extended prüft automatisch X-CSRF-TOKEN Header
# wenn JWT_COOKIE_CSRF_PROTECT = True
```

---

## Password Security

### Hashing

**Argon2 (empfohlen):**
```python
# src/app/auth/services.py
from passlib.hash import argon2

def hash_password(password: str) -> str:
    return argon2.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return argon2.verify(password, hash)
```

**Config:**
```python
# src/app/config/__init__.py
AUTH_ARGON2_TIME_COST = 2        # Iterations
AUTH_ARGON2_MEMORY_COST = 102400  # 100 MB
AUTH_ARGON2_PARALLELISM = 4       # Threads
```

**Fallback (bcrypt):**
```python
# Falls argon2-cffi nicht verfügbar
from passlib.hash import bcrypt
```

### Password Reset (optional)

**Hinweis:** Aktuell nicht implementiert. Placeholder in `models.py` vorhanden (`ResetToken`).

**Würde erfordern:**
1. Email-Service (SMTP)
2. Reset-Token-Generierung
3. Reset-Route (`/auth/reset/<token>`)

---

## Session Security

### Cookie-Settings

**Produktion:**
```python
SESSION_COOKIE_SECURE = True      # Nur HTTPS
SESSION_COOKIE_HTTPONLY = True    # JS-Access verhindern
SESSION_COOKIE_SAMESITE = "lax"   # CSRF-Schutz

JWT_COOKIE_SECURE = True
JWT_COOKIE_CSRF_PROTECT = True
JWT_COOKIE_SAMESITE = "Lax"
```

**Development:**
```python
SESSION_COOKIE_SECURE = False     # HTTP erlauben
JWT_COOKIE_SECURE = False
JWT_COOKIE_CSRF_PROTECT = False   # vereinfacht Testen
```

### Token-Lifetime

| Token | Lifetime | Zweck |
|-------|----------|-------|
| Access Token | 1h | Kurzlebig, für API-Requests |
| Refresh Token | 7d | Langlebig, für Token-Refresh |
| CSRF Token | 1h | Gebunden an Access Token |

**Config:**
```python
ACCESS_TOKEN_EXP = 3600     # 1 Stunde
REFRESH_TOKEN_EXP = 604800  # 7 Tage
```

---

## Security Headers

**Automatisch hinzugefügt (via `register_security_headers()`):**

```python
# src/app/__init__.py
@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Optional: CSP (Content Security Policy)
    # response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## Soft Delete & DSGVO

### Soft Delete

```python
# src/app/auth/services.py
def soft_delete_user(user_id: str):
    user = db.query(User).get(user_id)
    user.deleted_at = datetime.utcnow()
    user.deletion_requested_at = datetime.utcnow()
    db.commit()
```

### Anonymisierung

**Nach X Tagen (Config: `AUTH_ACCOUNT_ANONYMIZE_AFTER_DAYS = 30`):**

```python
# scripts/anonymize_old_users.py
def anonymize_soft_deleted_users_older_than(days: int):
    cutoff = datetime.utcnow() - timedelta(days=days)
    users = db.query(User).filter(
        User.deleted_at < cutoff,
        User.email.isnot(None)  # Nur wenn Email vorhanden
    ).all()
    
    for user in users:
        user.username = f"deleted_{user.id[:8]}"
        user.email = None
        user.password_hash = "DELETED"
        user.display_name = None
    
    db.commit()
    return len(users)
```

**Cron Job:**
```bash
# Täglich um 2 Uhr
0 2 * * * cd /app && flask auth-anonymize
```

---

## Audit Logging (planned)

**Hinweis:** Aktuell keine detaillierten Audit-Logs implementiert. Kann erweitert werden:

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: str
    user_id: str
    action: str       # "login", "logout", "user_created", etc.
    resource: str     # "user", "transcript", etc.
    timestamp: datetime
    ip_address: str
    user_agent: str
    details: str      # JSON
```

---

## Extension Points

**Neue Auth-Provider (OAuth, SAML):**
1. Route in `src/app/routes/auth.py` hinzufügen
2. Provider-spezifische Library integrieren (z.B. `authlib`)
3. Callback-Route für Token-Exchange
4. User-Provisioning in DB

**2FA (Two-Factor Auth):**
1. Neue Tabelle: `user_totp_secrets`
2. TOTP-Library (z.B. `pyotp`)
3. Login-Flow erweitern (2. Schritt nach Password)

**API Keys (für externe Clients):**
1. Neue Tabelle: `api_keys`
2. Decorator: `@require_api_key()`
3. Header: `X-API-Key: <key>`
