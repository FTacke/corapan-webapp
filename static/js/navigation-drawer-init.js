/* Navigation drawer initialization moved from template to external JS for CSP hardening */
(function() {
  try {
    if (new URLSearchParams(window.location.search).get('drawer_animate') === '1') {
      var drawer = document.getElementById('navigation-drawer-standard');
      if (drawer) {
        drawer.classList.add('pending-slide-in');
      }
    }
  } catch (e) { /* no-op */ }
})();
