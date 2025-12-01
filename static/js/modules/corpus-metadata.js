/**
 * Corpus Metadata Page Module
 *
 * Provides interactive country tabs and file tables for the metadata dashboard.
 * Supports deep-linking via URL query parameter (?country=XXX).
 *
 * Data source: /api/v1/atlas/files
 */

// DOM Elements
let tabsContainer = null;
let panelsContainer = null;
let loadingElement = null;
let errorElement = null;

// Data store
let fileMetadata = [];
let countryStats = [];

// Country labels for display
const COUNTRY_LABELS = {
  ARG: "Argentina",
  "ARG-CBA": "Argentina: Córdoba",
  "ARG-CHU": "Argentina: Chubut",
  "ARG-SDE": "Argentina: Santiago del Estero",
  BOL: "Bolivia",
  CHL: "Chile",
  COL: "Colombia",
  CRI: "Costa Rica",
  CUB: "Cuba",
  DOM: "República Dominicana",
  ECU: "Ecuador",
  ESP: "España",
  "ESP-CAN": "España: Canarias",
  "ESP-SEV": "España: Sevilla",
  GTM: "Guatemala",
  HND: "Honduras",
  MEX: "México",
  NIC: "Nicaragua",
  PAN: "Panamá",
  PER: "Perú",
  PRY: "Paraguay",
  SLV: "El Salvador",
  URY: "Uruguay",
  USA: "Estados Unidos",
  VEN: "Venezuela",
};

/**
 * Extract country code from filename
 * Format: prefix_CODE_suffix.json -> CODE
 */
function extractCode(filename) {
  const match = filename.match(/_(.+?)_/);
  if (!match) return "";
  return match[1];
}

/**
 * Format duration from seconds to HH:MM:SS
 */
function formatDuration(value) {
  if (!value) return "00:00:00";

  if (typeof value === "number") {
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const seconds = Math.floor(value % 60);
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }

  const parts = value.split(":");
  if (parts.length < 3) return value;
  const seconds = parts[2].split(".")[0];
  return `${parts[0].padStart(2, "0")}:${parts[1].padStart(2, "0")}:${seconds.padStart(2, "0")}`;
}

/**
 * Format number with locale-specific thousand separators
 */
function formatNumber(value) {
  if (typeof value !== "number") return value || "0";
  return value.toLocaleString("es-ES");
}

/**
 * Get country code from URL query parameter
 */
function getCountryFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get("country") || null;
}

/**
 * Update URL with country code (without page reload)
 */
function updateURL(countryCode) {
  const url = new URL(window.location);
  if (countryCode) {
    url.searchParams.set("country", countryCode);
  } else {
    url.searchParams.delete("country");
  }
  window.history.replaceState({}, "", url);
}

/**
 * Get unique sorted country codes from file metadata
 */
function getCountryCodes() {
  const codes = [...new Set(fileMetadata.map((item) => extractCode(item.filename)))].filter(Boolean);
  return codes.sort();
}

/**
 * Calculate stats for a specific country
 */
function calculateCountryStats(countryCode) {
  const files = fileMetadata.filter((item) => extractCode(item.filename) === countryCode);
  const totalDuration = files.reduce((sum, f) => sum + (f.duration || 0), 0);
  const totalWords = files.reduce((sum, f) => sum + (f.word_count || 0), 0);
  const emisoras = [...new Set(files.map((f) => f.radio))].filter(Boolean);

  return {
    fileCount: files.length,
    totalDuration,
    totalWords,
    emisoras,
  };
}

/**
 * Render country tabs
 */
function renderTabs(countryCodes, activeCode) {
  if (!tabsContainer) return;

  const tabs = countryCodes
    .map((code) => {
      const isActive = code === activeCode;
      const label = COUNTRY_LABELS[code] || code;
      return `
        <button
          class="md3-metadata-tab"
          role="tab"
          aria-selected="${isActive}"
          aria-controls="panel-${code}"
          data-country="${code}"
          id="tab-${code}"
          tabindex="${isActive ? "0" : "-1"}"
          title="${label}"
        >
          ${code}
        </button>
      `;
    })
    .join("");

  tabsContainer.innerHTML = tabs;

  // Attach click and keyboard handlers
  tabsContainer.querySelectorAll(".md3-metadata-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const code = tab.dataset.country;
      activateTab(code);
    });

    // Keyboard navigation (Arrow keys, Home, End)
    tab.addEventListener("keydown", (e) => {
      const allTabs = Array.from(tabsContainer.querySelectorAll(".md3-metadata-tab"));
      const currentIndex = allTabs.indexOf(e.target);
      let newIndex = currentIndex;

      switch (e.key) {
        case "ArrowRight":
        case "ArrowDown":
          e.preventDefault();
          newIndex = (currentIndex + 1) % allTabs.length;
          break;
        case "ArrowLeft":
        case "ArrowUp":
          e.preventDefault();
          newIndex = (currentIndex - 1 + allTabs.length) % allTabs.length;
          break;
        case "Home":
          e.preventDefault();
          newIndex = 0;
          break;
        case "End":
          e.preventDefault();
          newIndex = allTabs.length - 1;
          break;
        default:
          return;
      }

      if (newIndex !== currentIndex) {
        const newTab = allTabs[newIndex];
        newTab.focus();
        activateTab(newTab.dataset.country);
      }
    });
  });
}

/**
 * Render panel for a specific country
 */
