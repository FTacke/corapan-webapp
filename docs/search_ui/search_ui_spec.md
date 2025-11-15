# CO.RA.PAN – Such-UI-Redesign (Branch: `search_ui`)

Stand: Konzeption für Umbau der Suchoberfläche (Simple + Advanced/CQL) in einem einheitlichen MD3-Design.  
Ziel: Grundlage für die Umsetzung im Branch `search_ui`.

---

## 1. Zielsetzung

- Eine **einheitliche Suchoberfläche** für:
  - „Búsqueda simple“ (einfache Suche, jetzt über BlackLab).
  - „Modo avanzado (CQL)“ (erweiterte Muster-/CQL-Suche).
- **Backend-technisch** läuft alles über BlackLab, Simple + Advanced erzeugen CQL-Anfragen.
- **UX-Ziele**:
  - Klar verständliches Formular für Nicht-Expert:innen.
  - Erweiterter Modus für komplexe Muster, ohne reine „CQL-Textwüste“.
  - Robust, MD3-konform, ohne externe UI-Stacks (z. B. kein Select2).

---

## 2. Seitenaufbau (High-Level)

1. Seiten-Header (wie bisher, wo vorhanden).
2. **Suchformular** (MD3-Card) mit:
   - A: Basis-Query
   - B: Metadaten-Filter
   - C: Optionen (Checkboxen)
   - D: Toggle „Modo avanzado (CQL)“
   - E: Expertenbereich (eingeklappt, inhaltlich E1–E3)
   - F: Formular-Footer (Buttons)
3. **Aktive Filter-Chip-Zeile** („Filtros activos“).
4. **Sub-Tabs** unter dem Formular:
   - Resultados
   - Estadísticas (Backend-Funktionalität später an BlackLab anbinden)
5. Trefferliste / Statistikpanel (UI-Ablauf später im Branch finalisieren).

---

## 3. Suchformular-Details (A–F)

### A. Basis-Query

- Elemente:
  - Textfeld für Suchbegriff.
  - Dropdown für Suchtyp:
    - „Forma“
    - „Forma exacta“
    - „Lema“
- Verhalten:
  - Änderungen an Suchfeld/Dropdown beeinflussen die generierte CQL-Query (sichtbar in E2, wenn „Modo avanzado“ aktiv ist).
  - Standardmodus bleibt „Simple Search“ (ohne Sicht auf CQL).

---

### B. Metadaten-Filter (Facettenleiste)

- Facetten:
  - País
  - Hablante
  - Sexo
  - Modo
  - Discurso
- Layout:
  - **Desktop**: in einer Zeile (ggf. responsives Wrapping).
  - **Mobile**: gestapelt oder in 1–2 Zeilen, Layout bleibt MD3-konform.
- UI-Prinzip:
  - **Exposed Filter Fields** (MD3):
    - Je Facette ein Feld mit Label („País“ etc.).
    - Feld öffnet ein MD3-konformes Menü mit Mehrfachauswahl.
  - Menüs:
    - Liste mit Checkbox-Optionen (native Inputs).
    - Auswahl ändert den internen Facetten-Status.
- Anzeige im Feld:
  - Keine Pseudo-Zähler wie „2 seleccionados“.
  - Immer **konkrete Werte** anzeigen:
    - keine Auswahl: Placeholder („Todos los países“ o. ä.).
    - eine Auswahl: `España`
    - mehrere: `España, México, Colombia` (Feld kann mehrzeilig werden).
- Backend-Repräsentation (Variante A):
  - Pro Facette ein `<select name="FACET" multiple hidden>`:
    ```html
    <select name="pais" multiple hidden>
      <option value="es">España</option>
      <option value="mx">México</option>
      ...
    </select>
    ```
  - JS sorgt dafür, dass `selected`-Attribute zu `selectedFacets` passen.
  - Flask/Backend erhält alle Werte per `getlist("pais")` usw.

---

### C. Optionen (Checkboxen)

- Checkbox 1: „Incluir emisoras regionales“
  - Standard: **deaktiviert**.
