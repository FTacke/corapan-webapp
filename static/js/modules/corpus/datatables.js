/**
 * Corpus DataTables Manager
 * Verwaltet DataTables mit Server-Side Processing
 */

import { MEDIA_ENDPOINT, allowTempMedia } from './config.js';

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
                    console.error('DataTables AJAX error:', error, thrown);
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
            
            // Layout with Export Buttons
            dom: '<"top"pB<"ml-auto"lf>>rt<"bottom"ip>',
            
            // Export Buttons (skip Audio column)
            buttons: this.buildExportButtons(),
            
            // Column Definitions
            columns: this.buildColumns(),
            
            // Default Sorting
            order: [[0, 'asc']],
            
            // Layout
            scrollX: false,
            scrollCollapse: false,
            autoWidth: true,
            
            // Callbacks
            initComplete: () => {
                console.log('✅ DataTable (Server-Side) initialized');
                this.table.columns.adjust();
            },
            
            drawCallback: () => {
                this.table.columns.adjust();
            }
        });

        // Resize handler
        $(window).on('resize', () => {
            if (this.table) {
                this.table.columns.adjust();
            }
        });
    }

    /**
     * Build AJAX data parameters from URL
     */
    buildAjaxData(d) {
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
     */
    buildColumns() {
        return [
            // 0: # (Row number)
            { data: 0, width: '40px', className: 'center-align' },
            
            // 1: Ctx.← (Left context)
            {
                data: 1,
                width: '200px',
                className: 'right-align',
                render: (data) => `<span class="md3-corpus-context">${data || ''}</span>`
            },
            
            // 2: Palabra (Keyword with styling and data attributes)
            {
                data: 2,
                width: '100px',
                className: 'center-align',
                render: (data, type, row) => {
                    const filename = row[11];
                    const start = row[12];
                    const end = row[13];
                    return `<span class="md3-corpus-keyword" 
                                  data-filename="${filename}" 
                                  data-start="${start}" 
                                  data-end="${end}">${data || ''}</span>`;
                }
            },
            
            // 3: Ctx.→ (Right context)
            {
                data: 3,
                width: '200px',
                render: (data) => `<span class="md3-corpus-context">${data || ''}</span>`
            },
            
            // 4: Audio Player (Pal + Ctx buttons)
            {
                data: 4,
                orderable: false,
                searchable: false,
                className: 'center-align',
                width: '120px',
                render: (data, type, row) => this.renderAudioButtons(row)
            },
            
            // 5-10: Metadata columns
            { data: 5, width: '80px' },   // País
            { data: 6, width: '80px' },   // Hablante
            { data: 7, width: '80px' },   // Sexo
            { data: 8, width: '80px' },   // Modo
            { data: 9, width: '80px' },   // Discurso
            { data: 10, width: '100px' }, // Token-ID
            
            // 11: Archivo (File icon with player link)
            {
                data: 11,
                width: '80px',
                className: 'center-align',
                orderable: true,
                render: (data, type, row) => this.renderFileLink(data, type, row)
            }
        ];
    }

    /**
     * Render Audio Buttons (Pal + Ctx)
     */
    renderAudioButtons(row) {
        const audioAvailable = row[4];
        const filename = row[11];
        const tokenId = row[10];
        const wordStart = row[12];
        const wordEnd = row[13];
        const ctxStart = row[14];
        const ctxEnd = row[15];
        
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

    /**
     * Render File Link (Player icon)
     */
    renderFileLink(data, type, row) {
        const filename = row[11];
        const tokenId = row[10];
        
        // For sorting, return just the filename
        if (type === 'sort' || type === 'type') {
            return filename;
        }
        
        // Build player URL
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

    /**
     * Refresh table data
     */
    refresh() {
        if (this.table) {
            this.table.ajax.reload();
        }
    }

    /**
     * Destroy table instance
     */
    destroy() {
        if (this.table) {
            this.table.destroy();
            this.table = null;
        }
    }

    /**
     * Get DataTables API instance
     */
    getTable() {
        return this.table;
    }
}
