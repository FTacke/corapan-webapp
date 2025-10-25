/**
 * CO.RA.PAN - Corpus DataTables Implementation (Server-Side Processing)
 * Hochperformantes Such-Interface mit Server-Side DataTables
 * 
 * PERFORMANCE: 100-2500x schneller bei häufigen Wörtern durch Server-Side Processing
 */

const MEDIA_ENDPOINT = "/media";
const allowTempMedia = (window.ALLOW_PUBLIC_TEMP_AUDIO === 'true') || (window.IS_AUTHENTICATED === 'true');

// Audio State Management
let currentAudio = null;
let currentPlayButton = null;

// DataTable Instance
let corpusTable = null;

/**
 * Initialisierung
 */
$(document).ready(function() {
    initializeSelect2Filters();
    initializeSearchForm();
    initializeResetButton();
    
    if ($('#corpus-table').length) {
        initializeDataTable();
        bindAudioEvents();
        bindPlayerLinks();
    }
});

/**
 * Select2 Multi-Select Dropdowns initialisieren
 */
function initializeSelect2Filters() {
    // Regional options (kept separate for logic)
    const regionalOptions = [
        { value: 'ARG-CHU', text: 'Argentina / Chubut', country: 'ARG' },
        { value: 'ARG-CBA', text: 'Argentina / Córdoba', country: 'ARG' },
        { value: 'ARG-SDE', text: 'Argentina / Santiago del Estero', country: 'ARG' },
        { value: 'ESP-CAN', text: 'España / Canarias', country: 'ESP' },
        { value: 'ESP-SEV', text: 'España / Sevilla', country: 'ESP' }
    ];
    
    $('#filter-speaker, #filter-sex, #filter-mode, #filter-discourse').select2({
        placeholder: 'Seleccionar...',
        allowClear: true,
        closeOnSelect: false,
        language: {
            noResults: function() {
                return "No se encontraron resultados";
            }
        }
    });
    
    // Initialize country select
    $('#filter-country-national').select2({
        placeholder: 'Seleccionar...',
        allowClear: true,
        closeOnSelect: false,
        language: {
            noResults: function() {
                return "No se encontraron resultados";
            }
        }
    });
    
    // Checkbox toggles regional options in país dropdown
    $('#include-regional').on('change', function() {
        const isChecked = $(this).is(':checked');
        const $countrySelect = $('#filter-country-national');
        const currentValues = $countrySelect.val() || [];
        
        if (isChecked) {
            // Add regional options to país dropdown
            regionalOptions.forEach(opt => {
                // Check if option doesn't already exist
                if ($countrySelect.find(`option[value="${opt.value}"]`).length === 0) {
                    const newOption = new Option(opt.text, opt.value, false, false);
                    $countrySelect.append(newOption);
                }
            });
        } else {
            // Remove regional options from país dropdown
            regionalOptions.forEach(opt => {
                $countrySelect.find(`option[value="${opt.value}"]`).remove();
            });
            // Clear any selected regional values
            const filteredValues = currentValues.filter(val => !regionalOptions.some(r => r.value === val));
            $countrySelect.val(filteredValues);
        }
        
        $countrySelect.trigger('change');
    });
    
    // Check if checkbox is already checked on page load (e.g., from URL params)
    if ($('#include-regional').is(':checked')) {
        $('#include-regional').trigger('change');
    }
}

/**
 * Such-Formular Event Handler
 */
function initializeSearchForm() {
    const form = $('#corpus-search-form');
    
    form.on('submit', function(e) {
        e.preventDefault();
        
        // Loading-Overlay anzeigen
        $('#loading-overlay').addClass('active');
        
        // Formular-Daten sammeln
        const formData = new FormData(this);
        const params = new URLSearchParams();
        
        // Query und search_mode
        params.append('query', formData.get('query'));
        params.append('search_mode', formData.get('search_mode'));
        
        // Multi-Select Werte
        const countries = $('#filter-country-national').val();
        const includeRegional = $('#include-regional').is(':checked');
        const speakers = $('#filter-speaker').val();
        const sexes = $('#filter-sex').val();
        const modes = $('#filter-mode').val();
        const discourses = $('#filter-discourse').val();
        
        if (countries && countries.length > 0) {
            countries.forEach(c => params.append('country_code', c));
        }
        if (includeRegional) {
            params.append('include_regional', '1');
        }
        if (speakers && speakers.length > 0) {
            speakers.forEach(s => params.append('speaker_type', s));
        }
        if (sexes && sexes.length > 0) {
            sexes.forEach(s => params.append('sex', s));
        }
        if (modes && modes.length > 0) {
            modes.forEach(m => params.append('speech_mode', m));
        }
        if (discourses && discourses.length > 0) {
            discourses.forEach(d => params.append('discourse', d));
        }
        
        // Zur Suchseite mit Parametern navigieren
        window.location.href = '/corpus/search?' + params.toString();
    });
}

