# Homepage Footer Spacing Fix

## Betroffene Dateien

- `app/static/css/md3/components/index.css`
- `app/templates/pages/index.html`
- `app/templates/base.html`
- `app/static/css/layout.css`
- `docs/ui/homepage-footer-spacing-fix.md`
- `docs/md3/index.md`
- `docs/changes/2026-03-24-homepage-footer-spacing-fix.md`
- `.github/instructions/backend.instructions.md`

## Ist-Zustand

Auf der Startseite wurde der Footer auf grossen Desktop-Viewports nicht vollstaendig innerhalb des ersten Viewports sichtbar.
Der Footer war zwar im normalen Dokumentfluss, lag aber unterhalb der sichtbaren Flaeche und war erst nach Scrollen komplett erreichbar.

Die Startseite verwendet:

- `app/templates/pages/index.html` als startseitenlokales Template
- `app/templates/base.html` fuer die App-Shell mit `#main-content`, `.md3-content-wrapper` und `#site-footer`
- `app/static/css/layout.css` fuer die globale Desktop-App-Shell
- `app/static/css/md3/components/index.css` fuer die lokale Landingpage-Struktur
- `app/static/css/md3/components/cards.css` fuer die Landing-Card-Komposition
- `app/static/css/md3/components/footer.css` fuer die Footer-Komponente

## Root Cause

Die Ursache ist eine Kombination aus einem globalen Desktop-Minimum und grosszuegigem startseitenlokalem Spacing:

1. `app/static/css/layout.css`
   - Desktop setzt fuer `#main-content` / `.site-main` ein globales `min-height: calc(100vh - 200px)`.
   - Diese Regel ist fuer kurze Seiten im Standard-Drawer-Layout gedacht.

2. `app/static/css/md3/components/index.css`
   - Die Startseite blendet auf Desktop den permanenten Drawer aus und setzt das Grid lokal auf eine einspaltige Hauptflaeche um.
   - Sie hebt aber die globale Main-Minimumshoehe nicht auf.
   - Gleichzeitig nutzt sie auf Desktop einen luftigen Vertikalrhythmus ueber Logo-Padding, Card-Container-Padding und Card-Gap.

3. Ergebnis
   - Die Homepage traegt weiterhin die globale Mindesthoehe fuer die Hauptflaeche, obwohl ihr Desktop-Layout gar keinen permanenten Drawer mehr nutzt.
   - Diese unnoetige Mindesthoehe plus lokales Landingpage-Spacing drueckt den Footer auf grossen Screens unter die erste Viewport-Flaeche.

## Gewaehlte Loesung

Es wurde bewusst nur `app/static/css/md3/components/index.css` angepasst:

- auf Desktop setzt die Startseite fuer `#main-content` / `.site-main` lokal `min-height: 0`
- das Logo-Padding wird leicht gestrafft
- der Abstand im Kartenbereich wird leicht reduziert, vor allem nach unten zum Footer

Damit bleibt die globale App-Shell fuer alle anderen Seiten unveraendert.

## Warum minimal-invasiv

- keine Aenderung an `app/static/css/layout.css`
- keine globale Aenderung an `body.app-shell`, `#site-footer` oder generischen MD3-Page-Containern
- keine Aenderung an der Landing-Card-Komponente in `cards.css`, obwohl sie nur auf der Startseite verwendet wird
- kein Umbau der Template-Struktur, Card-Komposition oder Footer-Komponente

Der Fix bleibt strikt auf die Startseite begrenzt und respektiert die bestehende MD3-Systemarchitektur.

## Verworfene Alternativen

1. Globale Aenderung von `app/static/css/layout.css`
   - verworfen, weil die Desktop-Minimumshoehe fuer andere kurze Seiten weiterhin sinnvoll sein kann
   - hohes Regressionsrisiko fuer andere Views

2. Globales Reduzieren des Footer-Paddings
   - verworfen, weil das Problem nicht im Footer selbst entsteht
   - wuerde mehrere Seiten optisch veraendern

3. Eingriff in `cards.css` oder generische Landing-Card-Regeln
   - moeglich, aber fuer dieses Problem unnötig breit
   - die eigentliche Fehlanpassung liegt in der Homepage-Kombination aus lokalem Layout und globaler Main-Minimumshoehe

4. Pauschale `100vh`- oder `min-height`-Umbauten im ganzen Layout-System
   - explizit verworfen
   - unnoetig breit und nicht durch den Fehler belegt

## Auswirkungen auf MD3-System und Layout-System

- das MD3-System bleibt intakt
- die globale App-Shell bleibt intakt
- die Landing-Card-Komposition bleibt intakt
- geaendert wurde nur die startseitenspezifische Desktop-Variante in `index.css`

Die Aenderung entspricht damit der bestehenden Pattern-Logik des Projekts: startseitenlokale Ausnahmen liegen in `app/static/css/md3/components/index.css`, nicht in den globalen Shell-Regeln.

## Verifikationsschritte

1. Startseiten-Template und globale Wrapper analysiert:
   - `app/templates/pages/index.html`
   - `app/templates/base.html`

2. Globale Layout-Regeln analysiert:
   - `app/static/css/layout.css`

3. Startseitenlokale Regeln analysiert:
   - `app/static/css/md3/components/index.css`
   - `app/static/css/md3/components/cards.css`
   - `app/static/css/md3/components/footer.css`

4. Laufende Dev-Seite unter `http://127.0.0.1:8000/` inhaltlich geprueft
   - Footer rendert im DOM korrekt
   - Startseite rendert mit Logo, drei Cards und Footer

5. Browser-Automatisierung geprueft
   - kein lokales `npx` vorhanden, daher kein zusaetzlicher Playwright-Messlauf verfuegbar

## Verifikationsergebnis

- Root Cause ist nachvollziehbar auf die Kombination aus globalem Desktop-`min-height` und startseitenlokalem Desktop-Spacing zurueckgefuehrt
- der Fix bleibt startseitenlokal und greift nicht in das globale Layoutsystem ein
- mobile Viewports wurden bewusst nicht veraendert
- andere Seiten erhalten keine neuen CSS-Regeln aus diesem Fix

## Offene Rest-Risiken

- die finale Sichtbarkeit auf jeder lokalen Desktop-Hoehe kann ohne Browser-Messautomation nur ueber die CSS-Analyse und manuelle Dev-Pruefung abgesichert werden
- falls kuenftig das Startseitenlogo oder die Card-Hoehe deutlich wachsen, kann die Startseite erneut einen eigenen Desktop-Tuningbedarf bekommen

Dieses Restrisiko ist bewusst begrenzt, weil die Regel lokal in `index.css` sitzt und nicht globalen Layoutschaden erzeugt.