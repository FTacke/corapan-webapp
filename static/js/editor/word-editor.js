/**
 * WordEditor - Handles inline word editing with change tracking
 * 
 * Features:
 * - Click-to-edit words
 * - Enter to save, ESC to cancel
 * - Tracks changes in editHistory Map
 * - Visual feedback (yellow=editing, green=modified)
 * - Prevents editing timestamps/token_id
 */

export class WordEditor {
  constructor(transcriptData, config) {
    this.data = transcriptData;
    this.config = config;
    this.editHistory = new Map(); // token_id -> {original, modified, segmentIndex, wordIndex}
    this.undoStack = []; // Array of action objects for undo
    this.redoStack = []; // Array of action objects for redo
    this.maxUndoActions = 10; // Limit to last 10 actions
    this.currentlyEditingElement = null;
    this.originalValue = null;
    this.transcription = null;
    
    // Store original speaker IDs for change detection
    this.originalSpeakers = {};
    this.data.segments?.forEach((seg, idx) => {
      this.originalSpeakers[idx] = seg.speaker;
    });
    
    this.initializeUI();
  }

  /**
   * Attach to transcription manager
   */
  attachToTranscription(transcription) {
    this.transcription = transcription;
    console.log('[WordEditor] Attached to transcription manager');
  }

