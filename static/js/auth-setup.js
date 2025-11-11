/**
 * CO.RA.PAN Authentication Setup
 * 
 * Ensures cookies are sent with all fetch requests and handles
 * authentication-specific behavior.
 * 
 * This script MUST load before other app scripts.
 */

console.log('[Auth Setup] Initializing...');

// =============================================================================
// 1. Intercept all fetch() calls to include credentials
// =============================================================================

const originalFetch = window.fetch;

window.fetch = function(resource, config = {}) {
  // Ensure credentials are sent with same-origin requests
  // This is CRITICAL for cookies to be included in requests
  if (!config.credentials) {
    config.credentials = 'same-origin';
  }
  
  // Log auth-related requests
  if (typeof resource === 'string' && resource.includes('/auth/')) {
    console.log('[Auth Fetch]', resource, 'with credentials:', config.credentials);
  }
  
  return originalFetch(resource, config);
};

console.log('[Auth Setup] ✅ Fetch interceptor installed');

// =============================================================================
// 2. Disable Turbo for authentication-related forms
// =============================================================================

// Disable Turbo for login form to ensure clean page reload with cookies
document.addEventListener('turbo:before-fetch-request', (event) => {
  const url = event.detail.fetchOptions.url || '';
  
  if (url.includes('/auth/login')) {
    // Force full page reload for login (don't use Turbo cache)
    event.detail.fetchOptions.headers = event.detail.fetchOptions.headers || {};
    event.detail.fetchOptions.headers['Turbo-Force-Full-Page-Load'] = 'true';
    console.log('[Auth] Disabling Turbo caching for login');
  }
});

// Also disable Turbo for form submissions on /auth/login
document.addEventListener('turbo:submit-start', (event) => {
  const form = event.detail.formSubmission.form;
  if (form && form.action && form.action.includes('/auth/login')) {
    form.setAttribute('data-turbo', 'false');
    console.log('[Auth] Turbo disabled for login form');
  }
});

// Alternative: Mark login form with data-turbo="false" on page load
document.addEventListener('turbo:load', () => {
  const loginForms = document.querySelectorAll('form[action*="/auth/login"]');
  loginForms.forEach(form => {
    form.setAttribute('data-turbo', 'false');
    console.log('[Auth] Marked login form with data-turbo=false');
  });
});

console.log('[Auth Setup] ✅ Turbo authentication handlers installed');

// =============================================================================
// 3. Helper: Get CSRF token for mutating requests
// =============================================================================

window.getCSRFToken = function(tokenName = 'csrf_access_token') {
  // Extract CSRF token from cookie
  const name = tokenName + '=';
  const decodedCookie = decodeURIComponent(document.cookie);
  const cookieArray = decodedCookie.split(';');
  
  for (let cookie of cookieArray) {
    cookie = cookie.trim();
    if (cookie.indexOf(name) === 0) {
      return cookie.substring(name.length);
    }
  }
  
  return null;
};

console.log('[Auth Setup] ✅ CSRF token helper available');

// =============================================================================
// 4. Verify authentication on page load
// =============================================================================

async function verifyAuth() {
  try {
    const response = await fetch('/auth/session', {
      credentials: 'same-origin'
    });
    const data = await response.json();
    
    if (data.authenticated) {
      console.log(`[Auth] ✅ Authenticated as: ${data.user}`);
      document.body.classList.add('authenticated');
      document.body.classList.remove('not-authenticated');
    } else {
      console.log('[Auth] ℹ️  Not authenticated');
      document.body.classList.add('not-authenticated');
      document.body.classList.remove('authenticated');
    }
    
    return data;
  } catch (error) {
    console.warn('[Auth] Error checking session:', error);
    return null;
  }
}

// Run on initial page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', verifyAuth);
} else {
  verifyAuth();
}

// Re-verify after each Turbo navigation
document.addEventListener('turbo:load', verifyAuth);

console.log('[Auth Setup] ✅ Session verification installed');

// =============================================================================
// Export for use in other scripts
// =============================================================================

window.authSetup = {
  getCSRFToken: window.getCSRFToken,
  verifyAuth: verifyAuth
};

console.log('[Auth Setup] ✅ Complete - all auth features enabled');
