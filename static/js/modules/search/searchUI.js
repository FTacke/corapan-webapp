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

import { getSearchFilters } from "./filters.js";
import { getPatternBuilder } from "./patternBuilder.js";
import {
  initAdvancedTable,
  destroyAdvancedTable,
} from "../advanced/initTable.js";

export class SearchUI {
  constructor() {
    this.advancedMode = false;
    this.manualCQLEdit = false;
    this.currentView = "results";

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

    // Bind CQL Guide Dialog
    this.bindCqlGuide();

    // Restore state from URL or SessionStorage
    this.restoreState();

    console.log("✅ Search UI initialized");
  }

  /**
   * Restore state from URL or SessionStorage
   */
  restoreState() {
    const params = new URLSearchParams(window.location.search);

    // If URL has params, use them (and save to session)
    if (params.toString()) {
      sessionStorage.setItem("lastSearch", params.toString());
      this.restoreFormFromParams(params);
      // Trigger search
      this.performSearch(params);
    }
    // If URL is empty but session has params, restore them
    else {
      const lastSearch = sessionStorage.getItem("lastSearch");
      if (lastSearch) {
        const savedParams = new URLSearchParams(lastSearch);
        // Update URL without reloading
        const newUrl = `${window.location.pathname}?${savedParams.toString()}`;
        window.history.replaceState({ path: newUrl }, "", newUrl);

        this.restoreFormFromParams(savedParams);
        this.performSearch(savedParams);
      }
    }
  }

  /**
   * Restore form values from params
   */
  restoreFormFromParams(params) {
    // Basic fields
    const q = params.get("q");
    if (q) {
      const qInput = document.getElementById("q");
      if (qInput) qInput.value = q;
    }

    const type = params.get("search_type") || params.get("mode");
    if (type) {
      const typeSelect = document.getElementById("search_type");
      if (typeSelect) typeSelect.value = type;
    }

    // Checkboxes
    const sensitive = params.get("sensitive");
    if (sensitive === "0") {
      const ignoreAccents = document.getElementById("ignore-accents");
      if (ignoreAccents) ignoreAccents.checked = true;
    }

    const regional = params.get("include_regional");
    if (regional === "1" || regional === "true") {
      const regionalCheck = document.getElementById("include-regional");
      if (regionalCheck) {
        regionalCheck.checked = true;
        // Trigger change event to show regional options
        regionalCheck.dispatchEvent(new Event("change"));
      }
    }

    // Restore filters (requires filter module support)
    const searchFilters = getSearchFilters();
    if (
      searchFilters &&
      typeof searchFilters.restoreFiltersFromParams === "function"
    ) {
      searchFilters.restoreFiltersFromParams(params);
    }
  }

  /**
   * Bind advanced mode toggle
   */
  bindAdvancedToggle() {
    const toggleBtn = document.getElementById("advanced-mode-toggle");
    const expertArea = document.getElementById("expert-area");
    const icon = document.getElementById("advanced-mode-icon");

    if (!toggleBtn || !expertArea) return;

    toggleBtn.addEventListener("click", () => {
      this.advancedMode = !this.advancedMode;

      // Update UI
      toggleBtn.setAttribute("aria-expanded", this.advancedMode);
      if (this.advancedMode) {
        expertArea.removeAttribute("hidden");
        toggleBtn.classList.add("md3-button--filled-tonal");
        toggleBtn.classList.remove("md3-button--outlined");
        if (icon) icon.textContent = "expand_less";

        // Initialize pattern builder if not already done
        const patternBuilder = getPatternBuilder();
        if (patternBuilder) {
          patternBuilder.updateCQLPreview();
        }
      } else {
        expertArea.setAttribute("hidden", "");
        toggleBtn.classList.remove("md3-button--filled-tonal");
        toggleBtn.classList.add("md3-button--outlined");
        if (icon) icon.textContent = "expand_more";
      }
    });
  }

