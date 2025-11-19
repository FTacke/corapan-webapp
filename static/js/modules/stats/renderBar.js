/**
 * ECharts Bar Chart Renderer for CO.RA.PAN Statistics
 * 
 * Renders horizontal bar charts with MD3 styling.
 * Supports automatic rotation for long category lists and responsive resize.
 * 
 * NOTE: Requires ECharts to be loaded globally (via CDN or script tag).
 */

import corapanTheme from './theme/corapanTheme.js';

// ECharts is loaded globally from CDN
const echarts = window.echarts;

if (!echarts) {
  console.error('ECharts not loaded! Include ECharts CDN in the HTML.');
}

// Register CO.RA.PAN theme
if (echarts) {
  echarts.registerTheme('corapan', corapanTheme);
}

/**
 * Format number with Spanish locale
 */
function formatNumber(n) {
  return new Intl.NumberFormat('es-ES').format(n);
}

/**
 * Format percentage with Spanish locale
 */
function formatPercent(p) {
  return new Intl.NumberFormat('es-ES', {
    style: 'percent',
    maximumFractionDigits: 1,
  }).format(p);
}

/**
 * Get text color from CSS variable based on current theme
 */
function getTextColor() {
  return getComputedStyle(document.documentElement)
    .getPropertyValue('--md-sys-color-on-surface')
    .trim() || '#1C1B1F';
}

/**
 * Render a bar chart in the specified container
 * 
 * @param {HTMLElement} container - Chart container element
 * @param {Array<{key: string, n: number, p: number}>} data - Chart data
 * @param {string} title - Chart title (Spanish)
 * @param {string} displayMode - Display mode: 'absolute' (default) or 'percent'
 * @returns {echarts.ECharts} Chart instance
 */
export function renderBar(container, data, title, displayMode = 'absolute') {
  if (!container) {
    console.error('renderBar: container is null or undefined');
    return null;
  }

  // Handle empty data
  if (!data || data.length === 0) {
    container.innerHTML = '<div class="chart-empty">Sin datos para los filtros actuales.</div>';
    return null;
  }

  // Dispose existing chart instance
  const existingInstance = echarts.getInstanceByDom(container);
  if (existingInstance) {
    existingInstance.dispose();
  }

  // Get current text color (supports light/dark mode)
  const textColor = getTextColor();
  
  // Get divider color from CSS (supports dark mode)
  const dividerColor = getComputedStyle(document.documentElement)
    .getPropertyValue('--md-sys-color-outline-variant')
    .trim() || 'rgba(0, 0, 0, 0.12)';
  
  // Get primary color from CSS (supports dark mode)
  const primaryColor = getComputedStyle(document.documentElement)
    .getPropertyValue('--md-sys-color-primary')
    .trim() || '#1B5E9F';
  
  const primaryContainerColor = getComputedStyle(document.documentElement)
    .getPropertyValue('--md-sys-color-primary-container')
    .trim() || '#5A7FA3';

  // Extract categories and values based on display mode
  const categories = data.map(item => item.key);
  const values = displayMode === 'percent' 
    ? data.map(item => item.p * 100) // Convert to percentage (0-100 scale)
    : data.map(item => item.n);
  const absoluteValues = data.map(item => item.n);
  const proportions = data.map(item => item.p);

  // Determine if axis labels should be rotated
  const shouldRotate = categories.length > 20;

  // Determine if dataZoom is needed
  const needsDataZoom = categories.length > 30;

  // Calculate container height based on data length
  const baseHeight = 360;
  const additionalHeight = Math.max(0, (categories.length - 10) * 5);
  const height = Math.min(baseHeight + additionalHeight, 600);
  container.style.height = `${height}px`;
  
  // Dynamic bar width based on number of categories
  // Fewer categories = wider bars (max 32), Many categories = thinner bars (min 16)
  const barWidth = categories.length > 15 ? 16 : 32;

  // Initialize chart
  const chart = echarts.init(container, 'corapan', {
    renderer: 'canvas',
  });

  // Chart configuration
  const option = {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 500,
    grid: {
      top: 10,
      bottom: 10,
      left: 10,
      right: 40, // Space for labels
      containLabel: true
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--md-sys-color-surface-container') || '#fff',
      borderColor: getComputedStyle(document.documentElement).getPropertyValue('--md-sys-color-outline-variant') || '#ccc',
      textStyle: {
        color: textColor
      },
      formatter: function(params) {
        const item = params[0];
        const dataIndex = item.dataIndex;
        const absVal = absoluteValues[dataIndex];
        const pctVal = proportions[dataIndex];
        
        return `
          <div style="font-weight: 500; margin-bottom: 4px;">${item.name}</div>
          <div>${formatNumber(absVal)} hits</div>
          <div style="opacity: 0.8;">${formatPercent(pctVal)}</div>
        `;
      }
    },
    xAxis: {
      type: 'value',
      show: true, // Show X axis
      splitLine: { 
        show: true,
        lineStyle: {
          color: dividerColor,
          type: 'dashed'
        }
      },
      axisLabel: {
        color: textColor,
        formatter: displayMode === 'percent' 
          ? (value) => `${value.toFixed(1)}%`
          : (value) => formatNumber(value),
      }
    },
    yAxis: {
      type: 'category',
      data: categories,
      inverse: true, // Top to bottom
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: textColor,
        width: 140, // Limit label width
        overflow: 'break', // Wrap text
        interval: 0,
        fontSize: 13,
        fontFamily: 'system-ui, sans-serif'
      }
    },
    series: [
      {
        name: title,
        type: 'bar',
        data: values,
        barWidth: barWidth, // Dynamic bar width
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: function(params) {
            // Use different colors for bars
            const colors = [
              '#006C4C', '#006D31', '#3E638B', '#6750A4', '#9A4058', 
              '#9D4226', '#8B5000', '#725C00', '#566500', '#3A6900'
            ];
            return colors[params.dataIndex % colors.length];
          }
        },
        label: {
          show: true,
          position: 'right',
          formatter: function(params) {
            if (displayMode === 'percent') {
              return params.value.toFixed(1) + '%';
            }
            return formatNumber(params.value);
          },
          color: textColor,
          fontSize: 12
        },
        // Background bar
        showBackground: false,
        backgroundStyle: {
          color: 'transparent',
          borderRadius: [0, 4, 4, 0]
        }
      }
    ]
  };

  chart.setOption(option);

  // Setup resize observer for responsive behavior
  const resizeObserver = new ResizeObserver(() => {
    chart.resize();
  });
  resizeObserver.observe(container);

  // Store observer on chart instance for cleanup
  chart._resizeObserver = resizeObserver;

  return chart;
}

