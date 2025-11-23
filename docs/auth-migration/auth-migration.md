# Auth Migration Guide (DE)

Diese Dokumentation beschreibt schrittweise die komplette Migration des bestehenden Auth-Systems von einer passwords.env-basierten Lösung auf ein modernes, DB-basiertes Auth-System mit JWT (Access + Refresh), Token-Rotation, bcrypt/argon2id-Hashing, und Admin-Funktionalität.

Ziel: Vollständige Umstellung von passwords.env zu einer Users-Datenbanktabelle mit sicherem, getesteten, wartbarem Auth-Flow.

---

## Inhaltsverzeichnis

1. Überblick & Ziele
2. Datenbank-Scheme
3. Sicherheitsentscheidungen (Hashing, Token-Management)
4. API-Routen (komplett)
5. Dateistruktur & Beispielpfade
6. Module / Controller / Middlewares / Guards
7. Migration: Schritte & Skripte
8. Frontend-Anpassungen
9. Admin Dashboard & Management APIs
10. Tests & Testplan
11. Deployment & Operational Notes
12. Optional: Password-Reset Token Flow
13. Appendix: Beispiel-Snippets, SQL, JWT Payloads

---

## 1. Überblick & Ziele

- Entfernen von credentials aus `passwords.env`.
- Zentralisiertes Benutzer-Management in der DB.
- Sicheres Passwort-Hashing mit bcrypt oder argon2id.
- Kurzlebige Access-Tokens (JWT) 15–30 Minuten.
- Langläufer Refresh-Token (HttpOnly + Secure Cookie, 30 Tage).
- Token-Rotation bei jeder Refresh-Nutzung.
- Middleware für geschützte Routen.
- Admin-Funktionalität: Benutzer anlegen, sperren, Passwörter zurücksetzen, Rollen verwalten.
- Rate-Limiting beim Login, HTTPS zwingend.

Nächste Schritte: implementierbare Details, Migrationsskripte, Tests und Deployment-Guidance.

---

## 2. Datenbank-Schema

Empfohlene DB-Tabelle `users` (SQL-Beispiel):

```sql
CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL, -- oder email
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  must_reset_password BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

-- optional: table for refresh tokens (recommended for token rotation/blacklisting)
CREATE TABLE refresh_tokens (
  token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  expires_at TIMESTAMP NOT NULL,
  last_used_at TIMESTAMP,
  replaced_by UUID -- token_id of replacement
);
```

Hinweis: Speichere niemals den Refresh-Token im Klartext in der DB; speichere stattdessen einen Hash (z.B. SHA-256) und vergleiche Hashes bei Nutzung.

---

## 3. Sicherheitsentscheidungen

- Passwort-Hashing: bcrypt oder argon2id (stark bevorzugt argon2id wenn die Infrastruktur es erlaubt). Beispiel-werkzeuge: passlib, argon2-cffi, bcrypt.
- JWT signing: Use an environment managed secret (JWT_SECRET / PRIVATE_KEY) — never store in repo.
- Access Token: 15–30 min
- Refresh Token: 30 days
- Refresh Token Rotation: Bei jedem /auth/refresh-Call: verifiziere old refresh token, issue new access + refresh token pair, store hash of new refresh token, mark old token as rotated (or delete) — reject reuse of old token.
- Store refresh token as HttpOnly, Secure cookie only; Access token is returned in body (or Authorization header) and kept short-lived.
- Use HTTPS only in production.
- Login rate-limiting: per IP and per account (e.g., 5 attempts per 5 minutes).
- Use argumented logging and monitoring for suspicious auth events.

---

## 4. API-Routen (detailliert)

Pfad-Spezifikation inkl. Payloads und Antworten.

### /auth/login (POST)
- Beschreibung: Überprüfe Credentials aus DB, gebe Access-Token und Refresh-Cookie zurück.
- Body: { "username": "user@example.org", "password": "plaintext" }
- Response (200):
  - JSON: { "accessToken": "<JWT>", "expiresIn": 900 }
  - Cookie: Set-Cookie: refreshToken=<refresh_token>; HttpOnly; Secure; SameSite=Strict; Path=/auth/refresh; Max-Age=2592000
