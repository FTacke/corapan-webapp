// ============================================
// Top App Bar Controller - User Menu Handler
// ============================================

/**
 * Initialize User Menu Toggle
 *
 * Handles opening/closing of avatar dropdown menu.
 * Uses delegated event listeners to work on every page load.
 * Binds on DOMContentLoaded to ensure DOM is ready.
 */
function initUserMenu() {
  // Delegate: Find elements whenever they exist (after any page reload)
  const btn = document.querySelector("[data-user-menu-toggle]");
  const menu = document.querySelector("[data-user-menu]");

  if (!btn || !menu) {
    console.log("[TopAppBar] User menu not found on this page");
    return;
  }

  // Open/Close on button click
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = menu.hasAttribute("data-open");

    if (isOpen) {
      closeUserMenu(btn, menu);
    } else {
      openUserMenu(btn, menu);
    }
  });

  // Close on outside click
  document.addEventListener("click", (e) => {
    if (!btn.contains(e.target) && !menu.contains(e.target)) {
      closeUserMenu(btn, menu);
    }
  });

  // Close on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && menu.hasAttribute("data-open")) {
      closeUserMenu(btn, menu);
      btn.focus();
    }
  });

  console.log("[TopAppBar] User menu initialized");
}

function openUserMenu(btn, menu) {
  menu.setAttribute("data-open", "1");
  btn.setAttribute("aria-expanded", "true");

  // Focus first menu item
  const firstItem = menu.querySelector('[role="menuitem"]');
  if (firstItem) {
    setTimeout(() => firstItem.focus(), 50);
  }
}

function closeUserMenu(btn, menu) {
  menu.removeAttribute("data-open");
  btn.setAttribute("aria-expanded", "false");
}

/**
 * Top App Bar Manager (Legacy - kept for compatibility)
 * - Transparent, Elevation 0
 * - Burger links (nur Compact/Medium)
 * - Login/Avatar rechts
 * - User Menu mit Logout
 * - Login Sheet
 */
export class TopAppBar {
  constructor() {
    this.appBar = document.querySelector('[data-element="top-app-bar"]');

    if (!this.appBar) {
      console.warn("[TopAppBar] App Bar not found");
      return;
    }

    this.init();
  }

  init() {
    // User menu functionality
    this.initUserMenu();

    // Login sheet functionality
    this.initLoginSheet();

    // Optional: Check for ?showlogin=1 query parameter
    this.checkAutoOpenLogin();
  }

  /**
   * User Menu (Avatar mit Logout-Menü)
   */
  initUserMenu() {
    const userMenuRoot = document.querySelector("[data-user-menu-root]");
    if (!userMenuRoot) return;

    const toggle = userMenuRoot.querySelector("[data-user-menu-toggle]");
    const dropdown = userMenuRoot.querySelector("[data-user-menu]");

    if (!toggle || !dropdown) return;

    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      const isExpanded = toggle.getAttribute("aria-expanded") === "true";

      if (isExpanded) {
        this.closeUserMenu(toggle, dropdown);
      } else {
        this.openUserMenu(toggle, dropdown);
      }
    });

    // Close on outside click
    document.addEventListener("click", (e) => {
      if (!userMenuRoot.contains(e.target)) {
        this.closeUserMenu(toggle, dropdown);
      }
    });

    // Close on ESC
    document.addEventListener("keydown", (e) => {
      if (
        e.key === "Escape" &&
        toggle.getAttribute("aria-expanded") === "true"
      ) {
        this.closeUserMenu(toggle, dropdown);
        toggle.focus();
      }
    });
  }

  openUserMenu(toggle, dropdown) {
    toggle.setAttribute("aria-expanded", "true");
    dropdown.hidden = false;

    // Focus first item (Logout button)
    const firstItem = dropdown.querySelector('[role="menuitem"]');
    if (firstItem) {
      setTimeout(() => firstItem.focus(), 50);
    }
  }

  closeUserMenu(toggle, dropdown) {
    toggle.setAttribute("aria-expanded", "false");
    dropdown.hidden = true;
  }

  /**
   * Login Sheet (Bottom Sheet auf Mobile, Dialog auf Desktop)
   */
  initLoginSheet() {
    const loginSheet = document.querySelector('[data-element="login-sheet"]');
    if (!loginSheet) return;

    const openButtons = document.querySelectorAll('[data-action="open-login"]');
    const closeButtons = document.querySelectorAll(
      '[data-action="close-login"]',
    );

    openButtons.forEach((btn) => {
      btn.addEventListener("click", () => this.openLoginSheet(loginSheet));
    });

    closeButtons.forEach((btn) => {
      btn.addEventListener("click", () => this.closeLoginSheet(loginSheet));
    });

    // Close on backdrop click
    const backdrop = loginSheet.querySelector(".md3-login-backdrop");
    if (backdrop) {
      backdrop.addEventListener("click", () =>
        this.closeLoginSheet(loginSheet),
      );
    }

    // Close on ESC
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !loginSheet.hidden) {
        this.closeLoginSheet(loginSheet);
      }
    });
  }

  openLoginSheet(sheet) {
    sheet.hidden = false;
    document.body.classList.add("overflow-hidden");

    // Focus first input
    const firstInput = sheet.querySelector(
      'input[type="text"], input[name="username"]',
    );
    if (firstInput) {
      setTimeout(() => firstInput.focus(), 150);
    }
  }

  closeLoginSheet(sheet) {
    sheet.hidden = true;
    document.body.classList.remove("overflow-hidden");
  }

  /**
   * Auto-open login if ?showlogin=1 in URL
   */
  checkAutoOpenLogin() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("showlogin") === "1") {
      const loginSheet = document.querySelector('[data-element="login-sheet"]');
      if (loginSheet) {
        setTimeout(() => this.openLoginSheet(loginSheet), 300);

        // Remove query parameter from URL without reload
        const url = new URL(window.location);
        url.searchParams.delete("showlogin");
        window.history.replaceState({}, "", url);
      }
    }
  }
}

/**
 * Initialize top app bar
 */
export function initTopAppBar() {
  return new TopAppBar();
}

// Export delegated user menu initializer
export { initUserMenu };
