# MD3 Error Pages & Admin Dashboard - Quick Reference

**Letzte Aktualisierung:** 19. Oktober 2025

---

## 🎨 Error Page Template

### Struktur
```html
<div class="md3-error-page">
  <div class="md3-error-container">
    <div class="md3-error-icon">
      <i class="bi bi-{icon-name}"></i>
    </div>
    <h1 class="md3-error-code md3-display-large">{code}</h1>
    <h2 class="md3-error-title md3-headline-medium">{title}</h2>
    <p class="md3-error-message md3-body-large">{message}</p>
    
    <div class="md3-error-suggestions">
      <p class="md3-title-medium">{heading}:</p>
      <ul class="md3-body-medium">
        <li>{suggestion}</li>
      </ul>
    </div>
    
    <div class="md3-error-actions">
      <a href="{url}" class="md3-button-filled">
        <i class="bi bi-{icon}"></i>
        <span>{text}</span>
      </a>
    </div>
  </div>
</div>
```

### Icons pro Fehlertyp
| Code | Icon | Beschreibung |
|------|------|--------------|
| 400 | `bi-exclamation-triangle` | Bad Request |
| 401 | `bi-lock` | Unauthorized |
| 403 | `bi-shield-x` | Forbidden |
| 404 | `bi-compass` | Not Found |
| 500 | `bi-exclamation-octagon` | Server Error |

---

## 🎛️ Admin Dashboard Components

### Hero Section
```html
<div class="md3-admin-hero">
  <div class="md3-admin-hero__content">
    <p class="md3-admin-hero__eyebrow md3-label-large">{eyebrow}</p>
    <h1 class="md3-admin-hero__title md3-display-small">{title}</h1>
    <p class="md3-admin-hero__subtitle md3-body-large">{subtitle}</p>
  </div>
</div>
```

### Control Card
```html
<div class="md3-admin-card md3-admin-card--control">
  <div class="md3-admin-card__header">
    <i class="bi bi-{icon} md3-admin-card__icon"></i>
    <div>
      <h2 class="md3-admin-card__title md3-title-large">{title}</h2>
      <p class="md3-admin-card__subtitle md3-body-medium">{subtitle}</p>
    </div>
  </div>
  <div class="md3-admin-card__body">
    {content}
  </div>
</div>
```

### MD3 Switch
```html
<button 
  type="button" 
  class="md3-switch" 
  role="switch"
  aria-checked="false"
  aria-label="{label}">
  <span class="md3-switch__track">
    <span class="md3-switch__thumb"></span>
  </span>
  <span class="md3-switch__label md3-body-large">{text}</span>
</button>
```

**JavaScript Toggle:**
```javascript
function updateToggleVisual(state) {
  toggleButton.setAttribute('aria-checked', state ? 'true' : 'false');
  toggleLabel.textContent = state ? 'Aktiviert' : 'Deaktiviert';
}
```

### Metric Card
```html
<div class="md3-metric-card" data-metric="{name}">
  <div class="md3-metric-card__icon">
    <i class="bi bi-{icon}"></i>
  </div>
  <div class="md3-metric-card__content">
    <p class="md3-metric-card__label md3-label-large">{label}</p>
    <h3 class="md3-metric-card__value md3-display-medium">{value}</h3>
    <p class="md3-metric-card__delta md3-body-small">{delta}</p>
  </div>
</div>
```

**JavaScript Update:**
```javascript
function hydrateMetricCard(metric, payload) {
  const valueEl = card.querySelector('.md3-metric-card__value');
  const detailEl = card.querySelector('.md3-metric-card__delta');
  valueEl.textContent = numberFormatter.format(summary.value);
  detailEl.textContent = summary.detail;
}
```

### Info Card
```html
<div class="md3-admin-card md3-admin-card--info">
  <div class="md3-admin-card__header">
    <i class="bi bi-info-circle md3-admin-card__icon"></i>
    <h2 class="md3-admin-card__title md3-title-large">{title}</h2>
  </div>
  <div class="md3-admin-card__body">
    <ul class="md3-admin-list md3-body-medium">
      <li>{item}</li>
    </ul>
  </div>
</div>
```

---

## 📐 CSS-Variablen Reference

### Spacing (4dp Grid)
```css
--md3-space-1: 0.25rem;  /* 4px */
--md3-space-2: 0.5rem;   /* 8px */
--md3-space-3: 0.75rem;  /* 12px */
--md3-space-4: 1rem;     /* 16px */
--md3-space-5: 1.25rem;  /* 20px */
--md3-space-6: 1.5rem;   /* 24px */
--md3-space-8: 2rem;     /* 32px */
--md3-space-10: 2.5rem;  /* 40px */
--md3-space-12: 3rem;    /* 48px */
```

