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

## Datenschutz (DSGVO) — Anforderungen & technische Umsetzung

Diese Sektion ergänzt die technische Migration um die erforderlichen DSGVO-Maßnahmen. Alle Punkte sind als umsetzbare Hinweise formuliert und gehören zwingend zur Implementierung.

### 1.1 Mindest‑Datenschutzmaßnahmen (technisch umsetzbar)

- Zweckbindung: Jede gespeicherte personenbezogene Information muss einen klaren Zweck haben (Authentifizierung, Autorisierung, Audit, Support). In der DB/Modelldokumentation muss für jedes Feld ein Zweckfeld dokumentiert werden.
- Datenminimierung: Speichere nur die minimal notwendigen Felder (vollständige Feldliste siehe Datenmodell-Abschnitt). Keine Tracking-Daten in Auth-Tabellen, keine Klartext-Passwörter, keine unnötigen personenbezogenen Metadaten.
- Speicherdauer (Richtwerte):
  - Nutzerkonto-Daten (users) — solange das Konto aktiv ist und maximal 10 Jahre nach Inaktivität (konfigurierbar).
  - Auth-Logs / Sicherheitslogs — 1 Jahr (für forensische Zwecke), danach archivieren oder löschen.
  - Refresh-Tokens (DB): standardmäßig 30 Tage plus Rotation-Audit (keine längere Speicherung im Klartext), entsorgen / anonymisieren 90 Tage nach Widerruf.
  - Password-Reset-Tokens: sehr kurzlebig (1 Stunde), werden nach Benutzung oder Ablauf sofort ungültig und spätestens nach 7 Tagen gelöscht.
  - Account-Löschung / Soft-Delete: Konten werden sofort soft-gelöscht (deleted_at gesetzt) und nach 30 Tagen anonymisiert (oder früher, abhängig von rechtlicher Aufbewahrungspflicht).
- Lösch- und Anonymisierungsregeln:
  - Soft-Delete: `deleted_at` + `is_active=false` + `login_disabled=true` sofort bei Löschanfrage.
  - Nach Frist X (konfigurierbar, z. B. 30 Tage) Pseudonymisierung/Anonymisierung aller personenbezogenen Felder (username, email) — ersetze durch hashed-placeholder (z. B. `deleted-{user_id}@example.invalid`) und entferne sensible Audit-Felder soweit möglich.
  - Audit-Logs: prüfen, ob gesetzliche Aufbewahrungspflichten einem anonymisieren/zurückhalten entgegenstehen — implementiere getrennte Archiv-Speicherplätze und Aufbewahrungsfristen.
- Backups:
  - Backups müssen verschlüsselt gespeichert werden (AES-256). Keine Speicherung sensitiver Klartext-Backups in unverschlüsselten Speicherbereichen.
  - Zugriff auf Backups ist auf einen gekapselten Ops/Infra-Admin-Account beschränkt (Principle of Least Privilege).
  - Retention: Backups automatisch rotieren/überschreiben — beispielsweise tägliche Backups mit 30 Tagen Aufbewahrung, Wochen- und Monats-Backups nach Bedarf.
- Transport & TLS: Alle Endpunkte in Produktion müssen HTTPS erzwingen (redirect und HSTS). Interne API-Kommunikation ebenfalls TLS-gesichert.
- Reset-Tokens Schutz: Reset-Tokens sind einmalig, random, kurzlebig (z. B. 3600s) und werden nur als Hash (SHA-256) in der DB gespeichert. E-Mail enthält niemals ein direkter Link mit Klartext-Passwort.
- Rate-Limiting & Lockout: Rate-Limit pro IP und pro Account (z. B. 5 Fehlversuche in 10 Minuten) plus inkrementeller Backoff; bei Verdacht auf Brute-Force Aktionskette (temporary lock + alert).

### 1.2 Betroffenenrechte (Art. 15–20 DSGVO) — techn. Spezifikation

Die Implementierung muss APIs und Frontend-Komponenten bereitstellen, die die Ausübung der DSGVO-Rechte erlauben:

- Auskunftsrecht (Art. 15):
  - API: `GET /account/data-export` (auth-required)
  - Response: JSON mit allen personenbezogenen Feldern, Audit-Einträgen (letzter Login, created_at, deleted_at), Verarbeitungszwecken und ggf. Löschfristen. Maximum: 1 MB, komprimierbar.
  - Intern: Aufruf führt zu Erzeugung eines Download-Token (einmalig gültig, 15 Minuten) und POST-Export-Job falls Dataset groß.

- Recht auf Berichtigung (Art. 16):
  - UI: `/account/profile` mit editierbaren Feldern (siehe Section Enduser-Flows).
  - API: `PATCH /account/profile` — validiert Felder, schreibt `updated_at`, versioniert kritische Änderungen (z. B. email change -> email_verified=false). Audit-Log-Eintrag.

