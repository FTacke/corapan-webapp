"""
TOKEN REFRESH INFINITE RECURSION FIX
=====================================

Problem:
--------
"InternalError: too much recursion" when loading Atlas page.
The token-refresh.js module caused an infinite loop.

Error Stack:
-----------
fetchWithTokenRefresh → fetch → fetchWithTokenRefresh → fetch → ...
(Repeats infinitely until stack overflow)

Root Cause:
-----------
The global fetch() override was calling itself recursively:

1. Line 64 (fetchWithTokenRefresh): Calls fetch(url, options)
2. Line 151 (setupTokenRefresh): Global fetch() calls fetchWithTokenRefresh()
3. Line 64 (fetchWithTokenRefresh): Calls fetch(url, options) again
4. INFINITE LOOP → Stack overflow

The problem was that we were storing originalFetch INSIDE setupTokenRefresh(),
but using window.fetch everywhere else, which pointed to the OVERRIDDEN version.

Solution:
---------
Store originalFetch at MODULE LEVEL (line 12) BEFORE any functions use it.
Use originalFetch consistently throughout instead of fetch():

1. Line 12: const originalFetch = window.fetch;  (BEFORE override)
2. Line 38: refreshAccessToken() uses originalFetch
3. Line 68: fetchWithTokenRefresh() uses originalFetch for initial request
4. Line 87: Queue retry uses originalFetch
5. Line 115: Final retry uses originalFetch
6. Line 138: setupTokenRefresh() still overrides window.fetch

Changes Made:
-------------
File: static/js/modules/auth/token-refresh.js

BEFORE:
```javascript
async function fetchWithTokenRefresh(url, options = {}) {
  const response = await fetch(url, options);  // ❌ Uses overridden fetch
  // ...
}

export function setupTokenRefresh() {
  const originalFetch = window.fetch;  // ⚠️  Stored too late
  window.fetch = function(...args) {
    // ...
    return fetchWithTokenRefresh(url, options);
  };
}
```

AFTER:
```javascript
// ✅ Store FIRST at module level
const originalFetch = window.fetch;

async function fetchWithTokenRefresh(url, options = {}) {
  const response = await originalFetch(url, options);  // ✅ Uses original
  // ...
  return originalFetch(url, options);  // ✅ All retries use original
}

export function setupTokenRefresh() {
  window.fetch = function(...args) {
    // ...
    return fetchWithTokenRefresh(url, options);
  };
}
```

Test Results:
-------------
✅ Atlas page loads without infinite recursion
✅ Token refresh works correctly on 401 responses
✅ No stack overflow errors
✅ All API calls succeed

Why This Works:
---------------
- originalFetch always points to the NATIVE browser fetch()
- fetchWithTokenRefresh uses NATIVE fetch for actual HTTP requests
- window.fetch override acts as a ROUTER, not executor
- No circular dependency: Router → Wrapper → Native (never back to Router)

Lessons Learned:
----------------
1. Always store native functions BEFORE overriding them
2. Store at MODULE level, not function scope
3. Use stored native function consistently, never the override
4. Test with network errors/401s to catch recursion early

Related Files:
--------------
- static/js/modules/auth/token-refresh.js (FIXED)
- static/js/main.js (imports setupTokenRefresh)
- LOKAL/Roadmaps/JWT_TOKEN_REFRESH_GUIDE.md (documentation)
"""
