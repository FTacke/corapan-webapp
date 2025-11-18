/**
 * Corpus Audio Manager
 * Verwaltet Audio-Playback und Player-Navigation
 */

import { MEDIA_ENDPOINT } from './config.js';

export class CorpusAudioManager {
    constructor() {
        this.currentAudio = null;
        this.currentPlayButton = null; // Store the DOM element, not jQuery object
        console.log('[Corpus Audio] Constructor initialized');
    }

    /**
     * Bind event handlers for audio buttons and player links
     */
    bindEvents() {
        this.bindAudioButtons();
        this.bindPlayerLinks();
        // No post-login action listeners - action replay removed for simplification
    }

    /**
     * Bind audio play button events
     */
    bindAudioButtons() {
        console.log('[Corpus Audio] Binding audio buttons');
        // Use event delegation for dynamically created buttons
        $(document).off('click', '.audio-button').on('click', '.audio-button', async (e) => {
            e.preventDefault();
            const $btn = $(e.currentTarget);
            
            // Check if this button is currently playing (showing stop icon)
            // Compare jQuery objects by their DOM element
            const isPlaying = this.currentPlayButton && this.currentPlayButton[0] === $btn[0];
            // Extract audio metadata unconditionally so playback works in all branches
            const filename = $btn.data('filename');
            const start = parseFloat($btn.data('start'));
            const end = parseFloat($btn.data('end'));
            const tokenId = $btn.data('token-id');
            const snippetType = $btn.data('type');
            // Debug: log playback attempt
            console.debug('[Corpus Audio] Play button clicked - attempting playback');
            
            if (isPlaying) {
                // Stop the audio and do not re-start playback
                this.stopCurrentAudio();
                return; // Prevent starting playback again
            } else {
                // Nothing special to do here - metadata already extracted
            }

            // Start playback for this snippet
            this.playAudioSegment(filename, start, end, $btn, tokenId, snippetType);
        });
        // Download buttons
        $(document).off('click', '.download-button').on('click', '.download-button', async (e) => {
            e.preventDefault();
            const $btn = $(e.currentTarget);
            const filename = $btn.data('filename');
            const start = parseFloat($btn.data('start'));
            const end = parseFloat($btn.data('end'));
            const tokenId = $btn.data('token-id');
            const snippetType = $btn.data('type');

            // Downloads for snippets are public - proceed with direct download

            const timestamp = Date.now();
            let downloadUrl = `${MEDIA_ENDPOINT}/play_audio/${filename}?start=${start}&end=${end}&t=${timestamp}&download=true`;
            if (tokenId) downloadUrl += `&token_id=${encodeURIComponent(tokenId)}`;
            if (snippetType) downloadUrl += `&type=${encodeURIComponent(snippetType)}`;

            const a = document.createElement('a');
            a.href = downloadUrl;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            document.body.appendChild(a);
            a.click();
            a.remove();
        });
    }

    /**
     * Bind player link events (with auth check)
     */
    bindPlayerLinks() {
        // Use event delegation for player links
        $(document).off('click', '.player-link').on('click', '.player-link', async (e) => {
            e.preventDefault();
            const $link = $(e.currentTarget);
            const playerUrl = $link.attr('href');
            
            // Extract transcription URL from player URL to test access
            const url = new URL(playerUrl, window.location.origin);
            const transcriptionPath = url.searchParams.get('transcription');
            
            if (!transcriptionPath) {
                console.error('[Corpus Audio] No transcription path found');
                return;
            }
            
            // If user is not authenticated, show a friendly message and do not open the login sheet
            if (window.IS_AUTHENTICATED !== 'true' && window.IS_AUTHENTICATED !== true) {
                // Unauthenticated users should see a simple message instead of the login sheet
                alert('Para ver la transcripción completa y abrir el reproductor, por favor inicia sesión.');
                return;
            }

            // Test if user has access to transcription (auth check)
            try {
                const response = await fetch(transcriptionPath, {
                    method: 'HEAD',
                    credentials: 'same-origin'
                });
                
                    if (response.status === 401) {
                        // Access denied - open login with intended target
                        const playerUrlFull = playerUrl;
                        this.openLoginForTarget(playerUrlFull);
                        return;
                    }
                
                if (!response.ok) {
                    console.error('[Corpus Audio] Failed to access transcription:', response.status);
                    return;
                }
                
                // User has access - navigate to player
                window.location.href = playerUrl;
            } catch (error) {
                console.error('[Corpus Audio] Error checking auth:', error);
            }
        });
        
        console.log('[Corpus Audio] Player links bound with auth check');
    }

    /**
     * Show authentication required message (same as play button)
     */
    showAuthRequiredMessage() {
        // Default behavior: show simple message for unauthenticated users
        const msg = 'Para ver funciones avanzadas (p. ej. abrir el reproductor completo) debes iniciar sesión.';
        if (window.toast) {
            // If there is a global toast helper
            window.toast(msg);
        } else {
            alert(msg);
        }
    }

    async openLoginForTarget(targetUrl, postAction = null) {
        // Save redirect server-side to ensure server can redirect after login
        try {
            await fetch('/auth/save-redirect', {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: targetUrl })
            });
        } catch (e) {
            console.warn('[Auth] Could not save redirect to server', e);
        }
        // Open login sheet with next param so the login form gets it and server-side fallback is present
        const loginUrl = `/auth/login_sheet?next=${encodeURIComponent(targetUrl)}`;
        if (window.htmx) {
            htmx.ajax('GET', loginUrl, { target: '#modal-root', swap: 'beforeend' });
        } else {
            window.location.href = `/auth/login?next=${encodeURIComponent(targetUrl)}`;
        }
        return;
    }
    
    /**
     * Play audio snippet from filename/start/end
     */
    async playAudioSegment(filename, start, end, $button, tokenId, snippetType) {
        // Snippet playback is public - proceed directly

        // Stop any currently playing audio
        this.stopCurrentAudio();

        // Build audio URL (backend handles segment extraction)
        const timestamp = Date.now();
        let audioUrl = `${MEDIA_ENDPOINT}/play_audio/${filename}?start=${start}&end=${end}&t=${timestamp}`;
        
        // Add token_id and type if available
        if (tokenId) {
            audioUrl += `&token_id=${encodeURIComponent(tokenId)}`;
        }
        if (snippetType) {
            audioUrl += `&type=${encodeURIComponent(snippetType)}`;
        }
        
        // Create new audio instance
        this.currentAudio = new Audio(audioUrl);
        // Set default volume and CORS mode if needed
        try {
            this.currentAudio.volume = 1.0; // ensure audible
            // console.log for debugging network issues
            console.log('[Corpus Audio] Audio URL:', audioUrl);
        } catch (e) {
            console.warn('[Corpus Audio] Could not set audio properties', e);
        }
        this.currentPlayButton = $button;
        
        // Update button to "stop" state
        $button.html('<i class="fa-solid fa-stop"></i>');
        
        // Log when audio actually begins playing
        this.currentAudio.addEventListener('playing', () => {
            console.log('[Corpus Audio] Playing started');
        });

        // Play audio
        this.currentAudio.play().then(() => {
            console.log('[Corpus Audio] play() resolved');
        }).catch((error) => {
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
