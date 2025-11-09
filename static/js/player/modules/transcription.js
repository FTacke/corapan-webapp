/**
 * Transcription Module
 * Handles transcription loading, rendering, and word interactions
 * @module player/modules/transcription
 */

import { formatMorphLeipzig } from '../../morph_formatter.js';

export class TranscriptionManager {
  constructor(audioPlayer, tokenCollector) {
    this.audioPlayer = audioPlayer;
    this.tokenCollector = tokenCollector;
    this.transcriptionData = null;
    this.targetTokenId = null;
    
    // Word highlighting state
    this.isPlaying = false;
    this.animationFrameId = null;
    this.lastActiveGroup = null;
    this.deactivateTimeout = null;
    this.DEACTIVATE_DELAY = 0.35; // Seconds delay for smoother transitions
    
    // Feature flag: disable click-to-play (for editor mode)
    this.disableClickPlay = false;
  }

  /**
   * Load and render transcription
   * @param {string} transcriptionFile - Path to JSON transcription file
   * @param {string} targetTokenId - Optional token ID to highlight and scroll to
   */
  async load(transcriptionFile, targetTokenId = null) {
    this.targetTokenId = targetTokenId;

    console.log('[Transcription] Loading with:', {
      transcriptionFile,
      targetTokenId,
      origin: location.origin
    });

    try {
      // Ensure relative URL for same-origin requests (avoids CORS issues)
      const url = new URL(transcriptionFile, location.origin);
      console.log('[Transcription] Resolved URL:', url.toString());
      
      const response = await fetch(url, {
        credentials: 'same-origin',
        cache: 'no-store'
      });
      
      console.log('[Transcription] Fetch response status:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      this.transcriptionData = await response.json();
      console.log('[Transcription] JSON parsed successfully, segments:', this.transcriptionData.segments?.length || 'unknown');
      
      // Prefer server-provided display name (field `country_display`). Do not
      // attempt client-side lookup — rely on server augmentation.
      this._updateMetadata();
      this._renderSegments();
      
      console.log('[Transcription] Loaded successfully with targetTokenId:', this.targetTokenId);
    } catch (error) {
      console.error('[Transcription] Failed to load:', error);
      alert('Fehler beim Laden der Transkription: ' + error.message);
    }
  }

  /**
   * Update metadata display
   * @private
   */
  _updateMetadata() {
    const data = this.transcriptionData;
    
    this._setElementContent('documentName', data.filename);
    // Only use server-provided human-readable label. If missing, show fallback.
    const countryLabel = data.country_display || 'Unbekanntes Land';

    // Update metadata items with MD3 structure
    this._setMetadataItem('countryInfo', 'País:', countryLabel, true);
    this._setMetadataItem('radioInfo', 'Emisora:', data.radio || 'Unbekannter Radiosender');
    this._setMetadataItem('cityInfo', 'Ciudad:', data.city || 'Unbekannte Stadt');
    this._setMetadataItem('revisionInfo', 'Revisión:', data.revision || 'Unbekannte Revision');
    this._setMetadataItem('dateInfo', 'Fecha:', data.date || 'Unbekanntes Datum');
  }

  /**
   * Set metadata item with label and value (MD3 structure)
   * @private
   */
  _setMetadataItem(id, label, value, isPrimary = false) {
    const element = document.getElementById(id);
    if (!element) return;
    
    const valueClass = isPrimary ? 'md3-player-metadata-value md3-player-metadata-value--primary' : 'md3-player-metadata-value';
    element.innerHTML = `
      <span class="md3-player-metadata-label">${label}</span>
      <span class="${valueClass}">${value}</span>
    `;
  }

  /**
   * Ensure locations lookup map is available on this instance.
   * Fetches /api/v1/atlas/locations and builds a code->name map.
   * @private
   */
  async _ensureLocationsLookup() {
    // Client-side lookup removed: rely on server augmentation `country_display`.
    // Kept for compatibility if re-enabled in future.
    return;
  }

  /**
   * Convert a raw country field from the transcription JSON to a display label.
   * Accepts full names, codes (ARG, ARG-CBA), or legacy codes.
   * @private
   */
  _formatCountryLabel(raw) {
    if (!raw) return 'Unbekanntes Land';

    const asUpper = raw.toString().toUpperCase();

    // If we have a direct mapping, prefer it
    if (this._locationsLookup && this._locationsLookup[asUpper]) {
      return this._locationsLookup[asUpper];
    }

    // Try splitting if input looks like a composite name (e.g., 'Argentina: Buenos Aires')
    if (raw.includes(':')) return raw;

    // If raw already looks like a human-readable name (contains letters and spaces), return as-is
    if (/^[A-Za-zÀ-ÖØ-öø-ÿ\s\/\-]+$/.test(raw) && raw.length > 2) return raw;

    // Fallback to raw value
    return raw;
  }

  /**
   * Helper to set element content safely
   * @private
   */
  _setElementContent(id, content) {
    const element = document.getElementById(id);
    if (element) element.textContent = content;
  }

  /**
   * Helper to set element HTML safely
   * @private
   */
  _setElementHTML(id, html) {
    const element = document.getElementById(id);
    if (element) element.innerHTML = html;
  }

  /**
   * Render all transcription segments
   * @private
   */
  _renderSegments() {
    const container = document.getElementById('transcriptionContainer');
    if (!container) return;

    container.innerHTML = '';

    this.transcriptionData.segments.forEach((segment, segmentIndex) => {
      const speakerCode = segment.speaker_code;
      const words = segment.words;

      if (!speakerCode || !words || words.length === 0) {
        console.warn(`Segment ${segmentIndex} wird übersprungen (fehlende Sprecher- oder Wortdaten).`);
        return;
      }

      const segmentElement = this._createSegmentElement(segment, segmentIndex);
      container.appendChild(segmentElement);
    });
  }

  /**
   * Create segment element
   * @private
   */
  _createSegmentElement(segment, segmentIndex) {
    const speakerCode = segment.speaker_code || segment.speaker || "otro";
    const words = segment.words;

    // Main container
    const segmentContainer = document.createElement('div');
    segmentContainer.classList.add('md3-speaker-turn');
    segmentContainer.setAttribute('data-segment-index', segmentIndex);

    // Speaker header (Zeile 1: Edit-Icon | Name | Time)
    const headerContainer = this._createSpeakerHeader(speakerCode, words, segmentIndex);
    
    // Transcript text (Zeile 2: Monospace Text mit Words)
    const transcriptBlock = this._createTranscriptBlock(words, segmentIndex);

    segmentContainer.appendChild(headerContainer);
    segmentContainer.appendChild(transcriptBlock);

    return segmentContainer;
  }

  /**
   * Create speaker header with edit icon, name, and time
   * @private
   */
  _createSpeakerHeader(speakerCode, words, segmentIndex) {
    const headerContainer = document.createElement('div');
    headerContainer.classList.add('md3-speaker-header');

    // 1. Edit Icon (links)
    const editIcon = document.createElement('i');
    // Check both flags for editor mode (new: disableNormalClick, legacy: disableClickPlay)
    const isEditorMode = this.disableNormalClick || this.disableClickPlay;
    
    if (isEditorMode) {
      // Editor mode: pen icon
      editIcon.classList.add('fa-solid', 'fa-user-pen', 'md3-speaker-edit-icon');
      editIcon.title = 'Speaker ändern';
      editIcon.setAttribute('data-segment-index', segmentIndex);
      headerContainer.appendChild(editIcon);
    } else {
      // Player mode: user icon with native tooltip
      editIcon.classList.add('fa-solid', 'fa-user', 'md3-speaker-edit-icon');
      
      // Use native title attribute for tooltip (MD3-compliant)
      const tooltipText = this._getTooltipContentPlainText(speakerCode);
      editIcon.title = tooltipText;
      
      headerContainer.appendChild(editIcon);
    }

    // 2. Speaker Name (Mitte)
    const speakerNameSpan = this._createSpeakerName(speakerCode, words, segmentIndex);
    headerContainer.appendChild(speakerNameSpan);

    // 3. Speaker Time (rechts)
    const timeElement = this._createTimeElement(words);
    headerContainer.appendChild(timeElement);

    return headerContainer;
  }

  /**
   * Create speaker name element
   * @private
   */
  _createSpeakerName(speakerCode, words, segmentIndex) {
    const nameSpan = document.createElement('span');
    nameSpan.classList.add('md3-speaker-name');
    nameSpan.textContent = speakerCode;
    nameSpan.setAttribute('data-segment-index', segmentIndex); // Für Speaker-Änderungen
    
    // Speaker name is always clickable to play segment audio (even in editor mode)
    nameSpan.style.cursor = 'pointer';
    nameSpan.addEventListener('click', () => {
      this._playSegment(words[0].start, words[words.length - 1].end, true);
      console.log(`Speaker: ${speakerCode} Start: ${words[0].start} End: ${words[words.length - 1].end}`);
    });
    
    return nameSpan;
  }

  /**
   * Get tooltip content for speaker type
   * @private
   */
  _getTooltipContent(speakerName) {
    const speakerTypeMapping = {
      "lib-pm": `<span class="tooltip-high">Modo: </span>habla libre<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>masculino<br>`,
      "lib-pf": `<span class="tooltip-high">Modo: </span>habla libre<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>femenino<br>`,
      "lib-om": `<span class="tooltip-high">Modo: </span>habla libre<br>
                 <span class="tooltip-high">Hablante: </span>no profesional<br>
                 <span class="tooltip-high">Sexo: </span>masculino<br>`,
      "lib-of": `<span class="tooltip-high">Modo: </span>habla libre<br>
                 <span class="tooltip-high">Hablante: </span>no profesional<br>
                 <span class="tooltip-high">Sexo: </span>femenino<br>`,
      "lec-pm": `<span class="tooltip-high">Modo: </span>lectura<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>masculino<br>`,
      "lec-pf": `<span class="tooltip-high">Modo: </span>lectura<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>femenino<br>`,
      "lec-om": `<span class="tooltip-high">Modo: </span>lectura<br>
                 <span class="tooltip-high">Hablante: </span>no profesional<br>
                 <span class="tooltip-high">Sexo: </span>masculino<br>`,
      "lec-of": `<span class="tooltip-high">Modo: </span>lectura<br>
                 <span class="tooltip-high">Hablante: </span>no profesional<br>
                 <span class="tooltip-high">Sexo: </span>femenino<br>`,
      "pre-pm": `<span class="tooltip-high">Modo: </span>lectura pregrabada<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>masculino<br>`,
      "pre-pf": `<span class="tooltip-high">Modo: </span>lectura pregrabada<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>femenino<br>`,
      "tie-pm": `<span class="tooltip-high">Discurso: </span>pronóstico del tiempo<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>masculino<br>`,
      "tie-pf": `<span class="tooltip-high">Discurso: </span>pronóstico del tiempo<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>femenino<br>`,
      "traf-pm": `<span class="tooltip-high">Discurso: </span>informaciones de tránsito<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>masculino<br>`,
      "traf-pf": `<span class="tooltip-high">Discurso: </span>informaciones de tránsito<br>
                 <span class="tooltip-high">Hablante: </span>profesional<br>
                 <span class="tooltip-high">Sexo: </span>femenino<br>`,
      "rev": `<span class="tooltip-high">Rol: </span>revisor/revisora<br>`
    };

    return speakerTypeMapping[speakerName] || `<span class="tooltip-high">Speaker: </span>${speakerName}<br>`;
  }

  /**
   * Get plain text tooltip content for speaker type (for native title attribute)
   * @private
   */
  _getTooltipContentPlainText(speakerName) {
    const speakerTypeMapping = {
      "lib-pm": "Modo: habla libre | Hablante: profesional | Sexo: masculino",
      "lib-pf": "Modo: habla libre | Hablante: profesional | Sexo: femenino",
      "lib-om": "Modo: habla libre | Hablante: no profesional | Sexo: masculino",
      "lib-of": "Modo: habla libre | Hablante: no profesional | Sexo: femenino",
      "lec-pm": "Modo: lectura | Hablante: profesional | Sexo: masculino",
      "lec-pf": "Modo: lectura | Hablante: profesional | Sexo: femenino",
      "lec-om": "Modo: lectura | Hablante: no profesional | Sexo: masculino",
      "lec-of": "Modo: lectura | Hablante: no profesional | Sexo: femenino",
      "pre-pm": "Modo: lectura pregrabada | Hablante: profesional | Sexo: masculino",
      "pre-pf": "Modo: lectura pregrabada | Hablante: profesional | Sexo: femenino",
      "tie-pm": "Discurso: pronóstico del tiempo | Hablante: profesional | Sexo: masculino",
      "tie-pf": "Discurso: pronóstico del tiempo | Hablante: profesional | Sexo: femenino",
      "traf-pm": "Discurso: informaciones de tránsito | Hablante: profesional | Sexo: masculino",
      "traf-pf": "Discurso: informaciones de tránsito | Hablante: profesional | Sexo: femenino",
      "rev": "Revisor / Revisora"
    };

    return speakerTypeMapping[speakerName] || `Speaker: ${speakerName}`;
  }

  /**
   * Create time element
   * @private
   */
  _createTimeElement(words) {
    const timeElement = document.createElement('div');
    timeElement.classList.add('md3-speaker-time');
    
    const startTime = this._formatTime(words[0].start);
    const endTime = this._formatTime(words[words.length - 1].end);
    timeElement.textContent = `${startTime} - ${endTime}`;

    return timeElement;
  }

  /**
   * Create transcript block with word elements
   * @private
   */
  _createTranscriptBlock(words, segmentIndex) {
    const transcriptBlock = document.createElement('div');
    transcriptBlock.classList.add('md3-speaker-text');
    transcriptBlock.classList.add('speaker-text');

    // Group words based on pauses
    const wordGroups = this._groupWords(words);

    words.forEach((word, idx) => {
      const wordElement = this._createWordElement(word, idx, words, segmentIndex, wordGroups);
      transcriptBlock.appendChild(wordElement);
    });

    return transcriptBlock;
  }

  /**
   * Group words based on pauses
   * @private
   */
  _groupWords(words) {
    const PAUSE_THRESHOLD = 0.25;
    const MAX_GROUP_SIZE = 3;
    const wordGroups = [];
    let currentGroup = [];

    words.forEach((word, idx) => {
      currentGroup.push({ word, idx });

      if (idx < words.length - 1) {
        const pauseToNext = words[idx + 1].start - word.end;
        const groupIsFull = currentGroup.length >= MAX_GROUP_SIZE;

        if (pauseToNext >= PAUSE_THRESHOLD || groupIsFull) {
          wordGroups.push([...currentGroup]);
          currentGroup = [];
        }
      } else {
        wordGroups.push([...currentGroup]);
      }
    });

    return wordGroups;
  }

  /**
   * Create word element with tooltip and click handlers
   * @private
   */
  _createWordElement(word, idx, words, segmentIndex, wordGroups) {
    const wordElement = document.createElement('span');
    wordElement.textContent = word.text + ' ';
    wordElement.classList.add('word');
    wordElement.dataset.start = word.start;
    wordElement.dataset.end = word.end;
    wordElement.dataset.tokenId = word.token_id;
    wordElement.style.cursor = 'pointer';

    // Assign group index
    const groupIndex = wordGroups.findIndex(group => 
      group.some(item => item.idx === idx)
    );
    wordElement.dataset.groupIndex = `${segmentIndex}-${groupIndex}`;

    // Highlight target token
    if (this.targetTokenId && word.token_id === this.targetTokenId) {
      console.log('[Transcription] MATCH! Found target token_id:', this.targetTokenId, 'in word:', word);
      wordElement.classList.add('word-token-id');
      
      setTimeout(() => {
        console.log('[Transcription] Scrolling to token and setting audio time');
        wordElement.scrollIntoView({ behavior: "smooth", block: "center" });
        const startTime = parseFloat(word.start) - 0.25;
        if (!isNaN(startTime)) {
          this.audioPlayer.audioElement.currentTime = Math.max(0, startTime);
          console.log('[Transcription] Audio time set to:', startTime);
        }
      }, 300);
    }

    // Tooltip data
    const morphInfo = formatMorphLeipzig(word.pos, word.morph);
    const tooltipText = `
      <span class="tooltip-high">lemma:</span> <span class="tooltip-bold">${word.lemma}</span><br>
      <span class="tooltip-high">pos:</span> ${word.pos}, ${morphInfo}<br>
      <span class="tooltip-high">dep:</span> ${(word.dep || '').toUpperCase()}<br>
      <span class="tooltip-high">head_text:</span> <span class="tooltip-italic">${word.head_text}</span><br>
      <span class="tooltip-high">token_id:</span> <span class="tooltip-token">${word.token_id}</span><br>
    `;
    wordElement.dataset.tooltip = tooltipText;

    // Tooltip events
    this._attachTooltipEvents(wordElement);

    // Click handler
    wordElement.addEventListener('click', (event) => {
      // In editor mode: allow Ctrl+Click and Shift+Click, but block normal clicks
      if (this.disableNormalClick && !event.ctrlKey && !event.shiftKey) {
        return; // Block normal click in editor mode
      }
      
      // Legacy: also check old disableClickPlay flag
      if (this.disableClickPlay) {
        return;
      }

      const startPrev = idx >= 2 ? parseFloat(words[idx - 2].start) : parseFloat(words[0].start);
      const endNext = idx < words.length - 1 ? parseFloat(words[idx + 2].end) : parseFloat(word.end);

      if (event.ctrlKey) {
        // Ctrl+Click: Play only this word
        this._playSegment(parseFloat(word.start), parseFloat(word.end), false);
        console.log(`Ctrl+Click: ${word.text} Start: ${word.start} End: ${word.end}`);
      } else if (event.shiftKey) {
        // Shift+Click: Play from this word to end of segment
        const segmentEnd = parseFloat(words[words.length - 1].end);
        this._playSegment(parseFloat(word.start), segmentEnd, false);
        console.log(`Shift+Click: ${word.text} Start: ${word.start} End: ${segmentEnd}`);
      } else {
        // Normal click: Play with context (word before and after)
        this._playSegment(startPrev, endNext, true);
        console.log(`Click: ${word.text} Start: ${startPrev} End: ${endNext}`);
      }

      // Add to token collector
      if (this.tokenCollector) {
        this.tokenCollector.addTokenId(word.token_id);
      }
    });

    return wordElement;
  }

  /**
   * Attach tooltip events to word element
   * @private
   */
  _attachTooltipEvents(wordElement) {
    wordElement.addEventListener('mouseenter', (event) => {
      const tooltip = document.createElement('div');
      tooltip.className = 'tooltip-text word-tooltip';
      tooltip.innerHTML = event.target.dataset.tooltip;
      document.body.appendChild(tooltip);

      // Position tooltip near word
      setTimeout(() => {
        const rect = event.target.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        // Position below word, centered horizontally
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        let top = rect.bottom + 8;
        
        // Keep tooltip in viewport (horizontal)
        if (left < 10) {
          left = 10;
        } else if (left + tooltipRect.width > window.innerWidth - 10) {
          left = window.innerWidth - tooltipRect.width - 10;
        }
        
        // Check if tooltip goes below viewport, if so position above
        if (top + tooltipRect.height > window.innerHeight - 10) {
          top = rect.top - tooltipRect.height - 8;
        }
        
        tooltip.style.position = 'fixed';
        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
        
        tooltip.classList.add('visible');
      }, 10);

      event.target._tooltipElement = tooltip;
    });

    wordElement.addEventListener('mouseleave', (event) => {
      const tooltip = event.target._tooltipElement;
      if (tooltip) {
        tooltip.classList.remove('visible');
        setTimeout(() => {
          tooltip.remove();
        }, 150);
        event.target._tooltipElement = null;
      }
    });
  }

  /**
   * Play audio segment
   * @private
   */
  _playSegment(startTime, endTime, shouldPause) {
    this.audioPlayer.playSegment(startTime, shouldPause ? endTime : null);
  }

  /**
   * Format time in seconds to hh:mm:ss
   * @private
   */
  _formatTime(timeInSeconds) {
    const hours = Math.floor(timeInSeconds / 3600);
    const minutes = Math.floor((timeInSeconds % 3600) / 60);
    const seconds = Math.round(timeInSeconds % 60);
    const pad = (num) => num < 10 ? '0' + num : num.toString();
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  }

  /**
   * Start continuous word highlighting using requestAnimationFrame
   * Called when audio starts playing
   */
  startWordHighlighting() {
    if (this.animationFrameId) return; // Already active
    
    this.isPlaying = true;
    console.log('[Transcription] Starting word highlighting');
    
    const animate = () => {
      if (!this.isPlaying) return;
      this.updateWordsHighlight();
      this.animationFrameId = requestAnimationFrame(animate);
    };
    
    this.animationFrameId = requestAnimationFrame(animate);
  }

  /**
   * Stop continuous word highlighting
   * Called when audio pauses or ends
   */
  stopWordHighlighting() {
    this.isPlaying = false;
    
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
      console.log('[Transcription] Stopped word highlighting');
    }
  }

