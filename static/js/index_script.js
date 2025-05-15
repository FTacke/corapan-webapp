document.addEventListener('DOMContentLoaded', function () {
  console.log('index_script loaded');

// FOOTER
// FOOTER
// FOOTER

  const totalWordCountElement = document.getElementById('totalWordCount');
  const totalDurationElement = document.getElementById('totalDuration');
  
  // Statistiken aus stats_all.db laden
  fetch('/get_stats_all_from_db')
    .then(response => response.json())
    .then(data => {
      updateTotalStats(data.total_word_count, data.total_duration_all);
    })
    .catch(error => {
      console.error('Error fetching statistics from the database:', error);
    });

  function updateTotalStats(totalWordCount, totalDuration) {
    totalDurationElement.innerHTML = `<span style="color: #053c96; font-weight: bold;">${totalDuration}</span> horas de audio`;
    totalWordCountElement.innerHTML = `<span style="color: #053c96; font-weight: bold;">${totalWordCount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.')}</span> palabras transcritas`;
  }
});

function toggleTooltip(e) {
  const tip = e.target.nextElementSibling;
  if (!tip) return;

  // nur den zugehörigen Tooltip ein-/ausblenden
  tip.classList.toggle('visible');

  // alle anderen sichtbaren Tooltips einklappen
  document.querySelectorAll('.tooltip-text.visible')
          .forEach(el => { if (el !== tip) el.classList.remove('visible'); });
}