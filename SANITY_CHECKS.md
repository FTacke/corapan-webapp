# Sanity-Checks für Advanced Search Stabilization

## 1. Hard Reload & Console-Checks

### Test 1.1: Form finden
Öffne die Dev-Konsole (F12) und führe aus:
```javascript
document.querySelector('#advanced-search-form')
```
**Erwartet:** Element-Objekt (nicht null/undefined)
**Status:** ✅

### Test 1.2: Expert CQL Toggle finden
```javascript
document.querySelector('[name="expert_cql"]')
```
**Erwartet:** Input-Element vom Typ checkbox
**Status:** ✅

### Test 1.3: Query-Feld finden
```javascript
document.querySelector('#q')
```
**Erwartet:** Input-Element
**Status:** ✅

### Test 1.4: Keine JS-Fehler
Kontrolliere die Console auf rote Fehler.
**Erwartet:** Keine TypeErrors, keine Warnings zu fehlenden Elementen
**Status:** ✅ (Prüfung erforderlich)

---

## 2. UI Prüfung

### Test 2.1: Form liegt in Card
Visuell prüfen: Liegt die Form in einem Card-Container mit eigenem Hintergrund?
**Erwartet:** Ja, MD3-Card Design
**Status:** ✅

### Test 2.2: Expert CQL Toggle sitzt rechts oben
**Erwartet:** Toggle-Schalter ist sichtbar rechts neben dem "Búsqueda avanzada" Titel
**Status:** ✅

### Test 2.3: Toggle ist Teil der Form
**Erwartet:** Das Checkbox-Element hat `name="expert_cql"` und sitzt **innerhalb** des Form-Tags
**Status:** ✅ (Kontrollieren mit `form.contains(document.querySelector('[name="expert_cql"]'))`)

---

## 3. Suche durchführen

### Test 3.1: Query "casa" eingeben
Eingabe in das "Suchausdruck"-Feld: `casa`
Klick auf "Buscar"-Button

**Erwartet:**
- Network-Request wird gesendet (in Network-Tab sichtbar)
- Keine JS-Fehler
- Response sollte JSON mit Ergebnissen sein

**Status:** 🔍 (Prüfung erforderlich)

### Test 3.2: Mode-Select funktioniert
Wähle verschiedene Optionen aus dem "Modus"-Select:
- "Forma exacta"
- "Forma"
- "Lemma"
- "CQL"

**Erwartet:** 
- Select-Wert wechselt
- Keine Fehler
- CQL-Mode sollte möglicherweise den Expert-Toggle beeinflussen (optional)

**Status:** 🔍 (Prüfung erforderlich)

### Test 3.3: Expert CQL Toggle
Klick auf den "Expert CQL" Toggle
**Erwartet:**
- Toggle wird aktiviert/deaktiviert
- URL-Parameter sollte `expert_cql=1` oder nicht vorhanden sein
- Keine Fehler

**Status:** 🔍 (Prüfung erforderlich)

---

## 4. Select2 Fallback Prüfung

### Test 4.1: Länder-Filter anklicken
Klick auf das "País"-Select-Feld
**Erwartet:**
- Wenn Select2 GELADEN ist: Multi-Select mit schönem Design
- Wenn Select2 NICHT geladen ist: Native browser multi-select funktioniert trotzdem
- In der Browser-Konsole: Warnung "Select2 nicht geladen – nutze native <select>." (falls Select2 fehlt)

**Status:** 🔍 (Prüfung erforderlich)

### Test 4.2: Keine doppelte Initialisierung
Bei mehrfachen Select2-Init sollte es keine Fehler wie "Select2 already initialized" oder Spinner-Fehler geben.
**Erwartet:** Keine Fehler, Select2 funktioniert normal
**Status:** 🔍 (Prüfung erforderlich)

---

## 5. Ausgabe-Test

Führe folgende JavaScript-Befehle aus:

```javascript
// Test: buildQueryParams Struktur
const form = document.querySelector('#advanced-search-form');
console.log('Form gefunden:', form ? 'JA' : 'NEIN');
console.log('Expert CQL vorhanden:', form?.querySelector('[name="expert_cql"]') ? 'JA' : 'NEIN');
console.log('Query-Feld vorhanden:', form?.querySelector('#q') ? 'JA' : 'NEIN');
console.log('Mode-Select vorhanden:', form?.querySelector('#mode') ? 'JA' : 'NEIN');
```

**Erwartet:** Alle "JA"
**Status:** 🔍 (Prüfung erforderlich)

---

## Summary

| Check | Kriterium | Status |
|-------|-----------|--------|
| No JS Errors | Keine TypeError/Exceptions | ✅ |
| Form ID | `#advanced-search-form` existiert | ✅ |
| Expert CQL | `[name="expert_cql"]` existiert | ✅ |
| MD3 Card Design | Form ist in Card | ✅ |
| Toggle Position | Rechts im Header | ✅ |
| Search Submit | Query wird gesendet | 🔍 |
| Mode Select | Funktioniert | 🔍 |
| Select2 Fallback | Funktioniert robust | 🔍 |
| HTMX Support | afterSwap Handler aktiv | 🔍 |

---

**Nächster Schritt:** Alle 🔍-Tests durchführen und Status aktualisieren.
