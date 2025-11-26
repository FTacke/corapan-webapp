# MD3 Goldstandard - Documentation Index

**Version:** 1.0  
**Date:** 2025-11-26

This documentation defines the canonical patterns for MD3 components in the CO.RA.PAN webapp.

---

## Documentation Files

| File | Description |
|------|-------------|
| [00-audit-report.md](./00-audit-report.md) | Initial component audit and findings |
| [01-buttons.md](./01-buttons.md) | Button variants and action zones |
| [02-tables.md](./02-tables.md) | Tables, lists, and empty states |
| [03-feedback.md](./03-feedback.md) | Snackbar, loading, and feedback components |
| [04-badges.md](./04-badges.md) | Role and status badges with icons |
| [05-responsiveness.md](./05-responsiveness.md) | Mobile breakpoints and responsive rules |

---

## Quick Reference

### Button Variants

```html
<!-- Primary Action -->
<button class="md3-button md3-button--filled">Primary</button>

<!-- Secondary Action -->
<button class="md3-button md3-button--outlined">Secondary</button>

<!-- Tertiary Action -->
<button class="md3-button md3-button--text">Tertiary</button>

<!-- Danger Action -->
<button class="md3-button md3-button--filled md3-button--danger">Delete</button>
```

### Action Zones

```html
<!-- Form Actions -->
<div class="md3-actions">
  <button class="md3-button md3-button--text">Cancel</button>
  <button class="md3-button md3-button--filled">Save</button>
</div>

<!-- Dialog Actions -->
<div class="md3-dialog__actions">
  <button class="md3-button md3-button--text">Cancel</button>
  <button class="md3-button md3-button--filled">Confirm</button>
</div>
```

### Tables

```html
<div class="md3-table-container">
  <table class="md3-table">
    <thead>
      <tr><th>Column</th></tr>
    </thead>
    <tbody>
      <tr><td>Data</td></tr>
    </tbody>
  </table>
</div>
```

### Empty State

```html
<div class="md3-empty-state">
  <span class="material-symbols-rounded md3-empty-state__icon">search_off</span>
  <p class="md3-empty-state__title">No results</p>
  <p class="md3-empty-state__text">Try different search terms.</p>
</div>
```

### Badges

```html
<!-- Role Badge -->
<span class="md3-badge md3-badge--role-admin">
  <span class="material-symbols-rounded md3-badge__icon">verified_user</span>
  Admin
</span>

<!-- Status Badge -->
<span class="md3-badge md3-badge--status-active">
  <span class="material-symbols-rounded md3-badge__icon">check_circle</span>
  Active
</span>
```

### Snackbar (JavaScript)

```javascript
// Via global helper
window.MD3Snackbar.showSnackbar('Message', 'success');

// Or import module
import { showSnackbar } from './modules/core/snackbar.js';
showSnackbar('Message', 'error');
```

### Loading States

```html
<!-- Linear Progress -->
<div class="md3-linear-progress"></div>

<!-- Button Loading -->
<button class="md3-button md3-button--filled is-loading" disabled>
  <span class="md3-button__spinner"></span>
  Loading...
</button>
```

---

## CSS Files Reference

| Component | CSS File |
|-----------|----------|
| Buttons | `static/css/md3/components/buttons.css` |
| Tables | `static/css/md3/layout.css` |
| Badges | `static/css/md3/components/top-app-bar.css` |
| Snackbar | `static/css/md3/components/snackbar.css` |
| Progress | `static/css/md3/components/progress.css` |
| Alerts | `static/css/md3/components/alerts.css` |
| Dialog | `static/css/md3/components/dialog.css` |
| Actions | `static/css/md3/components/auth.css` |

---

## Changelog

### 2025-11-26 - v1.0
- Initial goldstandard documentation
- Extended `.md3-table` with hover/selected/disabled states
- Added `.md3-empty-state` canonical CSS
- Extended badge system with status variants
- Added icon button (`.md3-button--icon`)
- Added responsive rules for actions and tables
- Extended snackbar with warning variant
- Added button loading states and skeleton loaders
