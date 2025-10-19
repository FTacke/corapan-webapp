const MAP_CONTAINER = document.getElementById('atlas-map');
const selectElement = document.querySelector('[data-element="atlas-select"]');
const filesContainer = document.querySelector('[data-element="atlas-files"]');
const overviewContainer = document.querySelector('[data-element="atlas-overview"]');
const headerRoot = document.querySelector('.site-header');
const loginSheet = document.querySelector('[data-element="login-sheet"]');
const loginButtons = document.querySelectorAll('[data-action="open-login"]');

const CITY_LIST = [
  { code: 'ARG', label: 'Argentina: Buenos Aires', lat: -34.6118, lng: -58.4173, tier: 'primary' },
  { code: 'ARG-Cht', label: 'Argentina: Trelew (Chubut)', lat: -43.2489, lng: -65.3051, tier: 'secondary' },
  { code: 'ARG-Cba', label: 'Argentina: Cordoba (Cordoba)', lat: -31.4201, lng: -64.1888, tier: 'secondary' },
  { code: 'ARG-SdE', label: 'Argentina: Santiago del Estero', lat: -27.7951, lng: -64.2615, tier: 'secondary' },
  { code: 'BOL', label: 'Bolivia: La Paz', lat: -16.5, lng: -68.15, tier: 'primary' },
  { code: 'CHI', label: 'Chile: Santiago', lat: -33.4489, lng: -70.6693, tier: 'primary' },
  { code: 'COL', label: 'Colombia: Bogota', lat: 4.6097, lng: -74.0817, tier: 'primary' },
  { code: 'CR', label: 'Costa Rica: San Jose', lat: 9.9281, lng: -84.0907, tier: 'primary' },
  { code: 'CUB', label: 'Cuba: La Habana', lat: 23.133, lng: -82.383, tier: 'primary' },
  { code: 'ECU', label: 'Ecuador: Quito', lat: -0.23, lng: -78.52, tier: 'primary' },
  { code: 'ES-CAN', label: 'Espa\u00f1a: La Laguna (Canarias)', lat: 28.4874, lng: -16.3141, tier: 'secondary' },
  { code: 'ES-SEV', label: 'Espa\u00f1a: Sevilla (Andaluc\u00eda)', lat: 37.3886, lng: -5.9823, tier: 'secondary' },
  { code: 'ES-MAD', label: 'Espa\u00f1a: Madrid', lat: 40.4168, lng: -3.7038, tier: 'primary' },
  { code: 'GUA', label: 'Guatemala: Ciudad de Guatemala', lat: 14.6349, lng: -90.5069, tier: 'primary' },
  { code: 'HON', label: 'Honduras: Tegucigalpa', lat: 14.0723, lng: -87.1921, tier: 'primary' },
  { code: 'MEX', label: 'M\u00e9xico: Ciudad de M\u00e9xico', lat: 19.4326, lng: -99.1332, tier: 'primary' },
  { code: 'NIC', label: 'Nicaragua: Managua', lat: 12.1364, lng: -86.2514, tier: 'primary' },
  { code: 'PAN', label: 'Panam\u00e1: Ciudad de Panam\u00e1', lat: 8.9824, lng: -79.5199, tier: 'primary' },
  { code: 'PAR', label: 'Paraguay: Asunci\u00f3n', lat: -25.2637, lng: -57.5759, tier: 'primary' },
  { code: 'PER', label: 'Per\u00fa: Lima', lat: -12.0464, lng: -77.0428, tier: 'primary' },
  { code: 'RD', label: 'Rep\u00fablica Dominicana: Santo Domingo', lat: 18.4663, lng: -69.9526, tier: 'primary' },
  { code: 'SAL', label: 'El Salvador: San Salvador', lat: 13.6929, lng: -89.2182, tier: 'primary' },
  { code: 'URU', label: 'Uruguay: Montevideo', lat: -34.9011, lng: -56.191, tier: 'primary' },
  { code: 'VEN', label: 'Venezuela: Caracas', lat: 10.5, lng: -66.9333, tier: 'primary' }
];

