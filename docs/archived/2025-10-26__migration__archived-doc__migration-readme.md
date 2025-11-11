# Migration & Legacy - Übersicht

Dieser Ordner enthält alle Dokumentation, Scripts und Backups zur Migration und Modernisierung der CO.RA.PAN Web-Applikation.

## 📂 Struktur

```
LOKAL/migration/
├── docs/           # Migrations-Dokumentation (MD-Dateien)
├── scripts/        # Migrations- und Test-Scripts (Python)
├── backups/        # Design-Backups und Legacy-Code
└── README.md       # Diese Datei
```

## 📄 Hauptdokumentation

**→ Siehe [`MIGRATION_STATUS.md`](./MIGRATION_STATUS.md) für vollständige Übersicht**

Diese Datei enthält:
- ✅ Abgeschlossene Migrationen
- 🔧 Verbleibende Legacy-Elemente
- 🎯 Noch zu erledigende Aufgaben
- 📊 Migration-Statistik
- 🔍 Erkenntnisse & Empfehlungen

## 🗂️ Inhalt nach Kategorie

### Dokumentation (`docs/`)

#### Datenbank-Migration
- `DATABASE_MIGRATION_SUMMARY.md` - Migration auf neue Media-Ordnerstruktur
- `phase1_completion_report.md` - Performance-Optimierung mit Indexes
- `phase2_serverside_datatables_complete.md` - Server-Side DataTables

#### UI-Migration
- `corpus_datatables_migration.md` - Corpus-Seite DataTables Migration
- `player_md3_migration_summary.md` - Player MD3 Design Migration
- `MOBILE_LAYOUT_*.md` (5 Dateien) - Mobile Layout Optimierungen
- `MOBILE_PLAYER_*.md` (3 Dateien) - Mobile Player Fixes

#### Refactoring
- `REFACTORING_COMPLETE.md` - Abschluss Player-Refactoring
- `REFACTORING_NIGHT_SESSION.md` - Refactoring-Session Protokoll

### Scripts (`scripts/`)

- `organize_media_files.py` - Media-Dateien in Country-Ordner organisieren
- `test_cleanup.py` - Audio-Snippet-Cleanup testen
- `test_cleanup_direct.py` - Direkter Cleanup-Test
- `test_country_extraction.py` - Country-Code-Extraktion testen
- `render_check.py` - Template-Rendering validieren

### Backups (`backups/`)

- `design_backups/` - Alte Design-Iterationen (HTML/CSS)
- `components_backup_20251016_231754.css` - CSS-Backup vor MD3-Migration
- `nav_legacy.html` - Altes Navigation-Template

## 🎯 Verwendungszweck

**Dieser Ordner ist für:**
- 📚 Historische Dokumentation von Migrations-Schritten
- 🔧 Wartungs-Scripts die gelegentlich benötigt werden
- 💾 Sicherheits-Backups von alten Design-Versionen
- 🔍 Nachvollziehbarkeit von Änderungen

**Nicht für:**
- ❌ Produktions-Code (liegt in `src/`)
- ❌ Aktive Webapp-Dateien (liegt in `static/`, `templates/`)
- ❌ Datenbanken (liegt in `data/db/`)

## ⚠️ Wichtig

- **Git-Ignore:** Gesamter `LOKAL/`-Ordner ist von Git ausgeschlossen
- **Backup:** Backups sind lokal, nicht im Repository
- **Legacy-Code:** Produktions-Legacy-Code liegt teils noch in `src/` - siehe `MIGRATION_STATUS.md`

## 📖 Weitere Dokumentation

Hauptdokumentation der Webapp:
- `docs/architecture.md` - Webapp-Architektur
- `docs/roadmap.md` - Entwicklungsplan
- `docs/database_maintenance.md` - Datenbank-Wartung
- `docs/media-folder-structure.md` - Media-Ordnerstruktur

---

**Erstellt:** 18. Oktober 2025  
**Zweck:** Zentralisierung aller Migrations-Materialien
