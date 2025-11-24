// DOM elements - will be initialized in init()
let MAP_CONTAINER = null;
let selectNationalElement = null;
let selectRegionalElement = null;
let filesContainer = null;
let tabsContainer = null;
let loginSheet = null;
let loginButtons = null;

// Function to get current auth status (checks dynamically)
function isUserAuthenticated() {
  const headerRoot = document.querySelector('[data-element="top-app-bar"]');
  return headerRoot?.dataset.auth === "true";
}

const CITY_LIST = [
  {
    code: "ARG",
    label: "Argentina: Buenos Aires",
    lat: -34.6118,
    lng: -58.4173,
    tier: "primary",
    type: "national",
  },
  {
    code: "ARG-CHU",
    label: "Argentina: Trelew (Chubut)",
    lat: -43.2489,
    lng: -65.3051,
    tier: "secondary",
    type: "regional",
  },
  {
    code: "ARG-CBA",
    label: "Argentina: Cordoba (Cordoba)",
    lat: -31.4201,
    lng: -64.1888,
    tier: "secondary",
    type: "regional",
  },
  {
    code: "ARG-SDE",
    label: "Argentina: Santiago del Estero",
    lat: -27.7951,
    lng: -64.2615,
    tier: "secondary",
    type: "regional",
  },
  {
    code: "BOL",
    label: "Bolivia: La Paz",
    lat: -16.5,
    lng: -68.15,
    tier: "primary",
    type: "national",
  },
  {
    code: "CHL",
    label: "Chile: Santiago",
    lat: -33.4489,
    lng: -70.6693,
    tier: "primary",
    type: "national",
  },
  {
    code: "COL",
    label: "Colombia: Bogota",
    lat: 4.6097,
    lng: -74.0817,
    tier: "primary",
    type: "national",
  },
  {
    code: "CRI",
    label: "Costa Rica: San Jose",
    lat: 9.9281,
    lng: -84.0907,
    tier: "primary",
    type: "national",
  },
  {
    code: "CUB",
    label: "Cuba: La Habana",
    lat: 23.133,
    lng: -82.383,
    tier: "primary",
    type: "national",
  },
  {
    code: "ECU",
    label: "Ecuador: Quito",
    lat: -0.23,
    lng: -78.52,
    tier: "primary",
    type: "national",
  },
  {
    code: "SLV",
    label: "El Salvador: San Salvador",
    lat: 13.6929,
    lng: -89.2182,
    tier: "primary",
    type: "national",
  },
  {
    code: "USA",
    label: "Estados Unidos: Miami",
    lat: 25.7617,
    lng: -80.1918,
    tier: "primary",
    type: "national",
  },
  {
    code: "ESP",
    label: "Espa\u00f1a: Madrid",
    lat: 40.4168,
    lng: -3.7038,
    tier: "primary",
    type: "national",
  },
  {
    code: "ESP-CAN",
    label: "Espa\u00f1a: La Laguna (Canarias)",
    lat: 28.4874,
    lng: -16.3141,
    tier: "secondary",
    type: "regional",
  },
  {
    code: "ESP-SEV",
    label: "Espa\u00f1a: Sevilla (Andaluc\u00eda)",
    lat: 37.3886,
    lng: -5.9823,
    tier: "secondary",
    type: "regional",
  },
  {
    code: "GTM",
    label: "Guatemala: Ciudad de Guatemala",
    lat: 14.6349,
    lng: -90.5069,
    tier: "primary",
    type: "national",
  },
  {
    code: "HND",
    label: "Honduras: Tegucigalpa",
    lat: 14.0723,
    lng: -87.1921,
    tier: "primary",
    type: "national",
  },
  {
    code: "MEX",
    label: "M\u00e9xico: Ciudad de M\u00e9xico",
    lat: 19.4326,
    lng: -99.1332,
    tier: "primary",
    type: "national",
  },
  {
    code: "NIC",
    label: "Nicaragua: Managua",
    lat: 12.1364,
    lng: -86.2514,
    tier: "primary",
    type: "national",
  },
  {
    code: "PAN",
    label: "Panam\u00e1: Ciudad de Panam\u00e1",
    lat: 8.9824,
    lng: -79.5199,
    tier: "primary",
    type: "national",
  },
  {
    code: "PRY",
    label: "Paraguay: Asunci\u00f3n",
    lat: -25.2637,
    lng: -57.5759,
    tier: "primary",
    type: "national",
  },
  {
    code: "PER",
    label: "Per\u00fa: Lima",
    lat: -12.0464,
    lng: -77.0428,
    tier: "primary",
    type: "national",
  },
  {
    code: "DOM",
    label: "Rep\u00fablica Dominicana: Santo Domingo",
    lat: 18.4663,
    lng: -69.9526,
    tier: "primary",
    type: "national",
  },
  {
    code: "URY",
    label: "Uruguay: Montevideo",
    lat: -34.9011,
    lng: -56.191,
    tier: "primary",
    type: "national",
  },
  {
    code: "VEN",
    label: "Venezuela: Caracas",
    lat: 10.5,
    lng: -66.9333,
    tier: "primary",
    type: "national",
  },
];

