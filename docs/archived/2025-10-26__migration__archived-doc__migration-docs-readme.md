# LOKAL - Projektinterne Dokumentation & Entwicklung

Dieser Ordner enthält projektinterne Ressourcen, die nicht in die Produktion deployed werden.

## 📁 Struktur

### `/Roadmaps/` - Security & Feature Roadmaps
Enthält alle Roadmaps, Implementierungsberichte und Testdokumentationen für die Security-Modernisierung und Feature-Entwicklung.

**Dateien:**
- `SECURITY_MODERNIZATION_ROADMAP.md` - Hauptroadmap für Security-Updates (Phase 1-3)
- `SECURITY_QUICKSTART.md` - Quick Reference für Security-Features
- `JWT_TOKEN_REFRESH_GUIDE.md` - Detaillierter Guide zum JWT Refresh Token System
- `PHASE1_IMPLEMENTATION_SUMMARY.md` - Phase 1 Implementation Details
- `PHASE1_TEST_REPORT.md` - Phase 1 Test Results
- `PHASE2_IMPLEMENTATION_SUMMARY.md` - Phase 2 Implementation Details
- `PHASE2_TEST_REPORT.md` - Phase 2 Test Results

### `/Design/` - UI/UX Design Dokumentation
Material Design 3 (MD3) Modernisierung und Design-System-Dokumentation.

**Dateien:**
- `MD3_DESIGN_MODERNISIERUNG.md` - MD3 Migration Guide
- `MD3_QUICK_REFERENCE.md` - MD3 Component Reference
- `CSP_BOOTSTRAP_ICONS_FIX.md` - Content Security Policy Fixes

### `/Admin/` - Admin & Session Dokumentation
Analysen zum Admin-Dashboard und Session-Summaries.

**Dateien:**
- `ADMIN_DASHBOARD_ANALYSIS.md` - Admin Dashboard Analyse
- `SESSION_SUMMARY_2025-10-19.md` - Entwicklungs-Session vom 19.10.2025

### `/Tests/` - Test-Suite
Python-Test-Dateien für alle Features.

**Dateien:**
- `test_phase2.py` - Phase 2 Feature Tests (Haupttest-Suite)
- `test_caching.py` - Cache Performance Tests
- `test_jwt_refresh.py` - JWT Refresh Token Tests
- `test_return_url.py` - Return-to-Intended-URL Tests
- `test_summary.py` - Test Summary Reporter

### `/analysis/` - Datenanalyse
Python-Skripte für Tense-Analysen und alte Ergebnisse.

### `/annotation/` - Annotationsskripte
Skripte für die Annotation von Grabaciones.

### `/database/` - Datenbank-Verwaltung
Datenbank-Erstellung, Migration und Backups.

### `/migration/` - Datenmigration
Migration von alter zu neuer Datenbankstruktur.

### `/security/` - Security-Skripte
Passwort-Hashing und Security-Tools.

### `/zenodo_corpus/` - Zenodo-Export
Skripte für Corpus-Export zu Zenodo.

---

## 🎯 Verwendung

### Roadmap-Dokumente ansehen
```bash
cd LOKAL/Roadmaps
# Öffne gewünschtes Dokument in deinem Editor
```

### Tests ausführen
```bash
cd LOKAL/Tests
python test_phase2.py
```

### Design-Referenz
```bash
cd LOKAL/Design
# Öffne MD3_QUICK_REFERENCE.md für schnelle Referenz
```

---

**Letzte Aktualisierung:** 2025-10-19
