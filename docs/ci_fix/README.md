# CI Fix Audit Log

Dieser Ordner dokumentiert den laufenden Audit- und Reparaturprozess fuer die Repository-CI.

Zweck:
- nachvollziehbare Inventarisierung aller Workflows und Jobs
- belegte Root-Cause-Analyse statt Vermutungen
- persistente Ablage pro Audit-/Fix-Durchgang
- klare Trennung zwischen lokalen Reproduktionen und echten GitHub-Run-Daten

Vorgehensweise:
1. Workflows und zugehoerige Projekt-/Runtime-Dateien lesen
2. direkte GitHub-Daten nutzen, falls `gh` verfuegbar ist
3. sonst Jobs lokal moeglichst CI-nah reproduzieren
4. Root Causes einzeln beheben
5. nach jedem Durchgang `docs/ci_fix/runs/<timestamp>/` aktualisieren

Aktuellen Status lesen:
- [STATUS.md](STATUS.md) zeigt den Gesamtstand, offene Probleme und Entscheidungen
- der neueste Ordner unter `runs/` enthaelt die Detailprotokolle eines einzelnen Durchgangs
- `logs/` in jedem Run enthaelt die ersten relevanten Fehlerauszuege oder Repro-Notizen
