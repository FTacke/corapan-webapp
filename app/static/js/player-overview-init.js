(() => {
  const root = document.querySelector('[data-element="player-overview-root"]');
  const initialCountry = root?.dataset?.initialCountry || null;
  window.PLAYER_OVERVIEW_INITIAL_COUNTRY = initialCountry || null;
})();
