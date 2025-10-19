export function isTempAudioPublic() {
  const config = window.__CORAPAN__ || {};
  const publicFlag = config.allowPublicTempAudio === true || config.allowPublicTempAudio === 'true';
  if (publicFlag) {
    return true;
  }
  const banner = document.querySelector('.status-banner');
  if (!banner) return false;
  const isAuthenticated = banner.dataset.auth === 'true';
  return isAuthenticated;
}