/**
 * Reset-Button Handler
 */
function initializeResetButton() {
    $('#reset-filters').on('click', function() {
        // Formular zurücksetzen
        $('#corpus-search-form')[0].reset();
        
        // Select2 zurücksetzen
        $('#filter-country-national, #filter-country-regional, #filter-speaker, #filter-sex, #filter-mode, #filter-discourse')
            .val(null).trigger('change');
        
        // Checkbox zurücksetzen
        $('#include-regional').prop('checked', false).trigger('change');
        
        // Query-Feld leeren
        $('#query').val('');
    });
}

/**
 * DataTables initialisieren (SERVER-SIDE PROCESSING)
 */
function initializeDataTable() {
    // Get search parameters from URL
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('query') || '';
    const searchMode = urlParams.get('search_mode') || 'text';
    const tokenIds = urlParams.get('token_ids') || '';
    
    corpusTable = $('#corpus-table').DataTable({
        // SERVER-SIDE PROCESSING
        serverSide: true,
        processing: true,
        
        // AJAX Configuration
        ajax: {
            url: '/corpus/search/datatables',
            type: 'GET',
            data: function(d) {
                // Add search parameters
                d.query = query;
                d.search_mode = searchMode;
                d.token_ids = tokenIds;
                
                // Add filters from URL
                const countries = urlParams.getAll('country_code');
                const regions = urlParams.getAll('region_code');
                const includeRegional = urlParams.get('include_regional');
                const speakers = urlParams.getAll('speaker_type');
                const sexes = urlParams.getAll('sex');
                const modes = urlParams.getAll('speech_mode');
                const discourses = urlParams.getAll('discourse');
                
                // Note: We need to pass arrays correctly for Flask's getlist()
                // jQuery automatically serializes arrays as "key[]=val" but Flask expects "key=val1&key=val2"
                // So we manually add each value as a separate parameter
                if (countries.length > 0) {
                    // Don't use d.country_code = countries; as jQuery will serialize it wrong
                    // Instead, we'll let jQuery's traditional mode handle it below
                    d.country_code = countries;
                }
                if (regions.length > 0) {
                    d.region_code = regions;
                }
                if (includeRegional) {
                    d.include_regional = includeRegional;
                }
                if (speakers.length > 0) {
                    d.speaker_type = speakers;
                }
                if (sexes.length > 0) {
                    d.sex = sexes;
                }
                if (modes.length > 0) {
                    d.speech_mode = modes;
                }
                if (discourses.length > 0) {
                    d.discourse = discourses;
                }
                
                return d;
            },
            // CRITICAL FIX: Use traditional jQuery parameter serialization
            // This ensures arrays are sent as "key=val1&key=val2" instead of "key[]=val1&key[]=val2"
            traditional: true,
            dataSrc: 'data',
            error: function(xhr, error, thrown) {
                console.error('DataTables AJAX error:', error, thrown);
            }
        },
        
        // DataTables Optionen
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        language: {
            url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json',
            search: '',
            searchPlaceholder: 'Buscar en tabla...',
            lengthMenu: '_MENU_ registros',
            processing: 'Cargando resultados...'
        },
        stateSave: false,  // Disable with server-side (conflicts)
        
        // Layout
        dom: '<"top"pB<"ml-auto"lf>>rt<"bottom"ip>',
        
        // Buttons für Export
        // Columns: #, Ctx.←, Palabra, Ctx.→, (skip Audio), País, Hablante, Sexo, Modo, Discurso, Token-ID, Archivo
        buttons: [
            {
                extend: 'copyHtml5',
                text: '<i class="fa-solid fa-copy"></i> Copiar',
                exportOptions: {
                    columns: [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11]
                }
            },
            {
                extend: 'csvHtml5',
                text: '<i class="bi bi-filetype-csv"></i> CSV',
                filename: function() {
                    return 'corapan_' + query + '_' + new Date().toISOString().slice(0,10);
                },
                exportOptions: {
                    columns: [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11]
                }
            },
            {
                extend: 'excelHtml5',
                text: '<i class="bi bi-filetype-xlsx"></i> Excel',
                filename: function() {
                    return 'corapan_' + query + '_' + new Date().toISOString().slice(0,10);
                },
                exportOptions: {
                    columns: [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11]
                }
            },
            {
                extend: 'pdfHtml5',
                text: '<i class="bi bi-filetype-pdf"></i> PDF',
                orientation: 'landscape',
                pageSize: 'A4',
                filename: function() {
                    return 'corapan_' + query + '_' + new Date().toISOString().slice(0,10);
                },
                exportOptions: {
                    columns: [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11]
                },
                customize: function(doc) {
                    doc.defaultStyle.fontSize = 8;
                    doc.styles.tableHeader.fontSize = 9;
                }
            }
        ],
        
        // Spalten-Definitionen
        // Order matches backend and HTML: #, Ctx.←, Palabra, Ctx.→, Audio, País, Hablante, Sexo, Modo, Discurso, Token-ID, Arch., Emis.
        columns: [
            { data: 0, width: '40px', className: 'center-align' },  // 0: # (Row number)
            {   // 1: Ctx.← (Contexto izquierdo)
                data: 1, 
                width: '200px', 
                className: 'right-align',
                render: function(data, type, row) {
                    return `<span class="md3-corpus-context">${data || ''}</span>`;
                }
            },
            {   // 2: Palabra (keyword with styling)
                data: 2, 
                width: '100px', 
                className: 'center-align',
                render: function(data, type, row) {
                    const filename = row[11];  // filename is at index 11
                    const start = row[12];     // word start
                    const end = row[13];       // word end
                    return `<span class="md3-corpus-keyword" 
                                  data-filename="${filename}" 
                                  data-start="${start}" 
                                  data-end="${end}">${data || ''}</span>`;
                }
            },
            {   // 3: Ctx.→ (Contexto derecho)
                data: 3, 
                width: '200px',
                render: function(data, type, row) {
                    return `<span class="md3-corpus-context">${data || ''}</span>`;
                }
            },
            {   // 4: Audio Player (Pal + Ctx buttons)
                data: 4,  // Use audio_available for sorting
                orderable: false,
                searchable: false,
                className: 'center-align',
                width: '120px',
                render: function(data, type, row) {
                    const audioAvailable = row[4];   // audio_available boolean
                    const filename = row[11];        // filename
                    const tokenId = row[10];         // token_id
                    const wordStart = row[12];       // word start time
                    const wordEnd = row[13];         // word end time
                    const ctxStart = row[14];        // context start time
                    const ctxEnd = row[15];          // context end time
                    
                    if (!audioAvailable) {
                        return '<span class="text-muted">-</span>';
                    }
                    
                    return `
                        <div class="md3-corpus-audio-buttons">
                          <div class="md3-corpus-audio-row">
                            <span class="md3-corpus-audio-label">Pal:</span>
                            <a class="audio-button" data-filename="${filename}" data-start="${wordStart}" data-end="${wordEnd + 0.1}" data-token-id="${tokenId}" data-type="pal">
                              <i class="fa-solid fa-play"></i>
                            </a>
                            <a class="download-button" data-filename="${filename}" data-start="${wordStart}" data-end="${wordEnd + 0.1}" data-token-id="${tokenId}" data-type="pal">
                              <i class="fa-solid fa-download"></i>
                            </a>
                          </div>
                          <div class="md3-corpus-audio-row">
                            <span class="md3-corpus-audio-label">Ctx:</span>
                            <a class="audio-button" data-filename="${filename}" data-start="${ctxStart}" data-end="${ctxEnd}" data-token-id="${tokenId}" data-type="ctx">
                              <i class="fa-solid fa-play"></i>
                            </a>
                            <a class="download-button" data-filename="${filename}" data-start="${ctxStart}" data-end="${ctxEnd}" data-token-id="${tokenId}" data-type="ctx">
                              <i class="fa-solid fa-download"></i>
                            </a>
                          </div>
                        </div>
                    `;
                }
            },
            { data: 5, width: '80px' },   // 5: País (country_code)
            { data: 6, width: '80px' },   // 6: Hablante (speaker_type)
            { data: 7, width: '80px' },   // 7: Sexo
            { data: 8, width: '80px' },   // 8: Modo
            { data: 9, width: '80px' },   // 9: Discurso
            { data: 10, width: '100px' }, // 10: Token-ID
            {   // 11: Archivo (Combined: file icon with player link)
                data: 11,  // Use column 11 (filename) for sorting
                width: '80px',
                className: 'center-align',
                orderable: true,
                render: function(data, type, row) {
                    const filename = row[11];  // filename (e.g., "2023-08-12_ARG_Mitre.mp3")
                    const tokenId = row[10];   // token_id
                    
                    // For sorting, return just the filename
                    if (type === 'sort' || type === 'type') {
                        return filename;
                    }
                    
                    // For display, show icon with player link
                    // Build full media paths like the old corpus_datatables.js
                    const base = filename.trim().replace(/\.mp3$/i, '');
                    const transcriptionPath = `${MEDIA_ENDPOINT}/transcripts/${base}.json`;
                    const audioPath = `${MEDIA_ENDPOINT}/full/${base}.mp3`;
                    const playerUrl = `/player?transcription=${encodeURIComponent(transcriptionPath)}&audio=${encodeURIComponent(audioPath)}&token_id=${encodeURIComponent(tokenId)}`;
                    
                    return `
                        <a href="${playerUrl}" 
                           class="player-link" 
                           title="${filename}">
                          <i class="fa-regular fa-file"></i>
                        </a>
                    `;
                }
            },
        ],
        
        // Sortierung
        order: [[0, 'asc']],
        
        // Layout
        scrollX: false,
        scrollCollapse: false,
        autoWidth: true,
        
        // Callbacks
        initComplete: function() {
            console.log('DataTable (Server-Side) initialized');
            const api = this.api();
            api.columns.adjust();
            
            // Re-bind audio events after init
            bindAudioEvents();
            bindPlayerLinks();
        },
        
        drawCallback: function() {
            this.api().columns.adjust();
            
            // Re-bind audio events after each draw
            bindAudioEvents();
            bindPlayerLinks();
        }
    });
    
    // Resize-Handler
    $(window).on('resize', function() {
        if (corpusTable) {
            corpusTable.columns.adjust();
        }
    });
}

