# Design System Guidelines

## Typography
- Primary display font: 'Arial Narrow', 'Helvetica Neue Condensed', Arial, sans-serif.
- Body font: Arial, sans-serif with 16px base size; clamp scaling on hero headings.
- Monospace usage remains JetBrains Mono / Fira Mono for code fragments.

## Color Palette
- Background (--color-bg): #c7d5d8 for the overall canvas.
- Surface (--color-surface): #eaf3f5 for cards and interactive shells.
- Secondary surface (--color-surface-alt): #d7e6eb for subtle elevation.
- Border / accent (--color-border / --color-accent): #2f5f73 for outlines, primary buttons and iconography.
- Accent soft (--color-accent-soft): #a9c9d0 for navigation chips and hover states.
- Text (--color-text): #244652, muted text (--color-text-muted): #3a6070.
- Support: success (#2f5f73), warning (#efede1), error (#913535).

## Layout Principles
- Max content width 1200px; spacing tokens (--space-*) define gutters and vertical rhythm.
- Cards and filters use 1px solid #2f5f73 borders, soft inner shadows (0 0 12px rgba(36,70,82,0.05)).
- Mobile navigation collapses into a drawer; hero and project sections rely on responsive grids.

## Component Notes
- Feature cards and project sections share `.project-card` / `.project-meta-card` styling for consistency.
- Buttons inherit `.btn` base: border + background from surface, hover lifts via box-shadow; `.btn-primary` fills with #2f5f73, hover darkens to #244652.
- Login sheet keeps blurred backdrop; `.project-hero` reuses surface tokens for prominent summaries.

## Accessibility
- Palette tuned for WCAG AA contrast on background #c7d5d8; primary text (#244652) has >4.5:1.
- HTML entities replace non-ASCII glyphs in templates to avoid encoding regressions.
- Maintain sr-only helpers and focusable controls for all interactive elements.
