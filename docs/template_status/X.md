# Popup- und Tooltip-Spezifikation fuer Karten

Diese Datei dokumentiert das aktuelle Karten-UI im Projekt so, dass es in einem anderen Projekt praezise nachgebaut werden kann.

Der Schwerpunkt liegt auf:

- der strukturellen Definition von Popups und Tooltips
- der Rolle von Leaflet als Layout-Lieferant
- der genauen Definition des Schliessen-X
- den projektweiten Overrides fuer Position, Groesse und Verhalten

## 1. Systemgrenze: Was stammt von Leaflet, was vom Projekt?

Die Karten verwenden Leaflet. Das Popup-System ist deshalb zweistufig aufgebaut:

1. Leaflet erzeugt die Popup-DOM-Struktur inklusive Close-Button automatisch.
2. Das Projekt ueberschreibt Verhalten und Aussehen zentral ueber `map_ui.js` und `50_map.css`.

Fuer ein anderes Projekt ist das entscheidend: Das X wird hier nicht als eigener HTML-Baustein in den Popup-Content geschrieben, sondern von Leaflet erzeugt und anschliessend per CSS gestaltet.

## 2. Relevante Stellen im aktuellen Projekt

### JavaScript

- `docs/assets/javascripts/map_ui.js`
  - `popupOptions(className)` definiert die Popup-Optionen.
  - `bindClickPopup(...)` bindet Popups an Marker.
  - `enablePopupCloseUX(map)` ergaenzt Schliessen per Klick auf die Karte und per `Escape`.

### CSS

- `docs/assets/styles/50_map.css`
  - definiert Popup- und Tooltip-Design zentral
  - enthaelt die Projekt-Overrides fuer `.leaflet-popup-close-button`

### Framework-Basis

- `docs/assets/vendor/leaflet/leaflet.js`
  - erzeugt die DOM-Struktur des Popups und setzt den Close-Button nur dann, wenn `closeButton: true`
- `docs/assets/vendor/leaflet/leaflet.css`
  - liefert die Default-Positionierung und die Standard-Groesse des Close-Buttons

## 3. Popup-Architektur

### 3.1 Aktivierung in JavaScript

Zentrale Popup-Optionen:

```js
function popupOptions(className) {
  const mobile = isMobileViewport();
  return {
    className: className || 'corapan-popup',
    closeButton: true,
    autoClose: true,
    closeOnClick: false,
    autoPan: true,
    keepInView: true,
    maxWidth: mobile ? 300 : 320,
    minWidth: mobile ? 180 : 200,
    autoPanPaddingTopLeft: mobile ? [20, 80] : [50, 100],
    autoPanPaddingBottomRight: mobile ? [20, 20] : [50, 50]
  };
}
```

Konsequenz fuer das X:

- Das X existiert nur, weil `closeButton: true` gesetzt ist.
- Es ist kein Teil des Inhalts von `.popup-sprachenkarte`.
- Jede gestalterische Definition des X muss deshalb an `.leaflet-popup-close-button` ansetzen.

### 3.2 DOM-Struktur des Popups

Leaflet erzeugt sinngemaess folgende Struktur:

```html
<div class="leaflet-popup corapan-popup leaflet-zoom-animated">
  <div class="leaflet-popup-content-wrapper">
    <div class="leaflet-popup-content">
      <div class="popup-sprachenkarte">...</div>
    </div>
  </div>

  <div class="leaflet-popup-tip-container">
    <div class="leaflet-popup-tip"></div>
  </div>

  <a class="leaflet-popup-close-button" role="button" aria-label="Close popup" href="#close">
    <span aria-hidden="true">&#215;</span>
  </a>
</div>
```

Wichtig fuer das Layout:

- der Close-Button ist ein direktes Kind von `.leaflet-popup`
- der Close-Button liegt nicht in `.leaflet-popup-content-wrapper`
- der Close-Button liegt nicht in `.leaflet-popup-content`
- das X wird absolut ueber dem Popup positioniert

## 4. Default-Verhalten in Leaflet

Leaflet liefert standardmaessig:

```css
.leaflet-container a.leaflet-popup-close-button {
  position: absolute;
  top: 0;
  right: 0;
  width: 24px;
  height: 24px;
  font: 16px/24px Tahoma, Verdana, sans-serif;
  color: #757575;
  background: transparent;
}
```

Das bedeutet:

- Ankerpunkt ist immer die obere rechte Ecke von `.leaflet-popup`.
- Ohne Projekt-Overrides sitzt das X direkt in der Ecke ohne Innenabstand.
- Die Klickflaeche ist standardmaessig relativ klein: `24 x 24 px`.

