# Migration auf neuen Windows-PC

## Ziel

Reproduzierbares Setup mit `uv`, festem Python und `.venv` im Repo-Root – ohne lokale Altlasten im Git-Repo.

## Manuell vom alten PC migrieren

Diese Verzeichnisse sind lokal/groß und werden nicht aus Git reproduziert:

- `runtime/corapan/media` (~15168.8 MB) → enthält Audiodaten/Transkripte
- `data/blacklab_export` (~1466.4 MB) → Export-/Index-Basisdaten
- `data/blacklab_index*` (mehrere Ordner, jeweils ~157–291 MB) → Suchindexe und Backups
- `data/exports` (~161.7 MB) → generierte Exporte

Empfohlenes Ziel außerhalb des Repos: `D:\data\corapan-webapp\...`

Regel:

- Diese Ordner bleiben gitignored und werden niemals committet.
- Runtime-Pfade werden per ENV gesetzt (z. B. `CORAPAN_RUNTIME_ROOT`, `CORAPAN_MEDIA_ROOT`).

## Wird neu erzeugt

- `.venv/` (lokale Python-Umgebung)
- installierte Python-Pakete aus `requirements.txt` (und optional `requirements-dev.txt`)

## Setup-Kommandos auf dem Ziel-PC

```powershell
git clone <repo-url>
cd corapan-webapp

# uv installieren (falls nicht vorhanden)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Runtime-Setup
.\scripts\bootstrap.ps1

# Optional Dev-Tools (pytest/ruff/mypy)
.\scripts\bootstrap.ps1 -Dev

# Secrets-Datei anlegen (nur falls für lokalen Run benötigt)
# Copy-Item .env.example .env

# App starten
python -m src.app.main
```

## Secrets (nur Namen, keine Werte)

- `FLASK_SECRET_KEY`
- `JWT_SECRET_KEY`
- `AUTH_DATABASE_URL`
- `AUTH_HASH_ALGO`
- `BLS_BASE_URL`
- `BLS_CORPUS`
- `CORAPAN_RUNTIME_ROOT`
- `CORAPAN_MEDIA_ROOT`
- `PUBLIC_STATS_DIR`
- `STATS_TEMP_DIR`
- `ALLOW_PUBLIC_TEMP_AUDIO`

Zusätzlich nach Bedarf:

- `FLASK_ENV`, `FLASK_DEBUG`, `FLASK_SESSION_SECURE`, `FLASK_SESSION_SAMESITE`
- `AUTH_ACCOUNT_ANONYMIZE_AFTER_DAYS`