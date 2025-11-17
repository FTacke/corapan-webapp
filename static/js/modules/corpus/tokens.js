/**
 * Corpus Token Manager (Compatibility Shim)
 *
 * This file is a minimal compatibility shim for the legacy Tagify-based
 * token manager. The project now uses `token-tab.js` (MD3-native chips).
 * The shim maps a very small set of legacy functions to TokenTab where
 * possible to avoid breaking older code that may still import tokens.js.
 */

export class CorpusTokenManager {
    constructor() {
        // No-op
        console.info('[Corpus] Legacy TokenManager shim loaded. Use TokenTab for new behavior.');
    }

    initialize() {
        if (window.TokenTab) {
            console.info('[Corpus] TokenTab is present; no Tagify initialization required.');
        } else {
            console.warn('[Corpus] TokenTab not present; token input UI disabled.');
        }
    }

    destroy() {
        if (window.TokenTab && typeof window.TokenTab.clearTokens === 'function') {
            window.TokenTab.clearTokens();
        }
    }

    getTokenState() {
        return window.TokenTab ? window.TokenTab.getTokenIds() : [];
    }

    setTokenState(ids) {
        if (window.TokenTab) {
            window.TokenTab.clearTokens();
            window.TokenTab.addTokenIds(ids);
        } else {
            console.warn('[Corpus] setTokenState called but TokenTab not present.');
        }
    }

    initializeTokenDataTable(idsRaw) {
        if (window.TokenTab && typeof window.TokenTab.initializeTokenDataTable === 'function') {
            window.TokenTab.initializeTokenDataTable(idsRaw);
        } else {
            console.warn('[Corpus] initializeTokenDataTable called but TokenTab not present.');
        }
    }
}

// Backwards compatible globals
window.getTokenTabState = function() {
    return window.TokenTab ? window.TokenTab.getTokenIds() : [];
};

window.setTokenTabState = function(ids) {
    if (window.TokenTab) {
        window.TokenTab.clearTokens();
        window.TokenTab.addTokenIds(ids);
    } else {
        console.warn('[Corpus] setTokenTabState called but TokenTab not present.');
    }
};
