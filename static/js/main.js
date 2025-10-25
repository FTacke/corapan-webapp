// ============================================
// JWT Token Auto-Refresh Initialization
// ============================================
import { setupTokenRefresh } from './modules/auth/token-refresh.js';

// Setup automatic token refresh on app initialization
setupTokenRefresh();

// ============================================
// Mobile Navigation
// ============================================
const navbarRoot = document.querySelector('.site-header');
const mobileToggle = navbarRoot?.querySelector('[data-mobile-toggle]');
const mobileMenu = navbarRoot?.querySelector('[data-mobile-menu]');
const mobileClose = mobileMenu?.querySelector('[data-mobile-close]');
const mobileBackdrop = mobileMenu?.querySelector('[data-mobile-backdrop]');
let lastFocusedElement = null;

const focusableSelectors = 'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';
let releaseFocusTrap = () => {};
const MOBILE_MENU_TRANSITION_FALLBACK = 380;
let mobileMenuTransitionHandler = null;
let mobileMenuCloseTimeout = null;
let mobileMenuAnimationFrame = null;

function getMobileMenuTransitionDuration() {
  if (!mobileMenu) return MOBILE_MENU_TRANSITION_FALLBACK;
  const raw = getComputedStyle(mobileMenu).getPropertyValue('--md3-mobile-menu-duration').trim();
  if (!raw) return MOBILE_MENU_TRANSITION_FALLBACK;
  if (raw.endsWith('ms')) {
    const value = Number.parseFloat(raw);
    return Number.isNaN(value) ? MOBILE_MENU_TRANSITION_FALLBACK : value;
  }
  if (raw.endsWith('s')) {
    const value = Number.parseFloat(raw);
    return Number.isNaN(value) ? MOBILE_MENU_TRANSITION_FALLBACK : value * 1000;
  }
  const value = Number.parseFloat(raw);
  return Number.isNaN(value) ? MOBILE_MENU_TRANSITION_FALLBACK : value;
}

function trapFocus(container) {
  const focusable = Array.from(container.querySelectorAll(focusableSelectors)).filter((element) => !element.hasAttribute('disabled') && element.tabIndex !== -1);
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
    } else if (document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
  container.addEventListener('keydown', handleKeydown);
  return () => container.removeEventListener('keydown', handleKeydown);
}

function openMobileMenu() {
  if (!mobileMenu) return;
  if (mobileMenuTransitionHandler) {
    mobileMenu.removeEventListener('transitionend', mobileMenuTransitionHandler);
    mobileMenuTransitionHandler = null;
  }
  if (mobileMenuCloseTimeout) {
    window.clearTimeout(mobileMenuCloseTimeout);
    mobileMenuCloseTimeout = null;
  }
  mobileMenu.hidden = false;
  // Force reflow so transitions fire correctly.
  void mobileMenu.getBoundingClientRect();
  document.body.classList.add('overflow-hidden');
  mobileToggle?.setAttribute('aria-expanded', 'true');
  lastFocusedElement = document.activeElement;
  const dialog = mobileMenu.querySelector('[role="dialog"]');
  if (dialog) {
    releaseFocusTrap = trapFocus(dialog);
  }
  if (mobileMenuAnimationFrame) {
    window.cancelAnimationFrame(mobileMenuAnimationFrame);
  }
  mobileMenuAnimationFrame = window.requestAnimationFrame(() => {
    mobileMenuAnimationFrame = null;
    mobileMenu.classList.add('is-open');
    if (dialog) {
      const firstFocusable = dialog.querySelector(focusableSelectors);
      firstFocusable?.focus();
    }
  });
}