  /**
   * Update word highlighting based on current audio time
   * Highlights current word group and provides preview for next group
   */
  updateWordsHighlight() {
    const currentTime = this.audioPlayer.getCurrentTime();
    const allWords = document.querySelectorAll('.word');
    let currentActiveGroup = null;
    let currentActiveWord = null;
    
    // Find currently active word
    allWords.forEach(word => {
      const start = parseFloat(word.dataset.start);
      const end = parseFloat(word.dataset.end);
      if (currentTime >= start && currentTime <= end) {
        currentActiveWord = word;
        currentActiveGroup = word.dataset.groupIndex;
      }
    });
    
    // Highlight all words in active group
    if (currentActiveGroup !== null) {
      // Clear any pending deactivation
      if (this.deactivateTimeout) {
        clearTimeout(this.deactivateTimeout);
        this.deactivateTimeout = null;
      }
      
      allWords.forEach(word => {
        if (word.dataset.groupIndex === currentActiveGroup) {
          word.classList.add('playing');
          
          // Scroll to currently spoken word (not entire group)
          if (word === currentActiveWord) {
            const rect = word.getBoundingClientRect();
            // Scroll if word is close to bottom of viewport
            if (window.innerHeight - rect.bottom < 300) {
              word.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          }
        } else {
          // Remove playing class from other groups
          word.classList.remove('playing', 'playing-preview');
        }
      });
      
      // Preview for next group (format: "segmentIndex-groupIndex")
      const [segIdx, grpIdx] = currentActiveGroup.split('-').map(Number);
      const nextGroupIndex = `${segIdx}-${grpIdx + 1}`;
      allWords.forEach(word => {
        if (word.dataset.groupIndex === nextGroupIndex) {
          word.classList.add('playing-preview');
        }
      });
      
      this.lastActiveGroup = currentActiveGroup;
    } else if (this.lastActiveGroup !== null) {
      // No active word - delayed deactivation for smoother transitions
      if (!this.deactivateTimeout) {
        this.deactivateTimeout = setTimeout(() => {
          allWords.forEach(word => {
            word.classList.remove('playing', 'playing-preview');
          });
          this.lastActiveGroup = null;
          this.deactivateTimeout = null;
        }, this.DEACTIVATE_DELAY * 1000);
      }
    }
  }
}

export default TranscriptionManager;
