/**
 * Admin Dashboard Module
 * Handles metrics fetching and rendering for the redesigned dashboard.
 */

export function initAdminDashboard() {
  // Check if we are on the dashboard page by looking for the metrics grid
  const metricsGrid = document.querySelector('[data-element="metrics-grid"]');
  if (!metricsGrid) return;

  fetchMetrics();
}

async function fetchMetrics() {
  try {
    const response = await fetch('/admin/metrics');
    if (!response.ok) throw new Error('Failed to fetch metrics');
    const data = await response.json();
    renderMetrics(data);
  } catch (error) {
    console.error('Error fetching metrics:', error);
    // Optional: Show error state in UI
  }
}

function renderMetrics(data) {
  // data structure: { visits: DetailedCounter, access: AccessCounter, search: DetailedCounter }
  renderMetricCard('visits', data.visits);
  renderMetricCard('access', data.access);
  renderMetricCard('search', data.search);
}

function renderMetricCard(type, metricData) {
  if (!metricData) return;

  // 1. Render Total
  const totalEl = document.getElementById(`${type}-total`);
  if (totalEl) {
    // DetailedCounter: metricData.overall
    // AccessCounter: metricData.total.overall
    let total = 0;
    if (typeof metricData.overall === 'number') {
        total = metricData.overall;
    } else if (metricData.total && typeof metricData.total.overall === 'number') {
        total = metricData.total.overall;
    }
    totalEl.textContent = total.toLocaleString('es-ES');
  }

  // 2. Render Days (Current Month)
  const daysList = document.getElementById(`${type}-days-list`);
  if (daysList) {
    daysList.innerHTML = '';
    
    let daysMap = {};
    
    // Normalize data to a map: { "YYYY-MM-DD": count }
    if (metricData.days && !Array.isArray(metricData.days)) {
        // DetailedCounter format: { "2023-10-27": 5 }
        daysMap = metricData.days;
    } else if (metricData.total && Array.isArray(metricData.total.days)) {
        // AccessCounter format: ["2023-10-27", "2023-10-27", ...]
        metricData.total.days.forEach(day => {
            daysMap[day] = (daysMap[day] || 0) + 1;
        });
    }

    // Filter for current month
    const now = new Date();
    const currentMonthPrefix = now.toISOString().slice(0, 7); // "YYYY-MM"

    const sortedDays = Object.keys(daysMap)
        .filter(day => day.startsWith(currentMonthPrefix))
        .sort()
        .reverse();

    if (sortedDays.length === 0) {
        daysList.innerHTML = '<li class="md3-list-item"><span class="md3-list-item__text">Sin datos este mes</span></li>';
    } else {
        sortedDays.forEach(day => {
            const count = daysMap[day];
            const li = document.createElement('li');
            li.className = 'md3-list-item';
            li.innerHTML = `
                <span class="md3-list-item__text">${day}</span>
                <span class="md3-list-item__meta">${count}</span>
            `;
            daysList.appendChild(li);
        });
    }
  }

  // 3. Render Months (History)
  const monthsList = document.getElementById(`${type}-months-list`);
  if (monthsList) {
    monthsList.innerHTML = '';
    
    let monthsMap = {};
    
    if (metricData.monthly) {
        // DetailedCounter format
        monthsMap = metricData.monthly;
    } else if (metricData.total && metricData.total.monthly) {
        // AccessCounter format
        monthsMap = metricData.total.monthly;
    }

    const sortedMonths = Object.keys(monthsMap).sort().reverse();

    if (sortedMonths.length === 0) {
        monthsList.innerHTML = '<li class="md3-list-item"><span class="md3-list-item__text">Sin historial</span></li>';
    } else {
        sortedMonths.forEach(month => {
            const count = monthsMap[month];
            const li = document.createElement('li');
            li.className = 'md3-list-item';
            li.innerHTML = `
                <span class="md3-list-item__text">${month}</span>
                <span class="md3-list-item__meta">${count}</span>
            `;
            monthsList.appendChild(li);
        });
    }
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initAdminDashboard);
