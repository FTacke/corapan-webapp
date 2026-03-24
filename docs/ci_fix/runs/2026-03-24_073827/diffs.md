# Diff Summary

Betroffene Dateien:
- `.github/workflows/ci.yml`
- `.github/workflows/md3-lint.yml`
- `app/pyproject.toml`
- `app/src/app/config/__init__.py`
- `app/src/app/extensions/http_client.py`
- `app/src/app/auth/services.py`
- `app/src/app/routes/admin_users.py`
- `app/tests/test_advanced_api_enrichment.py`
- `app/tests/test_e2e_ui.py`
- `app/tests/test_runtime_paths.py`
- `app/tests/test_auth_hash_algorithms.py`

Klartext-Zusammenfassung:
- CI von einem entwerteten Testjob auf eine echte mehrstufige Struktur umgebaut
- veraltete Action-Majors aktualisiert
- Importzeit-Validierung entschaerft, ohne Pflichtvariablen als Laufzeitvertrag aufzugeben
- SQLAlchemy-Filterfehler in Auth-/Admin-Pfaden korrigiert
- mehrere Tests an den aktuellen Runtime-/Security-Vertrag angepasst
- neue schlanke Hash-Kompatibilitaetsabdeckung hinzugefuegt

Aktueller lokaler Diff-Stat:
- `10 files changed, 277 insertions(+), 89 deletions(-)` fuer bereits von Git erfasste Dateien
- zusaetzlich neue, noch nicht in `git diff --stat` enthaltene Dokumentations- und Testdateien dieses Runs