/**
 * Audio Play Button Events binden
 */
function bindAudioEvents() {
    // Bind to audio-button class (for play buttons)
    $('.audio-button').off('click').on('click', function(e) {
        e.preventDefault();
        const $btn = $(this);
        const filename = $btn.data('filename');
        const start = parseFloat($btn.data('start'));
        const end = parseFloat($btn.data('end'));
        
        playAudioSegment(filename, start, end, $btn);
    });
}

/**
 * Player-Links binden
 */
function bindPlayerLinks() {
    // Bind to any link that opens the player (both old and new style)
    $('a.player-link, a[href^="/player/"]').off('click').on('click', function(e) {
        e.preventDefault();
        
        const playerUrl = $(this).attr('href');
        
        // Check if user is authenticated via the header/navbar
        const headerRoot = document.querySelector('.site-header');
        const isAuthenticated = headerRoot?.dataset.auth === 'true';
        
        if (!isAuthenticated) {
            // Save the intended destination in sessionStorage
            sessionStorage.setItem('_player_redirect_after_login', playerUrl);
            
            // Open login sheet
            const openLoginBtn = document.querySelector('[data-action="open-login"]');
            if (openLoginBtn) {
                openLoginBtn.click();
            }
            return false;
        }
        
        // User is authenticated - just clean up any playing audio and navigate
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
        if (currentPlayButton) {
            currentPlayButton.html('<i class="bi bi-play-fill"></i>');
            currentPlayButton = null;
        }
        
        // Navigate to player
        window.location.href = playerUrl;
        return false;
    });
}

