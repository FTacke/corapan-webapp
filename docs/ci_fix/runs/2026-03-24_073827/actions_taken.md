# Actions Taken

1. App-Konfigurationsvalidierung auf Laufzeit verschoben
   - Warum: Pytest-Sammlung und lokale Repros scheiterten schon beim Import.
   - Erwarteter Effekt: Tests und Hilfsskripte koennen Module importieren, ohne die Produktions-Policy abzuschwaechen.

2. `TestingConfig` eingefuehrt
   - Warum: `create_app("testing")` fiel bislang auf `BaseConfig` zurueck.
   - Erwarteter Effekt: klarer und reproduzierbarer Testpfad fuer CI-Smokes.

3. `http_client.py` auf lazy `BLS_CORPUS`-Validierung umgestellt
   - Warum: BlackLab-Konfiguration blockierte selbst servicefreie Tests beim Import.
   - Erwarteter Effekt: BlackLab bleibt streng konfiguriert, aber erst bei tatsaechlicher Nutzung.

4. SQLAlchemy-Praedikate korrigiert
   - Warum: Python-Operatoren in ORM-Filtern brachen Refresh-Rotation, Session-Invalidierung und Last-Admin-Schutz.
   - Erwarteter Effekt: Auth-/Admin-Schnelltests decken wieder reales Verhalten ab.

5. Instabile oder veraltete Tests bereinigt
   - Warum: einige Tests prueften nicht mehr den aktuellen Vertrag, sondern alte Annahmen.
   - Erwarteter Effekt: Fast-Suite spiegelt die aktuelle Runtime- und Passwort-Policy.

6. Neue fokussierte Hash-Kompatibilitaetsabdeckung hinzugefuegt
   - Warum: `bcrypt`-Unterstuetzung ist noch relevant, aber nicht mehr als Vollsuite-Matrix.
   - Erwarteter Effekt: beide Hash-Pfade bleiben abgesichert, ohne doppelte Gesamtlaufzeit.

7. CI-Workflow neu strukturiert
   - Warum: der bisherige Testjob war fachlich entwertet.
   - Erwarteter Effekt:
     - `fast-checks` als ehrlicher Pflichtcheck
     - `auth-hash-compat` als fokussierter Support-Scope-Check
     - `migration-postgres` als kanonischer Service-Smoke
     - `playwright-e2e` mit Postgres statt SQLite

8. Veraltete GitHub Actions angehoben
   - Warum: sichtbare Warnings fuer alte Node-Runtimes und Action-Majors.
   - Erwarteter Effekt: weniger technische Schulden und saubere Actions-Basis.
