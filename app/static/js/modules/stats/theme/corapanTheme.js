/**
 * CO.RA.PAN ECharts Theme
 *
 * Phase-2 locked rule: runtime chart colors must resolve from CSS tokens,
 * not from an independent JS palette.
 */

function cssVar(name, fallback) {
  if (typeof document === "undefined") {
    return fallback;
  }

  return (
    getComputedStyle(document.documentElement).getPropertyValue(name).trim() ||
    fallback
  );
}

export function buildCorapanTheme() {
  const palette = [
    cssVar("--md-sys-color-primary", "#1B5E9F"),
    cssVar("--md-sys-color-primary-container", "#5A7FA3"),
    cssVar("--md-sys-color-secondary", "#78909C"),
    cssVar("--md-sys-color-secondary-container", "#B0BEC5"),
    cssVar("--md-sys-color-tertiary", "#455A64"),
    cssVar("--md-sys-color-surface-container-high", "#90A4AE"),
  ];
  const surface = cssVar("--md-sys-color-surface", "#ffffff");
  const onSurface = cssVar("--md-sys-color-on-surface", "CanvasText");
  const outline = cssVar("--md-sys-color-outline", "GrayText");
  const outlineVariant = cssVar("--md-sys-color-outline-variant", outline);
  const success = cssVar("--md-sys-color-success", palette[0]);
  const error = cssVar("--md-sys-color-error", palette[2]);

  return {
    color: palette,
    backgroundColor: "transparent",
    textStyle: {
      fontFamily:
        'system-ui, Roboto, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif',
      fontSize: 14,
      color: onSurface,
    },
    title: {
      textStyle: {
        fontWeight: 500,
        fontSize: 16,
        color: onSurface,
      },
      subtextStyle: {
        fontSize: 14,
        color: onSurface,
      },
    },
    line: {
      itemStyle: {
        borderWidth: 2,
      },
      lineStyle: {
        width: 2,
      },
      symbolSize: 6,
      symbol: "circle",
      smooth: false,
    },
    bar: {
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
      },
    },
    pie: {
      itemStyle: {
        borderRadius: 4,
        borderWidth: 2,
        borderColor: surface,
      },
    },
    scatter: {
      itemStyle: {
        borderWidth: 0,
      },
      symbolSize: 8,
    },
    boxplot: {
      itemStyle: {
        borderWidth: 1,
      },
    },
    parallel: {
      itemStyle: {
        borderWidth: 0,
      },
      lineStyle: {
        width: 1,
      },
    },
    sankey: {
      itemStyle: {
        borderWidth: 0,
      },
      lineStyle: {
        width: 1,
        color: outlineVariant,
      },
    },
    funnel: {
      itemStyle: {
        borderWidth: 0,
      },
    },
    gauge: {
      itemStyle: {
        borderWidth: 0,
      },
    },
    candlestick: {
      itemStyle: {
        color: success,
        color0: error,
        borderColor: success,
        borderColor0: error,
        borderWidth: 1,
      },
    },
    graph: {
      itemStyle: {
        borderWidth: 0,
      },
      lineStyle: {
        width: 1,
        color: outlineVariant,
      },
      symbolSize: 6,
      symbol: "circle",
      smooth: false,
      color: palette,
      label: {
        color: surface,
      },
    },
    categoryAxis: {
      axisLine: {
        show: true,
        lineStyle: {
          color: outlineVariant,
        },
      },
      axisTick: {
        show: true,
        lineStyle: {
          color: outlineVariant,
        },
      },
      axisLabel: {
        show: true,
        color: onSurface,
      },
      splitLine: {
        show: false,
      },
      splitArea: {
        show: false,
      },
    },
    valueAxis: {
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        show: true,
        color: onSurface,
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: outlineVariant,
          type: "solid",
        },
      },
      splitArea: {
        show: false,
      },
    },
    logAxis: {
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      axisLabel: {
        show: true,
        color: onSurface,
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: outlineVariant,
        },
      },
      splitArea: {
        show: false,
      },
    },
    timeAxis: {
      axisLine: {
        show: true,
        lineStyle: {
          color: outlineVariant,
        },
      },
      axisTick: {
        show: true,
        lineStyle: {
          color: outlineVariant,
        },
      },
      axisLabel: {
        show: true,
        color: onSurface,
      },
      splitLine: {
        show: true,
        lineStyle: {
          color: outlineVariant,
        },
      },
      splitArea: {
        show: false,
      },
    },
    toolbox: {
      iconStyle: {
        borderColor: outline,
      },
      emphasis: {
        iconStyle: {
          borderColor: palette[0],
        },
      },
    },
    legend: {
      textStyle: {
        color: onSurface,
      },
    },
    tooltip: {
      axisPointer: {
        lineStyle: {
          color: outline,
          width: 1,
        },
        crossStyle: {
          color: outline,
          width: 1,
        },
      },
    },
    timeline: {
      lineStyle: {
        color: palette[5],
        width: 1,
      },
      itemStyle: {
        color: palette[2],
        borderWidth: 1,
      },
      controlStyle: {
        color: palette[0],
        borderColor: palette[0],
        borderWidth: 1,
      },
      checkpointStyle: {
        color: palette[0],
        borderColor: outlineVariant,
      },
      label: {
        color: onSurface,
      },
      emphasis: {
        itemStyle: {
          color: palette[1],
        },
        controlStyle: {
          color: palette[0],
          borderColor: palette[0],
          borderWidth: 1,
        },
        label: {
          color: onSurface,
        },
      },
    },
    visualMap: {
      color: palette.slice(0, 4),
      textStyle: {
        color: onSurface,
      },
    },
    dataZoom: {
      backgroundColor: outlineVariant,
      dataBackgroundColor: palette[1],
      fillerColor: palette[0],
      handleColor: palette[0],
      handleSize: "100%",
      textStyle: {
        color: onSurface,
      },
    },
    markPoint: {
      label: {
        color: surface,
      },
      emphasis: {
        label: {
          color: surface,
        },
      },
    },
  };
}

export default buildCorapanTheme();
