(() => {
  if (window.__APPBAR_TITLE_FIX__) {
    console.log('[Page Title] Already initialized, skipping');
    return;
  }
  window.__APPBAR_TITLE_FIX__ = true;
  console.log('[Page Title] Module initializing... (v2.0 - no scroll override)');

  // ------- helpers -------
  const norm = s => String(s || '').trim().replace(/\s+/g, ' ');
  const getEl = id => document.getElementById(id);

  // Titel aus bevorzugter Quelle ermitteln
  function extractTitleFromRoots({ head, body }) {
    // 1) <meta name="page-title" content="..."> im neuen HEAD
    if (head) {
      const meta = head.querySelector('meta[name="page-title"]');
      if (meta?.content) {
        console.log('[Page Title] Found via meta:', meta.content);
        return norm(meta.content);
      }
      const headTitle = head.querySelector('title');
      if (headTitle?.textContent) {
        const cleaned = norm(headTitle.textContent.replace(/\s+\|\s+.*/,''));
        console.log('[Page Title] Found via title:', cleaned);
        return cleaned;
      }
    }
    // 2) data-page-title an main/body im neuen BODY
    if (body) {
      const host = body.querySelector('main[data-page-title], body[data-page-title]');
      const v = host?.getAttribute?.('data-page-title');
      if (v) {
        console.log('[Page Title] Found via data-page-title:', v);
        return norm(v);
      }
      const h1 = (body.querySelector('main') || body).querySelector('h1');
      if (h1?.textContent) {
        console.log('[Page Title] Found via H1:', h1.textContent);
        return norm(h1.textContent);
      }
    }
    // 3) Fallback: aktuelles document.title
    const fallback = norm((document.title || '').replace(/\s+\|\s+.*/,''));
    console.log('[Page Title] Using fallback:', fallback);
    return fallback;
  }

  // Anwenden (OHNE Scroll-State zu überschreiben!)
  function applyTitle(txt) {
    const el = getEl('pageTitle');
    if (!el) {
      console.warn('[Page Title] Element #pageTitle not found!');
      return;
    }
    el.textContent = txt || '';
    console.log('[Page Title] Applied:', txt);
    // WICHTIG: Scroll-State wird von scroll-state.js verwaltet!
    // Wir überschreiben es NICHT mehr hier.
  }

  // -------- Turbo wiring --------
  let pendingTitle = null;

  // Wichtig: vor Render aus neuem HEAD/BODY lesen
  document.addEventListener('turbo:before-render', (e) => {
    console.log('[Page Title] 🔵 turbo:before-render');
    const head = e.detail?.newHead;
    const body = e.detail?.newBody;
    pendingTitle = extractTitleFromRoots({ head, body });
    console.log('[Page Title] Pending title:', pendingTitle);
  });

  // Nach Render anwenden
  document.addEventListener('turbo:render', () => {
    console.log('[Page Title] 🟢 turbo:render');
    applyTitle(pendingTitle ?? extractTitleFromRoots({ head: null, body: document }));
    pendingTitle = null;
    mountObserver(); // neuen <main> überwachen
  });

  // Frames explizit unterstützen
  document.addEventListener('turbo:frame-render', () => {
    console.log('[Page Title] 📦 turbo:frame-render');
    applyTitle(extractTitleFromRoots({ head: null, body: document }));
  });
  document.addEventListener('turbo:frame-load', () => {
    console.log('[Page Title] 📦 turbo:frame-load');
    applyTitle(extractTitleFromRoots({ head: null, body: document }));
  });

  // Snapshot: alten Text vor Caching neutralisieren
  document.addEventListener('turbo:before-cache', () => {
    console.log('[Page Title] 🔴 turbo:before-cache - clearing title');
    const el = getEl('pageTitle');
    if (el) el.textContent = ''; // verhindert „alter Titel kommt zurück"
  });

  // Klassische Pfade
  document.addEventListener('DOMContentLoaded', () => {
    console.log('[Page Title] 📄 DOMContentLoaded');
    applyTitle(extractTitleFromRoots({ head: null, body: document }));
    mountObserver();
  });
  
  window.addEventListener('pageshow', () => {
    console.log('[Page Title] 🔄 pageshow (bfcache)');
    applyTitle(extractTitleFromRoots({ head: null, body: document }));
  });

  // Änderungen im neuen <main> beobachten (Streams/Partial)
  let observer = null;
  function mountObserver() {
    console.log('[Page Title] 👁️ Mounting observer');
    const main = document.querySelector('main') || document.body;
    if (!main) return;
    if (observer) observer.disconnect();
    let tId = null;
    observer = new MutationObserver(() => {
      clearTimeout(tId);
      tId = setTimeout(() => {
        console.log('[Page Title] 🔄 Mutation detected');
        applyTitle(extractTitleFromRoots({ head: null, body: document }));
      }, 50);
    });
    observer.observe(main, { childList: true, subtree: true, characterData: true });
  }
  
  // Initial setup
  console.log('[Page Title] 🚀 Initial setup');
  applyTitle(extractTitleFromRoots({ head: null, body: document }));
  mountObserver();
  
  console.log('[Page Title] ✅ Module initialized');
})();
