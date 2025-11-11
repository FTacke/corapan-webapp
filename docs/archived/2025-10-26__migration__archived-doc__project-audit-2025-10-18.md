# Projekt-Audit: Aktive vs. Legacy-Dateien

**Datum:** 18. Oktober 2025  
**Zweck:** Überprüfung aller Root-Level-Files, static/-Dateien und LOKAL/database-Scripts

---

## 1. 🔍 ROOT-LEVEL FILES AUDIT

### Konfigurationsdateien

| Datei | Status | Benötigt | Aktuell | Bemerkung |
|-------|--------|----------|---------|-----------|
| `.dockerignore` | ✅ AKTIV | Ja | Ja | Docker-Build Konfiguration |
| `.gitattributes` | ✅ AKTIV | Ja | Ja | Git Line-Ending Konfiguration |
| `.gitignore` | ✅ AKTIV | Ja | ✅ Gerade aktualisiert | Exclusions aktuell |
| `.gitlab-ci.yml` | ✅ AKTIV | Ja | ❓ Zu prüfen | GitLab CI/CD Pipeline |
| `Dockerfile` | ✅ AKTIV | Ja | Ja | Container-Build |
| `package.json` | ✅ AKTIV | Ja | Ja | Node Dependencies |
| `package-lock.json` | ✅ AKTIV | Ja | Ja | Locked Dependencies |
| `passwords.env` | ⚠️ LOCAL | Nein* | - | Sollte in .gitignore sein ✓ |
| `pyproject.toml` | ✅ AKTIV | Ja | Ja | Python Project Metadata |
| `requirements.txt` | ✅ AKTIV | Ja | Ja | Python Dependencies |
| `tailwind.config.js` | ✅ AKTIV | Ja | Ja | Tailwind CSS Konfiguration |
| `vite.config.js` | ✅ AKTIV | Ja | Ja | Vite Build Konfiguration |
| **`README.md`** | ✅ AKTIV | Ja | ✅ Aktuell | **Haupt-README, gut geschrieben** |

**Ergebnis:** Alle Root-Files sind aktiv und benötigt. ✅

### README.md - Status

**ROOT `README.md`:**
- ✅ Aktuell und gut strukturiert
- ✅ Beschreibt Flask + Vite Setup
- ✅ Verweist auf `docs/` für Details
- ✅ Enthält Getting Started, Features, Struktur

**`docs/README.md`:**
- ❌ **EXISTIERT NICHT!**

**Empfehlung:** Keine separate `docs/README.md` nötig - die Root-README verweist bereits gut auf die Dokumentation.

---

## 2. 🎨 STATIC/ FILES AUDIT

### CSS-Dateien (`static/css/`)

| Datei | Status | Verwendet in | Aktuell | Bemerkung |
|-------|--------|--------------|---------|-----------|
| `components.css` | ✅ AKTIV | `base.html` | Ja | Haupt-Komponenten-CSS |
| `corapan_styles.css` | ⚠️ LEGACY? | ❌ NICHT GEFUNDEN | ? | **NICHT verwendet in Templates!** |
| `layout.css` | ✅ AKTIV | `base.html` | Ja | Layout-System |
| `md3-components.css` | ✅ AKTIV | `base.html` | Ja | Material Design 3 Komponenten |
| `md3-tokens.css` | ✅ AKTIV | `base.html` | Ja | MD3 Design Tokens |
| `nav_new.css` | ✅ AKTIV | `base.html` | Ja | Neue Navigation |
| `player-mobile.css` | ✅ AKTIV | `player.html` | Ja | Mobile Player Styles |
| `tokens.css` | ✅ AKTIV | `base.html` | Ja | Design Tokens |

**KRITISCH:** `corapan_styles.css` wird **NICHT in Templates verwendet** - scheint Legacy zu sein!

### JavaScript-Dateien (`static/js/`)

| Datei | Status | Verwendet in | Aktuell | Bemerkung |
|-------|--------|--------------|---------|-----------|
| `atlas_script.js` | ✅ AKTIV | `atlas.html` | Ja | Atlas-Karte |
| `corpus_datatables.js` | ⚠️ LEGACY | `corpus_new.html` | ? | **corpus_new.html ist Legacy!** |
| `corpus_datatables_serverside.js` | ✅ AKTIV | `corpus.html` | Ja | Server-Side DataTables (aktiv) |
| `corpus_filter.js` | ❓ UNKNOWN | ❌ NICHT GEFUNDEN | ? | **Nicht verwendet?** |
| `corpus_script.js` | ❓ UNKNOWN | ❌ NICHT GEFUNDEN | ? | **Nicht verwendet?** |
| `corpus_snapshot.js` | ✅ AKTIV | `corpus.html` | Ja | Token-Snapshot Export |
| `corpus_token.js` | ✅ AKTIV | `corpus.html` | Ja | Token-Formular |
| `main.js` | ✅ AKTIV | `base.html` | Ja | Haupt-JS |
| `morph_formatter.js` | ✅ AKTIV | `corpus.html` | Ja | Morphologie-Formatter |
| `nav_proyecto.js` | ✅ AKTIV | `base.html` | Ja | Projekt-Navigation |
| `player_script.js` | ✅ AKTIV | `player.html` | Ja | Audio Player |
| `modules/` | ✅ AKTIV | Verschiedene | Ja | JS-Module |
| `player/` | ✅ AKTIV | `player_script.js` | Ja | Player-Module |

