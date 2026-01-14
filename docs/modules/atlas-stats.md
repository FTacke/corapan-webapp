# Atlas & Statistik Modul

**Scope:** Geografische & statistische Visualisierungen  
**Source-of-truth:** `src/app/routes/atlas.py`, `src/app/routes/stats.py`

## Übersicht

- **Atlas:** Leaflet-basierte Karten (OpenStreetMap)
- **Statistik:** ECharts-Diagramme (Balken, Line, Pie)
- **Export:** CSV/TSV mit Metadaten

**Routes:**
- `/atlas` — Geografische Visualisierung
- `/stats` — Statistik-Dashboard
- `/stats/export` — CSV/TSV Export

---

## Atlas

**Karte:** Leaflet + OpenStreetMap

```javascript
// Map initialisieren
const map = L.map("map").setView([40.4168, -3.7038], 6);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

// Marker pro Location
data.locations.forEach(loc => {
  L.marker([loc.lat, loc.lon])
    .bindPopup(`<b>${loc.name}</b><br>${loc.count} Sprecher`)
    .addTo(map);
});
```

---

## Statistik

**ECharts:**
```javascript
const chart = echarts.init(document.getElementById("chart"));
chart.setOption({
  xAxis: {type: "category", data: countries},
  yAxis: {type: "value"},
  series: [{type: "bar", data: counts}]
});
```

**Metriken:**
- Sprecher pro Land
- Geschlechterverteilung
- Altersverteilung
- Bildungsniveau

---

## Export

**Route:** `GET /stats/export?format=csv`

```python
@stats_bp.route("/export")
@jwt_required()
def export():
    data = get_corpus_statistics()
    
    # CSV generieren
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["country", "count"])
    writer.writeheader()
    writer.writerows(data)
    
    return Response(output.getvalue(), mimetype="text/csv")
```

---

## Extension Points

- **Heatmaps:** Dichte-Visualisierung
- **Zeitreihen:** Korpus-Wachstum über Zeit
- **Kollokations-Netzwerke:** (D3.js)
