/**
 * Corpus DataTables Manager
 * Verwaltet DataTables mit Server-Side Processing
 */

import { MEDIA_ENDPOINT, allowTempMedia } from './config.js';

// Global DataTable instance for external access
let corpusTable = null;

export class CorpusDatatablesManager {
    constructor() {
        this.table = null;
        this.tableElement = $('#corpus-table');
        this.urlParams = new URLSearchParams(window.location.search);
        this.query = this.urlParams.get('query') || '';
        this.searchMode = this.urlParams.get('search_mode') || 'text';
        this.tokenIds = this.urlParams.get('token_ids') || '';
    }

    /**
     * Initialize DataTables with server-side processing
     */
    initialize() {
        if (!this.tableElement.length) {
            console.warn('Corpus table element not found');
            return;
        }

        // Check if already initialized
        if ($.fn.dataTable.isDataTable(this.tableElement)) {
            console.log('[DataTable] Already initialized, adjusting columns...');
            this.table = this.tableElement.DataTable();
            corpusTable = this.table;
            this.adjustColumns();
            return;
        }

        this.table = this.tableElement.DataTable({
            // SERVER-SIDE PROCESSING
            serverSide: true,
            processing: true,
            
            // AJAX Configuration
            ajax: {
                url: '/corpus/search/datatables',
                type: 'GET',
                data: (d) => this.buildAjaxData(d),
                traditional: true,  // CRITICAL: Use traditional parameter serialization for arrays
                dataSrc: 'data',
                error: (xhr, error, thrown) => {
                    console.error('DataTables AJAX error:', error, thrown, xhr);
                    console.error('Response:', xhr.responseText);
                }
            },
            
            // DataTables Options
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
            searching: true,   // Enable searching (handled server-side)
            ordering: true,    // Enable ordering (handled server-side)
            
            // Layout with Export Buttons
            dom: '<"top"pB<"ml-auto"lf>>rt<"bottom"ip>',
            
            // Export Buttons (skip Audio column)
            buttons: this.buildExportButtons(),
            
            // Column Definitions
            columns: this.buildColumns(),
            
            // Default Sorting
            order: [[0, 'asc']],
            
            // Layout - no horizontal scrolling, container handles overflow
            scrollX: false,
            scrollCollapse: false,
            autoWidth: false,  // Disable auto width to respect our column definitions
            
            // Callbacks
            initComplete: () => {
                console.log('✅ DataTable (Server-Side) initialized');
                corpusTable = this.table;
                // Only adjust columns once on init
                setTimeout(() => this.adjustColumns(), 100);
            },
            
            drawCallback: () => {
                // Don't adjust columns on every draw to prevent pixel shifts
                // this.adjustColumns();
            }
        });

        corpusTable = this.table;

        // Resize handler
        $(window).on('resize', () => {
            this.adjustColumns();
        });

        console.log('[DataTable] Initialization complete');
    }

    /**
     * Adjust DataTable columns (idempotent, safe to call repeatedly)
     */
    adjustColumns() {
        if (this.table) {
            requestAnimationFrame(() => {
                try {
                    this.table.columns.adjust();
                    if (this.table.responsive) {
                        this.table.responsive.recalc();
                    }
                    console.log('[DataTable] Columns adjusted');
                } catch (e) {
                    console.warn('[DataTable] Error adjusting columns:', e);
                }
            });
        }
    }

