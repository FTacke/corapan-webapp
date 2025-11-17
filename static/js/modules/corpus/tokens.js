/**
 * Legacy `tokens.js` removed.
 *
 * This legacy shim was intentionally removed in favor of the MD3-native
 * `token-tab.js`. If you import this module, use `token-tab.js` or the
 * global `window.TokenTab` API instead.
 */

export function legacyTokenManagerRemoved() {
    throw new Error('Legacy tokens.js removed. Use window.TokenTab or import token-tab.js');
}
