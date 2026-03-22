# Auth & Admin Modul

**Scope:** User Management, Login/Logout, Rollen  
**Source-of-truth:** `src/app/auth/`, `src/app/routes/auth.py`, `src/app/routes/admin_users.py`

## Übersicht

Das Auth & Admin Modul verwaltet:
- **Authentication:** Login, Logout, Token Refresh
- **User Management:** Create, Update, Delete, List (Admin-only)
- **Roles:** User, Editor, Admin (Hierarchisch)
- **Audit:** Soft-Delete, Anonymisierung (DSGVO)

**Routes:**
- `/auth/login` — Login-Seite
- `/auth/logout` — Logout (POST)
- `/auth/refresh` — Token Refresh (POST)
- `/admin/users` — User-Liste (Admin)
- `/admin/users/create` — User erstellen (Admin)
- `/admin/users/<id>/edit` — User bearbeiten (Admin)
- `/admin/users/<id>/delete` — User löschen (Admin)

---

## Authentication Flow

Siehe [docs/architecture/security-auth.md](../architecture/security-auth.md) für Details.

**Kurz:**
1. User sendet Username + Password
2. Server prüft Credentials, generiert JWT
3. JWT in Cookies gesetzt (Access + Refresh)
4. Geschützte Routes prüfen JWT via `@jwt_required()`
5. Refresh nach 50min (automatisch via JS)

---

## Rollen

| Rolle | Wert | Berechtigungen |
|-------|------|----------------|
| `user` | 1 | Basis-Zugriff (Suche, Atlas, Stats) |
| `editor` | 2 | + JSON-Editor |
| `admin` | 3 | + User Management, Analytics Dashboard |

**Hierarchie:** `admin > editor > user`

**Implementierung:**
```python
# src/app/auth/__init__.py
class Role(Enum):
    user = 1
    editor = 2
    admin = 3
```

---

## User Management (Admin)

### User erstellen

**Route:** `POST /admin/users/create`

**Form:**
```html
<form method="POST">
  <input name="username" required>
  <input name="email" type="email">
  <input name="password" type="password" required>
  <select name="role">
    <option value="user">User</option>
    <option value="editor">Editor</option>
    <option value="admin">Admin</option>
  </select>
  <button type="submit">Erstellen</button>
</form>
```

**Service:**
```python
# src/app/auth/services.py
def create_user(username, email, password, role="user"):
    password_hash = hash_password(password)
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(user)
    session.commit()
    return user
```

---

### User bearbeiten

**Route:** `POST /admin/users/<id>/edit`

**Felder:**
- Username (readonly, da Unique)
- Email
- Role
- is_active
- must_reset_password

---

### User löschen (Soft Delete)

**Route:** `POST /admin/users/<id>/delete`

**Implementierung:**
```python
def soft_delete_user(user_id):
    user = session.query(User).get(user_id)
    user.deleted_at = datetime.utcnow()
    user.deletion_requested_at = datetime.utcnow()
    user.is_active = False
    session.commit()
```

**Anonymisierung:**
```bash
# Cron Job (täglich)
flask auth-anonymize
```

**Siehe:** `scripts/anonymize_old_users.py`

---

## Login Sheet (UI)

**Template:** `templates/partials/_login_sheet.html`

**Features:**
- Material Design 3 Bottom Sheet
- Username + Password
- "Angemeldet bleiben" (Checkbox, nicht implementiert)
- Fehler-Feedback (Snackbar)

**JavaScript:**
```javascript
// static/js/auth-setup.js
async function login(username, password) {
  const response = await fetch("/auth/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username, password})
  });
  
  if (response.ok) {
    location.reload();  // Neu laden, um Auth-Context zu aktualisieren
  } else {
    showSnackbar("Login fehlgeschlagen");
  }
}
```

---

## Extension Points

**OAuth/SAML:**
- Neue Route `/auth/oauth/<provider>`
- Provider-spezifische Library (z.B. `authlib`)
- User-Provisioning in DB

**2FA:**
- Neue Tabelle `user_totp_secrets`
- TOTP-Library (z.B. `pyotp`)
- Login-Flow erweitern (2. Schritt)

**API Keys:**
- Neue Tabelle `api_keys`
- Decorator `@require_api_key()`
- Header: `X-API-Key: <key>`

---

## Projekt-spezifische Annahmen

- **Initial Admin:** Username `admin`, Password `change-me` (muss geändert werden!)
- **Email:** Optional (kein Password-Reset Feature aktiv)
- **Rollen:** Fest definiert (keine dynamischen Permissions)