- Recht auf Löschung (Art. 17):
  - API: `POST /account/delete` — erzeugt Soft-Delete (`deletion_requested_at`, `deleted_at` optionally on timeout) and führt folgende Schritte aus:
    - Revoke all refresh tokens for user
    - Remove PII from active tables only at anonymization time, keep audit footprints as needed
    - Queue background job to perform irreversible anonymization after configurable retention (e.g., 30 days)
  - Endpoint requires re-auth (fresh access token) to prevent abuse.

- Recht auf Datenportabilität (Art. 20):
  - Implement via `GET /account/data-export` returning a JSON file that the user can download.
  - Format: JSON + CSV (optional) with clear field mapping; include a schema version number.

- Einschränkung der Verarbeitung (Art. 18):
  - System-support for user-level processing restriction: `PATCH /account/profile` or `POST /account/restrictions` -> set `is_active=false` or set `locked_until` to a requested timestamp. Admin must be able to mark `restriction_requested` and document reason.

### 1.3 Aktualisierung der Datenschutzerklärung (privacy policy)

Forderung: Die Datenschutzerklärung muss die folgenden, präzise Textbausteine enthalten (vorformuliert):

- Beschreibung der personenbezogenen Daten, die für Auth/Account gespeichert werden: username / email, password_hash, role, is_active, must_reset_password, access_expires_at, valid_from, last_login_at, login_failed_count, locked_until, deleted_at, deletion_requested_at, sowie Refresh-/Reset-Token-Hashes.
- Verarbeitungszwecke: Authentifizierung, Autorisierung, Security/Audit, Support, rechtliche Aufbewahrung.
- Aufbewahrungsfristen: klare, präzise Fristen für accounts (in days/years), logs, tokens und backups. Beispieltext: "Account-Daten werden solange gespeichert wie das Konto aktiv ist. Nach Löschung werden personenbezogene Daten nach 30 Tagen anonymisiert.".
- Cookies: technische Notwendigkeit bei Refresh-Cookie (HttpOnly, Secure) und CSRF-Token. Dokumentiere: keine Tracking-/Marketing-Cookies durch die App selbst -> daher kein Cookie-Banner notwendig für diese Applikation, nur eine klare Erwähnung, welche technisch notwendigen Cookies gesetzt werden.
- Betroffenenrechte: erkläre, wie Nutzer Auskunft, Berichtigung, Löschung, Einschränkung und Datenportabilität ausüben können (Web-Aufruf/Support Email). Links zu `GET /account/data-export` und Lösch-Buttons erwähnen.

Bei Unsicherheiten oder lokalen Rechtsvorgaben (z. B. Archivpflichten) bitte juristische Prüfung hinzuzuziehen.


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
  updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
  -- Neue Felder zur Steuerung / Audit und Security
  access_expires_at TIMESTAMP NULL DEFAULT NULL, -- optional: Konto zeitlich begrenzt
  valid_from TIMESTAMP NULL DEFAULT NULL, -- Konto aktiv erst ab diesem Datum
  last_login_at TIMESTAMP NULL DEFAULT NULL, -- Timestamp letzte erfolgreiche Auth
  login_failed_count INTEGER NOT NULL DEFAULT 0, -- Zähler für fehlgeschlagene Logins
  locked_until TIMESTAMP NULL DEFAULT NULL, -- Wenn gesetzt: temporär gesperrt bis zu diesem Zeitpunkt
  deleted_at TIMESTAMP NULL DEFAULT NULL, -- Soft-delete: Zeitpunkt der Löschung
  deletion_requested_at TIMESTAMP NULL DEFAULT NULL -- Zeitpunkt der Nutzer-Löschanfrage
);