**LEGACY-KANDIDATEN:**
- ❌ `corpus_datatables.js` - Nur in `corpus_new.html` verwendet (Legacy-Template)
- ❌ `corpus_filter.js` - Nicht gefunden in Templates
- ❌ `corpus_script.js` - Nicht gefunden in Templates

---

## 3. 📄 TEMPLATES AUDIT

### Corpus-Templates

| Template | Route | Status | Bemerkung |
|----------|-------|--------|-----------|
| `corpus.html` | `/corpus` | ✅ AKTIV | **HAUPTTEMPLATE** - Server-Side DataTables |
| `corpus_new.html` | ❌ KEINE ROUTE | 🔴 LEGACY | **Kann gelöscht werden!** |

**BEFUND:** 
- Route verwendet `corpus.html` (Line 70 in `corpus.py`)
- `corpus_new.html` hat **KEINE Route** und ist **LEGACY**

### Weitere Templates

Alle anderen Templates unter `templates/pages/` sind aktiv:
- `admin_dashboard.html`, `atlas.html`, `index.html`, `player.html`
- `proyecto_*.html` (5 Projekt-Seiten)
- `impressum.html`, `privacy.html`

---

## 4. 💾 LOKAL/database/ AUDIT

### Aktive Production-Scripts

| Datei | Zweck | Status | Benötigt |
|-------|-------|--------|----------|
| `database_creation_v2.py` | ✅ DB-Erstellung (optimiert) | AKTIV | **JA - HAUPTSCRIPT** |
| `semantic_database_creation.py` | Semantische Analyse | AKTIV | **JA - wenn Semantik benötigt** |
| `MIGRATION_NOTES.md` | Dokumentation | AKTIV | **JA - Referenz** |
| `OPTIMIZATION_QUICKSTART.md` | Anleitung | AKTIV | **JA - Anleitung** |

### Migration/Test-Scripts (KÖNNEN GELÖSCHT WERDEN)

| Datei | Zweck | Status | Empfehlung |
|-------|-------|--------|------------|
| `corpus_search_performance_patch.py` | Performance-Patch | 🔴 VERALTET | ❌ **LÖSCHEN** - Patch bereits angewendet |
| `database_performance_optimization.py` | Indexes hinzufügen | 🔴 VERALTET | ❌ **LÖSCHEN** - In v2 integriert |
| `test_new_paths.py` | Pfad-Test | 🔴 TEST | ❌ **LÖSCHEN** - Migration abgeschlossen |
| `token_id_delete.py` | Token-ID Cleanup | 🔴 EINMALIG | ❌ **LÖSCHEN** - Einmalige Aktion |

**BEGRÜNDUNG:**
- ✅ DB läuft perfekt mit `database_creation_v2.py`
- ✅ Performance-Optimierungen sind in v2 integriert
- ✅ Migration ist abgeschlossen
- ⚠️ **Scripts sind überflüssig geworden**

### Legacy-Ordner

| Ordner | Inhalt | Status | Empfehlung |
|--------|--------|--------|------------|
| `legacy/` | `database_creation.py` (alte Version) | 🟡 ARCHIV | **BEHALTEN** für 3-6 Monate, dann löschen |
| `backups/` | `20251018_135510/` (DB-Backup) | 🟢 BACKUP | **BEHALTEN** - Automatische Backups |

---

## 5. 🗑️ ZUSAMMENFASSUNG - ZU LÖSCHEN

### Sofort löschen (SICHER):

