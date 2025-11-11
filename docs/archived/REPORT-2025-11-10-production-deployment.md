---
title: "Production Deployment Report"
status: archived
owner: devops
updated: "2025-11-10"
tags: [report, deployment, production, stage-5]
---

# Production Deployment Report — Stage 5

**Date:** 2025-11-10  
**Phase:** Stage 5 — Production Go-Live (Flask-Proxy + BlackLab Server)  
**Status:** ✅ Documentation Complete, ⚠️ Live Tests Pending

---

## Summary

- **Files Created:** 4
- **Files Modified:** 4
- **Live Tests:** Pending (manual execution required)
- **Documentation:** Complete (Deployment, Runbook, Testing)

---

## Changes

| Datei (neu/geändert) | Aktion | Status |
|----------------------|--------|--------|
| `ops/corapan-gunicorn.service` | create | ✅ Done |
| `scripts/start_waitress.py` | create | ✅ Done |
| `docs/operations/production-deployment.md` | create | ✅ Done |
| `docs/operations/runbook-advanced-search.md` | create | ✅ Done |
| `docs/operations/development-setup.md` | modify | ✅ Done |
| `docs/how-to/advanced-search.md` | modify | ✅ Done |
| `docs/reference/search-params.md` | modify | ✅ Done |
| `docs/CHANGELOG.md` | modify | ✅ Done |

---

## Deliverables

### 1. Production Deployment Guide
**File:** `docs/operations/production-deployment.md`

**Content:**
- **Pre-Deployment:** TSV-Export, Index-Build, systemd-Units
- **Deployment Steps:**
  1. BlackLab Server starten (systemd/manual)
  2. Flask App starten (Gunicorn/Waitress)
  3. Validierung (5 Smoke Tests)
  4. Logging (journalctl/tail)
- **Smoke Tests:**
  - Proxy Health (`/bls/`)
  - CQL Autodetect (patt/cql/cql_query)
  - Serverfilter (with/without `filter=`)
  - Advanced Search UI (HTML `md3-search-summary`)
  - Load Test (Apache Bench)
- **Rollback:** BLS-Neustart, Flask-Reload, Index-Fallback
- **Monitoring:** Healthchecks, Alerts, Logs
- **Checkliste:** Pre/Post-Deployment

**Status:** ✅ Complete

---

### 2. Runbook: Advanced Search
**File:** `docs/operations/runbook-advanced-search.md`

**Content:**
- **Quick Reference Table:** 5 Incident-Szenarien
- **Incident 1:** BLS Server nicht erreichbar (502 Bad Gateway)
  - Diagnose: `ps aux | grep blacklab-server`, `curl http://localhost:8081/...`
  - Lösung: `systemctl restart blacklab-server`
- **Incident 2:** BLS Server Timeout (504 Gateway Timeout)
  - Diagnose: BLS Load, Memory
  - Lösung: Restart, Memory erhöhen, Index-Rebuild
- **Incident 3:** Advanced Search No Results (False Negative)
  - Diagnose: CQL-Syntax, Serverfilter, Index-Fields
  - Lösung: Fix CQL, Remove Filter, Rebuild Index
- **Incident 4:** Rate-Limit 429 Too Many Requests
  - Diagnose: Check IP, Limit
  - Lösung: Whitelist IP, Block IP, Erhöhe Limit
- **Incident 5:** Flask 500 Internal Server Error
  - Diagnose: Flask Logs (journalctl/tail)
  - Lösung: Fix DB-Lock, JSON-Parsing, Template-Error, Rollback
- **Maintenance Mode:** Flag-File, Banner
- **Escalation Matrix:** P1-P4 Severity
- **Post-Incident Review:** Template

**Status:** ✅ Complete

---

### 3. Waitress Start Script (Windows)
**File:** `scripts/start_waitress.py`

**Content:**
- CLI-Args: `--host`, `--port`, `--threads`
- Environment: `FLASK_ENV=production`, `BLS_BASE_URL`
- Start: `serve(app, host='0.0.0.0', port=8000, threads=4)`

**Usage:**
```bash
python scripts/start_waitress.py --port 8000 --threads 4
```

**Status:** ✅ Complete

---

### 4. systemd-Unit: Gunicorn (Linux)
**File:** `ops/corapan-gunicorn.service`

**Content:**
- **Service:** Gunicorn mit 4 Workers, Timeout 180s
- **Environment:** `FLASK_ENV=production`, `BLS_BASE_URL=http://localhost:8081/blacklab-server`
- **Logging:** `/var/log/corapan/access.log`, `/var/log/corapan/error.log`
- **Restart:** `on-failure`, `RestartSec=10s`

**Installation:**
```bash
sudo cp ops/corapan-gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable corapan-gunicorn
sudo systemctl start corapan-gunicorn
```

**Status:** ✅ Complete

---

### 5. Documentation Updates

**Modified Files:**
- `docs/operations/development-setup.md` → Added "Production Deployment" section
- `docs/how-to/advanced-search.md` → Added "Live Testing (Production)" with 4 curl tests
- `docs/reference/search-params.md` → Enhanced "Server-Side Filter Detection" with UI Badge
- `docs/CHANGELOG.md` → Release [2.4.0] - Production Deployment & Operations

**Status:** ✅ Complete

---

## Live Tests (Pending)