-- optional: table for refresh tokens (recommended for token rotation/blacklisting)
CREATE TABLE refresh_tokens (
  token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  expires_at TIMESTAMP NOT NULL,
  last_used_at TIMESTAMP NULL DEFAULT NULL,
  revoked_at TIMESTAMP NULL DEFAULT NULL, -- Zeitpunkt der manuellen/automatischen Widerrufs
  user_agent TEXT NULL DEFAULT NULL, -- optional: for logging/abuse detection
  ip_address TEXT NULL DEFAULT NULL,
  replaced_by UUID NULL -- token_id of replacement
);
```

Hinweis: Speichere niemals den Refresh-Token im Klartext in der DB; speichere stattdessen einen Hash (z.B. SHA-256) und vergleiche Hashes bei Nutzung.

### Feld-Beschreibung & Verhalten

Kurze Hinweise, wann die Felder erzeugt oder geprüft werden:

- user_id: Primärschlüssel, bei Erstellung gesetzt.
- username: bei Erstellung gesetzt; für Queries/Lookups verwendet.
- password_hash: bei Erstellung und bei Passwort-Änderung gesetzt; bei Login gegen eingegebenes Passwort geprüft.
- role: bei Erstellung gesetzt; geprüft bei RBAC-Checks (Admin-Routen).
- is_active: geprüft bei Login und Refresh; Admin kann setzen.
- must_reset_password: geprüft nach erfolgreichem Auth; wenn TRUE, wird normaler Zugriff verweigert und Nutzer zur PW-Änderung weitergeleitet. Wird auf FALSE gesetzt nach Reset/Change.
- created_at / updated_at: Audit-Felder, updated_at bei jeder Änderung des Nutzerobjekts aktualisieren.
- access_expires_at: wenn gesetzt, verhindert Login und Refresh nach dem Zeitpunkt; geprüft bei Login/Refresh.
- valid_from: wenn gesetzt, verhindert Login vor diesem Zeitpunkt.
- last_login_at: bei erfolgreichem Login gesetzt; hilfreich für Audit/Reporting.
- login_failed_count: erhöht bei Fehlversuchen; bei Überschreitung einer Schwelle (z.B. 5) kann locked_until gesetzt werden.
- locked_until: wenn gesetzt und > now(), Login verweigern mit `account_locked`-Fehler.
 - locked_until: wenn gesetzt und > now(), Login verweigern mit `account_locked`-Fehler.
 - deleted_at: wenn gesetzt => Konto ist soft-deleted; Login verweigern; Tokens widerrufen; spätere Anonymisierung möglich.
 - deletion_requested_at: Zeitpunkt, zu dem der Nutzer die Löschung angefordert hat; dient zur Rückverfolgbarkeit und Fristenberechnung.

Für `refresh_tokens`:

- token_id: Primärschlüssel, bei Erzeugung gesetzt.
- token_hash: Hash des Refresh-Tokens; niemals das Klartext-Token speichern.
- created_at / expires_at: bei Erzeugung gesetzt; `expires_at` verhindert Nutzung nach Ablauf.
- last_used_at: bei jeder erfolgreichen Nutzung aktualisiert.
- revoked_at: Markiert Widerruf; geprüft bei /auth/refresh.
- user_agent / ip_address: optional zur Forensik; können in Alerts verwendet werden.
- replaced_by: bei Rotation auf neuen Token zeigen; dienen zur Erkennung von Reuse-Versuchen.

---

### Migrationsanweisungen (SQL / Alembic)

Die Migration des Schemas und die sichere Übernahme bestehender Nutzerkonten erfordert mehrere Schritte. Die folgenden Befehle und Skript‑Skizzen sind als technische Vorlage gedacht.

1) Versioniere & teste in einer Staging-DB

 - Erzeuge eine Alembic-Revision und prüfe die DDL-Schritte in einer Staging-Instanz bevor du in Production upgradest.

2) Beispiel-SQL / DDL (Postgres)

```sql
ALTER TABLE users ADD COLUMN access_expires_at TIMESTAMP NULL DEFAULT NULL;
ALTER TABLE users ADD COLUMN valid_from TIMESTAMP NULL DEFAULT NULL;
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP NULL DEFAULT NULL;
ALTER TABLE users ADD COLUMN login_failed_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP NULL DEFAULT NULL;
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL DEFAULT NULL;
ALTER TABLE users ADD COLUMN deletion_requested_at TIMESTAMP NULL DEFAULT NULL;

-- Refresh/reset token tables
CREATE TABLE IF NOT EXISTS refresh_tokens (
  token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  expires_at TIMESTAMP NOT NULL,
  last_used_at TIMESTAMP NULL DEFAULT NULL,
  revoked_at TIMESTAMP NULL DEFAULT NULL,
  user_agent TEXT NULL DEFAULT NULL,
  ip_address TEXT NULL DEFAULT NULL,
  replaced_by UUID NULL
);