## 5. Projekt-Override fuer das Schliessen-X

Im aktuellen Projekt wird der Leaflet-Standard bewusst ueberschrieben:

```css
.md-typeset .book-map .leaflet-popup-close-button {
  top: 10px;
  right: 10px;
  inline-size: 30px;
  block-size: 30px;
  padding: 0;
  border-radius: 999px;
  color: var(--book-muted);
  font-size: 24px;
  font-weight: 400;
  line-height: 30px;
  text-align: center;
}

.md-typeset .book-map .leaflet-popup-close-button:hover {
  color: var(--book-fg);
  background: transparent;
}

@media (max-width: 767px) {
  .md-typeset .book-map .leaflet-popup-close-button {
    top: 8px;
    right: 8px;
  }
}
```

### 5.1 Exakte Gestaltungsdefinition des X

Das X ist in diesem System:

- ein absolut positionierter Overlay-Button
- an der oberen rechten Ecke des Popup-Containers verankert
- nach innen eingerueckt statt exakt an die Ecke geklebt
- visuell kreisfoermig gedacht durch `border-radius: 999px`
- standardmaessig ohne sichtbare Fuelle oder Border
- im Ruhemodus dezent (`var(--book-muted)`)
- beim Hover nur farblich hervorgehoben (`var(--book-fg)`)

### 5.2 Exakte Positionslogik

Die Position wird nicht relativ zum Content, sondern relativ zum gesamten Popup gesetzt:

- Desktop: `top: 10px`, `right: 10px`
- Mobile bis `767px`: `top: 8px`, `right: 8px`

Damit ist die Layout-Regel:

- Das X schwebt als Bedien-Overlay ueber der Karteikarte.
- Es sitzt innerhalb des visuellen Popup-Rahmens, aber ausserhalb des Content-Flows.
- Seine Position ist durch Insets definiert, nicht durch Margin oder Grid/Flex.

## 6. Zusammenspiel von X und Popup-Innenlayout

Das Popup selbst ist so definiert:

```css
.md-typeset .book-map .leaflet-popup-content {
  padding: 16px 18px 16px;
  max-inline-size: var(--map-popup-max-width);
  max-block-size: min(360px, 62dvh);
  overflow-x: hidden;
  overflow-y: auto;
}
```

Wichtige Konsequenz:

- Das Projekt reserviert keinen eigenen rechten Spaltenbereich fuer den Close-Button.
- Das X liegt daher als Overlay ueber dem oberen rechten Bereich des Popups.
- Das funktioniert gut, solange Titel und Meta kompakt bleiben.

Fuer eine Uebertragung in ein anderes Projekt gilt deshalb:

1. Wenn kurze Titel erwartet werden, kann dieses Overlay-Modell unveraendert uebernommen werden.
2. Wenn lange Titel haeufig sind, sollte zusaetzlich rechter Innenabstand fuer den Header vorgesehen werden.

Empfohlene robuste Variante fuer lange Titel:

```css
.popup-header {
  padding-inline-end: 2.5rem;
}
```

Das ist im aktuellen Projekt nicht gesetzt, aber fuer allgemeinere Wiederverwendung oft sinnvoll.

## 7. Popup-Karte: restliches Layout

Das X sitzt auf einer bewusst kompakten Informationskarte. Die zentralen Werte:

```css
:root {
  --map-popup-radius: 16px;
  --map-popup-max-width: 320px;
  --map-popup-font-size: 0.7rem;
  --map-popup-line-height: 1.4;
  --map-popup-title-scale: 1.28;
  --map-popup-title-gap: 10px;
  --map-popup-block-gap: 10px;
}
```

Popup-Container:

```css
.md-typeset .book-map .leaflet-popup-content-wrapper {
  padding: 0;
  border: 1px solid var(--book-border);
  background: color-mix(in srgb, var(--book-bg) 97%, white);
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.12);
}
```

Popup-Titel:

```css
.md-typeset .book-map .popup-title {
  font-size: calc(1em * var(--map-popup-title-scale));
  line-height: var(--map-popup-title-line-height);
  font-weight: 700;
  color: var(--book-fg);
}
```

Aus Design-Sicht heisst das:

- Der Button muss sich in einen ruhigen, editoriellen Kartenstil einfuegen.
- Deshalb ist das X zwar gross genug zum Treffen, aber visuell untergeordnet.
- Es bekommt keine starke Flaeche, keinen Schatten und keinen separaten Rahmen.