function closeMobileMenu() {
  if (!mobileMenu || mobileMenu.hidden) return;
  
  // Close all expanded collapsibles before closing menu
  const collapsibleTriggers = document.querySelectorAll('.md3-mobile-collapsible__trigger');
  collapsibleTriggers.forEach(trigger => {
    trigger.setAttribute('aria-expanded', 'false');
    const contentId = trigger.getAttribute('aria-controls');
    const content = document.getElementById(contentId);
    if (content) {
      content.classList.remove('is-expanded');
      content.hidden = true;
    }
  });
  
  if (mobileMenuTransitionHandler) {
    mobileMenu.removeEventListener('transitionend', mobileMenuTransitionHandler);
    mobileMenuTransitionHandler = null;
  }
  if (mobileMenuCloseTimeout) {
    window.clearTimeout(mobileMenuCloseTimeout);
    mobileMenuCloseTimeout = null;
  }
  mobileMenu.classList.remove('is-open');
  if (mobileMenuAnimationFrame) {
    window.cancelAnimationFrame(mobileMenuAnimationFrame);
    mobileMenuAnimationFrame = null;
  }
  document.body.classList.remove('overflow-hidden');
  mobileToggle?.setAttribute('aria-expanded', 'false');
  releaseFocusTrap();
  if (lastFocusedElement) {
    lastFocusedElement.focus();
  }
  mobileMenuTransitionHandler = (event) => {
    if (event.target !== mobileMenu || event.propertyName !== 'opacity') {
      return;
    }
    mobileMenu.hidden = true;
    mobileMenu.removeEventListener('transitionend', mobileMenuTransitionHandler);
    mobileMenuTransitionHandler = null;
    if (mobileMenuCloseTimeout) {
      window.clearTimeout(mobileMenuCloseTimeout);
      mobileMenuCloseTimeout = null;
    }
  };
  mobileMenu.addEventListener('transitionend', mobileMenuTransitionHandler);
  const menuTransitionDuration = getMobileMenuTransitionDuration();
  mobileMenuCloseTimeout = window.setTimeout(() => {
    if (!mobileMenu.hidden) {
      mobileMenu.hidden = true;
    }
    if (mobileMenuTransitionHandler) {
      mobileMenu.removeEventListener('transitionend', mobileMenuTransitionHandler);
      mobileMenuTransitionHandler = null;
    }
    mobileMenuCloseTimeout = null;
  }, menuTransitionDuration);
}

mobileToggle?.addEventListener('click', () => {
  if (!mobileMenu) return;
  if (mobileMenu.classList.contains('is-open')) {
    closeMobileMenu();
  } else {
    openMobileMenu();
  }
});

mobileClose?.addEventListener('click', closeMobileMenu);
mobileBackdrop?.addEventListener('click', closeMobileMenu);

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    if (mobileMenu && mobileMenu.classList.contains('is-open')) {
      closeMobileMenu();
    }
    if (userMenuOpen) {
      closeUserMenu();
      userMenuToggle?.focus();
    }
    if (loginSheet && !loginSheet.hidden) {
      closeLogin();
    }
  }
});

const userMenuToggle = navbarRoot?.querySelector('[data-user-menu-toggle]');
const userMenu = navbarRoot?.querySelector('[data-user-menu]');
let userMenuOpen = false;

function openUserMenu() {
  if (!userMenu) return;
  userMenu.hidden = false;
  userMenuToggle?.setAttribute('aria-expanded', 'true');
  userMenuOpen = true;
  const firstFocusable = userMenu.querySelector(focusableSelectors);
  firstFocusable?.focus();
}

function closeUserMenu() {
  if (!userMenu) return;
  userMenu.hidden = true;
  userMenuToggle?.setAttribute('aria-expanded', 'false');
  userMenuOpen = false;
}

userMenuToggle?.addEventListener('click', (event) => {
  event.preventDefault();
  if (!userMenu) return;
  if (userMenuOpen) {
    closeUserMenu();
  } else {
    openUserMenu();
  }
});

document.addEventListener('click', (event) => {
  if (!userMenuOpen) return;
  if (!userMenu?.contains(event.target) && !userMenuToggle?.contains(event.target)) {
    closeUserMenu();
  }
});

userMenu?.addEventListener('click', (event) => {
  const target = event.target;
  if (!(target instanceof Element)) return;
  if (target.closest('a, button')) {
    closeUserMenu();
  }
});

const loginSheet = document.querySelector('[data-element="login-sheet"]');
const openLoginButtons = document.querySelectorAll('[data-action="open-login"]');
const closeLoginButtons = document.querySelectorAll('[data-action="close-login"]');
let previouslyFocusedForLogin = null;
let scrollPositionBeforeLogin = 0;

