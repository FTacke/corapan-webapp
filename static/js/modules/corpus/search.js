/**
 * Corpus Search Form Manager
 * Verwaltet das Such-Formular und Navigation
 */

export class CorpusSearchManager {
    constructor(filtersManager) {
        this.filtersManager = filtersManager;
        this.form = $('#corpus-search-form');
        this.resetButton = $('#reset-filters');
        this.loadingOverlay = $('#loading-overlay');
    }

    /**
     * Initialize search form and reset button
     */
    initialize() {
        if (!this.form.length) {
            console.warn('Search form not found');
            return;
        }

        this.bindFormSubmit();
        this.bindResetButton();
        
        console.log('✅ Search form initialized');
    }

    /**
     * Bind form submit handler
     */
    bindFormSubmit() {
        this.form.on('submit', (e) => {
            e.preventDefault();
            
            // Show loading overlay
            if (this.loadingOverlay.length) {
                this.loadingOverlay.addClass('active');
            }
            
            // Build URL parameters
            const params = this.buildSearchParams();
            
            // Navigate to search results
            window.location.href = '/corpus/search?' + params.toString();
        });
    }

    /**
     * Build search parameters from form data
     */
    buildSearchParams() {
        const formData = new FormData(this.form[0]);
        const params = new URLSearchParams();
        
        // Query and search mode
        params.append('query', formData.get('query'));
        params.append('search_mode', formData.get('search_mode'));
        
        // Get filter values from FiltersManager
        const filterValues = this.filtersManager.getFilterValues();
        
        // Countries
        if (filterValues.countries && filterValues.countries.length > 0) {
            filterValues.countries.forEach(c => params.append('country_code', c));
        }
        
        // Regional checkbox
        if (filterValues.includeRegional) {
            params.append('include_regional', '1');
        }
        
        // Speakers
        if (filterValues.speaker && filterValues.speaker.length > 0) {
            filterValues.speaker.forEach(s => params.append('speaker_type', s));
        }
        
        // Sex
        if (filterValues.sex && filterValues.sex.length > 0) {
            filterValues.sex.forEach(s => params.append('sex', s));
        }
        
        // Speech modes
        if (filterValues.mode && filterValues.mode.length > 0) {
            filterValues.mode.forEach(m => params.append('speech_mode', m));
        }
        
        // Discourse types
        if (filterValues.discourse && filterValues.discourse.length > 0) {
            filterValues.discourse.forEach(d => params.append('discourse', d));
        }
        
        return params;
    }

    /**
     * Bind reset button handler
     */
    bindResetButton() {
        if (!this.resetButton.length) {
            return;
        }

        this.resetButton.on('click', () => {
            // Reset HTML form
            this.form[0].reset();
            
            // Clear query field explicitly
            $('#query').val('');
            
            // Reset all filters via FiltersManager
            this.filtersManager.reset();
            
            console.log('✅ Search form reset');
        });
    }

    /**
     * Show loading overlay
     */
    showLoading() {
        if (this.loadingOverlay.length) {
            this.loadingOverlay.addClass('active');
        }
    }

    /**
     * Hide loading overlay
     */
    hideLoading() {
        if (this.loadingOverlay.length) {
            this.loadingOverlay.removeClass('active');
        }
    }
}
