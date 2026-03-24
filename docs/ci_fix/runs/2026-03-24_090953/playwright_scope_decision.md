# Playwright Scope Decision

## Zielbild fuer `playwright-e2e`

Der manuelle Browser-Job soll einen kleinen, stabilen Produkt-Smoke liefern und nicht die Rolle eines vollstaendigen Frontend-Integrations- oder Visual-Regression-Suites uebernehmen.

## Behaltene Tests

1. Login-Smoke
2. Zugriffsschutz-Smoke fuer die geschuetzte Profilseite
3. Logout-Smoke
4. schlanker Profil-Smoke mit Anzeige der Seed-Daten

## Nicht mehr Teil des Smoke-Umfangs

1. visuelle Pixel-/Hover-Stabilitaet von Buttons und Icons
2. detailreiche Mock-Interaktionen rund um Kontoloeschung
3. detailreiche Mock-Interaktionen rund um Profil-PATCH-Payloads
4. browserbasierte Search-/Admin-/Health-Pruefungen ohne unmittelbaren Auth-Smoke-Wert

## Entscheidungsregel

Ein Playwright-Test bleibt nur dann im manuellen Smoke-Job, wenn er gleichzeitig:

1. einen realen produktrelevanten Benutzerfluss prueft,
2. stabil gegen legitime UI-Weiterentwicklung bleibt,
3. ohne starre historische Selektoren oder Layoutdetails auskommt,
4. ohne kuenstliches Mocking des eigentlichen Browser-Vertrags auskommt.

## Offene Einschraenkung

Auf diesem Windows-Host war keine lokale End-to-End-Ausfuehrung mit Node plus laufendem Postgres-Stack verfuegbar. Die Aenderung wurde daher statisch gegen die aktuelle Implementierung und CI-Wiring geprueft; die finale Verifikation bleibt der manuelle `playwright-e2e`-Workflow-Run.