const MARKER_ICONS = {
  primary: {
    path: "/static/img/citymarkers/primary/",
    file: "communications-tower.svg",
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  },
  secondary: {
    path: "/static/img/citymarkers/secondary/",
    file: "communications-tower.svg",
    iconSize: [25, 25],
    iconAnchor: [17, 17],
  },
};

let mapInstance = null;
const cityMarkers = new Map();
let fileMetadata = [];
let overviewStats = null;
let countryStats = [];

function getMapWidth() {
  return MAP_CONTAINER ? MAP_CONTAINER.offsetWidth : window.innerWidth;
}

function getInitialZoom() {
  const width = getMapWidth();
  if (width <= 480) return 2.6;
  if (width <= 900) return 2.8;
  return 3;
}

function getInitialCenter() {
  const width = getMapWidth();
  if (width <= 480) return [-6, -60];
  if (width <= 900) return [-2, -55];
  return [1, -50];
}

function openLoginSheet(nextTarget = "") {
  if (loginSheet) {
    // Save current scroll position
    const scrollY = window.scrollY || window.pageYOffset;

    // Lock body scroll position using CSS variable (prevents jump when overflow:hidden is applied)
    // On desktop (>=840px), we don't use position:fixed, so this is only relevant for mobile
    document.body.style.setProperty("--scroll-lock-offset", `-${scrollY}px`);

    loginSheet.hidden = false;
    document.body.classList.add("login-open");

    // Focus input without scrolling
    const input = loginSheet.querySelector('input[name="username"]');
    if (input) {
      input.focus({ preventScroll: true });
    }
  } else if (loginButtons.length) {
    if (nextTarget) {
      // Open login sheet with next param via HTMX
      if (window.htmx) {
        htmx.ajax(
          "GET",
          `/auth/login_sheet?next=${encodeURIComponent(nextTarget)}`,
          { target: "#modal-root", swap: "beforeend" },
        );
      } else {
        // Fallback: navigate to canonical full page login when HTMX not available
        window.location.href = `/login?next=${encodeURIComponent(nextTarget)}`;
      }
    } else {
      // Trigger the global open-login button (already has scroll handling)
      loginButtons[0].click();
    }
  }
}

function extractCode(filename) {
  const match = filename.match(/_(.+?)_/);
  if (!match) return "";
  const code = match[1];
  return code;
}

function formatDuration(value) {
  if (!value) return "00:00:00";

  // Wenn value eine Zahl ist (Sekunden aus DB), konvertieren
  if (typeof value === "number") {
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const seconds = Math.floor(value % 60);
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }

  // Wenn value ein String ist, wie bisher verarbeiten
  const parts = value.split(":");
  if (parts.length < 3) return value;
  const seconds = parts[2].split(".")[0];
  return `${parts[0].padStart(2, "0")}:${parts[1].padStart(2, "0")}:${seconds.padStart(2, "0")}`;
}

function formatNumber(value) {
  if (typeof value !== "number") return value || "0";
  return value.toLocaleString("es-ES");
}

function renderLoginPrompt() {
  return `
    <div class="atlas-login-prompt">
      <p><strong>Autenticaci&oacute;n requerida.</strong> Inicia sesi&oacute;n para acceder al reproductor.</p>
    </div>
  `;
}

// renderOverview function removed - stats element no longer needed

function attachPlayerHandlers() {
  // Remove existing handler to avoid duplicate listeners
  if (filesContainer) {
    filesContainer.removeEventListener("click", handlePlayerLinkClick);
    filesContainer.addEventListener("click", handlePlayerLinkClick);
  }
}

