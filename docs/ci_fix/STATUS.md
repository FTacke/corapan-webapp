# CI Status

| Bereich | Status | Befund |
|---|---|---|
| Fast Checks | yellow | Lokal warning-clean reproduziert (`168 passed, 8 skipped, 6 deselected`); erster Remote-Run fiel an veralteter Struktur-Allowlist und wurde nachklassifiziert |
| Auth Hash Support | yellow | Neue fokussierte Kompatibilitaetsabdeckung lokal gruen, Remote-Run ausstehend |
| Migration Postgres | yellow | Erster Remote-Run zeigte, dass der Job fachfremde BlackLab-/UI-Tests mitlief; auf reinen Auth/Postgres-Smoke eingegrenzt |
| Playwright E2E | yellow | Von SQLite-Auth auf Postgres umgebaut, manueller Remote-Run noch ausstehend |
| GitHub Action Warnings | green | Action-Majors aktualisiert; repo-eigene Fast-Pfad-Warnings lokal bereinigt |
| Agent Integration | green | CI-Lessons in Root- und App-Governance sowie Skillfiles integriert |

Offene Probleme:
- Remote-GitHub-Run kann nur ueber oeffentliche GitHub-API, nicht ueber `gh`, analysiert werden.
- Lokale Service-Verifikation fuer Postgres/Playwright konnte nicht vollstaendig erfolgen, weil der Docker-Daemon auf diesem Windows-Host nicht lief.
- `tests/test_advanced_datatables_results.py` ist jetzt explizit als service-/datengebunden zu behandeln; sinnvoll nur mit echtem BlackLab-Kontext.

Bereits geloeste Probleme:
- Importzeit-Abbrueche durch harte `BLS_CORPUS`-/`AUTH_DATABASE_URL`-Validierung in App-Konfigurationsmodulen beseitigt.
- Zweiter Importzeit-Abbruch in `http_client.py` auf Laufzeitvalidierung umgestellt.
- Gemeinsame Auth-/Admin-Root-Cause behoben: SQLAlchemy-Filter nutzten Python-Operatoren wie `is None` und `not`, wodurch Refresh-Rotation, Session-Invalidierung und Last-Admin-Schutz fehlerhaft waren.
- Veraltete bzw. unstabile Tests bereinigt: Runtime-Config-Pfad, Passwortstaerke-Erwartung, data-abhaengiger Docmeta-Enrichment-Test.
- Ruff ist wieder ein ehrlicher Gatekeeper; der alte `|| true`-Bypass im CI-Testjob ist entfernt.
- Vollstaendige `bcrypt`/`argon2`-Matrix fuer die ganze Suite ersetzt durch eine schlanke, explizite Kompatibilitaetsabdeckung.
- Repo-eigene Fast-Pfad-Warnings bereinigt; Live-Smoke-Checks von der Default-Suite getrennt.
- Agent-Governance fuer CI-Integritaet, Testklassifikation und importzeit-sichere Config-Validierung erweitert.
- Remote-Root-Cause im `fast-checks`-Job identifiziert: `app/scripts/check_structure.py` kannte aktuelle legitime App-Root-Dateien nicht.
- Remote-Root-Cause im `migration-postgres`-Job identifiziert: Der Job lief ueber seinen fachlichen Scope hinaus und zog BlackLab-/UI-Tests mit.

Entscheidungsliste:

Behalten:
- `fast-checks` als Pflichtgate fuer servicefreie Qualitaet
- `migration-postgres` als kanonischer Auth-/App-Start-Smoke gegen PostgreSQL
- `playwright-e2e` als manueller Browser-Smoke
- `md3-lint` als UI-/Template-spezifischer Nebenworkflow
- `deploy` als operativer Deploy-Workflow, nicht als Produktqualitaets-CI

Vereinfachen:
- Python-Testjob nicht mehr als Vollsuite-Matrix ueber `bcrypt` und `argon2`
- servicegebundene Voll-App-Tests aus dem Fast-Job herausziehen und in den Postgres-Smoke legen
- `playwright-e2e` nicht mehr ueber SQLite-Auth seeden, sondern ueber kanonisches PostgreSQL

Entfernen oder seltener laufen lassen:
- keine kompletten Workflows entfernt
- alte Vollsuite-Hash-Matrix entfernt
- SQLite-basierte E2E-Seeding-Route aus der CI-Nutzung entfernt; Script bleibt vorerst als historische lokale Hilfe bestehen

Geschaeftskritisch:
- `fast-checks`
- `migration-postgres`
- Deploy-Workflow fuer operativen Rollout, aber nicht als allgemeines Qualitaetsgate

Nice to have:
- `playwright-e2e` als manueller oder spaeter ggf. nightly Browser-Smoke
- `md3-lint` als spezialisierter UI-Konventionscheck

Hashing-Scope:
- `argon2` ist produktionskritisch und muss als Default abgesichert bleiben.
- `bcrypt` ist nur fuer Kompatibilitaet mit Alt-Hashes bzw. Verifikationspfaden relevant.
- Deshalb ist eine Vollsuite-Matrix ueber beide Algorithmen nicht mehr gerechtfertigt.
- Beibehalten wird stattdessen eine fokussierte Kompatibilitaetsabdeckung in `tests/test_auth_hash_algorithms.py`.