function openLogin() {
  if (!loginSheet) return;
  
  // Save current scroll position to restore later if needed
  scrollPositionBeforeLogin = window.scrollY || window.pageYOffset;
  
  // Lock body scroll position using CSS variable (prevents jump when overflow:hidden is applied)
  document.body.style.setProperty('--scroll-lock-offset', `-${scrollPositionBeforeLogin}px`);
  
  loginSheet.hidden = false;
  document.body.classList.add('login-open');
  previouslyFocusedForLogin = document.activeElement;
  
  // Focus input without scrolling the page
  const input = loginSheet.querySelector('input[name="username"]');
  if (input) {
    // Use preventScroll to avoid automatic scroll-to-focused-element
    input.focus({ preventScroll: true });
  }
}

function closeLogin() {
  if (!loginSheet) return;
  
  loginSheet.hidden = true;
  document.body.classList.remove('login-open');
  
  // Remove scroll lock CSS variable
  document.body.style.removeProperty('--scroll-lock-offset');
  
  // Restore scroll position
  window.scrollTo(0, scrollPositionBeforeLogin);
  
  if (previouslyFocusedForLogin) {
    previouslyFocusedForLogin.focus({ preventScroll: true });
  }
}

openLoginButtons.forEach((button) => {
  button.addEventListener('click', (event) => {
    event.preventDefault();
    openLogin();
  });
});

closeLoginButtons.forEach((button) => {
  button.addEventListener('click', (event) => {
    event.preventDefault();
    closeLogin();
  });
});

loginSheet?.addEventListener('click', (event) => {
  if (event.target === loginSheet) {
    closeLogin();
  }
});

const loginForm = loginSheet?.querySelector('form');
loginForm?.addEventListener('submit', async (event) => {
  // Check if there's a stored player redirect URL (from client-side navigation)
  const clientRedirectUrl = sessionStorage.getItem('_player_redirect_after_login');
  
  if (clientRedirectUrl) {
    // Prevent default form submission
    event.preventDefault();
    
    // Get form data
    const formData = new FormData(loginForm);
    
    try {
      // Submit login via fetch
      const response = await fetch(loginForm.action, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      });
      
      if (response.ok) {
        // Login successful - clear storage and navigate to player
        sessionStorage.removeItem('_player_redirect_after_login');
        window.location.href = clientRedirectUrl;
      } else {
        // Login failed - reload page to show error message
        window.location.reload();
      }
    } catch (error) {
      // On error, reload page
      console.error('Login error:', error);
      window.location.reload();
    }
  } else {
    // No client-side redirect URL - let form submit normally
    // Backend will handle redirect to saved session URL or referrer
    closeLogin();
  }
});

function getCookie(name) {
  return document.cookie
    .split(';')
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith(`${name}=`))?.split('=')[1] || '';
}

function syncLogoutCsrf() {
  const logoutForms = document.querySelectorAll('[data-element^="logout-form"]');
  if (!logoutForms.length) return;
  const csrfToken = decodeURIComponent(getCookie('csrf_access_token'));
  logoutForms.forEach((form) => {
    const field = form.querySelector('[data-element="csrf-token"]');
    if (field && csrfToken) {
      field.value = csrfToken;
    }
  });
}

function ensureLoginHiddenForAuthenticated() {
  if (!navbarRoot || !loginSheet) return;
  const isAuthenticated = navbarRoot.dataset.auth === 'true';
  if (isAuthenticated) {
    loginSheet.hidden = true;
    document.body.classList.remove('login-open');
  }
}

syncLogoutCsrf();
ensureLoginHiddenForAuthenticated();

// Open login sheet if redirected with ?showlogin=1 query parameter
// Using query param instead of hash avoids automatic scroll-to-anchor behavior
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.has('showlogin')) {
  // Remove showlogin parameter from URL without reload (clean URL)
  urlParams.delete('showlogin');
  const newSearch = urlParams.toString();
  const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '');
  history.replaceState(null, '', newUrl);
  
  // Open login sheet (scroll position is preserved automatically)
  openLogin();
}

