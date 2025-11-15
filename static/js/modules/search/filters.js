/**
 * Search UI Filters Module
 * Handles MD3 filter fields and active filter chips
 * 
 * Features:
 * - Custom filter field UI with dropdown menus
 * - Multi-select with checkboxes
 * - Synchronization with hidden <select multiple> for backend
 * - Active filter chip bar with color coding
 * - Click-to-remove functionality
 */

export class SearchFilters {
  constructor() {
    this.filterFields = new Map();
    this.activeFilters = new Map();
    this.init();
  }

  init() {
    // Initialize all filter fields
    document.querySelectorAll('.md3-filter-field').forEach(field => {
      this.initFilterField(field);
    });

    // Bind active filter chip removal
    this.bindChipRemoval();
  }

  /**
   * Initialize a single filter field
   */
  initFilterField(field) {
    const facet = field.dataset.facet;
    const trigger = field.querySelector('.md3-filter-field__trigger');
    const menu = field.querySelector('.md3-filter-field__menu');
    const valueDisplay = field.querySelector('.md3-filter-field__value');
    const checkboxes = field.querySelectorAll('input[type="checkbox"]');
    const hiddenSelect = field.querySelector('select[multiple][hidden]');

    if (!trigger || !menu || !valueDisplay || !hiddenSelect) {
      console.warn('[SearchFilters] Missing required elements for filter field:', facet);
      return;
    }

    // Store references
    this.filterFields.set(facet, {
      field,
      trigger,
      menu,
      valueDisplay,
      checkboxes,
      hiddenSelect,
      placeholder: valueDisplay.dataset.placeholder || 'Todos'
    });

    // Toggle menu on trigger click
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleMenu(facet);
    });

    // Handle keyboard navigation
    trigger.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.toggleMenu(facet);
      }
    });

    // Handle checkbox changes
    checkboxes.forEach(checkbox => {
      checkbox.addEventListener('change', () => {
        this.updateFilterField(facet);
      });
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!field.contains(e.target)) {
        this.closeMenu(facet);
      }
    });

    // Initialize from URL parameters
    this.initializeFromURL(facet);
  }

  /**
   * Initialize filter values from URL parameters
   */
  initializeFromURL(facet) {
    const params = new URLSearchParams(window.location.search);
    const filterConfig = this.filterFields.get(facet);
    if (!filterConfig) return;

    const backendParamName = filterConfig.hiddenSelect.name;
    const values = params.getAll(backendParamName);

    if (values.length > 0) {
      filterConfig.checkboxes.forEach(checkbox => {
        if (values.includes(checkbox.value)) {
          checkbox.checked = true;
        }
      });
      this.updateFilterField(facet);
    }
  }

  /**
   * Toggle menu open/closed
   */
  toggleMenu(facet) {
    const filterConfig = this.filterFields.get(facet);
    if (!filterConfig) return;

    const isExpanded = filterConfig.trigger.getAttribute('aria-expanded') === 'true';
    
    // Close all other menus first
    this.filterFields.forEach((config, otherFacet) => {
      if (otherFacet !== facet) {
        this.closeMenu(otherFacet);
      }
    });

    if (isExpanded) {
      this.closeMenu(facet);
    } else {
      this.openMenu(facet);
    }
  }

  /**
   * Open menu
   */
  openMenu(facet) {
    const filterConfig = this.filterFields.get(facet);
    if (!filterConfig) return;

    filterConfig.trigger.setAttribute('aria-expanded', 'true');
    filterConfig.menu.removeAttribute('hidden');
  }

  /**
   * Close menu
   */
  closeMenu(facet) {
    const filterConfig = this.filterFields.get(facet);
    if (!filterConfig) return;

    filterConfig.trigger.setAttribute('aria-expanded', 'false');
    filterConfig.menu.setAttribute('hidden', '');
  }

  /**
   * Update filter field display and sync with hidden select
   */
  updateFilterField(facet) {
    const filterConfig = this.filterFields.get(facet);
    if (!filterConfig) return;

    const selectedValues = [];
    const selectedLabels = [];

    // Collect selected values and labels
    filterConfig.checkboxes.forEach(checkbox => {
      if (checkbox.checked) {
        selectedValues.push(checkbox.value);
        selectedLabels.push(checkbox.dataset.label || checkbox.value);
      }
    });

    // Update display
    if (selectedValues.length === 0) {
      filterConfig.valueDisplay.textContent = '';
      filterConfig.valueDisplay.dataset.placeholder = filterConfig.placeholder;
    } else {
      filterConfig.valueDisplay.textContent = selectedLabels.join(', ');
    }

    // Sync with hidden select
    this.syncHiddenSelect(facet, selectedValues);

    // Update active filters
    this.updateActiveFilters(facet, selectedValues, selectedLabels);

    // Update chip bar visibility and content
    this.renderChips();
  }

  /**
   * Sync hidden select element with selected values
   */
  syncHiddenSelect(facet, selectedValues) {
    const filterConfig = this.filterFields.get(facet);
    if (!filterConfig) return;

    const select = filterConfig.hiddenSelect;
    
    // Clear all selections
    Array.from(select.options).forEach(option => {
      option.selected = false;
    });

    // Set selected values
    selectedValues.forEach(value => {
      const option = select.querySelector(`option[value="${value}"]`);
      if (option) {
        option.selected = true;
      }
    });
  }

  /**
   * Update active filters map
   */
  updateActiveFilters(facet, values, labels) {
    if (values.length === 0) {
      this.activeFilters.delete(facet);
    } else {
      this.activeFilters.set(facet, {
        values,
        labels,
        facet
      });
    }
  }

  /**
   * Render active filter chips
   */
  renderChips() {
    const chipsContainer = document.getElementById('active-filters-chips');
    const filterBar = document.getElementById('active-filters-bar');
    
    if (!chipsContainer || !filterBar) return;

    // Clear existing chips
    chipsContainer.innerHTML = '';

    // Check if there are any active filters
    if (this.activeFilters.size === 0) {
      filterBar.setAttribute('hidden', '');
      return;
    }

    // Show filter bar
    filterBar.removeAttribute('hidden');

    // Create chips for each filter
    this.activeFilters.forEach((filter, facet) => {
      filter.values.forEach((value, index) => {
        const chip = this.createChip(facet, value, filter.labels[index]);
        chipsContainer.appendChild(chip);
      });
    });
  }

  /**
   * Create a filter chip element
   */
  createChip(facet, value, label) {
    const chip = document.createElement('div');
    chip.className = `md3-filter-chip md3-filter-chip--${facet}`;
    chip.setAttribute('role', 'button');
    chip.setAttribute('tabindex', '0');
    chip.dataset.facet = facet;
    chip.dataset.value = value;

    // Chip text - for countries, show only code (value); for others, show facet + label
    let chipText = '';
    if (facet === 'pais') {
      chipText = value; // Use code directly (ARG, MEX, etc.)
    } else {
      const facetLabels = {
        'hablante': 'Hablante',
        'sexo': 'Sexo',
        'modo': 'Modo',
        'discurso': 'Discurso'
      };
      chipText = `${facetLabels[facet] || facet}: ${label}`;
    }

    chip.innerHTML = `
      <span>${chipText}</span>
      <span class="material-symbols-rounded md3-filter-chip__close">close</span>
    `;

    // Click to remove
    chip.addEventListener('click', () => {
      this.removeFilter(facet, value);
    });

    // Keyboard support
    chip.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.removeFilter(facet, value);
      }
    });

    return chip;
  }

  /**
   * Remove a specific filter value
   */
  removeFilter(facet, value) {
    const filterConfig = this.filterFields.get(facet);
    if (!filterConfig) return;

    // Uncheck the corresponding checkbox
    filterConfig.checkboxes.forEach(checkbox => {
      if (checkbox.value === value) {
        checkbox.checked = false;
      }
    });

    // Update the filter field
    this.updateFilterField(facet);
  }

  /**
   * Bind chip removal events
   */
  bindChipRemoval() {
    // Event delegation is handled in createChip
    // This method is kept for future enhancements
  }

  /**
   * Clear all filters
   */
  clearAllFilters() {
    this.filterFields.forEach((config, facet) => {
      config.checkboxes.forEach(checkbox => {
        checkbox.checked = false;
      });
      this.updateFilterField(facet);
    });
  }

  /**
   * Get all active filter values for form submission
   */
  getActiveFilterParams() {
    const params = new URLSearchParams();
    
    this.filterFields.forEach((config, facet) => {
      const selectedValues = Array.from(config.checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);
      
      const paramName = config.hiddenSelect.name;
      selectedValues.forEach(value => {
        params.append(paramName, value);
      });
    });

    return params;
  }
}

// Auto-initialize on page load
let searchFiltersInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  searchFiltersInstance = new SearchFilters();
});

// Export singleton instance
export function getSearchFilters() {
  return searchFiltersInstance;
}
