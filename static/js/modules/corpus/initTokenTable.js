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

let tokenTable = null;
let currentTokenIds = [];

/**
 * Initialize DataTables with server-side processing for Token Search
 * 
 * @param {Array<string>} tokenIds - Array of token IDs to search for
 */
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
  
  // Step 1: Destroy existing table if present (Re-init safety)
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

  console.log('[Token DataTables] Init with token IDs:', tokenIds);

  // Step 3: Initialize DataTables with server-side processing
  tokenTable = $('#token-results-table').DataTable({
    serverSide: true,
    processing: true,
    deferRender: true,
    autoWidth: false,
    searching: false,       // Disable client-side search
    ordering: true,         // Enable server-side ordering
    pageLength: 50,
    lengthMenu: [25, 50, 100],
    
    // AJAX config - POST to token search endpoint
    ajax: {
      url: '/search/advanced/token/search',
      type: 'POST',
      contentType: 'application/json',
      data: function(d) {
        // Merge DataTables pagination params with token request
        return JSON.stringify({
          draw: d.draw,
          start: d.start,
          length: d.length,
          order: d.order,
          ...requestBody
        });
      },
      error: function(xhr, error, thrown) {
        console.error('[Token] AJAX error:', xhr.status, error);
        handleTokenDataTablesError(xhr);
      },
      dataSrc: function(json) {
        console.log('[Token DataTables dataSrc] Response received:', json);
        
        // Check for backend error in response
        if (json && json.error) {
          console.warn(`[Token] Backend error detected: ${json.error}`);
          handleTokenBackendError(json);
          return [];
        }
        
        // Normal flow
        updateTokenSummary(json, tokenIds);
        updateTokenExportButtons(tokenIds);
        focusTokenResults();
        return json.data || [];
      }
    },

    // Column definitions (12 columns - IDENTICAL to Advanced Search)
    columnDefs: [
      // Column 0: Row number (#)
      {
        targets: 0,
        render: function(data, type, row, meta) {
          return meta.row + meta.settings._iDisplayStart + 1;
        },
        width: '40px',
        searchable: false,
        orderable: false
      },
      // Column 1: Context left
      {
        targets: 1,
        data: 'context_left',
        render: function(data) {
          return `<span class="md3-corpus-context">${escapeHtml(data || '')}</span>`;
        },
        className: 'md3-datatable__cell--context right-align',
        width: '200px'
      },
      // Column 2: Match (KWIC) - highlighted
      {
        targets: 2,
        data: 'text',
        render: function(data) {
          return `<span class="md3-corpus-keyword"><mark>${escapeHtml(data || '')}</mark></span>`;
        },
        className: 'md3-datatable__cell--match center-align',
        width: '150px'
      },
      // Column 3: Context right
      {
        targets: 3,
        data: 'context_right',
        render: function(data) {
          return `<span class="md3-corpus-context">${escapeHtml(data || '')}</span>`;
        },
        className: 'md3-datatable__cell--context',
        width: '200px'
      },
      // Column 4: Audio player (play + download buttons)
      {
        targets: 4,
        data: null,
        render: function(data, type, row) {
          return renderTokenAudioButtons(row);
        },
        orderable: false,
        className: 'md3-datatable__cell--audio center-align',
        width: '120px'
      },
      // Column 5: Country code
      {
        targets: 5,
        data: 'country_code',
        render: function(data, type) {
          if (type === 'sort' || type === 'filter' || type === 'type') {
            return data || '';
          }
          return escapeHtml((data || '-').toUpperCase());
        },
        width: '80px',
        orderable: true
      },
      // Column 6: Speaker type
      {
        targets: 6,
        data: 'speaker_type',
        render: function(data) {
          return escapeHtml(data || '-');
        },
        width: '80px',
        orderable: true
      },
      // Column 7: Sex
      {
        targets: 7,
        data: 'sex',
        render: function(data) {
          return escapeHtml(data || '-');
        },
        width: '80px',
        orderable: true
      },
      // Column 8: Mode
      {
        targets: 8,
        data: 'mode',
        render: function(data) {
          return escapeHtml(data || '-');
        },
        width: '80px',
        orderable: true
      },
      // Column 9: Discourse
      {
        targets: 9,
        data: 'discourse',
        render: function(data) {
          return escapeHtml(data || '-');
        },
        width: '80px',
        orderable: true
      },
      // Column 10: Token ID
      {
        targets: 10,
        data: 'token_id',
        render: function(data) {
          return escapeHtml(data || '-');
        },
        width: '100px',
        orderable: true
      },
      // Column 11: Filename (file link with player icon)
      {
        targets: 11,
        data: 'filename',
        render: function(data, type, row) {
          return renderTokenFileLink(data, type, row);
        },
        width: '80px',
        className: 'center-align'
      }
    ],

    // Responsive behavior
    responsive: false,
    
    // DOM structure with export buttons
    dom: '<"top"pB<"ml-auto"lf>>rt<"bottom"ip>',
    buttons: [
      { 
        extend: 'copyHtml5', 
        text: '<i class="fa-solid fa-copy"></i> Copiar', 
        exportOptions: { 
          columns: [0,1,2,3,5,6,7,8,9,10,11] 
        } 
      },
      { 
        extend: 'csvHtml5', 
        text: '<i class="bi bi-filetype-csv"></i> CSV', 
        exportOptions: { 
          columns: [0,1,2,3,5,6,7,8,9,10,11] 
        } 
      },
      { 
        extend: 'excelHtml5', 
        text: '<i class="bi bi-filetype-xlsx"></i> Excel', 
        exportOptions: { 
          columns: [0,1,2,3,5,6,7,8,9,10,11] 
        } 
      },
      { 
        extend: 'pdfHtml5', 
        text: '<i class="bi bi-filetype-pdf"></i> PDF', 
        orientation: 'landscape', 
        pageSize: 'A4', 
        exportOptions: { 
          columns: [0,1,2,3,5,6,7,8,9,10,11] 
        }, 
        customize: function(doc) { 
          doc.defaultStyle.fontSize = 8; 
          doc.styles.tableHeader.fontSize = 9; 
        } 
      }
    ],

    // Spanish localization (same as Advanced Search)
    language: {
      lengthMenu: '_MENU_ resultados por página',
      zeroRecords: 'No se encontraron resultados',
      info: 'Mostrando _START_ a _END_ de _TOTAL_ resultados',
      infoEmpty: 'Sin resultados',
      infoFiltered: '(filtrados de _MAX_ resultados totales)',
      loadingRecords: 'Cargando...',
      processing: 'Procesando...',
      paginate: {
        first: 'Primero',
        last: 'Último',
        next: 'Siguiente',
        previous: 'Anterior'
      }
    },

    // Horizontal scroll
    scrollX: true,
    scrollCollapse: false
  });

  console.log('✅ Token DataTable initialized');

  // Adjust columns after init
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

  // Window resize -> adjust columns
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

