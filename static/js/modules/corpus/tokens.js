/**
 * Corpus Token Input Manager
 * Verwaltet Token-ID-Eingabe mit Tagify
 */

export class CorpusTokenManager {
    constructor() {
        this.tokenInput = document.getElementById('token-input');
        this.hiddenTokens = document.getElementById('token_ids_hidden');
        this.applyButton = document.getElementById('token-apply');
        this.clearButton = document.getElementById('clear-tokens');
        this.form = document.getElementById('corpus-search-form');
        this.searchModeOverride = document.getElementById('search_mode_override');
        
        this.tagify = null;
        this.TOKEN_LIMIT = 2000;
    }

    /**
     * Initialize Token Input with Tagify
     */
    initialize() {
        if (!this.tokenInput || !window.Tagify) {
            // Silently skip if not on corpus page or Tagify not loaded
            return;
        }

        this.initTagify();
        this.bindButtons();
        this.restoreTokens();
        
        console.log('✅ Token input initialized');
    }

    /**
     * Initialize Tagify on token input
     */
    initTagify() {
        this.tagify = new Tagify(this.tokenInput, {
            delimiters: ',;\\s\\n\\r\\t',
            pattern: /^[A-Za-z0-9-]+$/,
            duplicates: false,
            keepInvalidTags: false,
            maxTags: this.TOKEN_LIMIT,
            editTags: 1,
            enforceWhitelist: false,
            dropdown: {
                enabled: 0
            },
            transformTag: (tagData) => {
                tagData.value = tagData.value.trim();
            }
        });

        // Make globally accessible for restore
        window.tagify = this.tagify;

        // Enable drag-and-drop reordering with SortableJS
        if (window.Sortable) {
            Sortable.create(this.tagify.DOM.scope, {
                animation: 150,
                draggable: '.tagify__tag',
                forceFallback: true,
                onEnd: () => {
                    this.tagify.updateValueByDOMTags();
                }
            });
        }

        // Handle paste events for multi-token input
        this.setupPasteHandler();

        // Handle Enter key for adding tokens
        this.setupEnterHandler();

        // Handle blur event
        this.setupBlurHandler();

        // Limit warning
        this.tagify.on('add', (e) => {
            if (this.tagify.value.length > this.TOKEN_LIMIT) {
                alert(`Máximo ${this.TOKEN_LIMIT} tokens permitidos.`);
                this.tagify.removeTag(e.detail.tag);
            }
        });
    }