    /**
     * Build AJAX data parameters from URL
     */
    buildAjaxData(d) {
        // Debug: Log DataTables parameters
        console.log('[DataTables AJAX] Request params:', {
            draw: d.draw,
            start: d.start,
            length: d.length,
            order: d.order,
            order_details: d.order && d.order[0] ? d.order[0] : null,
            search: d.search
        });
        
        // Flatten order parameters for Flask (from array/object to query string format)
        // DataTables sends: order: [{column: 5, dir: 'asc'}]
        // Flask expects: order[0][column]=5&order[0][dir]=asc
        if (d.order && d.order.length > 0) {
            d['order[0][column]'] = d.order[0].column;
            d['order[0][dir]'] = d.order[0].dir;
            delete d.order; // Remove the array version
        }
        
        // Flatten search parameter for Flask
        // DataTables sends: search: {value: 'searchterm', regex: false}
        // Flask expects: search[value]=searchterm
        if (d.search && d.search.value) {
            d['search[value]'] = d.search.value;
        }
        delete d.search; // Remove the object version
        
        // Flatten columns array (remove it to reduce payload size)
        delete d.columns;
        
        // Add search parameters
        d.query = this.query;
        d.search_mode = this.searchMode;
        d.token_ids = this.tokenIds;
        
        // Add filters from URL
        const countries = this.urlParams.getAll('country_code');
        const regions = this.urlParams.getAll('region_code');
        const includeRegional = this.urlParams.get('include_regional');
        const speakers = this.urlParams.getAll('speaker_type');
        const sexes = this.urlParams.getAll('sex');
        const modes = this.urlParams.getAll('speech_mode');
        const discourses = this.urlParams.getAll('discourse');
        
        if (countries.length > 0) d.country_code = countries;
        if (regions.length > 0) d.region_code = regions;
        if (includeRegional) d.include_regional = includeRegional;
        if (speakers.length > 0) d.speaker_type = speakers;
        if (sexes.length > 0) d.sex = sexes;
        if (modes.length > 0) d.speech_mode = modes;
        if (discourses.length > 0) d.discourse = discourses;
        
        // Add sensitive parameter (case/accent sensitivity)
        const sensitiveCheckbox = document.getElementById('sensitive-search');
        if (sensitiveCheckbox) {
            d.sensitive = sensitiveCheckbox.checked ? 1 : 0;
        }
        
        console.log('[DataTables AJAX] Final params:', d);
        return d;
    }

    /**
     * Build Export Buttons configuration
     */
    buildExportButtons() {
        const exportColumns = [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11];  // Skip Audio column (index 4)
        const baseFilename = () => `corapan_${this.query}_${new Date().toISOString().slice(0,10)}`;

        return [
            {
                extend: 'copyHtml5',
                text: '<i class="fa-solid fa-copy"></i> Copiar',
                exportOptions: { columns: exportColumns }
            },
            {
                extend: 'csvHtml5',
                text: '<i class="bi bi-filetype-csv"></i> CSV',
                filename: baseFilename,
                exportOptions: { columns: exportColumns }
            },
            {
                extend: 'excelHtml5',
                text: '<i class="bi bi-filetype-xlsx"></i> Excel',
                filename: baseFilename,
                exportOptions: { columns: exportColumns }
            },
            {
                extend: 'pdfHtml5',
                text: '<i class="bi bi-filetype-pdf"></i> PDF',
                orientation: 'landscape',
                pageSize: 'A4',
                filename: baseFilename,
                exportOptions: { columns: exportColumns },
                customize: (doc) => {
                    doc.defaultStyle.fontSize = 8;
                    doc.styles.tableHeader.fontSize = 9;
                }
            }
        ];
    }

    /**
     * Build Column Definitions
     * Switched to OBJECT MODE for robustness against DB column reordering
     */
    buildColumns() {
        return [
            // Row number (computed)
            { 
                data: 'row_number', 
                width: '40px', 
                className: 'center-align',
                render: (data) => data || ''
            },
            
            // Left context
            {
                data: 'context_left',
                width: '200px',
                className: 'right-align',
                render: (data) => `<span class="md3-corpus-context">${data || ''}</span>`
            },
            
            // Result (keyword with styling - can be multi-word)
            {
                data: 'text',
                width: '150px',
                className: 'center-align',
                render: (data, type, row) => {
                    return `<span class="md3-corpus-keyword" 
                                  data-filename="${row.filename}" 
                                  data-start="${row.start}" 
                                  data-end="${row.end}">${data || ''}</span>`;
                }
            },
            
            // Right context
            {
                data: 'context_right',
                width: '200px',
                render: (data) => `<span class="md3-corpus-context">${data || ''}</span>`
            },
            
            // Audio Player (Pal + Ctx buttons)
            {
                data: 'audio_available',
                orderable: false,
                searchable: false,
                className: 'center-align',
                width: '120px',
                render: (data, type, row) => this.renderAudioButtons(row)
            },
            
            // Metadata columns (using object keys)
            { data: 'country_code', width: '80px' },   // País
            { data: 'speaker_type', width: '80px' },   // Hablante
            { data: 'sex', width: '80px' },            // Sexo
            { data: 'mode', width: '80px' },           // Modo
            { data: 'discourse', width: '80px' },      // Discurso
            { 
                data: 'token_id', 
                width: '100px',
                render: (data) => `<span class="token-id">${data || ''}</span>`
            },
            
            // Archivo (File icon with player link)
            {
                data: 'filename',
                width: '80px',
                className: 'center-align',
                orderable: true,
                render: (data, type, row) => this.renderFileLink(data, type, row)
            }
        ];
    }

