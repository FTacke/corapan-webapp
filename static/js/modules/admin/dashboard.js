const metricsGrid = document.querySelector('[data-element="metrics-grid"]');
const toggleButton = document.querySelector('[data-element="toggle-temp"]');
const toggleLabel = document.querySelector(
  '[data-element="toggle-temp-label"]',
);

const numberFormatter = new Intl.NumberFormat("es-ES");

function getInitialToggleState() {
  const globalValue = window.__CORAPAN__?.allowPublicTempAudio;
  if (typeof globalValue === "boolean") {
    return globalValue;
  }
  if (typeof globalValue === "string") {
    return globalValue.toLowerCase() === "true";
  }
  return false;
}

let allowPublicTempAudio = getInitialToggleState();

function updateToggleVisual(state) {
  if (!toggleButton || !toggleLabel) return;
  toggleButton.setAttribute("aria-checked", state ? "true" : "false");
  toggleLabel.textContent = state
    ? "Acceso público activado (/media/temp, /media/snippet)"
    : "Acceso público desactivado (/media/temp, /media/snippet)";
}

function summariseAccessMetric(data) {
  if (!data) {
    return { value: 0, detail: "Sin datos" };
  }
  const totalOverall = data.total?.overall ?? 0;
  const monthly = data.total?.monthly ?? {};
  const lastMonthKey = Object.keys(monthly).sort().pop();
  const monthlyTotal = lastMonthKey ? monthly[lastMonthKey] : 0;
  const detail = lastMonthKey
    ? `En ${lastMonthKey}: ${numberFormatter.format(monthlyTotal)}`
    : "Sin desglose mensual";
  return {
    value: totalOverall,
    detail,
  };
}

function summariseSimpleMetric(data) {
  if (!data) {
    return { value: 0, detail: "Sin datos" };
  }
  const total = data.overall ?? 0;
  return {
    value: total,
    detail: "Total hist\u00f3rico",
  };
}

function hydrateMetricCard(metric, payload) {
  if (!metricsGrid) return;
  const card = metricsGrid.querySelector(`[data-metric="${metric}"]`);
  if (!card) return;
  const valueEl = card.querySelector(".md3-metric-card__value");
  const detailEl = card.querySelector(".md3-metric-card__delta");

  let summary = { value: 0, detail: "Sin datos" };
  if (metric === "access") {
    summary = summariseAccessMetric(payload);
  } else {
    summary = summariseSimpleMetric(payload);
  }

  if (valueEl) {
    valueEl.textContent = numberFormatter.format(summary.value ?? 0);
  }
  if (detailEl) {
    detailEl.textContent = summary.detail;
  }
}

async function loadMetrics() {
  if (!metricsGrid) return;
  try {
    const response = await fetch("/admin/metrics", {
      credentials: "same-origin",
    });
    if (!response.ok) {
      throw new Error("No se pudieron obtener las métricas");
    }
    const payload = await response.json();
    hydrateMetricCard("access", payload.access);
    hydrateMetricCard("visits", payload.visits);
    hydrateMetricCard("search", payload.search);
  } catch (error) {
    console.error(error);
    metricsGrid.classList.add("is-error");
    metricsGrid
      .querySelectorAll(".md3-metric-card__delta")
      .forEach((element) => {
        element.textContent = "No se pudo cargar la información";
      });
  }
}

async function toggleTempAccess() {
  if (!toggleButton) return;
  toggleButton.disabled = true;
  try {
    const response = await fetch("/media/toggle/temp", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      throw new Error("No se pudo actualizar el ajuste");
    }
    const payload = await response.json();
    allowPublicTempAudio = Boolean(payload.allow_public_temp_audio);
    updateToggleVisual(allowPublicTempAudio);
    if (window.__CORAPAN__) {
      window.__CORAPAN__.allowPublicTempAudio = allowPublicTempAudio;
    }
  } catch (error) {
    console.error(error);
  } finally {
    toggleButton.disabled = false;
  }
}

updateToggleVisual(allowPublicTempAudio);
loadMetrics();

toggleButton?.addEventListener("click", toggleTempAccess);
