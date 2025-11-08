# CSP Bootstrap Icons Fix - Dokumentation

**Datum:** 19. Oktober 2025  
**Status:** ✅ Behoben

---

## 🐛 Problem

Bootstrap Icons wurden nicht angezeigt, weil die Content Security Policy (CSP) den Font-Zugriff auf `cdn.jsdelivr.net` blockierte.

### Fehlermeldung im Browser:
```
Content-Security-Policy: Die Einstellungen der Seite haben das Laden einer Ressource (font-src) 
auf https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/fonts/bootstrap-icons.woff 
blockiert, da sie gegen folgende Direktive verstößt: "font-src 'self' https://cdnjs.cloudflare.com"
```

### Betroffene Komponenten:
- ❌ Error Pages (Icons: compass, lock, shield-x, etc.)
- ❌ Admin Dashboard (Icons: headphones, wave-square, globe-americas, search)
- ❌ Alle Seiten mit Bootstrap Icons (`class="bi bi-*"`)

---

## ✅ Lösung

### Geänderte Datei: `src/app/__init__.py`

**Vorher:**
```python
"font-src 'self' https://cdnjs.cloudflare.com; "
```

**Nachher:**
```python
"font-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
```

### Vollständige CSP-Direktive:
```python
csp = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://code.jquery.com https://cdn.jsdelivr.net "
    "https://cdn.datatables.net https://cdnjs.cloudflare.com https://unpkg.com; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.datatables.net "
    "https://cdnjs.cloudflare.com https://unpkg.com; "
    "img-src 'self' data: https: blob:; "
    "font-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "media-src 'self' blob:; "
    "frame-ancestors 'none';"
)
```

---

## 🔍 Warum war das notwendig?

### Bootstrap Icons werden von `cdn.jsdelivr.net` geladen:
```html
<!-- In base.html -->
<link rel="stylesheet" 
      href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.min.css">
```

### Das CSS lädt dann die Font-Dateien:
```css
@font-face {
  font-family: "bootstrap-icons";
  src: url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/fonts/bootstrap-icons.woff")
}
```

### CSP prüft BEIDE Quellen:
1. ✅ `style-src` für das CSS → War erlaubt
2. ❌ `font-src` für die Font-Datei → War NICHT erlaubt

---

## 🧪 Test

### Vorher (Icons nicht sichtbar):
```html
<i class="bi bi-compass"></i>  <!-- ❌ Keine Anzeige -->
```

### Nachher (Icons sichtbar):
```html
<i class="bi bi-compass"></i>  <!-- ✅ Compass-Icon wird angezeigt -->
```

### CSP-Header überprüfen:
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing
$response.Headers.'Content-Security-Policy' -match "font-src ([^;]+)"
# Output: 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net
```

---

## 📊 Erlaubte CDN-Quellen (Übersicht)

### Font-Quellen (`font-src`):
- ✅ `'self'` - Lokale Fonts aus `/static/fonts/`
- ✅ `https://cdnjs.cloudflare.com` - Font Awesome
- ✅ `https://cdn.jsdelivr.net` - Bootstrap Icons (NEU)

### Script-Quellen (`script-src`):
- ✅ `'self'` - Lokale JavaScript-Dateien
- ✅ `'unsafe-inline'` - Inline-Scripts (TODO: entfernen nach jQuery-Migration)
- ✅ `https://code.jquery.com` - jQuery
- ✅ `https://cdn.jsdelivr.net` - jQuery-Plugins
- ✅ `https://cdn.datatables.net` - DataTables
- ✅ `https://cdnjs.cloudflare.com` - Diverse Libraries
- ✅ `https://unpkg.com` - Leaflet (Karten-Bibliothek)

### Style-Quellen (`style-src`):
- ✅ `'self'` - Lokale CSS-Dateien
- ✅ `'unsafe-inline'` - Inline-Styles (TODO: entfernen nach jQuery-migration)
- ✅ `https://cdn.jsdelivr.net` - Bootstrap Icons CSS
- ✅ `https://cdn.datatables.net` - DataTables CSS
- ✅ `https://cdnjs.cloudflare.com` - Font Awesome CSS
- ✅ `https://unpkg.com` - Leaflet CSS

---

## 🔒 Sicherheits-Bewertung

### Ist `cdn.jsdelivr.net` sicher?

**✅ JA**, aus folgenden Gründen:

1. **Integrity-Checks:** jsdelivr bietet SRI (Subresource Integrity)
2. **CDN-Reputation:** Von GitHub/npm gesponsert, sehr vertrauenswürdig
3. **HTTPS:** Alle Ressourcen über verschlüsselte Verbindung
4. **Versionierung:** Wir nutzen feste Version `@1.11.2`, kein Auto-Update

### Best Practice für Production:

**Option A: CDN mit SRI (Empfohlen für schnelles Laden)**
```html
<link rel="stylesheet" 
      href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.min.css"
      integrity="sha512-..." 
      crossorigin="anonymous">
```

**Option B: Self-Hosted (Maximale Kontrolle)**
1. Bootstrap Icons lokal nach `/static/fonts/` kopieren
2. CSP auf `font-src 'self'` beschränken
3. Kein CDN-Dependency

**Für CO.RA.PAN:** Option A ist akzeptabel (schneller, weniger Wartung).

---

## 📝 Weitere CSP-Anpassungen (Roadmap)

### Phase 3 MITTELFRISTIG: CSP Hardening

1. **`'unsafe-inline'` entfernen**
   - Nach jQuery-Migration möglich
   - Nonce-basierte Inline-Scripts verwenden

2. **`'unsafe-eval'` vermeiden**
   - Aktuell nicht verwendet (gut!)
   - Nach Migration beibehalten

3. **SRI Hashes hinzufügen**
   ```html
   <link rel="stylesheet" 
         href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.min.css"
         integrity="sha384-abcd1234..." 
         crossorigin="anonymous">
   ```

4. **CSP Report-URI einrichten**
   ```python
   "report-uri /csp-report; "
   ```
   Für Monitoring von CSP-Verstößen

---

## 🎯 Zusammenfassung

| Aspekt | Status |
|--------|--------|
| **Problem** | Bootstrap Icons blockiert |
| **Ursache** | `font-src` erlaubte nur `cdnjs.cloudflare.com` |
| **Lösung** | `cdn.jsdelivr.net` zu `font-src` hinzugefügt |
| **Sicherheit** | ✅ Keine Bedenken (vertrauenswürdiger CDN) |
| **Performance** | ✅ Keine Auswirkung (Fonts gecacht) |
| **Testing** | ✅ Icons werden jetzt angezeigt |

---

**Fazit:** Problem behoben, Icons funktionieren jetzt auf allen Seiten! 🎉
