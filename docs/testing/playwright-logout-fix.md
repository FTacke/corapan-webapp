# Playwright Logout Fix

## Ursache

Der Logout-Test in der Playwright-Suite klickte mit dem globalen Selektor `[data-logout="fetch"]` auf ein Element, das in der aktuellen responsiven Navigation mehrfach existiert.

Die Seite rendert denselben Logout-Mechanismus in mehreren Containern:

- im kanonischen Benutzermenue der Top App Bar
- im Navigation Drawer
- je nach responsivem Zustand potenziell mehrfach sichtbar oder zumindest im DOM vorhanden

Dadurch lief der Test in einen Playwright-Strict-Mode-Fehler, weil der Selektor nicht eindeutig war.

## Aenderung

Der Test verwendet jetzt nicht mehr den globalen Logout-Selektor, sondern schraenkt den Klick auf das geoeffnete Benutzermenue der Top App Bar ein:

1. Menue-Trigger klicken
2. sichtbares `[data-user-menu]` abwarten
3. Logout nur innerhalb dieses Containers aufloesen und klicken

## Warum der neue Selektor stabiler ist

Der neue Selektor ist stabiler, weil er die kanonische Logout-Interaktion des Tests ausdrueckt:

- Der Test oeffnet explizit das Benutzer-Menue der Top App Bar.
- Der anschliessende Logout-Klick ist auf genau diesen Container begrenzt.
- Drawer-Duplikate oder andere responsive Logout-Links werden dadurch nicht mehr versehentlich mitgematcht.

Damit bleibt der Test semantisch sauber und robust gegen responsive Doppel-Rendering-Faelle, ohne die App selbst aendern zu muessen.