# Admin Dashboard - Analyse und Empfehlungen

**Datum:** 19. Oktober 2025  
**Status:** Phase 1 SOFORT - Abgeschlossen

---

## ✅ Implementierte Features

### 1. **Dashboard UI (Neu mit MD3-Design)**
- ✅ Moderne Hero-Section mit Eyebrow, Title, Subtitle
- ✅ Metriken-Cards mit Icons und Live-Daten
- ✅ MD3-Switch-Komponente für Toggle-Button
- ✅ Info-Card mit operativen Hinweisen
- ✅ Responsive Design (Mobile-first)
- ✅ Elevation und Hover-Effekte nach MD3-Spezifikation

### 2. **Backend API**
- ✅ `/admin/dashboard` - Dashboard-Seite (nur für Admins)
- ✅ `/admin/metrics` - JSON-Endpoint für Metriken
  - Counter: Accesos (mit monatlichem Breakdown)
  - Counter: Visitas (Gesamtzahl)
  - Counter: Búsquedas (Gesamtzahl)
- ✅ Role-based Access Control (RBAC)
- ✅ JWT-Cookie-Authentifizierung

### 3. **Metriken-System**
- ✅ Counter für Corpus-Zugriffe (`counter_access`)
- ✅ Counter für Seitenbesuche (`counter_visits`)
- ✅ Counter für Suchanfragen (`counter_search`)
- ✅ JSON-Persistenz in `data/counters/`

### 4. **Toggle-Funktion**
- ✅ Public Temp Audio aktivieren/deaktivieren
- ✅ Live-Update ohne Server-Neustart
- ✅ Endpoint: `POST /media/toggle/temp`

---

## 🔍 Funktionalitäts-Analyse

### User Management
**Status:** ❌ NICHT IMPLEMENTIERT

**Aktuelles System:**
- User-Daten werden in `CREDENTIALS` Dictionary gespeichert (in-memory)
- Passwörter werden beim Start aus `passwords.env` geladen
- Keine Persistenz, keine Datenbank
- Keine User-Verwaltung möglich

**Was fehlt:**
- User-Datenbank (SQLite oder ähnliches)
- CRUD-Operationen für User
- Passwort-Reset-Funktion
- User-Aktivierung/Deaktivierung
- Audit-Log für User-Aktionen

### Logging & Monitoring
**Status:** ✅ TEILWEISE IMPLEMENTIERT

**Vorhanden:**
- RotatingFileHandler in `logs/corapan.log`
- Login-Events werden geloggt (Success/Failure mit IP)
- Error-Events werden geloggt (500 mit Stack Trace)

**Was fehlt:**
- Log-Viewer im Admin-Dashboard
- Log-Level-Konfiguration (DEBUG, INFO, WARNING, ERROR)
- Strukturierte Logs (JSON-Format für maschinelles Parsing)
- Integration mit Monitoring-Tools (Sentry, Prometheus)
- Alert-System bei kritischen Errors

### Counter Management
**Status:** ⚠️ BASIC IMPLEMENTIERT

**Vorhanden:**
- JSON-basierte Counter
- Automatisches Increment

**Was fehlt:**
- Counter Reset-Funktion (z.B. monatlich)
- Counter-Export (CSV, Excel)
- Historische Daten-Visualisierung (Charts)
- Counter-Konfiguration (z.B. Custom-Counter)

### System Health
**Status:** ❌ NICHT IMPLEMENTIERT

**Was fehlt:**
- Disk Space Monitoring
- Memory Usage Monitoring
- Database Size Tracking
- Response Time Metrics
- Uptime Tracking
- Health Check Endpoint

---

## 📊 Empfohlene Erweiterungen

### PRIORITÄT 1: User Management (Kurzfristig)

**1. User-Datenbank erstellen**
```python
# src/app/models/user.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role: str
    email: str
    created_at: datetime
    last_login: datetime | None
    is_active: bool
```

**2. Admin-Routes erweitern**
```python
# src/app/routes/admin.py
@blueprint.get("/users")  # Liste aller User
@blueprint.post("/users")  # Neuen User anlegen
@blueprint.put("/users/<id>")  # User bearbeiten
@blueprint.delete("/users/<id>")  # User löschen
@blueprint.post("/users/<id>/reset-password")  # Passwort zurücksetzen
```

**3. UI-Komponenten**
- User-Liste mit DataTable
- User-Formular (Create/Edit)
- Passwort-Generator
- Role-Selector
- Active/Inactive Toggle

**Geschätzter Aufwand:** 2-3 Tage

---

### PRIORITÄT 2: Log Viewer (Kurzfristig)

