/**
 * CO.RA.PAN Main Application Entry Point
 * Handles Turbo Drive lifecycle and page-specific asset loading
 */

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Register Turbo event listener
 */
function onTurbo(event, fn) {
  document.addEventListener(event, fn);
}

/**
 * Ensure stylesheet is loaded (idempotent)
 */
function ensureStyles(href) {
  if (!document.querySelector(`link[rel="stylesheet"][href="${href}"]`)) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.setAttribute('data-turbo-track', 'dynamic');
    document.head.appendChild(link);
  }
}

/**
 * Ensure script is loaded (async, idempotent)
 */
async function ensureScript(src) {
  if (document.querySelector(`script[src="${src}"]`)) return;
  
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.defer = true;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// =============================================================================
// Atlas Module - Lazy Loading & Lifecycle
// =============================================================================

let atlasMap = null;
let atlasModule = null;

/**
 * Initialize Atlas page with lazy-loaded dependencies
 */
async function initAtlas() {
  const mapEl = document.getElementById('atlas-map');
  if (!mapEl) return;

  console.log('[Atlas] Initializing...');

  try {
    // 1) Load external dependencies
    ensureStyles('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css');
    ensureStyles('/static/css/md3/components/atlas.css');
    await ensureScript('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js');

    // 2) Prevent double initialization
    if (atlasMap) {
      console.log('[Atlas] Map already exists, removing...');
      try {
        atlasMap.remove();
      } catch (e) {
        console.warn('[Atlas] Error removing map:', e);
      }
      atlasMap = null;
    }

    // 3) Wait for Leaflet to be available
    if (!window.L) {
      console.error('[Atlas] Leaflet not loaded');
      return;
    }

    // 4) Dynamically import Atlas module
    if (!atlasModule) {
      atlasModule = await import('/static/js/modules/atlas/index.js');
      console.log('[Atlas] Module loaded');
    }

    // 5) Initialize Atlas (module should export init function)
    if (atlasModule.init) {
      atlasMap = atlasModule.init();
      console.log('[Atlas] Initialized successfully');
    } else {
      console.warn('[Atlas] No init function exported from module');
    }

  } catch (error) {
    console.error('[Atlas] Initialization failed:', error);
  }
}

/**
 * Cleanup Atlas before Turbo caches the page
 */
function teardownAtlas() {
  if (atlasMap) {
    console.log('[Atlas] Tearing down...');
    try {
      atlasMap.remove();
    } catch (e) {
      console.warn('[Atlas] Error during teardown:', e);
    }
    atlasMap = null;
  }
}

// =============================================================================
// Turbo Drive Lifecycle Hooks
// =============================================================================

onTurbo('turbo:load', () => {
  console.log('[Turbo] Page loaded');
  initAtlas();
});

onTurbo('turbo:before-cache', () => {
  console.log('[Turbo] Before cache');
  teardownAtlas();
});

onTurbo('turbo:before-render', () => {
  console.log('[Turbo] Before render');
});

// =============================================================================
// Initial Load
// =============================================================================

console.log('[App] Initialized');
