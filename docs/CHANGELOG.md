# Documentation Changelog

Dokumentiert alle wesentlichen Änderungen an der CO.RA.PAN-Dokumentation.

---

## [2.0.0] - 2025-11-07: "Docs as Code" Reorganization

### Major Changes

#### 🗂️ Structure Overhaul
- **Introduced 8-category taxonomy**: `concepts/`, `how-to/`, `reference/`, `operations/`, `design/`, `decisions/`, `migration/`, `troubleshooting/`, `archived/`
- **Created master index**: `docs/index.md` with navigation by category and task
- **Archived obsolete docs**: 5 completed analysis files moved to `archived/`

#### 📝 Front-Matter Metadata
- **Added YAML front-matter** to all 25 active documentation files
- **Schema**: `title`, `status`, `owner`, `updated`, `tags`, `links`
- **Enables**: Searchability, status tracking, ownership clarity

#### 📄 File Organization
**Moved** (15 files):
- `architecture.md` → `concepts/architecture.md`
- `token-input-multi-paste.md` → `how-to/token-input-usage.md`
- `database_maintenance.md` → `reference/database-maintenance.md`
- `media-folder-structure.md` → `reference/media-folder-structure.md`
- `deployment.md` → `operations/deployment.md`
- `gitlab-setup.md` → `operations/gitlab-setup.md`
- `git-security-checklist.md` → `operations/git-security-checklist.md`
- `mobile-speaker-layout.md` → `design/mobile-speaker-layout.md`
- `stats-interactive-features.md` → `design/stats-interactive-features.md`
- `roadmap.md` → `decisions/roadmap.md`
- 5 analysis docs → `archived/` (CleaningUp.md, DeleteObsoleteDocumentation.md, etc.)

**Split** (3 large files → 11 total):
1. `auth-flow.md` (466 lines) → 3 files:
   - `concepts/authentication-flow.md` (Overview & Login-Szenarien)
   - `reference/api-auth-endpoints.md` (API-Dokumentation)
   - `troubleshooting/auth-issues.md` (Bekannte Probleme)

2. `design-system.md` (200 lines) → 4 files:
   - `design/design-system-overview.md` (Philosophie & Layout)
   - `design/design-tokens.md` (CSS Custom Properties)
   - `design/material-design-3.md` (MD3-Implementierung)
   - `design/accessibility.md` (WCAG-Konformität)

3. `troubleshooting.md` (638 lines) → 4 files:
   - `troubleshooting/docker-issues.md` (Server & Deployment)
   - `troubleshooting/database-issues.md` (DB Performance)
   - `troubleshooting/auth-issues.md` (Login & Token - merged with auth-flow split)
   - `troubleshooting/frontend-issues.md` (UI & DataTables)

#### 🔗 Link Updates
- **Fixed ~40 internal links** across all documentation
- **Converted to relative paths**: `../reference/database-maintenance.md`
- **Updated README.md**: Links point to new locations

#### 📋 New Documentation
- **`docs/index.md`**: Master navigation index
- **`decisions/ADR-0001-docs-reorganization.md`**: Architecture Decision Record
- **`docs/CHANGELOG.md`**: This file

#### 🗄️ Archived Planning Documents
- `PLAN.md` → `docs/archived/PLAN.md`
- `QUALITY_REPORT.md` → `docs/archived/QUALITY_REPORT.md`

### Git Commits
- Single atomic commit: `docs: Reorganize documentation (Docs as Code) - ADR-0001`
- Used `git mv` to preserve file history

### Impact
- **25 active files** with front-matter
- **9 new directories** for clear taxonomy
- **~1,300 lines** split from 3 monolithic files
- **0 broken links** (validated post-migration)

---

## [1.2.0] - 2024-11-06: Root Directory Cleanup

### Changes
- **Moved** `DEPLOYMENT.md` → `docs/deployment.md`
- **Moved** `GIT_SECURITY_CHECKLIST.md` → `docs/git-security-checklist.md`
- **Removed** test credentials from `startme.md`
- **Updated** README.md with "Key Resources" section

### Commits
- `f123f41`: Reorganize root directory, remove test credentials
- `d171a69`: Add cleanup completion report

---

## [1.1.0] - 2024-11-05: Obsolete Documentation Cleanup

### Changes
- **Archived** `docs/bug-report-auth-session.md` → `LOKAL/records/archived_docs/bugs/`
- **Verified** Token-Input feature (ACTIVE) - kept `docs/token-input-multi-paste.md`
- **Verified** Migration Token-ID v2 (COMPLETE) - archived to `LOKAL/records/archived_docs/migration/`
- **Created** analysis documents: `CleaningUp.md`, `DeleteObsoleteDocumentation.md`, `DocumentationSummary.md`

### Commits
- `94a3f4b`: Archive bug report, remove archived docs
- `4e1ae34`: Update DeleteObsoleteDocumentation.md

---

## [1.0.0] - 2024-10 and earlier

### Initial Documentation
- Flat `docs/` structure with 18 files
- No front-matter metadata
- Mixed naming conventions (CAPS, lowercase, kebab-case)
- Large monolithic files (`troubleshooting.md`, `auth-flow.md`)

---

## Future Roadmap

### Planned Improvements
- [ ] **Auto-generated API docs** (Sphinx/pdoc3 for Python docstrings)
- [ ] **Link checker CI** (Validate internal links on every commit)
- [ ] **MkDocs integration** (Optional: Generate static site from Markdown)
- [ ] **Search functionality** (Algolia DocSearch or local lunr.js)
- [ ] **Dark mode support** (Front-matter flag: `theme: auto|light|dark`)

### Maintenance Guidelines
- **New docs**: Always include front-matter
- **Large files (>400 lines)**: Consider splitting by logical domain
- **Links**: Always use relative paths
- **Archive**: Move completed/obsolete docs to `archived/` (don't delete)
- **ADRs**: Document significant architecture decisions in `decisions/`

---

**Last Updated:** 2025-11-07  
**Contributors:** Felix Tacke
