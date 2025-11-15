/**
 * Main Search UI Module
 * Coordinates all search UI components
 * 
 * Features:
 * - Advanced mode toggle
 * - Manual CQL editing
 * - Form submission
 * - Sub-tabs switching
 * - Integration with filters and pattern builder
 */

import { getSearchFilters } from './filters.js';
import { getPatternBuilder } from './patternBuilder.js';
import { initAdvancedTable } from '../advanced/initTable.js';

export class SearchUI {
  constructor() {
    this.advancedMode = false;
    this.manualCQLEdit = false;
    this.currentView = 'results';
    
    this.init();
  }

  init() {
    // Bind advanced mode toggle
    this.bindAdvancedToggle();

    // Bind manual CQL edit checkbox
    this.bindManualEditToggle();

    // Bind form submission
    this.bindFormSubmit();

    // Bind reset button
    this.bindResetButton();

    // Bind sub-tabs
    this.bindSubTabs();

    console.log('✅ Search UI initialized');
  }

  /**
   * Bind advanced mode toggle
   */
  bindAdvancedToggle() {
    const toggle = document.getElementById('modo-avanzado');
    const expertArea = document.getElementById('expert-area');

    if (!toggle || !expertArea) return;

    // Ensure aria-checked reflects initial state
    toggle.setAttribute('aria-checked', toggle.checked ? 'true' : 'false');

    toggle.addEventListener('change', (e) => {
      this.advancedMode = e.target.checked;
      // Keep aria attribute in sync
      toggle.setAttribute('aria-checked', e.target.checked ? 'true' : 'false');

      if (this.advancedMode) {
        expertArea.removeAttribute('hidden');
        
        // Initialize pattern builder if not already done
        const patternBuilder = getPatternBuilder();
        if (patternBuilder) {
          patternBuilder.updateCQLPreview();
        }
      } else {
        expertArea.setAttribute('hidden', '');
      }
    });
  }

  /**
   * Bind manual CQL edit checkbox
   */
  bindManualEditToggle() {
    const checkbox = document.getElementById('allow-manual-edit');
    const cqlPreview = document.getElementById('cql-preview');
    const cqlWarning = document.getElementById('cql-warning');

    if (!checkbox || !cqlPreview || !cqlWarning) return;

    checkbox.addEventListener('change', (e) => {
      this.manualCQLEdit = e.target.checked;

      if (this.manualCQLEdit) {
        cqlPreview.removeAttribute('readonly');
        cqlWarning.removeAttribute('hidden');
      } else {
        cqlPreview.setAttribute('readonly', '');
        cqlWarning.setAttribute('hidden', '');
        
        // Regenerate CQL from builder
        const patternBuilder = getPatternBuilder();
        if (patternBuilder) {
          patternBuilder.updateCQLPreview();
        }
      }
    });
  }

