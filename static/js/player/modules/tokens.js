/**
 * Token Collection Module
 * Handles collection, display, and clipboard operations for token IDs
 * @module player/modules/tokens
 */

import PLAYER_CONFIG from '../config.js';

export class TokenCollector {
  constructor() {
    this.collectedTokenIds = [];
    this.inputElement = null;
    this.copyButton = null;
    this.resetButton = null;
  }

  /**
   * Initialize token collector
   */
  init() {
    this.inputElement = document.getElementById('tokenCollectorInput');
    this.copyButton = document.getElementById('copyTokenIdsBtn');
    this.resetButton = document.getElementById('resetTokenCollectorBtn');
    
    if (!this.inputElement) {
      console.warn('[Tokens] Token collector input not found');
      return;
    }

    this._setupEventListeners();
  }

  /**
   * Setup event listeners for token collector controls
   * @private
   */
  _setupEventListeners() {
    if (this.copyButton) {
      this.copyButton.addEventListener('click', () => this.copyToClipboard());
    }

    if (this.resetButton) {
      this.resetButton.addEventListener('click', () => this.reset());
    }
  }

  /**
   * Add a token ID to the collection
   * @param {string} tokenId - Token ID to add
   */
  addTokenId(tokenId) {
    if (!this.collectedTokenIds.includes(tokenId)) {
      this.collectedTokenIds.push(tokenId);
      this._updateDisplay();
      this._resetCopyIcon();
    }
  }

  /**
   * Remove a token ID from the collection
   * @param {string} tokenId - Token ID to remove
   */
  removeTokenId(tokenId) {
    const index = this.collectedTokenIds.indexOf(tokenId);
    if (index > -1) {
      this.collectedTokenIds.splice(index, 1);
      this._updateDisplay();
    }
  }

  /**
   * Reset the entire collection
   */
  reset() {
    this.collectedTokenIds = [];
    this._updateDisplay();
    this._resetCopyIcon();
  }

  /**
   * Copy token IDs to clipboard
   */
  async copyToClipboard() {
    if (this.collectedTokenIds.length === 0) {
      alert('Keine Token-IDs zum Kopieren vorhanden.');
      return;
    }

    const text = this.collectedTokenIds.join(', ');
    
    try {
      await navigator.clipboard.writeText(text);
      this._showCopySuccess();
    } catch (err) {
      console.error('[Tokens] Failed to copy:', err);
      
      // Fallback: Select text
      this.inputElement.select();
      document.execCommand('copy');
      this._showCopySuccess();
    }
  }

  /**
   * Update the display of collected token IDs
   * @private
   */
  _updateDisplay() {
    if (!this.inputElement) return;

    this.inputElement.value = this.collectedTokenIds.join(', ');
    
    // Auto-resize textarea
    this.inputElement.style.height = 'auto';
    this.inputElement.style.height = this.inputElement.scrollHeight + 'px';
  }

  /**
   * Show copy success feedback
   * @private
   */
  _showCopySuccess() {
    if (!this.copyButton) return;

    const icon = this.copyButton.querySelector('i');
    if (!icon) return;

    // Change to success icon
    icon.classList.remove('fa-copy');
    icon.classList.add('fa-check');
    this.copyButton.classList.add('copy-success');

    // Reset after delay
    setTimeout(() => {
      this._resetCopyIcon();
    }, PLAYER_CONFIG.COPY_FEEDBACK_DURATION);
  }

  /**
   * Reset copy button icon to default
   * @private
   */
  _resetCopyIcon() {
    if (!this.copyButton) return;

    const icon = this.copyButton.querySelector('i');
    if (!icon) return;

    icon.classList.remove('fa-check');
    icon.classList.add('fa-copy');
    this.copyButton.classList.remove('copy-success');
  }

  /**
   * Get all collected token IDs
   * @returns {string[]}
   */
  getTokenIds() {
    return [...this.collectedTokenIds];
  }

  /**
   * Get token count
   * @returns {number}
   */
  getCount() {
    return this.collectedTokenIds.length;
  }

  /**
   * Check if a token ID is collected
   * @param {string} tokenId
   * @returns {boolean}
   */
  hasTokenId(tokenId) {
    return this.collectedTokenIds.includes(tokenId);
  }
}

export default TokenCollector;
