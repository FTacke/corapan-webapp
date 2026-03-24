# Run Summary

Ziel dieses Folge-Runs:
- lokale Warnungsbereinigung abschliessen
- Fast-Checks erneut validieren
- CI-Lessons in Agent-Governance und Skills integrieren
- Push- und Remote-Verifikation vorbereiten

Ergebnis dieses Runs:
- repo-eigene Fast-Suite-Warnings bereinigt
- `tests/test_advanced_api_quick.py` als `live` klassifiziert und aus dem Default-Fast-Pfad entfernt
- timezone-naive `datetime.utcnow`-Hilfen durch timezone-aware Helfer ersetzt
- bekannte Passlib-Deprecation eng auf pytest-Ebene gefiltert
- Agent-Governance-Dateien um CI-/Test-Integritaetsregeln erweitert
- erster Remote-Run ausgewertet: `auth-hash-compat` gruen, Deploy gruen, `playwright-e2e` auf Push korrekt geskippt
- Remote-Fehler auf zwei konkrete Ursachen reduziert und korrigiert: Struktur-Allowlist in `check_structure.py` sowie zu breiter Test-Scope in `migration-postgres`

Lokaler Validierungsstand:
- Ruff gruen
- Fast-Suite gruen: `168 passed, 8 skipped, 6 deselected`
- keine verbleibenden repo-eigenen Warnings im validierten Fast-Pfad

Remote-Stand:
- erster Push-Run ausgewertet, Folge-Push nach Remote-Fix noch ausstehend