# MD3 Structural Compliance Documentation — CO.RA.PAN Webapp

> Version 1.0 • Created: 2025-11-25

This document defines canonical HTML structures for MD3 components (Pages, Cards, Dialogs, Sheets, Forms) and provides enforceable rules for linting and migration.

---

## 1. Canonical Structures

### 1.1 Card Structure

**Order**: `header` → `content` → `actions`

```html
<article class="md3-card md3-card--outlined">
  <header class="md3-card__header">
    <h2 class="md3-title-large md3-card__title">Title</h2>
  </header>
  <div class="md3-card__content md3-stack--section">
    <!-- content, form fields, paragraphs -->
  </div>
  <footer class="md3-card__footer md3-card__actions">
    <button class="md3-button md3-button--text">Cancel</button>
    <button class="md3-button md3-button--filled">Save</button>
  </footer>
</article>
```

**Rules**:
- `md3-card__content` MUST exist
- `md3-card__actions`/`md3-card__footer` MUST come AFTER `md3-card__content`
- Header contains only: title, eyebrow, short intro text

### 1.2 Dialog Structure

**Order**: `<dialog>` → `__container` → `__surface` → `__header` → `__content` → `__actions`

```html
<dialog class="md3-dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
  <div class="md3-dialog__container">
    <div class="md3-dialog__surface">
      <header class="md3-dialog__header">
        <h2 id="dialog-title" class="md3-title-large md3-dialog__title">Title</h2>
      </header>
      <div class="md3-dialog__content md3-stack--dialog">
        <!-- body content, form -->
      </div>
      <div class="md3-dialog__actions">
        <button class="md3-button md3-button--text">Cancel</button>
        <button class="md3-button md3-button--filled">Confirm</button>
      </div>
    </div>
  </div>
</dialog>
```

**Rules**:
- MUST have `md3-dialog__surface`
- MUST have `md3-dialog__content`
- MUST have `md3-dialog__actions`
- MUST have `md3-dialog__title` (h2) with an ID
- MUST have `aria-modal="true"`
- MUST have `aria-labelledby` or `aria-label`

### 1.3 Bottom Sheet Structure

**Order**: `md3-sheet` → `__backdrop` → `__surface` → `__header` → `__content` → `__actions`

```html
<div class="md3-sheet" role="dialog" aria-modal="true" aria-label="Sheet title">
  <div class="md3-sheet__backdrop"></div>
  <div class="md3-sheet__surface md3-sheet__container">
    <header class="md3-sheet__header">
      <h2 class="md3-title-large md3-sheet__title">Title</h2>
      <button class="md3-sheet__close-button">×</button>
    </header>
    <div class="md3-sheet__content md3-stack--dialog">
      <!-- fields -->
    </div>
    <div class="md3-sheet__actions">
      <button class="md3-button md3-button--filled">Submit</button>
    </div>
  </div>
</div>
```

### 1.4 Page Structure

**Order**: `md3-page` → `__header` → `__main` → `__section`

```html
<div class="md3-page">
  <header class="md3-page__header md3-stack--section">
    <div class="md3-page__eyebrow md3-body-small">Category</div>
    <h1 class="md3-headline-large">Page Title</h1>
    <p class="md3-body-medium">Short intro</p>
  </header>
  <main class="md3-page__main">
    <section class="md3-page__section md3-stack--page">
      <!-- content -->
    </section>
  </main>
</div>
```

### 1.5 Hero Structure (Goldstandard)

**Canonical Hero-Card mit Icon**:

```html
<header class="md3-page__header">
  <div class="md3-hero md3-hero--card md3-hero__container">
    <div class="md3-hero__icon" aria-hidden="true">
      <span class="material-symbols-rounded">icon_name</span>
    </div>
    <div class="md3-hero__content">
      <p class="md3-body-small md3-hero__eyebrow">Category / Context</p>
      <h1 class="md3-headline-medium md3-hero__title">Page Title</h1>
    </div>
  </div>
</header>
```

**Rules**:
- Hero MUST be inside `md3-page__header`
- Hero container has `md3-hero md3-hero--card md3-hero__container`
- Icon uses `md3-hero__icon` with `aria-hidden="true"`
- Content uses `md3-hero__content` with eyebrow and title
- Title is H1 with `md3-headline-medium md3-hero__title`
- Eyebrow is optional, uses `md3-body-small md3-hero__eyebrow`

**Reference Implementation**: `templates/pages/impressum.html`