/**
 * Update chart for theme changes (dark/light mode)
 * 
 * @param {echarts.ECharts} chart - Chart instance
 */
export function updateChartTheme(chart) {
  if (!chart) return;

  const textColor = getTextColor();
  
  chart.setOption({
    xAxis: {
      axisLabel: {
        color: textColor,
      },
    },
    yAxis: {
      axisLabel: {
        color: textColor,
      },
    },
  }, { notMerge: false });
}

/**
 * Update chart display mode (absolute ↔ percentage) with smooth transition
 * 
 * @param {echarts.ECharts} chart - Chart instance
 * @param {Array<{key: string, n: number, p: number}>} data - Chart data
 * @param {string} displayMode - 'absolute' or 'percent'
 */
export function updateChartMode(chart, data, displayMode) {
  if (!chart || !data) return;

  const textColor = getTextColor();
  const usePercent = displayMode === 'percent';
  const values = usePercent 
    ? data.map(item => item.p * 100)
    : data.map(item => item.n);

  // Update with smooth transition (universalTransition handles the morphing)
  chart.setOption({
    xAxis: {
      max: usePercent ? 100 : null,
      axisLabel: {
        color: textColor,
        formatter: usePercent 
          ? (value) => `${value.toFixed(1)}%`
          : (value) => formatNumber(value),
      },
    },
    series: [{
      data: values,
    }],
  }, { notMerge: false }); // Important: notMerge:false enables universalTransition
}

/**
 * Dispose chart and cleanup resources
 * 
 * @param {echarts.ECharts} chart - Chart instance
 */
export function disposeChart(chart) {
  if (!chart) return;

  // Cleanup resize observer
  if (chart._resizeObserver) {
    chart._resizeObserver.disconnect();
    delete chart._resizeObserver;
  }

  chart.dispose();
}
