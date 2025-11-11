/**
 * Advanced Search DataTables Initialization
 * Server-Side processing for /search/advanced/data endpoint
 * 
 * Handles:
 * - DataTables init with server-side pagination
 * - Singleton pattern with reloadWith(params) method
 * - KWIC rendering (left|match|right)
 * - Audio player integration
 * - Metadata display + Summary box updates
 * - Export URL generation
 */

let advancedTable = null;
let currentParams = null;

/**
 * Initialize DataTables with server-side processing (Singleton)
 * Safely destroys existing table before re-initialization
 * 
 * @param {string} queryParams - Query string (e.g., "q=radio&mode=forma")
 */
export function initAdvancedTable(queryParams) {
  // Store current params for reloadWith
  currentParams = queryParams;
  
  // Step 1: Destroy existing table if present (Re-init safety)
  if (advancedTable && $.fn.dataTable.isDataTable('#advanced-table')) {
    try {
      advancedTable.destroy();  // Destroy DataTables instance
      advancedTable = null;
    } catch (e) {
      console.warn('[DataTables] Destroy error:', e);
    }
  }

  // Step 2: Build AJAX URL from current form values
  const ajaxUrl = `/search/advanced/data?${queryParams}`;
  console.log('[DataTables] Init with:', ajaxUrl);

  // Step 3: Initialize DataTables with minimal config
  advancedTable = $('#advanced-table').DataTable({
    serverSide: true,
    processing: true,
    deferRender: true,
    autoWidth: false,
    searching: false,      // Disable client-side search
    ordering: false,       // Disable sorting
    pageLength: 50,
    lengthMenu: [25, 50, 100],
    
    // AJAX config
    ajax: {
      url: ajaxUrl,
      type: 'GET',
      error: function(xhr, error, thrown) {
        console.error('DataTables AJAX error:', xhr.status, error);
        handleDataTablesError(xhr);
      },
      dataSrc: function(json) {
        // After data load: update summary and export buttons
        updateSummary(json, queryParams);
        updateExportButtons(queryParams);
        focusSummary();
        return json.data;
      }
    },

    // Column definitions (12 columns - same as Simple)
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
        data: 'left',
        render: function(data) {
          return escapeHtml(data || '');
        },
        className: 'md3-datatable__cell--context'
      },
      // Column 2: Match (KWIC) - highlighted
      {
        targets: 2,
        data: 'match',
        render: function(data) {
          return `<mark>${escapeHtml(data || '')}</mark>`;
        },
        className: 'md3-datatable__cell--match'
      },
      // Column 3: Context right
      {
        targets: 3,
        data: 'right',
        render: function(data) {
          return escapeHtml(data || '');
        },
        className: 'md3-datatable__cell--context'
      },
      // Column 4: Audio player
      {
        targets: 4,
        data: null,
        render: function(data, type, row) {
          if (!row.start_ms || !row.filename) {
            return '<span class="md3-datatable__empty">-</span>';
          }
          const startMs = parseInt(row.start_ms) || 0;
          const endMs = parseInt(row.end_ms) || startMs + 5000;
          const audioUrl = `/media/segment/${encodeURIComponent(row.filename)}/${startMs}/${endMs}`;
          return `<audio controls style="width: 150px; height: 30px;" 
            aria-label="Audio excerpt from ${escapeHtml(row.filename)}">
            <source src="${audioUrl}" type="audio/mpeg">
            Your browser does not support the audio element.
          </audio>`;
        },
        orderable: false,
        className: 'md3-datatable__cell--audio'
      },
      // Column 5: Country
      {
        targets: 5,
        data: 'country',
        render: function(data) {
          return escapeHtml(data || '-');
        }
      },
      // Column 6: Speaker type
      {
        targets: 6,
        data: 'speaker_type',
        render: function(data) {
          return escapeHtml(data || '-');
        }
      },
      // Column 7: Sex
      {
        targets: 7,
        data: 'sex',
        render: function(data) {
          return escapeHtml(data || '-');
        }
      },
      // Column 8: Mode
      {
        targets: 8,
        data: 'mode',
        render: function(data) {
          return escapeHtml(data || '-');
        }
      },
      // Column 9: Discourse
      {
        targets: 9,
        data: 'discourse',
        render: function(data) {
          return escapeHtml(data || '-');
        }
      },
      // Column 10: Token ID
      {
        targets: 10,
        data: 'tokid',
        render: function(data) {
          return escapeHtml(data || '-');
        }
      },
      // Column 11: Filename
      {
        targets: 11,
        data: 'filename',
        render: function(data) {
          return escapeHtml(data || '-');
        }
      }
    ],

    // Responsive behavior
    responsive: false,
    
    // DOM structure
    dom: '<"top"lp><"clear">rt<"bottom"lpi><"clear">',

    // Localization
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
    }
  });

  console.log('✅ DataTables initialized');
}

/**
 * Reload table with new parameters (public API)
 * 
 * @param {URLSearchParams|string} params - New query parameters
 */
