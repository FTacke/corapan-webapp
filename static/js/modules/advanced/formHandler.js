/**
 * Advanced Search Form Handler
 * Manages form submission, reset, and filter/query parameter building
 * 
 * Responsibilities:
 * - Restore form state from URL parameters BEFORE Select2 init
 * - Expert-Toggle: Show/Hide CQL-Raw field, sync mode to CQL
 * - Prevent default form submit
 * - Build query parameters from form controls
 * - Initialize Select2 for filter dropdowns
 * - Handle reset button
 * - Update DataTables on submit
 * - Update export buttons with current parameters
 */

import { initAdvancedTable, updateExportButtons, updateSummary } from './initTable.js';
import { CorpusFiltersManager } from '../corpus/filters.js';

// Track filter manager and initialization state
let filtersManager = null;
let resultsLoaded = false;
let isInitialized = false;

/**
 * Main initialization function
 * Called on both DOMContentLoaded and turbo:load
 * Idempotent - guards against multiple initializations
 */
function initFormHandler() {
  // Guard: jQuery must be present
  if (typeof window.$ === 'undefined' || typeof window.jQuery === 'undefined') {
    console.error('[Advanced] jQuery not loaded, cannot initialize');
    return;
  }
  
  // Guard: Prevent double-initialization
  if (isInitialized) {
    console.log('[Advanced] Already initialized, skipping');
    return;
  }
  
  // Check if we're on the advanced search page
  const form = document.getElementById('adv-form');
  if (!form) {
    console.log('[Advanced] Form not found, skipping initialization');
    return;
  }
  
  console.log('[Advanced] Initializing form handler');
  
  // Step 1: Restore form state from URL BEFORE Select2 init
  // This ensures values are pre-filled before Select2 renders
  restoreStateFromURL();
  
  // Step 2: Initialize filters with Select2
  initializeFilters();
  
  // Step 3: Bind Expert Toggle
  bindExpertToggle();
  
  // Step 3.5: Apply initial CQL visibility (after URL restore)
  applyCqlVisibility();
  
  // Step 3.6: Bind mode change handler
  bindModeChange();
  
  // Step 4: Bind form submit
  bindFormSubmit();
  
  // Step 5: Bind reset button
  bindResetButton();
  
  isInitialized = true;
  console.log('✅ Advanced form handler ready');
}

/**
 * Cleanup function called before Turbo caches the page
 * Destroys Select2 instances to prevent memory leaks
 */
function cleanupFormHandler() {
  if (!isInitialized) return;
  
  console.log('[Advanced] Cleaning up before Turbo cache');
  
  // Destroy Select2 instances
  if (filtersManager) {
    filtersManager.cleanup?.();
  }
  
  isInitialized = false;
  resultsLoaded = false;
}

// Standard page load
document.addEventListener('DOMContentLoaded', initFormHandler);

// Turbo page load (for Turbo Drive navigation)
document.addEventListener('turbo:load', initFormHandler);

// Turbo cleanup (before page is cached)
document.addEventListener('turbo:before-cache', cleanupFormHandler);

// HTMX afterSwap event (for dynamic content swaps)
document.addEventListener('htmx:afterSwap', (e) => {
  const target = e.target || e.detail?.target;
  if (target && (target.id === 'adv-form' || target.querySelector?.('#adv-form'))) {
    console.log('[Advanced] HTMX swap detected, re-initializing');
    isInitialized = false;
    initFormHandler();
  }
});

/**
 * Initialize filters with Select2
 */
function initializeFilters() {
  filtersManager = new CorpusFiltersManager();
  filtersManager.initialize();
}

/**
 * Restore form state from URL query parameters
 * Executes BEFORE Select2 initialization
 * Enables bookmarkable/shareable search URLs and browser back/forward
 */