- Fehlercodes: 401 (invalid credentials), 423 (user locked), 429 (rate limit)

Flow:
- Find user by username/email.
- Verify is_active flag.
- Verify password using bcrypt/argon2id.
- If must_reset_password true => 403 with code "password_reset_required".
- Issue access token and refresh token; save hashed refresh token in DB (refresh_tokens) with expiry 30d.
- Set refresh cookie, return access token.

### /auth/refresh (POST)
- Beschreibung: Rotiert Refresh-Token.
- Cookie (HttpOnly): refreshToken
- Response (200): { "accessToken": "<JWT>", "expiresIn": 900 }
- Error: 401 unauthorized if token invalid/expired; 403 if token reused or blacklisted.

Flow:
- Read refresh token cookie.
- Hash token and find matching refresh_tokens entry for user.
- Verify expiry and not already replaced/used.
- Create new refresh token + hash, save; mark the old token's replaced_by to new token ID and optionally delete/expire old token.
- Issue new access token and set refresh cookie.
- Implement refresh rotation and reuse detection (if old token re-used, revoke all tokens for user and force re-login).

### /auth/logout (POST)
- Beschreibung: Revoke current refresh token (remove DB entry), clear cookie.
- Cookie: refreshToken required.
- Response: 200 OK

Flow:
- Find refresh token from cookie, delete row or mark revoked.
- Clear cookie (set Max-Age=0)

### /auth/change-password (POST)
- Beschreibung: Authenticated route; user authenticated with access token; change password.
- Body: { "oldPassword": "...", "newPassword": "..." }
- Flow:
  - Verify oldPassword, hash & store new password, set must_reset_password=false, update updated_at.
  - Optionally invalidate existing refresh tokens (delete all refresh_tokens for user).

### /auth/reset-password (POST)
- Beschreibung: Request flow for password reset.
- Body to request reset: { "email": "..." } => send email with reset link with short-lived token (e.g., 1 hour).
- Body to confirm reset: { "resetToken": "...", "newPassword": "..." }
- Implementation notes: can use DB table reset_tokens with token_hash, user_id, expires_at.

---

## 5. Dateistruktur & Beispielpfade

Die Dokumentation referenziert vorhandene Ordnerstruktur; wir schlagen diese neuen Dateien/Module vor:

Backend: (Python / Flask ähnliche Struktur; passe Pfade ggf. an)

- src/app/auth/
  - __init__.py
  - controllers.py        # Handlers für /auth/*
  - models.py             # User, RefreshToken-Modelle
  - services.py           # Token generation, password hashing
  - schemas.py            # request/response validation
  - routes.py             # blueprint /auth
  - migrations/           # SQL / alembic migrations
  - tests/
- src/app/admin/
  - users_controller.py   # /admin/users/*
  - routes.py
  - tests/
- src/app/middleware/
  - jwt_middleware.py     # prüft Access Tokens
  - rate_limit.py         # Login rate-limit
  - require_role.py       # is_admin checks

Frontend (if present):
- src/static/js/auth/
  - login.js
  - refresh.js
  - logout.js
  - admin_users.js

Config & env:
- Add ENV variables (example in .env or deployment):
  - JWT_SECRET or RSA_PRIVATE_KEY, JWT_ALGORITHM
  - ACCESS_TOKEN_EXP (900) -- optional
  - REFRESH_TOKEN_EXP (2592000)
  - BCRYPT_ROUNDS or ARGON2_CONFIG
  - START_ADMIN_USERNAME, START_ADMIN_PASSWORD (only during migration/setup)

---

## 6. Module / Controller / Middlewares / Guards

Empfohlene Implementierungen mit Verantwortlichkeiten.

### services.py
- Password hashing functions: hash_password(password) -> str, verify_password(password, hash) -> bool
- Token functions: create_access_token(user), create_refresh_token(user) -> raw token string
- Token hashing for storage: hash_refresh_token(raw) -> string (sha256)

### controllers.py
- login_controller(req) -> checks credentials, uses services, sets cookie
- refresh_controller(req) -> rotate tokens
- logout_controller(req) -> revoke refresh token
- change_password_controller(req) -> secure password change
- reset_password_controllers -> request and confirm

