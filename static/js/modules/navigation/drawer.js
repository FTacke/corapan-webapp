// ============================================
// Navigation Drawer Controller
// ============================================

import { getWindowSize, WindowSize } from './window-size.js';

/**
 * Focus trap utility (reused from existing mobile menu)
 */
const focusableSelectors = 'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';

function trapFocus(container) {
  const focusable = Array.from(container.querySelectorAll(focusableSelectors))
    .filter(el => !el.hasAttribute('disabled') && el.tabIndex !== -1);
  
  if (!focusable.length) return () => {};
  
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  
  function handleKeydown(event) {
    if (event.key !== 'Tab') return;
    
    if (event.shiftKey) {
      if (document.activeElement === first) {
        event.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  }
  
  container.addEventListener('keydown', handleKeydown);
  return () => container.removeEventListener('keydown', handleKeydown);
}

/**
 * Navigation Drawer Manager
 */
export class NavigationDrawer {
  constructor() {
    this.modalDrawer = document.getElementById('navigation-drawer-modal');
    this.standardDrawer = document.getElementById('navigation-drawer-standard');
    this.openButton = document.querySelector('[data-action="open-drawer"]');
    this.closeTargets = document.querySelectorAll('[data-action="close-drawer"]');
    
    this.isOpen = false;
    this.releaseFocusTrap = null;
    this.lastFocusedElement = null;
    
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
    
    // Close button and scrim
    this.closeTargets.forEach(target => {
      target.addEventListener('click', () => this.close());
    });
    
    // ESC key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
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
    const triggers = drawer.querySelectorAll('.md3-navigation-drawer__trigger');
    
    triggers.forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        const submenuId = trigger.getAttribute('aria-controls');
        const submenu = drawer.querySelector(`#${submenuId}`);
        const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
        
        // Close other open submenus
        triggers.forEach(otherTrigger => {
          if (otherTrigger !== trigger) {
            const otherSubmenuId = otherTrigger.getAttribute('aria-controls');
            const otherSubmenu = drawer.querySelector(`#${otherSubmenuId}`);
            otherTrigger.setAttribute('aria-expanded', 'false');
            if (otherSubmenu) otherSubmenu.hidden = true;
          }
        });
        
        // Toggle current submenu
        trigger.setAttribute('aria-expanded', !isExpanded);
        if (submenu) {
          submenu.hidden = isExpanded;
        }
      });
    });
  }
  
  open() {
    if (this.isOpen) return;
    
    // Only open modal drawer on Compact/Medium
    const windowSize = getWindowSize();
    if (windowSize === WindowSize.EXPANDED) return;
    
    this.lastFocusedElement = document.activeElement;
    
    // Reine CSS-Animation mit @starting-style (Chrome 117+)
    // Keine setTimeout nötig - Browser handled Entry-Animation automatisch
    this.modalDrawer.hidden = false;
    this.modalDrawer.classList.add('md3-navigation-drawer--open');
    
    document.body.classList.add('overflow-hidden');
    
    // Update ARIA
    if (this.openButton) {
      this.openButton.setAttribute('aria-expanded', 'true');
    }
    
    // Setup focus trap
    const container = this.modalDrawer.querySelector('.md3-navigation-drawer__container');
    if (container) {
      this.releaseFocusTrap = trapFocus(container);
      
      // Focus first focusable element
      const firstFocusable = container.querySelector(focusableSelectors);
      if (firstFocusable) {
        setTimeout(() => firstFocusable.focus(), 100);
      }
    }
    
    this.isOpen = true;
  }
  
  close() {
    if (!this.isOpen) return;
    
    // Remove open class to trigger close animation
    this.modalDrawer.classList.remove('md3-navigation-drawer--open');
    
    // After animation, set hidden attribute
    setTimeout(() => {
      this.modalDrawer.hidden = true;
    }, 250); // Match CSS transition duration
    
    document.body.classList.remove('overflow-hidden');
    
    // Update ARIA
    if (this.openButton) {
      this.openButton.setAttribute('aria-expanded', 'false');
    }
    
    // Release focus trap
    if (this.releaseFocusTrap) {
      this.releaseFocusTrap();
      this.releaseFocusTrap = null;
    }
    
    // Restore focus
    if (this.lastFocusedElement) {
      this.lastFocusedElement.focus();
      this.lastFocusedElement = null;
    }
    
    this.isOpen = false;
  }
}

/**
 * Initialize navigation drawer
 */
export function initNavigationDrawer() {
  return new NavigationDrawer();
}
