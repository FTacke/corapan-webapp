/**
 * Token-Tab Module (MD3 Filter Chips)
 * Ersetzt Tagify mit nativer MD3-konformer Chip-Implementierung
 * 
 * Features:
 * - Alphanumerische Token-IDs (Hashes)
 * - Deduplizierung (jede ID nur einmal)
 * - Visuelle Kürzung auf 8 Zeichen (voller Hash im Tooltip)
 * - DataTables-Integration via initTokenTable.js (serverSide)
 * - 1:1 Mirror der Advanced Search Konfiguration
 */

import { initTokenTable, reloadTokenTable, destroyTokenTable } from './initTokenTable.js';

// ===========================
// State Management
// ===========================

let tokIds = []; // Array of normalized token IDs

// ===========================
// Normalization & Validation
// ===========================

/**
 * Normalisiert Token-ID (lowercase, trim)
 */
function normalizeTokId(str) {
  return str.trim().toLowerCase();
}

/**
 * Validiert Token-ID Format (alphanumerisch, mindestens 1 Zeichen)
 * Erlaubt: 0-9, a-z, A-Z
 */
function isValidTokId(str) {
  return /^[0-9a-z]+$/i.test(str);
}

/**
 * Kürzt Token-ID auf 8 Zeichen für Anzeige
 */
function shortenId(id) {
  return id.length <= 8 ? id : id.slice(0, 8) + '…';
}

// ===========================
// Hidden Input Update
// ===========================

/**
 * Aktualisiert Hidden-Input mit aktuellem Token-ID-Array
 */
function updateTokidHidden() {
  const hiddenInput = document.getElementById('tokid-hidden');
  if (hiddenInput) {
    hiddenInput.value = tokIds.join(',');
  }
}

// ===========================
// Chip Rendering
// ===========================

/**
 * Rendert alle Token-ID-Chips neu
 */
function renderTokidChips() {
  const container = document.getElementById('tokid-chip-container');
  if (!container) return;
  // Prepare container: remove only chip items, keep count label
  container.innerHTML = '';

  // Add count label
  const countLabel = document.createElement('span');
  countLabel.id = 'tokid-count';
  countLabel.className = 'md3-active-filters__label tokid-count';
  container.appendChild(countLabel);

  // Chips wrapper
  const itemsWrap = document.createElement('div');
  itemsWrap.id = 'tokid-chip-items';
  itemsWrap.className = 'md3-active-filters__chips tokid-chips-wrap';
  container.appendChild(itemsWrap);

  // Toggle empty class
  if (tokIds.length === 0) {
    container.classList.add('tokid-chip-container--empty');
  } else {
    container.classList.remove('tokid-chip-container--empty');
  }

  // Chips erstellen
  tokIds.forEach(id => {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'tokid-chip';
    chip.dataset.id = id;
    chip.title = id; // Voller Hash als Tooltip

    chip.innerHTML = `
      <span class="tokid-chip__label">${shortenId(id)}</span>
      <span class="tokid-chip__trailing" role="button" aria-label="Entfernen" tabindex="0">×</span>
    `;

    itemsWrap.appendChild(chip);
  });

  // Counter aktualisieren
  updateTokenCount();
}

/**
 * Aktualisiert Token-Counter
 */
function updateTokenCount() {
  const countElement = document.getElementById('tokid-count');
  if (countElement) {
    const count = tokIds.length;
    countElement.textContent = `IDs: ${count}`;
  }
}

// ===========================
// Add Token IDs
// ===========================

/**
 * Fügt Token-IDs aus Input hinzu
 */
function addTokidFromInput() {
  const input = document.getElementById('tokid-input');
  if (!input) return;

  const raw = input.value.trim();
  if (!raw) return;

  // Parse multiple IDs (separiert durch Komma, Semikolon oder Whitespace)
  const parts = raw.split(/[,;]|\s+/).map(p => p.trim()).filter(Boolean);

  let changed = false;
  for (let p of parts) {
    const norm = normalizeTokId(p);
    if (!isValidTokId(norm)) {
      console.warn(`Ungültige Token-ID ignoriert: "${p}"`);
      continue;
    }
    if (!tokIds.includes(norm)) {
      tokIds.push(norm);
      changed = true;
    }
  }

  if (changed) {
    updateTokidHidden();
    renderTokidChips();
    reloadTokenDataTable();
  }

  // Input leeren
  input.value = '';
}

// ===========================
// Remove Token IDs
// ===========================

/**
 * Entfernt einzelne Token-ID
 */
function removeTokid(id) {
  const index = tokIds.indexOf(id);
  if (index > -1) {
    tokIds.splice(index, 1);
    updateTokidHidden();
    renderTokidChips();
    reloadTokenDataTable();
  }
}

/**
 * Entfernt alle Token-IDs
 */
function clearAllTokens() {
  tokIds = [];
  updateTokidHidden();
  renderTokidChips();
  
  // Destroy DataTable
  destroyTokenTable();
  
  // Hide results section
  const resultsSection = document.getElementById('token-results');
  if (resultsSection) {
    resultsSection.style.display = 'none';
  }
}

// ===========================
// DataTables Integration
// ===========================

/**
 * Lädt DataTable neu (delegiert an initTokenTable.js)
 */
function reloadTokenDataTable() {
  if (tokIds.length === 0) {
    console.warn('[Token] No token IDs to reload');
    return;
  }
  reloadTokenTable(tokIds);
}

/**
 * Initialisiert DataTables-Instanz (delegiert an initTokenTable.js)
 * 1:1 Mirror der Advanced Search Konfiguration
 */