    /**
     * Setup paste handler for multi-token input
     */
    setupPasteHandler() {
        const tagifyScope = this.tagify.DOM.scope;
        if (tagifyScope) {
            tagifyScope.addEventListener('paste', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const text = (e.clipboardData || window.clipboardData).getData('text') || '';
                if (!text) return;
                
                console.log('Paste detected, raw text:', text);
                
                const tokenIds = this.parseMultipleTokenIds(text);
                if (tokenIds.length > 0) {
                    console.log(`Pasting ${tokenIds.length} token ID(s):`, tokenIds);
                    this.tagify.addTags(tokenIds);
                }
            });
        }
    }

    /**
     * Setup Enter key handler
     */
    setupEnterHandler() {
        this.tokenInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const raw = this.tokenInput.value;
                if (!raw) return;
                this.tokenInput.value = '';
                
                const tokenIds = this.parseMultipleTokenIds(raw);
                if (tokenIds.length > 0) {
                    console.log(`Adding ${tokenIds.length} token ID(s) via Enter:`, tokenIds);
                    this.tagify.addTags(tokenIds);
                }
            }
        });
    }

    /**
     * Setup blur handler
     */
    setupBlurHandler() {
        this.tokenInput.addEventListener('blur', () => {
            setTimeout(() => {
                const raw = this.tokenInput.value;
                if (!raw || raw.trim() === '') return;
                
                const tokenIds = this.parseMultipleTokenIds(raw);
                if (tokenIds.length > 0) {
                    console.log(`Adding ${tokenIds.length} token ID(s) via blur:`, tokenIds);
                    this.tagify.addTags(tokenIds);
                    this.tokenInput.value = '';
                }
            }, 100);
        });
    }

    /**
     * Parse multiple token IDs from text
     * Supports various delimiters: comma, semicolon, newline, tab, multiple spaces
     */
    parseMultipleTokenIds(text) {
        if (!text || typeof text !== 'string') {
            return [];
        }

        // Split by comma, semicolon, tabs, newlines, or multiple spaces
        const parts = text.split(/[,;\t\n\r]+|\s{2,}/).filter(Boolean);
        
        const tokenIds = [];
        for (let part of parts) {
            const cleaned = part.trim();
            if (!cleaned) continue;
            
            // Validate token ID format (letters, numbers, hyphens)
            // Example: ES-SEVf619e, ES-SEV1026f, ES-SEVc5c3b
            if (/^[A-Za-z0-9-]+$/.test(cleaned)) {
                tokenIds.push(cleaned);
            } else {
                console.warn(`Invalid token ID format skipped: "${cleaned}"`);
            }
        }
        
        return tokenIds;
    }

    /**
     * Bind button handlers
     */
    bindButtons() {
        // Apply button - submit search with tokens
        if (this.applyButton) {
            this.applyButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.applyTokenSearch();
            });
        }

        // Clear button - remove all tokens
        if (this.clearButton) {
            this.clearButton.addEventListener('click', () => {
                this.clearTokens();
            });
        }
    }

    /**
     * Apply token search
     */
    applyTokenSearch() {
        // Validate
        if (!this.tagify || this.tagify.value.length === 0) {
            alert('Por favor ingresa al menos un Token-ID');
            return;
        }

        // Set search mode to token_ids
        if (this.searchModeOverride) {
            this.searchModeOverride.value = 'token_ids';
        }

        // Serialize tokens to hidden field
        this.serializeTokens();

        // Show loading overlay
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.removeAttribute('hidden');
        }

        // Submit form
        if (this.form) {
            this.form.submit();
        }
    }

    /**
     * Clear all tokens
     */
    clearTokens() {
        if (this.tagify) {
            this.tagify.removeAllTags();
        }
        if (this.hiddenTokens) {
            this.hiddenTokens.value = '';
        }
    }

    /**
     * Serialize tokens to hidden field
     */
    serializeTokens() {
        if (!this.hiddenTokens) return;
        const tokens = this.tagify ? this.tagify.value.map(v => v.value) : [];
        this.hiddenTokens.value = tokens.join(',');
        console.log('Serialized tokens:', tokens);
    }

    /**
     * Restore tokens from hidden field (for page reload)
     */
    restoreTokens() {
        if (!this.hiddenTokens || !this.tagify) return;
        
        const tokenIds = this.hiddenTokens.value;
        if (tokenIds) {
            const tokens = tokenIds.split(',').map(t => t.trim()).filter(t => t);
            if (tokens.length > 0) {
                console.log('Restoring tokens:', tokens);
                this.tagify.addTags(tokens);
            }
        }
    }

    /**
     * Get current token state (for external use)
     */
    getTokenState() {
        if (!this.tagify) return [];
        return this.tagify.value.map(tag => tag.value);
    }

    /**
     * Set token state (for external use)
     */
    setTokenState(tokenIds) {
        if (!this.tagify) return;
        this.tagify.removeAllTags();
        this.tagify.addTags(tokenIds);
    }

    /**
     * Cleanup
     */
    destroy() {
        if (this.tagify) {
            this.tagify.destroy();
        }
    }
}

// Make globally accessible for backward compatibility
window.getTokenTabState = function() {
    if (!window.tagify) return [];
    return window.tagify.value.map(tag => tag.value);
};

window.setTokenTabState = function(tokenIds) {
    if (!window.tagify) return;
    window.tagify.removeAllTags();
    window.tagify.addTags(tokenIds);
};