function handlePlayerLinkClick(event) {
  const link = event.target.closest('[data-action="open-player"]');
  if (!link) return;

  event.preventDefault();
  event.stopPropagation();
  event.stopImmediatePropagation(); // Prevent other handlers

  const filename = link.dataset.filename;
  if (!filename) return;

  // Remove .json extension, then ensure no duplicate .mp3
  let baseName = filename.replace(".json", "");
  // If baseName already ends with .mp3, remove it (to avoid .mp3.mp3)
  if (baseName.endsWith(".mp3")) {
    baseName = baseName.slice(0, -4);
  }
  const transcriptionPath = `/media/transcripts/${baseName}.json`;
  const audioPath = `/media/full/${baseName}.mp3`;
  const playerUrl = `/player?transcription=${encodeURIComponent(transcriptionPath)}&audio=${encodeURIComponent(audioPath)}`;

  // Check auth status dynamically (in case user logged in)
  if (!isUserAuthenticated()) {
    // Save the intended destination in server session (more reliable than sessionStorage)
    fetch("/auth/save-redirect", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: playerUrl }),
      credentials: "same-origin",
    })
      .then(() => {
        // Open login sheet after saving redirect URL
        openLoginSheet(playerUrl);
      })
      .catch((error) => {
        console.error("Failed to save redirect URL:", error);
        // Fall back to opening login sheet without storing redirect server-side
        openLoginSheet(playerUrl);
      });
    return false;
  }

  window.location.href = playerUrl;
  return false;
}

// Render country tabs (like editor_overview)
function renderCountryTabs() {
  if (!tabsContainer || !fileMetadata.length) return;

  // Get unique country codes from files and sort alphabetically
  const countryCodes = [
    ...new Set(fileMetadata.map((item) => extractCode(item.filename))),
  ]
    .filter(Boolean)
    .sort();

  if (!countryCodes.length) {
    tabsContainer.innerHTML = "";
    return;
  }

  // Create tabs for each country (showing only country code)
  const tabs = countryCodes
    .map((code, index) => {
      return `
      <button class="md3-atlas-country-tab ${index === 0 ? "active" : ""}" 
              data-country="${code}"
              role="tab"
              aria-selected="${index === 0 ? "true" : "false"}"
              aria-controls="table-${code}">
        ${code}
      </button>
    `;
    })
    .join("");

  tabsContainer.innerHTML = tabs;

  // Attach tab click handlers
  attachTabHandlers();
}

// Attach click handlers to tabs
function attachTabHandlers() {
  if (!tabsContainer) return;

  const tabs = tabsContainer.querySelectorAll(".md3-atlas-country-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const code = tab.dataset.country;
      activateTab(code);
    });
  });
}

