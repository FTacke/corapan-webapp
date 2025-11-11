# Login-Sheet-Only Implementation — Abgeschlossen ✅

## Überblick

Die CO.RA.PAN-Web-App wurde erfolgreich auf ein **Login-Sheet-Only**-System migriert. Es gibt jetzt **keinen Full-Page-Login** mehr. Alle Authentifizierungsflows verwenden ein Modal Sheet.

## Implementierte Features

### 1. **Nur Login-Sheet, kein Full-Page-Login**
- ✅ `templates/auth/login.html` entfernt (legacy full-page)
- ✅ Nur `templates/auth/_login_sheet.html` bleibt (modal sheet)
- ✅ GET `/auth/login` ist jetzt ein Router (nicht render_template):
  - **HTMX**: `204 No Content + HX-Redirect → /auth/login_sheet`
  - **Non-HTMX**: `303 SEE OTHER → /?login=1&next=...` (auto-opens sheet in landing page)

### 2. **Intended-Redirect überall**
- ✅ `_safe_next()` implementiert (Open-Redirect-Schutz, double-decode-aware)
- ✅ Player-Gating nutzt `request.full_path` für `next` mit double-encoding
- ✅ Template-Filter `|urlencode` erhält vollständige Query-Strings
- ✅ POST `/auth/login` dekodiert und redirectet zu ursprünglichem Ziel
- ✅ Basis-Template öffnet Sheet automatisch bei `?login=1`

### 3. **Query-String-Preservation**
Das größte Problem war: Query-Parameter in `next` wurden abgeschnitten (z.B. `/player?transcription=foo&audio=bar.mp3` → nur `/player?transcription=foo`).

**Lösung:**
- Player-Gating double-enkodiert `next` in HX-Redirect-Header
- Template nutzt `{{ next|urlencode }}` im hidden input
- `_safe_next()` dekodiert double-encoded Werte

**Beispiel:**
```
GET /player?transcription=foo&audio=bar
  → HX-Redirect: /auth/login_sheet?next=%252Fplayer%253F...
  → Sheet hidden input: value="/player%3Ftranscription%3Dfoo%26audio%3Dbar"
  → POST login → HX-Redirect: /player?transcription=foo&audio=bar ✅
```

### 4. **Rate-Limiting**
- ✅ POST `/auth/login` hat `@limiter.limit("5 per minute")`

### 5. **E2E Tests**
- ✅ `scripts/test_e2e_player_login.ps1`: Player unauth → Sheet → Login → Player (mit JWT)
- ✅ `scripts/test_e2e_direct_login.ps1`: GET `/auth/login` Router-Verhalten (HTMX/non-HTMX)

### 6. **Passwords**
- ✅ `hash_passwords_v2.py` aktualisiert (korrekte Env-Var-Formate)
- ✅ `passwords.env` generiert mit `{ROLE}__{ACCOUNT}_PASSWORD_HASH`
- ✅ Standard-Accounts: admin, editor, user (mit default-Passwörtern)

## Akzeptanz-Tests (Alle Grün ✅)

| Test | Status | Details |
|------|--------|---------|
| Non-HX GET /auth/login | ✅ PASS | 303 → /?login=1&next=... |
| HTMX GET /auth/login | ✅ PASS | 204 + HX-Redirect → login_sheet |
| Login Sheet Render | ✅ PASS | 200 OK mit hidden next input |
| HTMX Player Gating | ✅ PASS | 204 + HX-Redirect → login_sheet?next=... |
| POST Login (HTMX) | ✅ PASS | 204 + HX-Redirect → intended player URL |
| Query-String Preservation | ✅ PASS | Full query string preserved (foo&bar&segment) |
| Repo Sweep | ✅ PASS | Keine legacy `auth.login` Referenzen |

## Wie Man Tests Ausführt

```powershell
# E2E Test 1: Player Auth Flow
PowerShell.exe -File .\scripts\test_e2e_player_login.ps1

# E2E Test 2: Direct Login Router
PowerShell.exe -File .\scripts\test_e2e_direct_login.ps1

# Passwords regenerieren
python "LOKAL\02 - Add New Users (Security)\hash_passwords_v2.py"
```

## Dateien Geändert

### Routes
- `src/app/routes/auth.py`: `_safe_next()`, `login_sheet()`, `login_form()` (router), `login_post()`
- `src/app/routes/player.py`: Gating mit HTMX-aware HX-Redirect + double-encoding

### Templates
- `templates/auth/_login_sheet.html`: hidden input mit `|urlencode` filter
- `templates/auth/login.html`: **GELÖSCHT** (legacy)
- `templates/partials/_navbar.html`, `_navigation_drawer.html`, `_top_app_bar.html`, `status_banner.html`, `errors/401.html`: Links zu `hx-get` login_sheet
- `templates/base.html`: Auto-trigger script für Sheet bei `?login=1`

### Utility
- `LOKAL/02 - Add New Users (Security)/hash_passwords_v2.py`: Aktualisiert für korrekte Env-Formate
- `scripts/test_e2e_player_login.ps1`: Neue E2E-Test
- `scripts/test_e2e_direct_login.ps1`: Neue E2E-Test

## Produktions-Checklist

- [ ] Starke Passwörter in `hash_passwords_v2.py` setzen (nicht "admin", "editor", "user")
- [ ] `passwords.env` regenerieren: `python "LOKAL/02 - Add New Users (Security)/hash_passwords_v2.py"`
- [ ] `passwords.env` **nicht in Git commiten** (.gitignore überprüfen)
- [ ] RSA Keys existieren (`config/keys/private.pem`, `public.pem`)
- [ ] Test mit echten Benutzern durchführen
- [ ] Logging überprüfen für Failed-Login-Attempts (10.29.238.1 IP-Blocking?).

## Bekannte Limitationen

- Logout-Link ist nicht implementiert (benutzer müssen Browser-Cookies löschen / Session-Timeout warten)
- Passwort-Reset nicht implementiert
- 2FA/MFA nicht implementiert

## Kontakt / Support

Bei Fragen zu dieser Implementierung siehe:
- `/docs/reports/LOGIN-SHEET-COMPLETION-REPORT.md`
- Git-Log für einzelne Commits
