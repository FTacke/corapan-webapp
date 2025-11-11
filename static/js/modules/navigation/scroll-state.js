// ============================================
// Scroll State Detection
// ============================================
// Setzt data-scrolled="true" am <body> wenn > 8px gescrollt
// Für Elevation-Änderungen der Top App Bar

(() => {
  let lastScrollY = 0;
  const threshold = 8; // Mindest-Scroll-Distanz in px

  function updateScrollState() {
    const currentScrollY = window.scrollY || window.pageYOffset || 0;
    const body = document.body;
    
    // Nur aktualisieren wenn Schwelle überschritten/unterschritten
    if ((currentScrollY > threshold) !== (lastScrollY > threshold)) {
      body.dataset.scrolled = currentScrollY > threshold ? 'true' : 'false';
      
      // Debug-Logging aktiv
      console.log('[Scroll State] Changed to:', body.dataset.scrolled, '(scrollY:', currentScrollY, ')');
    }
    
    lastScrollY = currentScrollY;
  }

  // Guard: Scroll-Listener nur einmal registrieren
  if (!window.__scrollStateInit) {
    window.addEventListener('scroll', updateScrollState, { passive: true });
    window.__scrollStateInit = true;
    console.log('[Scroll State] Scroll listener registered');
  }

  // Set initial state (läuft bei jedem Turbo-Render)
  updateScrollState();
  
  // Re-apply scroll state after Turbo navigation
  document.addEventListener('turbo:render', () => {
    console.log('[Scroll State] 🟢 turbo:render - re-applying scroll state');
    updateScrollState();
  });
})();
