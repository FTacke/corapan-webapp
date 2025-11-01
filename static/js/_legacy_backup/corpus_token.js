/**
 * CO.RA.PAN - Token-Suche mit robuster Serialisierung
 */

(function() {
    'use strict';

    const form = document.getElementById('corpus-search-form');
    const hiddenTokens = document.getElementById('token_ids_hidden');
    const searchModeSelect = document.getElementById('search_mode');
    const activeTabHidden = document.getElementById('active_tab');
    const tokenInputEl = document.getElementById('token-input');

    const TOKEN_LIMIT = 2000;

    /**
     * Hilfsfunktion: Token-IDs aus Text extrahieren
     * Unterstützt verschiedene Trennzeichen: ", " oder "," oder "; " oder ";" oder Leerzeichen
     * @param {string} text - Der eingegebene oder eingefügte Text
     * @returns {string[]} - Array von bereinigten Token-IDs
     */
    function parseMultipleTokenIds(text) {
        if (!text || typeof text !== 'string') {
            return [];
        }

        // Zuerst nach verschiedenen Trennzeichen splitten
        // Regex: Split bei Komma, Semikolon, Tabs, Newlines, mehreren Leerzeichen
        const parts = text.split(/[,;\t\n\r]+|\s{2,}/).filter(Boolean);
        
        // Token-IDs validieren und bereinigen
        const tokenIds = [];
        for (let part of parts) {
            // Whitespace entfernen
            const cleaned = part.trim();
            
            // Leere Strings überspringen
            if (!cleaned) continue;
            
            // Token-ID-Format validieren (Buchstaben, Zahlen, Bindestriche)
            // Beispiel: ES-SEVf619e, ES-SEV1026f, ES-SEVc5c3b
            if (/^[A-Za-z0-9-]+$/.test(cleaned)) {
                tokenIds.push(cleaned);
            } else {
                console.warn(`Ungültiges Token-ID-Format übersprungen: "${cleaned}"`);
            }
        }
        
        return tokenIds;
    }

    /**
     * Tagify initialisieren
     */
    function initTagify() {
        if (!tokenInputEl || window.tagify) return;

        window.tagify = new Tagify(tokenInputEl, {
            delimiters: ',;\\s\\n\\r\\t',
            pattern: /^[A-Za-z0-9-]+$/,
            duplicates: false,
            keepInvalidTags: false,
            maxTags: TOKEN_LIMIT,
            editTags: 1,
            enforceWhitelist: false,
            dropdown: {
                enabled: 0
            },
            transformTag: (tagData) => {
                tagData.value = tagData.value.trim();
            }
        });

        // SortableJS für Drag-Reorder
        Sortable.create(window.tagify.DOM.scope, {
            animation: 150,
            draggable: '.tagify__tag',
            forceFallback: true,
            onEnd: function() {
                window.tagify.updateValueByDOMTags();
            }
        });

        // Natives Paste-Event auf dem Tagify-Wrapper (nicht auf dem versteckten Input)
        const tagifyScope = window.tagify.DOM.scope;
        if (tagifyScope) {
            tagifyScope.addEventListener('paste', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                // Text aus Clipboard holen
                const text = (e.clipboardData || window.clipboardData).getData('text') || '';
                
                if (!text) return;
                
                console.log('Paste detected, raw text:', text);
                
                // Token-IDs extrahieren - unterstützt verschiedene Trennzeichen
                const tokenIds = parseMultipleTokenIds(text);
                
                if (tokenIds.length > 0) {
                    console.log(`Pasting ${tokenIds.length} token ID(s):`, tokenIds);
                    // Tags hinzufügen
                    window.tagify.addTags(tokenIds);
                }
            });
        }

        // Enter-Key Handling - unterstützt auch mehrere Token-IDs
        tokenInputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const raw = tokenInputEl.value;
                if (!raw) return;
                tokenInputEl.value = '';
                
                // Token-IDs extrahieren
                const tokenIds = parseMultipleTokenIds(raw);
                if (tokenIds.length > 0) {
                    console.log(`Adding ${tokenIds.length} token ID(s) via Enter:`, tokenIds);
                    window.tagify.addTags(tokenIds);
                }
            }
        });

        // Blur-Event: Wenn Benutzer außerhalb klickt, auch Token-IDs hinzufügen
        tokenInputEl.addEventListener('blur', () => {
            setTimeout(() => {
                const raw = tokenInputEl.value;
                if (!raw || raw.trim() === '') return;
                
                const tokenIds = parseMultipleTokenIds(raw);
                if (tokenIds.length > 0) {
                    console.log(`Adding ${tokenIds.length} token ID(s) via blur:`, tokenIds);
                    window.tagify.addTags(tokenIds);
                    tokenInputEl.value = '';
                }
            }, 100);
        });

        // Limit-Warnung
        window.tagify.on('add', function(e) {
            if (window.tagify.value.length > TOKEN_LIMIT) {
                alert(`Máximo ${TOKEN_LIMIT} tokens permitidos.`);
                window.tagify.removeTag(e.detail.tag);
            }
        });
    }

    /**
     * Token-IDs in Hidden-Field serialisieren
     */
    function serializeTokens() {
        if (!hiddenTokens) return;
        const tokens = window.tagify ? window.tagify.value.map(v => v.value) : [];
        hiddenTokens.value = tokens.join(',');
        console.log('Serialized tokens:', tokens);
    }

    /**
     * Aktiven Tab setzen
     */
    function setActiveTab(tabId) {
        if (activeTabHidden) {
            activeTabHidden.value = tabId;
        }
        try {
            localStorage.setItem('corapan_active_tab', tabId);
        } catch(e) {}
    }

    /**
     * Tab-Switching
     */
    function initTabSwitching() {
        document.querySelectorAll('.corpus-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                if (this.disabled) return;

                const targetTab = this.getAttribute('data-tab');

                // Tab-Buttons aktualisieren
                document.querySelectorAll('.corpus-tab').forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // Content aktualisieren
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                const targetContent = document.getElementById(targetTab);
                if (targetContent) {
                    targetContent.classList.add('active');
                }

                setActiveTab(targetTab);
            });
        });

        // Initial aus LocalStorage
        try {
            const savedTab = localStorage.getItem('corapan_active_tab');
            if (savedTab && activeTabHidden) {
                activeTabHidden.value = savedTab;
            }
        } catch(e) {}
    }

    /**
     * Token-Apply Button Handler
     */
    function initTokenApplyButton() {
        const applyBtn = document.getElementById('token-apply');
        if (!applyBtn) return;

        applyBtn.addEventListener('click', (e) => {
            e.preventDefault();

            // Validierung
            if (!window.tagify || window.tagify.value.length === 0) {
                alert('Por favor ingresa al menos un Token-ID');
                return;
            }

            // Modus setzen - wichtig: auf 'token_ids' setzen
            if (searchModeSelect) {
                searchModeSelect.value = 'token_ids';
            }
            
            // Alternativ: Hidden field hinzufügen falls select nicht existiert
            let searchModeInput = document.getElementById('search_mode_override');
            if (searchModeInput) {
                searchModeInput.value = 'token_ids';
            }

            // Tab fixieren
            setActiveTab('tab-token');

            // Token serialisieren
            serializeTokens();

            // Loading-Overlay
            const overlay = document.getElementById('loading-overlay');
            if (overlay) overlay.classList.add('active');

            // Submit
            if (form) {
                form.submit();
            }
        });
    }

    /**
     * Clear-Button Handler
     */
    function initClearButton() {
        const clearBtn = document.getElementById('clear-tokens');
        if (!clearBtn) return;

        clearBtn.addEventListener('click', () => {
            if (window.tagify) {
                window.tagify.removeAllTags();
            }
            if (hiddenTokens) {
                hiddenTokens.value = '';
            }
        });
    }

    /**
     * Token-Filter Select2 initialisieren
     */
    function initTokenFilters() {
        $('#filter-country-token, #filter-speaker-token, #filter-sex-token, #filter-mode-token, #filter-discourse-token').select2({
            placeholder: 'Seleccionar...',
            allowClear: true,
            closeOnSelect: false,
            language: {
                noResults: function() {
                    return "No se encontraron resultados";
                }
            }
        });
    }

    /**
     * Globaler Form-Submit Hook
     */
    function initFormSubmitHook() {
        if (!form) return;

        form.addEventListener('submit', (e) => {
            // Bei Token-Modus: immer serialisieren
            if (searchModeSelect && searchModeSelect.value === 'token_ids') {
                setActiveTab('tab-token');
                serializeTokens();
            }
        });
    }

    /**
     * Initialisierung
     */
    function init() {
        initTagify();
        initTabSwitching();
        initTokenApplyButton();
        initClearButton();
        initTokenFilters();
        initFormSubmitHook();
    }

    // Document Ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Global verfügbar für Snapshot
    window.getTokenTabState = function() {
        if (!window.tagify) return [];
        return window.tagify.value.map(tag => tag.value);
    };

    window.setTokenTabState = function(tokenIds) {
        if (!window.tagify) return;
        window.tagify.removeAllTags();
        window.tagify.addTags(tokenIds);
    };

})();
