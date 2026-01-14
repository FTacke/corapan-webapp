# Request-Flow

**Scope:** Detaillierter Request-Lifecycle durch die Anwendung  
**Source-of-truth:** `src/app/__init__.py`, `src/app/routes/*.py`, `templates/`

## Überblick

Jeder HTTP-Request durchläuft folgende Phasen:

1. **Reverse Proxy (Nginx)** → Weiterleitung an Gunicorn
2. **ProxyFix Middleware** → Verarbeitung von `X-Forwarded-*` Headers
3. **before_request Hook** → JWT Auth Context setzen (`g.user`, `g.role`)
4. **Route Handler** → Blueprint-spezifische Logik
5. **Service Layer** → Business Logic, Daten abrufen
6. **Template Rendering / JSON** → Response generieren
7. **after_request Hook** → Security Headers hinzufügen
8. **Response** → Zurück zum Client

## Beispiel 1: Normale Seite (ohne Auth)

**Request:** `GET /`

### 1. Nginx → Gunicorn
```
https://corapan.hispanistica.com/ → Nginx → http://localhost:6000/
```

### 2. ProxyFix Middleware
```python
# src/app/__init__.py
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
```
- Setzt `request.scheme = "https"` (aus `X-Forwarded-Proto`)
- Ermöglicht korrekte `url_for(_external=True)` Generierung

### 3. before_request: Auth Context
```python
# src/app/__init__.py → register_auth_context()
@app.before_request
def _set_auth_context():
    if request.path.startswith("/static/"):
        return  # Skip für Static Assets
    
    try:
        verify_jwt_in_request(optional=True)
        g.user = get_jwt_identity()
        g.role = Role[get_jwt().get("role", "user")]
    except:
        g.user = None
        g.role = None
```
- JWT aus Cookie/Header lesen
- `g.user` und `g.role` setzen (oder `None` wenn nicht authentifiziert)

### 4. Route Handler
```python
# src/app/routes/public.py
@public_bp.route("/")
def index():
    return render_template("home/index.html")
```
- Kein Auth-Check → öffentlich zugänglich
- Template rendern

### 5. Template Rendering
```jinja2
{# templates/home/index.html #}
{% extends "base.html" %}
{% block content %}
  <h1>Willkommen bei CO.RA.PAN</h1>
{% endblock %}
```
- `base.html` inkludiert: NavDrawer, TopAppBar, Footer
- `g.user` in Template verfügbar (für Login/Logout Buttons)

### 6. Response
```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
...
```
- Security Headers automatisch hinzugefügt (via `register_security_headers()`)

---

## Beispiel 2: Geschützte API (mit Auth)

**Request:** `POST /search` (AJAX Call)

### 1-3. Wie oben (Nginx, ProxyFix, Auth Context)

### 4. Route Handler mit Auth-Check
```python
# src/app/routes/corpus.py
@corpus_bp.route("/search", methods=["POST"])
@jwt_required()  # Decorator prüft JWT
def search():
    query = request.json.get("query")
    filters = request.json.get("filters", {})
    
    # Service aufrufen
    from ..search import search_service
    results = search_service.execute_search(query, filters)
    
    return jsonify(results), 200
```
- `@jwt_required()` → wirft 401 Unauthorized wenn JWT fehlt/ungültig
- Service-Layer aufrufen für Business Logic

### 5. Service Layer
```python
# src/app/search/search_service.py
def execute_search(query: str, filters: dict):
    # BlackLab API Call
    blacklab_url = "http://blacklab:8080/blacklab-server/corpus/search"
    response = requests.post(blacklab_url, json={"query": query, "filters": filters})
    return response.json()
```
- Externe Services ansprechen (BlackLab)
- Daten transformieren/aggregieren

### 6. JSON Response
```json
{
  "results": [...],
  "total": 42,
  "page": 1
}
```

---

## Beispiel 3: Admin-geschützte Seite

**Request:** `GET /admin/users`

### 1-3. Wie oben

### 4. Route Handler mit Role-Check
```python
# src/app/routes/admin_users.py
from ..auth import require_role, Role

@admin_users_bp.route("/users")
@require_role(Role.admin)  # Custom Decorator
def list_users():
    from ..auth import services
    users = services.list_all_users()
    return render_template("admin/users.html", users=users)
```
- `@require_role(Role.admin)` → wirft 403 Forbidden wenn nicht Admin
- Service-Layer für DB-Zugriff

### 5. Service Layer (DB-Zugriff)
```python
# src/app/auth/services.py
def list_all_users():
    from .models import User
    from ..extensions.sqlalchemy_ext import get_session
    
    with get_session() as session:
        users = session.query(User).filter(User.deleted_at.is_(None)).all()
        return [user_to_dict(u) for u in users]
```
- SQLAlchemy Session via Context Manager
- Soft-Deleted User herausfiltern

### 6. Template Rendering
```jinja2
{# templates/admin/users.html #}
{% for user in users %}
  <tr>
    <td>{{ user.username }}</td>
    <td>{{ user.role }}</td>
  </tr>
{% endfor %}
```

---

## Static Assets

**Request:** `GET /static/css/md3/tokens.css`

### Nginx-Handling (Produktion)
```nginx
location /static/ {
    alias /var/www/corapan/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```
- Nginx serviert direkt → Flask wird nicht involviert
- Cache-Headers für Performance

### Flask-Handling (Development)
```python
# Flask Dev-Server serviert /static/ automatisch
# Konfiguriert via static_folder in create_app()
```

---

## Error Handling

### 404 Not Found
```python
# src/app/__init__.py → register_error_handlers()
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not Found"}), 404
    return render_template("errors/404.html"), 404
```

### 401 Unauthorized (JWT fehlt)
```python
@app.errorhandler(401)
def unauthorized(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Unauthorized"}), 401
    return redirect(url_for("auth.login", next=request.path))
```

### 403 Forbidden (Falsche Rolle)
```python
@app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html"), 403
```

---

## CSRF Protection

**Forms (POST):**
```html
<form method="POST" action="/auth/login">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>
```

**AJAX (mit JWT):**
```javascript
fetch("/search", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-TOKEN": getCookie("csrf_access_token")
  },
  body: JSON.stringify({query: "test"})
})
```
- JWT-Cookies enthalten CSRF-Token
- `JWT_COOKIE_CSRF_PROTECT = True` in Config

---

## Zusammenfassung

| Phase | Komponente | Zweck | Datei |
|-------|-----------|-------|-------|
| 1 | Nginx | HTTPS, Static Serving | nginx.conf |
| 2 | ProxyFix | Header-Normalisierung | `src/app/__init__.py` |
| 3 | before_request | Auth Context | `src/app/__init__.py` |
| 4 | Route Handler | Routing, Decorators | `src/app/routes/*.py` |
| 5 | Service Layer | Business Logic | `src/app/services/`, `src/app/search/`, etc. |
| 6 | Template/JSON | Response-Generierung | `templates/`, `jsonify()` |
| 7 | after_request | Security Headers | `src/app/__init__.py` |

**Extension Points:**
- Neue Routes: Blueprint in `src/app/routes/` erstellen
- Neue Services: Modul in `src/app/` erstellen
- Neue Templates: In `templates/<modul>/` ablegen
