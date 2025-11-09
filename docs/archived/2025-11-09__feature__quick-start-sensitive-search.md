# 2025-11-09 Feature: Sensitive Search Implementation - Quick Start

> **Status:** ARCHIVED (superseded by formal documentation)  
> **Reason:** Original implementation summary; replaced by ADR-0005 + Specification + How-To  
> **Date Archived:** 2025-11-09

---

See official documentation:
- `decisions/ADR-0005-sensitive-search.md` - Decision record
- `reference/sensitive-search-specification.md` - Technical spec
- `how-to/enable-sensitive-search.md` - Deployment guide

---

## Quick Summary (For Reference)

Implementation of case/accent-insensitive search toggle:

**Features:**
- ✅ UI Checkbox ("Sensibilidad a mayúsculas y acentos")
- ✅ localStorage persistence
- ✅ Backend query-branching (sensitive=0/1)
- ✅ Database support (norm column + index)
- ✅ Full backwards-compatibility

**Files Modified:**
- templates/pages/corpus.html
- static/js/modules/corpus/datatables.js
- src/app/services/corpus_search.py
- src/app/routes/corpus.py
- src/app/__init__.py

**Status:** ✅ PRODUCTION READY