```powershell
# Templates
Remove-Item "templates\pages\corpus_new.html"

# JavaScript (Legacy)
Remove-Item "static\js\corpus_datatables.js"
Remove-Item "static\js\corpus_filter.js"
Remove-Item "static\js\corpus_script.js"

# CSS (Nicht verwendet)
Remove-Item "static\css\corapan_styles.css"

# LOKAL/database/ Scripts (Veraltet)
Remove-Item "LOKAL\database\corpus_search_performance_patch.py"
Remove-Item "LOKAL\database\database_performance_optimization.py"
Remove-Item "LOKAL\database\test_new_paths.py"
Remove-Item "LOKAL\database\token_id_delete.py"

# Leere Ordner
Remove-Item "qa" -Force -Recurse
Remove-Item "scripts" -Force -Recurse
```

**Gesamtzahl:** 11 Dateien + 2 Ordner können gelöscht werden

### Nach 3-6 Monaten löschen (wenn Production stabil):

```powershell
# Legacy Database Script
Remove-Item "LOKAL\database\legacy\database_creation.py"
```

---

## 6. ✅ AKTUELLE FILES - BESTÄTIGT

### Production-Ready:

**Root:**
- ✅ Alle Config-Files aktuell
- ✅ README.md aktuell und gut

**Static/CSS:**
- ✅ 7 von 8 CSS-Dateien aktiv
- ❌ 1 Legacy (`corapan_styles.css`)

**Static/JS:**
- ✅ 10 von 13 JS-Dateien aktiv
- ❌ 3 Legacy (`corpus_datatables.js`, `corpus_filter.js`, `corpus_script.js`)

**Templates:**
- ✅ 14 von 15 Templates aktiv
- ❌ 1 Legacy (`corpus_new.html`)

**LOKAL/database:**
- ✅ 2 Production-Scripts aktiv
- ✅ 2 Dokumentations-Files aktiv
- ❌ 4 veraltete Migrations-Scripts

---

## 7. 🚀 EMPFOHLENE AKTIONEN

### Priorität 1: Sofort (Kein Risiko)

1. **Leere Ordner entfernen:**
   ```powershell
   Remove-Item "qa" -Force -Recurse
   Remove-Item "scripts" -Force -Recurse
   ```

2. **Legacy Template entfernen:**
   ```powershell
   Remove-Item "templates\pages\corpus_new.html"
   ```

3. **Legacy JS entfernen:**
   ```powershell
   Remove-Item "static\js\corpus_datatables.js"
   Remove-Item "static\js\corpus_filter.js"
   Remove-Item "static\js\corpus_script.js"
   ```

### Priorität 2: Nach Verifikation (Minimales Risiko)

4. **Legacy CSS entfernen (nach Test):**
   ```powershell
   # Erst testen: Webapp starten, alle Seiten prüfen
   Remove-Item "static\css\corapan_styles.css"
   ```

5. **Veraltete DB-Scripts entfernen:**
   ```powershell
   Remove-Item "LOKAL\database\corpus_search_performance_patch.py"
   Remove-Item "LOKAL\database\database_performance_optimization.py"
   Remove-Item "LOKAL\database\test_new_paths.py"
   Remove-Item "LOKAL\database\token_id_delete.py"
   ```

### Priorität 3: Langfristig (Backup-Strategie)

6. **Nach 3-6 Monaten stabiler Production:**
   ```powershell
   Remove-Item "LOKAL\database\legacy\database_creation.py"
   ```

---

## 8. 📊 AUDIT-STATISTIK

| Kategorie | Gesamt | Aktiv | Legacy | Zu löschen |
|-----------|--------|-------|--------|------------|
| **Root-Files** | 13 | 13 | 0 | 0 |
| **CSS** | 8 | 7 | 1 | 1 |
| **JS** | 13 | 10 | 3 | 3 |
| **Templates** | 15 | 14 | 1 | 1 |
| **DB-Scripts** | 8 | 4 | 4 | 4 |
| **Ordner** | 2 | 0 | 2 | 2 |
| **GESAMT** | 59 | 48 | 11 | **11** |

**Cleanup-Potenzial:** 11 Dateien + 2 Ordner = ~18% weniger Files

---

## ✨ FAZIT

### Gut organisiert:
- ✅ Root-Level sauber
- ✅ Templates größtenteils aufgeräumt
- ✅ Migration gut dokumentiert

### Noch aufzuräumen:
- ⚠️ 1 Legacy Template (`corpus_new.html`)
- ⚠️ 3 Legacy JS-Files
- ⚠️ 1 unbenutztes CSS-File
- ⚠️ 4 veraltete DB-Migrations-Scripts
- ⚠️ 2 leere Ordner

### Zustand nach Cleanup:
- 📦 Projekt wird ~18% schlanker
- 🚀 Keine toten Code-Pfade mehr
- 📚 Klare Trennung: Production vs. Migration-Archiv

---

**Erstellt:** 18. Oktober 2025  
**Nächster Schritt:** Cleanup ausführen (siehe Sektion 7)
