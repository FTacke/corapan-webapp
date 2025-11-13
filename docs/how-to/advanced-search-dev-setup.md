# Advanced Search Dev Setup: BlackLab Configuration & Troubleshooting

**Date:** November 13, 2025  
**Author:** GitHub Copilot  
**Audience:** Developers working on the Advanced Search feature  
**Status:** Complete

## Overview

The Advanced Search feature requires a running **BlackLab Server** instance. This guide explains:

1. How BlackLab is configured in the app
2. How to start BlackLab locally for development
3. How to diagnose issues when BlackLab is unavailable
4. What happens in the UI when BlackLab goes offline

---

## 1. BlackLab Configuration

### Quick Start for Windows Development

**Fastest way to get Advanced Search running:**

```powershell
# Terminal 1: Start Mock BlackLab Server (Port 8081)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python scripts/mock_bls_server.py 8081"

# Terminal 2: Start Flask with BLS_BASE_URL
.venv\Scripts\activate
$env:FLASK_ENV="development"
$env:BLS_BASE_URL="http://localhost:8081/blacklab-server"
python -m src.app.main

# Test in browser: http://localhost:8000/search/advanced
# Search for "casa" - should return 324 mock results
```

---

### Environment Variable

The app communicates with BlackLab via the `BLS_BASE_URL` environment variable:

```bash
# Default (if not set)
BLS_BASE_URL=http://localhost:8081/blacklab-server

# Set manually for local dev (Docker on different port)
export BLS_BASE_URL=http://localhost:8080/blacklab-server

# Or in passwords.env (read on app startup)
BLS_BASE_URL=http://localhost:8080/blacklab-server
```

### Configuration Location

- **Environment variable:** `BLS_BASE_URL`
- **Default value:** `http://localhost:8081/blacklab-server`
- **Code location:** `src/app/extensions/http_client.py`
- **Setup method:** `passwords.env` or shell export

### What URL Should Point To?

BlackLab exposes two interfaces:

| Interface       | Purpose                              | Example URL                           |
|-----------------|--------------------------------------|---------------------------------------|
| **FCS** (Search)| REST API for search, exports, etc.  | `http://localhost:8080/blacklab-server` |
| **GUI**         | Web interface (optional)            | `http://localhost:8080/blacklab-server-gui` |

The app uses the **FCS interface** for CQL queries, metadata filtering, and hit retrieval.

---

## 2. Starting BlackLab Locally

### Quick Start: Mock Server (Recommended for Development)

For **rapid development and UI testing**, use the included mock BlackLab server:

```powershell
# Windows PowerShell - Start mock server in separate window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python scripts/mock_bls_server.py 8081"

# Or run directly in current terminal
python scripts/mock_bls_server.py 8081
```

**What the mock provides:**
- ✅ Realistic response structure matching real BlackLab API
- ✅ 324 mock hits with KWIC data (left, match, right)
- ✅ Pagination, filtering, and metadata support
- ✅ Fast startup (no index building required)
- ⚠️ **Limitation:** Returns same mock data for any query (not real search results)

**When to use mock:**
- UI development and styling
- Error handling testing
- DataTables integration verification
- Quick local testing without Docker

---

### Option A: Docker Container (For Real Search Results)

```bash
# Start BlackLab on port 8080 (map to 8080 on host)
docker run -d \
  --name blacklab-dev \
  -p 8080:8080 \
  -v "$(pwd)/config/blacklab/corapan.blf.yaml:/etc/blacklab/corapan.blf.yaml:ro" \
  -v "$(pwd)/data/blacklab_index:/var/lib/blacklab/index:rw" \
  corpuslab/blacklab-server:3.5.0

# Verify it's running
curl -s http://localhost:8080/blacklab-server/ | head -20
# Should return XML/JSON with BlackLab server info
```

### Option B: Docker Compose (Advanced)

If you want to manage BlackLab alongside the Flask app in production, add a service to `docker-compose.yml`:

```yaml
services:
  # ... existing web service ...
  
  blacklab:
    image: corpuslab/blacklab-server:3.5.0
    container_name: corapan-blacklab-dev
    ports:
      - "8081:8080"
    volumes:
      - ./config/blacklab/corapan.blf.yaml:/etc/blacklab/corapan.blf.yaml:ro
      - ./data/blacklab_index:/var/lib/blacklab/index:rw
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s

  web:
    # ... existing config ...
    environment:
      BLS_BASE_URL: "http://blacklab:8080/blacklab-server"
    depends_on:
      - blacklab
```