const MARKER_ICONS = {
  primary: {
    path: '/static/img/citymarkers/primary/',
    file: 'communications-tower.svg',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  },
  secondary: {
    path: '/static/img/citymarkers/secondary/',
    file: 'communications-tower.svg',
    iconSize: [25, 25],
    iconAnchor: [17, 17],
  },
};

let isAuthenticated = headerRoot?.dataset.auth === 'true';
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

function openLoginSheet() {
  if (loginSheet) {
    // Save current scroll position
    const scrollY = window.scrollY || window.pageYOffset;
    
    // Lock body scroll position using CSS variable (prevents jump when overflow:hidden is applied)
    document.body.style.setProperty('--scroll-lock-offset', `-${scrollY}px`);
    
    loginSheet.hidden = false;
    document.body.classList.add('login-open');
    
    // Focus input without scrolling
    const input = loginSheet.querySelector('input[name="username"]');
    if (input) {
      input.focus({ preventScroll: true });
    }
  } else if (loginButtons.length) {
    // Trigger the global open-login button (already has scroll handling)
    loginButtons[0].dispatchEvent(new Event('click', { bubbles: true }));
  }
}

function extractCode(filename) {
  const match = filename.match(/_(.+?)_/);
  return match ? match[1] : '';
}

function formatDuration(value) {
  if (!value) return '00:00:00';
  
  // Wenn value eine Zahl ist (Sekunden aus DB), konvertieren
  if (typeof value === 'number') {
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const seconds = Math.floor(value % 60);
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  }
  
  // Wenn value ein String ist, wie bisher verarbeiten
  const parts = value.split(':');
  if (parts.length < 3) return value;
  const seconds = parts[2].split('.')[0];
  return `${parts[0].padStart(2, '0')}:${parts[1].padStart(2, '0')}:${seconds.padStart(2, '0')}`;
}

function formatNumber(value) {
  if (typeof value !== 'number') return value || '0';
  return value.toLocaleString('es-ES');
}

function renderLoginPrompt() {
  return `
    <div class="atlas-login-prompt">
      <p><strong>Autenticaci&oacute;n requerida.</strong> Inicia sesi&oacute;n para acceder al reproductor.</p>
    </div>
  `;
}

function renderOverview() {
  if (!overviewContainer) return;
  if (!overviewStats) {
    overviewContainer.innerHTML = '<p class="md3-body-small" style="color: var(--md3-color-on-surface-variant); margin: 0;">Cargando...</p>';
    return;
  }
  const totalHours = formatDuration(overviewStats.total_duration_all || 0);
  const totalWords = formatNumber(overviewStats.total_word_count || 0);
  
  overviewContainer.innerHTML = `
    <div class="md3-atlas-stat">
      <span class="md3-atlas-stat__label">Horas:</span>
      <span class="md3-atlas-stat__value">${totalHours}</span>
    </div>
    <div class="md3-atlas-stat">
      <span class="md3-atlas-stat__label">Palabras:</span>
      <span class="md3-atlas-stat__value">${totalWords}</span>
    </div>
  `;
}

function attachPlayerHandlers() {
  if (!filesContainer) return;
  const links = filesContainer.querySelectorAll('[data-action="open-player"]');
  
  links.forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation(); // Prevent event bubbling
      
      const filename = link.dataset.filename;
      if (!filename) return;
      
      if (!isAuthenticated) {
        openLoginSheet();
        return;
      }
      
      const baseName = filename.replace('.json', '');
      const transcriptionPath = `/media/transcripts/${baseName}.json`;
      const audioPath = `/media/full/${baseName}.mp3`;
      window.location.href = `/player?transcription=${encodeURIComponent(transcriptionPath)}&audio=${encodeURIComponent(audioPath)}`;
    }, { once: true });
  });
}