## 8. Schliessen-Verhalten

Das Projekt kombiniert drei Schliesswege:

### 8.1 Klick auf X

Standardverhalten von Leaflet ueber den generierten Close-Button.

### 8.2 Klick auf die Karte

Ergaenzt in `enablePopupCloseUX(map)`:

```js
map.on('click', () => {
  map.closePopup();
});
```

### 8.3 Escape-Taste

Ebenfalls in `enablePopupCloseUX(map)`:

```js
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') {
    return;
  }

  document
    .querySelectorAll('.leaflet-popup-close-button')
    .forEach((button) => button.click());
});
```

Design-Interpretation:

- Das X ist sichtbar und explizit.
- Die Interaktion ist aber nicht auf das X allein angewiesen.
- Das Popup bleibt dadurch auf Touch-Geraeten und bei dichter Kartenbelegung leichter kontrollierbar.

## 9. Tooltip-System

Das Projekt besitzt bereits eine zentrale Tooltip-Gestaltung, nutzt derzeit aber in den Karten-Skripten keine gesonderte, projektweite Tooltip-Bindung wie bei Popups.

Definiert ist:

```css
.md-typeset .book-map .leaflet-tooltip {
  border: 1px solid var(--book-border);
  border-radius: 8px;
  background: var(--map-panel-bg-strong);
  color: var(--book-fg);
  box-shadow: var(--map-shadow-sm);
  padding: 6px 8px;
  font-size: var(--map-tooltip-font-size);
  line-height: var(--map-tooltip-line-height);
}
```

Fuer die Uebertragung wichtig:

- Tooltips sind hier als leichte, transiente Labels gedacht.
- Tooltips haben kein Schliessen-X.
- Ein X ist nur fuer persistente Popup-Karten vorgesehen.

## 10. Praezise Uebertragungsregel fuer ein anderes Projekt

Wenn dieses Verhalten in einem anderen Leaflet-Projekt nachgebaut werden soll, ist die kuerzeste korrekte Spezifikation:

### 10.1 JavaScript-Regel

```js
marker.bindPopup(html, {
  closeButton: true,
  closeOnClick: false,
  autoClose: true,
  autoPan: true,
  keepInView: true,
  maxWidth: 320,
  minWidth: 200
});
```

### 10.2 CSS-Regel fuer den Button

```css
.leaflet-popup-close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 30px;
  height: 30px;
  padding: 0;
  border-radius: 999px;
  color: var(--popup-close-color-idle, #6b7280);
  font-size: 24px;
  font-weight: 400;
  line-height: 30px;
  text-align: center;
  background: transparent;
}

.leaflet-popup-close-button:hover,
.leaflet-popup-close-button:focus {
  color: var(--popup-close-color-active, #111827);
  background: transparent;
}
```

### 10.3 Layout-Regel in einem Satz

Das X ist ein absolut positionierter, dezent gestalteter Overlay-Button in der oberen rechten Innenecke des Leaflet-Popups; es gehoert nicht zum Content-Flow, sondern wird vom Framework erzeugt und vom Projekt nur visuell und positionsbezogen ueberschrieben.

## 11. Empfehlung fuer Nachbau ohne Leaflet-Abhaengigkeit

Falls das andere Projekt kein Leaflet nutzt, sollte dieselbe Semantik beibehalten werden:

- Close-Button als eigenes Overlay-Element auf Container-Ebene
- Verankerung oben rechts ueber `position: absolute`
- Bedienflaeche mindestens `30 x 30 px`
- visuell sekundar, aber funktional klar treffbar
- Tooltips weiterhin ohne Close-Button

Minimalstruktur ohne Leaflet:

```html
<div class="map-popup-card">
  <button class="map-popup-card__close" type="button" aria-label="Popup schliessen">×</button>
  <div class="map-popup-card__content">...</div>
</div>
```

```css
.map-popup-card {
  position: relative;
}

.map-popup-card__close {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #6b7280;
  font-size: 24px;
  line-height: 30px;
  text-align: center;
  cursor: pointer;
}
```

## 12. Kernaussage

Fuer dieses System ist das X nicht einfach ein Icon, sondern ein Layout-Prinzip:

- erzeugt vom Popup-Framework
- absolut an den Popup-Container gebunden
- mit definiertem Innenabstand positioniert
- nicht als Inhaltsbaustein modelliert
- nur fuer persistente Popups, nicht fuer Tooltips

Genau dieses Prinzip sollte in einem anderen Projekt uebernommen werden, wenn das Verhalten und die visuelle Logik konsistent bleiben sollen.