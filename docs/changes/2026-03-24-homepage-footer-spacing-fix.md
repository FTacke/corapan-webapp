# 2026-03-24 Homepage Footer Spacing Fix

Scope:
- UI-Implementierung unter `app/`
- Agent-Governance-Hinweis unter `.github/`

Geaendert:
- startseitenlokaler Desktop-Fix in `app/static/css/md3/components/index.css`
- Dokumentation des Root Cause und der verwarften Alternativen unter `docs/ui/`
- kurze Governance-Notiz fuer kuenftige Homepage-Layoutarbeit in `.github/instructions/backend.instructions.md`

Warum:
- die Startseite erbte eine globale Desktop-Main-Mindesthoehe, obwohl sie auf Desktop den permanenten Drawer ausblendet
- zusammen mit dem lokalen Landingpage-Spacing drueckte das den Footer unter die erste Viewport-Flaeche

Auswirkung:
- auf grossen Screens ist die Startseite kompakter und der Footer soll ohne unnoetiges Scrollen vollstaendig erreichbar bleiben
- andere Seiten behalten die bestehende globale App-Shell-Geometrie

Kompatibilitaet:
- keine globale Layout-Neuarchitektur
- keine Aenderung am Footer- oder Card-System fuer andere Seiten