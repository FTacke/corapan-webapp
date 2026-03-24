# MD3 Index

## 2026-03-24 Homepage Footer Spacing

- Dokumentation: `docs/ui/homepage-footer-spacing-fix.md`
- Root Cause: Die Startseite erbte auf Desktop die globale Main-Mindesthoehe aus `app/static/css/layout.css`, obwohl sie ihren permanenten Drawer lokal deaktiviert. Zusammen mit dem luftigen Landingpage-Spacing in `app/static/css/md3/components/index.css` drueckte das den Footer unter die erste Viewport-Flaeche.
- Loesung: rein startseitenlokale Desktop-Korrektur in `app/static/css/md3/components/index.css`, keine globale App-Shell-Aenderung.
- Betroffene Implementierungsdatei: `app/static/css/md3/components/index.css`
- Governance-Hinweis: Homepage-/Landingpage-Layoutprobleme zuerst lokal in `index.css` pruefen, nicht pauschal in den globalen Shell-Regeln.