export function reloadWith(params) {
  const paramString = params instanceof URLSearchParams ? params.toString() : params;
  console.log('[DataTables] Reloading with:', paramString);
  
  // Re-initialize with new params
  initAdvancedTable(paramString);
}

/**
 * Focus on summary box after data load (A11y)
 */
function focusSummary() {
  const summaryBox = document.getElementById('adv-summary');
  if (summaryBox) {
    // Small delay to ensure content is rendered
    setTimeout(() => {
      summaryBox.focus();
      summaryBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
  }
}

/**
 * Handle DataTables AJAX errors
 */
function handleDataTablesError(xhr) {
  // Punkt 7: Differentiate CQL syntax errors from other errors
  let errorMsg = 'Error al cargar resultados';
  let errorType = 'unknown';
  
  try {
    const response = JSON.parse(xhr.responseText);
    if (response.error === 'invalid_cql') {
      errorType = 'cql_syntax';
      errorMsg = `Sintaxis CQL inválida: ${response.message}`;
    } else if (response.error === 'invalid_filter') {
      errorType = 'filter_validation';
      errorMsg = `Filtro inválido: ${response.message}`;
    } else if (response.message) {
      errorMsg = response.message;
    }
  } catch (e) {
    // Not JSON, use HTTP status
    if (xhr.status === 400) {
      errorMsg = 'Consulta inválida. Verifica la sintaxis CQL.';
    } else if (xhr.status >= 500) {
      errorMsg = 'Error del servidor. Por favor, intenta más tarde.';
    }
  }

  console.error(`[ERROR] ${errorType}: ${errorMsg}`);

  // Display error message in results section
  const resultsSection = document.getElementById('results-section');
  if (resultsSection) {
    // Remove any existing error messages
    const existingErrors = resultsSection.querySelectorAll('.md3-alert--error');
    existingErrors.forEach(el => el.remove());
    
    const errorHtml = `<div class="md3-alert md3-alert--error" role="alert">
      <span class="material-symbols-rounded md3-alert__icon" aria-hidden="true">error</span>
      <div class="md3-alert__message">
        <strong>Error:</strong> ${escapeHtml(errorMsg)}
      </div>
    </div>`;
    resultsSection.insertAdjacentHTML('afterbegin', errorHtml);
  }
}

/**
 * Update export button URLs with current query parameters
 * Includes timestamp in download filename
 */
export function updateExportButtons(queryParams) {
  const csvBtn = document.getElementById('export-csv');
  const tsvBtn = document.getElementById('export-tsv');
  
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  
  if (csvBtn) {
    const csvParams = new URLSearchParams(queryParams);
    csvParams.set('format', 'csv');
    csvBtn.href = `/search/advanced/export?${csvParams.toString()}`;
    csvBtn.download = `corapan_advanced_${timestamp}.csv`;
  }
  
  if (tsvBtn) {
    const tsvParams = new URLSearchParams(queryParams);
    tsvParams.set('format', 'tsv');
    tsvBtn.href = `/search/advanced/export?${tsvParams.toString()}`;
    tsvBtn.download = `corapan_advanced_${timestamp}.tsv`;
  }
  
  console.log('[Export] Buttons updated');
}

/**
 * Update summary box with results info
 * Shows query, hit count + badge if server filters are active
 * 
 * @param {Object} data - DataTables response data
 * @param {string} queryParams - Current query parameters
 */
export function updateSummary(data, queryParams) {
  const summaryBox = document.getElementById('adv-summary');
  if (!summaryBox) return;

  const filtered = data.recordsFiltered || 0;
  const total = data.recordsTotal || 0;
  
  // Extract query from params
  const params = new URLSearchParams(queryParams);
  const query = params.get('q') || params.get('cql_raw') || '—';
  
  // Check if filters are active (any metadata filter set) - WITHOUT [] suffix
  const hasFilters = params.has('country_code') || params.has('speaker_type') || 
                     params.has('sex') || params.has('speech_mode') || 
                     params.has('discourse') || params.get('include_regional') === '1';
  
  const filtersActive = hasFilters && filtered < total;

  // Build summary HTML
  let html = `
    <span class="md3-advanced__summary-query">"${escapeHtml(query)}"</span>: 
    <span class="md3-advanced__summary-count">${filtered.toLocaleString('es-ES')}</span>
    <span class="md3-advanced__summary-total">resultados`;
  
  if (total > 0) {
    html += ` de ${total.toLocaleString('es-ES')} documentos`;
  }
  
  html += `</span>`;
  
  if (filtersActive) {
    html += ` <span class="md3-badge--serverfilter">
      <span class="material-symbols-rounded" aria-hidden="true">filter_alt</span>
      Serverfilter activo
    </span>`;
  }
  
  summaryBox.innerHTML = html;
  summaryBox.hidden = false;
  
  console.log('[Summary] Updated:', filtered, 'results,', 'filters:', filtersActive);
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

// Export for external use
export { advancedTable };
