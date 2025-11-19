// Deprecated: use js/modules/search/filters.js instead
console.warn('[DEPRECATED] js/modules/corpus/filters.js is deprecated; use js/modules/search/filters.js');

export default {};
// Deprecated: use js/modules/search/filters.js instead
console.warn('[DEPRECATED] js/modules/corpus/filters.js is deprecated; use js/modules/search/filters.js');

export default {};
        this.regionalCheckbox = document.getElementById('include-regional');
        this.countrySelect = document.getElementById('filter-country-national');
        this.filters = {
            speaker: document.getElementById('filter-speaker'),
            sex: document.getElementById('filter-sex'),
            mode: document.getElementById('filter-mode'),
            discourse: document.getElementById('filter-discourse')
        };
        this.isInitialized = false;
    }

    /**
     * Check if dependencies are ready
     */
    depsReady() {
        return !!(window.jQuery && window.jQuery.fn && window.jQuery.fn.select2);
    }

    /**
     * Initialize all Select2 filters with Turbo-aware event handling
     */
    initialize() {
        if (!this.countrySelect) {
            // Silently skip if not on corpus page
            return;
        }

        // Set up Turbo-specific event handlers
        this.setupTurboHandlers();

        // Initial enhancement
        this.enhanceFilters();

        console.log('✅ Corpus filters initialized with Turbo support');
    }

    /**
     * Setup Turbo Drive event handlers
     */
    setupTurboHandlers() {
        // Before Turbo renders new body: mark selects for hydration
        document.addEventListener('turbo:before-render', (e) => {
            const newBody = e.detail.newBody;
            const grid = newBody.querySelector('.md3-corpus-filter-grid');
            if (!grid) return;

            console.log('[Turbo] Preparing new body for hydration');
            newBody.classList.add('corpus-hydrating');
            
            grid.querySelectorAll('select[data-enhance]').forEach(select => {
                select.removeAttribute('data-enhanced'); // Reset for fresh enhancement
                select.setAttribute('data-enhance-pending', ''); // CSS will hide these
            });
        });

        // After Turbo loads new page: enhance filters
        document.addEventListener('turbo:load', () => {
            console.log('[Turbo] Page loaded, enhancing filters');
            this.isInitialized = false; // Reset for new page
            this.updateReferences(); // Get new DOM references
            this.enhanceFilters();
        });

        // Before caching page: cleanup Select2 instances
        document.addEventListener('turbo:before-cache', () => {
            console.log('[Turbo] Cleaning up before cache');
            this.cleanupForCache();
        });

        // Handle back-forward cache
        window.addEventListener('pageshow', (e) => {
            if (e.persisted) {
                console.log('[Turbo] Page restored from bfcache');
                this.updateReferences();
                this.enhanceFilters();
            }
        });
    }

    /**
     * Update DOM references (after Turbo navigation)
     */
    updateReferences() {
        this.regionalCheckbox = document.getElementById('include-regional');
        this.countrySelect = document.getElementById('filter-country-national');
        this.filters = {
            speaker: document.getElementById('filter-speaker'),
            sex: document.getElementById('filter-sex'),
            mode: document.getElementById('filter-mode'),
            discourse: document.getElementById('filter-discourse')
        };
    }

    /**
     * Enhance all filters with Select2 (idempotent)
     */
    enhanceFilters() {
        const grid = document.querySelector('.md3-corpus-filter-grid');
        if (!grid) {
            console.log('[Filters] Grid not found, skipping enhancement');
            return;
        }

        // 1) Check if data/options are ready
        if (!document.documentElement.hasAttribute('data-filters-ready')) {
            console.log('[Filters] Waiting for data to be ready...');
            document.addEventListener('corpus:filters-ready', () => this.enhanceFilters(), { once: true });
            
            // Mark as ready if options already present
            const allSelects = [this.countrySelect, ...Object.values(this.filters)].filter(Boolean);
            const allReady = allSelects.every(s => s && s.options.length > 1);
            if (allReady) {
                document.documentElement.setAttribute('data-filters-ready', '');
            }
            return;
        }

        // 2) Guard: jQuery and Select2 must be present
        if (typeof window.$ === 'undefined' || typeof window.jQuery === 'undefined') {
            console.error('[Filters] jQuery not loaded, cannot initialize Select2');
            return;
        }
        
        if (typeof $.fn.select2 === 'undefined') {
            console.error('[Filters] Select2 plugin not loaded');
            return;
        }

        if (this.isInitialized) {
            console.log('[Filters] Already enhanced, skipping');
            return;
        }

        // 3) Idempotent enhancement
        const allSelects = [this.countrySelect, ...Object.values(this.filters)].filter(Boolean);
        
        allSelects.forEach(select => {
            if (!select || select.hasAttribute('data-enhanced')) {
                return; // Already enhanced
            }
            
            // Skip if already has Select2 instance
            if ($(select).data('select2')) {
                console.log('[Filters] Already has Select2:', select.id);
                return;
            }

            const placeholder = select.dataset.placeholder || 'Seleccionar';
            
            try {
                $(select).select2({
                    ...SELECT2_CONFIG,
                    width: '100%',
                    placeholder: placeholder,
                    allowClear: true,
                    dropdownAutoWidth: true
                });

                select.setAttribute('data-enhanced', '');
                select.removeAttribute('data-enhance-pending');
                console.log(`✅ Enhanced select: ${select.id}`);
            } catch (error) {
                console.error(`❌ Error enhancing select ${select.id}:`, error);
            }
        });

        this.isInitialized = true;

        // 4) Remove hydration flag
        document.body.classList.remove('corpus-hydrating');

        // 5) Setup regional checkbox handler after enhancement
        this.setupRegionalToggle();

        console.log('✅ All filters enhanced');
    }

    /**
     * Cleanup Select2 instances before Turbo caches the page
     */
    cleanupForCache() {
        document.body.classList.remove('corpus-hydrating');
        
        // Guard: Check if jQuery and Select2 are available
        if (typeof window.$ === 'undefined' || typeof $.fn.select2 === 'undefined') {
            console.log('[Filters] jQuery/Select2 not available for cleanup');
            this.isInitialized = false;
            return;
        }
        
        const allSelects = document.querySelectorAll('.md3-corpus-filter-grid select[data-enhance][data-enhanced]');
        
        allSelects.forEach(select => {
            try {
                if ($(select).data('select2')) {
                    $(select).select2('destroy');
                }
                select.removeAttribute('data-enhanced');
                select.removeAttribute('data-enhance-pending');
            } catch (error) {
                console.warn('Error destroying Select2:', error);
            }
        });

        this.isInitialized = false;
        console.log('✅ Select2 instances cleaned up for cache');
    }

    /**
     * Setup regional options toggle
     */
    setupRegionalToggle() {
        if (!this.regionalCheckbox || !this.countrySelect) {
            return;
        }

        $(this.regionalCheckbox).on('change', () => {
            const isChecked = $(this.regionalCheckbox).is(':checked');
            const currentValues = $(this.countrySelect).val() || [];

            if (isChecked) {
                // Add regional options
                REGIONAL_OPTIONS.forEach(opt => {
                    if ($(this.countrySelect).find(`option[value="${opt.value}"]`).length === 0) {
                        const newOption = new Option(opt.text, opt.value, false, false);
                        $(this.countrySelect).append(newOption);
                    }
                });
            } else {
                // Remove regional options
                REGIONAL_OPTIONS.forEach(opt => {
                    $(this.countrySelect).find(`option[value="${opt.value}"]`).remove();
                });
                // Clear selected regional values
                const filteredValues = currentValues.filter(val => 
                    !REGIONAL_OPTIONS.some(r => r.value === val)
                );
                $(this.countrySelect).val(filteredValues);
            }

            $(this.countrySelect).trigger('change');
        });

        // Trigger change if already checked on load
        if ($(this.regionalCheckbox).is(':checked')) {
            $(this.regionalCheckbox).trigger('change');
        }
    }

    /**
     * Get current filter values
     */
    getFilterValues() {
        const values = {};
        
        if (this.countrySelect) {
            values.countries = $(this.countrySelect).val() || [];
            values.includeRegional = $(this.regionalCheckbox).is(':checked');
        }

        Object.entries(this.filters).forEach(([key, element]) => {
            if (element) {
                values[key] = $(element).val() || [];
            }
        });

        return values;
    }

    /**
     * Reset all filters to default
     */
    reset() {
        // Reset Select2 filters
        Object.values(this.filters).forEach(filter => {
            if (filter) {
                $(filter).val(null).trigger('change');
            }
        });

        if (this.countrySelect) {
            $(this.countrySelect).val(null).trigger('change');
        }

        if (this.regionalCheckbox) {
            $(this.regionalCheckbox).prop('checked', false).trigger('change');
        }

        console.log('✅ Filters reset');
    }

    /**
     * Destroy all Select2 instances
     */
    destroy() {
        if (typeof window.$ === 'undefined' || typeof $.fn.select2 === 'undefined') {
            console.log('[Filters] jQuery/Select2 not available for destroy');
            return;
        }
        
        Object.values(this.filters).forEach(filter => {
            if (filter && $(filter).data('select2')) {
                $(filter).select2('destroy');
            }
        });

        if (this.countrySelect && $(this.countrySelect).data('select2')) {
            $(this.countrySelect).select2('destroy');
        }
    }
    
    /**
     * Safe cleanup method for external use
     */
    cleanup() {
        this.destroy();
    }
}
