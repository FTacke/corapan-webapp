/**
 * Player Token Marker
 * Handles highlighting and scrolling to token_id in transcriptions
 * This is a minimal script that works with the new player.html structure
 */

console.log('[Player Token Marker] Script loaded');

// When DOM is ready, enhance the player with token_id functionality
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Player Token Marker] DOM ready, checking for token_id');
    
    const urlParams = new URLSearchParams(window.location.search);
    const targetTokenId = urlParams.get('token_id');
    
    if (!targetTokenId) {
        console.log('[Player Token Marker] No token_id in URL');
        return;
    }
    
    console.log('[Player Token Marker] Looking for token_id:', targetTokenId);
    
    // Wait a bit for transcription to render
    setTimeout(() => {
        // Find all words with the target token_id
        const words = document.querySelectorAll('[data-token-id]');
        console.log('[Player Token Marker] Found', words.length, 'words with token_id data');
        
        let found = false;
        words.forEach(word => {
            if (word.dataset.tokenId === targetTokenId) {
                console.log('[Player Token Marker] MATCH! Found target token_id in word:', word.textContent);
                
                // Add highlight class
                word.classList.add('word-token-id');
                found = true;
                
                // Scroll into view after a short delay
                setTimeout(() => {
                    word.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    console.log('[Player Token Marker] Scrolled to token');
                }, 100);
            }
        });
        
        if (!found) {
            console.warn('[Player Token Marker] Token_id not found in transcription:', targetTokenId);
        }
    }, 500);
});