### Typography Scale
```css
/* Display */
--md3-display-large: 3.562rem;   /* 57px */
--md3-display-medium: 2.812rem;  /* 45px */
--md3-display-small: 2.25rem;    /* 36px */

/* Headline */
--md3-headline-large: 2rem;      /* 32px */
--md3-headline-medium: 1.75rem;  /* 28px */
--md3-headline-small: 1.5rem;    /* 24px */

/* Title */
--md3-title-large: 1.375rem;     /* 22px */
--md3-title-medium: 1rem;        /* 16px */
--md3-title-small: 0.875rem;     /* 14px */

/* Body */
--md3-body-large: 1rem;          /* 16px */
--md3-body-medium: 0.875rem;     /* 14px */
--md3-body-small: 0.75rem;       /* 12px */

/* Label */
--md3-label-large: 0.875rem;     /* 14px */
--md3-label-medium: 0.75rem;     /* 12px */
--md3-label-small: 0.6875rem;    /* 11px */
```

### Colors
```css
/* Primary */
--md3-color-primary
--md3-color-on-primary
--md3-color-primary-container
--md3-color-on-primary-container

/* Surface */
--md3-color-surface
--md3-color-on-surface
--md3-color-on-surface-variant
--md3-color-surface-container
--md3-color-surface-container-low
--md3-color-surface-container-highest

/* Error */
--md3-color-error
--md3-color-on-error

/* Outline */
--md3-color-outline
--md3-color-outline-variant
```

### Elevation
```css
--md3-elevation-0: none;
--md3-elevation-1: /* Light shadow */
--md3-elevation-2: /* Medium shadow */
--md3-elevation-3: /* Dialog shadow */
```

### Border Radius
```css
--md3-radius-extra-small: 4px;
--md3-radius-small: 8px;
--md3-radius-medium: 12px;
--md3-radius-large: 16px;
--md3-radius-extra-large: 28px;
--md3-radius-full: 9999px;
```

### Motion
```css
--md3-motion-duration-short-4: 200ms;
--md3-motion-duration-medium-2: 300ms;
--md3-motion-easing-standard: cubic-bezier(0.2, 0, 0, 1);
--md3-motion-easing-emphasized: cubic-bezier(0.2, 0, 0, 1);
```

---

## 🎨 Button Components

### Filled Button (Highest Emphasis)
```html
<a href="{url}" class="md3-button-filled">
  <i class="bi bi-{icon}"></i>
  <span>{text}</span>
</a>
```

### Tonal Button (Medium Emphasis)
```html
<a href="{url}" class="md3-button-tonal">
  <i class="bi bi-{icon}"></i>
  <span>{text}</span>
</a>
```

### Outlined Button (Low Emphasis)
```html
<a href="{url}" class="md3-button-outlined">
  <i class="bi bi-{icon}"></i>
  <span>{text}</span>
</a>
```

### Text Button (Lowest Emphasis)
```html
<a href="{url}" class="md3-button-text">
  <i class="bi bi-{icon}"></i>
  <span>{text}</span>
</a>
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 599px) { ... }

/* Tablet */
@media (min-width: 600px) and (max-width: 899px) { ... }

/* Desktop */
@media (min-width: 900px) { ... }
```

---

## 🔧 Utility Classes

### Typography
- `md3-display-large`, `md3-display-medium`, `md3-display-small`
- `md3-headline-large`, `md3-headline-medium`, `md3-headline-small`
- `md3-title-large`, `md3-title-medium`, `md3-title-small`
- `md3-body-large`, `md3-body-medium`, `md3-body-small`
- `md3-label-large`, `md3-label-medium`, `md3-label-small`

### Layout
- `md3-error-page` - Error page container
- `md3-admin-page` - Admin page container
- `md3-admin-content` - Content wrapper (max-width: 1200px)

---

## 🚀 Best Practices

### 1. Spacing
✅ **Do:** Nutze das 4dp Grid System (`--md3-space-*`)  
❌ **Don't:** Hardcoded Pixel-Werte

### 2. Colors
✅ **Do:** Nutze CSS-Variablen (`var(--md3-color-primary)`)  
❌ **Don't:** Hardcoded Hex-Werte

### 3. Typography
✅ **Do:** Nutze Typography Classes (`md3-body-large`)  
❌ **Don't:** Inline Font-Sizes

### 4. Elevation
✅ **Do:** Nutze `--md3-elevation-*` für Shadows  
❌ **Don't:** Custom `box-shadow` Werte

### 5. Transitions
✅ **Do:** Nutze MD3 Motion Tokens  
❌ **Don't:** Random Transition-Durations

---

## 📚 Ressourcen

- **Material Design 3:** https://m3.material.io/
- **Bootstrap Icons:** https://icons.getbootstrap.com/
- **CSS Variables:** `/static/css/md3-tokens.css`
- **Components:** `/static/css/md3-components.css`

---

**Tipp:** Kopiere diese Snippets direkt in deine Templates für konsistentes MD3-Design!
