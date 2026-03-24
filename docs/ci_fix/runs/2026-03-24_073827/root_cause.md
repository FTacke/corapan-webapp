# Root Cause Analysis

## Problem 1: Importzeit-Initialisierung machte Pytest-Sammlung fragil

Root Cause:
- `app/src/app/config/__init__.py` und `app/src/app/extensions/http_client.py` erzwangen Pflichtvariablen bereits beim Modulimport.

Evidenz:
- lokaler Vollsuite-Lauf scheiterte noch vor echter Testausfuehrung mit `RuntimeError` fuer `BLS_CORPUS` bzw. `AUTH_DATABASE_URL`
- dieselben Fehler traten beim servernahen Repro des alten `playwright-e2e`-Environments auf

Alternative Hypothesen:
- fehlende Python-Pakete waren nur ein lokales Vorproblem, aber nicht der fachliche Root Cause

## Problem 2: Mehrere Auth-/Admin-Fehler hatten dieselbe ORM-Ursache

Root Cause:
- SQLAlchemy-Queries nutzten Python-Operatoren wie `is None`, `is not None` und `not` innerhalb von `.filter()`/`.where()` statt SQLAlchemy-Ausdruecken.

Evidenz:
- `rotate_refresh_token()` benutzte `RefreshToken.replaced_by is None` und `RefreshToken.revoked_at is None`
- `revoke_all_refresh_tokens_for_user()` benutzte `RefreshToken.revoked_at is None`
- `admin_users.py` benutzte `UserModel.deleted_at is None`, `UserModel.deleted_at is not None`, `not UserModel.is_active`
- nach Korrektur auf `.is_(None)`, `.is_not(None)` und `.is_(False)` wurden vormals rote Auth-/Admin-Tests gruene Schnelltests

Alternative Hypothesen:
- Cookie-Pfade oder Passlib/Bcrypt-Warnungen erklaerten die roten Tests nicht konsistent genug

## Problem 3: Testjob war fachlich entwertet

Root Cause:
- der bisherige `test`-Job uebersprang `pytest` komplett und liess Ruff durch `|| true` weich werden.

Evidenz:
- Workflow-Datei enthielt explizit `echo "Pytest disabled in CI"`
- Workflow-Datei enthielt `ruff check src/app || true`

Alternative Hypothesen:
- kein echter Build-/Infra-Engpass noetig, um das Verhalten zu erklaeren; die Entwertung war direkt im Workflow kodiert

## Problem 4: `playwright-e2e` lief auf einem historischen SQLite-Pfad

Root Cause:
- der Workflow seedete `sqlite:///data/db/auth_e2e.db` und startete die App ohne kanonische Pflichtvariablen.

Evidenz:
- alte Workflow-Datei setzte `AUTH_DATABASE_URL: sqlite:///data/db/auth_e2e.db`
- lokaler Serverstart mit denselben Variablen brach vor dem App-Start mit `BLS_CORPUS`-Fehler ab

Alternative Hypothesen:
- Playwright selbst war nicht der erste Fehler, sondern nur der nachgelagerte Konsument eines nicht gestarteten Servers

## Problem 5: `bcrypt`/`argon2`-Vollmatrix war ueberbreit

Root Cause:
- die Matrix pruefte die gesamte Suite doppelt, obwohl produktionskritisch nur `argon2` als Default und `bcrypt` als Kompatibilitaetsverifikation relevant sind.

Evidenz:
- Produktdoku und Konfiguration nennen `argon2` als empfohlenen bzw. Standardpfad
- neue fokussierte Tests belegen beide Hash-Pfade ohne Vollsuite-Duplizierung

Alternative Hypothesen:
- ein voller zweiter Pytest-Lauf mit `bcrypt` liefert keinen proportionalen Mehrwert gegenueber einer expliziten Kompatibilitaetspruefung
