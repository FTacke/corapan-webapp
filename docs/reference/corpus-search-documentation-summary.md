---
title: "Corpus Search Documentation Summary"
status: active
owner: documentation
updated: "2025-11-08"
tags: [corpus, documentation, index, guide]
links:
  - ../index.md
  - ../CONTRIBUTING.md
---

# Corpus Search Documentation Summary

Übersicht der neulich erstellten Dokumentation zur CO.RA.PAN Corpus-Suchfunktionalität.

---

## Neue Dokumentationsdateien

### 1. `reference/corpus-search-architecture.md` 📚
**Status:** Active | **Länge:** ~1100 Zeilen | **Audience:** Backend/Frontend Developer, Architect

**Inhalt:**
- Vollständige Tech-Stack-Übersicht (Backend + Frontend)
- Datenbankstruktur mit Spalten-Mapping
- SearchParams Dataclass Dokumentation
- Backend-Architektur mit Route-Handlers und Service-Layer
- Frontend-Architektur mit ES6-Modulen
- Detaillierter Datenfluss für beide Suchtypen
- DataTables-Mapping und Column-Index-Referenz
- Filterlogik mit Länder-/Regionalcodes
- Implementierte Suchfunktionen (Simple Search ✅, Token Search ✅)
- Geplante erweiterte Suche (Advanced Search 🚧)

**Verwendung:**
- Gesamtüberblick verstehen
- Architektur-Entscheidungen nachvollziehen
- Neue Features planen

---

### 2. `how-to/corpus-advanced-search-planning.md` 📋
**Status:** Draft | **Länge:** ~800 Zeilen | **Audience:** Backend Developer, Project Manager

**Inhalt:**
- Schritt-für-Schritt-Anleitung für Advanced-Search-Implementierung
- Anforderungen sammeln (Schritt 1)
- SQL-Queries testen (Schritt 2, mit Dry-Run Beispiele)
- Backend-Code-Struktur planen (Schritt 3)
- Frontend-UI-Mockup (Schritt 4)
- Implementierungs-Checklist (Schritt 5)
- Validierung und Testing (Schritt 6)
- Rollback/Backout-Strategie (Schritt 7)

**Verwendung:**
- Advanced Search planen und implementieren
- SQL-Queries vorab testen
- Entwicklungs-Workflow folgen
- Edge-Cases und Performance-Optimierung verstehen

---

### 3. `reference/corpus-search-quick-reference.md` ⚡
**Status:** Active | **Länge:** ~400 Zeilen | **Audience:** Developer (Quick Lookup)

**Inhalt:**
- API-Endpoint-Übersicht (alle Parameter)
- Search-Modes Quick-Table
- Filter-Optionen (Länder, Hablante, Sexo, Modo, Discurso)
- Python Code-Snippets (SearchParams bauen, DB-Queries)
- JavaScript Code-Snippets (DataTables, Filter-Werte auslesen)
- Bash/cURL Beispiele
- URL-Parameter-Kombinationen
- Frontend-Module Import-Struktur
- Performance-Targets
- Debugging-Tipps
- Häufige Fehler + Lösungen

**Verwendung:**
- Schnelle Referenz während Entwicklung
- API-Dokumentation
- Code-Snippets kopieren

---

## Dokumentations-Struktur

```
docs/
├── reference/
│   ├── corpus-search-architecture.md        ← Architektur-Referenz
│   ├── corpus-search-quick-reference.md     ← Quick Lookup
│   └── database-schema.md                   ← DB-Schema (TODO)
├── how-to/
│   ├── corpus-advanced-search-planning.md   ← Schritt-für-Schritt Guide
│   └── token-input-usage.md                 ← Token Input Guide (existing)
├── concepts/
│   └── (architecture, auth-flow, etc.)
├── decisions/
│   └── ADR-0001-docs-reorganization.md
└── CONTRIBUTING.md                         ← Docs-Guidelines
```

---

## Key Takeaways

### Tech-Stack

**Backend:**
- Flask Blueprint (`corpus.py`)
- SQLite3 mit Raw SQL
- searchParams Dataclass

**Frontend:**
- 6 ES6-Module für verschiedene Funktionen
- jQuery 3.7.1 + DataTables 1.13.7
- Select2 4.1.0-rc0 + Tagify
- MD3 Design System

**Database:**
- SQLite `transcription.db`
- Tokens-Tabelle mit 16+ Spalten
- Indexierung auf häufigen Suchfeldern

### Implementierte Features

| Feature | Status | Tab | Suchtyp |
|---------|--------|-----|---------|
| Simple Word Search | ✅ Aktiv | "Búsqueda simple" | text/lemma mit Wildcard |
| Exact Match | ✅ Aktiv | "Búsqueda simple" | text_exact/lemma_exact |
| Token-ID Search | ✅ Aktiv | "Token" | Direkte Token-IDs |
| DataTables Integration | ✅ Aktiv | Beide | Server-Side Processing |
| Statistiken | ✅ Aktiv | "Estadísticas" | ECharts Visualisierung |
| Advanced Search | 🚧 Geplant | "Búsqueda avanzada" | Sequenzen, Regex, etc. |