function initializeTokenDataTable() {
  // Validierung
  if (tokIds.length === 0) {
    alert('Por favor ingresa al menos un Token-ID');
    return;
  }

  const tableElement = document.getElementById('token-results-table');
  if (!tableElement) {
    console.error('[Token] Table element #token-results-table not found');
    return;
  }

  console.log('[Token] Initializing DataTable with', tokIds.length, 'token IDs');
  
  // Delegiere zu initTokenTable.js (1:1 Mirror von Advanced Search)
  initTokenTable(tokIds);
  
  // Show results section
  const resultsSection = document.getElementById('token-results');
  if (resultsSection) {
    resultsSection.style.display = 'block';
  }
}

// ===========================
// Event Handlers
// ===========================

/**
 * Initialisiert Event-Listener
 */
function initializeEventHandlers() {
  // Add Button
  const addBtn = document.getElementById('tokid-add-btn');
  if (addBtn) {
    addBtn.addEventListener('click', addTokidFromInput);
  }

  // Enter-Key im Input
  const input = document.getElementById('tokid-input');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addTokidFromInput();
      }
    });
  }

  // Chip-Container (Event Delegation für Remove-Buttons)
  const chipContainer = document.getElementById('tokid-chip-container');
  if (chipContainer) {
    chipContainer.addEventListener('click', (e) => {
      const deleteBtn = e.target.closest('.tokid-chip__trailing');
      if (!deleteBtn) return;
      const chip = deleteBtn.closest('.tokid-chip');
      if (!chip) return;
      const id = chip.dataset.id;
      if (id) {
        removeTokid(id);
      }
    });
    // Keyboard support for trailing remove button
    chipContainer.addEventListener('keydown', (e) => {
      const deleteBtn = e.target.closest('.tokid-chip__trailing');
      if (!deleteBtn) return;
      if (e.key !== 'Enter' && e.key !== ' ') return;
      e.preventDefault();
      const chip = deleteBtn.closest('.tokid-chip');
      if (!chip) return;
      const id = chip.dataset.id;
      if (id) {
        removeTokid(id);
      }
    });
  }

  // Search Button
  const searchBtn = document.getElementById('token-search-btn');
  if (searchBtn) {
    searchBtn.addEventListener('click', () => {
      initializeTokenDataTable();
    });
  }

  // Clear Button
  const clearBtn = document.getElementById('clear-tokens-btn');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (tokIds.length > 0) {
        if (confirm('¿Borrar todos los Token-IDs?')) {
          clearAllTokens();
        }
      }
    });
  }
}

// ===========================
// Initialization
// ===========================

/**
 * Initialisiert Token-Tab
 */
function initializeTokenTab() {
  console.log('🔧 Initializing Token Tab (MD3 Chips)...');
  
  // Event-Handler registrieren
  initializeEventHandlers();
  
  // Initial render (leer)
  renderTokidChips();
  // Initialize token sub-tabs if present
  initializeTokenSubTabs();
  
  console.log('✅ Token Tab initialized');
}

/**
 * Initialize token tab sub-tabs (Resultados | Estadísticas)
 * Re-uses the same markup/styling as the advanced search sub-tabs
 * The statistics tab is currently inactive (display a small message)
 */
function initializeTokenSubTabs() {
  const sub = document.getElementById('token-sub-tabs');
  if (!sub) return;

  const btnResult = sub.querySelector('[data-view="results"]');
  const btnStats = sub.querySelector('[data-view="stats"]');
  const panelResults = document.getElementById('token-panel-resultados');
  const panelStats = document.getElementById('token-panel-estadisticas');

  // Ensure statistics tab remains inactive by default
  if (btnStats) {
    btnStats.setAttribute('aria-disabled', 'true');
    btnStats.classList.remove('md3-stats-tab--active');
  }

  if (btnResult && panelResults) {
    btnResult.addEventListener('click', () => {
      // Activate Results / hide Stats
      if (btnStats) btnStats.classList.remove('md3-stats-tab--active');
      btnResult.classList.add('md3-stats-tab--active');
      if (panelResults) {
        panelResults.classList.add('md3-view-content--active');
        panelResults.removeAttribute('hidden');
      }
      if (panelStats) {
        panelStats.classList.remove('md3-view-content--active');
        panelStats.setAttribute('hidden', '');
      }
    });
  }

  if (btnStats && panelStats) {
    // Clicking stats shows a small message in the stats panel
    btnStats.addEventListener('click', () => {
      // If the button is aria-disabled, do nothing
      if (btnStats.getAttribute('aria-disabled') === 'true') {
        // Toggle a tooltip or temporary message to inform user that it's not implemented
        panelStats.innerHTML = `<div class="md3-body-medium" style="padding: 1rem;">Estadísticas no implementadas todavía.</div>`;
        // Show the small message briefly then switch back to results
        panelStats.classList.add('md3-view-content--active');
        panelStats.removeAttribute('hidden');
        setTimeout(() => {
          panelStats.classList.remove('md3-view-content--active');
          panelStats.setAttribute('hidden', '');
        }, 2000);
        return;
      }

      // Normal behavior (not used currently)
      btnResult.classList.remove('md3-stats-tab--active');
      btnStats.classList.add('md3-stats-tab--active');
      if (panelResults) panelResults.classList.remove('md3-view-content--active');
      if (panelStats) panelStats.classList.add('md3-view-content--active');
    });
  }
}

// DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeTokenTab);
} else {
  initializeTokenTab();
}

// Export für externe Nutzung (optional)
window.TokenTab = {
  addTokenIds: (ids) => {
    ids.forEach(id => {
      const norm = normalizeTokId(id);
      if (isValidTokId(norm) && !tokIds.includes(norm)) {
        tokIds.push(norm);
      }
    });
    updateTokidHidden();
    renderTokidChips();
  },
  clearTokens: clearAllTokens,
  getTokenIds: () => [...tokIds]
};
