// ============================================
// Navigation Drawer Controller - Dialog-basiert
// ============================================

import { getWindowSize, WindowSize } from './window-size.js';

/**
 * Focusable element selector
 */
const focusableSelectors = 'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';

/**
 * Navigation Drawer Manager (Dialog-basiert)
 */
export class NavigationDrawer {
  constructor() {
    this.modalDrawer = document.getElementById('navigation-drawer-modal');
    this.standardDrawer = document.getElementById('navigation-drawer-standard');
    this.openButton = document.querySelector('[data-action="open-drawer"]');
    this.mediaQuery = window.matchMedia('(max-width: 839px)');
    
    if (!this.modalDrawer || !this.standardDrawer) {
      console.error('Navigation drawers not found');
      return;
    }
    
    this.init();
  }
  
  init() {
    // Open button
    if (this.openButton) {
      this.openButton.addEventListener('click', () => this.open());
    }
    
    // Klick ins Backdrop → schließen (Light Dismiss)
    this.modalDrawer.addEventListener('click', (e) => {
      if (e.target === this.modalDrawer) {
        this.close();
      }
    });
    
    // ESC wird von <dialog> automatisch gehandhabt via 'cancel' event
    // Aber wir können es auch explizit handlen für bessere Kontrolle
    this.modalDrawer.addEventListener('cancel', (e) => {
      // Optional: preventDefault() wenn man custom Logik will
      // e.preventDefault();
      this.close();
    });
    
    // Cleanup bei Resize: bei Expanded schließen
    this.mediaQuery.addEventListener('change', (e) => {
      if (!e.matches && this.modalDrawer.open) {
        this.close();
      }
    });
    
    // Initialize collapsibles for both drawers
    this.initCollapsibles(this.modalDrawer);
    this.initCollapsibles(this.standardDrawer);
    
    // Handle links (close modal on navigation)
    this.modalDrawer.querySelectorAll('a[href]').forEach(link => {
      link.addEventListener('click', () => {
        this.close();
      });
    });
  }
  
  initCollapsibles(drawer) {
    // Event Delegation: Ein Listener für alle Trigger
    drawer.addEventListener('click', (e) => {
      const trigger = e.target.closest('.md3-navigation-drawer__trigger');
      if (!trigger) return;

      const submenuId = trigger.getAttribute('aria-controls');
      const submenu = drawer.querySelector(`#${submenuId}`);
      if (!submenu) return;

      const isExpanded = trigger.getAttribute('aria-expanded') === 'true';

      // Optional: Nur ein Submenü gleichzeitig offen (Single-Open-Modus)
      drawer.querySelectorAll('.md3-navigation-drawer__trigger[aria-expanded="true"]').forEach(otherTrigger => {
        if (otherTrigger !== trigger) {
          const otherSubmenuId = otherTrigger.getAttribute('aria-controls');
          const otherSubmenu = drawer.querySelector(`#${otherSubmenuId}`);
          
          // Close other submenu with animation
          otherTrigger.setAttribute('aria-expanded', 'false');
          if (otherSubmenu) {
            otherSubmenu.classList.add('closing');
            // Nach Animation: Attributes aufräumen
            setTimeout(() => {
              otherSubmenu.removeAttribute('data-open');
              otherSubmenu.setAttribute('aria-hidden', 'true');
              otherSubmenu.classList.remove('closing');
            }, 250); // Match CSS transition duration
          }
        }
      });

      // Toggle current submenu
      trigger.setAttribute('aria-expanded', String(!isExpanded));
      if (!isExpanded) {
        // Open
        submenu.classList.remove('closing');
        submenu.setAttribute('data-open', '');
        submenu.setAttribute('aria-hidden', 'false');
      } else {
        // Close with animation
        submenu.classList.add('closing');
        setTimeout(() => {
          submenu.removeAttribute('data-open');
          submenu.setAttribute('aria-hidden', 'true');
          submenu.classList.remove('closing');
        }, 250); // Match CSS transition duration
      }
    });
  }
  
  open() {
    // Only open modal drawer on Compact/Medium
    if (!this.mediaQuery.matches) return;
    
    // Native Dialog API: showModal() für Modalität + Fokus-Management
    if (!this.modalDrawer.open) {
      this.modalDrawer.showModal();
      
      // Optional: Ersten Fokus setzen
      const firstFocusable = this.modalDrawer.querySelector(focusableSelectors);
      if (firstFocusable) {
        // preventScroll: true verhindert Jump bei Fokus
        setTimeout(() => firstFocusable.focus({ preventScroll: true }), 100);
      }
    }
    
    // Update ARIA auf Open-Button
    if (this.openButton) {
      this.openButton.setAttribute('aria-expanded', 'true');
    }
  }
  
  close() {
    // Native Dialog API: close() - aber mit Animation
    if (this.modalDrawer.open) {
      // Remove [open] attribute um Exit-Animation zu triggern
      // Aber Dialog bleibt technisch "open" bis Animation fertig
      this.modalDrawer.classList.add('closing');
      
      // Nach Animation: tatsächlich schließen
      setTimeout(() => {
        this.modalDrawer.close();
        this.modalDrawer.classList.remove('closing');
      }, 250); // Match CSS transition duration
    }
    
    // Update ARIA auf Open-Button
    if (this.openButton) {
      this.openButton.setAttribute('aria-expanded', 'false');
    }
  }
}

/**
 * Initialize navigation drawer
 */
export function initNavigationDrawer() {
  return new NavigationDrawer();
}
