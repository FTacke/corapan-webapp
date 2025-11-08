# Corpus DataTables Migration - Dokumentation

## Übersicht

Die neue Corpus-Suchseite basiert auf **DataTables** - einer bewährten, robusten JavaScript-Library für tabellarische Daten. Diese Implementierung ersetzt die alte Custom-Lösung mit deutlich weniger Code und höherer Stabilität.

## Neue Features

### ✅ Was funktioniert jetzt besser:

1. **Stabile Filter**
   - Multi-Select Dropdowns mit Select2
   - Filter-States werden korrekt persistiert
   - Keine inkonsistenten Checkbox-Zustände mehr

2. **Native Export-Funktionen**
   - CSV Export (integriert)
   - Excel Export (integriert)
   - PDF Export (integriert)
   - Copy to Clipboard (integriert)
   - ~300 Zeilen Custom-Export-Code entfallen

3. **Performance**
   - Client-seitiges Paging mit DataTables
   - Sortierung pro Spalte
   - Schnellere Suche in der Tabelle

4. **Benutzerfreundlichkeit**
   - Moderne UI mit Select2 Dropdowns
   - Alle Filter sofort sichtbar
   - Intuitive Bedienung

## Technischer Stack

### Dependencies

```html
<!-- DataTables Core -->
- jquery-3.7.1.min.js
- jquery.dataTables.min.js (v1.13.7)

<!-- DataTables Extensions -->
- dataTables.buttons.min.js (v2.4.2)
- buttons.html5.min.js
- jszip.min.js (für Excel Export)

<!-- Select2 für Multi-Select -->
- select2.min.js (v4.1.0)
- select2.min.css
```

### Dateien

1. **templates/pages/corpus_new.html**
   - Neues Template mit DataTables-Struktur
   - Integriertes CSS
   - Select2 Multi-Select Dropdowns

2. **static/js/corpus_datatables.js**
   - Neue JavaScript-Implementierung (~500 Zeilen statt ~1000+)
   - DataTables Konfiguration
   - Audio-Funktionen (von alter Version übernommen)
   - Filter-Management
   - Export-Handling

3. **src/app/routes/corpus.py**
   - Neue Routen:
     - `/corpus/new` - Neue Corpus-Seite
     - `/corpus/search_new` - Suchendpoint für neue Seite

## Zugriff

### URLs

- **Neue Seite**: http://localhost:5000/corpus/new
- **Alte Seite**: http://localhost:5000/corpus (bleibt vorerst verfügbar)

## Code-Vergleich

### Alte Implementierung
```
corpus.html:           ~800 Zeilen
corpus_script.js:      ~800 Zeilen
corpus_filter.js:      ~200 Zeilen
GESAMT:              ~1800 Zeilen
```

### Neue Implementierung
```
corpus_new.html:       ~600 Zeilen (mit inline CSS)
corpus_datatables.js:  ~500 Zeilen
GESAMT:              ~1100 Zeilen (-39% Code!)
```

## Wichtige Änderungen

### Filter-System

**ALT (Custom Checkboxes):**
```html
<div class="dropdown-select">
  <div class="select-box">País</div>
  <div class="select-menu">
    <label><input type="checkbox" value="all">Todos</label>
    <label><input type="checkbox" value="ARG">ARG</label>
    <!-- ... -->
  </div>
</div>
```

**NEU (Select2 Multi-Select):**
```html
<select id="filter-country" name="country_code" multiple="multiple">
  <option value="ARG">Argentina</option>
  <option value="BOL">Bolivia</option>
  <!-- ... -->
</select>
```

### Export-Funktionen

**ALT (Custom Code ~300 Zeilen):**
```javascript
function downloadResultsTxtFile() {
  // Komplexe custom Implementierung
  // ~100 Zeilen Code
}
function downloadResultsCsvFile() {
  // Komplexe custom Implementierung
  // ~100 Zeilen Code
}
function downloadResultsXlsxFile() {
  // Komplexe custom Implementierung mit XLSX library
  // ~100 Zeilen Code
}
```