**Voraussetzungen:**
- BlackLab Server läuft (`bash scripts/run_bls.sh 8081 2g 512m`)
- Flask läuft (Waitress: `python scripts/start_waitress.py`)

**Tests (manuell in separatem Terminal):**

### Test 1: Proxy Health
```bash
curl -s http://localhost:8000/bls/ | jq .blacklabBuildTime
```
**Erwartung:** `"2024-XX-XX XX:XX:XX"`

### Test 2: CQL Autodetect
```bash
for P in patt cql cql_query; do
  curl -s "http://localhost:8000/bls/corapan/hits?${P}=[lemma=\"ser\"]&maxhits=3" | jq '.summary.numberOfHits';
done
```
**Erwartung:** Alle drei liefern `numberOfHits > 0`

### Test 3: Serverfilter
```bash
# Ohne Filter
curl -s 'http://localhost:8000/bls/corapan/hits?patt=[word="test"]&maxhits=1' \
  | jq '.summary | {docsRetrieved, numberOfDocs}'

# Mit Filter
curl -s 'http://localhost:8000/bls/corapan/hits?filter=country:"ARG"&patt=[word="test"]&maxhits=1' \
  | jq '.summary | {docsRetrieved, numberOfDocs}'
```
**Erwartung:** `docsRetrieved` mit Filter < ohne Filter

### Test 4: Advanced Search UI
```bash
curl -s 'http://localhost:8000/search/advanced/results?q=M%C3%A9xico&mode=forma_exacta' | head -c 500
```
**Erwartung:** HTML mit `<div class="md3-search-summary" aria-live="polite">`

**Status:** ⚠️ Pending (benötigt separates Terminal für Waitress)

---

## Akzeptanzkriterien

**Erfüllt:**
- ✅ Deployment-Guide mit Step-by-Step-Anleitung
- ✅ Runbook mit 5 Incident-Szenarien
- ✅ WSGI-Unterstützung: Gunicorn (Linux) + Waitress (Windows)
- ✅ systemd-Units für Production
- ✅ Live-Test-Befehle dokumentiert
- ✅ Serverfilter-Badge dokumentiert (`docsRetrieved < numberOfDocs`)

**Offen:**
- ⚠️ Live-Tests nicht ausgeführt (manuell erforderlich)
- ⚠️ Load-Test (Apache Bench) nicht durchgeführt
- ⚠️ Monitoring/Healthchecks nicht implementiert (nur dokumentiert)

---

## Nächste Schritte (Manual Execution Required)

### 1. Flask mit Waitress starten (separates Terminal)
```bash
python scripts/start_waitress.py
```

### 2. Live-Tests ausführen (zweites Terminal)
```bash
# Test 1: Proxy
curl -s http://localhost:8000/bls/ | jq .blacklabBuildTime

# Test 2: CQL
for P in patt cql cql_query; do
  curl -s "http://localhost:8000/bls/corapan/hits?${P}=[lemma=\"ser\"]&maxhits=3" | jq '.summary.numberOfHits';
done

# Test 3: Serverfilter
curl -s 'http://localhost:8000/bls/corapan/hits?patt=[word="test"]&maxhits=1' | jq '.summary'
curl -s 'http://localhost:8000/bls/corapan/hits?filter=country:"ARG"&patt=[word="test"]&maxhits=1' | jq '.summary'

# Test 4: UI
curl -s 'http://localhost:8000/search/advanced/results?q=M%C3%A9xico&mode=forma_exacta' | grep "md3-search-summary"
```

### 3. UAT (User Acceptance Testing)
- **Szenarien:**
  - forma_exacta: `q=México&mode=forma_exacta`
  - forma (case-insensitive): `q=méxico&mode=forma`
  - lemma: `q=ser&mode=lema`
  - POS: `q=ser&mode=lema&pos=VERB`
  - Sequenz: `q=ir a&mode=lema`
  - Filter: `q=covid&filter=country:ARG`
- **Badge:** "filtrado activo" bei `docsRetrieved < numberOfDocs`

### 4. Production Deployment (Linux)
```bash
# Install systemd-Units
sudo cp ops/corapan-gunicorn.service /etc/systemd/system/
sudo cp ops/blacklab-server.service /etc/systemd/system/  # (falls vorhanden)
sudo systemctl daemon-reload

# Start Services
sudo systemctl start blacklab-server
sudo systemctl start corapan-gunicorn

# Verify
sudo systemctl status corapan-gunicorn
curl http://localhost:8000/bls/ | jq .blacklabBuildTime
```

---

## Known Limitations

**Windows:**
- Gunicorn nicht verfügbar (Unix-only) → Waitress als Alternative
- systemd nicht verfügbar → Manueller Start mit `start_waitress.py`

**Testing:**
- Live-Tests nicht automatisiert (manuell in separatem Terminal)
- Load-Test nicht durchgeführt (Apache Bench optional)

**Monitoring:**
- Healthchecks dokumentiert, aber nicht implementiert
- Alerts (5xx, Timeouts) dokumentiert, aber nicht konfiguriert

---

## Siehe auch

- [Production Deployment Guide](../operations/production-deployment.md)
- [Runbook: Advanced Search](../operations/runbook-advanced-search.md)
- [Development Setup](../operations/development-setup.md)
- [How-To: Advanced Search](../how-to/advanced-search.md)
- [CHANGELOG](../CHANGELOG.md) - Release [2.4.0]
