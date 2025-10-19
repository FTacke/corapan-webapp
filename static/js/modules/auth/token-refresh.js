/**
 * JWT Token Auto-Refresh Module
 * 
 * Automatically refreshes access tokens when they expire (401 responses).
 * This runs in the background without user interaction.
 * 
 * Usage:
 *   import { setupTokenRefresh } from './modules/auth/token-refresh.js';
 *   setupTokenRefresh();
 */

// Store original fetch FIRST before we override it
const originalFetch = window.fetch;

let isRefreshing = false;
let failedQueue = [];

/**
 * Process queued requests after token refresh
 */
function processQueue(error, token = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

/**
 * Refresh the access token using the refresh token
 * @returns {Promise<boolean>} True if refresh successful
 */
async function refreshAccessToken() {
  try {
    // Use ORIGINAL fetch to avoid recursion
    const response = await originalFetch('/auth/refresh', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    console.log('✅ Access token refreshed successfully');
    return true;
  } catch (error) {
    console.error('❌ Token refresh failed:', error);
    return false;
  }
}

/**
 * Enhanced fetch wrapper with automatic token refresh
 * @param {string} url - Request URL
 * @param {RequestInit} options - Fetch options
 * @returns {Promise<Response>}
 */
async function fetchWithTokenRefresh(url, options = {}) {
  // First attempt - use ORIGINAL fetch to avoid recursion
  const response = await originalFetch(url, {
    ...options,
    credentials: options.credentials || 'same-origin',
  });

  // If not 401, return response as-is
  if (response.status !== 401) {
    return response;
  }

  console.log('🔄 Received 401, attempting token refresh...');

  // If already refreshing, queue this request
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      failedQueue.push({
        resolve: () => {
          // Retry original request after refresh - use ORIGINAL fetch
          originalFetch(url, { ...options, credentials: options.credentials || 'same-origin' })
            .then(resolve)
            .catch(reject);
        },
        reject,
      });
    });
  }

  isRefreshing = true;

  try {
    const refreshSuccess = await refreshAccessToken();

    if (!refreshSuccess) {
      processQueue(new Error('Token refresh failed'), null);
      isRefreshing = false;
      
      // Redirect to login if refresh fails
      if (window.location.pathname !== '/') {
        console.log('🔐 Redirecting to login...');
        window.location.href = '/?message=session_expired';
      }
      return response; // Return original 401 response
    }

    // Refresh successful, process queued requests
    processQueue(null, true);
    isRefreshing = false;

    // Retry original request with new token - use ORIGINAL fetch
    return originalFetch(url, {
      ...options,
      credentials: options.credentials || 'same-origin',
    });
  } catch (error) {
    processQueue(error, null);
    isRefreshing = false;
    throw error;
  }
}

/**
 * Setup global fetch interceptor for automatic token refresh
 * Call this once when your app initializes
 */
export function setupTokenRefresh() {
  // Override global fetch with our wrapper
  window.fetch = function (...args) {
    const [url, options] = args;

    // Skip refresh logic for:
    // - The refresh endpoint itself (avoid infinite loop)
    // - Static assets
    // - External URLs
    if (
      typeof url === 'string' &&
      (url === '/auth/refresh' ||
        url.startsWith('/static/') ||
        url.startsWith('http://') ||
        url.startsWith('https://'))
    ) {
      return originalFetch.apply(this, args);
    }

    // Use our enhanced fetch for API calls
    return fetchWithTokenRefresh(url, options);
  };

  console.log('✅ JWT Token auto-refresh enabled');
}

/**
 * Get CSRF token from cookie (needed for protected endpoints)
 * @param {string} name - Cookie name
 * @returns {string|null}
 */
export function getCsrfToken(name = 'csrf_access_token') {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(';').shift();
  }
  return null;
}

/**
 * Add CSRF token to fetch headers if available
 * @param {HeadersInit} headers - Existing headers
 * @returns {HeadersInit}
 */
export function addCsrfHeader(headers = {}) {
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    return {
      ...headers,
      'X-CSRF-TOKEN': csrfToken,
    };
  }
  return headers;
}