function restoreStateFromURL() {
  const params = new URLSearchParams(window.location.search);
  const form = document.getElementById('adv-form');
  if (!form) return;
  
  console.log('[URL] Restoring state from:', window.location.search);
  
  // Restore text inputs
  const q = params.get('q');
  if (q) {
    form.querySelector('#q').value = q;
    console.log('[URL] Restored q:', q);
  }
  
  const mode = params.get('mode');
  if (mode) {
    form.querySelector('#mode').value = mode;
  }
  
  // Restore Expert toggle and CQL raw
  const expert = params.get('expert');
  if (expert === '1' || expert === 'true') {
    form.querySelector('#expert').checked = true;
    const cqlRow = document.getElementById('cql-row');
    if (cqlRow) cqlRow.hidden = false;
  }
  
  const cqlRaw = params.get('cql_raw');
  if (cqlRaw) {
    form.querySelector('#cql_raw').value = cqlRaw;
  }
  
  // Restore sensitive checkbox
  const sensitive = params.get('sensitive');
  if (sensitive === '1' || sensitive === 'true') {
    form.querySelector('#sensitive').checked = true;
  } else if (sensitive === '0' || sensitive === 'false') {
    form.querySelector('#sensitive').checked = false;
  }
  
  const includeRegional = params.get('include_regional');
  if (includeRegional === '1') {
    form.querySelector('#include-regional').checked = true;
  }
  
  // Restore multi-select filters BEFORE Select2 initialization
  // Select2 will pick up the pre-selected options
  const filterMappings = [
    { param: 'country_code', selector: '#filter-country-code' },
    { param: 'speaker_type', selector: '#filter-speaker-type' },
    { param: 'sex', selector: '#filter-sex' },
    { param: 'speech_mode', selector: '#filter-speech-mode' },
    { param: 'discourse', selector: '#filter-discourse' },
  ];
  
  filterMappings.forEach(({ param, selector }) => {
    const values = params.getAll(param);
    if (values.length > 0) {
      const selectElement = form.querySelector(selector);
      if (selectElement) {
        // Pre-select options BEFORE Select2 init
        Array.from(selectElement.options).forEach(opt => {
          opt.selected = values.includes(opt.value);
        });
        console.log(`[URL] Restored ${selector}:`, values);
      }
    }
  });
  
  // If URL contains search params, auto-submit the form after initialization
  if (q && params.size > 0) {
    console.log('[URL] Auto-submitting form from URL');
    setTimeout(() => {
      form.dispatchEvent(new Event('submit'));
    }, 200);  // Delay for Select2 to be ready
  }
}

/**
 * Apply CQL row visibility based on Expert checkbox state
 * Called on page load after URL restore
 */
function applyCqlVisibility() {
  const expertCheckbox = document.getElementById('expert');
  const cqlRow = document.getElementById('cql-row');
  
  if (!expertCheckbox || !cqlRow) return;
  
  if (expertCheckbox.checked) {
    cqlRow.removeAttribute('hidden');
    console.log('[Expert] Initial state: visible');
  } else {
    cqlRow.setAttribute('hidden', '');
    console.log('[Expert] Initial state: hidden');
  }
}

/**
 * Bind Expert Toggle
 * Shows/hides CQL raw field
 * When enabled and mode != cql, switches mode to cql
 */
function bindExpertToggle() {
  const expertCheckbox = document.getElementById('expert');
  const cqlRow = document.getElementById('cql-row');
  const modeSelect = document.getElementById('mode');
  
  if (!expertCheckbox || !cqlRow) return;
  
  expertCheckbox.addEventListener('change', function() {
    if (this.checked) {
      // Show CQL row
      cqlRow.removeAttribute('hidden');
      // If mode is not CQL, switch to CQL
      if (modeSelect && modeSelect.value !== 'cql') {
        modeSelect.value = 'cql';
      }
      console.log('[Expert] Enabled, mode:', modeSelect?.value);
    } else {
      // Hide CQL row
      cqlRow.setAttribute('hidden', '');
      console.log('[Expert] Disabled');
    }
  });
}

/**
 * Bind Mode Change Handler
 * When mode changes to "cql", auto-check Expert checkbox
 */
function bindModeChange() {
  const modeSelect = document.getElementById('mode');
  const expertCheckbox = document.getElementById('expert');
  
  if (!modeSelect || !expertCheckbox) return;
  
  modeSelect.addEventListener('change', function() {
    if (this.value === 'cql' && !expertCheckbox.checked) {
      expertCheckbox.checked = true;
      // Trigger change event to update visibility
      expertCheckbox.dispatchEvent(new Event('change'));
      console.log('[Mode] Changed to CQL, enabled Expert mode');
    }
  });
}

/**
 * Bind form submit handler
 */
function bindFormSubmit() {
  const form = document.getElementById('adv-form');
  if (!form) return;

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Build query parameters
    const queryParams = buildQueryParams();
    console.log('[Advanced] Submitting with params:', queryParams);
    
    // Make AJAX request to /search/advanced/data
    loadSearchResults(queryParams);
  });
}

/**
 * Build query parameters from form controls
 * Returns URLSearchParams object
 */
