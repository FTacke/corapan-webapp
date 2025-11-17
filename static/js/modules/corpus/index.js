/**
 * Corpus Module - Main Entry Point
 * Orchestrates all Corpus functionality with DataTables
 * Enhanced with Turbo Drive compatibility
 */

import { CorpusFiltersManager } from './filters.js';
import { CorpusDatatablesManager, adjustCorpusTable } from './datatables.js';
import { CorpusAudioManager } from './audio.js';
import { CorpusSearchManager } from './search.js';
import '../search/corpusForm.js';
// Token input: Tagify-based Token Manager was replaced by `token-tab.js` (MD3 chips)
// Keep compatibility with legacy Tagify if present; otherwise, token-tab.js provides the token UI.

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
        this.isInitialized = false;
    }

    /**
     * Check if external dependencies are loaded
     * @returns {boolean} True if all dependencies are ready
     */
    depsReady() {
        // Core deps: jQuery + DataTables
        const core = !!(window.jQuery && window.jQuery.fn && window.jQuery.fn.dataTable);

        // Select2 only necessary when selects exist and require enhancement
        const selectsPresent = !!document.querySelector('[data-enhance="select2"]');
        const select2Ready = !selectsPresent || !!(window.jQuery && window.jQuery.fn && window.jQuery.fn.select2);

        // Token input: allow either Tagify OR TokenTab (MD3 chips) to satisfy the token UI
        const tokenInputPresent = !!(document.getElementById('token-input') || document.getElementById('tokid-input'));
        const tokenReady = !tokenInputPresent || !!(window.Tagify || window.TokenTab);

        return core && select2Ready && tokenReady;
    }

    /**
     * Wait for external dependencies to be loaded
     * @returns {Promise} Resolves when all dependencies are ready
     */
    async waitForDependencies({ maxAttempts = 50, checkInterval = 200, logInterval = 5 } = {}) {
        // Waits for critical page dependencies with a quieter default logging cadence.
        // Default: 50 attempts * 200ms = 10s total
        for (let i = 0; i < maxAttempts; i++) {
            if (this.depsReady()) {
                console.log('✅ All Corpus dependencies loaded');
                return true;
            }

            // Only log every `logInterval` iterations to avoid spammy logs
            if (i % logInterval === 0) {
                // Use console.debug so it's off by default in production consoles
                console.debug('[Corpus] Waiting for dependencies...', {
                    jQuery: !!window.jQuery,
                    select2: !!(window.jQuery?.fn?.select2),
                    tokenInput: !!(window.Tagify || window.TokenTab),
                    dataTable: !!(window.jQuery?.fn?.dataTable)
                });
            }

            await new Promise(resolve => setTimeout(resolve, checkInterval));
        }

        console.warn('⚠️ Timeout waiting for Corpus dependencies (proceeding with partial init)');
        return false;
    }

    /**
     * Initialize all Corpus components
     */
    async initialize() {
        if (this.isInitialized) {
            console.log('[Corpus] Already initialized, skipping');
            return;
        }

        // Check if we're on a corpus page before initializing
        const isCorpusPage = document.querySelector('.md3-corpus-page') || 
                            document.querySelector('#corpus-search-form') ||
                            document.querySelector('#corpus-table');
        
        if (!isCorpusPage) {
            console.log('[Corpus] Not on corpus page, skipping initialization');
            return;
        }

        console.log('🚀 Initializing Corpus Module...');

        // Wait for dependencies to be ready
        if (!this.depsReady()) {
            console.log('[Corpus] Dependencies not ready; waiting (quiet mode)...');
            // Wait for dependencies but continue initializing audio manager even if some optional deps
            // don't become available. This ensures basic features like audio playback are available.
            await this.waitForDependencies({ maxAttempts: 50, checkInterval: 200, logInterval: 10 });
            if (!this.depsReady()) {
                console.warn('[Corpus] Dependencies still not ready after wait; proceeding with partial initialization');
            }
        }

        try {
            // Mark filters as ready if options are already present
            const grid = document.querySelector('.md3-corpus-filter-grid');
            if (grid) {
                const selects = grid.querySelectorAll('select[data-enhance]');
                const allReady = Array.from(selects).every(s => s.options.length > 1);
                if (allReady) {
                    document.documentElement.setAttribute('data-filters-ready', '');
                }
            }

            // 1. Initialize Audio Manager (early) so Play buttons work even if other modules fail
            console.log('[Corpus] Step 1: Initializing Audio Manager (early)');
            try {
                this.audio = new CorpusAudioManager();
                this.audio.bindEvents();
            } catch (err) {
                console.warn('[Corpus] Audio Manager init error (non-fatal):', err);
            }

            // 2. Initialize Filters (Select2) - handles Turbo events internally
            console.log('[Corpus] Step 2: Initializing Filters...');
            this.filters = new CorpusFiltersManager();
            this.filters.initialize();

            // 2. Initialize Token Input - if a legacy Tagify-based manager is present, initialize it
            console.log('[Corpus] Step 2: Initializing Token Manager (Tagify if present)...');
            try {
                if (window.Tagify) {
                    // Dynamically import the legacy Tagify token manager only when Tagify exists
                    const { CorpusTokenManager } = await import('./tokens.js');
                    this.tokens = new CorpusTokenManager();
                    this.tokens.initialize();
                } else if (window.TokenTab) {
                    // token-tab is MD3-native and auto-initializes itself in `token-tab.js`
                    console.log('[Corpus] TokenTab present (native MD3 chips). Tagify not required.');
                } else {
                    console.log('[Corpus] No token input manager found (Tagify or TokenTab). Token input disabled.');
                }
            } catch (err) {
                console.warn('[Corpus] Token Manager init error (non-fatal):', err);
            }

            // 3. Initialize Search Form (depends on filters)
            console.log('[Corpus] Step 3: Initializing Search Manager...');
            this.search = new CorpusSearchManager(this.filters);
            this.search.initialize();

            // 4. Initialize DataTables (if on results page)
            if ($('#corpus-table').length) {
                console.log('[Corpus] Step 4: Initializing DataTables...');
                this.datatables = new CorpusDatatablesManager();
                this.datatables.initialize();
                
                // Adjust columns after visible
                setTimeout(() => this.adjustTableIfVisible(), 250);
            } else {
                console.log('[Corpus] Step 4: Skipping DataTables (no table found)');
            }

            // 5. Initialize Audio Manager (always available)
            console.log('[Corpus] Step 5: Initializing Audio Manager...');
            this.audio = new CorpusAudioManager();
            this.audio.bindEvents();

            this.isInitialized = true;
            console.log('✅ Corpus Module initialized successfully');
            
            // Dispatch ready event (triggers filter enhancement if not yet done)
            document.dispatchEvent(new Event('corpus:filters-ready'));
        } catch (error) {
            console.error('❌ Error initializing Corpus Module:', error);
        }
    }

    /**
     * Adjust DataTable if container is visible
     */
    adjustTableIfVisible() {
        const tableContainer = document.querySelector('.md3-corpus-table-container');
        if (tableContainer && $.fn.dataTable.isDataTable('#corpus-table')) {
            requestAnimationFrame(() => {
                $('#corpus-table').DataTable().columns.adjust();
                if ($('#corpus-table').DataTable().responsive) {
                    $('#corpus-table').DataTable().responsive.recalc();
                }
                console.log('[Corpus] Table adjusted after initialization');
            });
        }
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
        this.isInitialized = false;
    }
}

