/**
 * ================================================================================
 * DEPRECATED - DO NOT USE
 * ================================================================================
 * This module has been deprecated as part of the MD3 Goldstandard migration.
 * 
 * Login is now exclusively handled via the full-page login:
 *   /login?next=intended_url
 * 
 * All authentication flows redirect to the login page instead of opening a sheet.
 * This file is kept temporarily for reference but should be deleted after
 * verifying no code paths import it.
 * 
 * See: docs/md3-template/md3-structural-compliance.md section 6.2
 * ================================================================================
 */

/**
 * Login Sheet Controller (DEPRECATED)
 * Handles interactions for the login sheet overlay.
 */

export function initLoginSheet() {
    console.warn('[DEPRECATED] initLoginSheet() - Login sheet pattern removed. Use full-page login instead.');
    // Legacy initialization kept for backwards compatibility during transition
    const sheets = document.querySelectorAll('.md3-login-sheet, .md3-sheet');
    sheets.forEach((sheet) => {
        if (!sheet || sheet.dataset.initialized) return;
        // Only operate on visible sheets
        if (sheet.hasAttribute('hidden')) return;

        sheet.dataset.initialized = 'true';

        // Close button (support both selectors)
        const closeBtn = sheet.querySelector('.md3-sheet__close-button, .md3-login-sheet__close-button');
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                // remove the sheet element from DOM
                sheet.remove();
            });
        }

        // Backdrop click (support legacy and new)
        const backdrop = sheet.querySelector('.md3-sheet__backdrop, .md3-login-backdrop');
        if (backdrop) {
            backdrop.addEventListener('click', (e) => {
                e.preventDefault();
                sheet.remove();
            });
        }

        // Escape key closes the sheet
        sheet.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') sheet.remove();
        });

        // Focus trap: move focus to first interactive element inside sheet when shown
        const focusable = sheet.querySelectorAll('input, button, a, textarea, select');
        if (focusable && focusable.length) focusable[0].focus();
    });
}

// NOTE: Global hooks removed - no longer needed with full-page login