  /**
   * Initialize UI elements
   */
  initializeUI() {
    this.saveBtn = document.getElementById('save-btn');
    this.discardBtn = document.getElementById('discard-btn');
    this.cancelEditBtn = document.getElementById('cancel-edit-btn');
    this.undoBtn = document.getElementById('undo-btn');
    this.redoBtn = document.getElementById('redo-btn');
    this.modifiedCountEl = document.getElementById('modified-count');
    this.saveIndicator = document.getElementById('save-indicator');
    this.wordEditInfo = document.getElementById('word-edit-info');
    this.currentWordDisplay = document.getElementById('current-word');

    // Button handlers
    this.saveBtn?.addEventListener('click', () => this.saveAllChanges());
    this.discardBtn?.addEventListener('click', () => this.discardAllChanges());
    this.cancelEditBtn?.addEventListener('click', () => this.cancelCurrentEdit());
    this.undoBtn?.addEventListener('click', () => this.undo());
    this.redoBtn?.addEventListener('click', () => this.redo());

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // Enter to finish editing
      if (e.key === 'Enter' && this.currentlyEditingElement) {
        e.preventDefault();
        this.finishEditing();
      }
      // ESC to cancel editing
      if (e.key === 'Escape' && this.currentlyEditingElement) {
        e.preventDefault();
        this.cancelCurrentEdit();
      }
      // CTRL+Z for undo (when not editing)
      if (e.ctrlKey && e.key === 'z' && !this.currentlyEditingElement) {
        e.preventDefault();
        this.undo();
      }
      // CTRL+Y or CTRL+Shift+Z for redo (when not editing)
      if ((e.ctrlKey && e.key === 'y') || (e.ctrlKey && e.shiftKey && e.key === 'Z')) {
        if (!this.currentlyEditingElement) {
          e.preventDefault();
          this.redo();
        }
      }
    });

    this.updateUndoRedoButtons();
  }

  /**
   * Attach event listeners to word elements
   */
  attachEventListeners() {
    const transcriptContainer = document.getElementById('transcript-content');
    
    // Delegate click events to word spans
    transcriptContainer.addEventListener('click', (e) => {
      const wordSpan = e.target.closest('.word');
      if (wordSpan && !wordSpan.classList.contains('editing')) {
        this.startEditing(wordSpan);
      }
    });

    // Global keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (this.currentlyEditingElement) {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.finishEditing();
        } else if (e.key === 'Escape') {
          e.preventDefault();
          this.cancelCurrentEdit();
        }
      }
    });
  }

  /**
   * Start editing a word
   */
  startEditing(wordSpan) {
    // Cancel any ongoing edit
    if (this.currentlyEditingElement) {
      this.cancelCurrentEdit();
    }

    this.currentlyEditingElement = wordSpan;
    this.originalValue = wordSpan.textContent;

    // Visual state
    wordSpan.classList.add('editing');
    wordSpan.contentEditable = 'true';
    wordSpan.focus();

    // Select all text
    const range = document.createRange();
    range.selectNodeContents(wordSpan);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);

    // Update UI
    this.wordEditInfo.classList.remove('hidden');
    this.currentWordDisplay.textContent = this.originalValue;

    console.log(`[Editor] Started editing: "${this.originalValue}"`);
  }

  /**
   * Finish editing and save change
   */
  finishEditing() {
    if (!this.currentlyEditingElement) return;

    const wordSpan = this.currentlyEditingElement;
    const newValue = wordSpan.textContent.trim();
    const tokenId = wordSpan.dataset.tokenId;
    
    // Extract segment and word indices from groupIndex (format: "segmentIndex-groupIndex")
    const groupIndex = wordSpan.dataset.groupIndex;
    if (!groupIndex) {
      console.error('[Editor] No groupIndex found in word element');
      this.cancelCurrentEdit();
      return;
    }
    
    const [segmentIndexStr, _] = groupIndex.split('-');
    const segmentIndex = parseInt(segmentIndexStr);
    
    // Find word index within segment by matching token_id
    let wordIndex = -1;
    const segment = this.data.segments[segmentIndex];
    if (segment && segment.words) {
      wordIndex = segment.words.findIndex(w => w.token_id === tokenId);
    }

    console.log(`[Editor] finishEditing - segmentIndex: ${segmentIndex}, wordIndex: ${wordIndex}, tokenId: ${tokenId}`);

    // Validate
    if (segmentIndex < 0 || wordIndex < 0) {
      console.error('[Editor] Could not determine segment/word indices');
      this.cancelCurrentEdit();
      return;
    }

    // Validate: not empty
    if (!newValue) {
      alert('Word darf nicht leer sein!');
      wordSpan.textContent = this.originalValue;
      this.cancelCurrentEdit();
      return;
    }

    // Check if actually changed
    if (newValue !== this.originalValue) {
      // Get the original value from history (if exists) or use current original
      const existingChange = this.editHistory.get(tokenId);
      const veryOriginalValue = existingChange ? existingChange.original : this.originalValue;

      // Record action for undo (6 parameters: tokenId, segIdx, wordIdx, oldVal, newVal, origVal)
      this._recordAction(
        tokenId,
        segmentIndex,
        wordIndex,
        this.originalValue, // old value (before this edit)
        newValue,            // new value (after this edit)
        veryOriginalValue    // original value (before any edits)
      );

      // Track change in history
      this.editHistory.set(tokenId, {
        original: veryOriginalValue,
        modified: newValue,
        segmentIndex,
        wordIndex,
        tokenId
      });

      // Update underlying data (JSON uses "text" not "word")
      const wordObj = this.data.segments[segmentIndex].words[wordIndex];
      if ('text' in wordObj) {
        wordObj.text = newValue;
      } else {
        wordObj.word = newValue;
      }

      // Visual feedback
      wordSpan.classList.add('modified');
      
      console.log(`[Editor] Changed "${this.originalValue}" -> "${newValue}"`);
      
      this.updateUI();
    }

    // Cleanup
    wordSpan.classList.remove('editing');
    wordSpan.contentEditable = 'false';
    this.currentlyEditingElement = null;
    this.originalValue = null;
    this.wordEditInfo.classList.add('hidden');
  }

  /**
   * Cancel current edit
   */
  cancelCurrentEdit() {
    if (!this.currentlyEditingElement) return;

    const wordSpan = this.currentlyEditingElement;
    
    // Restore original value
    wordSpan.textContent = this.originalValue;
    wordSpan.classList.remove('editing');
    wordSpan.contentEditable = 'false';

    this.currentlyEditingElement = null;
    this.originalValue = null;
    this.wordEditInfo.classList.add('hidden');

    console.log('[Editor] Edit cancelled');
  }

  /**
   * Discard all changes
   */
  discardAllChanges() {
    const totalChanges = this.getTotalChanges();
    if (totalChanges === 0) return;

    if (!confirm(`${totalChanges} Änderungen verwerfen?`)) {
      return;
    }

    // Restore original word values
    this.editHistory.forEach((change, tokenId) => {
      // Find word element by token_id
      const wordSpan = document.querySelector(`[data-token-id="${tokenId}"]`);
      if (wordSpan) {
        wordSpan.textContent = change.original;
        wordSpan.classList.remove('modified');
      }

      // Restore in data (JSON uses "text" not "word")
      const wordObj = this.data.segments[change.segmentIndex].words[change.wordIndex];
      if ('text' in wordObj) {
        wordObj.text = change.original;
      } else {
        wordObj.word = change.original;
      }
    });

    // Restore original speaker values
    this.undoStack.forEach(action => {
      if (action.type === 'speaker_change') {
        const { segmentIndex, oldValue } = action;
        this.data.segments[segmentIndex].speaker = oldValue;
        
        // Restore original speakers map
        this.originalSpeakers[segmentIndex] = oldValue;
        
        // Update UI
        this._updateSpeakerDisplay(segmentIndex, oldValue);
      }
    });

    // Clear all change tracking
    this.editHistory.clear();
    this.undoStack = [];
    this.redoStack = [];
    
    // Remove all modified classes
    document.querySelectorAll('.word.modified').forEach(el => {
      el.classList.remove('modified');
    });
    document.querySelectorAll('.speaker-name.modified-speaker').forEach(el => {
      el.classList.remove('modified-speaker');
    });
    
    this.updateUI();

    console.log('[Editor] All changes discarded');
  }

  /**
   * Save all changes to backend
   */
  async saveAllChanges() {
    const totalChanges = this.getTotalChanges();
    if (totalChanges === 0) return;

    this.saveBtn.disabled = true;
    this.saveIndicator.innerHTML = '<i class="bi bi-hourglass-split"></i> Speichert...';
    this.saveIndicator.className = 'status-badge status-saving';

    try {
      // Prepare changes payload (word changes only for changes array)
      const changes = Array.from(this.editHistory.values()).map(change => ({
        token_id: change.tokenId,
        segment_index: change.segmentIndex,
        word_index: change.wordIndex,
        old_value: change.original,
        new_value: change.modified
      }));

      // Add speaker changes from undoStack
      const speakerChanges = this.undoStack.filter(action => action.type === 'speaker_change');
      speakerChanges.forEach(action => {
        // Get speaker names from data
        const oldSpeakerObj = this.data.speakers?.find(s => s.spkid === action.oldValue);
        const newSpeakerObj = this.data.speakers?.find(s => s.spkid === action.newValue);
        const oldSpeakerName = oldSpeakerObj?.name || action.oldValue;
        const newSpeakerName = newSpeakerObj?.name || action.newValue;
        
        changes.push({
          type: 'speaker_change',
          segment_index: action.segmentIndex,
          old_value: oldSpeakerName,
          new_value: newSpeakerName
        });
      });

      const response = await fetch(this.config.apiEndpoints.saveEdits, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          file: this.config.transcriptFile,
          changes: changes,
          transcript_data: this.data // Full updated transcript (includes speaker changes)
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Save failed');
      }

      const result = await response.json();
      
      // Clear edit history and remove visual markers
      this.editHistory.forEach((change, tokenId) => {
        const wordSpan = document.querySelector(`[data-token-id="${tokenId}"]`);
        if (wordSpan) {
          wordSpan.classList.remove('modified');
        }
      });
      
      this.editHistory.clear();
      
      // Clear undo/redo stacks (changes have been saved)
      this.undoStack = [];
      this.redoStack = [];
      
      // Reset original speakers to current state
      this.data.segments?.forEach((seg, idx) => {
        this.originalSpeakers[idx] = seg.speaker;
      });
      
      // Remove modified-speaker classes
      document.querySelectorAll('.speaker-name').forEach(el => {
        el.classList.remove('modified-speaker');
      });
      
      this.saveIndicator.innerHTML = '<i class="bi bi-check-circle"></i> Gespeichert';
      this.saveIndicator.className = 'status-badge status-saved';
      
      console.log('[Editor] Changes saved:', result);
      
      this.updateUI();
      
    } catch (error) {
      console.error('[Editor] Save failed:', error);
      
      this.saveIndicator.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Fehler';
      this.saveIndicator.className = 'status-badge status-error';
      
      alert(`Speichern fehlgeschlagen: ${error.message}`);
    } finally {
      this.saveBtn.disabled = false;
    }
  }

  /**
   * Update UI elements based on current state
   */
  /**
   * Count total number of changes (word + speaker)
   */
  getTotalChanges() {
    // Count word changes from editHistory
    let totalChanges = this.editHistory.size;

    // Count speaker changes from undoStack
    const speakerChanges = this.undoStack.filter(a => a.type === 'speaker_change').length;
    totalChanges += speakerChanges;

    return totalChanges;
  }

  updateUI() {
    const totalChanges = this.getTotalChanges();
    const hasChanges = totalChanges > 0;
    
    this.saveBtn.disabled = !hasChanges;
    this.discardBtn.disabled = !hasChanges;
    this.modifiedCountEl.textContent = totalChanges;
    
    if (hasChanges) {
      this.saveIndicator.innerHTML = '<i class="bi bi-exclamation-circle"></i> Ungespeichert';
      this.saveIndicator.className = 'status-badge status-unsaved';
    } else {
      this.saveIndicator.innerHTML = '<i class="bi bi-check-circle"></i> Gespeichert';
      this.saveIndicator.className = 'status-badge status-saved';
    }

    this.updateUndoRedoButtons();
  }

  /**
   * Update undo/redo button states
   */
  updateUndoRedoButtons() {
    if (this.undoBtn) {
      this.undoBtn.disabled = this.undoStack.length === 0;
    }
    if (this.redoBtn) {
      this.redoBtn.disabled = this.redoStack.length === 0;
    }
  }

  /**
   * Undo last action
   */
  undo() {
    if (this.undoStack.length === 0) {
      console.log('[Editor] Nothing to undo');
      return;
    }

    const action = this.undoStack.pop();
    console.log('[Editor] Undoing action:', action);

    // Apply undo
    this._applyAction(action, true);

    // Move to redo stack
    this.redoStack.push(action);

    // Limit redo stack size
    if (this.redoStack.length > this.maxUndoActions) {
      this.redoStack.shift();
    }

    this.updateUI();
  }

  /**
   * Redo last undone action
   */
  redo() {
    if (this.redoStack.length === 0) {
      console.log('[Editor] Nothing to redo');
      return;
    }

    const action = this.redoStack.pop();
    console.log('[Editor] Redoing action:', action);

    // Apply redo (inverse of undo)
    this._applyAction(action, false);

    // Move back to undo stack
    this.undoStack.push(action);

    this.updateUI();
  }

  /**
   * Apply an action (for undo/redo)
   * @param {Object} action - The action to apply
   * @param {boolean} isUndo - True if undoing, false if redoing
   * @private
   */
  _applyAction(action, isUndo) {
    // Handle speaker changes
    if (action.type === 'speaker_change') {
      const { segmentIndex, oldValue, newValue } = action;
      const valueToApply = isUndo ? oldValue : newValue;

      // Update data
      this.data.segments[segmentIndex].speaker = valueToApply;

      // Update UI
      this._updateSpeakerDisplay(segmentIndex, valueToApply);

      console.log(`[Editor] Applied speaker change via undo/redo for segment ${segmentIndex}`);
      return;
    }

    // Handle word changes
    const { tokenId, segmentIndex, wordIndex, oldValue, newValue } = action;
    const valueToApply = isUndo ? oldValue : newValue;

    // Find word element
    const wordSpan = document.querySelector(`[data-token-id="${tokenId}"]`);
    if (!wordSpan) {
      console.warn('[Editor] Word element not found for undo/redo:', tokenId);
      return;
    }

    // Update DOM
    wordSpan.textContent = valueToApply;

    // Update data
    const wordObj = this.data.segments[segmentIndex].words[wordIndex];
    if ('text' in wordObj) {
      wordObj.text = valueToApply;
    } else {
      wordObj.word = valueToApply;
    }

    // Update edit history
    if (isUndo) {
      // If undoing and value matches original, remove from history
      if (valueToApply === action.originalValue) {
        this.editHistory.delete(tokenId);
        wordSpan.classList.remove('modified');
      } else {
        // Update history entry
        const historyEntry = this.editHistory.get(tokenId);
        if (historyEntry) {
          historyEntry.modified = valueToApply;
        }
        wordSpan.classList.add('modified');
      }
    } else {
      // Redoing - add/update history
      if (valueToApply !== action.originalValue) {
        this.editHistory.set(tokenId, {
          original: action.originalValue,
          modified: valueToApply,
          segmentIndex,
          wordIndex,
          tokenId
        });
        wordSpan.classList.add('modified');
      } else {
        this.editHistory.delete(tokenId);
        wordSpan.classList.remove('modified');
      }
    }
  }

  /**
   * Record an action for undo
   * @param {string} tokenId
   * @param {number} segmentIndex
   * @param {number} wordIndex
   * @param {string} oldValue
   * @param {string} newValue
   * @param {string} originalValue - The very first value before any edits
   * @private
   */
  _recordAction(tokenId, segmentIndex, wordIndex, oldValue, newValue, originalValue) {
    const action = {
      tokenId,
      segmentIndex,
      wordIndex,
      oldValue,
      newValue,
      originalValue,
      timestamp: Date.now()
    };

    this.undoStack.push(action);

    // Limit undo stack size
    if (this.undoStack.length > this.maxUndoActions) {
      this.undoStack.shift();
    }

    // Clear redo stack when new action is performed
    this.redoStack = [];

    console.log('[Editor] Action recorded:', action);
  }

  /**
   * Get current edit statistics
   */
  getStats() {
    return {
      totalChanges: this.editHistory.size,
      isEditing: !!this.currentlyEditingElement,
      undoAvailable: this.undoStack.length,
      redoAvailable: this.redoStack.length
    };
  }

  /**
   * Initialize speaker selection UI
   * @param {Array} speakers - List of available speakers from transcript
   */
  initializeSpeakerSelection(speakers) {
    const speakerSelect = document.getElementById('speaker-select');
    if (!speakerSelect) return;

    // Populate speaker options
    speakers.forEach(speaker => {
      const option = document.createElement('option');
      option.value = speaker.spkid;
      option.textContent = speaker.name || speaker.spkid;
      speakerSelect.appendChild(option);
    });

    // Event listeners
    document.getElementById('confirm-speaker-btn')?.addEventListener('click', () => {
      this.confirmSpeakerChange();
    });

    document.getElementById('cancel-speaker-btn')?.addEventListener('click', () => {
      this.cancelSpeakerChange();
    });

    console.log('[Editor] Speaker selection initialized');
  }

  /**
   * Open speaker selection for a segment
   * @param {number} segmentIndex - The segment to change speaker for
   * @param {string} currentSpeaker - Current speaker ID
   */
  openSpeakerSelection(segmentIndex, currentSpeaker) {
    this.currentSpeakerSegment = segmentIndex;
    this.currentSpeakerValue = currentSpeaker;

    const speakerSelect = document.getElementById('speaker-select');
    const speakerSelection = document.getElementById('speaker-selection');

    if (speakerSelect && speakerSelection) {
      speakerSelect.value = currentSpeaker;
      speakerSelection.classList.remove('hidden');
      speakerSelect.focus();
    }

    console.log(`[Editor] Speaker selection opened for segment ${segmentIndex}`);
  }

  /**
   * Confirm speaker change
   */
  confirmSpeakerChange() {
    const speakerSelect = document.getElementById('speaker-select');
    const newSpeaker = speakerSelect?.value;

    if (!newSpeaker || this.currentSpeakerSegment === undefined) {
      return;
    }

    const segment = this.data.segments[this.currentSpeakerSegment];
    if (!segment) return;

    const oldSpeaker = segment.speaker;
    if (newSpeaker === oldSpeaker) {
      this.cancelSpeakerChange();
      return;
    }

    // Record the change
    this._recordSpeakerChange(this.currentSpeakerSegment, oldSpeaker, newSpeaker);

    // Update data
    segment.speaker = newSpeaker;

    // Update UI
    this._updateSpeakerDisplay(this.currentSpeakerSegment, newSpeaker);

    // Close selection
    this.cancelSpeakerChange();
    this.updateUI();

    console.log(`[Editor] Speaker changed from ${oldSpeaker} to ${newSpeaker} for segment ${this.currentSpeakerSegment}`);
  }

  /**
   * Cancel speaker selection
   */
  cancelSpeakerChange() {
    const speakerSelection = document.getElementById('speaker-selection');
    speakerSelection?.classList.add('hidden');

    this.currentSpeakerSegment = undefined;
    this.currentSpeakerValue = null;
  }

  /**
   * Record a speaker change action
   * @private
   */
  _recordSpeakerChange(segmentIndex, oldSpeaker, newSpeaker) {
    const action = {
      type: 'speaker_change',
      segmentIndex,
      oldValue: oldSpeaker,
      newValue: newSpeaker,
      timestamp: Date.now()
    };

    this.undoStack.push(action);

    if (this.undoStack.length > this.maxUndoActions) {
      this.undoStack.shift();
    }

    this.redoStack = [];
    this.updateUndoRedoButtons();
  }

  /**
   * Update speaker display in UI - completely re-render the speaker block
   * @private
   */
  _updateSpeakerDisplay(segmentIndex, newSpeaker) {
    // Find speaker name from data
    const speakerObj = this.data.speakers?.find(s => s.spkid === newSpeaker);
    const speakerName = speakerObj?.name || newSpeaker;

    // Find the speaker-name block
    const speakerNameBlock = document.querySelector(`.speaker-name[data-segment-index="${segmentIndex}"]`);
    if (!speakerNameBlock) {
      console.warn(`[Editor] Could not find speaker-name block for segment ${segmentIndex}`);
      return;
    }

    // Clear the speaker-name block
    speakerNameBlock.innerHTML = '';

    // Re-create the speaker name span
    const nameSpan = document.createElement('span');
    nameSpan.textContent = speakerName;
    nameSpan.style.cursor = 'pointer';
    nameSpan.addEventListener('click', () => {
      // Play audio segment (only if click-to-play enabled in transcription)
      if (this.transcription && !this.transcription.disableClickPlay) {
        const segment = this.data.segments[segmentIndex];
        if (segment && segment.words && segment.words.length > 0) {
          const startTime = segment.words[0].start;
          const endTime = segment.words[segment.words.length - 1].end;
          this.transcription.audioPlayer?.seekAndPlay(startTime, endTime);
        }
      }
    });
    speakerNameBlock.appendChild(nameSpan);

    // Re-create the speaker icon - always fa-user-pen in editor mode
    const userIcon = document.createElement('i');
    userIcon.style.color = 'rgb(5, 60, 150)';
    userIcon.style.cursor = 'pointer';
    userIcon.style.marginTop = '0.25rem';
    userIcon.title = 'Speaker ändern';
    userIcon.classList.add('fa-solid', 'fa-user-pen'); // Always pen icon in editor

    userIcon.addEventListener('click', (e) => {
      e.stopPropagation();
      this.openSpeakerSelection(segmentIndex, this.data.segments[segmentIndex].speaker);
    });

    speakerNameBlock.appendChild(userIcon);

    // Add modified-speaker class if modified
    const currentSpeaker = this.data.segments[segmentIndex].speaker;
    const isModified = currentSpeaker !== this.originalSpeakers[segmentIndex];
    if (isModified) {
      speakerNameBlock.classList.add('modified-speaker');
    } else {
      speakerNameBlock.classList.remove('modified-speaker');
    }

    console.log(`[Editor] Speaker display updated for segment ${segmentIndex}: ${newSpeaker} (modified: ${isModified})`);
  }

  /**
   * Check if there are unsaved changes
   * @returns {boolean} true if there are any modifications
   */
  hasUnsavedChanges() {
    // Check if there are any word edits
    if (this.editHistory.size > 0) {
      return true;
    }

    // Check if any speakers have been modified
    for (let segIdx in this.originalSpeakers) {
      if (this.data.segments[segIdx].speaker !== this.originalSpeakers[segIdx]) {
        return true;
      }
    }

    return false;
  }
}

