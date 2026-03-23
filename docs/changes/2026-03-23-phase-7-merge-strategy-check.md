# Phase 7 merge strategy check

Datum: 2026-03-23

## Was dokumentiert wurde

- die reale Historienlage zwischen `origin/main` und `origin/root-lift-review` wurde als unrelated-histories-Sonderfall festgehalten
- GitHub-Compare-Verhalten fuer diesen Fall wurde dokumentiert
- die Strategien normaler PR-Merge, Review-only, Branch-Ersatz, Cherry-Pick/Rebase und Bridge-Integration wurden gegeneinander bewertet
- die Empfehlung wurde in `docs/repo_finish/phase_7_merge_strategy_check.md` festgehalten

## Warum

Nach dem erfolgreichen Push von `root-lift-review` war der naechste offene Punkt nicht mehr die Publikation, sondern der spaetere sichere Uebergang nach `main`.

Da der publizierte Review-Branch keine gemeinsame Merge-Base mit `origin/main` besitzt, reicht ein normaler PR-Reflex hier nicht aus. Die technische Uebernahmemethode musste deshalb vorab explizit bewertet werden.

## Operative Wirkung

- `root-lift-review` bleibt der publizierte Review- und Sichtungsstand
- ein direkter Standard-Merge nach `main` ist nicht die empfohlene Hauptstrategie
- fuer den spaeteren Uebergang wird stattdessen ein separater Integrations-Branch auf Basis von `origin/main` empfohlen, der den Root-Lift-Baum kontrolliert uebernimmt

## Kompatibilitaet und Grenzen

- es wurde kein Merge ausgefuehrt
- es wurde nicht nach `main` gepusht
- es wurde kein Deploy ausgeloest
- vor einem spaeteren echten Integrations-PR bleiben erneute lokale Struktur-, Runtime- und CI-Pruefungen erforderlich