/**
 * Audio-Segment abspielen
 */
function playAudioSegment(filename, start, end, $button) {
    // Prüfen ob Audio erlaubt ist
    if (!allowTempMedia) {
        alert('Audio-Wiedergabe erfordert Authentifizierung');
        return;
    }
    
    // Vorheriges Audio stoppen
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
    }
    if (currentPlayButton) {
        currentPlayButton.html('<i class="fa-solid fa-play"></i>');
    }
    
    // Audio-URL mit Backend-Endpoint erstellen (wie alte Version)
    // Backend schneidet das Segment automatisch zu
    const timestamp = Date.now();
    const audioUrl = `${MEDIA_ENDPOINT}/play_audio/${filename}?start=${start}&end=${end}&t=${timestamp}`;
    
    // Neues Audio erstellen
    currentAudio = new Audio(audioUrl);
    currentPlayButton = $button;
    
    // Button auf "Playing" setzen
    $button.html('<i class="fa-solid fa-stop"></i>');
    
    // Audio direkt abspielen (Backend liefert bereits das zugeschnittene Segment)
    currentAudio.play().catch(function(error) {
        console.error('Audio playback error:', error);
        alert('Audio konnte nicht abgespielt werden');
        $button.html('<i class="fa-solid fa-play"></i>');
    });
    
    // Bei Ende
    currentAudio.addEventListener('ended', function() {
        $button.html('<i class="fa-solid fa-play"></i>');
        currentAudio = null;
        currentPlayButton = null;
    });
    
    // Bei Fehler
    currentAudio.addEventListener('error', function(e) {
        console.error('Audio error:', e);
        alert('Audio konnte nicht geladen werden');
        $button.html('<i class="fa-solid fa-play"></i>');
        currentAudio = null;
        currentPlayButton = null;
    });
}
