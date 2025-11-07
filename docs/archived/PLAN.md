# Documentation Reorganization Plan (DRY RUN)

**Date:** 2025-11-07  
**Mode:** DRY_RUN=true  
**Scope:** /docs/** + /LOKAL/records/**  

---

## Executive Summary

This plan reorganizes 18 documentation files in `/docs` and ~68 files in `/LOKAL/records` according to "Docs as Code" principles with clear categorization, consistent naming, front-matter metadata, and modular structure.

### Statistics (Preliminary)
- **Total files to process:** ~86 MD files
- **Files to rename/move:** 18 (from /docs)
- **Files to archive:** ~68 (already in LOKAL/records/archived_docs)
- **Files to split:** 3-5 (long documents > 1200 words)
- **New directory structure:** 8 categories
- **Links to fix:** TBD (after full scan)
- **Front-matter to add:** 18 active files

---

## Proposed Directory Structure

```
/docs
  /concepts            # Architectural concepts and ideas
  /how-to             # Step-by-step guides
  /reference          # API, CLI, schema references
  /operations         # Deployment, maintenance, runbooks
  /design             # UI/UX, design tokens, components
  /decisions          # Architecture Decision Records (ADRs)
  /migration          # Migration paths and records
  /troubleshooting    # Error diagnostics and solutions
  /archived           # Historical/deprecated documents
  index.md            # Master index with links to all sections
```

---

## File Mapping: /docs → New Structure

| # | Old Path | New Path | Action | Type | Reason | Status |
|---|----------|----------|--------|------|--------|--------|
| 1 | `architecture.md` | `concepts/architecture-overview.md` | MOVE + ADD_FRONTMATTER | concept | Core architectural concepts | active |
| 2 | `auth-flow.md` | Split: | SPLIT | - | >1200 words, multiple topics | - |
|   | → | `concepts/auth-flow.md` | NEW | concept | Authentication concepts | active |
|   | → | `how-to/handle-expired-jwt.md` | NEW | how-to | JWT expiration handling | active |
|   | → | `troubleshooting/auth-cookie-race.md` | NEW | troubleshooting | /auth/ready race condition | active |
| 3 | `CleaningUp.md` | `archived/cleanup-analysis-2025-11.md` | MOVE | archived | One-time cleanup analysis | archived |
| 4 | `CLEANUP_COMPLETION_REPORT.md` | `archived/cleanup-completion-2025-11.md` | MOVE | archived | Completion report (historical) | archived |
| 5 | `database_maintenance.md` | `operations/database-maintenance.md` | MOVE + ADD_FRONTMATTER | operations | DB operations guide | active |
| 6 | `DeleteObsoleteDocumentation.md` | `archived/obsolete-docs-analysis-2025-11.md` | MOVE | archived | Historical analysis | archived |
| 7 | `deployment.md` | `operations/deployment.md` | MOVE + ADD_FRONTMATTER | operations | Production deployment | active |
| 8 | `design-system.md` | Split: | SPLIT | - | >1200 words, multiple topics | - |
|   | → | `design/md3-foundations.md` | NEW | design | MD3 design system basics | active |
|   | → | `design/color-palette.md` | NEW | design | Color tokens and usage | active |
|   | → | `design/typography.md` | NEW | design | Typography system | active |
|   | → | `design/components.md` | NEW | design | Component patterns | active |
| 9 | `DocumentationSummary.md` | `index.md` | RENAME + RESTRUCTURE | index | Master documentation index | active |
| 10 | `git-security-checklist.md` | `operations/git-security-checklist.md` | MOVE + ADD_FRONTMATTER | operations | Security best practices | active |
| 11 | `gitlab-setup.md` | `operations/ci-cd-gitlab.md` | RENAME + ADD_FRONTMATTER | operations | CI/CD configuration | active |
| 12 | `media-folder-structure.md` | `reference/media-folder-structure.md` | MOVE + ADD_FRONTMATTER | reference | Media organization reference | active |
| 13 | `mobile-speaker-layout.md` | `design/mobile-speaker-layout.md` | MOVE + ADD_FRONTMATTER | design | Mobile layout specification | active |
| 14 | `roadmap.md` | `decisions/roadmap.md` | MOVE + ADD_FRONTMATTER | decisions | Development roadmap | active |
| 15 | `RootDirectoryDocumentationAnalysis.md` | `archived/root-docs-analysis-2025-11.md` | MOVE | archived | One-time analysis | archived |
| 16 | `stats-interactive-features.md` | `design/stats-interactive-features.md` | MOVE + ADD_FRONTMATTER | design | Stats feature design | active |
| 17 | `token-input-multi-paste.md` | `design/token-input-multi-paste.md` | MOVE + ADD_FRONTMATTER | design | Token input feature | active |
| 18 | `troubleshooting.md` | `troubleshooting/common-issues.md` | MOVE + ADD_FRONTMATTER | troubleshooting | General troubleshooting | active |

---

## File Mapping: LOKAL/records → Archive Strategy

**Note:** Files in `/LOKAL/records/archived_docs/` are already archived and will remain there. They represent historical records and are not part of the active documentation.

### LOKAL/records Active Files (Move to /docs)

| Old Path | New Path | Action | Type | Reason |
|----------|----------|--------|------|--------|
| `LOKAL/records/README.md` | `operations/records-conventions.md` | MOVE | operations | Process documentation conventions |
| `LOKAL/records/PROCESS_LOG.md` | Keep in LOKAL | NO_ACTION | - | Active process log (not docs) |

### LOKAL/records/archived_docs (Status: Already Archived)

**Total:** ~66 files in categories:
- `/admin/` - 2 files (archived admin docs)
- `/bugs/` - 1 file (bug-report-auth-session.md)
- `/design/` - 7 files (archived design iterations)
- `/migration/` - 38 files (historical migration records)
- `/roadmaps/` - 15 files (archived roadmap versions)
- `/tests/` - 1 file (archived test snapshot)

**Action:** NO_ACTION - These files are correctly archived and serve as historical reference.

### LOKAL/records Active Recommendations (Optional)

| Old Path | New Path | Action | Type |
|----------|----------|--------|------|
| `LOKAL/records/css/finding/2025-11-01__responsive-design-audit.md` | `design/responsive-design-audit.md` | CONSIDER_MOVE | design |
| `LOKAL/records/frontend/recommendation/*.md` | Review individually | REVIEW | - |

---

## Splitting Strategy

### 1. auth-flow.md → 3 files

**Original:** 466 lines, ~3500 words

**Split Plan:**
1. **concepts/auth-flow.md** (Lines 1-200)
   - Overview
   - JWT Cookie-Based Auth
   - Cookie Configuration
   - Login-Flow with Auth-Ready-Page
   
2. **how-to/handle-expired-jwt.md** (Lines 200-350)
   - Technical Implementation
   - Flask Decorators (@jwt_required)
   - JWT Error Handlers
   - Step-by-step expiration handling
   
3. **troubleshooting/auth-cookie-race.md** (Lines 350-466)
   - Problem: Cookie-Timing Race Condition
   - Solution: /auth/ready Intermediate Page
   - Browser-specific issues
   - Debugging guide

### 2. design-system.md → 4 files

**Original:** 200 lines, ~1200 words

**Split Plan:**
1. **design/md3-foundations.md**
   - Overview
   - Design Principles
   - Layout Principles
   
2. **design/color-palette.md**
   - Color Palette
   - Token definitions
   - Usage examples
   
3. **design/typography.md**
   - Typography system
   - Font families
   - Size scales
   
4. **design/components.md**
   - Component Notes
   - Button styles
   - Card patterns

### 3. troubleshooting.md → Keep as single + extract sections

**Original:** 638 lines, ~4500 words

**Strategy:** Keep as `troubleshooting/common-issues.md` but extract specific guides:
- Extract "Performance-Probleme" → `troubleshooting/performance-slow-search.md`
- Extract "Audio-Probleme" → `troubleshooting/audio-playback-issues.md`
- Extract "Player-Probleme" → `troubleshooting/player-not-loading.md`

---

## Front-Matter Schema

All active files will receive this front-matter:

```yaml
---
title: <Clear Title>
status: active
owner: corapan-team
updated: 2025-11-07
tags: [<relevant-tags>]
links:
  - /docs/<related-file-1>
  - /docs/<related-file-2>
---
```

### Generated Front-Matter Examples

**concepts/architecture-overview.md:**
```yaml
---
title: CO.RA.PAN Architecture Overview
status: active
owner: corapan-team
updated: 2025-11-07
tags: [architecture, backend, frontend, deployment]
links:
  - /docs/concepts/auth-flow.md
  - /docs/operations/deployment.md
  - /docs/design/md3-foundations.md
---
```

**operations/database-maintenance.md:**
```yaml
---
title: Database Maintenance and Updates
status: active
owner: corapan-team
updated: 2025-11-07
tags: [database, sqlite, maintenance, operations]
links:
  - /docs/operations/deployment.md
  - /docs/troubleshooting/performance-slow-search.md
  - /docs/how-to/rebuild-database.md
---
```

**design/md3-foundations.md:**
```yaml
---
title: Material Design 3 Foundations
status: active
owner: corapan-team
updated: 2025-11-07
tags: [design, md3, ui, foundations]
links:
  - /docs/design/color-palette.md
  - /docs/design/typography.md
  - /docs/design/components.md
---
```

---

## Link Fixup Strategy

### Internal Links to Update

**Pattern Detection:**
- `docs/architecture.md` → `concepts/architecture-overview.md`
- `docs/auth-flow.md` → `concepts/auth-flow.md`
- `DEPLOYMENT.md` → `operations/deployment.md`
- `GIT_SECURITY_CHECKLIST.md` → `operations/git-security-checklist.md`

### Cross-Reference Updates

Files referencing other docs will be updated:
1. **README.md** (Root) - Update all /docs links
2. **index.md** (new) - Create comprehensive index
3. **All active docs** - Fix internal cross-references

### Example Fixups

**Before:**
```markdown
See `docs/architecture.md` for details.
Refer to `DEPLOYMENT.md` for deployment steps.
```

**After:**
```markdown
See [Architecture Overview](concepts/architecture-overview.md) for details.
Refer to [Deployment Guide](operations/deployment.md) for deployment steps.
```

---

## ADR (Architecture Decision Records)

No existing ADRs found. Roadmap can be converted:

**New ADR:**
```
/docs/decisions/ADR-0001-2025-11-07-modular-docs-structure.md
```

**Content Structure:**
- Date: 2025-11-07
- Status: Accepted
- Owners: corapan-team
- Context: Documentation growth requires clear structure
- Decision: Adopt Docs-as-Code with 8-category structure
- Consequences: Better findability, consistency, maintainability
- Alternatives: Single-folder flat structure, wiki-based
- Links: index.md

---

## Archive Strategy

### Files to Archive (Set status=archived)

1. **CleaningUp.md** → archived/cleanup-analysis-2025-11.md
   - Reason: One-time cleanup analysis, historical record
   - Replacement: None (completed task)
   
2. **CLEANUP_COMPLETION_REPORT.md** → archived/cleanup-completion-2025-11.md
   - Reason: Historical completion report
   - Replacement: None (completed task)
   
3. **DeleteObsoleteDocumentation.md** → archived/obsolete-docs-analysis-2025-11.md
   - Reason: One-time analysis, now completed
   - Replacement: None (completed task)
   
4. **RootDirectoryDocumentationAnalysis.md** → archived/root-docs-analysis-2025-11.md
   - Reason: One-time analysis, now completed
   - Replacement: None (completed task)

### Archive Front-Matter

```yaml
---
title: <Original Title>
status: archived
owner: corapan-team
updated: 2025-11-07
archived_date: 2025-11-07
archived_reason: One-time analysis completed
replacement: null
tags: [archived, historical]
---
```

---

## Quality Checks (To Be Executed)

### Pre-Flight Checks
- [ ] All files have valid front-matter
- [ ] No duplicate filenames in target structure
- [ ] All internal links resolve correctly
- [ ] No secrets/PII in documents
- [ ] File paths use lowercase + hyphens only
- [ ] Max directory depth: 3 levels

### Post-Migration Checks
- [ ] 0 broken links
- [ ] 100% files with front-matter
- [ ] index.md exists and links to all sections
- [ ] All "See also" sections have 3-5 links
- [ ] Git history preserved (via git mv)

---

## Link Analysis (Preliminary)

### Documents with Outbound Links

**To be scanned:**
- README.md
- docs/DocumentationSummary.md
- docs/auth-flow.md
- docs/architecture.md
- docs/database_maintenance.md
- docs/deployment.md
- docs/troubleshooting.md

### Expected Link Updates

**Estimate:** 30-50 link fixups across all files

---

## Execution Plan (DRY_RUN=false)

### Phase 1: Create Structure
```bash
mkdir -p docs/{concepts,how-to,reference,operations,design,decisions,migration,troubleshooting,archived}
```

### Phase 2: Move & Rename Files
```bash
# Use git mv to preserve history
git mv docs/architecture.md docs/concepts/architecture-overview.md
git mv docs/database_maintenance.md docs/operations/database-maintenance.md
# ... (17 more moves)
```

### Phase 3: Split Files
- Split auth-flow.md into 3 files
- Split design-system.md into 4 files
- Split troubleshooting.md into 4 files

### Phase 4: Add Front-Matter
- Add front-matter to all 18 active files
- Generate appropriate tags and links

### Phase 5: Fix Links
- Update all internal references
- Fix cross-links in README.md
- Create index.md with navigation

### Phase 6: Create ADR
- Create ADR-0001 documenting this reorganization

### Phase 7: Git Commit
```bash
git add -A
git commit -m "feat(docs): modularize and reorganize per Docs-as-Code conventions

- Restructure into 8 categories (concepts, how-to, reference, operations, design, decisions, migration, troubleshooting)
- Add front-matter metadata to all active docs
- Split large files (auth-flow, design-system, troubleshooting)
- Archive completed analysis documents
- Fix all internal cross-references
- Create master index.md

See docs/decisions/ADR-0001-2025-11-07-modular-docs-structure.md for details."
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Broken links during migration | Medium | Medium | Comprehensive link scan + fixup script |
| Lost git history | Low | High | Use git mv for all moves |
| User confusion | Medium | Low | Create index.md, update README.md |
| Merge conflicts | Low | Medium | Single atomic commit |

---

## Next Steps

1. **Review this plan** - Approve or request changes
2. **Execute DRY_RUN=false** - Apply changes
3. **Validate results** - Run quality checks
4. **Create CHANGELOG-DOCS.md** - Document all changes
5. **Update external references** - If any exist

---

## Summary

**Total Actions:**
- 18 files to move/rename
- 3 files to split (→ 11 new files)
- 4 files to archive
- 1 index.md to create
- 1 ADR to create
- ~30-50 links to fix
- 18 front-matter blocks to add

**Expected Benefits:**
- ✅ Clear documentation taxonomy
- ✅ Easier navigation and discovery
- ✅ Consistent naming conventions
- ✅ Metadata for search and filtering
- ✅ Modular, maintainable structure
- ✅ Historical record preservation

**Estimated Time:** 45-60 minutes for full execution

---

*This is a DRY RUN plan. No files have been modified. Execute with DRY_RUN=false to apply changes.*