- Checkbox 2: „Ignorar acentos/mayúsculas“
  - Standard: **deaktiviert**.
- Beide Checkboxen sitzen in einem Abschnitt „Opciones“ (z. B. unterhalb von A + B oder am rechten Rand in Desktop-Layout).
- Änderungen müssen in der CQL-Generierung berücksichtigt werden (Accent-/Case-Handling, Filter auf Sender).

---

### D. Toggle für Advanced

- Schalter-Label: **„Modo avanzado (CQL)“**
- Verhalten:
  - Standard: **aus** → Expertenbereich E wird nicht angezeigt.
  - Wenn aktiv:
    - Bereich E (E1–E3) wird unterhalb des Hauptformulars angezeigt.
- Wichtig:
  - **E ist immer eingeklappt**, wenn Toggle aus ist – unabhängig von Screen-Größe (auch auf Desktop standardmäßig nicht sichtbar).

---

### E. Expertenbereich (nur bei „Modo avanzado (CQL)“)

Struktur von E:

1. E1: Visueller Pattern-Builder (Token-Zeilen + Distanz-Regel).
2. E2: CQL-Ansicht („Consulta CQL“).
3. E3: Plantillas rápidas (befüllen den Builder).

#### E1. Pattern-Builder („Patrones de palabras (CQL)“)

- Ziel:
  - Mehrwortmuster definieren (z. B. „Adjektiv + Substantiv“), ohne direkt CQL schreiben zu müssen.
- Oberer Abschnitt:
  - Titel, z. B. **„Patrones de palabras (CQL)“**
  - Kurzbeschreibung (in einfachem Spanisch, sinngemäß):
    - „Construye patrones como ‘verbo + sustantivo’ paso a paso sin escribir CQL a mano.“
- Token-Zeilen:
  - Jede Zeile repräsentiert einen Token-Baustein (T1, T2, T3 …).
  - Pro Zeile:
    - Feld-Auswahl:
      - `Forma`
      - `Lema`
      - `Categoría gramatical (POS)`
      - ggf. `Otro atributo` (später erweiterbar).
    - Match-Typ:
      - `es exactamente`
      - `contiene`
      - `empieza por`
      - `termina en`
    - Textfeld für den Wert.
    - Button „Eliminar“ (entfernt die Zeile).
  - Buttons:
    - „Añadir palabra siguiente“ (fügt eine neue Zeile unterhalb ein).
- CQL-Generierung:
  - Jede Zeile → ein `[...]`-Block mit passendem Attribut:
    - z. B. `[lemma="comer"]`, `[pos="ADJ"]`, etc.
  - Reihenfolge der Zeilen → Sequenz von Token-Blöcken (T1 T2 T3).

##### Distanz-Regel (global für den Pattern-Builder)

- Block „Distancia entre palabras“ unter den Token-Zeilen:
  - Radiobuttons:
    - `◉ Justo seguidas`
      - CQL: T1 T2 T3 (keine Zwischen-Patterns).
    - `◉ Hasta N palabras entre medias`
      - Bei Auswahl erscheint ein Number-Field:
        - Label: „Número máximo de palabras entre medias“
        - Typ: `number`
        - Default: `1`
        - Min: `0`
        - Max: `10`
      - CQL:
        - Zwischen jedem Token-Paar: `[]{0,N}`
        - Ergebnis für drei Tokens: `T1 []{0,N} T2 []{0,N} T3`
- Eingabe-Validierung:
  - Leeres Feld oder Wert < 0 → auf 0 setzen.
  - Wert > 10 → auf 10 begrenzen.

> Negation ist bewusst **nicht** Bestandteil der ersten Ausbau-Stufe.

---

#### E2. CQL-Ansicht („Consulta CQL“)

- Textbereich (Textarea) mit Label: **„Consulta CQL“**.
- Inhalt:
  - Zeigt die aktuell generierte CQL-Anfrage:
    - aus Basis-Query (A),
    - Metadaten-Filtern (B),
    - Optionen (C),
    - Pattern-Builder (E1),
    - Distanz-Regel.
- Standardzustand:
  - `readonly` (nur Anzeige).