    /**
     * Render Audio Buttons (Pal + Ctx)
     * Uses object keys instead of array indices
     */
    renderAudioButtons(row) {
        const audioAvailable = row.audio_available;
        const filename = row.filename; // DB enthält jetzt MP3-Filenames direkt
        const tokenId = row.token_id;
        const wordStartMs = row.start || row.start_ms || 0;
        const wordEndMs = row.end || row.end_ms || 0;
        const ctxStartMs = row.context_start || row.context_start_ms || wordStartMs;
        const ctxEndMs = row.context_end || row.context_end_ms || wordEndMs;
        // Convert to seconds with millisecond precision for backend
        const startSec = (wordStartMs / 1000).toFixed(3);
        const endSec = ((wordEndMs + 100) / 1000).toFixed(3); // extend 100ms padding
        const contextStartSec = (ctxStartMs / 1000).toFixed(3);
        const contextEndSec = (ctxEndMs / 1000).toFixed(3);
        
        if (!audioAvailable) {
            return '<span class="text-muted">-</span>';
        }
        
        return `
            <div class="md3-corpus-audio-buttons">
              <div class="md3-corpus-audio-row">
                <span class="md3-corpus-audio-label">Res.:</span>
                <a class="audio-button" data-filename="${filename}" data-start="${startSec}" data-end="${endSec}" data-token-id="${tokenId}" data-type="pal">
                  <i class="fa-solid fa-play"></i>
                </a>
                <a class="download-button" data-filename="${filename}" data-start="${startSec}" data-end="${endSec}" data-token-id="${tokenId}" data-type="pal">
                  <i class="fa-solid fa-download"></i>
                </a>
              </div>
              <div class="md3-corpus-audio-row">
                <span class="md3-corpus-audio-label">Ctx:</span>
                <a class="audio-button" data-filename="${filename}" data-start="${contextStartSec}" data-end="${contextEndSec}" data-token-id="${tokenId}" data-type="ctx">
                  <i class="fa-solid fa-play"></i>
                </a>
                <a class="download-button" data-filename="${filename}" data-start="${contextStartSec}" data-end="${contextEndSec}" data-token-id="${tokenId}" data-type="ctx">
                  <i class="fa-solid fa-download"></i>
                </a>
              </div>
            </div>
        `;
    }

    /**
     * Render File Link (Player icon)
     * Uses object keys instead of array indices
     */
    renderFileLink(data, type, row) {
        const filename = row.filename;
        const tokenId = row.token_id;
        
        // For sorting, return just the filename
        if (type === 'sort' || type === 'type') {
            return filename;
        }
        
        // Build player URL
        const base = filename.trim().replace(/\.mp3$/i, '');
        const transcriptionPath = `${MEDIA_ENDPOINT}/transcripts/${base}.json`;
        const audioPath = `${MEDIA_ENDPOINT}/full/${base}.mp3`;
        
        // Build URL with token_id only if it has a value
        let playerUrl = `/player?transcription=${encodeURIComponent(transcriptionPath)}&audio=${encodeURIComponent(audioPath)}`;
        if (tokenId && tokenId.trim()) {
            playerUrl += `&token_id=${encodeURIComponent(tokenId)}`;
        }
        
        return `
            <a href="${playerUrl}" 
               class="player-link" 
               title="${filename}">
              <i class="fa-regular fa-file"></i>
            </a>
        `;
    }

    /**
     * Refresh table data
     */
    refresh() {
        if (this.table) {
            this.table.ajax.reload(null, false); // Keep current page
            this.adjustColumns();
        }
    }

    /**
     * Destroy table instance
     */
    destroy() {
        if (this.table) {
            this.table.destroy();
            this.table = null;
            corpusTable = null;
        }
    }

    /**
     * Get DataTables API instance
     */
    getTable() {
        return this.table;
    }
}

/**
 * Global function to adjust DataTable columns
 * Called by external events (accordion open, results updated, etc.)
 */
export function adjustCorpusTable() {
    if (corpusTable) {
        requestAnimationFrame(() => {
            try {
                corpusTable.columns.adjust();
                if (corpusTable.responsive) {
                    corpusTable.responsive.recalc();
                }
                console.log('[DataTable] Columns adjusted (external call)');
            } catch (e) {
                console.warn('[DataTable] Error adjusting columns:', e);
            }
        });
    }
}