**NEU (DataTables Buttons ~20 Zeilen):**
```javascript
buttons: [
  {
    extend: 'csvHtml5',
    text: '<i class="bi bi-filetype-csv"></i> CSV',
    filename: 'corapan_resultados'
  },
  {
    extend: 'excelHtml5',
    text: '<i class="bi bi-filetype-xlsx"></i> Excel'
  }
  // Fertig!
]
```

## Migration Steps (für Produktiv)

### Phase 1: Testing (JETZT)
1. ✅ Neue Seite unter `/corpus/new` verfügbar
2. ✅ Alte Seite läuft parallel unter `/corpus`
3. Test mit realen Daten
4. User-Feedback sammeln

### Phase 2: Rollout (SPÄTER)
1. Wenn alles getestet:
   ```python
   # In corpus.py Route anpassen:
   @blueprint.get("/")
   def corpus_home():
       return render_template("pages/corpus_new.html", ...)
   ```

2. Alte Dateien archivieren:
   - `templates/pages/corpus.html` → `templates/legacy/corpus.html.bak`
   - `static/js/corpus_script.js` → `static/js/legacy/corpus_script.js.bak`
   - `static/js/corpus_filter.js` → `static/js/legacy/corpus_filter.js.bak`

## Beibehaltene Funktionen

Alle bestehenden Funktionen wurden übernommen:

✅ Audio-Wiedergabe (Play-Buttons)  
✅ Audio-Download  
✅ Spectrogram-Anzeige  
✅ Player-Integration  
✅ Kontext-Audio  
✅ Palabra-Audio  
✅ Token-ID Links  
✅ Authentifizierungs-Check für Media

## Vorteile der DataTables-Lösung

### 1. **Bewährt & Stabil**
- DataTables existiert seit 2008
- Millionen von Installationen weltweit
- Umfangreiche Dokumentation

### 2. **Wartbarkeit**
- Weniger Custom-Code
- Standard-Patterns
- Einfachere Fehlersuche

### 3. **Features out-of-the-box**
- Pagination
- Sorting
- Filtering
- Export
- Responsive
- i18n (Spanische Übersetzung integriert)

### 4. **Performance**
- Optimierte Rendering-Engine
- Effizientes DOM-Handling
- Lazy Loading bei großen Datasets

### 5. **Erweiterbarkeit**
- 100+ Plugins verfügbar
- Custom Extensions möglich
- Große Community

## Testing Checklist

- [ ] Suche mit verschiedenen Queries testen
- [ ] Alle Filter-Kombinationen testen (País, Hablante, Sexo, etc.)
- [ ] Export-Funktionen testen (CSV, Excel, PDF)
- [ ] Audio-Wiedergabe testen
- [ ] Audio-Download testen
- [ ] Spectrogram-Overlay testen
- [ ] Player-Link testen
- [ ] Mobile/Responsive testen
- [ ] Verschiedene Browser testen (Chrome, Firefox, Safari)
- [ ] Performance mit großen Resultsets testen

## Support & Dokumentation

### DataTables Docs
- Offizielle Dokumentation: https://datatables.net/
- Examples: https://datatables.net/examples/
- API Reference: https://datatables.net/reference/

### Select2 Docs
- Offizielle Dokumentation: https://select2.org/
- Examples: https://select2.org/examples

## Troubleshooting

### Problem: Filter behalten nicht die Werte
**Lösung**: Select2 Initialisierung prüfen in `corpus_datatables.js`

### Problem: Export-Buttons fehlen
**Lösung**: JSZip library wird benötigt für Excel-Export

### Problem: Spanische Übersetzung fehlt
**Lösung**: DataTables i18n JSON wird von CDN geladen

### Problem: Audio funktioniert nicht
**Lösung**: Authentifizierung und MEDIA_ENDPOINT prüfen

## Nächste Schritte

1. **Testing**: Ausführlich testen mit verschiedenen Szenarien
2. **Feedback**: User-Feedback sammeln
3. **Optimierung**: Basierend auf Feedback anpassen
4. **Migration**: Nach erfolgreicher Testphase die neue Version als Standard setzen

---

**Erstellt**: 2025-01-05  
**Version**: 1.0  
**Status**: Ready for Testing
