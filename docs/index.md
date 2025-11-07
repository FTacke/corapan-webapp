# CO.RA.PAN Documentation Index

Willkommen zur CO.RA.PAN Dokumentation. Diese Übersicht hilft dir, die richtige Dokumentation für deine Aufgabe zu finden.

---

## 📚 Documentation by Category

### 🧠 Concepts - Was ist das und warum?

Konzeptuelle Übersichten und Architektur-Entscheidungen.

- **[Architecture Overview](concepts/architecture.md)** - Backend/Frontend Architektur, Blueprints
- **[Authentication Flow](concepts/authentication-flow.md)** - JWT, Cookie-Auth, Login-Szenarien

---

### 📖 How-To Guides - Wie mache ich X?

Schritt-für-Schritt-Anleitungen für häufige Aufgaben.

- **[Token Input Usage](how-to/token-input-usage.md)** - Multi-Paste-Feature für Corpus-Tokens

---

### 📋 Reference - Technische Details

API-Dokumentation, Datenbank-Schema, technische Spezifikationen.

- **[API Auth Endpoints](reference/api-auth-endpoints.md)** - JWT-Endpoints, Decorators, Error-Handler
- **[Database Maintenance](reference/database-maintenance.md)** - Schema, Indizes, Wartung, Performance
- **[Media Folder Structure](reference/media-folder-structure.md)** - MP3/Transcript-Organisation

---

### ⚙️ Operations - Betrieb & Deployment

Deployment, CI/CD, Server-Konfiguration, Security.

- **[Deployment Guide](operations/deployment.md)** - Production-Server-Setup, Docker, Updates
- **[GitLab CI/CD Setup](operations/gitlab-setup.md)** - Pipeline-Konfiguration
- **[Git Security Checklist](operations/git-security-checklist.md)** - Security Best Practices

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

Historische Migrations-Guides (meist in `LOKAL/records/archived_docs/migration/`).

- **Keine aktiven Migration-Guides** - Alle Migrationen abgeschlossen

---

### 🔧 Troubleshooting - Problem-Lösungen

Häufige Probleme und deren Lösungen.

- **[Auth Issues](troubleshooting/auth-issues.md)** - Login, Token, Redirect-Probleme
- **[Database Issues](troubleshooting/database-issues.md)** - Performance, Indizes, SQLite
- **[Docker Issues](troubleshooting/docker-issues.md)** - Server, Deployment, Health-Checks
- **[Frontend Issues](troubleshooting/frontend-issues.md)** - DataTables, Audio, Player

---

### 📦 Archived - Historische Dokumente

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

**Last Updated:** 2025-11-07  
**Documentation Version:** 2.0 (Post-Reorganization)
