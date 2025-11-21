/**
 * Login Sheet Controller
 * Handles interactions for the login sheet overlay.
 */

export function initLoginSheet() {
    const sheet = document.getElementById('login-sheet');
    if (!sheet || sheet.dataset.initialized) return;
    
    sheet.dataset.initialized = 'true';

    // Close button
    const closeBtn = sheet.querySelector('.md3-login-sheet__close-button');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            sheet.remove();
        });
    }

    // Backdrop click
    const backdrop = sheet.querySelector('.md3-login-backdrop');
    if (backdrop) {
        backdrop.addEventListener('click', () => {
            sheet.remove();
        });
    }
}

// Global listener for htmx:beforeSwap to handle redirect
document.body.addEventListener('htmx:beforeSwap', function(evt) {
    if (evt.detail.xhr.status === 204 && evt.detail.xhr.getResponseHeader('HX-Redirect')) {
        const sheet = document.getElementById('login-sheet');
        if (sheet) sheet.remove();
    }
});

// Initialize when the module is loaded (if the sheet is already in DOM)
// Also re-check after any HTMX swap (e.g. when opening from nav drawer)
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (document.getElementById('login-sheet')) {
        initLoginSheet();
    }
});

// Also try to init immediately in case it's already there
initLoginSheet();