CREATE TABLE IF NOT EXISTS reset_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  expires_at TIMESTAMP NOT NULL,
  used_at TIMESTAMP NULL DEFAULT NULL
);
```

3) Migration von `passwords.env` in DB

 - Entwickle ein idempotentes Script (`scripts/migrate_passwords_env.py`) welches:
   - `passwords.env` parst
   - für jedes Konto einen `users`-Datensatz anlegt (username/email)
   - das Klartextpasswort mit Argon2id/Bcrypt hasht
   - evtl. `must_reset_password=true` setzt, wenn Policy erforderlich
 - Prüfe und dokumentiere die Anzahl migrierter Accounts und mögliche Deltas (z. B. gleiche Emails mehrfach).

4) Bootstrapping des ersten Admins

 - Script `scripts/create_initial_admin.py` liest `START_ADMIN_USERNAME` und `START_ADMIN_PASSWORD` aus Umgebungsvariablen (CI secrets), legt den Admin an, setzt `must_reset_password=true` und schreibt einen Eintrag im Audit-Log.

5) Tests & Rollback

 - Teste den kompletten Migrationspfad in Staging inklusive Login, Refresh, Reset-Flow.
 - Fertige vor Live-Migration ein Backup an (verschlüsselt) und dokumentiere Restore-Schritte.

6) Nach der Migration

 - Schalte die Feature-Flag `AUTH_BACKEND=db` in Staging on, teste Verfügbarkeit, erst dann in Prod.
 - Entferne `passwords.env`-abhängige Pfade erst wenn alle Backups, Migrationsergebnisse und Tests bestätigt wurden.


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

### Token-System, Middleware-Checks & Security Rules (detailliert)

1) Token lifecycles

- Access Token:
  - Type: JWT (signed)
  - Lifetime: default 15–30 minutes (ACCESS_TOKEN_EXP config)
  - Storage: do NOT store in localStorage; keep in memory on web clients, or use secure per-platform storage for mobile.
  - Claims: `sub` (user_id), `role`, `is_active`, `must_reset_password`, `iat`, `exp`, `jti` (optional for short lived revocation support).

- Refresh Token:
  - Type: opaque random token (at least 64 bytes of entropy), stored as an HttpOnly+Secure cookie, `SameSite=Strict`, Path=/auth/refresh.
  - Lifetime: 30 days by default (REFRESH_TOKEN_EXP config).
  - Storage in DB: only store a hash of the token (SHA-256) in `refresh_tokens.token_hash` and record `created_at`, `expires_at`, `user_agent`, `ip_address`.
  - Rotation: on `/auth/refresh`, issue new refresh token (raw) and store its hash as a new DB row with `replaced_by` pointers. Mark old token `replaced_by` to new token_id and set `last_used_at`.
  - Reuse detection: If an old token is presented when it's already `replaced_by` or `revoked_at` is set, treat as reuse attack — revoke all refresh tokens for user and force re-auth.

2) Token invalidation rules

- Password change: revoke all refresh_tokens for user (set revoked_at=now()).
- Account deletion / soft-delete: revoke all refresh tokens for user immediately.
- Admin invalidation: `POST /admin/users/:id/invalidate-sessions` with scope triggers revocation.

3) Middleware checks for all protected routes

- `require_auth` middleware must check:
  - Validate JWT signature and `exp`.
  - Load user by `sub` and verify `is_active=true`.
  - Reject if `deleted_at` is set (account deleted).
  - Reject if `locked_until` > now() -> return `account_locked` (423).
  - If `access_expires_at` is set and expired -> return `account_expired` (403).
  - If `valid_from` > now() -> return `account_not_yet_valid` (403).
  - If `must_reset_password` true -> return `password_reset_required` (403) and require redirect to password change page.

4) Refresh endpoint `/auth/refresh` specifics

- Read refresh cookie, compute hash, and lookup DB row.
- Verify `expires_at`, `revoked_at` is NULL, and token is not previously `replaced_by` unless it is the immediate predecessor in rotation protocol.
- On success: create new token, store its hash, set `replaced_by` on old token, set `last_used_at` and return new access and refresh cookie.
- On token reuse detection: revoke all user's refresh tokens (set revoked_at), log event, send monitoring alert, return 403 with `refresh_token_reused`.

5) Storage & transport policies

- Transport: TLS enforced for all public and internal endpoints.
- Cookies: Set `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/auth/refresh`.
- Do not store tokens in client-side storage (localStorage/sessionStorage) to avoid XSS exposure. Access token ephemeral storage in memory is acceptable.

6) Additional hardening

- Implement Content Security Policy (CSP), CSP reporting and secure headers.
- Protect login/refresh endpoints with IP-based rate-limiting and anomaly detection.


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

Errors / standardized error codes (API-wise):

- invalid_credentials — 401: provided username/password not valid
- account_locked — 423: account is temporarily locked until `locked_until`
- account_expired — 403: `access_expires_at` passed or `valid_from` not yet reached
- password_reset_required — 403: user must change password
- rate_limited — 429: too many attempts — include Retry-After header

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

Detailed behaviour / security checks:

- Verify refresh token by hashing and comparing to stored `token_hash`.
- If a token is already replaced (replaced_by is set) or revoked_at is present and the presented token is not the direct predecessor, treat as `refresh_token_reused` attack: revoke all refresh tokens for the user, log the event, and force re-authentication.
- On success, generate a new refresh token (raw), persist its hash and expiry in DB, update the old token's replaced_by to the new id, set last_used_at on the old token, and return the new refresh cookie together with a fresh access token.

### /auth/logout (POST)
- Beschreibung: Revoke current refresh token (remove DB entry), clear cookie.
- Cookie: refreshToken required.
- Response: 200 OK

Flow:
- Find refresh token from cookie, delete row or mark revoked.
- Clear cookie (set Max-Age=0)

Notes:

- We recommend setting `revoked_at` and keeping the row for audit instead of hard-deleting tokens. Admin endpoints can also revoke all tokens for a user as requested.

### /auth/change-password (POST)
- Beschreibung: Authenticated route; user authenticated with access token; change password.
- Body: { "oldPassword": "...", "newPassword": "..." }
- Flow:
  - Verify oldPassword, hash & store new password, set must_reset_password=false, update updated_at.
  - Optionally invalidate existing refresh tokens (delete all refresh_tokens for user).

Security note: Changing a user's password must invalidate/rotate existing sessions: invalidate all refresh_tokens, or alternatively rotate them so old tokens cannot continue to be used.

### /auth/reset-password (POST)
- Beschreibung: Request flow for password reset.
- Body to request reset: { "email": "..." } => send email with reset link with short-lived token (e.g., 1 hour).
- Body to confirm reset: { "resetToken": "...", "newPassword": "..." }
- Implementation notes: can use DB table reset_tokens with token_hash, user_id, expires_at.

### User-facing routes & pages (Passwort-Handling)

Für jede Frontend-Route beschreiben wir die zugehörigen Backend-API-Endpunkte, JSON-Formate und Fehlercodes.

1) Login

- Page: `/login` (Frontend form)
- API: POST `/auth/login`
- Request JSON: {"username": "<user|email>", "password": "<plaintext>"}
- Success Response (200):
  - Body: {"accessToken": "<JWT>", "expiresIn": 900}
  - Cookie: Set-Cookie: refreshToken=<token>; HttpOnly; Secure; Path=/auth/refresh; Max-Age=2592000
- Errors:
  - 401 invalid_credentials
  - 423 account_locked
  - 403 account_expired / password_reset_required
  - 429 rate_limited

Integration Hinweis: Das bestehende Login-Sheet (Templates: `templates/auth/login.html` und `templates/auth/_login_sheet.html`) ist für die UI-Ebene wiederverwendbar. Die Login-Form sollte folgende client-seitige Anforderungen implementieren:

- Formular validiert Eingaben lokal (min length email/password), zeigt Sicherheits-Hinweise (z. B. Passwort-Richtlinien) und sendet POST `/auth/login`.
- Bei `password_reset_required` muss das Login-Client eine forcierte Redirect auf `/account/password?mustReset=1` durchführen.


2) Passwort vergessen / Request reset

- Page: `/password/forgot`
- API: POST `/auth/reset-password/request` (or `/auth/reset-password` depending on naming)
- Request JSON: {"email": "<email>"} (or {"username": "<username|email>"})
- Response (200): {"ok": true} — Do not reveal whether the email exists (always return success/fallback message)
- Errors:
  - 429 rate_limited

3) Passwort zurücksetzen (mit Token aus E-Mail)

- Page: `/password/reset?token=<token>`
- API: POST `/auth/reset-password/confirm`
- Request JSON: {"resetToken": "<token>", "newPassword": "<new-password>"}
- Success: 200 OK with message {"ok": true}
- Errors:
  - 400 invalid_reset_token
  - 410 reset_token_expired
  - 400 weak_password

Security / Behaviour:

- Das `resetToken` darf nur in Hash-Form in DB gespeichert werden. Der Reset-Link enthält das Token in der URL; das Frontend reicht den Token im POST Body ein.
- Der Reset-Token ist einmalig verwendbar: `used_at` wird gesetzt.
- Nach erfolgreichem Reset: setze `must_reset_password=false`, invalidiere vorhandene Refresh-Tokens und zwinge Logout aller Sessions (invalidate-sessions) oder rotiere Tokens.

4) Passwort ändern (eingeloggt)

- Page: `/account/password`
- API: POST `/auth/change-password`
- Request JSON: {"oldPassword": "...", "newPassword": "..."}
- Success: 200 OK — password changed; optionally also return {"ok": true} and rotate/invalidate refresh tokens.
- Errors:
  - 401 invalid_credentials (oldPassword mismatch)
  - 400 weak_password

Re-auth und Security: Für Passwort-Änderungen empfehlen wir einen frischen Login-Anforderung (z. B. Access-Token Alter < 5 Minuten) oder die erneute Eingabe des aktuellen Passworts zur Bestätigung.

5) Erzwungener Passwortwechsel (must_reset_password)

- Behaviour: If `must_reset_password = true` for the user, upon successful login the server must respond with 200 but cause a client redirect to the forced password change page (`/account/password?mustReset=1`) and respond with a code `password_reset_required` to indicate the client must block other actions until password change.

Richtlinie: Client must never proceed to other features before password changed; server-side protections should also require `must_reset_password` checks on protected endpoints and respond with a `password_reset_required` error if enforced.

---

6) Profilseite / Account-Daten

- Page: `/account/profile`
- API: `GET /account/profile` (auth-required) -> liefert alle editierbaren personenbezogenen Felder: `{ "username", "email", "display_name", "about" }` und nicht-editierbare Audit-Felder `{ "created_at", "last_login_at", "is_active", "access_expires_at", "valid_from", "deleted_at" }`.
- API: `PATCH /account/profile` (auth-required)
  - Request JSON: allow partial updates e.g. `{ "display_name": "New", "email": "new@example.org" }`
  - On email change set `email_verified=false` and send verification email; require re-auth for sensitive updates.
  - Response: 200 OK + updated user object (do not return password_hash).

7) Account-Löschung (User-Initiated)

- Page: `/account/delete` (confirmation + reauth)
- API: `POST /account/delete` (auth-required, re-auth with fresh credentials)
  - Request: must include either a current password or a fresh one-time challenge for re-auth.
  - Behaviour on request:
    1. Set `deletion_requested_at = now()`, set `deleted_at = now()` if immediate soft-delete policy, otherwise schedule anonymization after retention window.
    2. Revoke/invalidate all refresh tokens for the user (`revoked_at` set on all rows).
    3. Invalidate active sessions (optionally rotate access-tokens to invalid) and log audit event.
    4. Respond 202 Accepted with information about anonymization schedule and possible reversal window (e.g. 30 days).
- Background job: after configured grace period (default 30 days) perform irreversible anonymization:
  - Replace email/username with pseudonym `deleted-{user_id}@example.invalid`, delete or scrub PII fields, drop reset token rows and older logs as per retention rules.
  - Keep minimal audit records for legal obligations but remove any personal identifiers where possible.

8) Account Deletion by Admin (Admin-initiated)

- Admin endpoint `DELETE /admin/users/:id` should perform a soft-delete equivalent to user deletion, set `deleted_at` and `deletion_requested_at`, revoke tokens, and optionally add an admin note for audit.

Technical notes on token handling during deletion:

- All refresh tokens must be marked `revoked_at=now()` as soon as deletion is requested.
- Access tokens (JWT) cannot always be revoked immediately unless using token blacklist lookup; prefer short-lived access tokens and immediate revocation of refresh tokens so session expiry is limited.

9) Data export endpoint (user-initiated & admin-initiated)

- User: `GET /account/data-export` -> returns JSON with all personal data fields and metadata (audits, created_at, deletion_requested_at, deleted_at). Rate-limit the endpoint and require re-authentication on request > sensitive.
- Admin: `POST /admin/users/:id/export` -> generate export package for compliance. Exports must be delivered via time-limited download link (15 minutes) and protected by audit log.

Errors & Responses (examples):

- 200 OK: {"ok": true, "downloadUrl": "..."}
- 401 unauthorized: invalid access
- 403 forbidden: insufficient scope/role
- 404 not_found: user not found


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

  ## 6. Sicherheitsaspekte & Best Practices

  Diese Sektion fasst Security-spezifische Vorgaben präzise zusammen, damit Implementierung und Betrieb in Übereinstimmung mit Best Practices erfolgt.

  1) Passwort-Hashing

  - Empfohlen: argon2id (wenn verfügbar). Alternativ bcrypt (mindestens 12 rounds).
  - Parameter / Beispiel (argon2-cffi): time_cost=2, memory_cost=102400 (100MiB), parallelism=4 — an die Infrastruktur anpassen und dokumentieren.
  - Verwendung: Verwende stets geprüfte Bibliotheken (passlib, argon2-cffi, bcrypt). Niemals eigenen Krypto-Code schreiben.

  2) JWT / Signing

  - Signiere Access-Tokens mit HMAC (shared secret) oder RSA/ECDSA (asymmetrisch) mit klaren rotation / versioning.
  - Env vars:
    - JWT_SECRET (HMAC) oder PRIVATE_KEY (PEM) + PUBLIC_KEY
    - JWT_ALG = HS256 | RS256 | ES256
  - Halte kompakte Access-Tokens (15–30 min lifetime). Refresh-Tokens sind opaque and long-lived; keep them out of client JS.

  3) Token storage & transport

  - Access-Token: short-lived, keep in-memory on clients (do not store in localStorage). Mobile apps can use secure storage per platform.
  - Refresh-Token: HttpOnly + Secure cookie, set SameSite=Strict (or Lax if necessary for cross-site). Cookie path should be /auth/refresh.
  - Use HTTPS in production always.

  4) Rate-limiting & abuse prevention

  - Enforce rate limits on critical endpoints:
    - POST /auth/login — per IP and per account (e.g. 5 attempts / 5 minutes) with exponential backoff.
    - POST /auth/reset-password/request — per account / per IP to avoid account enumeration and abuse.
  - Apply generic rate limits for anonymous endpoints on per-client and global basis.

  5) Expiry / validity checks

  - access_expires_at: when set and current time is greater, block login and refresh flows; return `account_expired` (403).
  - valid_from: if current time is before valid_from block login with `account_not_yet_valid` (403).

  6) Monitoring & alerting

  - Log and alert suspicious auth events (repeated refresh token reuse attempts, sudden number of failed logins across accounts, mass resets).
  - Keep audit trails for admin operations and token revocations.

  7) Misc

  - Access tokens must be validated on each request, including signature and expiry.
  - Consider device fingerprinting (user_agent/ip) only for logging and anomaly detection; never rely on those as the only security control.

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
  - Query params: ?page=1&size=50&role=admin&status=locked
  - Response: {"items": [{"id":...,"username":...,"role":...,"is_active":...,"last_login_at":...,"valid_from":...,"access_expires_at":...}], "meta":{}}
- GET /admin/users/:id (detail)
  - Response: user object (fields listed above plus audit data)
- POST /admin/users (create)
  - Request JSON: {"username": "...", "email": "...", "password": "<plain>" | "tempPassword": "...", "role": "user|admin|sysadmin", "is_active": true|false, "valid_from": "<ISO>" , "access_expires_at": "<ISO>", "must_reset_password": true|false}
  - Response: 201 created, created user object (no password)
- PATCH /admin/users/:id (partial update)
  - Request JSON: {"role":"admin","is_active":false,"must_reset_password":true, "valid_from":"ISO","access_expires_at":"ISO"}
  - Response: 200 updated user
- POST /admin/users/:id/reset-password (admin set new password)
  - Request JSON: {"newPassword": "<plaintext>", "must_reset_password": true|false}
  - Response: 200 OK, returns {"ok": true}
- POST /admin/users/:id/lock
  - Request JSON: {"until":"<ISO>"} (optional — if missing, set an administrative indefinite lock)
  - Response: 200OK {"ok":true, "locked_until":"<ISO>"}
- POST /admin/users/:id/unlock
  - Request JSON: none
  - Response: 200OK
- POST /admin/users/:id/invalidate-sessions
  - Request JSON: {"scope":"all"|"current"} — "all" invalidates all refresh_tokens for the user
  - Response: 200OK
- DELETE /admin/users/:id (delete user)

All admin endpoints must be protected by RBAC middleware. Suggested roles and allowed actions:

- sysadmin: full rights (create/delete users, change roles, invalidate sessions, create system-level admin users)
- admin: manage regular users, change role to/from 'user', lock/unlock, trigger `invalidate-sessions`, request password resets
- support: read-only listing, trigger forced password reset for support cases (if allowed), cannot change roles or delete accounts

Role enforcement should be explicit in middleware, and endpoints must validate both the caller's role and the target user's properties (e.g., prevent lower-privileged admins changing sysadmin accounts).

### UI layout & behaviour — `/admin/users` (React/Vanilla frontend spec)

1) Listing page `/admin/users`

- Table columns (default):
  - Checkbox (select), Username, E-Mail, Rolle, is_active, Status (Active/Locked/Expired/Deleted/NotYetValid), `last_login_at`, `created_at`, `updated_at`, Aktionen (Buttons)
- Filters & search:
  - Quick search (username/email)
  - Filters: Role (dropdown), Status (active/locked/expired/deleted), Date ranges (created_at/last_login_at)
  - Sortable columns: username, role, last_login_at, created_at
- Pagination & size selection.
- Bulk actions (on selected): invalidate sessions, lock, unlock, set must_reset_password, delete (soft-delete) — bulk ops must be rate-limited and protected by higher role (admin or sysadmin).

2) Row actions (per user):

- View (opens detail pane) — GET /admin/users/:id
- Edit (opens modal) — PATCH /admin/users/:id
- Invite / Set password — POST /admin/users (create) OR POST /admin/users/:id/reset-password (admin initiates a reset or sends Invite link). Invite flows should send a secure one-time link using `reset_tokens` with short expiry.
- Lock/Unlock — POST /admin/users/:id/lock / unlock
- Invalidate sessions — POST /admin/users/:id/invalidate-sessions
- Delete — DELETE /admin/users/:id (soft-delete)

3) Detail / Audit view `/admin/users/:id`

- Show full user object (safe fields only): username, email (masked optional), role, is_active, must_reset_password, valid_from, access_expires_at, last_login_at, login_failed_count, locked_until, created_at, updated_at, deleted_at, deletion_requested_at
- Audit timeline: last login IP, last login user_agent, recent failed login attempts (count + last events), recent token rotations, admin actions (who changed role / locked account). Provide a paginated small audit log view.

4) Create user / Invite

- Instead of storing admin-chosen plaintext passwords, offer two flows:
  - Invite flow: `POST /admin/users` with `{"username":"...","email":"...","role":"user","must_reset_password":true}` -> server generates a reset/invite token (reset_tokens row) and sends an invite email with single-use link. The created user has no accessible password; they must set it via reset flow.
  - Admin create with tempPassword (allowed only for sysadmin): same as above but store temporary password hashed and optionally set `must_reset_password=true`.

5) RBAC and UI restrictions

- A user with `admin` role cannot modify or delete `sysadmin` users. UI must hide action buttons not permitted for the logged-in admin.
- Actions that affect authentication (invalidate sessions, reset passwords) must require a confirmation modal and be logged in audit trail.

6) Compliance & Audit

- Every admin action (create/update/delete/reset/invalidate-session) must produce an audit record with: `actor_id`, `actor_role`, `target_user_id`, `action`, `reason` (optional), `timestamp`.
- Audit logs must be write-once (append-only) and retained according to policy (1 year) or per legal requirement.

7) Rate-limits & protections for admin endpoints

- Enforce rate-limits and require MFA for high-privileged actions (invalidate all sessions, delete users). Consider additional approval flow for deleting accounts older than X days.

8) Example JSON payloads (summary)

- GET /admin/users
  - Response: {"items": [{"id":"uuid","username":"...","email":"x@x","role":"user","is_active":true,"status":"active","last_login_at":"ISO"}], "meta": {"page":1,"size":50}}

- PATCH /admin/users/:id
  - Request: {"role":"admin","is_active":true,"must_reset_password":false, "valid_from":"ISO","access_expires_at":"ISO"}
  - Response: 200 {"ok":true, "user": {...}}

- POST /admin/users (invite)
  - Request: {"username":"bob","email":"bob@example.org","role":"user","must_reset_password":true}
  - Response: 201 {"ok":true, "inviteSent":true, "userId":"..."}

9) Frontend UX considerations

- For destructive actions provide “Are you sure?” with typed confirmation (e.g. type the username to confirm delete).
- Show clear status badges in UI for `deleted`, `locked`, `expired`, `must_reset_password`.


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

Detailed Test Matrix and validation expectations (unit, integration & E2E):

1) Login flow

- Success: valid username/password -> 200, returns accessToken and refresh cookie, increments last_login_at, resets login_failed_count.
- Invalid password -> 401 invalid_credentials; increments login_failed_count.
- Locked account -> after N attempts -> 423 account_locked and locked_until set in DB.
- Account not yet valid (valid_from in future) -> 403 account_not_yet_valid.
- Account expired (access_expires_at in the past) -> 403 account_expired.

2) Refresh token & rotation

- Valid refresh cookie -> new access+refresh tokens returned; old refresh token `replaced_by` set; last_used_at updated.
- Reuse of old (rotated) refresh token -> 403 refresh_token_reused; all refresh tokens for user revoked.
- Expired refresh token -> 401 invalid/expired.

3) Logout

- POST /auth/logout -> revoke current refresh token and clear cookie; access token may expire naturally (verify refresh row revoked_at set).

4) Password reset

- Request reset -> rate-limited, always return 200 success message (no enumeration).
- Token usage -> single-use; after use `used_at` set.
- Invalid or expired -> appropriate 400/410 codes.
- After reset, existing refresh tokens invalidated.

5) Password change (authenticated)

- Correct oldPassword -> password updated, must_reset_password cleared, all refresh tokens invalidated.
- Wrong oldPassword -> 401 and no changes.

6) Profile editing

- GET /account/profile -> returns current data (200).
- PATCH /account/profile -> updates allowed fields, sets updated_at, not exposing password_hash.

7) Account deletion

- POST /account/delete (re-auth required) -> sets deleted_at, deletion_requested_at, revoke tokens -> return 202 with scheduled anonymization info.
- After anonymization window -> user row pseudonymized; login fails; data export returns limited/anonymous view.

8) Admin flows

- Create user (invite) -> creates user and sends invite; no password stored in logs / admin UI.
- Patch user -> change role/valid_from/access_expires_at; unauthorized roles are rejected.
- Lock/unlock/invalidate-sessions -> check token rows updated and audit entry created.

9) Security negative tests

- Attempt to use access token after refresh-token-based revocation -> expected 401 (if immediate blacklist enabled) or short window until access token expires.
- Reuse of refresh token -> detect and revoke all tokens.
- Rate-limit exceeded on password reset -> return 429.

10) Compliance & data-rights tests

- `GET /account/data-export` returns valid JSON that includes all requested personal fields and meta data.
- `POST /account/delete` and subsequent anonymization steps validated — verify no PII remains and backup handling is compliant.

Example test mapping / locations for implementation:

- tests/test_auth_flow.py -> login/refresh/logout/reset/change tests
- tests/test_account_profile.py -> profile GET/PATCH and data-export
- tests/test_admin_users.py -> admin create/patch/lock/unlock/invalidate/delete tests
- tests/test_privacy_compliance.py -> deletion/anonymization/data retention tests


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
