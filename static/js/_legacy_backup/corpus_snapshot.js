/**
 * CO.RA.PAN - Snapshot Export/Import mit robuster Serialisierung
 */

$(document).ready(function() {
    initializeSnapshotButtons();
});

/**
 * Snapshot-Buttons initialisieren
 */
function initializeSnapshotButtons() {
    if ($('#corpus-table').length) {
        setTimeout(() => {
            const $buttonContainer = $('.dt-buttons');
            if ($buttonContainer.length) {
                $buttonContainer.append(`
                    <button id="export-snapshot" class="dt-button" title="Exportar estado de búsqueda">
                        <i class="fa-solid fa-camera"></i> Estado
                    </button>
                    <label for="import-snapshot-file" class="dt-button" title="Importar estado de búsqueda">
                        <i class="fa-solid fa-upload"></i> Importar
                    </label>
                    <input type="file" id="import-snapshot-file" accept="application/json" style="display:none">
                `);

                $('#export-snapshot').on('click', exportSnapshot);
                $('#import-snapshot-file').on('change', handleImportFile);
            }
        }, 500);
    }
}

/**
 * Aktuellen Formular-Status erfassen
 */
function currentFormState() {
    const activeTab = $('.corpus-tab.active').data('tab') || 'tab-simple';
    const searchMode = $('#search_mode').val() || 'text';
    const query = $('#query').val() || '';

    // Token-IDs aus Tagify
    let tokenIds = [];
    if (window.getTokenTabState) {
        tokenIds = window.getTokenTabState();
    }

    // Filter-Werte (je nach aktivem Tab)
    let filters = {};
    if (activeTab === 'tab-token') {
        filters = {
            country_code: $('#filter-country-token').val() || [],
            speaker_type: $('#filter-speaker-token').val() || [],
            sex: $('#filter-sex-token').val() || [],
            speech_mode: $('#filter-mode-token').val() || [],
            discourse: $('#filter-discourse-token').val() || []
        };
    } else {
        filters = {
            country_code: $('#filter-country-national').val() || [],
            include_regional: $('#include-regional').is(':checked'),
            speaker_type: $('#filter-speaker').val() || [],
            sex: $('#filter-sex').val() || [],
            speech_mode: $('#filter-mode').val() || [],
            discourse: $('#filter-discourse').val() || []
        };
    }

    // Optional: Exclusions
    const exclusions = window.hiddenRows ? Array.from(window.hiddenRows) : [];

    return {
        schema: "corapan.corpus.snapshot",
        version: 1,
        timestamp: new Date().toISOString(),
        form: {
            active_tab: activeTab,
            search_mode: activeTab === 'tab-token' ? 'token_ids' : searchMode,
            query: query,
            token_ids: tokenIds,
            filters: filters
        },
        exclusions: exclusions
    };
}

/**
 * Snapshot exportieren
 */
