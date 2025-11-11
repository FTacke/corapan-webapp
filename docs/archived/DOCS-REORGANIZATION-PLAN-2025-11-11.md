---
title: "Docs Reorganization Plan (2025-11-11) [ARCHIVED]"
status: archived
owner: documentation
updated: "2025-11-11"
tags: [documentation, reorganization, archived, planning, 2.5.0]
links:
  - ../decisions/ADR-0001-docs-reorganization.md
  - ../CONTRIBUTING.md
---

# Docs Reorganization Plan (2025-11-11) [ARCHIVED]

**ARCHIVED**: 2025-11-11  
**Reason**: Plan wurde umgesetzt. Laufende Guidelines sind in `CONTRIBUTING.md`.  
**Status**: ✅ Durchgeführt  

---

## Summary

Dokumentation wurde gemäß CONTRIBUTING.md Guidelines neu organisiert:

### Archiviert (Root → /docs/archived/)
- `ADVANCED-SEARCH-UI-COMPLETE.md` → `docs/archived/ADVANCED-SEARCH-UI-COMPLETE-2025-11-10.md`
- `HARDENING-COMPLETION-REPORT.md` → `docs/archived/HARDENING-COMPLETION-REPORT-2025-11-10.md`
- `HARDENING-PLAN-2025-11-10.md` → Merged in Hardening Report
- `DOCS-REORGANIZATION-PLAN-2025-11-11.md` → Diese Datei

### Neu Erstellt (nach CONTRIBUTING.md)
- `docs/how-to/advanced-search-ui-finalization.md` ✅
- `docs/concepts/advanced-search-architecture.md` ✅ (existierte bereits)
- `docs/reference/advanced-export-streaming.md` ✅ (existierte bereits)
- `docs/operations/rate-limiting-strategy.md` ✅ (existierte bereits)

### Updated
- `docs/CONTRIBUTING.md` - Link zu `advanced-search-ui-finalization.md` hinzugefügt

---

## Struktur (Final)

```
/docs/
  ├── concepts/           # ✅ Advanced Search Architecture
  ├── how-to/             # ✅ Advanced Search UI Finalization
  ├── reference/          # ✅ Advanced Export Streaming, Rate Limiting
  ├── operations/         # ✅ Rate Limiting, Monitoring
  ├── archived/           # ✅ Completion Reports
  └── CONTRIBUTING.md     # ✅ Updated mit neuen Links
```

---

## Rationale

Alle Dokumentation folgt jetzt den CO.RA.PAN CONTRIBUTING Guidelines:
- ✅ Kategorisiert nach Divio Pattern (Concepts/How-To/Reference/Operations)
- ✅ Single-Topic Prinzip (eine Datei = ein Thema)
- ✅ Front-Matter (title, status, owner, updated, tags)
- ✅ Relativ Links
- ✅ Kebab-case Dateinamen

**Siehe auch**: [CONTRIBUTING.md](../CONTRIBUTING.md)
