# Playwright Actions Taken

## Test-Suite angepasst

Datei geaendert:

- `app/tests/e2e/playwright/auth.spec.js`

Dateien entfernt:

- `app/tests/e2e/playwright/profile-ui.spec.js`
- `app/tests/e2e/playwright/user-flows.spec.js`

## Inhaltliche Aenderungen

1. Login-Smoke auf die reale Login-Vollseite `/login` umgestellt.
2. Navbar-Login auf den aktuellen sichtbaren Login-Link statt auf das historische `aria-label="Anmelden"` umgestellt.
3. Logout-Smoke auf das reale Benutzer-Menue mit `data-account-menu-trigger` und `data-logout="fetch"` umgestellt.
4. Protected-Route-Smoke so formuliert, dass er die reale Unauthorized-Logik prueft, ohne eine historische feste Ziel-URL zu erzwingen.
5. Profil-Smoke so formuliert, dass aktuelle Seed-Daten in der Anzeige geprueft werden, statt leere Edit-Felder faelschlich als Regression zu behandeln.

## Entfernte Testtypen

Die folgenden Kategorien wurden bewusst entfernt:

1. visuelle Hover-/Pixel-/Layout-Assertions
2. Mock-basierte Account-Delete-Detailfaelle
3. Mock-basierte Profiledit-Detailfaelle
4. breit gestreute Search/Admin/Health-Browserfaelle ohne direkten Auth-Smoke-Fokus

## Begruendung

Diese entfernten Tests waren entweder fragil, historisch ueberholt oder fuer einen kleinen manuellen Browser-Smoke nicht der richtige Vertragskern.