function exportSnapshot() {
    try {
        const state = currentFormState();
        const blob = new Blob([JSON.stringify(state, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);

        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const filename = `corapan_snapshot_${timestamp}.json`;

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('Snapshot exportiert:', filename);
    } catch (err) {
        console.error('Fehler beim Export:', err);
        alert('Error al exportar: ' + err.message);
    }
}

/**
 * Import-File-Handler
 */
function handleImportFile(e) {
    const file = e.target.files[0];
    if (!file) return;

    importSnapshot(file);
    e.target.value = '';
}

/**
 * Snapshot importieren mit robuster Token-Serialisierung
 */
function importSnapshot(file) {
    const reader = new FileReader();

    reader.onload = function(e) {
        try {
            const snapshot = JSON.parse(e.target.result);

            // Schema-Validierung
            if (snapshot.schema !== "corapan.corpus.snapshot") {
                throw new Error("Schema inválido. Esperado: corapan.corpus.snapshot");
            }
            if (snapshot.version !== 1) {
                throw new Error("Versión no soportada: " + snapshot.version);
            }

            console.log('Snapshot importiert:', snapshot);

            // Formular-Werte setzen
            restoreFormState(snapshot);

            // Exclusions speichern
            if (snapshot.exclusions && snapshot.exclusions.length > 0) {
                window.snapshotExclusions = new Set(snapshot.exclusions);
            }

            // Bei Token-Modus: robuste Serialisierung
            if (snapshot.form.search_mode === 'token_ids') {
                // Tab aktivieren
                activateTab('tab-token');

                // Search-Mode setzen
                $('#search_mode').val('token_ids');
                $('#active_tab').val('tab-token');

                // Token-IDs setzen
                if (window.setTokenTabState && snapshot.form.token_ids) {
                    window.setTokenTabState(snapshot.form.token_ids);
                }

                // Hidden-Field direkt befüllen
                const tokenStr = (snapshot.form.token_ids || []).join(',');
                $('#token_ids_hidden').val(tokenStr);

                console.log('Token-IDs serialisiert:', tokenStr);

                // Filter für Token-Tab
                $('#filter-country-token').val(snapshot.form.filters.country_code || []).trigger('change');
                $('#filter-speaker-token').val(snapshot.form.filters.speaker_type || []).trigger('change');
                $('#filter-sex-token').val(snapshot.form.filters.sex || []).trigger('change');
                $('#filter-mode-token').val(snapshot.form.filters.speech_mode || []).trigger('change');
                $('#filter-discourse-token').val(snapshot.form.filters.discourse || []).trigger('change');
            } else {
                // Simple-Tab aktivieren
                activateTab('tab-simple');
            }

            // Submit mit kurzer Verzögerung
            setTimeout(() => {
                $('#loading-overlay').addClass('active');
                document.getElementById('corpus-search-form').submit();
            }, 200);

        } catch (err) {
            console.error('Import-Fehler:', err);
            alert('Error al importar: ' + err.message);
        }
    };

    reader.onerror = function() {
        alert('Error al leer el archivo');
    };

    reader.readAsText(file);
}

/**
 * Tab aktivieren
 */
function activateTab(tabId) {
    // Tab-Buttons
    $('.corpus-tab').removeClass('active');
    $(`.corpus-tab[data-tab="${tabId}"]`).addClass('active');

    // Content
    $('.tab-content').removeClass('active');
    $(`#${tabId}`).addClass('active');

    // Hidden-Field
    $('#active_tab').val(tabId);

    // LocalStorage
    try {
        localStorage.setItem('corapan_active_tab', tabId);
    } catch(e) {}
}

/**
 * Formular-Status wiederherstellen (nur Simple-Tab)
 */
function restoreFormState(snapshot) {
    const { form } = snapshot;

    if (form.active_tab === 'tab-simple') {
        $('#query').val(form.query || '');
        $('#search_mode').val(form.search_mode || 'text');

        // Filter setzen
        $('#filter-country-national').val(form.filters.country_code || []).trigger('change');
        $('#include-regional').prop('checked', form.filters.include_regional || false).trigger('change');
        $('#filter-speaker').val(form.filters.speaker_type || []).trigger('change');
        $('#filter-sex').val(form.filters.sex || []).trigger('change');
        $('#filter-mode').val(form.filters.speech_mode || []).trigger('change');
        $('#filter-discourse').val(form.filters.discourse || []).trigger('change');
    }
    // Token-Tab wird in importSnapshot() separat behandelt
}

/**
 * Exclusions nach Tabellen-Init anwenden
 */
function applySnapshotExclusions() {
    if (!window.snapshotExclusions || window.snapshotExclusions.size === 0) return;

    $('#corpus-table tbody tr').each(function() {
        const $row = $(this);
        const tokenId = $row.find('.token-id').text().trim();
        const filename = $row.find('[data-filename]').first().data('filename');
        const startMs = $row.find('[data-start]').first().data('start');

        if (tokenId && filename && startMs) {
            const fingerprint = `${tokenId}|${filename}|${startMs}`;
            if (window.snapshotExclusions.has(fingerprint)) {
                $row.hide();
                console.log('Zeile ausgeblendet:', fingerprint);
            }
        }
    });

    window.snapshotExclusions = null;
}

// Nach DataTable-Init Exclusions anwenden
$(document).on('init.dt', function() {
    setTimeout(applySnapshotExclusions, 100);
});
