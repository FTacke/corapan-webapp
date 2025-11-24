/**
 * Login Sheet Controller
 * Handles interactions for the login sheet overlay.
 */

export function initLoginSheet() {
    // Initialize all visible sheets that have not been initialized yet.
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

// Global listener for htmx:beforeSwap to handle redirect
document.body.addEventListener('htmx:beforeSwap', function(evt) {
    if (!evt.detail || !evt.detail.xhr) return;
    // If server returned 204 with HX-Redirect we can remove any active sheet
    if (evt.detail.xhr.status === 204 && evt.detail.xhr.getResponseHeader('HX-Redirect')) {
        const sheet = document.querySelector('.md3-login-sheet, .md3-sheet');
        if (sheet) sheet.remove();
    }
});

// Initialize when the module is loaded (if the sheet is already in DOM)
// Also re-check after any HTMX swap (e.g. when opening from nav drawer)
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // If a sheet was swapped/inserted, initialize it.
    if (document.querySelector('.md3-login-sheet, .md3-sheet')) {
        initLoginSheet();
    }
});

// Also try to init immediately in case it's already there
initLoginSheet();