// Mark active navigation link
function markActiveNavLink() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.nav-link');
  const mobileLinks = document.querySelectorAll('.mobile-link');
  
  navLinks.forEach(link => {
    const linkPath = new URL(link.href).pathname;
    if (linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath))) {
      link.classList.add('nav-link--active');
    }
  });
  
  mobileLinks.forEach(link => {
    const linkPath = new URL(link.href).pathname;
    if (linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath))) {
      link.classList.add('mobile-link--active');
    }
  });
}

// Desktop submenu functionality
let openDesktopSubmenu = null;

function closeAllDesktopSubmenus() {
  document.querySelectorAll('.md3-nav__submenu').forEach(menu => {
    menu.hidden = true;
    const trigger = menu.previousElementSibling;
    if (trigger && trigger.classList.contains('md3-nav__trigger')) {
      trigger.setAttribute('aria-expanded', 'false');
    }
  });
  openDesktopSubmenu = null;
}

function initDesktopSubmenus() {
  // Use event delegation: attach a single click listener to the nav links container.
  // This is more robust (works even if triggers are dynamically replaced or listeners
  // would otherwise be missed on some pages).
  const navLinksContainer = document.querySelector('.md3-nav__links');
  if (!navLinksContainer) return;

  navLinksContainer.addEventListener('click', (event) => {
    const clicked = event.target instanceof Element ? event.target.closest('.md3-nav__trigger') : null;
    if (!clicked) return;
    event.preventDefault();
    event.stopPropagation();

    const submenuId = clicked.getAttribute('aria-controls');
    const submenu = submenuId ? document.getElementById(submenuId) : null;
    if (!submenu) return;

    const isCurrentlyOpen = !submenu.hidden;
    // Close all submenus first
    closeAllDesktopSubmenus();

    // If it wasn't open, open it
    if (!isCurrentlyOpen) {
      submenu.hidden = false;
      clicked.setAttribute('aria-expanded', 'true');
      openDesktopSubmenu = submenu;
    }
  });

  // Close desktop submenu when clicking outside
  document.addEventListener('click', (event) => {
    if (!openDesktopSubmenu) return;
    const target = event.target;
    if (!(target instanceof Element)) return;

    // Don't close if clicking inside the submenu or on the trigger wrapper
    if (!target.closest('.md3-nav__link-with-menu')) {
      closeAllDesktopSubmenus();
    }
  });
}

// Initialize desktop submenus - wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', initDesktopSubmenus);

// Mobile collapsible functionality (replaces subpanel logic)
function initMobileCollapsibles() {
  const collapsibleTriggers = document.querySelectorAll('.md3-mobile-collapsible__trigger');
  
  collapsibleTriggers.forEach(trigger => {
    const contentId = trigger.getAttribute('aria-controls');
    const content = document.getElementById(contentId);
    if (!content) return;
    
    // Auto-expand if any child link is active (Best Practice: show current location)
    const hasActiveChild = content.querySelector('.md3-mobile-link--active');
    if (hasActiveChild) {
      trigger.setAttribute('aria-expanded', 'true');
      content.removeAttribute('hidden');
      content.classList.add('is-expanded');
    }
    
    // Toggle on click
    trigger.addEventListener('click', (event) => {
      event.preventDefault();
      
      const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
      
      if (isExpanded) {
        // Collapse with smooth animation
        trigger.setAttribute('aria-expanded', 'false');
        content.classList.remove('is-expanded');
        // Set hidden after animation completes
        setTimeout(() => {
          if (!content.classList.contains('is-expanded')) {
            content.hidden = true;
          }
        }, 400);
      } else {
        // Expand with smooth animation
        trigger.setAttribute('aria-expanded', 'true');
        content.removeAttribute('hidden');
        // Trigger reflow for smooth animation
        void content.offsetHeight;
        content.classList.add('is-expanded');
      }
    });
  });
}

// Initialize mobile collapsibles - wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', initMobileCollapsibles);

// Run on page load - wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', markActiveNavLink);