- Checkbox (oder Switch) daneben:
  - Label z. B. „Permitir editar manualmente“.
  - Verhalten:
    - Wenn aktiv:
      - Textarea wird editierbar.
      - Ein kurzer Warnhinweis:
        - „Si editas la consulta CQL a mano, la interfaz de patrones puede dejar de reflejar todos los detalles.“
    - Technisch:
      - Ab dem Moment, wo manuelle Änderungen erkannt werden, gilt die CQL-Textarea als **Quelle der Wahrheit**.
      - Der Pattern-Builder wird ggf. nicht mehr versucht, rückwärts mit der CQL zu synchronisieren.

---

#### E3. Plantillas rápidas

- Ziel:
  - Einstieg in typische Muster ohne überlegen zu müssen, wie der Builder eingestellt werden muss.
- UI:
  - Abschnitt mit Label, z. B. **„Plantillas frecuentes“**.
  - Liste von Buttons (oder Dropdown mit auswählbaren Vorlagen), z. B.:
    - „Verbo + sustantivo“
    - „Adjetivo + sustantivo“
    - „Dos palabras con el mismo lema“
- Verhalten:
  - **Variante 1**: Plantillas befüllen **den Pattern-Builder (E1)** direkt:
    - Token-Zeilen werden passend vorkonfiguriert.
    - Distanz-Regel wird ggf. auf sinnvollen Default gesetzt.
  - CQL-Textarea (E2) wird anschließend mit der daraus generierten CQL aktualisiert.

---

### F. Formular-Footer

- Buttons am Ende des Formulars:
  - Primär:
    - „Buscar“
  - Sekundär:
    - „Restablecer“ (setzt Felder A–C, Facetten, E1–E3, Distanz und CQL-Textarea zurück).
- Position:
  - Innerhalb der MD3-Card, im Footer-Bereich (vollbreit, auch auf Mobile klar sichtbar).

---

## 4. Aktive Filter – Chip-Zeile („Filtros activos“)

- Position:
  - Direkt unter der Filterzeile (B) bzw. unter dem Formularblock (noch vor den Sub-Tabs).
- Inhalt:
  - Ein Chip pro ausgewähltem Filterwert (nicht pro Facette).
  - Beispiel:
    - `[ESP ✕] [MEX ✕] [Sexo: femenino ✕] [Modo: oral ✕] [Discurso: general ✕]`
- Darstellung:

  - **Länderchips**:
    - Text: nur der Wert (z. B. `ESP`, `MEX`).
    - Keine Typ-Präfixe („País:“).
    - Einheitliche **leichte Tönung** (z. B. zartes Blau), MD3-kompatibel.
  - **Andere Facetten**:
    - Text: mit Typ-Präfix, z. B.:
      - `Sexo: femenino`
      - `Modo: oral`
      - `Discurso: general`
    - Eigene **leichte Tönung pro Facette** (unterschiedliche, aber dezente Akzentfarben).
  - Keine Icons/Symbole außer dem Close-Icon (`✕`).
  - Typ: MD3-kompatible Input-/Filter-Chips mit leichter Hintergrundaura, Text + Close-Icon.

- Interaktion:

  - Jeder Chip ist **entfernbar**:
    - Ein Close-Icon `✕` ist sichtbar.
    - UX: Klick auf den gesamten Chip löscht den Filter (nicht nur das `✕`).
  - Beim Entfernen:
    - wird der Wert aus dem entsprechenden Facetten-Array entfernt,
    - das `<select multiple hidden>` wird aktualisiert,
    - die Anzeige im dazugehörigen Filterfeld wird aktualisiert,
    - der Chip wird aus „Filtros activos“ entfernt.
- Sichtbarkeit:
  - Wenn **kein Filter aktiv**:
    - Chip-Zeile ausblenden oder neutralen Hinweis anzeigen („Sin filtros activos“).

---

## 5. Sub-Tabs: Resultados | Estadísticas

- Die Sub-Tabs der einfachen Corpus-Suche werden übernommen.

Beispiel-Struktur:

