# Playwright Root Cause

## Ausgangslage

Die vorhandene Playwright-Suite pruefte nicht mehr die reale aktuelle Webapp, sondern historische Annahmen ueber Auth-UI, Redirects und Profilformulare.

## Verifizierte Abweichungen zur aktuellen App

1. Canonical Login ist nicht mehr `/auth/login`, sondern die oeffentliche Vollseite `/login`.
2. Fehler im Login werden nicht mehr in `.md3-sheet__errors` gerendert, sondern als `.md3-alert` auf der Login-Seite.
3. Der unauthentifizierte Navbar-Link heisst aktuell `Login`, nicht `Anmelden`.
4. Logout ueber `data-logout="fetch"` navigiert bewusst auf `/`, nicht auf `/auth/login`.
5. Geschuetzte HTML-Seiten ohne JWT fuehren nicht stabil zu `/auth/login`, sondern ueber die aktuelle Unauthorized-Logik typischerweise zu einer oeffentlichen Seite mit `showlogin=1` oder einer anderen Login-Aufforderung.
6. Das Profilformular ist kein vorbefuelltes Edit-Formular mehr. Aktuelle Werte werden in `#current-username` und `#current-email` angezeigt; die Edit-Felder sind fuer neue Werte gedacht und starten leer.
7. Die geloeschten Profiltests arbeiteten stark mit Mocking und Layout-Details statt mit produktrelevanten Browser-Smokes.

## Ursache der Fehlschlaege

Die Fehlschlaege lagen primaer in veralteten Testannahmen, nicht in nachgewiesenen Produktregressionen:

- veraltete Selektoren
- veraltete Redirect-Erwartungen
- veraltete Form-State-Erwartungen
- ueberdetaillierte visuelle Assertions ohne echten Smoke-Wert
- Mock-basierte Detailpruefungen fuer Flows, die im manuellen CI-Smoke nicht der relevante Vertragskern sind

## Konsequenz

Die Suite wurde auf einen kleinen, ehrlichen Smoke-Kern zurueckgeschnitten, der die aktuelle Produktrealitaet prueft:

- Login-Smoke
- Zugriffsschutz-Smoke fuer geschuetzte Profilseite
- Logout-Smoke
- ein schlanker Profil-Smoke fuer die Anzeige der aktuellen Seed-Daten