/**
 * Authentication Handler
 * Handles 401 errors and auto-login triggers.
 */

export function initAuthHandler() {
  // 401 Handler: Open Login Sheet on Authentication Errors
  document.body.addEventListener("htmx:responseError", function(evt){
    if (evt.detail.xhr && evt.detail.xhr.status === 401) {
      // Fetch login sheet and inject into modal-root
      if (window.htmx) {
        htmx.ajax("GET", "/auth/login?sheet=1", {
          target: "#modal-root",
          swap: "innerHTML"
        });
      }
    }
  });

  // Open login sheet on page load if ?login=1 is present (from 401 redirect)
  const params = new URLSearchParams(location.search);
  if (params.get("login") === "1") {
    if (window.htmx) {
      htmx.ajax("GET", "/auth/login?sheet=1", {
        target: "#modal-root",
        swap: "innerHTML"
      });
      // Remove ?login=1 from URL (clean history)
      history.replaceState({}, "", location.pathname + location.hash);
    }
  }
}

export function checkAutoLogin() {
  const p = new URLSearchParams(location.search);
  if (p.get("login") === "1" && window.htmx) {
    const next = p.get("next") || "";
    const url = "/auth/login_sheet" + (next ? "?next=" + encodeURIComponent(next) : "");
    htmx.ajax('GET', url, { target: 'body', swap: 'beforeend' });
  }
}
