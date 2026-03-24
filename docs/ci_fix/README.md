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
# CI Fix Notes

This directory is for the current CI stabilization state only.

Keep it lean:

- record durable CI findings
- summarize the current CI contract
- do not keep a long tail of timestamped run transcripts once the lesson has been integrated into workflows, tests, or agent rules

Aktuellen Status lesen:
- [STATUS.md](STATUS.md) zeigt den Gesamtstand, offene Probleme und Entscheidungen
- der neueste Ordner unter `runs/` enthaelt die Detailprotokolle eines einzelnen Durchgangs
- `logs/` in jedem Run enthaelt die ersten relevanten Fehlerauszuege oder Repro-Notizen