Then start with:
```bash
docker-compose up -d blacklab
docker-compose up -d web
```

### Option C: Standalone JAR (If Available)

If you have a BlackLab JAR file locally:

```bash
java -jar blacklab-server.jar \
  --port 8080 \
  --config config/blacklab/corapan.blf.yaml \
  --index data/blacklab_index/
```

---

## 3. Checking BlackLab Status

### Quick Health Check

```bash
# Check if BlackLab is responding
curl -s http://localhost:8080/blacklab-server/ | head -5

# Check via the app's health endpoint
curl -s http://localhost:8000/health/bls | jq .
# Response:
# {
#   "ok": true,
#   "url": "http://localhost:8081/blacklab-server",
#   "status_code": 200,
#   "error": null
# }
```

### Using the App's Health Endpoints

**Check overall app + BlackLab:**
```bash
curl -s http://localhost:8000/health | jq .

# Response (BlackLab healthy):
# {
#   "status": "healthy",
#   "service": "corapan-web",
#   "checks": {
#     "flask": {"ok": true},
#     "blacklab": {"ok": true, "url": "http://localhost:8081/blacklab-server", "error": null}
#   }
# }

# Response (BlackLab unavailable):
# {
#   "status": "degraded",
#   "service": "corapan-web",
#   "checks": {
#     "flask": {"ok": true},
#     "blacklab": {"ok": false, "url": "http://localhost:8081/blacklab-server", 
#                  "error": "Connection refused (check if BlackLab is running at ...)"}
#   }
# }
```

**Check BlackLab only:**
```bash
curl -s http://localhost:8000/health/bls | jq .

# Response (healthy):
# {"ok": true, "url": "http://localhost:8081/blacklab-server", "status_code": 200, "error": null}

# Response (not running):
# {"ok": false, "url": "http://localhost:8081/blacklab-server", "status_code": null, 
#  "error": "Connection refused (check if BlackLab is running at http://localhost:8081/blacklab-server)"}
```

---

## 4. Troubleshooting: BlackLab Not Running

### Symptoms

1. **In Flask logs:**
   ```
   ERROR in advanced_api: BLS request failed on /corapan/hits: ConnectError: [WinError 10061] 
   Es konnte keine Verbindung hergestellt werden...
   ```

2. **In the browser (Advanced Search):**
   - Form works normally
   - Click "Search" → empty table appears
   - **Error banner above table:**
     > ☁️ **Search Backend Unavailable**
     > The search backend (BlackLab) is currently not reachable. Please check that the 
     > BlackLab server is running at `http://localhost:8081/blacklab-server`.

3. **Health check returns degraded:**
   ```bash
   curl -s http://localhost:8000/health | jq .checks.blacklab.ok
   # false
   ```

### Solutions

**Step 1: Verify BlackLab is running**

```bash
# Check if Docker container is running
docker ps | grep blacklab
# Or
docker logs corapan-blacklab-dev

# Check if process is listening on port 8080/8081
netstat -an | grep 8080  # Windows: use netstat -ano or Get-NetTCPConnection
```

**Step 2: Verify the configured URL**

```bash
# Check what URL is configured
echo $BLS_BASE_URL

# Or check in the app
curl -s http://localhost:8000/health/bls | jq .url
```

**Step 3: Test connectivity directly**

```bash
# From host machine
curl -v http://localhost:8080/blacklab-server/

# From inside Docker app container
docker exec corapan-container curl -v http://blacklab:8080/blacklab-server/
# (if using docker-compose network)
```

**Step 4: Check Docker network (if using compose)**

```bash
# Verify services are on the same network
docker network inspect corapan-network

# Restart both services
docker-compose restart blacklab web
```

---

## 5. UI Behavior When BlackLab is Unavailable

### Advanced Search Form

- ✅ Form inputs and filters work normally
- ✅ Submit button can be clicked
- ✅ Validation still happens (CQL syntax, required fields)

### Search Results

When BlackLab is offline and you click "Search":

1. **Error Banner appears** (MD3-styled, persistent):
   - **Icon:** ☁️ (cloud_off)
   - **Title:** "Search Backend Unavailable"
   - **Message:** Explains that BlackLab is not reachable and how to fix it

2. **Results table:**
   - Empty (no data shown)
   - No JavaScript errors in the console
   - DataTables initializes but shows 0 records