// Activate a specific tab and show its content
function activateTab(code) {
  if (!tabsContainer) return;

  // Update active tab
  const tabs = tabsContainer.querySelectorAll(".md3-atlas-country-tab");
  tabs.forEach((t) => {
    const isActive = t.dataset.country === code;
    t.classList.toggle("active", isActive);
    t.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  // Show corresponding table
  const containers = filesContainer.querySelectorAll(
    ".md3-atlas-files-table-container",
  );
  containers.forEach((container) => {
    container.classList.toggle("active", container.id === `table-${code}`);
  });

  // Update dropdowns (without triggering their change handlers)
  const city = CITY_LIST.find((c) => c.code === code);
  if (city) {
    if (city.type === "national" && selectNationalElement) {
      selectNationalElement.value = code;
      if (selectRegionalElement) selectRegionalElement.value = "ALL";
    } else if (city.type === "regional" && selectRegionalElement) {
      selectRegionalElement.value = code;
      if (selectNationalElement) selectNationalElement.value = "ALL";
    }
  }

  // Focus map on city
  focusCity(code);
}

function renderCityTables(code = "ALL") {
  if (!filesContainer) return;

  if (!fileMetadata.length) {
    filesContainer.innerHTML =
      '<p class="md3-atlas-empty">No hay registros disponibles en este momento.</p>';
    tabsContainer.innerHTML = "";
    return;
  }

  // Get unique country codes from files
  const countryCodes = [
    ...new Set(fileMetadata.map((item) => extractCode(item.filename))),
  ].filter(Boolean);

  if (!countryCodes.length) {
    filesContainer.innerHTML =
      '<p class="md3-atlas-empty">No hay registros disponibles en este momento.</p>';
    tabsContainer.innerHTML = "";
    return;
  }

  // Render tabs
  renderCountryTabs();

  // Render all country tables (as hidden containers)
  const allTables = countryCodes
    .map((countryCode, index) => {
      const city = CITY_LIST.find((c) => c.code === countryCode);
      if (!city) return "";

      const entries = fileMetadata.filter(
        (item) => extractCode(item.filename) === countryCode,
      );
      if (!entries.length) return "";

      const rows = entries
        .map(
          (item) => `
        <tr>
          <td>${item.date}</td>
          <td>${item.radio}</td>
          <td><button type="button" class="atlas-player-link" data-action="open-player" data-filename="${item.filename}">${item.filename.replace(".json", "")}</button></td>
          <td class="right-align">${formatDuration(item.duration)}</td>
          <td class="right-align">${formatNumber(item.word_count)}</td>
        </tr>
      `,
        )
        .join("");

      return `
      <div class="md3-atlas-files-table-container ${index === 0 ? "active" : ""}" 
           id="table-${countryCode}"
           role="tabpanel">
        <article class="md3-atlas-city-block">
          <h3 class="md3-atlas-city-block__title">${city.label}</h3>
          <div class="md3-atlas-table-wrapper">
            <table class="md3-atlas-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Emisora</th>
                  <th>Audio / Transcripci\u00f3n</th>
                  <th class="right-align">Duraci\u00f3n</th>
                  <th class="right-align">Palabras</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </article>
      </div>
    `;
    })
    .filter(Boolean)
    .join("");

  if (!allTables) {
    filesContainer.innerHTML =
      '<p class="md3-atlas-empty">No hay registros disponibles en este momento.</p>';
    tabsContainer.innerHTML = "";
    return;
  }

  filesContainer.innerHTML = allTables;
  attachPlayerHandlers();

  // If a specific code was requested, activate that tab
  if (code && code !== "ALL") {
    activateTab(code);
  }
}

function populateDropdown() {
  // Populate National Capital Dropdown
  if (selectNationalElement) {
    selectNationalElement.innerHTML = "";
    const defaultOptionNational = document.createElement("option");
    defaultOptionNational.value = "ALL";
    defaultOptionNational.textContent = "Elige capital";
    selectNationalElement.appendChild(defaultOptionNational);

    CITY_LIST.filter((city) => city.type === "national").forEach((city) => {
      const option = document.createElement("option");
      option.value = city.code;
      option.textContent = city.label;
      selectNationalElement.appendChild(option);
    });
  }

  // Populate Regional Capital Dropdown
  if (selectRegionalElement) {
    selectRegionalElement.innerHTML = "";
    const defaultOptionRegional = document.createElement("option");
    defaultOptionRegional.value = "ALL";
    defaultOptionRegional.textContent = "Elige capital";
    selectRegionalElement.appendChild(defaultOptionRegional);

    CITY_LIST.filter((city) => city.type === "regional").forEach((city) => {
      const option = document.createElement("option");
      option.value = city.code;
      option.textContent = city.label;
      selectRegionalElement.appendChild(option);
    });
  }
}

function focusCity(code) {
  if (!mapInstance) return;
  if (code === "ALL") {
    mapInstance.flyTo(getInitialCenter(), getInitialZoom());
    return;
  }
  const marker = cityMarkers.get(code);
  if (marker) {
    marker.openPopup();
    mapInstance.flyTo(marker.getLatLng(), 4);
  }
}

function addCityMarkers() {
  if (!window.L || !MAP_CONTAINER) return;
  CITY_LIST.forEach((city) => {
    const config = MARKER_ICONS[city.tier] || MARKER_ICONS.primary;
    const icon = window.L.icon({
      iconUrl: `${config.path}${config.file}`,
      iconSize: config.iconSize,
      iconAnchor: config.iconAnchor,
      popupAnchor: [0, -config.iconAnchor[1]],
    });
    const marker = window.L.marker([city.lat, city.lng], { icon }).addTo(
      mapInstance,
    );
    marker.bindPopup(city.label);
    marker.on("click", () => {
      // Update the appropriate select based on city type
      if (city.type === "national" && selectNationalElement) {
        selectNationalElement.value = city.code;
        if (selectRegionalElement) selectRegionalElement.value = "ALL";
      } else if (city.type === "regional" && selectRegionalElement) {
        selectRegionalElement.value = city.code;
        if (selectNationalElement) selectNationalElement.value = "ALL";
      }
      activateTab(city.code);
    });
    cityMarkers.set(city.code, marker);
  });
}

function initMap() {
  if (!window.L || !MAP_CONTAINER) return;
  const center = getInitialCenter();
  mapInstance = window.L.map(MAP_CONTAINER, {
    center,
    zoom: getInitialZoom(),
    attributionControl: false,
  });
  window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(mapInstance);
  addCityMarkers();
  setTimeout(() => mapInstance.invalidateSize(), 200);
  window.addEventListener("resize", () => {
    setTimeout(() => {
      mapInstance.invalidateSize();
      const nationalIsAll =
        !selectNationalElement || selectNationalElement.value === "ALL";
      const regionalIsAll =
        !selectRegionalElement || selectRegionalElement.value === "ALL";
      if (nationalIsAll && regionalIsAll) {
        mapInstance.flyTo(getInitialCenter(), getInitialZoom());
      }
    }, 200);
  });
}

async function loadFiles() {
  try {
    const response = await fetch("/api/v1/atlas/files", {
      credentials: "same-origin",
    });
    if (response.status === 401) {
      if (filesContainer) {
        filesContainer.innerHTML = renderLoginPrompt();
      }
      return [];
    }
    if (!response.ok) {
      throw new Error("No se pudieron obtener los metadatos de audio.");
    }
    const data = await response.json();
    return Array.isArray(data.files) ? data.files : [];
  } catch (error) {
    console.error("Error loading files:", error);
    // Don't show login prompt for network/server errors (Atlas data is public)
    // Login prompt only shown for 401 (handled above)
    if (filesContainer) {
      filesContainer.innerHTML =
        '<div class="alert alert-warning">Error cargando archivos. Por favor recarga la página.</div>';
    }
    return [];
  }
}

async function bootstrap() {
  populateDropdown();
  initMap();
  const [overviewRes, countriesRes, filesRes] = await Promise.all([
    fetch("/api/v1/atlas/overview")
      .then((res) => (res.ok ? res.json() : null))
      .catch(() => null),
    fetch("/api/v1/atlas/countries")
      .then((res) => (res.ok ? res.json() : null))
      .catch(() => null),
    loadFiles(),
  ]);
  overviewStats = overviewRes || null;
  countryStats = countriesRes?.countries || [];
  fileMetadata = filesRes;
  renderCityTables("ALL");
}

function setupEventListeners() {
  if (selectNationalElement) {
    selectNationalElement.addEventListener("change", (event) => {
      const code = event.target.value;
      // Reset regional select
      if (selectRegionalElement && code !== "ALL") {
        selectRegionalElement.value = "ALL";
      }

      if (code !== "ALL") {
        activateTab(code);
      }
    });
  }

  if (selectRegionalElement) {
    selectRegionalElement.addEventListener("change", (event) => {
      const code = event.target.value;
      // Reset national select
      if (selectNationalElement && code !== "ALL") {
        selectNationalElement.value = "ALL";
      }

      if (code !== "ALL") {
        activateTab(code);
      }
    });
  }
}

/**
 * Initialize Atlas module
 * Called by app.js after Leaflet is loaded
 * @returns {object} mapInstance for cleanup
 */
export function init() {
  console.log("[Atlas Module] Initializing...");

  // Get DOM elements
  MAP_CONTAINER = document.getElementById("atlas-map");
  selectNationalElement = document.querySelector(
    '[data-element="atlas-select-national"]',
  );
  selectRegionalElement = document.querySelector(
    '[data-element="atlas-select-regional"]',
  );
  filesContainer = document.querySelector('[data-element="atlas-files"]');
  tabsContainer = document.querySelector('[data-element="atlas-country-tabs"]');
  loginSheet = document.querySelector('[data-element="login-sheet"]');
  loginButtons = document.querySelectorAll('[data-action="open-login"]');

  // Check if we have the required elements
  if (!MAP_CONTAINER) {
    console.warn("[Atlas Module] Map container not found");
    return null;
  }

  // Setup event listeners
  setupEventListeners();

  // Bootstrap the atlas
  bootstrap();

  // Return map instance for cleanup
  return mapInstance;
}