  /**
   * Bind manual CQL edit checkbox
   */
  bindManualEditToggle() {
    const checkbox = document.getElementById("allow-manual-edit");
    const cqlPreview = document.getElementById("cql-preview");
    const cqlWarning = document.getElementById("cql-warning");

    if (!checkbox || !cqlPreview || !cqlWarning) return;

    checkbox.addEventListener("change", (e) => {
      this.manualCQLEdit = e.target.checked;

      if (this.manualCQLEdit) {
        cqlPreview.removeAttribute("readonly");
        cqlWarning.removeAttribute("hidden");
      } else {
        cqlPreview.setAttribute("readonly", "");
        cqlWarning.setAttribute("hidden", "");

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
    const form = document.getElementById("advanced-search-form");
    if (!form) return;

    form.addEventListener("submit", (e) => {
      e.preventDefault();

      const queryParams = this.buildQueryParams();
      console.log(
        "[SearchUI] Submitting search:",
        Object.fromEntries(queryParams),
      );

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
    const ignoreAccentsEarly = document.getElementById("ignore-accents");
    const sensitiveFlag =
      ignoreAccentsEarly && ignoreAccentsEarly.checked ? "0" : "1";
    params.set("sensitive", sensitiveFlag);

    // A: Basic query
    const queryInput = document.getElementById("q");
    const searchTypeSelect = document.getElementById("search_type");

    if (queryInput && queryInput.value.trim()) {
      // If advanced mode is active and manual CQL or pattern builder has content, use CQL
      if (this.advancedMode) {
        const cqlPreview = document.getElementById("cql-preview");
        if (cqlPreview && cqlPreview.value.trim()) {
          let cqlStr = cqlPreview.value.trim();
          // Map sensitivity: if insensitive (0) and not manual edit, substitute word -> norm
          const sensitive = sensitiveFlag;
          const allowManualCql = document.getElementById("allow-manual-edit");
          const manualEdit = allowManualCql && allowManualCql.checked;
          if (sensitive === "0" && !manualEdit) {
            // Simple transformation: replace word="..." -> norm="..."
            cqlStr = cqlStr.replace(/\bword=/g, "norm=");
          }
          params.set("q", cqlStr);
          params.set("mode", "cql");
        } else {
          // Fallback to basic query
          params.set("q", queryInput.value.trim());
          const uiSearchType = searchTypeSelect
            ? searchTypeSelect.value
            : "forma";
          params.set("search_type", uiSearchType);
          // Map spanish UI 'lema' to backend 'lemma'
          if (uiSearchType === "lema") {
            params.set("mode", "lemma");
          } else if (uiSearchType === "forma") {
            params.set("mode", "forma");
          } else if (uiSearchType === "forma_exacta") {
            params.set("mode", "forma_exacta");
          }
        }
      } else {
        // Simple mode
        params.set("q", queryInput.value.trim());
        const uiSearchType = searchTypeSelect
          ? searchTypeSelect.value
          : "forma";
        params.set("search_type", uiSearchType);
        // Map Spanish to canonical backend modes for advanced search
        if (uiSearchType === "lema") {
          params.set("mode", "lemma");
        } else if (uiSearchType === "forma") {
          params.set("mode", "forma");
        } else if (uiSearchType === "forma_exacta") {
          params.set("mode", "forma_exacta");
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
    const includeRegional = document.getElementById("include-regional");
    if (includeRegional && includeRegional.checked) {
      params.set("include_regional", "1");
    }

    // (sensitivity already set earlier)

    return params;
  }

  /**
   * Perform search with given parameters
   */
  async performSearch(queryParams) {
    // Dispatch search start event
    document.dispatchEvent(new Event("search:start"));

    const resultsSection = document.getElementById("results-section");
    const summaryBox = document.getElementById("adv-summary");

    try {
      if (summaryBox) {
        summaryBox.hidden = false;
        // MD3 Linear Progress Indicator
        summaryBox.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 8px; width: 100%;">
            <span class="md3-body-medium">Cargando resultados...</span>
            <div role="progressbar" class="md3-linear-progress md3-linear-progress--indeterminate" aria-label="Cargando resultados">
              <div class="md3-linear-progress__buffer"></div>
              <div class="md3-linear-progress__bar md3-linear-progress__primary-bar">
                <span class="md3-linear-progress__bar-inner"></span>
              </div>
              <div class="md3-linear-progress__bar md3-linear-progress__secondary-bar">
                <span class="md3-linear-progress__bar-inner"></span>
              </div>
            </div>
          </div>
        `;
      }

      // Update URL with search params to allow persistence/bookmarks
      const newUrl = `${window.location.pathname}?${queryParams.toString()}`;
      window.history.pushState({ path: newUrl }, "", newUrl);

      // Save to session storage
      sessionStorage.setItem("lastSearch", queryParams.toString());

      // Call existing advanced search handler
      // This should integrate with initTable.js
      const response = await fetch(
        `/search/advanced/data?${queryParams.toString()}`,
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Debug: if the server returned the generated CQL, log it
      if (data && data.cql_debug) {
        console.debug(
          "[SearchUI] Server CQL Debug:",
          data.cql_debug,
          "filter:",
          data.filter_debug || "",
        );
      }

      // Update summary
      if (summaryBox) {
        summaryBox.innerHTML = `
          <span>Resultados encontrados: ${data.recordsFiltered || 0}</span>
        `;
      }

      // Ensure UI container is visible (in case DataTables is initialized while hidden)
      const tableContainer = document.getElementById("datatable-container");
      if (tableContainer) tableContainer.style.display = "";
      const subTabs = document.getElementById("search-sub-tabs");
      if (subTabs) subTabs.style.display = "";

      // Force switch to "Resultados" tab
      const resultsTab = document.getElementById("tab-resultados");
      if (resultsTab) {
        resultsTab.click();
      }

      // Initialize DataTable (this would call existing initTable logic)
      this.initResultsTable(queryParams.toString());

      // Dispatch search complete event
      document.dispatchEvent(new Event("search:complete"));

      console.log("✅ Search completed:", data.recordsFiltered, "results");
    } catch (error) {
      console.error("❌ Search error:", error);
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
    console.log("[SearchUI] Would initialize table with query:", queryString);

    // Initialize DataTable with current query string
    try {
      initAdvancedTable(queryString);
    } catch (e) {
      console.error("[SearchUI] Could not init advanced table:", e);
    }
  }

  /**
   * Bind reset button
   */
  bindResetButton() {
    const resetBtn = document.getElementById("reset-form-btn");
    if (!resetBtn) return;

    resetBtn.addEventListener("click", () => {
      this.resetForm();
    });
  }

  /**
   * Reset entire form
   */
  resetForm() {
    // Reset basic query
    const queryInput = document.getElementById("q");
    const searchTypeSelect = document.getElementById("search_type");

    if (queryInput) queryInput.value = "";
    if (searchTypeSelect) searchTypeSelect.value = "forma";

    // Reset advanced filters
    const advancedInputs = document.querySelectorAll(
      "#advanced-search-options input, #advanced-search-options select",
    );
    advancedInputs.forEach((input) => {
      if (input.type === "checkbox" || input.type === "radio") {
        input.checked = false;
      } else if (input.tagName === "SELECT") {
        input.selectedIndex = -1;
      } else {
        input.value = "";
      }
    });

    // Reset expert mode
    const expertToggle = document.getElementById("expert-mode-toggle");
    if (expertToggle && expertToggle.checked) {
      expertToggle.click(); // Toggle off
    }

    // Clear results
    const resultsContainer = document.getElementById("results-container");
    if (resultsContainer) resultsContainer.innerHTML = "";

    const summaryBox = document.getElementById("search-summary");
    if (summaryBox) summaryBox.innerHTML = "";

    const advSummaryBox = document.getElementById("adv-summary");
    if (advSummaryBox) {
      advSummaryBox.innerHTML = "";
      advSummaryBox.hidden = true;
    }

    // Hide containers
    const tableContainer = document.getElementById("datatable-container");
    if (tableContainer) tableContainer.style.display = "none";
    const subTabs = document.getElementById("search-sub-tabs");
    if (subTabs) subTabs.style.display = "none";

    // Hide stats panel explicitly
    const statsPanel = document.getElementById("panel-estadisticas");
    if (statsPanel) {
      statsPanel.hidden = true;
      statsPanel.classList.remove("md3-view-content--active");
    }

    // Destroy DataTable
    destroyAdvancedTable();

    this.manualCQLEdit = false;

    // Dispatch reset event for other modules (like stats)
    document.dispatchEvent(new Event("search:reset"));

    console.log("[SearchUI] Form reset");
  }

  /**
   * Bind sub-tabs (Resultados / Estadísticas)
   */
  bindSubTabs() {
    // Do not bind to token-sub-tabs in token-tab module; exclude them explicitly
    const tabs = document.querySelectorAll(
      ".md3-stats-tab:not(#token-sub-tabs .md3-stats-tab)",
    );

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
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
    document.querySelectorAll(".md3-stats-tab").forEach((tab) => {
      if (tab.dataset.view === view) {
        tab.classList.add("md3-stats-tab--active");
        tab.setAttribute("aria-selected", "true");
      } else {
        tab.classList.remove("md3-stats-tab--active");
        tab.setAttribute("aria-selected", "false");
      }
    });

    // Update panel visibility
    const panelResultados = document.getElementById("panel-resultados");
    const panelEstadisticas = document.getElementById("panel-estadisticas");

    if (view === "results") {
      if (panelResultados) {
        panelResultados.classList.add("md3-view-content--active");
        panelResultados.removeAttribute("hidden");
      }
      if (panelEstadisticas) {
        panelEstadisticas.classList.remove("md3-view-content--active");
        panelEstadisticas.setAttribute("hidden", "");
      }
    } else if (view === "stats") {
      if (panelResultados) {
        panelResultados.classList.remove("md3-view-content--active");
        panelResultados.setAttribute("hidden", "");
      }
      if (panelEstadisticas) {
        panelEstadisticas.classList.add("md3-view-content--active");
        panelEstadisticas.removeAttribute("hidden");
      }
    }
  }

  /**
   * Show copy feedback on button
   */
  showCopyFeedback(button) {
    const originalText = button.innerHTML;
    button.innerHTML =
      '<span class="material-symbols-rounded">check</span> Copiado';
    setTimeout(() => {
      button.innerHTML = originalText;
    }, 2000);
  }

  /**
   * Fallback copy method using textarea and execCommand
   */
  copyViaFallback(text, button) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "-9999px";
    document.body.appendChild(textarea);

    try {
      textarea.select();
      const successful = document.execCommand("copy");
      if (successful) {
        this.showCopyFeedback(button);
      } else {
        console.warn(
          "[SearchUI] Fallback copy failed: execCommand returned false",
        );
      }
    } catch (err) {
      console.error("[SearchUI] Fallback copy error:", err);
    } finally {
      document.body.removeChild(textarea);
    }
  }

  /**
   * Escape HTML
   */
  escapeHtml(text) {
    if (!text) return "";
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }

  /**
   * Bind CQL Guide Dialog
   */
  bindCqlGuide() {
    const link = document.getElementById("cql-guide-link");
    const overlay = document.getElementById("cql-guide-overlay");
    const dialog = document.getElementById("cql-guide-dialog");
    const closeBtn = document.getElementById("cql-guide-close");
    const copyBtn = document.getElementById("cql-guide-copy");
    const promptText = document.getElementById("cql-guide-prompt");

    if (!link || !overlay || !dialog) return;

    link.addEventListener("click", (e) => {
      e.preventDefault();
      overlay.classList.add("active");
      overlay.removeAttribute("aria-hidden");
      document.body.style.overflow = "hidden";
      dialog.focus();
    });

    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        overlay.classList.remove("active");
        overlay.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
      });
    }

    if (copyBtn && promptText) {
      copyBtn.addEventListener("click", () => {
        // Get plain text from code block - trim whitespace
        const textToCopy = (
          promptText.innerText ||
          promptText.textContent ||
          ""
        ).trim();

        if (!textToCopy) {
          console.warn("[SearchUI] No text to copy");
          return;
        }

        // Always use fallback since it's more reliable in all contexts
        this.copyViaFallback(textToCopy, copyBtn);
      });
    }

    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        overlay.classList.remove("active");
        overlay.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && overlay.classList.contains("active")) {
        overlay.classList.remove("active");
        overlay.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
      }
    });
  }
}

// Auto-initialize
let searchUIInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("advanced-search-form");
  if (form) {
    searchUIInstance = new SearchUI();
  }
});

export function getSearchUI() {
  return searchUIInstance;
}