function renderCityTables(code = 'ALL') {
  if (!filesContainer) return;
  // Atlas data is public - no login prompt needed here
  // Login will be required only when clicking on a player link
  if (!fileMetadata.length) {
    filesContainer.innerHTML = '<p class="md3-atlas-empty">No hay registros disponibles en este momento.</p>';
    return;
  }

  const renderForCity = (city) => {
    const entries = fileMetadata.filter((item) => extractCode(item.filename) === city.code);
    if (!entries.length) return '';
    const rows = entries
      .map((item) => `
        <tr>
          <td>${item.date}</td>
          <td>${item.radio}</td>
          <td><a href="javascript:void(0)" data-action="open-player" data-filename="${item.filename}">${item.filename.replace('.json', '')}</a></td>
          <td class="right-align">${formatDuration(item.duration)}</td>
          <td class="right-align">${formatNumber(item.word_count)}</td>
        </tr>
      `)
      .join('');
    return `
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
    `;
  };

  let markup = '';
  if (code && code !== 'ALL') {
    const selected = CITY_LIST.find((item) => item.code === code);
    if (!selected) {
      filesContainer.innerHTML = '<p class=\"md3-atlas-empty\">No se ha encontrado la capital solicitada.</p>';
      return;
    }
    markup = renderForCity(selected) || '<p class="md3-atlas-empty">No hay registros disponibles para esta capital.</p>';
  } else {
    markup = CITY_LIST.map(renderForCity).filter(Boolean).join('');
    if (!markup) {
      markup = '<p class=\"md3-atlas-empty\">No hay registros disponibles en este momento.</p>';
    }
  }
  // Atlas data is public - display directly without login prompt
  filesContainer.innerHTML = markup;
  attachPlayerHandlers();
}

function populateDropdown() {
  if (!selectElement) return;
  selectElement.innerHTML = '';
  const defaultOption = document.createElement('option');
  defaultOption.value = 'ALL';
  defaultOption.textContent = 'Todas las capitales';
  selectElement.appendChild(defaultOption);
  CITY_LIST.forEach((city) => {
    const option = document.createElement('option');
    option.value = city.code;
    option.textContent = city.label;
    selectElement.appendChild(option);
  });
}

function focusCity(code) {
  if (!mapInstance) return;
  if (code === 'ALL') {
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
    const marker = window.L.marker([city.lat, city.lng], { icon }).addTo(mapInstance);
    marker.bindPopup(city.label);
    marker.on('click', () => {
      if (selectElement) {
        selectElement.value = city.code;
      }
      renderCityTables(city.code);
      focusCity(city.code);
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
  window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(mapInstance);
  addCityMarkers();
  setTimeout(() => mapInstance.invalidateSize(), 200);
  window.addEventListener('resize', () => {
    setTimeout(() => {
      mapInstance.invalidateSize();
      if (!selectElement || selectElement.value === 'ALL') {
        mapInstance.flyTo(getInitialCenter(), getInitialZoom());
      }
    }, 200);
  });
}

async function loadFiles() {
  try {
    const response = await fetch('/api/v1/atlas/files', { credentials: 'same-origin' });
    if (response.status === 401) {
      isAuthenticated = false;
      if (filesContainer) {
        filesContainer.innerHTML = renderLoginPrompt();
      }
      return [];
    }
    if (!response.ok) {
      throw new Error('No se pudieron obtener los metadatos de audio.');
    }
    const data = await response.json();
    isAuthenticated = true;
    return Array.isArray(data.files) ? data.files : [];
  } catch (error) {
    console.error('Error loading files:', error);
    // Don't show login prompt for network/server errors (Atlas data is public)
    // Login prompt only shown for 401 (handled above)
    if (filesContainer) {
      filesContainer.innerHTML = '<div class="alert alert-warning">Error cargando archivos. Por favor recarga la página.</div>';
    }
    return [];
  }
}

async function bootstrap() {
  populateDropdown();
  initMap();
  const [overviewRes, countriesRes, filesRes] = await Promise.all([
    fetch('/api/v1/atlas/overview').then((res) => (res.ok ? res.json() : null)).catch(() => null),
    fetch('/api/v1/atlas/countries').then((res) => (res.ok ? res.json() : null)).catch(() => null),
    loadFiles(),
  ]);
  overviewStats = overviewRes || null;
  countryStats = countriesRes?.countries || [];
  fileMetadata = filesRes;
  renderOverview();
  renderCityTables('ALL');
}

if (selectElement) {
  selectElement.addEventListener('change', (event) => {
    const code = event.target.value;
    renderCityTables(code);
    focusCity(code);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  bootstrap();
});
