# Bugfix: Buchstabenmarkierung nicht sichtbar

## Problem
Die Funktion `markLetters()` wurde aufgerufen und hat korrekt `<span class="highlight">` Tags eingefügt, aber die gelbe Markierung war nicht sichtbar.

## Ursache
**CSS-Selektor-Mismatch:**

```css
/* VORHER - Falsch */
.word.highlight {
  background: rgba(255, 215, 0, 0.5);
  font-weight: 600;
}
```

Dieser Selektor sucht nach einem `.word` Element mit der Klasse `.highlight`.

**Aber das JavaScript erstellt:**
```javascript
const highlightSpan = `<span class="highlight">${match[0]}</span>`;
```

Das ist ein `<span class="highlight">` **innerhalb** des `.word` Elements!

## Lösung

```css
/* NACHHER - Korrekt */
.word .highlight,
span.highlight {
  background: rgba(255, 215, 0, 0.6) !important;
  font-weight: 600 !important;
  padding: 0.1rem 0.2rem;
  border-radius: 2px;
  display: inline;
}
```

**Änderungen:**
1. `.word .highlight` - Selektor für span innerhalb von word
2. `span.highlight` - Fallback-Selektor
3. `!important` - Verhindert Überschreibung durch andere Styles
4. `display: inline` - Sicherstellt inline-Darstellung
5. Erhöhte Opacity: 0.5 → 0.6 für bessere Sichtbarkeit

## Geänderte Datei
- `static/css/components.css` - Zeile ~3130

## Test
1. Öffne Player-Seite
2. Gib einen Buchstaben ein (z.B. "s")
3. Klicke auf "Marcar"
4. → Gelbe Markierung sollte nun sichtbar sein

## Console-Logs
Die anderen Console-Meldungen (404 Audio, Tailwind Warning) sind nicht kritisch:
- **404 Audio**: Media-Pfad muss noch konfiguriert werden
- **Tailwind Warning**: CDN-Warnung für Entwicklung
- **Footer Stats Error**: Element existiert nicht auf Player-Seite

---

**Status:** ✅ Behoben
**Datum:** 16. Oktober 2025