function renderPanel(countryCode, isActive) {
  const files = fileMetadata.filter((item) => extractCode(item.filename) === countryCode);
  const stats = calculateCountryStats(countryCode);
  const label = COUNTRY_LABELS[countryCode] || countryCode;

  // Sort files by date descending
  files.sort((a, b) => (b.date || "").localeCompare(a.date || ""));

  const rows = files
    .map(
      (item) => `
      <tr>
        <td>${item.date || "—"}</td>
        <td>${item.radio || "—"}</td>
        <td>${item.filename?.replace(".json", "") || "—"}</td>
        <td class="right-align">${formatDuration(item.duration)}</td>
        <td class="right-align">${formatNumber(item.word_count)}</td>
      </tr>
    `
    )
    .join("");

  return `
    <div
      class="md3-metadata-panel"
      role="tabpanel"
      id="panel-${countryCode}"
      aria-labelledby="tab-${countryCode}"
      data-active="${isActive}"
    >
      <header class="md3-metadata-panel-header">
        <h2 class="md3-title-large md3-metadata-panel-title">${label}</h2>
        <div class="md3-metadata-panel-stats">
          <div class="md3-metadata-stat">
            <span class="md3-metadata-stat-label">Grabaciones</span>
            <span class="md3-metadata-stat-value">${stats.fileCount}</span>
          </div>
          <div class="md3-metadata-stat">
            <span class="md3-metadata-stat-label">Duración total</span>
            <span class="md3-metadata-stat-value">${formatDuration(stats.totalDuration)}</span>
          </div>
          <div class="md3-metadata-stat">
            <span class="md3-metadata-stat-label">Palabras</span>
            <span class="md3-metadata-stat-value">${formatNumber(stats.totalWords)}</span>
          </div>
          <div class="md3-metadata-stat">
            <span class="md3-metadata-stat-label">Emisoras</span>
            <span class="md3-metadata-stat-value">${stats.emisoras.length}</span>
          </div>
        </div>
      </header>

      ${
        files.length > 0
          ? `
        <div class="md3-metadata-table-wrapper">
          <table class="md3-metadata-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Emisora</th>
                <th>Archivo</th>
                <th class="right-align">Duración</th>
                <th class="right-align">Palabras</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `
          : `
        <div class="md3-metadata-empty">
          <p>No hay grabaciones disponibles para este país.</p>
        </div>
      `
      }
    </div>
  `;
}

/**
 * Render all panels
 */
function renderPanels(countryCodes, activeCode) {
  if (!panelsContainer) return;

  const panels = countryCodes.map((code) => renderPanel(code, code === activeCode)).join("");

  panelsContainer.innerHTML = panels;
}

/**
 * Activate a specific tab and panel
 */
function activateTab(countryCode) {
  // Update tab states (aria-selected and tabindex for keyboard nav)
  tabsContainer.querySelectorAll(".md3-metadata-tab").forEach((tab) => {
    const isActive = tab.dataset.country === countryCode;
    tab.setAttribute("aria-selected", isActive.toString());
    tab.setAttribute("tabindex", isActive ? "0" : "-1");
  });

  // Update panel states
  panelsContainer.querySelectorAll(".md3-metadata-panel").forEach((panel) => {
    const isActive = panel.id === `panel-${countryCode}`;
    panel.dataset.active = isActive.toString();
  });

  // Update URL
  updateURL(countryCode);
}

/**
 * Load file metadata from API
 */
async function loadFileMetadata() {
  try {
    const response = await fetch("/api/v1/atlas/files", {
      credentials: "same-origin",
    });
    if (!response.ok) {
      if (response.status === 401) {
        // User not authenticated - show limited data or empty state
        return [];
      }
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return Array.isArray(data.files) ? data.files : [];
  } catch (error) {
    console.error("[Corpus Metadata] Error loading files:", error);
    throw error;
  }
}

/**
 * Show loading state
 */
function showLoading() {
  if (loadingElement) loadingElement.hidden = false;
  if (errorElement) errorElement.hidden = true;
  if (tabsContainer) tabsContainer.innerHTML = "";
  if (panelsContainer) panelsContainer.innerHTML = "";
}

/**
 * Hide loading state
 */
function hideLoading() {
  if (loadingElement) loadingElement.hidden = true;
}

/**
 * Show error state
 */
function showError() {
  if (loadingElement) loadingElement.hidden = true;
  if (errorElement) errorElement.hidden = false;
}

/**
 * Initialize the corpus metadata page
 */
async function init() {
  console.log("[Corpus Metadata] Initializing...");

  // Get DOM elements
  tabsContainer = document.querySelector('[data-element="metadata-tabs"]');
  panelsContainer = document.querySelector('[data-element="metadata-panels"]');
  loadingElement = document.querySelector('[data-element="metadata-loading"]');
  errorElement = document.querySelector('[data-element="metadata-error"]');

  if (!tabsContainer || !panelsContainer) {
    console.warn("[Corpus Metadata] Required elements not found");
    return;
  }

  // Show loading state
  showLoading();

  try {
    // Load data
    fileMetadata = await loadFileMetadata();

    // Hide loading
    hideLoading();

    // Get country codes
    const countryCodes = getCountryCodes();

    if (countryCodes.length === 0) {
      panelsContainer.innerHTML = `
        <div class="md3-metadata-empty">
          <p>No hay metadatos disponibles. Inicie sesión para ver las grabaciones del corpus.</p>
        </div>
      `;
      return;
    }

    // Determine active tab from URL or default to first
    const urlCountry = getCountryFromURL();
    const activeCode = countryCodes.includes(urlCountry) ? urlCountry : countryCodes[0];

    // Render tabs and panels
    renderTabs(countryCodes, activeCode);
    renderPanels(countryCodes, activeCode);

    console.log("[Corpus Metadata] Initialized with", countryCodes.length, "countries");
  } catch (error) {
    console.error("[Corpus Metadata] Initialization failed:", error);
    showError();
  }
}

// Auto-init when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

export { init };
