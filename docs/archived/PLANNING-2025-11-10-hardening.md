---
title: "Hardening Planning Document - Advanced Search (2025-11-10)"
status: archived
owner: documentation
updated: "2025-11-10"
tags: [planning, hardening, advanced-search, security, 2025]
links:
  - archived/IMPLEMENTATION-REPORT-2025-11-10-hardening.md
  - concepts/advanced-search-architecture.md
  - reference/cql-escaping-rules.md
---

# HARDENING PLAN - Advanced Search Export & Security

**Date:** 2025-11-10  
**Workflow:** DISCOVER → PLAN → LINT → APPLY → REPORT  
**Status:** PLAN (DRY RUN - Freigabe erforderlich)

---

## DISCOVER: Betroffene Dateien

### Backend (Python/Flask)

**Neu zu erstellen:**
- `src/app/routes/advanced_export.py` - Export-Endpoint mit Hardening

**Zu modifizieren:**
- `src/app/routes/advanced.py` - `recordsTotal/Filtered` konsistent, Escaping, Logging
- `src/app/security/rate_limiter.py` - Separate Export-Limits
- `src/app/security/cql_validator.py` - Neue Escaping-Logik (oder in advanced.py)

### Frontend (JavaScript)

**Zu modifizieren:**
- `static/js/modules/advanced/formHandler.js` - URL-State-Restore, URL-lesen beim Load
- `static/js/modules/advanced/initTable.js` - Error-Bilder (CQL-Fehler, Leertreffer)
- `templates/search/advanced.html` - `<caption>`, `scope="col"`, A11y-Fixes

### Testing (Python)

**Zu erstellen/erweitern:**
- `scripts/test_advanced_hardening.py` - Export-Tests, CQL-Tests, Rate-Limit-Tests
- `scripts/test_advanced_search_real.py` - Tests mit 3 CQL-Varianten, Filterfall

### Dokumentation (Markdown)

**Neue Docs:**
- `docs/reference/advanced-export-streaming.md` - Export-Spezifikation (Headers, BOM, Chunks)
- `docs/reference/cql-escaping-rules.md` - CQL-Quoting-Regeln (intern + für UI)
- `docs/operations/rate-limiting-strategy.md` - Separate Limits für /export

**Zu modifizieren:**
- `docs/TESTING-advanced-search-ui.md` - Hardening-Tests hinzufügen
- `docs/CONTRIBUTING.md` - Falls relevant (wahrscheinlich nicht)

**Zu archivieren:**
- `ADVANCED-SEARCH-UI-COMPLETE.md` (ist temporärer Bericht, nicht im Docs-Standard)

---

## PLAN (DRY RUN)

### Backend Changes

| Datei (alt) | Datei (neu) | Aktion | Priorität | Grund |
|---|---|---|---|---|
| – | `src/app/routes/advanced_export.py` | create | P0 | Export-Endpoint mit Content-Disposition, Streaming, BOM, UTF-8 |
| – | `src/app/security/cql_validator.py` | create | P0 | CQL-Escaping: `"` → `\"`, Klammern-Balancing, Reject-Logic |
| `src/app/routes/advanced.py` | – | modify | P0 | **Punkt 2:** recordsTotal/Filtered = numberOfHits, logging, error-handling |
| `src/app/routes/advanced.py` | – | modify | P0 | **Punkt 3:** CQL-Escaping aufrufen, 400 bei verdächtig |
| `src/app/security/rate_limiter.py` | – | modify | P1 | **Punkt 4:** Separate Buckets `/export` (6/min) vs `/data` (30/min) |
| `src/app/routes/advanced.py` | – | modify | P0 | **Punkt 8:** Logging: BLS-duration, numberOfHits, Client-Disconnect |

### Frontend Changes

| Datei (alt) | Datei (neu) | Aktion | Priorität | Grund |
|---|---|---|---|---|
| `templates/search/advanced.html` | – | modify | P1 | **Punkt 5:** `<caption>`, `scope="col"`, `aria-live="polite"` auf Summary |
| `static/js/modules/advanced/formHandler.js` | – | modify | P0 | **Punkt 6:** URL-Parsing beim Load, Select2-Restore vor DataTables-Init |
| `static/js/modules/advanced/initTable.js` | – | modify | P0 | **Punkt 7:** Error-Handler CQL-Syntax, Leertreffer-Image |

### Testing

| Datei (alt) | Datei (neu) | Aktion | Priorität | Grund |
|---|---|---|---|---|
| – | `scripts/test_advanced_hardening.py` | create | P0 | **Punkt 9:** Export-Tests, CQL-Varianten, Filterfall |
| `scripts/test_advanced_search_real.py` | – | modify | P0 | **Punkt 9:** Tests für docsRetrieved vs numberOfDocs |

### Documentation

| Datei (alt) | Datei (neu) | Aktion | Priorität | Grund |
|---|---|---|---|---|
| – | `docs/reference/advanced-export-streaming.md` | create | P1 | Export-Spec: Headers, BOM, Chunk-Size 1000 |
| – | `docs/reference/cql-escaping-rules.md` | create | P1 | CQL-Quoting: `"text"`, `[pos="NN"]`, Escape-Tabelle |
| – | `docs/operations/rate-limiting-strategy.md` | create | P1 | Rate-Limit-Strategie: separate Buckets |
| `docs/TESTING-advanced-search-ui.md` | – | modify | P1 | Hardening-Tests hinzufügen (Export, CQL, Rate-Limit) |
| `ADVANCED-SEARCH-UI-COMPLETE.md` | `docs/archived/IMPLEMENTATION-REPORT-2025-11-10-advanced-search-ui.md` | rename | P2 | Archivierungspflicht nach CONTRIBUTING.md |

---

## Wichtige Entscheidungen

| Problem | Lösung | Grund |
|---------|--------|-------|
| **Streaming-Chunk-Größe** | 1000 Zeilen | Balance: Speicher vs HTTP-Overhead |
| **recordsTotal vs numberOfHits** | Beide = numberOfHits | Konsistenz DataTables ↔ Backend |
| **Export-Limits vs Query-Limits** | Separate Buckets | Export ist teurer (Streaming) |
| **CQL-Escaping-Ort** | Backend (validator.py) + Frontend-Error-Message | Defense in Depth |
| **State-Restore** | URL-Query beim Load | Bookmarkable, shareable Links |
| **Leertreffer-UI** | "0 resultados" statt leerer Tabelle | UX: Klarheit statt technisches Rauschen |

---

## Siehe auch

- [Hardening Implementation Report](archived/IMPLEMENTATION-REPORT-2025-11-10-hardening.md) - Implementation results and completion status
- [Advanced Search Architecture](../concepts/advanced-search-architecture.md) - System design and hardening overview
- [CQL Escaping Rules](../reference/cql-escaping-rules.md) - CQL validation and escaping specifications
