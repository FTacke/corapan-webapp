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

    try {
      const response = await fetch(transcriptionFile);
      this.transcriptionData = await response.json();
      // Prefer server-provided display name (field `country_display`). Do not
      // attempt client-side lookup — rely on server augmentation.
      this._updateMetadata();
      this._renderSegments();
      
      console.log('[Transcription] Loaded successfully');
    } catch (error) {
      console.error('[Transcription] Failed to load:', error);
      alert('Fehler beim Laden der Transkription.');
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

    this._setElementHTML('countryInfo', `País: <span class="meta-value meta-value--primary">${countryLabel}</span>`);
    this._setElementHTML('radioInfo', `Emisora: <span class="meta-value">${data.radio || 'Unbekannter Radiosender'}</span>`);
    this._setElementHTML('cityInfo', `Ciudad: <span class="meta-value">${data.city || 'Unbekannte Stadt'}</span>`);
    this._setElementHTML('revisionInfo', `Revisión: <span class="meta-value">${data.revision || 'Unbekannte Revision'}</span>`);
    this._setElementHTML('dateInfo', `Fecha: <span class="meta-value">${data.date || 'Unbekanntes Datum'}</span>`);
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
      const speakerId = segment.speaker;
      const words = segment.words;

      if (!speakerId || !words || words.length === 0) {
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
    const speakerId = segment.speaker;
    const words = segment.words;

    // Main container
    const segmentContainer = document.createElement('div');
    segmentContainer.classList.add('speaker-turn');
    segmentContainer.setAttribute('data-segment-index', segmentIndex);

    // Speaker name block (left column)
    const speakerBlock = this._createSpeakerBlock(speakerId, words, segmentIndex);

    // Content container (right column)
    const contentContainer = document.createElement('div');
    contentContainer.classList.add('speaker-content');

    // Speaker time
    const speakerTimeElement = this._createTimeElement(words);
    contentContainer.appendChild(speakerTimeElement);

    // Transcript text with words
    const transcriptBlock = this._createTranscriptBlock(words, segmentIndex);
    contentContainer.appendChild(transcriptBlock);

    segmentContainer.appendChild(speakerBlock);
    segmentContainer.appendChild(contentContainer);

    return segmentContainer;
  }

  /**
   * Create speaker name block with tooltip
   * @private
   */
  _createSpeakerBlock(speakerId, words, segmentIndex = null) {
    const speakerBlock = document.createElement('div');
    speakerBlock.classList.add('speaker-name');
    speakerBlock.style.position = 'relative';
    speakerBlock.style.display = 'flex';
    speakerBlock.style.flexDirection = 'column';
    speakerBlock.style.alignItems = 'flex-start';
    speakerBlock.style.gap = '0.5rem';
    speakerBlock.style.alignSelf = 'flex-start'; // Align to top
    
    // Store segment index for editor mode
    if (segmentIndex !== null) {
      speakerBlock.setAttribute('data-segment-index', segmentIndex);
    }

    const speakerInfo = this.transcriptionData.speakers.find(s => s.spkid === speakerId);
    const speakerName = speakerInfo ? speakerInfo.name : "otro";
    
    // Speaker name text (clickable in player mode to play segment)
    const nameSpan = document.createElement('span');
    nameSpan.textContent = speakerName;
    nameSpan.style.cursor = this.disableClickPlay ? 'default' : 'pointer';
    
    if (!this.disableClickPlay) {
      nameSpan.addEventListener('click', () => {
        this._playSegment(words[0].start, words[words.length - 1].end, true);
        console.log(`Speaker: ${speakerName} Start: ${words[0].start} End: ${words[words.length - 1].end}`);
      });
    }
    
    speakerBlock.appendChild(nameSpan);

    // Speaker type mapping for tooltips - map speaker NAME (e.g., "pre-pf", "lib-pm") to details
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
                 <span class="tooltip-high">Sexo: </span>femenino<br>`
    };

    // User icon or edit icon - different for player vs editor mode
    const userIcon = document.createElement('i');
    
    if (this.disableClickPlay) {
      // Editor mode: pen icon, no tooltip
      userIcon.classList.add('fa-solid', 'fa-user-pen');
      userIcon.title = 'Speaker ändern';
    } else {
      // Player mode: user icon with speaker type tooltip
      userIcon.classList.add('fa-solid', 'fa-user');
      userIcon.title = 'Speaker abspielen';
      
      // Create tooltip for player mode (with speaker type details from mapping)
      // Use speaker's NAME (e.g., "pre-pf", "lec-pf") to look up tooltip content
      const tooltipContent = speakerTypeMapping[speakerName] || `<span class="tooltip-high">Speaker: </span>${speakerName}<br>`;
      const tooltip = document.createElement('span');
      tooltip.classList.add('tooltip-text');
      tooltip.innerHTML = tooltipContent;
      
      // Show/hide tooltip on icon hover (player mode only)
      userIcon.addEventListener('mouseover', () => {
        tooltip.classList.add('visible');
      });
      userIcon.addEventListener('mouseout', () => {
        tooltip.classList.remove('visible');
      });
      
      speakerBlock.appendChild(tooltip);
    }
    
    userIcon.style.color = '#053c96';
    userIcon.style.cursor = 'pointer';

    speakerBlock.appendChild(userIcon);

    return speakerBlock;
  }

  /**
   * Create time element
   * @private
   */
  _createTimeElement(words) {
    const timeElement = document.createElement('div');
    timeElement.classList.add('speaker-time');
    
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
      wordElement.classList.add('word-token-id');
      
      setTimeout(() => {
        wordElement.scrollIntoView({ behavior: "smooth", block: "center" });
        const startTime = parseFloat(word.start) - 0.25;
        if (!isNaN(startTime)) {
          this.audioPlayer.audioElement.currentTime = Math.max(0, startTime);
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
      // Skip click handling if disabled (e.g., in editor mode)
      if (this.disableClickPlay) {
        return;
      }

      const startPrev = idx >= 2 ? parseFloat(words[idx - 2].start) : parseFloat(words[0].start);
      const endNext = idx < words.length - 1 ? parseFloat(words[idx + 2].end) : parseFloat(word.end);

      if (event.ctrlKey) {
        // Ctrl+Click: Play without pause
        const startCtrl = idx > 0 ? parseFloat(words[idx - 1].start) : parseFloat(word.start);
        this._playSegment(startCtrl, endNext, false);
        console.log(`Ctrl+Click: ${word.text} Start: ${startCtrl} End: ${endNext}`);
      } else {
        // Normal click: Play with pause
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
      tooltip.className = 'tooltip-text';
      tooltip.innerHTML = event.target.dataset.tooltip;
      document.body.appendChild(tooltip);

      setTimeout(() => {
        const rect = event.target.getBoundingClientRect();
        tooltip.style.position = 'absolute';
        tooltip.style.top = `${rect.bottom + window.scrollY + 6}px`;
        tooltip.style.left = `${rect.left + window.scrollX + rect.width / 2 - tooltip.offsetWidth / 2}px`;
        tooltip.classList.add('visible');
      }, 0);

      event.target._tooltipElement = tooltip;
    });

    wordElement.addEventListener('mouseleave', (event) => {
      const tooltip = event.target._tooltipElement;
      if (tooltip) {
        tooltip.remove();
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
