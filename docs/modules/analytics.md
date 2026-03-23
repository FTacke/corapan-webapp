# Analytics Modul

**Scope:** DSGVO-konformes Tracking  
**Source-of-truth:** `src/app/analytics/`, `src/app/routes/analytics.py`

## Übersicht

Das Analytics-Modul bietet:
- **Anonymes Tracking:** Keine personenbezogenen Daten
- **Daily Aggregates:** Visitor, Searches, Audio-Plays
- **Admin Dashboard:** Visualisierung (ECharts)
- **DSGVO-konform:** Kein Consent-Banner nötig

**Routes:**
- `/analytics/dashboard` — Admin-Dashboard (Admin-only)
- `/analytics/track` — Tracking-Endpoint (POST, intern)

**Datenbank:** `analytics_daily` Tabelle

---

## Datenmodell

**Tabelle:** `analytics_daily`

| Spalte | Typ | Beschreibung |
|--------|-----|--------------|
| `date` | DATE | Tag (Primary Key) |
| `visitors` | INTEGER | Unique Visitors (Session-basiert) |
| `mobile` | INTEGER | Mobile Geräte |
| `desktop` | INTEGER | Desktop Geräte |
| `searches` | INTEGER | Suchvorgänge |
| `audio_plays` | INTEGER | Audio-Wiedergaben |
| `errors` | INTEGER | 4xx/5xx Fehler |

**Wichtig:** **Keine** IPs, **keine** User-IDs, **keine** Suchinhalte gespeichert!

---

## Tracking

**Client-Side:**
```javascript
// static/js/analytics.js (optional)
async function trackEvent(type) {
  await fetch("/analytics/track", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({event: type})
  });
}

// Beispiel: Search getrackt
document.querySelector("#search-form").addEventListener("submit", () => {
  trackEvent("search");
});
```

**Server-Side (Middleware):**
```python
# src/app/__init__.py
@app.before_request
def track_request():
    if request.path.startswith("/static/"):
        return
    
    # Session-basierter Visitor-Count (kein Cookie)
    session_id = session.get("_analytics_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["_analytics_id"] = session_id
        
        # Visitor inkrementieren
        increment_daily_counter("visitors")
    
    # Device-Type (Mobile/Desktop)
    if is_mobile(request.user_agent):
        increment_daily_counter("mobile")
    else:
        increment_daily_counter("desktop")
```

---

## Aggregation

```python
# src/app/analytics/services.py
def increment_daily_counter(metric: str):
    today = date.today()
    
    with get_session() as session:
        row = session.query(AnalyticsDaily).filter_by(date=today).first()
        
        if not row:
            row = AnalyticsDaily(date=today)
            session.add(row)
        
        # Inkrementieren
        if metric == "visitors":
            row.visitors += 1
        elif metric == "searches":
            row.searches += 1
        elif metric == "audio_plays":
            row.audio_plays += 1
        elif metric == "errors":
            row.errors += 1
        
        row.updated_at = datetime.utcnow()
        session.commit()
```

---

## Admin Dashboard

**Route:** `GET /analytics/dashboard`

**Template:** `templates/analytics/dashboard.html`

**Charts (ECharts):**
```javascript
// Line Chart: Visitors über Zeit
const chart = echarts.init(document.getElementById("visitors-chart"));
chart.setOption({
  xAxis: {type: "category", data: dates},
  yAxis: {type: "value"},
  series: [{type: "line", data: visitors}]
});
```

**Metriken:**
- Visitors (letzte 30 Tage)
- Searches (letzte 30 Tage)
- Audio Plays (letzte 30 Tage)
- Mobile vs Desktop (Pie Chart)
- Top Search Days

---

## DSGVO-Konformität

**Was wird NICHT gespeichert:**
- IP-Adressen
- User-IDs (außer anonyme Session-Hashes)
- Suchinhalte
- URLs (außer Page-Type)
- Referrer
- Cookies (außer Session-ID)

**Session-ID:**
- Zufällig generiert (UUID)
- Nicht mit User verknüpft
- Nur für Unique-Visitor-Count
- Läuft ab nach Session-Ende

**Rechtslage:**
- Keine Einwilligung nötig (Art. 6 Abs. 1 lit. f DSGVO)
- Berechtigtes Interesse: Nutzungsstatistiken

---

## Extension Points

**Neue Metriken:**
- Page Views pro Seite
- Fehlertypen (404, 500, etc.)
- Export-Anzahl

**Erweiterte Analysen:**
- Zeitreihen-Analyse
- Anomalie-Erkennung
- Prognosen (Machine Learning)

**Export:**
- CSV/Excel Export
- API-Endpoint für externe Tools

---

## Projekt-spezifische Annahmen

- **Opt-In:** Modul ist aktiv (kann deaktiviert werden)
- **Retention:** Daten bleiben unbegrenzt (keine automatische Löschung)
- **Aggregation:** Täglich (keine stündliche Granularität)