**1. Backend**
```python
@blueprint.get("/logs")  # Log-Viewer-Page
@blueprint.get("/logs/data")  # JSON mit letzten N Einträgen
@blueprint.get("/logs/download")  # Log-Datei Download
```

**2. UI**
- Scrollbare Log-Anzeige mit Syntax-Highlighting
- Filter nach Level (DEBUG, INFO, WARNING, ERROR)
- Filter nach Datum
- Suche nach Keywords
- Auto-Refresh (optional)

**Geschätzter Aufwand:** 1-2 Tage

---

### PRIORITÄT 3: Counter Management (Mittelfristig)

**1. Backend**
```python
@blueprint.post("/counters/reset")  # Alle Counter zurücksetzen
@blueprint.post("/counters/<name>/reset")  # Einzelnen Counter zurücksetzen
@blueprint.get("/counters/export")  # CSV-Export
@blueprint.get("/counters/history")  # Historische Daten (Chart-Data)
```

**2. UI**
- Reset-Buttons mit Confirmation-Dialog
- Export-Button
- Chart.js Integration für Verlaufs-Graphen
- Zeitraum-Auswahl (Letzte 7 Tage, 30 Tage, etc.)

**Geschätzter Aufwand:** 2-3 Tage

---

### PRIORITÄT 4: System Health Dashboard (Mittelfristig)

**1. Backend**
```python
@blueprint.get("/health")  # System Health Metrics
```

**2. Metriken**
- Disk Space (Total, Used, Free)
- Memory (Total, Used, Free)
- Database Size
- Log File Size
- Uptime
- Average Response Time
- Error Rate (Last 24h)

**3. UI**
- Gauge-Charts für Disk/Memory
- Status-Badges (Healthy, Warning, Critical)
- Response Time Graph
- Error Rate Graph

**Geschätzter Aufwand:** 2-3 Tage

---

## 🎯 Implementierungs-Roadmap

### Phase A: Kurzfristig (Nächste 1-2 Wochen)
1. ✅ ~~Dashboard MD3-Design~~ (ABGESCHLOSSEN)
2. 🔲 User Management System
3. 🔲 Log Viewer

### Phase B: Mittelfristig (Nächste 3-4 Wochen)
4. 🔲 Counter Management
5. 🔲 System Health Dashboard
6. 🔲 Chart.js Integration

### Phase C: Langfristig (Nächste 2-3 Monate)
7. 🔲 Sentry Integration
8. 🔲 Prometheus Metrics
9. 🔲 Email-Alerts bei kritischen Events
10. 🔲 Backup-Management UI

---

## 🔧 Technische Empfehlungen

### Datenbank
**Option 1: SQLite (Empfohlen für Start)**
- Einfach zu deployen
- Keine zusätzliche Infrastruktur
- Gut für <100.000 User
- Bereits für Corpus verwendet

**Option 2: PostgreSQL (Langfristig)**
- Bessere Performance bei vielen Usern
- Bessere Concurrency
- Mehr Features (JSON, Full-Text-Search)

### Logging-Framework
**Empfehlung: Python Logging + Sentry**
- Strukturierte Logs mit `structlog`
- Error Tracking mit Sentry
- Kostenlos bis 5.000 Events/Monat

### Monitoring
**Empfehlung: Prometheus + Grafana**
- Open Source
- Sehr flexibel
- Gute Docker-Integration

---

## 📝 Nächste Schritte

1. **User Management implementieren**
   - SQLite-Tabelle erstellen
   - CRUD-Routes bauen
   - UI-Komponenten erstellen

2. **Log Viewer bauen**
   - Log-Parser schreiben
   - Route erstellen
   - UI mit Filtering

3. **Tests schreiben**
   - Unit-Tests für Admin-Routes
   - Integration-Tests für User-Management
   - E2E-Tests für Dashboard

4. **Dokumentation erweitern**
   - API-Dokumentation (Swagger/OpenAPI)
   - Admin-Handbuch
   - Troubleshooting-Guide

---

## 💡 Zusätzliche Features (Optional)

- **API Key Management** - Für externe Integrationen
- **Webhook-Konfiguration** - Bei bestimmten Events
- **Scheduled Tasks UI** - Cron-Jobs verwalten
- **Database Browser** - Datenbank-Explorer
- **File Manager** - Media-Dateien verwalten
- **Translation Manager** - i18n-Strings editieren

---

**Fazit:** Das Admin-Dashboard hat eine solide Basis mit modernem MD3-Design und funktionierenden Metriken. Die wichtigsten Erweiterungen sind User Management und Log Viewer für bessere Administrierbarkeit.
