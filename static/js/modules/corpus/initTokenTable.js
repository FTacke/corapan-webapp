/**
 * Token-Tab DataTables Initialization (1:1 Mirror of Advanced Search)
 * Server-Side processing for /search/advanced/token/search endpoint
 * 
 * Handles:
 * - DataTables init with server-side pagination (Singleton pattern)
 * - KWIC rendering (context_left | match | context_right)
 * - Audio player integration (play + download buttons)
 * - Metadata display (country, speaker_type, sex, mode, discourse, etc.)
 * - Export buttons (CSV, Excel, PDF)
 * - Error handling (BlackLab unavailable, network issues)
 */

import { makeBaseConfig, escapeHtml, renderAudioButtons, renderFileLink } from '../advanced/datatableFactory.js';
let tokenTable = null;
let currentTokenIds = [];

export function initTokenTable(tokenIds) {
  // Guard: jQuery must be present
  if (typeof window.$ === 'undefined' || typeof window.jQuery === 'undefined') {
    console.error('[Token] jQuery not available, cannot initialize DataTables');
    return;
  }
  
  // Guard: DataTables plugin must be available
  if (typeof $.fn.dataTable === 'undefined') {
    console.error('[Token] DataTables plugin not available');
    return;
  }

  // Store current token IDs
  currentTokenIds = tokenIds;
  
  // Step 1: Destroy existing table if present
  if (tokenTable && $.fn.dataTable.isDataTable('#token-results-table')) {
    try {
      tokenTable.destroy();
      tokenTable = null;
    } catch (e) {
      console.warn('[Token DataTables] Destroy error:', e);
    }
  }

  // Step 2: Build request body with token IDs
  const requestBody = {
    token_ids_raw: tokenIds.join(','),
    context_size: 5
  };

  const baseConfig = makeBaseConfig();
  const config = Object.assign({}, baseConfig, {
    ajax: {
      url: '/search/advanced/token/search',
      type: 'POST',
      contentType: 'application/json',
      data: function(d) {
        return JSON.stringify({ draw: d.draw, start: d.start, length: d.length, order: d.order, ...requestBody });
      },
      error: function(xhr, error, thrown) {
        console.error('[Token] AJAX error:', xhr.status, error);
        handleTokenDataTablesError(xhr);
      },
      dataSrc: function(json) {
        if (json && json.error) {
          handleTokenBackendError(json);
          return [];
        }
        updateTokenSummary(json, tokenIds);
        updateTokenExportButtons(tokenIds);
        focusTokenResults();
        return json.data || [];
      }
    },
    scrollX: false,
    scrollCollapse: false
  });

  tokenTable = $('#token-results-table').DataTable(config);
  
  console.log('✅ Token DataTable initialized');
  
  setTimeout(() => {
    try {
      if (tokenTable && tokenTable.columns) {
        tokenTable.columns.adjust();
        if (tokenTable.responsive) tokenTable.responsive.recalc();
      }
    } catch (e) {
      console.warn('[Token] Column adjust error:', e);
    }
  }, 100);

  $(window).on('resize.tokenTable', () => {
    try {
      if (tokenTable && tokenTable.columns) {
        tokenTable.columns.adjust();
        if (tokenTable.responsive) tokenTable.responsive.recalc();
      }
    } catch (e) {
      console.warn('[Token] Column adjust error on resize:', e);
    }
  });
}

  // (initTokenTable finished)

/**
 * Reload token table (public API)
 * 
 * @param {Array<string>} tokenIds - New token IDs
 */
export function reloadTokenTable(tokenIds) {
  console.log('[Token DataTables] Reloading with token IDs:', tokenIds);
  initTokenTable(tokenIds);
}

/**
 * Destroy token table
 */
export function destroyTokenTable() {
  if (tokenTable && $.fn.dataTable.isDataTable('#token-results-table')) {
    tokenTable.destroy();
    tokenTable = null;
  }
}

/**
 * Focus on token results section after data load (A11y)
 */
function focusTokenResults() {
  const resultsSection = document.getElementById('token-results');
  if (resultsSection) {
    setTimeout(() => {
      resultsSection.focus();
      resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }
}

/**
 * Handle DataTables AJAX errors (network, HTTP errors)
 */
function handleTokenDataTablesError(xhr) {
  const errorMsg = `DataTables Error: HTTP ${xhr.status}`;
  console.error('[Token]', errorMsg);
  
  // Could show user notification here
  alert(`Error loading results: ${errorMsg}`);
}

/**
 * Handle backend errors returned in JSON response
 * (BlackLab connection error, invalid query, etc.)
 */
function handleTokenBackendError(json) {
  const errorCode = json.error || 'unknown_error';
  const errorMessage = json.message || 'An error occurred in the search backend';
  
  console.error(`[Token Backend Error] ${errorCode}: ${errorMessage}`);
  alert(`Backend Error: ${errorMessage}`);
}

// Using shared renderAudioButtons from datatableFactory

// Using shared renderFileLink from datatableFactory

/**
 * Update summary box with token search results info
 */
function updateTokenSummary(json, tokenIds) {
  // Could display: "Found X results for token IDs: abc123, def456..."
  console.log('[Token Summary] Updated with:', json.recordsFiltered, 'results');
}

/**
 * Update token export buttons with timestamp
 */
function updateTokenExportButtons(tokenIds) {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  const tokIdStr = tokenIds.join('_').substring(0, 16);
  
  console.log('[Token Export] Buttons updated');
  // Export buttons are already configured in dom definition
}

// Use shared escapeHtml from datatableFactory