### models.py
- SQLAlchemy models for User and RefreshToken (or whichever ORM in project)

### middlewares/jwt_middleware.py
- Extract Bearer token from Authorization header
- Verify signature and expiry
- Load user_id from payload
- Attach user object to request for use in controllers

### middlewares/require_role.py
- Ensure current user has `admin` role or required role

### middlewares/rate_limit.py
- IP & account based rate limiting for login endpoints
- Backoff and 429 responses

---

## 7. Migration: Schritte & Skripte

Taktisches Migrations-Plan (zahme Reihenfolge):

### 0. Vorbereitungen
- Backup: DB + repo
- Add env vars for JWT secret and hashing config
- Add migrations scripts (alembic) in repo

### 1. DB-Schema erstellen
- Add `users` and `refresh_tokens` Tabelle mit migration

### 2. Erstelle Start-Admin (temporär)
- Skript: read START_ADMIN_USERNAME and START_ADMIN_PASSWORD from environment, hash password, insert into users.

### 3. Migrate existing users from passwords.env
- Parse `passwords.env` file
- For each entry, create DB user with default role (e.g., admin or user depending on original usage), set password_hash to bcrypt/argon2id(hash) of the plain password.
- For users that are already in DB, skip/merge.

### 4. Update codebase: Begin optional parallel path
- Add new `src/app/auth` code (controllers, models, services, routes, middleware)
- Keep current `passwords.env` code in place, but add feature flag or config switch (AUTH_BACKEND=env/db) to choose auth backend.

### 5. Tests
- Add comprehensive tests for login, refresh, logout, reset, admin endpoints.

### 6. Cut-over
- Switch AUTH_BACKEND to 'db' in config (deploy env variable change)
- Remove passwords.env user lookup code a few deploys later after monitoring

### 7. Cleanup
- Remove `passwords.env` usage entirely and remove file from repo
- Remove start-admin password env vars

Checklist for migration script:
- Validate migration created new DB rows and hashed passwords
- Preserve is_active state where possible
- If passwords.env lacks emails, map username accordingly

---

## 8. Frontend-Anpassungen

- Login form: send to POST /auth/login, on success store access token in memory / app state, refresh cookie handled by browser.
- Requests to protected APIs: attach Authorization: Bearer <accessToken>
- Implement automatic token refresh: when access token expires, call /auth/refresh. Handle 401 gracefully and redirect to login.
- Logout: call /auth/logout and clear client-side stored access token.
- Admin panel: add pages for user creation, listing, role changes, activate/deactivate users, reset passwords.

---

## 9. Admin Dashboard & Management APIs

### Endpoints under /admin/users

- GET /admin/users (list, filter, pagination)
- GET /admin/users/:id (detail)
- POST /admin/users (create) { username, password, role }
- PATCH /admin/users/:id (partial update) { role, is_active, must_reset_password }
- POST /admin/users/:id/reset-password (admin set new password)
- DELETE /admin/users/:id (delete user)

All admin endpoints must be protected by require_role('admin') middleware.

---

## 10. Tests & Testplan

Integration / E2E tests to implement:

- Login success with valid user.
- Login fail with invalid password.
- Login fail when is_active=false.
- Access protected endpoint with valid Access Token -> 200.
- Access with missing token -> 401.
- Access with expired token -> 401.
- Refresh with valid Refresh Token -> new Access + Refresh token and cookie is updated.
- Refresh with reused old Refresh Token -> revoke all tokens for user, require re-login.
- Logout invalidates refresh token.
- Change password invalidates refresh tokens.
- Admin create user, change role, lock/unlock user.
- Rate limiting test: more than N attempts -> 429.

### Example tests mapping to repo
- Add/modify tests in `tests/test_optional_auth_behavior.py` and `tests/test_...` or new `tests/test_auth_flow.py`.

---

## 11. Deployment & Operational Notes

- Ensure HTTPS is enforced (reverse proxy or Flask set-ups) to protect cookies.
- Ensure same-site policy for refresh cookie (SameSite=Strict recommended) unless cross-site auth is required.
- Rotate JWT signing key periodically (with careful support for validating old tokens if necessary) — maintain key versioning.
- Access tokens short-lived so if compromised impact is limited.
- Refresh tokens are long-lived and must be protected; store them in HttpOnly cookies and use token rotation.
- Start Admin account: create via bootstrapping script executed only once with ephemeral env vars, then remove env vars.