```html
<div id="simple-sub-tabs" role="tablist" class="md3-stats-tabs" style="margin-top: 1.5rem; display: {% if active_tab == 'tab-simple' or not active_tab %}flex{% else %}none{% endif %};">
  <button type="button" role="tab" id="tab-resultados" class="md3-stats-tab md3-stats-tab--active" data-view="results" aria-controls="panel-resultados" aria-selected="true">
    <span class="material-symbols-rounded" aria-hidden="true">table</span>
    <span>Resultados</span>
  </button>
  <button type="button" role="tab" id="tab-estadisticas" class="md3-stats-tab" data-view="stats" aria-controls="panel-estadisticas" aria-selected="false">
    <span class="material-symbols-rounded" aria-hidden="true">bar_chart</span>
    <span>Estadísticas</span>
  </button>
</div>
````

* UI-Plan:

  * Tabs übernehmen (Icons, Texte, MD3-Klassen).
  * Zunächst Fokus auf Design und Struktur.
  * Die **Estadísticas-Funktion** (BlackLab-basierte Statistiken) wird in einem späteren Schritt implementiert:

    * eigener Endpunkt / Parameter für Statistiken.
    * Aggregationen / Gruppenbildung über BlackLab.
    * Anzeige im Panel `panel-estadisticas`.

---

## 6. Technische Rahmenbedingungen / Implementations-Hinweise

### 6.1. Branch

* Neuer Branch: `search_ui`
* In diesem Branch:

  * Umbau des Templates der Suchseite (Advanced + ggf. Simple Search).
  * Umbau der Metadaten-Filter-UI.
  * Implementierung des Expertenbereichs E (Pattern-Builder, Distanz-Regel, CQL-Preview, Plantillas).
  * Sub-Tabs-Integration.

### 6.2. Relevante Dateien (Stand Konzept)

Konkrete Dateipfade im Projekt prüfen, voraussichtliche Kandidaten:

* Template:

  * `templates/search/advanced.html` (oder neues Template, das zur Suchseite gehört)
* JS:

  * `static/js/modules/advanced/formHandler.js` (CQL-Build, HTMX-Handling)
  * ggf. neue dedizierte Module:

    * `static/js/modules/search/filters.js`
    * `static/js/modules/search/patternBuilder.js`
      (Namensgebung nach Projektkonventionen klären)

### 6.3. JS-Architektur

* Kein externer UI-Stack (kein Select2 o. ä.).
* Reine DOM- und State-Logik:

  * State-Objekte für Facetten (z. B. `selectedPais`, `selectedSexo` …).
  * State für Pattern-Builder (Token-Liste; Distanz-Regel).
  * Synchronisation mit:

    * Hidden `<select multiple>` für Facetten.
    * CQL-Textarea (E2).
* HTMX:

  * Advanced-Request läuft wie bisher über HTMX.
  * Optionale Event-Handler:

    * Loading-/Error-Indikatoren im Formular und bei Ergebnissen (kann in diesem Branch mit umgesetzt werden oder separat).

---

## 7. Offene Punkte für die Umsetzung

* Konkrete CQL-Mapping-Regeln:

  * Abbildung von „Forma / Lema / POS“ auf BlackLab-Felder.
  * Umgang mit „Ignorar acentos/mayúsculas“ im CQL.
  * Einbindung der Metadatenfilter (País, etc.) in die CQL-Query (und/oder separate Filter-Parameter).
* Detailtexte (spanische Hilfetexte) finalisieren.
* Exaktes Farb-Set für die leichten Tönungen (MD3-konforme Farbpalette definieren).
* Statistikpanel:

  * Welche Statistiken?
  * Welche BlackLab-Abfragen?
  * Welche Visualisierung (Tabellen, Charts)?

---

Dieses Dokument ist die Basis-Spezifikation für den Umbau im Branch `search_ui`.
Umsetzungsschritte: zuerst Struktur + UI (Formular, Filter, E-Bereich, Chips, Tabs), danach CQL-Logik und Statistik-Anbindung.
Dokumentation immer systematisch anlegen unter docs/search_ui