function buildQueryParams() {
  const form = document.getElementById('adv-form');
  if (!form) {
    console.error('[Advanced] Form not found in buildQueryParams');
    throw new Error('Form element #adv-form is missing');
  }
  
  const params = new URLSearchParams();

  // Required: Query
  const qElement = form.querySelector('#q');
  if (!qElement) {
    console.error('[Advanced] Query element not found');
    throw new Error('Query element #q is missing');
  }
  
  const q = qElement.value.trim();
  if (!q) {
    alert('Por favor ingresa una consulta');
    throw new Error('Query is required');
  }
  params.append('q', q);

  // Mode
  const mode = form.querySelector('#mode').value || 'forma';
  params.append('mode', mode);

  // Expert mode
  const expert = form.querySelector('#expert').checked;
  if (expert) {
    params.append('expert', '1');
    // CQL raw (if expert mode)
    const cqlRaw = form.querySelector('#cql_raw').value.trim();
    if (cqlRaw) {
      params.append('cql_raw', cqlRaw);
    }
  }

  // Sensitive checkbox (0 or 1)
  const sensitive = form.querySelector('#sensitive').checked ? '1' : '0';
  params.append('sensitive', sensitive);

  // Filters (multi-select) - WITHOUT [] suffix, like Simple Search
  // Country codes
  const countries = Array.from(form.querySelectorAll('#filter-country-code option:checked'))
    .map(opt => opt.value)
    .filter(v => v !== '');
  countries.forEach(c => params.append('country_code', c));

  // Speaker types
  const speakers = Array.from(form.querySelectorAll('#filter-speaker-type option:checked'))
    .map(opt => opt.value)
    .filter(v => v !== '');
  speakers.forEach(s => params.append('speaker_type', s));

  // Sex
  const sexes = Array.from(form.querySelectorAll('#filter-sex option:checked'))
    .map(opt => opt.value)
    .filter(v => v !== '');
  sexes.forEach(sx => params.append('sex', sx));

  // Speech mode
  const modes = Array.from(form.querySelectorAll('#filter-speech-mode option:checked'))
    .map(opt => opt.value)
    .filter(v => v !== '');
  modes.forEach(m => params.append('speech_mode', m));

  // Discourse
  const discourses = Array.from(form.querySelectorAll('#filter-discourse option:checked'))
    .map(opt => opt.value)
    .filter(v => v !== '');
  discourses.forEach(d => params.append('discourse', d));

  // Regional checkbox
  const includeRegional = form.querySelector('#include-regional').checked ? '1' : '0';
  params.append('include_regional', includeRegional);

  return params;
}

/**
 * Load search results via AJAX to /search/advanced/data
 * 
 * @param {URLSearchParams} queryParams - Query parameters
 */
async function loadSearchResults(queryParams) {
  const summaryBox = document.getElementById('adv-summary');
  
  try {
    // Show summary (will be populated)
    if (summaryBox) {
      summaryBox.hidden = false;
      summaryBox.innerHTML = '<span>Cargando resultados...</span>';
    }
    
    // Initialize DataTables with current query params
    initAdvancedTable(queryParams.toString());
    
    // Update export button URLs with current params
    updateExportButtons(queryParams.toString());
    
    // Fetch first page to populate summary
    const response = await fetch(`/search/advanced/data?${queryParams.toString()}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    // Update summary box with results count
    updateSummary(data, queryParams);
    
    // Focus on summary for accessibility
    if (summaryBox) {
      summaryBox.focus();
      summaryBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    resultsLoaded = true;
    console.log('✅ Results loaded:', data.recordsFiltered, 'results');
    
  } catch (error) {
    console.error('❌ Error loading results:', error);
    
    // Show error message in summary
    if (summaryBox) {
      summaryBox.innerHTML = `<span style="color: var(--md-sys-color-error);">Error: ${escapeHtml(error.message)}</span>`;
    }
  }
}

/**
 * Bind reset button handler
 * Clears all form fields, destroys DataTables, hides results
 */
function bindResetButton() {
  const resetBtn = document.getElementById('reset-button');
  if (!resetBtn) return;

  resetBtn.addEventListener('click', function(e) {
    e.preventDefault();
    
    const form = document.getElementById('adv-form');
    
    // Clear text inputs
    form.querySelector('#q').value = '';
    form.querySelector('#cql_raw').value = '';
    
    // Reset mode to default
    form.querySelector('#mode').value = 'forma';
    
    // Reset expert mode
    form.querySelector('#expert').checked = false;
    const cqlRow = document.getElementById('cql-row');
    if (cqlRow) cqlRow.hidden = true;
    
    // Reset sensitive to checked (default: sensitive)
    form.querySelector('#sensitive').checked = true;
    
    // Clear all Select2 filters
    form.querySelectorAll('select[data-enhance="select2"]').forEach(select => {
      $(select).val(null).trigger('change');
    });
    
    // Reset regional checkbox to unchecked (default: no regional)
    form.querySelector('#include-regional').checked = false;
    
    // Hide summary box
    const summaryBox = document.getElementById('adv-summary');
    if (summaryBox) {
      summaryBox.hidden = true;
      summaryBox.innerHTML = '';
    }
    
    // Destroy DataTables if exists
    if ($.fn.dataTable.isDataTable('#advanced-table')) {
      try {
        $('#advanced-table').DataTable().destroy();
      } catch (e) {
        console.warn('DataTables destroy on reset:', e);
      }
    }
    
    // Focus on query input
    form.querySelector('#q').focus();
    
    resultsLoaded = false;
    console.log('✅ Form reset');
  });
}

/**
 * Escape HTML entities
 */
function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

// Export for testing
export { buildQueryParams, loadSearchResults };
