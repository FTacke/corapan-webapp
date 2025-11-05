// ============================================
// Swipe Gestures für Modal Drawer
// ============================================
// Wisch-Öffnen vom linken Rand (≤20px Touch-Zone)
// Wisch-Schließen auf Scrim oder im Drawer nach links

export class SwipeGestureHandler {
  constructor(drawer, mediaQuery) {
    this.drawer = drawer;
    this.mediaQuery = mediaQuery;
    this.isSwipeActive = false;
    this.startX = null;
    this.startY = null;
    this.currentX = null;
    this.edgeZone = 20; // px vom linken Rand
    this.threshold = 40; // Mindest-Swipe-Distanz
    
    this.init();
  }
  
  init() {
    // Touch Start: Detect edge swipe
    document.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
    
    // Touch Move: Track swipe
    document.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
    
    // Touch End: Complete swipe
    document.addEventListener('touchend', () => this.handleTouchEnd());
    
    // Touch Cancel: Reset
    document.addEventListener('touchcancel', () => this.reset());
  }
  
  handleTouchStart(e) {
    // Nur auf Compact/Medium aktiv
    if (!this.mediaQuery.matches) return;
    
    const touch = e.touches[0];
    this.startX = touch.clientX;
    this.startY = touch.clientY;
    
    // Wisch-Öffnen: Nur wenn Drawer geschlossen und Touch im Edge-Bereich
    if (!this.drawer.open && this.startX <= this.edgeZone) {
      this.isSwipeActive = true;
      // Prevent default nur wenn wir wirklich swipen wollen
      // e.preventDefault();
    }
    
    // Wisch-Schließen: Wenn Drawer offen
    if (this.drawer.open) {
      this.isSwipeActive = true;
    }
  }
  
  handleTouchMove(e) {
    if (!this.isSwipeActive) return;
    
    const touch = e.touches[0];
    this.currentX = touch.clientX;
    const currentY = touch.clientY;
    
    const deltaX = this.currentX - this.startX;
    const deltaY = currentY - this.startY;
    
    // Vertical scroll detection: Cancel horizontal swipe
    if (Math.abs(deltaY) > Math.abs(deltaX)) {
      this.reset();
      return;
    }
    
    // Optional: Visual feedback während Swipe
    // Könnte transform: translateX() für Preview nutzen
    
    // Prevent scroll während horizontal swipe
    if (Math.abs(deltaX) > 10) {
      e.preventDefault();
    }
  }
  
  handleTouchEnd() {
    if (!this.isSwipeActive || this.startX === null || this.currentX === null) {
      this.reset();
      return;
    }
    
    const deltaX = this.currentX - this.startX;
    
    // Wisch nach rechts (öffnen)
    if (!this.drawer.open && deltaX > this.threshold) {
      this.openDrawer();
    }
    
    // Wisch nach links (schließen)
    if (this.drawer.open && deltaX < -this.threshold) {
      this.closeDrawer();
    }
    
    this.reset();
  }
  
  reset() {
    this.isSwipeActive = false;
    this.startX = null;
    this.startY = null;
    this.currentX = null;
  }
  
  openDrawer() {
    // Trigger open via drawer controller
    const openButton = document.querySelector('[data-action="open-drawer"]');
    if (openButton) {
      openButton.click();
    }
  }
  
  closeDrawer() {
    // Trigger close via drawer controller
    if (this.drawer.open) {
      // Backdrop click simulieren oder direkt close() aufrufen
      const backdrop = this.drawer.querySelector('::backdrop') || this.drawer;
      backdrop.dispatchEvent(new Event('click', { bubbles: true }));
    }
  }
}

/**
 * Initialize swipe gestures
 */
export function initSwipeGestures(drawer, mediaQuery) {
  return new SwipeGestureHandler(drawer, mediaQuery);
}
