# Fixes für Login & JWT Problems (2025-10-20)

## Problem
Nach der Normalisierung der Ländercodes funktionierten Login und geschützte Routen nicht mehr:
- "Signature verification failed" bei Corpus & Atlas
- Login-Credentials wurden nicht geladen
- JWT-Tokens konnten nicht verifiziert werden

## Root Cause
1. **Config-Datei gelöscht**: `src/app/config.py` wurde versehentlich gelöscht, wodurch die `load_config()` Funktion fehlte
2. **Passwords.env nicht geladen**: Die `passwords.env` Datei mit Credentials wurde nicht automatisch eingelesen
3. **JWT_SECRET nicht konfiguriert**: JWT-Token-Signierung schlug fehl

## Lösung

### 1. Config-Modul wiederhergestellt
**Datei**: `src/app/config/__init__.py`

```python
from dotenv import load_dotenv

# Load environment variables from passwords.env file
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_PASSWORDS_ENV_PATH = _PROJECT_ROOT / "passwords.env"
if _PASSWORDS_ENV_PATH.exists():
    load_dotenv(_PASSWORDS_ENV_PATH)
```

**Was es macht:**
- Lädt automatisch `passwords.env` beim Import des Config-Moduls
- Macht alle `*_PASSWORD_HASH` Variablen verfügbar
- Lädt `FLASK_SECRET_KEY` aus der Datei

### 2. JWT-Secret-Key Fallback
**Datei**: `src/app/config/__init__.py`

```python
class BaseConfig:
    # ...
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", os.getenv("FLASK_SECRET_KEY", DEFAULT_SECRET_SENTINEL))
```

**Was es macht:**
- Wenn `JWT_SECRET` nicht gesetzt ist, verwendet es `FLASK_SECRET_KEY`
- `FLASK_SECRET_KEY` wird aus `passwords.env` geladen
- Vereinfacht den Start-Command

### 3. Vereinfachter Startbefehl
**Vorher** (kompliziert):
```powershell
$env:FLASK_SECRET_KEY="local-dev-secret"; $env:JWT_SECRET="local-dev-jwt-secret"; $env:FLASK_ENV="development"; python -m src.app.main
```

**Jetzt** (einfach):
```powershell
$env:FLASK_ENV="development"; python -m src.app.main
```

## Verifizierung

### Test 1: Credentials geladen?
```powershell
python LOKAL\test_credentials.py
```
Erwartete Ausgabe:
```
✅ Credentials loaded successfully!
Total credentials loaded: 3
Accounts: ['admin', 'editor_test', 'user_test']
```

### Test 2: Login funktioniert?
```powershell
python LOKAL\test_login.py
```
Erwartete Ausgabe:
```
Status: 302
Cookies in response: ['access_token_cookie', 'refresh_token_cookie']
Is logged in: True
```

### Test 3: Manuelle Verifikation
1. Starte App: `$env:FLASK_ENV="development"; python -m src.app.main`
2. Öffne Browser: http://127.0.0.1:8000
3. Login mit: `admin` / `0000`
4. Navigiere zu: http://127.0.0.1:8000/atlas
5. Klicke auf einen Player-Link → sollte funktionieren!

## Standard-Credentials (Development)
Definiert in `LOKAL/security/hash_passwords_v2.py`:

- **Admin**: `admin` / `0000`
- **Editor**: `editor_test` / `1111`
- **User**: `user_test` / `2222`

Neue Passwörter generieren:
```powershell
python LOKAL\security\hash_passwords_v2.py
```

## Zusammenfassung der Änderungen

### Geänderte Dateien
1. ✅ `src/app/config/__init__.py` - Neu erstellt mit dotenv-Support
2. ✅ `startme.md` - Vereinfachter Startbefehl
3. ✅ `LOKAL/test_credentials.py` - Neu erstellt für Testing
4. ✅ `LOKAL/test_login.py` - Neu erstellt für Testing

### Wie es jetzt funktioniert
1. **App-Start**: `python -m src.app.main`
2. **Config-Import**: `src/app/config/__init__.py` wird geladen
3. **Dotenv-Load**: `load_dotenv('passwords.env')` lädt alle Secrets
4. **Credential-Hydration**: `auth.loader.hydrate()` liest `*_PASSWORD_HASH` aus Environment
5. **Login**: Credentials sind verfügbar, JWT-Tokens werden signiert
6. **Protected Routes**: JWT-Middleware verifiziert Tokens erfolgreich

## Architektur-Prinzipien beibehalten

Die Fixes behalten die wichtigen Prinzipien bei:
- ✅ **Single Source of Truth**: `passwords.env` ist die einzige Quelle für Secrets
- ✅ **Separation of Concerns**: Config-Loading getrennt von Business Logic
- ✅ **12-Factor App**: Secrets über Environment-Variablen
- ✅ **Development Experience**: Ein einfacher Command zum Starten

## Nächste Schritte (falls nötig)

Wenn Probleme auftreten:
1. Lösche `passwords.env` und generiere neu: `python LOKAL\security\hash_passwords_v2.py`
2. Checke ob `python-dotenv` installiert ist: `pip install python-dotenv`
3. Prüfe Logs beim App-Start auf Fehler
4. Teste mit `LOKAL/test_credentials.py` ob Credentials geladen werden