/**
 * Render audio control buttons (identical to Advanced Search)
 */
function renderTokenAudioButtons(row) {
  const hasAudio = row.start_ms && row.filename;
  if (!hasAudio) return '<span class="md3-datatable__empty">-</span>';

  const filename = row.filename || '';
  const tokenId = row.token_id || '';
  
  const startMs = row.start_ms || row.start || 0;
  const endMs = row.end_ms || (parseInt(startMs) + 5000);
  const contextStartMs = row.context_start || startMs;
  const contextEndMs = row.context_end || endMs;
  
  const startSec = (startMs / 1000).toFixed(3);
  const endSec = (endMs / 1000).toFixed(3);
  const contextStartSec = (contextStartMs / 1000).toFixed(3);
  const contextEndSec = (contextEndMs / 1000).toFixed(3);
  
  return `
    <div class="md3-corpus-audio-buttons">
      <div class="md3-corpus-audio-row">
        <span class="md3-corpus-audio-label">Res.:</span>
        <a class="audio-button" data-filename="${escapeHtml(filename)}" data-start="${startSec}" data-end="${endSec}" data-token-id="${escapeHtml(tokenId)}" data-type="pal">
          <i class="fa-solid fa-play"></i>
        </a>
        <a class="download-button" data-filename="${escapeHtml(filename)}" data-start="${startSec}" data-end="${endSec}" data-token-id="${escapeHtml(tokenId)}" data-type="pal">
          <i class="fa-solid fa-download"></i>
        </a>
      </div>
      <div class="md3-corpus-audio-row">
        <span class="md3-corpus-audio-label">Ctx:</span>
        <a class="audio-button" data-filename="${escapeHtml(filename)}" data-start="${contextStartSec}" data-end="${contextEndSec}" data-token-id="${escapeHtml(tokenId)}" data-type="ctx">
          <i class="fa-solid fa-play"></i>
        </a>
        <a class="download-button" data-filename="${escapeHtml(filename)}" data-start="${contextStartSec}" data-end="${contextEndSec}" data-token-id="${escapeHtml(tokenId)}" data-type="ctx">
          <i class="fa-solid fa-download"></i>
        </a>
      </div>
    </div>
  `;
}

/**
 * Render file link with player icon
 */
function renderTokenFileLink(filename, type, row) {
  if (!filename) return '';
  if (type === 'sort' || type === 'type') return filename;
  
  const base = filename.trim().replace(/\.mp3$/i, '');
  const transcriptionPath = `/media/transcripts/${encodeURIComponent(base)}.json`;
  const audioPath = `/media/full/${encodeURIComponent(base)}.mp3`;
  let playerUrl = `/player?transcription=${encodeURIComponent(transcriptionPath)}&audio=${encodeURIComponent(audioPath)}`;
  
  if (row && row.token_id) {
    playerUrl += `&token_id=${encodeURIComponent(row.token_id)}`;
  }
  
  return `
    <a href="${playerUrl}" class="player-link" title="${escapeHtml(filename)}">
      <i class="fa-regular fa-file"></i>
    </a>
  `;
}

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

/**
 * Escape HTML special characters (prevent XSS)
 */
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}
