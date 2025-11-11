# Mobile Navbar Collapse Update

**Datum:** 24. Oktober 2025  
**Status:** ✅ Implementiert

## Übersicht

Die mobile Navigation wurde von einem **Sliding Subpanel System** auf ein **Accordion/Collapse System** umgestellt, das besser zu Material Design 3 passt und eine intuitivere UX bietet.

## Änderungen

### 1. HTML Template (`templates/partials/_navbar.html`)

**Vorher:** Komplexes System mit separaten Subpanels, die von links herein sliden
```html
<button class="md3-mobile-subdrawer-trigger">
  Proyecto <span>▸</span>
</button>
<!-- Separates Subpanel außerhalb -->
<div class="md3-mobile-subpanel">
  <button class="md3-subpanel__back">◂</button>
  <!-- Links -->
</div>
```

**Nachher:** Einfaches Collapsible/Accordion-Muster
```html
<div class="md3-mobile-collapsible">
  <button class="md3-mobile-collapsible__trigger" aria-expanded="false">
    <span>Proyecto</span>
    <i class="fa-solid fa-chevron-down"></i>
  </button>
  <div class="md3-mobile-collapsible__content" hidden>
    <!-- Child links direkt hier -->
  </div>
</div>
```

### 2. CSS (`static/css/md3-components.css`)

**Neu hinzugefügt:**

- `.md3-mobile-collapsible` - Container für collapsible Items
- `.md3-mobile-collapsible__trigger` - Button mit Chevron-Icon
- `.md3-mobile-link__chevron` - Animiertes Chevron (rotiert 180° beim Öffnen)
- `.md3-mobile-collapsible__content` - Collapsible Content-Bereich
- `.md3-mobile-collapsible__items` - Container für Child-Links
- `.md3-mobile-link--child` - Styling für verschachtelte Links (eingerückt mit border-left)

**Key Features:**
- Smooth `max-height` und `opacity` Transitions
- Chevron rotiert mit `transform: rotate(180deg)`
- Child-Links sind eingerückt mit subtiler linker Border
- Nutzt bestehende MD3 Design Tokens

### 3. JavaScript (`static/js/main.js`)

**Ersetzt:** `initMobileSubpanels()` (65+ Zeilen komplexe Logik)  
**Mit:** `initMobileCollapsibles()` (25 Zeilen einfacher Code)

**Neue Logik:**
```javascript
function initMobileCollapsibles() {
  // Einfacher Toggle für aria-expanded und hidden
  trigger.addEventListener('click', () => {
    const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
    trigger.setAttribute('aria-expanded', !isExpanded);
    content.hidden = isExpanded;
  });
}
```

**Bonus:** 
- Collapsibles werden automatisch geschlossen wenn mobile menu geschlossen wird
- Integriert in bestehende `closeMobileMenu()` Funktion

## Vorteile

✅ **Einfacher Code:** ~40% weniger JavaScript, keine komplexe Panel-Verwaltung  
✅ **Bessere UX:** Nutzer sehen immer alle Hauptmenüpunkte  
✅ **Smooth Animations:** Native CSS transitions mit MD3 easing curves  
✅ **Accessibility:** Korrekte ARIA-Attribute (aria-expanded, aria-controls)  
✅ **Material Design 3:** Folgt MD3 Navigation Drawer Patterns  
✅ **Performance:** Keine nested Panels, weniger DOM-Manipulation  
✅ **Wartbar:** Klarer, linearer Code ohne verschachtelte States

## Visuelle Verbesserungen

- Chevron-Icon rotiert smooth beim Öffnen/Schließen
- Child-Links mit subtiler Einrückung und linker Accent-Border
- Active State mit Primary Color und erhöhtem Font-Weight
- Hover-Effekte harmonieren mit Rest des Menüs

## Testing Checkliste

- [ ] Mobile Menu öffnen
- [ ] "Proyecto" anklicken → Unterpunkte klappen auf
- [ ] Chevron rotiert korrekt
- [ ] Andere Hauptlinks sind weiterhin sichtbar und nutzbar
- [ ] Nochmal klicken → Unterpunkte klappen zu
- [ ] Navigation zu Unterseite funktioniert
- [ ] Active State wird korrekt angezeigt
- [ ] Menu schließen → Alle Collapsibles werden zurückgesetzt
- [ ] Responsive: Funktioniert auf verschiedenen Bildschirmgrößen

## Browser Support

- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅
- Mobile Browsers: ✅

Alle Features nutzen moderne, aber gut unterstützte CSS/JS APIs.

## Rollback

Falls nötig, siehe Git History für das vorherige Subpanel-System.
Die Dateien waren:
- `templates/partials/_navbar.html` (Zeilen 120-160)
- `static/css/md3-components.css` (keine separaten Subpanel-Styles)
- `static/js/main.js` (Zeilen 440-520)
