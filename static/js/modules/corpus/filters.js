/**
 * Corpus Filters Manager
 * Verwaltet Select2-Filter und Regional-Checkbox-Logik
 */

import { REGIONAL_OPTIONS, SELECT2_CONFIG } from './config.js';

export class CorpusFiltersManager {
    constructor() {
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
     * Initialize all Select2 filters
     */
    initialize() {
        if (!this.countrySelect) {
            console.warn('Country select not found, skipping filters initialization');
            return;
        }

        // Initialize standard filters with Select2
        Object.values(this.filters).forEach(filter => {
            if (filter) {
                $(filter).select2(SELECT2_CONFIG);
            }
        });

        // Initialize country select
        $(this.countrySelect).select2(SELECT2_CONFIG);

        // Setup regional checkbox handler
        this.setupRegionalToggle();

        console.log('✅ Corpus filters initialized');
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
        Object.values(this.filters).forEach(filter => {
            if (filter && $(filter).data('select2')) {
                $(filter).select2('destroy');
            }
        });

        if (this.countrySelect && $(this.countrySelect).data('select2')) {
            $(this.countrySelect).select2('destroy');
        }
    }
}
