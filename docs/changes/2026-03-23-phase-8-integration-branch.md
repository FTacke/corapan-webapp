# Phase 8 integration branch

Datum: 2026-03-23

## Was geaendert wurde

- ein neuer lokaler Branch `root-lift-integration` wurde direkt auf Basis von `origin/main` erstellt
- der Baum von `origin/root-lift-review` wurde kontrolliert als neuer Projektzustand uebernommen
- die Uebernahme erfolgte ohne Merge, ohne `--allow-unrelated-histories` und ohne Cherry-Pick
- der Integrationsstand wurde in `docs/repo_finish/phase_8_integration_branch.md` dokumentiert

## Warum

Der publizierte Review-Branch `root-lift-review` ist wegen fehlender gemeinsamer Merge-Base nicht der richtige technische Mechanismus fuer den spaeteren Uebergang nach `main`.

Die Root-Lift-Zielstruktur musste deshalb auf einem separaten Branch mit `origin/main` als Historienbasis kontrolliert uebernommen werden, damit ein spaeterer PR normal auf der `main`-Historie aufsetzen kann.

## Operative Wirkung

- `root-lift-integration` ist jetzt die lokale Integrationsgrundlage fuer einen spaeteren PR
- der Root-Lift-Zielbaum ist auf einer `origin/main`-basierten Historie dargestellt
- Compose-Render und minimaler App-Factory-Start mit kanonischen Dev-Variablen wurden erfolgreich verifiziert

## Kompatibilitaet und Grenzen

- es wurde nicht nach `main` gepusht
- es wurde kein Deploy ausgeloest
- vor einem spaeteren echten PR bleiben CI-Auswertung, Workflow-Review und die bewusste Freigabe des Branches erforderlich