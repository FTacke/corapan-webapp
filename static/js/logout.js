/*
 * Logout helper
 * - Intercepts clicks on elements with data-logout="fetch" and performs
 *   a fetch request to the logout endpoint, then refreshes the UI using
 *   window.location.reload()
 * - Keeps fallback via href for no-JS environments
 */

(function () {
  if (typeof window === 'undefined') return;

  function performLogout(el) {
    const url = el.dataset.logoutUrl || el.getAttribute('href') || '/auth/logout';
    const method = (el.dataset.logoutMethod || 'POST').toUpperCase();

    // Try to obtain a CSRF token helper if available
    const token = (window.authSetup && window.authSetup.getCSRFToken) ? window.authSetup.getCSRFToken() : null;

    const opts = {
      method: method,
      credentials: 'same-origin',
      headers: {},
    };

    if (token && method !== 'GET') {
      opts.headers['X-CSRF-Token'] = token;
    }

    return fetch(url, opts)
      .then((res) => {
        // If server indicates redirect, follow it in JS by reloading
        if (res.redirected) {
          window.location.href = res.url;
          return;
        }

        // Always attempt to reload so client UI state (g, session) is cleared
        try {
          window.location.reload();
        } catch (e) {
          // fallback to navigate to the root
          window.location.href = '/';
        }
      })
      .catch((err) => {
        console.error('[Logout] Failed', err);
        // fallback to non-JS behaviour
        window.location.href = url;
      });
  }

  function onClick(e) {
    const el = e.target.closest && e.target.closest('[data-logout="fetch"], .md3-user-menu__item--logout');
    if (!el) return;

    // If it's a GET-only logout anchor, prefer to POST via fetch for safety, but respect data attributes
    e.preventDefault();
    performLogout(el);
  }

  document.addEventListener('click', onClick, { passive: false });

  // Find initial elements and make them accessible for assistive tech
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-logout="fetch"]').forEach(function (el) {
      el.setAttribute('role', el.getAttribute('role') || 'button');
      el.setAttribute('tabindex', el.getAttribute('tabindex') || '0');
    });
  });

  // Expose helper for tests
  window.CORAPAN = window.CORAPAN || {};
  window.CORAPAN.logout = performLogout;

})();
