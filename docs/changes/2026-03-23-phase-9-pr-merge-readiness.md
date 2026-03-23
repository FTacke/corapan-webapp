# Phase 9 PR merge readiness

Datum: 2026-03-23

## Was dokumentiert und gehaertet wurde

- der finale PR-/Merge-Readiness-Check fuer `root-lift-integration -> main` wurde dokumentiert
- der lokale Branch-Zustand wurde bereinigt, indem das irrefuehrende Tracking von `root-lift-integration` auf `origin/main` entfernt wurde
- `app/scripts/deploy_prod.sh` honoriert jetzt bei GitHub Actions die vom Workflow gesetzte `GITHUB_SHA`
- `.github/workflows/ci.yml` erzeugt fuer den Minimalruntime-Check jetzt `data/config` statt einer veralteten Root-`config`-Struktur

## Warum

Vor einem spaeteren bewussten Merge nach `main` musste abschliessend geklaert werden, ob der Integrations-Branch nicht nur lokal plausibel, sondern auch release-seitig belastbar genug ist.

Dabei zeigte sich ein echter release-naher Restpunkt: der Deploy-Workflow resetete serverseitig bereits auf `${GITHUB_SHA}`, waehrend `deploy_prod.sh` danach erneut stumpf `origin/main` uebernahm. Das war fuer einen kontrollierten Release-Merge unnötig riskant und wurde direkt korrigiert.

## Operative Wirkung

- `root-lift-integration` ist jetzt lokal ein klarer Release-Kandidat ohne irrefuehrendes Upstream-Tracking
- der spaetere Deploy nach einem Merge auf `main` bleibt sauberer an die gemergte SHA gebunden
- CI-Minimalruntime spiegelt den kanonischen `data/config`-Vertrag besser wider
- die finale Merge-Entscheidung kann jetzt auf einer expliziten Pre-/Post-Merge-Checkliste basieren

## Kompatibilitaet und Grenzen

- es wurde nicht nach `main` gepusht
- es wurde kein Merge ausgefuehrt
- es wurde kein Deploy ausgeloest
- `root-lift-integration` liegt weiterhin nur lokal und muss fuer einen echten PR noch bewusst gepusht werden
- einzelne operative Docs ausserhalb der kanonischen READMEs enthalten weiterhin Altpfad-Drift und sollten spaeter separat bereinigt werden