**Pages requiring Hero**:
- Text pages (impressum, proyecto, datenschutz)
- Auth pages (account_profile, account_password, admin_users)
- Editor overview, atlas pages
- Search pages (advanced.html - Hero only, DataTables preserved)

**Hero CSS**: `static/css/md3/components/hero.css`

---

## 2. Typography Rules

| Context | Element | Class |
|---------|---------|-------|
| Page title | H1 | `md3-headline-large` |
| Card/Dialog/Section title | H2 | `md3-title-large` |
| Subsection | H3 | `md3-title-medium` |
| Body text | p | `md3-body-medium` |
| Small text | p | `md3-body-small` |
| Labels | label | `md3-label-large` |

**Rule**: Headings must be in order (H1 > H2 > H3). No skipping levels.

---

## 3. Form & Input Rules

### 3.1 Textfield Pattern (Goldstandard)

**Canonical MD3 Outlined Textfield**:

```html
<div class="md3-outlined-textfield md3-outlined-textfield--block">
  <input 
    type="text" 
    class="md3-outlined-textfield__input" 
    id="field-id" 
    name="field"
    autocomplete="appropriate-value"
    required
    aria-label="Accessible Label">
  <label class="md3-outlined-textfield__label" for="field-id">Visible Label</label>
  <span class="md3-outlined-textfield__outline">
    <span class="md3-outlined-textfield__outline-start"></span>
    <span class="md3-outlined-textfield__outline-notch"></span>
    <span class="md3-outlined-textfield__outline-end"></span>
  </span>
</div>
```

**Rules**:
- Wrapper: `div.md3-outlined-textfield.md3-outlined-textfield--block`
- Input: `input.md3-outlined-textfield__input` with `id`, `name`, `autocomplete`
- Label: `label.md3-outlined-textfield__label` with `for` pointing to input ID
- Outline: span wrapper with 3 outline parts (start, notch, end)
- Order: Input → Label → Outline (CSS requires this order)

**DO NOT USE**:
- `<label>` wrapping `<input>` (breaks MD3 outline animation)
- Inline `placeholder` instead of label (accessibility issue)
- Missing outline structure (breaks visual styling)

**Reference Implementation**: `templates/auth/login.html`

### 3.2 Form Rules

- Inputs MUST be inside `.md3-form` or `<form class="md3-auth-form">`
- Submit buttons MUST be inside the `<form>` OR have `form="form-id"` attribute
- Use `.md3-form__row` and `.md3-form__field` for layout

### 3.3 Button Types

| Type | Class | Usage |
|------|-------|-------|
| Primary | `md3-button--filled` | Main action |
| Secondary | `md3-button--outlined` | Alternative action |
| Text | `md3-button--text` | Cancel, dismiss |
| Danger | `md3-button--filled md3-button--danger` | Destructive action |

---

## 4. Spacing Tokens

Use CSS custom properties from `static/css/md3/tokens.css`:

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 4px | Tight spacing |
| `--space-2` | 8px | Small gap |
| `--space-3` | 12px | Icon spacing |
| `--space-4` | 16px | Card padding |
| `--space-6` | 24px | Dialog padding |
| `--space-8` | 32px | Section gap |

**Stack helpers**: `md3-stack--page`, `md3-stack--section`, `md3-stack--dialog`

---

## 5. ARIA & Accessibility

