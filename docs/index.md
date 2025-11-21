# CO.RA.PAN Documentation Index

Willkommen zur CO.RA.PAN Dokumentation. Diese Übersicht hilft dir, die richtige Dokumentation für deine Aufgabe zu finden.

> **🎯 Status (November 2025):** Webapp ist produktionsreif mit allen Hauptfeatures vollständig implementiert. Dokumentation wurde reorganisiert und aktualisiert.

## 🚀 Quick Start

**Neu hier?** Starte mit diesen Dokumenten:
1. **[Architecture Overview](concepts/architecture.md)** - Verstehe die Systemarchitektur
2. **[Development Setup](operations/development-setup.md)** - Entwicklungsumgebung einrichten
3. **[Authentication Guide](guides/authentication.md)** - Umfassender Guide zur Authentifizierung

---

## 📚 Documentation by Category

### 🧠 Concepts - Was ist das und warum?

Konzeptuelle Übersichten und Architektur-Entscheidungen.

- **[Webapp Status Overview](concepts/webapp-status.md)** - Vollständiger Status aller Features, Metriken, Production-Readiness ⭐ NEU
- **[Architecture Overview](concepts/architecture.md)** - Backend/Frontend Architektur, Blueprints
- **[Authentication Flow](concepts/authentication-flow.md)** - JWT, Cookie-Auth, Login-Szenarien
- **[BlackLab Indexing Architecture](concepts/blacklab-indexing.md)** - Corpus Search Engine, Export→Index→Proxy Pipeline
- **[Advanced Search Architecture](concepts/advanced-search-architecture.md)** - Security hardening, streaming design, performance
- **[Search Unification Plan](concepts/search-unification-plan.md)** - Simple vs. Advanced Search, 3-Phasen-Plan, Unified Mapping ⭐ NEU (2025-11-13)

---

### 📖 How-To Guides - Wie mache ich X?

Schritt-für-Schritt-Anleitungen für häufige Aufgaben.

- **[Authentication Guide](guides/authentication.md)** - Alles über Auth: User Experience, Technik, Config (NEW)
- **[Advanced Search Dev Setup](how-to/advanced-search-dev-setup.md)** - BlackLab konfigurieren, starten, debuggen (NEW 2025-11-13)
- **[Token Input Usage](how-to/token-input-usage.md)** - Multi-Paste-Feature für Corpus-Tokens
- **[Build BlackLab Index](how-to/build-blacklab-index.md)** - Index-Build, CLI-Optionen, Validierung
- **[Execute BlackLab Stage 2-3](how-to/execute-blacklab-stage-2-3.md)** - Index-Build ausführen, Tests durchführen (NEW)

---

### 📋 Reference - Technische Details

API-Dokumentation, Datenbank-Schema, technische Spezifikationen.

