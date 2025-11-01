/**
 * Corpus Module - Main Entry Point
 * Orchestrates all Corpus functionality with DataTables
 */

import { CorpusFiltersManager } from './filters.js';
import { CorpusDatatablesManager } from './datatables.js';
import { CorpusAudioManager } from './audio.js';
import { CorpusSearchManager } from './search.js';
import { CorpusTokenManager } from './tokens.js';

/**
 * Main Corpus Application Class
 */
class CorpusApp {
    constructor() {
        this.filters = null;
        this.datatables = null;
        this.audio = null;
        this.search = null;
        this.tokens = null;
    }

    /**
     * Initialize all Corpus components
     */
    initialize() {
        console.log('🚀 Initializing Corpus Module...');

        // 1. Initialize Filters (Select2)
        this.filters = new CorpusFiltersManager();
        this.filters.initialize();

        // 2. Initialize Token Input (Tagify)
        this.tokens = new CorpusTokenManager();
        this.tokens.initialize();

        // 3. Initialize Search Form (depends on filters)
        this.search = new CorpusSearchManager(this.filters);
        this.search.initialize();

        // 4. Initialize DataTables (if on results page)
        if ($('#corpus-table').length) {
            this.datatables = new CorpusDatatablesManager();
            this.datatables.initialize();
        }

        // 5. Initialize Audio Manager (always available)
        this.audio = new CorpusAudioManager();
        this.audio.bindEvents();

        console.log('✅ Corpus Module initialized successfully');
    }

    /**
     * Cleanup on page unload
     */
    destroy() {
        if (this.filters) {
            this.filters.destroy();
        }
        if (this.tokens) {
            this.tokens.destroy();
        }
        if (this.datatables) {
            this.datatables.destroy();
        }
        if (this.audio) {
            this.audio.destroy();
        }
    }
}

// Initialize on DOM ready
$(document).ready(() => {
    const app = new CorpusApp();
    app.initialize();

    // Cleanup on page unload
    $(window).on('unload', () => {
        app.destroy();
    });
});

