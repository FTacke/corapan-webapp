/**
 * Admin Dashboard Module
 * Fetches data from new /api/analytics/stats endpoint
 * 
 * VARIANTE 3a: Keine Top-Queries Anzeige (keine Suchinhalte gespeichert)
 */

export function initAdminDashboard() {
  // Check if we are on the dashboard page by looking for the metrics grid
  const metricsGrid = document.querySelector('[data-element="metrics-grid"]');
  if (!metricsGrid) return;

  fetchAnalytics();
}

async function fetchAnalytics() {
  try {
    const response = await fetch('/api/analytics/stats?days=30');
    if (!response.ok) throw new Error('Failed to fetch analytics');
    const data = await response.json();
    renderDashboard(data);
  } catch (error) {
    console.error('Error fetching analytics:', error);
    showErrorState();
  }
}

function renderDashboard(data) {
  // Render totals (use totals_window for period)
  renderTotal('visitors-total', data.totals_window.visitors);
  renderTotal('searches-total', data.totals_window.searches);
  renderTotal('audio-total', data.totals_window.audio_plays);
  renderTotal('errors-total', data.totals_window.errors);
  
  // Render device breakdown
  const mobilePercent = data.totals_window.visitors > 0 
    ? Math.round((data.totals_window.mobile / data.totals_window.visitors) * 100) 
    : 0;
  const desktopPercent = 100 - mobilePercent;
  renderDeviceBreakdown(mobilePercent, desktopPercent);
  
  // Render daily chart
  renderDailyChart(data.daily);
  
  // VARIANTE 3a: Keine renderTopQueries() - keine Suchinhalte!
}

function renderTotal(elementId, value) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = (value || 0).toLocaleString('de-DE');
  }
}

function renderDeviceBreakdown(mobile, desktop) {
  const el = document.getElementById('device-breakdown');
  if (el) {
    el.textContent = `Mobile ${mobile}% · Desktop ${desktop}%`;
  }
}

function renderDailyChart(dailyData) {
  // dailyData is array of { date, visitors, searches, audio_plays, errors, ... }
  // API returns DESC order, we need chronological (ASC) for display
  const container = document.getElementById('daily-chart');
  if (!container) return;
  
  if (!dailyData || !dailyData.length) {
    container.innerHTML = `
      <div class="md3-no-data-card">
        <span class="material-symbols-rounded md3-no-data-card__icon">analytics</span>
        <p class="md3-body-medium md3-no-data-card__message">Noch keine Daten vorhanden.</p>
        <p class="md3-body-small md3-no-data-card__hint">Statistiken werden nach dem ersten Besuch angezeigt.</p>
      </div>
    `;
    return;
  }
  
  // Reverse to get chronological order (oldest first, newest last)
  // Then take last 7 days
  const ordered = dailyData.slice().reverse();
  const last7Days = ordered.slice(-7);
  
  const html = last7Days.map(day => `
    <div class="md3-chart-row">
      <span class="md3-chart-label">${formatDate(day.date)}</span>
      <span class="md3-chart-value">${day.visitors} Besuche · ${day.searches} Suchen</span>
    </div>
  `).join('');
  
  container.innerHTML = html;
}

/**
 * Format ISO date string to German locale
 */
function formatDate(isoDate) {
  try {
    const date = new Date(isoDate);
    return date.toLocaleDateString('de-DE', { weekday: 'short', day: 'numeric', month: 'short' });
  } catch {
    return isoDate;
  }
}

// VARIANTE 3a: renderTopQueries() Funktion ENTFERNT - keine Suchinhalte!

function showErrorState() {
  const container = document.querySelector('[data-element="metrics-grid"]');
  if (container) {
    container.innerHTML = `
      <div class="md3-error-card md3-card md3-card--outlined">
        <span class="material-symbols-rounded md3-error-card__icon">error</span>
        <p class="md3-body-large md3-error-card__message">Analytics konnten nicht geladen werden.</p>
      </div>
    `;
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initAdminDashboard);
