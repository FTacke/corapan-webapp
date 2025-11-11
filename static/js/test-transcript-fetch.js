/**
 * Quick test to verify transcript fetching works
 * Run this in the browser console after the player page loads
 */

async function testTranscriptFetch() {
  const url = '/media/transcripts/2023-08-16_ARG_Mitre.json';
  
  console.log('[TEST] Fetching:', url);
  
  try {
    const response = await fetch(url, {
      credentials: 'same-origin',
      cache: 'no-store'
    });
    
    console.log('[TEST] Response status:', response.status, response.statusText);
    console.log('[TEST] Response headers:', {
      'content-type': response.headers.get('content-type'),
      'cache-control': response.headers.get('cache-control')
    });
    
    if (!response.ok) {
      console.error('[TEST] Response not OK!');
      return;
    }
    
    const data = await response.json();
    console.log('[TEST] JSON parsed successfully');
    console.log('[TEST] Data keys:', Object.keys(data));
    console.log('[TEST] First segment:', data.segments?.[0]);
    
    // Check if token_id exists in first word
    const firstWord = data.segments?.[0]?.words?.[0];
    if (firstWord) {
      console.log('[TEST] First word token_id:', firstWord.token_id);
    }
    
  } catch (error) {
    console.error('[TEST] Fetch failed:', error);
  }
}

// Export for use in console
window.testTranscriptFetch = testTranscriptFetch;
console.log('[TEST] Run testTranscriptFetch() to test transcript fetching');