Cookie example:
Set-Cookie: refreshToken=<token>; HttpOnly; Secure; Path=/auth/refresh; Max-Age=2592000; SameSite=Strict; Domain=example.com

---

## 12. Optional: Password Reset & Tokens

- Table `reset_tokens` (token_hash, user_id, expires_at, used)
- Flow: request -> send email with link -> confirm -> verify token hash and expiry -> set new password and mark used=true
- Limit reset token lifetime (1 hour) and rate-limit requests

---

## 13. Appendix: Beispiel-Snippets und Payloads

### JWT Access token payload (example)

```json
{
  "sub": "user_id-uuid",
  "username": "alice@example.org",
  "role": "admin",
  "iat": 1694490412,
  "exp": 1694491312
}
```

### Refresh token storage scheme (DB)
- Store hash: sha256(refreshTokenRaw) -> token_hash
- When verifying refresh token: compute sha256(candidate) and compare with token_hash

### Beispiel: Token-Erzeugung (Python pseudocode)

```python
# services.py
import time
from datetime import datetime, timedelta
import jwt

ACCESS_EXP = int(os.getenv('ACCESS_TOKEN_EXP', 900))
REFRESH_EXP = int(os.getenv('REFRESH_TOKEN_EXP', 2592000))
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALG = os.getenv('JWT_ALG', 'HS256')

def create_access_token(user):
    now = int(time.time())
    payload = {
        'sub': str(user.user_id),
        'username': user.username,
        'role': user.role,
        'iat': now,
        'exp': now + ACCESS_EXP
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def create_refresh_token():
    return token_hex(64)  # 128 hex chars ~ 64 bytes
```

### Beispiel Middleware-Flow

1. Extract Authorization header `Bearer <token>`.
2. Verify signature & `exp`.
3. Load user from DB.
4. Attach `request.user` or abort 401.

---

## 14. Detaillierte Dateipfade (Projekt-spezifisch)

Konkrete Pfade im Repo (Vorschläge, bitte anpassen):

- `src/app/auth/routes.py` -> define blueprint and register under `/auth`
- `src/app/auth/controllers.py` -> login, refresh, logout, reset, change-password
- `src/app/auth/models.py` -> User, RefreshToken SQLAlchemy models
- `src/app/auth/services.py` -> hashing and token helpers
- `src/app/auth/tests/test_auth_flow.py`
- `src/app/admin/users_controller.py` -> /admin/users routes
- `src/app/middleware/jwt_middleware.py`
- `src/app/middleware/rate_limit.py`

---

## 15. Removing old components

- Identify code paths where `passwords.env` is read. Typical places: login functions, config loader or simple custom auth modules.
- Add a feature-flag controlled deprecation stage: AUTH_BACKEND defaults to 'env' or 'db'. Step-by-step: enable 'db' in pre-prod, smoke tests, then remove 'env' branch.

---

## 16. Acceptance Criteria & Rollout Plan

- Tests pass for all auth flows.
- Smoke tests for admin operations.
- Monitor suspicious failures and login rates for first 72h after switch.
- Plan rollback: enable `AUTH_BACKEND=env` for immediate rollback (still keep environment code until safe to remove). Keep a backup of `passwords.env` for 7 days.

---

## 17. Troubleshooting & FAQ

Q: How to handle legacy API tokens stored in other services?
A: Provide a one-time migration path: create users with hashed passwords using old tokens if mapping possible. Otherwise, invalidate legacy tokens and prompt users to reset.

Q: How to test locally without HTTPS?
A: For dev: allow insecure cookies only with `secure=False` and using sameSite='Lax'. For production `secure=True` and HTTPS mandatory.

---

## 18. Abschluss

Diese Anleitung soll als komplette, umsetzbare Roadmap dienen, um `passwords.env` sicher zu ersetzen durch eine DB-basierte Auth-Lösung mit JWT, Refresh-Token-Rotation, Admin-Management und sicheren Deployment-Standards.

Viel Erfolg bei der Migration!
