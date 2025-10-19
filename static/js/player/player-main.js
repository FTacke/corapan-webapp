/**
 * Player Main Controller
 * Orchestrates all player modules and initializes the application
 * @module player/player-main
 */

import AudioPlayer from './modules/audio.js';
import TokenCollector from './modules/tokens.js';
import TranscriptionManager from './modules/transcription.js';
import HighlightingManager from './modules/highlighting.js';
import ExportManager from './modules/export.js';
import UIManager from './modules/ui.js';
import MobileHandler from './modules/mobile.js';

class PlayerController {
  constructor() {
    // Initialize modules
    this.audio = new AudioPlayer();
    this.tokens = new TokenCollector();
    this.mobile = new MobileHandler();
    this.highlighting = new HighlightingManager();
    this.ui = new UIManager();
    
    // Modules that depend on others
    this.transcription = null;
    this.export = null;
    
    // URL parameters
    this.audioFile = null;
    this.transcriptionFile = null;
    this.targetTokenId = null;
  }

  /**
   * Initialize the player application
   */
  async init() {
    console.log('[Player] Initializing...');

    try {
      // Parse URL parameters
      this._parseURLParameters();

      // Initialize mobile handler first (affects layout)
      this.mobile.init();

      // Initialize UI components
      this.ui.init();
      this.tokens.init();
      this.highlighting.init();

      // Initialize audio player
      if (this.audioFile) {
        console.log('[Player] Audio file (raw):', this.audioFile);
        this.audio.init(this.audioFile);
      } else {
        console.warn('[Player] No audio file specified in URL');
      }

      // Initialize transcription (depends on audio & tokens)
      this.transcription = new TranscriptionManager(this.audio, this.tokens);
      
      // Connect audio playback events to word highlighting
      this.audio.onPlay = () => this.transcription.startWordHighlighting();
      this.audio.onPause = () => this.transcription.stopWordHighlighting();
      this.audio.onEnded = () => this.transcription.stopWordHighlighting();
      
      if (this.transcriptionFile) {
        console.log('[Player] Transcription file:', this.transcriptionFile);
        await this.transcription.load(this.transcriptionFile, this.targetTokenId);
      } else {
        console.warn('[Player] No transcription file specified in URL');
      }

      // Initialize export (depends on transcription)
      this.export = new ExportManager(this.transcription);
      this.export.init();

      // Load footer stats (if applicable)
      this.ui.loadFooterStats();

      console.log('[Player] Initialization complete');
    } catch (error) {
      console.error('[Player] Initialization failed:', error);
      alert('Fehler beim Laden des Players. Bitte Seite neu laden.');
    }
  }

  /**
   * Parse URL parameters
   * @private
   */
  _parseURLParameters() {
    const params = new URLSearchParams(window.location.search);
    
    this.audioFile = params.get('audio');
    this.transcriptionFile = params.get('transcription');
    this.targetTokenId = params.get('token_id');

    console.log('[Player] URL Parameters:', {
      audio: this.audioFile,
      transcription: this.transcriptionFile,
      token_id: this.targetTokenId
    });
  }

  /**
   * Get audio player instance
   * @returns {AudioPlayer}
   */
  getAudio() {
    return this.audio;
  }

  /**
   * Get token collector instance
   * @returns {TokenCollector}
   */
  getTokens() {
    return this.tokens;
  }

  /**
   * Get transcription manager instance
   * @returns {TranscriptionManager}
   */
  getTranscription() {
    return this.transcription;
  }

  /**
   * Get highlighting manager instance
   * @returns {HighlightingManager}
   */
  getHighlighting() {
    return this.highlighting;
  }

  /**
   * Get export manager instance
   * @returns {ExportManager}
   */
  getExport() {
    return this.export;
  }

  /**
   * Get UI manager instance
   * @returns {UIManager}
   */
  getUI() {
    return this.ui;
  }

  /**
   * Get mobile handler instance
   * @returns {MobileHandler}
   */
  getMobile() {
    return this.mobile;
  }
}

// Auto-initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('[Player] DOM Content Loaded');
  
  // Create global player instance
  window.corapanPlayer = new PlayerController();
  window.corapanPlayer.init();
});

// Export for potential manual initialization
export default PlayerController;