### Datenfluss

```
User Input
  ↓
Form Submit
  ↓
GET /corpus/search (oder POST)
  ↓
Backend: search_tokens(SearchParams)
  ↓
SQL Query + Filter/Order/Pagination
  ↓
Template Render (HTML mit Ergebnissen)
  ↓
DataTables AJAX Initialization
  ↓
GET /corpus/search/datatables (Server-Side)
  ↓
JSON Response
  ↓
Frontend: DataTables render rows
  ↓
User sees results + statisticscs
```

---

## Nächste Schritte

### Kurz-/Mittelfristig

1. **Database-Schema-Dokumentation**
   - Datei: `docs/reference/database-schema.md`
   - Inhalt: Vollständiges Tokens-Schema mit Indizes
   - Audience: Backend/DevOps

2. **API-Referenz erweitern**
   - Response-Formats detaillieren
   - Error-Handling dokumentieren
   - Rate-Limiting (falls vorhanden)

3. **Frontend-Module-Dokumentation**
   - Jedes Modul einzeln dokumentieren
   - Public API jedes Moduls
   - Event-Flows

### Langfristig

1. **Advanced Search implementieren**
   - Nutze: `docs/how-to/corpus-advanced-search-planning.md`
   - Schritte 1-7 folgen
   - Tests schreiben

2. **Deployment-Guide**
   - Production-Setup
   - Database-Optimierung
   - Performance-Tuning

3. **Troubleshooting-Guide**
   - Häufige Fehler
   - Debug-Strategien
   - Performance-Optimierung

---

## Verwendete Standards

### CO.RA.PAN Docs-Konventionen (aus CONTRIBUTING.md)

✅ **Eingehalten:**
- Front-Matter vollständig (title, status, owner, updated, tags)
- Kebab-case Dateinamen
- Single-Topic Prinzip
- "Siehe auch" Abschnitt mit 3-5 Links
- Relative interne Links
- Kategorisierte Pfade (`reference/`, `how-to/`)

✅ **Spezial-Features:**
- Tabellen für Übersicht
- Code-Blocks mit Syntax-Highlighting
- Strukturierte Workflows (DISCOVER → PLAN → LINT → APPLY → REPORT)
- Deutsche UND englische Terminologie (mit Links)

---

## Datei-Größen

| Datei | Zeilen | Länge | Kategorie |
|-------|--------|-------|-----------|
| `corpus-search-architecture.md` | 1100 | Reference | Komprehensiv |
| `corpus-advanced-search-planning.md` | 800 | How-To | Guide |
| `corpus-search-quick-reference.md` | 400 | Reference | Schnell |
| **Gesamt** | **2300** | — | **Umfassend** |

---

## Maintenance

### Wann aktualisieren?

- ✏️ Nach Backend-Changes (neue Endpoints, Parameter)
- ✏️ Nach Frontend-Changes (neue Module, UI-Updates)
- ✏️ Nach DB-Changes (neue Spalten, Indizes)
- ✏️ Nach Advanced-Search-Implementierung
- ✏️ Jährlich (Wartung + Validierung)

### Wer aktualisiert?

- **Backend-Team:** Architektur, Routes, Services
- **Frontend-Team:** Module, UI-Components
- **DevOps:** Deployment, Performance
- **Documentation Owner:** Front-Matter, Links, Structure

---

## Review-Checklist

**Vor Publish:**

- [x] Front-Matter vollständig?
- [x] Links relativ und funktionierend?
- [x] Dateinamen kebab-case?
- [x] Größe < 1200 Wörter? (nur wenn nicht absichtlich größer)
- [x] "Siehe auch" mit 3-5 Links?
- [x] Code-Beispiele valide?
- [x] Tabellen lesbar?
- [x] Keine Secrets/PII?
- [x] Status korrekt (active/draft/deprecated)?

---

## Lizenz & Attributionen

Diese Dokumentation folgt den **CO.RA.PAN Docs-Guidelines** (siehe `CONTRIBUTING.md`).

**Quellen:**
- Flask API: https://flask.palletsprojects.com/
- DataTables: https://datatables.net/
- SQLite: https://www.sqlite.org/
- CO.RA.PAN Codebase: Direkte Code-Analyse

---

## Siehe auch

- [Main Documentation Index](../index.md) - Zentrale Dokumentations-Übersicht
- [CONTRIBUTING Guidelines](../CONTRIBUTING.md) - Docs-Standards und Konventionen
- [Corpus Page Template](../../templates/pages/corpus.html) - Frontend-Template
- [Corpus Routes](../../src/app/routes/corpus.py) - Backend-Routes
- [Corpus Search Service](../../src/app/services/corpus_search.py) - Search-Logik