// Global instance
let corpusAppInstance = null;

/**
 * Initialize Corpus App (idempotent)
 */
function initCorpusApp() {
    if (!corpusAppInstance) {
        corpusAppInstance = new CorpusApp();
        corpusAppInstance.initialize();
    } else if (!corpusAppInstance.isInitialized) {
        corpusAppInstance.initialize();
    } else {
        console.log('[Corpus] App already initialized');
    }
}

// Initialize on DOM ready
$(document).ready(() => {
    console.log('[Corpus] DOM ready, initializing...');
    initCorpusApp();
});

// Fallback: Initialize on window load
window.addEventListener('load', () => {
    console.log('[Corpus] Window loaded');
    initCorpusApp();
}, { once: true });

// Global event handlers for DataTable adjustment
document.addEventListener('turbo:load', () => {
    console.log('[Corpus] Turbo:load event');
    
    // Reset initialization flag for new page
    if (corpusAppInstance) {
        corpusAppInstance.isInitialized = false;
    }
    
    // Re-initialize for new page
    initCorpusApp();
    
    // Adjust table if present
    adjustCorpusTable();
    
    // If on results page, fire results-updated event
    if (document.querySelector('#corpus-table')) {
        requestAnimationFrame(() => {
            document.dispatchEvent(new Event('corpus:results-updated'));
        });
    }
});

// Custom events for accordion and results updates
document.addEventListener('corpus:accordion-open', () => {
    console.log('[Corpus] Accordion opened, adjusting table...');
    adjustCorpusTable();
});

document.addEventListener('corpus:results-updated', () => {
    console.log('[Corpus] Results updated, adjusting table...');
    adjustCorpusTable();
});

// Export for external use
export { corpusAppInstance, adjustCorpusTable };