3. **Export buttons:**
   - Visible but will fail if clicked (with appropriate error)

### Example Error Flow

```
User → Enters "casa" in search field → Clicks "Search"
  ↓
Flask `/search/advanced/data` endpoint is called
  ↓
Backend tries to connect to BlackLab → ConnectError
  ↓
Flask returns 200 OK with JSON:
{
  "draw": 1,
  "recordsTotal": 0,
  "recordsFiltered": 0,
  "data": [],
  "error": "upstream_unavailable",
  "message": "Search backend (BlackLab) is currently not reachable..."
}
  ↓
Frontend JS (initTable.js) checks for `error` field
  ↓
Displays MD3 Alert banner with user-friendly message
  ↓
DataTables shows empty table (normal "no results" state)
```

### Error Types in Frontend

The Advanced Search shows different error messages based on the error code:

| Error Code | UI Banner Title | Message |
|---|---|---|
| `upstream_unavailable` | Search Backend Unavailable | ☁️ BLS not reachable |
| `upstream_timeout` | Search Timeout | ⏰ BLS took too long |
| `upstream_error` | Backend Error | ⚠️ BLS returned an error |
| `invalid_cql` | CQL Syntax Error | ❌ User's CQL is invalid |
| `invalid_filter` | Invalid Filter | 🔍 Filter values invalid |

---

## 6. Configuration for Different Environments

### Development (Local)

```bash
# Set BLS to local Docker or JAR
export BLS_BASE_URL=http://localhost:8080/blacklab-server

# Or in passwords.env
BLS_BASE_URL=http://localhost:8080/blacklab-server
FLASK_ENV=development
```

### Development (Windows/WSL2)

If BlackLab is on Windows host but Flask is in WSL container:

```bash
# In WSL, point to Windows host
export BLS_BASE_URL=http://host.docker.internal:8080/blacklab-server

# Or in docker-compose for wsl2
services:
  web:
    environment:
      BLS_BASE_URL: "http://host.docker.internal:8080/blacklab-server"
```

### Production

```bash
# Use internal Docker network
BLS_BASE_URL=http://blacklab-service:8080/blacklab-server

# Or use DNS/external URL
BLS_BASE_URL=http://blacklab.example.com:8080/blacklab-server

# Set in systemd service or docker-compose.yml
```

---

## 7. Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `WinError 10061: Connection refused` | BlackLab not running or wrong port | Start BlackLab, verify port matches `BLS_BASE_URL` |
| `Connection refused on localhost:8081` | Default port conflicts with something else | Change port in BlackLab config or `BLS_BASE_URL` |
| `404 Not Found on /blacklab-server/` | BlackLab running but path is wrong | Verify BlackLab is exposing `/blacklab-server` (not `/blacklab`) |
| `Timeout (no response from BLS)` | BlackLab slow or indexing | Wait for index to finish, or increase timeouts in code |
| `Invalid CQL parameter accepted` | BlackLab version mismatch (patt vs cql) | Code auto-detects; check logs for which parameter was used |
| Search works but very slow | BLS returning large result sets | Implement pagination, reduce result limit, or optimize index |

---

## 8. Useful Commands

```bash
# View Flask logs
docker logs corapan-container --follow

# View BlackLab logs
docker logs corapan-blacklab-dev --follow

# Check health in loop (useful for debugging)
watch -n 1 'curl -s http://localhost:8000/health/bls | jq .ok'

# Rebuild and restart Docker services
docker-compose up -d --build --force-recreate

# Stop and remove all
docker-compose down

# Connect to BlackLab web UI (if available)
# http://localhost:8080/blacklab-server-gui/
```

---

## 9. References

- **BlackLab Documentation:** https://inl.github.io/BlackLab/
- **CQL Query Language:** https://inl.github.io/BlackLab/corpus-query-language.html
- **App Configuration:** `src/app/extensions/http_client.py`
- **Search Endpoints:** `src/app/search/advanced_api.py`
- **Frontend Handler:** `static/js/modules/advanced/initTable.js`
- **Health Check:** `src/app/routes/public.py` (`/health`, `/health/bls`)

---

## 10. Related Documentation

- [Advanced Search (UI/UX)](./advanced-search-ui-finalization.md)
- [Advanced Search (CQL)](./advanced-search.md)
- [Build BlackLab Index](./build-blacklab-index.md)
- [Production Deployment](../operations/production-deployment.md)
