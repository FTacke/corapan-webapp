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

  // Initialize chart
  const chart = echarts.init(container, 'corapan', {
    renderer: 'canvas',
  });

  // Chart configuration
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: needsDataZoom ? '15%' : '3%',
      top: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: textColor,
        formatter: displayMode === 'percent' 
          ? (value) => `${value.toFixed(1)}%`
          : (value) => formatNumber(value),
      },
      splitLine: {
        lineStyle: {
          color: dividerColor,
        },
      },
      max: displayMode === 'percent' ? 100 : null,
    },
    yAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        color: textColor,
        rotate: shouldRotate ? 30 : 0,
        fontSize: categories.length > 25 ? 11 : 12,
      },
      axisTick: {
        alignWithLabel: true,
      },
    },
    series: [
      {
        name: title,
        type: 'bar',
        data: values,
        large: true,
        progressive: 800,
        // Smooth grow-in animation
        animation: true,
        animationDuration: 600,
        animationEasing: 'cubicOut',
        animationDelay: (idx) => idx * 15, // Stagger bars
        // Enable smooth transitions when switching n ↔ %
        universalTransition: true,
        itemStyle: {
          color: primaryColor,
          borderRadius: [0, 4, 4, 0],
        },
        emphasis: {
          itemStyle: {
            color: primaryContainerColor,
          },
        },
      },
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      formatter: (params) => {
        const item = params[0];
        const index = item.dataIndex;
        const n = absoluteValues[index];
        const p = proportions[index];
        return `
          <div style="padding: 4px 8px;">
            <div style="font-weight: 500; margin-bottom: 4px;">${item.name}</div>
            <div>n: ${formatNumber(n)}</div>
            <div>%: ${formatPercent(p)}</div>
          </div>
        `;
      },
    },
    dataZoom: needsDataZoom ? [
      {
        type: 'slider',
        yAxisIndex: 0,
        start: 0,
        end: Math.min(100, (30 / categories.length) * 100),
        handleSize: 20,
        showDetail: false,
      },
    ] : [],
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