| Component | Required Attributes |
|-----------|---------------------|
| Dialog | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` |
| Sheet | `role="dialog"`, `aria-modal="true"`, `aria-label` |
| Alert | `role="alert"`, `aria-live="assertive"` |
| Menu item | `role="menuitem"` |
| Separator | `role="separator"` |

---

## 6. Forbidden Patterns

### 6.1 Legacy Classes (ERROR)

- `class="card"` without `md3-card`
- `class="card-outlined"` → use `md3-card--outlined`
- `md3-button--contained` → use `md3-button--filled`
- `md3-login-sheet` → use `md3-sheet` (if sheet needed)

### 6.2 Login Sheet (DEPRECATED - REMOVED)

**Status**: Login-Sheet pattern is completely removed from the codebase.

**Old Pattern** (DO NOT USE):
- `_login_sheet.html` partial
- `/auth/login_sheet` endpoint
- HTMX-based sheet injection for 401 handling
- `login-sheet.js` controller

**New Pattern** (REQUIRED):
- Full-page login at `/login` with `?next=` parameter
- 401 responses redirect to `/login?next=intended_url`
- No sheet/overlay for authentication
- Simpler, more accessible, better UX on mobile

### 6.3 Legacy Tokens (ERROR)

- `--md3-*` tokens → use `--md-sys-*` or `--space-*`

### 6.4 Inline Styles (WARNING)

- `style="margin: 12px"` → use `--space-*` tokens
- `style="padding: 16px"` → use `--space-4`

---

## 7. Lint Rule IDs

| ID | Severity | Description |
|----|----------|-------------|
| `MD3-DIALOG-001` | ERROR | Dialog missing `md3-dialog__surface` |
| `MD3-DIALOG-002` | ERROR | Dialog missing `md3-dialog__content` |
| `MD3-DIALOG-003` | ERROR | Dialog missing `md3-dialog__actions` |
| `MD3-DIALOG-004` | ERROR | Dialog missing `md3-dialog__title` |
| `MD3-DIALOG-005` | ERROR | Dialog missing `aria-modal="true"` |
| `MD3-DIALOG-006` | ERROR | Dialog missing `aria-labelledby` or `aria-label` |
| `MD3-CARD-001` | ERROR | Card missing `md3-card__content` |
| `MD3-CARD-002` | ERROR | Card actions before content |
| `MD3-FORM-001` | ERROR | Submit button outside form without `form` attr |
| `MD3-LEGACY-001` | ERROR | Legacy `class="card"` usage |
| `MD3-LEGACY-002` | ERROR | Legacy `--md3-*` token usage |
| `MD3-LEGACY-003` | ERROR | Legacy `md3-button--contained` |
| `MD3-SPACING-001` | WARN | Inline pixel spacing |
| `MD3-TEXTFIELD-001` | WARN | Non-standard textfield structure |
| `MD3-HEADER-001` | WARN | Complex content in header |
| `MD3-INPUT-001` | INFO | Input field inventory (for audit) |

---

## 8. Exceptions

### 8.1 DataTables (search/advanced)

Files under `templates/search/advanced*` use legacy DataTables layout.

- **No auto-fixes** applied
- **No build failures** for MD3 violations
- Violations logged as `IGNORED_MD3_IN_DATATABLES` (info only)

---

## 9. Quick Checklist

Use this checklist for every page, card, dialog, or form:

### Structure
- [ ] Card has `md3-card__content` 
- [ ] Card actions come AFTER content
- [ ] Dialog has `__surface`, `__content`, `__actions`
- [ ] Dialog has title with ID

### Accessibility
- [ ] Dialog has `aria-modal="true"`
- [ ] Dialog has `aria-labelledby` pointing to title ID
- [ ] Alerts have `role="alert"` and `aria-live`

### Forms
- [ ] Submit button inside `<form>` OR has `form="id"`
- [ ] Inputs use `md3-outlined-textfield` pattern
- [ ] Form has `.md3-form` or `.md3-auth-form`

### Typography
- [ ] Page: H1 with `md3-headline-large`
- [ ] Card/Dialog: H2 with `md3-title-large`
- [ ] Subsection: H3 with `md3-title-medium`

### Tokens
- [ ] No `--md3-*` tokens (use `--md-sys-*`)
- [ ] No inline pixel values (use `--space-*`)
- [ ] No legacy class names

### Legacy Classes
- [ ] No `class="card"` (use `md3-card`)
- [ ] No `md3-button--contained` (use `--filled`)
- [ ] No `md3-login-sheet` (use `md3-sheet`)

---

## 10. Running the Linter

```bash
# Full scan with JSON report
python scripts/md3-lint.py --json-out reports/md3-lint.json

# Focus on auth templates
python scripts/md3-lint.py --focus templates/auth

# Allow warnings (CI mode)
python scripts/md3-lint.py --exit-zero
```

---

## 11. Auto-Fix (Conservative)

```bash
# Dry-run to see proposed fixes
python scripts/md3-autofix.py --dry-run

# Apply fixes to auth templates only
python scripts/md3-autofix.py --apply --scope templates/auth
```

**Safe auto-fixes**:
- Add `aria-modal="true"` to dialogs
- Add `aria-labelledby` when title ID exists
- Add `form="id"` to orphan submit buttons (single-form files)

**NOT auto-fixed** (manual review required):
- Reordering card/dialog blocks
- Changing class names
- Complex structural changes

---

*Document maintained by: CO.RA.PAN Development Team*
*Reference: `scripts/md3-lint.py`, `scripts/md3-autofix.py`*