  /**
   * Bind form submission
   */
  bindFormSubmit() {
    const form = document.getElementById('advanced-search-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      
      const queryParams = this.buildQueryParams();
      console.log('[SearchUI] Submitting search:', Object.fromEntries(queryParams));
      
      // Here you would typically call the existing search handler
      // For now, we'll log the parameters
      this.performSearch(queryParams);
    });
  }

  /**
   * Build query parameters from form
   */
  buildQueryParams() {
    const params = new URLSearchParams();
    // Read sensitivity early so we can adjust CQL generation
    const ignoreAccentsEarly = document.getElementById('ignore-accents');
    const sensitiveFlag = ignoreAccentsEarly && ignoreAccentsEarly.checked ? '0' : '1';
    params.set('sensitive', sensitiveFlag);

    // A: Basic query
    const queryInput = document.getElementById('q');
    const searchTypeSelect = document.getElementById('search_type');

    if (queryInput && queryInput.value.trim()) {
      // If advanced mode is active and manual CQL or pattern builder has content, use CQL
      if (this.advancedMode) {
        const cqlPreview = document.getElementById('cql-preview');
        if (cqlPreview && cqlPreview.value.trim()) {
          let cqlStr = cqlPreview.value.trim();
          // Map sensitivity: if insensitive (0) and not manual edit, substitute word -> norm
          const sensitive = sensitiveFlag;
          const allowManualCql = document.getElementById('allow-manual-edit');
          const manualEdit = allowManualCql && allowManualCql.checked;
          if (sensitive === '0' && !manualEdit) {
            // Simple transformation: replace word="..." -> norm="..."
            cqlStr = cqlStr.replace(/\bword=/g, 'norm=');
          }
          params.set('q', cqlStr);
          params.set('mode', 'cql');
        } else {
          // Fallback to basic query
          params.set('q', queryInput.value.trim());
          const uiSearchType = searchTypeSelect ? searchTypeSelect.value : 'forma';
          params.set('search_type', uiSearchType);
          // Map spanish UI 'lema' to backend 'lemma'
          if (uiSearchType === 'lema') {
            params.set('mode', 'lemma');
          } else if (uiSearchType === 'forma') {
            params.set('mode', 'forma');
          } else if (uiSearchType === 'forma_exacta') {
            params.set('mode', 'forma_exacta');
          }
        }
      } else {
        // Simple mode
        params.set('q', queryInput.value.trim());
        const uiSearchType = searchTypeSelect ? searchTypeSelect.value : 'forma';
        params.set('search_type', uiSearchType);
        // Map Spanish to canonical backend modes for advanced search
        if (uiSearchType === 'lema') {
          params.set('mode', 'lemma');
        } else if (uiSearchType === 'forma') {
          params.set('mode', 'forma');
        } else if (uiSearchType === 'forma_exacta') {
          params.set('mode', 'forma_exacta');
        }
      }
    }

    // B: Metadata filters (handled by SearchFilters)
    const searchFilters = getSearchFilters();
    if (searchFilters) {
      const filterParams = searchFilters.getActiveFilterParams();
      filterParams.forEach((value, key) => {
        params.append(key, value);
      });
    }

    // C: Options
    const includeRegional = document.getElementById('include-regional');
    if (includeRegional && includeRegional.checked) {
      params.set('include_regional', '1');
    }

    // (sensitivity already set earlier)

    return params;
  }

  /**
   * Perform search with given parameters
   */
  async performSearch(queryParams) {
    const resultsSection = document.getElementById('results-section');
    const summaryBox = document.getElementById('adv-summary');

    try {
      if (summaryBox) {
        summaryBox.hidden = false;
        summaryBox.innerHTML = '<span>Cargando resultados...</span>';
      }

      // Call existing advanced search handler
      // This should integrate with initTable.js
      const response = await fetch(`/search/advanced/data?${queryParams.toString()}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Debug: if the server returned the generated CQL, log it
      if (data && data.cql_debug) {
        console.debug('[SearchUI] Server CQL Debug:', data.cql_debug, 'filter:', data.filter_debug || '');
      }

      // Update summary
      if (summaryBox) {
        summaryBox.innerHTML = `
          <span>Resultados encontrados: ${data.recordsFiltered || 0}</span>
        `;
      }

      // Initialize DataTable (this would call existing initTable logic)
      this.initResultsTable(queryParams.toString());

      console.log('✅ Search completed:', data.recordsFiltered, 'results');

    } catch (error) {
      console.error('❌ Search error:', error);
      if (summaryBox) {
        summaryBox.innerHTML = `
          <span style="color: var(--md-sys-color-error);">
            Error: ${this.escapeHtml(error.message)}
          </span>
        `;
      }
    }
  }

  /**
   * Initialize results table (placeholder for integration with initTable.js)
   */
  initResultsTable(queryString) {
    // This should integrate with the existing advanced/initTable.js
    // For now, we'll just log
    console.log('[SearchUI] Would initialize table with query:', queryString);
    
    // Initialize DataTable with current query string
    try {
      initAdvancedTable(queryString);
    } catch (e) {
      console.error('[SearchUI] Could not init advanced table:', e);
    }
  }

  /**
   * Bind reset button
   */
  bindResetButton() {
    const resetBtn = document.getElementById('reset-form-btn');
    if (!resetBtn) return;

    resetBtn.addEventListener('click', () => {
      this.resetForm();
    });
  }

  /**
   * Reset entire form
   */
  resetForm() {
    // Reset basic query
    const queryInput = document.getElementById('q');
    const searchTypeSelect = document.getElementById('search_type');
    
    if (queryInput) queryInput.value = '';
    if (searchTypeSelect) searchTypeSelect.value = 'forma';

    // Reset filters
    const searchFilters = getSearchFilters();
    if (searchFilters) {
      searchFilters.clearAllFilters();
    }

    // Reset options
    const includeRegional = document.getElementById('include-regional');
    const ignoreAccents = document.getElementById('ignore-accents');
    
    if (includeRegional) includeRegional.checked = false;
    if (ignoreAccents) ignoreAccents.checked = false;

    // Reset advanced mode
    const advancedToggle = document.getElementById('modo-avanzado');
    const expertArea = document.getElementById('expert-area');
    
    if (advancedToggle) {
      advancedToggle.checked = false;
      this.advancedMode = false;
    }
    if (expertArea) {
      expertArea.setAttribute('hidden', '');
    }

    // Reset pattern builder
    const patternBuilder = getPatternBuilder();
    if (patternBuilder) {
      patternBuilder.reset();
    }

    // Reset manual edit
    const allowManualEdit = document.getElementById('allow-manual-edit');
    const cqlPreview = document.getElementById('cql-preview');
    const cqlWarning = document.getElementById('cql-warning');
    
    if (allowManualEdit) allowManualEdit.checked = false;
    if (cqlPreview) {
      cqlPreview.setAttribute('readonly', '');
      cqlPreview.value = '';
    }
    if (cqlWarning) cqlWarning.setAttribute('hidden', '');
    
    this.manualCQLEdit = false;

    console.log('[SearchUI] Form reset');
  }

  /**
   * Bind sub-tabs (Resultados / Estadísticas)
   */
  bindSubTabs() {
    const tabs = document.querySelectorAll('.md3-stats-tab');
    
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const view = tab.dataset.view;
        this.switchView(view);
      });
    });
  }

  /**
   * Switch between sub-tab views
   */
  switchView(view) {
    this.currentView = view;

    // Update tab active states
    document.querySelectorAll('.md3-stats-tab').forEach(tab => {
      if (tab.dataset.view === view) {
        tab.classList.add('md3-stats-tab--active');
        tab.setAttribute('aria-selected', 'true');
      } else {
        tab.classList.remove('md3-stats-tab--active');
        tab.setAttribute('aria-selected', 'false');
      }
    });

    // Update panel visibility
    const panelResultados = document.getElementById('panel-resultados');
    const panelEstadisticas = document.getElementById('panel-estadisticas');

    if (view === 'results') {
      if (panelResultados) {
        panelResultados.classList.add('md3-view-content--active');
        panelResultados.removeAttribute('hidden');
      }
      if (panelEstadisticas) {
        panelEstadisticas.classList.remove('md3-view-content--active');
        panelEstadisticas.setAttribute('hidden', '');
      }
    } else if (view === 'stats') {
      if (panelResultados) {
        panelResultados.classList.remove('md3-view-content--active');
        panelResultados.setAttribute('hidden', '');
      }
      if (panelEstadisticas) {
        panelEstadisticas.classList.add('md3-view-content--active');
        panelEstadisticas.removeAttribute('hidden');
      }
    }
  }

  /**
   * Escape HTML
   */
  escapeHtml(text) {
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
}

// Auto-initialize
let searchUIInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('advanced-search-form');
  if (form) {
    searchUIInstance = new SearchUI();
  }
});

export function getSearchUI() {
  return searchUIInstance;
}
