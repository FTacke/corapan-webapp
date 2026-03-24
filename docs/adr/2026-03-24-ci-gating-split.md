# ADR: Split CI Into Fast Gates And Service Gates

Datum:
- 2026-03-24

Status:
- accepted

Kontext:
- die alte CI mischte servicefreie und servicegebundene Tests unscharf
- der Haupt-Testjob war fachlich entwertet, weil `pytest` uebersprungen und Ruff weichgestellt wurde
- gleichzeitig war die Vollsuite-Matrix ueber `bcrypt` und `argon2` teurer als ihr realer Qualitaetsnutzen

Entscheidung:
- `fast-checks` wird das verpflichtende schnelle Gate fuer Struktur, Lint und servicefreie Tests
- `migration-postgres` wird das kanonische servicegebundene Gate fuer Auth-/App-Start gegen PostgreSQL
- `playwright-e2e` bleibt ein schwerer manueller Browser-Smoke
- `bcrypt` bleibt im Support-Scope nur als fokussierte Kompatibilitaetspruefung, nicht als Vollsuite-Matrix

Folgen:
- Pflicht-CI spiegelt echte Produktqualitaet besser wider
- historische SQLite-Abkuerzungen treiben die CI nicht mehr
- schwere Browserchecks blockieren nicht jeden Push
- Postgres bleibt der kanonische Auth-/Core-Datenpfad auch in der CI
