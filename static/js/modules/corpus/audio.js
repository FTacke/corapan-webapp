/**
 * Corpus Audio Manager
 * Verwaltet Audio-Playback und Player-Navigation
 */

import { MEDIA_ENDPOINT, allowTempMedia } from './config.js';

export class CorpusAudioManager {
    constructor() {
        this.currentAudio = null;
        this.currentPlayButton = null;
    }

    /**
     * Bind event handlers for audio buttons and player links
     */
    bindEvents() {
        this.bindAudioButtons();
        this.bindPlayerLinks();
    }

    /**
     * Bind audio play button events
     */
    bindAudioButtons() {
        // Use event delegation for dynamically created buttons
        $(document).off('click', '.audio-button').on('click', '.audio-button', (e) => {
            e.preventDefault();
            const $btn = $(e.currentTarget);
            const filename = $btn.data('filename');
            const start = parseFloat($btn.data('start'));
            const end = parseFloat($btn.data('end'));
            
            this.playAudioSegment(filename, start, end, $btn);
        });
    }

    /**
     * Bind player link events (with auth check)
     */
    bindPlayerLinks() {
        // Use event delegation
        $(document).off('click', 'a.player-link, a[href^="/player/"]').on('click', 'a.player-link, a[href^="/player/"]', (e) => {
            e.preventDefault();
            
            const playerUrl = $(e.currentTarget).attr('href');
            
            // Check if user is authenticated
            const headerRoot = document.querySelector('.site-header');
            const isAuthenticated = headerRoot?.dataset.auth === 'true';
            
            if (!isAuthenticated) {
                // Save intended destination
                sessionStorage.setItem('_player_redirect_after_login', playerUrl);
                
                // Open login sheet
                const openLoginBtn = document.querySelector('[data-action="open-login"]');
                if (openLoginBtn) {
                    openLoginBtn.click();
                }
                return false;
            }
            
            // User is authenticated - cleanup and navigate
            this.stopCurrentAudio();
            window.location.href = playerUrl;
            return false;
        });
    }

    /**
     * Play audio segment (word or context)
     */
    playAudioSegment(filename, start, end, $button) {
        // Check if audio playback is allowed
        if (!allowTempMedia()) {
            alert('Audio-Wiedergabe erfordert Authentifizierung');
            return;
        }
        
        // Stop any currently playing audio
        this.stopCurrentAudio();
        
        // Build audio URL (backend handles segment extraction)
        const timestamp = Date.now();
        const audioUrl = `${MEDIA_ENDPOINT}/play_audio/${filename}?start=${start}&end=${end}&t=${timestamp}`;
        
        // Create new audio instance
        this.currentAudio = new Audio(audioUrl);
        this.currentPlayButton = $button;
        
        // Update button to "stop" state
        $button.html('<i class="fa-solid fa-stop"></i>');
        
        // Play audio
        this.currentAudio.play().catch((error) => {
            console.error('Audio playback error:', error);
            alert('Audio konnte nicht abgespielt werden');
            $button.html('<i class="fa-solid fa-play"></i>');
        });
        
        // Event: Audio ended
        this.currentAudio.addEventListener('ended', () => {
            $button.html('<i class="fa-solid fa-play"></i>');
            this.currentAudio = null;
            this.currentPlayButton = null;
        });
        
        // Event: Audio error
        this.currentAudio.addEventListener('error', (e) => {
            console.error('Audio error:', e);
            alert('Audio konnte nicht geladen werden');
            $button.html('<i class="fa-solid fa-play"></i>');
            this.currentAudio = null;
            this.currentPlayButton = null;
        });
    }

    /**
     * Stop currently playing audio
     */
    stopCurrentAudio() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
        }
        
        if (this.currentPlayButton) {
            this.currentPlayButton.html('<i class="fa-solid fa-play"></i>');
            this.currentPlayButton = null;
        }
    }

    /**
     * Cleanup on page unload
     */
    destroy() {
        this.stopCurrentAudio();
        $(document).off('click', '.audio-button');
        $(document).off('click', 'a.player-link, a[href^="/player/"]');
    }
}