- **[API Auth Endpoints](reference/api-auth-endpoints.md)** - JWT-Endpoints, Decorators, Error-Handler
- **[Auth Access Matrix](reference/auth-access-matrix.md)** - Route Inventory, CSRF, Public/Protected Routes (NEW 2025-11-11)
- **[Database Maintenance](reference/database-maintenance.md)** - Schema, Indizes, Wartung, Performance
- **[Media Folder Structure](reference/media-folder-structure.md)** - MP3/Transcript-Organisation
- **[BlackLab API Proxy](reference/blacklab-api-proxy.md)** - /bls/** Proxy, CQL-Queries, Endpoints
- **[BLF YAML Schema](reference/blf-yaml-schema.md)** - Index-Konfiguration, Annotations, Metadata
- **[CQL Escaping Rules](reference/cql-escaping-rules.md)** - CQL security, escaping, injection prevention (NEW)
- **[Advanced Export Streaming](reference/advanced-export-streaming.md)** - Export endpoint spec, streaming, performance (NEW)

**Search System Analysis (Bestandsaufnahme):**
- **[ADVANCED SEARCH/BESTANDSAUFNAHME_SIMPLE_VS_ADVANCED.md](ADVANCED SEARCH/BESTANDSAUFNAHME_SIMPLE_VS_ADVANCED.md)** - Vollständige Analyse: Simple vs. Advanced Search
- **[ADVANCED SEARCH/BESTANDSAUFNAHME_SIMPLE_SEARCH.md](ADVANCED SEARCH/BESTANDSAUFNAHME_SIMPLE_SEARCH.md)** - Simple Search Datenfluss-Details
- **[ADVANCED SEARCH/BESTANDSAUFNAHME_ADVANCED_SEARCH.md](ADVANCED SEARCH/BESTANDSAUFNAHME_ADVANCED_SEARCH.md)** - Advanced Search BlackLab-Integration
- **[ADVANCED SEARCH/BESTANDSAUFNAHME_DATATABLES_VERGLEICH.md](ADVANCED SEARCH/BESTANDSAUFNAHME_DATATABLES_VERGLEICH.md)** - Frontend DataTables-Konfiguration
- **[ADVANCED SEARCH/BESTANDSAUFNAHME_GEMEINSAME_BASIS.md](ADVANCED SEARCH/BESTANDSAUFNAHME_GEMEINSAME_BASIS.md)** - Gemeinsames Mapping-Potenzial
- **[ADVANCED SEARCH/BESTANDSAUFNAHME_OFFENE_PUNKTE.md](ADVANCED SEARCH/BESTANDSAUFNAHME_OFFENE_PUNKTE.md)** - Stolpersteine & Offene Fragen

---

### ⚙️ Operations - Betrieb & Deployment

Deployment, CI/CD, Server-Konfiguration, Security.

- **[BlackLab Integration Status](operations/blacklab-integration-status.md)** - Current implementation status
- **[BlackLab Stage 2-3 Report](operations/blacklab-stage-2-3-implementation.md)** - Stage 2-3 complete, index built & tested (NEW)
- **[BlackLab Minimalplan](operations/blacklab-minimalplan.md)** - Setup-Anleitung: Java → Index → BLS → Proxy
- **[BlackLab Quick Reference](operations/blacklab-quick-reference.md)** - Quick start commands and troubleshooting
- **[Development Setup](operations/development-setup.md)** - Local dev environment setup with Make targets
- **[Deployment Guide](operations/deployment.md)** - Production-Server-Setup, Docker, Updates
- **[Git Security Checklist](operations/git-security-checklist.md)** - Security Best Practices
- **[Rate Limiting Strategy](operations/rate-limiting-strategy.md)** - Advanced Search API rate limits (NEW)
- **[Advanced Search Monitoring](operations/advanced-search-monitoring.md)** - Logging, metrics, observability (NEW)

---

### 🎨 Design - UI/UX & Design System

Design-System, Komponenten, Styling, Barrierefreiheit.

- **[Design System Overview](design/design-system-overview.md)** - Philosophie, Layout, Komponenten
- **[Design Tokens](design/design-tokens.md)** - CSS Custom Properties (Farben, Spacing)
- **[Material Design 3](design/material-design-3.md)** - MD3-Implementierung
- **[Accessibility](design/accessibility.md)** - WCAG-Konformität, Kontraste, A11y
- **[Mobile Speaker Layout](design/mobile-speaker-layout.md)** - Mobile Layout-Spezifikation
- **[Stats Interactive Features](design/stats-interactive-features.md)** - Statistik-Charts & Interaktivität

---

### 🗳️ Decisions - Architecture Decision Records

Dokumentierte Architektur-Entscheidungen (ADRs).

- **[ADR-0001: Docs Reorganization](decisions/ADR-0001-docs-reorganization.md)** - "Docs as Code" Reorganisation
- **[Roadmap](decisions/roadmap.md)** - Feature-Roadmap & Development-Priorities

---

### 🔄 Migration - Migrations & Upgrades

Abgeschlossene Migrations-Dokumentation für historische Referenz.

- **[JSON Annotation V2 Implementation](migration/json-annotation-v2-implementation.md)** - Token-ID-System Migration
- **[Speaker Code Standardization](migration/speaker-code-standardization.md)** - Sprechercode-Normalisierung
- **[EEUU to USA Standardization](migration/eeuu-to-usa-standardization.md)** - Ländercode-Vereinheitlichung
- **[Turbo to HTMX Migration](migration/turbo-to-htmx-migration-report.md)** - Frontend Framework Wechsel
- **Status**: Alle Hauptmigrationen abgeschlossen ✅

---

### 🔧 Troubleshooting - Problem-Lösungen

Häufige Probleme und deren Lösungen.

- **[Auth Issues](troubleshooting/auth-issues.md)** - Login, Token, Redirect-Probleme
- **[Database Issues](troubleshooting/database-issues.md)** - Performance, Indizes, SQLite
- **[Docker Issues](troubleshooting/docker-issues.md)** - Server, Deployment, Health-Checks
- **[Frontend Issues](troubleshooting/frontend-issues.md)** - DataTables, Audio, Player
- **[BlackLab Issues](troubleshooting/blacklab-issues.md)** - Server, Indexing, Proxy, Search Errors

---

### 📊 Reports - Recent Implementation Reports

Aktuelle Fix-Reports und Rollout-Dokumentation (November 2025).

**Authentication & Security:**
- **[Auth & Logout V3 Final Fix (2025-11-11)](reports/2025-11-11-auth-logout-v3-fix.md)** - GET Logout, CSRF Exemption
- **[Auth Public Access Fix (2025-11-11)](reports/2025-11-11-auth-public-access-fix.md)** - Public Corpus Access
- **[Auth Navigation Hardening (2025-11-11)](reports/auth-navigation-hardening-2025-11-11.md)** - Navigation Security

**Advanced Search:**
- **[Advanced Search Finalization (2025-11-11)](reports/2025-11-11-advanced-search-finalization.md)** - UI Completion
- **[Advanced Search Fixes (2025-11-11)](reports/2025-11-11-advanced-search-fixes.md)** - Bug Fixes
- **[CSS Audit Summary (2025-11-11)](reports/2025-11-11-audit-summary.md)** - CSS Compliance

> **Hinweis:** Ältere Reports befinden sich in [archived/](archived/)

---

### �📦 Archived - Historische Dokumente

Abgeschlossene Analysen, obsolete Dokumentation.

- **[Cleaning Up](archived/CleaningUp.md)** - File-Cleanup-Analyse (2024-11)
- **[Delete Obsolete Documentation](archived/DeleteObsoleteDocumentation.md)** - Obsolete Docs Analysis
- **[Root Directory Analysis](archived/RootDirectoryDocumentationAnalysis.md)** - Root-File Reorganisation
- **[Cleanup Completion Report](archived/CLEANUP_COMPLETION_REPORT.md)** - Final Cleanup-Report
- **[Documentation Summary](archived/DocumentationSummary.md)** - Legacy Documentation Index

---

## 🔍 Quick Links by Task

### Ich möchte...

**...die App lokal starten:**
→ Siehe [Deployment Guide](operations/deployment.md) → Development-Setup

**...einen Bug fixen:**
1. Symptom identifizieren → [Troubleshooting](troubleshooting/)
2. Code-Referenz finden → [Architecture](concepts/architecture.md)
3. Tests ausführen → [Database Maintenance](reference/database-maintenance.md)

**...ein neues Feature bauen:**
1. Design-Richtlinien → [Design System](design/design-system-overview.md)
2. Auth-Check → [Authentication Flow](concepts/authentication-flow.md)
3. DB-Schema prüfen → [Database Maintenance](reference/database-maintenance.md)

**...die Datenbank warten:**
→ Siehe [Database Maintenance](reference/database-maintenance.md)

**...auf Production deployen:**
→ Siehe [Deployment Guide](operations/deployment.md) → Production-Deployment

**...Accessibility prüfen:**
→ Siehe [Accessibility](design/accessibility.md) → Testing Tools

---

## 📝 Documentation Conventions

> **For Contributors:** See **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed guidelines on writing, structuring, and maintaining documentation.

### Front-Matter Metadata

Alle aktiven Dokumente verwenden YAML-Front-Matter:

```yaml
---
title: "Document Title"
status: active | deprecated | archived
owner: backend-team | frontend-team | devops | documentation
updated: "2025-11-07"
tags: [tag1, tag2, tag3]
links:
  - relative/path/to/related-doc.md
---
```

### File Naming

- **Kebab-case**: `authentication-flow.md` (nicht `Authentication_Flow.md`)
- **Descriptive**: `api-auth-endpoints.md` (nicht `api.md`)
- **No dates**: `troubleshooting/auth-issues.md` (nicht `auth-issues-2024-11.md`)

### Internal Links

**Relative Pfade** verwenden:
```markdown
[Database Maintenance](../reference/database-maintenance.md)
```

Nicht absolute Pfade oder Root-Pfade (`/docs/...`).

---

## 🆘 Support

**Bei Fragen:**
- Prüfe zuerst [Troubleshooting](troubleshooting/)
- Suche in diesem Index nach Keywords
- Schau in [Architecture Overview](concepts/architecture.md) für System-Überblick

**Dokumentation fehlt?**
- Erstelle ein Issue im GitLab-Repo
- Oder füge selbst hinzu (Pull Request)

---

**Last Updated:** 2025-11-11  
**Documentation Version:** 2.1 (Current Status Update)
