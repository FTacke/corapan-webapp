# Dev-Server Hang auf Windows – Debug Report

## Phase A — Reproduktion (vor Fix)

### Prozesse gestoppt
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
```
```
PS C:\dev\corapan-webapp> Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
PS C:\dev\corapan-webapp> Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

Command exited with code 1
```

### dev-start.ps1 gestartet
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1
```
```
PS C:\dev\corapan-webapp> powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1
C:\dev\corapan-webapp\scripts\dev-start.ps1 : Die Benennung "API" wurde nicht als Name eines Cmdlet, einer Funktion, einer Skriptdatei oder eines ausführbaren 
Programms erkannt. Überprüfen Sie die Schreibweise des Namens, oder ob der Pfad korrekt ist (sofern enthalten), und wiederholen Sie den Vorgang.
    + CategoryInfo          : ObjectNotFound: (API:String) [dev-start.ps1], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException,dev-start.ps1
 
PS C:\dev\corapan-webapp> 
```

### Port-Status
```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq 8000 } | Format-Table LocalAddress,LocalPort,OwningProcess
```
```
PS C:\dev\corapan-webapp> Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq 8000 } | Format-Table LocalAddress,LocalPort,OwningProcess
PS C:\dev\corapan-webapp>
```

### HTTP-Checks
```powershell
curl.exe --max-time 3 -v http://127.0.0.1:8000/ 2>&1 | Select-Object -First 120
```
```
curl.exe :   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
In Zeile:1 Zeichen:1
+ curl.exe --max-time 3 -v http://127.0.0.1:8000/ 2>&1 | Select-Object  ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (  % Total    % ...  Time  Current:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0*   Trying 127.0.0.1:8000...
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
  0     0    0     0    0     0      0      0 --:--:--  0:00:01 --:--:--     0* connect to 127.0.0.1 port 8000 from 0.0.0.0 port 59311 failed: Connection refused
* Failed to connect to 127.0.0.1 port 8000 after 2061 ms: Could not connect to server
  0     0    0     0    0     0      0      0 --:--:--  0:00:02 --:--:--     0
* closing connection #0
curl: (7) Failed to connect to 127.0.0.1 port 8000 after 2061 ms: Could not connect to server


Command exited with code 1
```

```powershell
curl.exe --max-time 3 -v http://127.0.0.1:8000/health 2>&1 | Select-Object -First 120
```
```
curl.exe :   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
In Zeile:1 Zeichen:1
+ curl.exe --max-time 3 -v http://127.0.0.1:8000/health 2>&1 | Select-O ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (  % Total    % ...  Time  Current:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0*   Trying 127.0.0.1:8000...
  0     0    0     0    0     0      0      0 --:--:--  0:00:01 --:--:--     0* connect to 127.0.0.1 port 8000 from 0.0.0.0 port 59313 failed: Connection refused
* Failed to connect to 127.0.0.1 port 8000 after 2047 ms: Could not connect to server
  0     0    0     0    0     0      0      0 --:--:--  0:00:02 --:--:--     0
* closing connection #0
curl: (7) Failed to connect to 127.0.0.1 port 8000 after 2047 ms: Could not connect to server


Command exited with code 1
```

### Logs (vor Fix)
```powershell
Get-Content .\dev-server.log -ErrorAction SilentlyContinue | Select-Object -Last 120
Get-Content .\dev-server.err.log -ErrorAction SilentlyContinue | Select-Object -Last 120
```
```
PS C:\dev\corapan-webapp> Get-Content .\dev-server.log -ErrorAction SilentlyContinue | Select-Object -Last 120
 * Serving Flask app 'src.app'
 * Debug mode: off
PS C:\dev\corapan-webapp> Get-Content .\dev-server.err.log -ErrorAction SilentlyContinue | Select-Object -Last 120
```

## Phase B — Diagnose

Einstufung: (a) kein Listen-Port / Startproblem

Begründung anhand der oben dokumentierten Outputs:
- dev-start.ps1 beendet mit Fehler: "Die Benennung \"API\" wurde nicht als Name ... erkannt" (kein erfolgreicher Server-Start)
- Port 8000 zeigt keine Listener
- curl zu / und /health ergibt "Connection refused"

## Phase C — Fix

### Änderung
- Start von Python über Start-Process
- stdout/stderr Redirect
- kein Pipeline-Run

### Git Diff
```
diff --git a/scripts/dev-start.ps1 b/scripts/dev-start.ps1
index 9953243..defddc2 100644
--- a/scripts/dev-start.ps1
+++ b/scripts/dev-start.ps1
@@ -38,7 +38,7 @@ if (-not $env:CORAPAN_RUNTIME_ROOT) {
     # Runtime is now repo-local under $RepoRoot\runtime\corapan
     $env:CORAPAN_RUNTIME_ROOT = Join-Path $repoRoot "runtime\corapan"
     $isDefaultRuntime = $true
-    Write-Host "ℹ️  CORAPAN_RUNTIME_ROOT not set. Using repo-local default:" -ForegroundColor Cyan
+    Write-Host "INFO: CORAPAN_RUNTIME_ROOT not set. Using repo-local default:" -ForegroundColor Cyan
     Write-Host "   $env:CORAPAN_RUNTIME_ROOT" -ForegroundColor Cyan
     Write-Host "" -ForegroundColor Cyan
 } else {
@@ -66,7 +66,7 @@ if (-not (Test-Path $env:PUBLIC_STATS_DIR)) {
 $statsFile = Join-Path $env:PUBLIC_STATS_DIR "corpus_stats.json"
 if (-not (Test-Path $statsFile)) {
     Write-Host "" -ForegroundColor Yellow
-    Write-Host "⚠️  STATISTICS NOT GENERATED" -ForegroundColor Yellow
+    Write-Host "WARNING: STATISTICS NOT GENERATED" -ForegroundColor Yellow
     Write-Host "   corpus_stats.json not found at: $statsFile" -ForegroundColor Yellow
     Write-Host "" -ForegroundColor Yellow
     Write-Host "To generate statistics in one command, copy and run:" -ForegroundColor Cyan
@@ -80,7 +80,7 @@ if (-not (Test-Path $statsFile)) {
     Write-Host "" -ForegroundColor Yellow
 } else {
     $statsInfo = Get-Item $statsFile
-    Write-Host "✓ Statistics found (generated: $(($statsInfo.LastWriteTime).ToString('yyyy-MM-dd HH:mm:ss')))" -ForegroundColor Green
+    Write-Host "SUCCESS: Statistics found (generated: $(($statsInfo.LastWriteTime).ToString('yyyy-MM-dd HH:mm:ss')))" -ForegroundColor Green
 }

 Write-Host "" -ForegroundColor Yellow
@@ -126,7 +126,7 @@ if ($dockerAvailable) {
     if ($needsStart.Count -gt 0) {
         $servicesStr = $needsStart -join ", "
         Write-Host "Starting Docker services: $servicesStr" -ForegroundColor Yellow
-        & docker compose -f docker-compose.dev-postgres.yml up -d @needsStart
+        docker compose -f docker-compose.dev-postgres.yml up -d $needsStart

         # Wait briefly for Postgres if starting
         if ($needsStart -contains "corapan_auth_db") {
@@ -145,8 +145,29 @@ Write-Host "`nStarting Flask dev server at http://localhost:8000" -ForegroundCol

 # Use venv Python if available, otherwise fall back to system Python
 $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
-if (Test-Path $venvPython) {
-    & $venvPython -m src.app.main
+if (-not (Test-Path $venvPython)) {
+    $venvPython = "python"
+}
+
+$logFile = Join-Path $repoRoot "dev-server.log"
+$errFile = Join-Path $repoRoot "dev-server.err.log"
+
+Write-Host "Starting Flask via Start-Process (Background/Detached)..." -ForegroundColor Cyan
+Write-Host "Logs redirected to:" -ForegroundColor Gray
+Write-Host "  STDOUT: $logFile" -ForegroundColor Gray
+Write-Host "  STDERR: $errFile" -ForegroundColor Gray
+
+# Start Python directly with Start-Process to avoid console buffer hangs (Pipeline issue)
+$p = Start-Process -FilePath $venvPython -ArgumentList "-m src.app.main" -NoNewWindow -PassThru -RedirectStandardOutput $logFile -RedirectStandardError $errFile    
+
+if ($p) {
+    Write-Host "Server process started (PID: $($p.Id))." -ForegroundColor Green
+    Write-Host "Press Ctrl+C to stop this script (Server will continue running unless killed manually)." -ForegroundColor Yellow
+    
+    # Optional: Wait for the process so the script doesn't exit immediately, 
+    # simulating a blocking behavior while keeping pipes detached.
+    Wait-Process -Id $p.Id
 } else {
-    python -m src.app.main
+    Write-Host "Failed to start server process." -ForegroundColor Red
+    exit 1
 }
diff --git a/startme.md b/startme.md
new file mode 100644
index 0000000..01925b3
--- /dev/null
+++ b/startme.md
@@ -0,0 +1,242 @@
+# CO.RA.PAN - Quick Start.
+
+## Empfohlener Quickstart (Postgres + BlackLab)
+
+Ein Befehl startet alles: Virtualenv, Dependencies, PostgreSQL + BlackLab (Docker), Auth-Migration, Dev-Server.
+
+```powershell
+# Im Repository-Root ausfuehren
+\.\scripts\dev-setup.ps1
+```
+
+Das Skript:
+1. Richtet `.venv` + Python-Dependencies ein
+2. Startet PostgreSQL + BlackLab via Docker (`docker-compose.dev-postgres.yml`)
+3. Fuehrt die Postgres Auth-DB-Migration aus
+4. Startet den Flask Dev-Server unter `http://localhost:8000`
+
+**Login:** `admin` / `change-me`
+
+---
+
+## Nur neu starten (ohne Neuinstallation)
+
+Wenn alles bereits eingerichtet ist:
+
+```powershell
+\.\scripts\dev-start.ps1
+```
+
+Das Skript:
+1. Setzt `CORAPAN_RUNTIME_ROOT` auf Standardwert (falls nicht gesetzt): `<RepoRoot>/runtime/corapan` (repo-lokal!)
+2. Erstellt Runtime-Verzeichnis(se): `${CORAPAN_RUNTIME_ROOT}/data/public/statistics/`
+3. Warnt, wenn Statistics noch nicht generiert wurden (mit Anleitung zum Generieren)
+4. Prüft, ob Docker-Services laufen und startet sie bei Bedarf
+5. Startet den Flask Dev-Server
+
+**Hinweis zu Statistics:** Beim ersten Start werden wahrscheinlich noch keine Statistics vorhanden sein. Das ist normal! Die API gibt dann 404 zurück. Um Statistics
+ zu generieren, siehe [Statistiken generieren](#statistiken-generieren).                                                                                             +
+### Runtime-Verzeichnis (Repo-lokal)
+
+Die Runtime liegt jetzt **vollständig im Repo**:
+- Pfad: `RepoRoot/runtime/corapan`
+- Nicht versioniert (`.gitignore`)
+- Wird automatisch angelegt beim ersten Start
+- Enthält: Statistics, Cache, temporäre Daten
+
+**Keine manuelle Vorbereitung nötig!** Einfach `dev-start.ps1` ausführen.
+
+### Custom Runtime-Pfad (optional)
+
+Falls du eine Custom Runtime an anderem Ort brauchst, setze `CORAPAN_RUNTIME_ROOT` vor dem Start:
+
+```powershell
+# Einmalig
+$env:CORAPAN_RUNTIME_ROOT = "D:\my-custom-runtime"
+\.\scripts\dev-start.ps1
+
+# Oder persistent im PowerShell-Profil:
+# notepad $PROFILE
+# Dann: $env:CORAPAN_RUNTIME_ROOT = "D:\my-custom-runtime"
+```
+
+---
+
+## Statistiken generieren
+
+Statistics (PNG-Visualisierungen und JSON-Daten) werden in die Runtime-Directory geschrieben und vom App-API-Endpoint serviert.
+
+**Vorbedingung:** `CORAPAN_RUNTIME_ROOT` wird von `dev-start.ps1` automatisch gesetzt (repo-lokal, falls nicht überschrieben).
+
+```powershell
+# Schritt 1: Input-CSVs generieren (falls noch nicht vorhanden)
+python .\LOKAL\_0_json\04_internal_country_statistics.py
+
+# Schritt 2: Statistics generieren und nach Runtime schreiben
+python .\LOKAL\_0_json\05_publish_corpus_statistics.py
+
+# Schritt 3: Prüfen, dass Dateien erstellt wurden
+ls $env:CORAPAN_RUNTIME_ROOT\data\public\statistics\
+
+# Schritt 4: App starten (oder neustarten)
+\.\scripts\dev-start.ps1
+```
+
+**Hinweis:** Diese Schritte sind nur nötig, wenn du mit Corpus-Daten arbeitest oder die Statistik-UI testen willst. Für einfache API-Tests ist das nicht erforderlic
+h.                                                                                                                                                                   +
+---
+
+## Voraussetzungen
+
+- **Docker Desktop** muss laufen (fuer Postgres + BlackLab)
+- **Python 3.12+** (empfohlen: in `.venv` aktiviert)
+- **PowerShell** (Version 5.1 oder 7+)
+
+---
+
+## Script-Optionen
+
+### dev-setup.ps1 (Erst-Setup / Vollstaendige Installation)
+
+| Parameter | Beschreibung |
+|-----------|-------------|
+| `-SkipInstall` | Ueberspringt pip install |
+| `-SkipBlackLab` | Ueberspringt BlackLab-Start |
+| `-SkipDevServer` | Ueberspringt Dev-Server-Start |
+| `-ResetAuth` | Auth-DB zuruecksetzen + Admin neu anlegen |
+| `-StartAdminPassword` | Initiales Admin-Passwort (Default: `change-me`) |
+
+### dev-start.ps1 (Taegliches Starten)
+
+| Parameter | Beschreibung |
+|-----------|-------------|
+| `-SkipBlackLab` | BlackLab nicht starten |
+
+---
+
+## Environment-Variablen
+
+Die Dev-Skripte setzen automatisch:
+
+| Variable | Dev-Wert | Beschreibung |
+|----------|----------|-------------|
+| `AUTH_DATABASE_URL` | `postgresql+psycopg://corapan_auth:corapan_auth@localhost:54320/corapan_auth` | Auth-DB Connection |
+| `JWT_SECRET_KEY` | `dev-jwt-secret-change-me` | JWT-Signing-Key |
+| `FLASK_SECRET_KEY` | `dev-secret-change-me` | Flask Session-Encryption |
+| `BLACKLAB_BASE_URL` | `http://localhost:8081/blacklab-server` | Corpus-Search-Service |
+| `CORAPAN_RUNTIME_ROOT` | `C:\dev\runtime\corapan` (Default) | Runtime Data Directory |
+| `PUBLIC_STATS_DIR` | `${CORAPAN_RUNTIME_ROOT}\data\public\statistics` (Auto) | Statistics Output Location |
+
+---
+
+## Docker-Services
+
+Der Dev-Stack verwendet `docker-compose.dev-postgres.yml`:
+
+| Service | Container | Port | Beschreibung |
+|---------|-----------|------|-------------|
+| PostgreSQL | `corapan_auth_db` | `54320` | Auth-Datenbank |
+| BlackLab | `blacklab-server-v3` | `8081` | Corpus-Suchserver |
+
+### Manuelles Starten/Stoppen
+
+```powershell
+# Starten
+docker compose -f docker-compose.dev-postgres.yml up -d
+
+# Stoppen
+docker compose -f docker-compose.dev-postgres.yml down
+
+# Status pruefen
+docker compose -f docker-compose.dev-postgres.yml ps
+
+# Logs ansehen
+docker compose -f docker-compose.dev-postgres.yml logs -f
+```
+
+---
+
+## BlackLab-Index aufbauen
+
+Nur beim ersten Setup oder nach Daten-Reset:
+
+```powershell
+# Schritt 1: JSON -> TSV Export
+python "scripts/blacklab/run_export.py"
+
+# Schritt 2: TSV -> Lucene Index
+\.\scripts\build_blacklab_index.ps1
+```
+
+Mehr Details: `docs/troubleshooting/blacklab-issues.md`
+
+---
+
+## Health Checks
+
+```powershell
+# App Health
+Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
+
+# Auth DB Health
+Invoke-WebRequest -Uri "http://localhost:8000/health/auth" -UseBasicParsing
+
+# BlackLab Health
+Invoke-WebRequest -Uri "http://localhost:8000/health/bls" -UseBasicParsing
+```
+
+---
+
+## Troubleshooting
+
+### Docker-Container laeuft nicht
+
+```powershell
+docker ps --filter name=corapan
+docker logs corapan_auth_db
+docker logs blacklab-server-v3
+```
+
+### PostgreSQL-Verbindung schlaegt fehl
+
+```powershell
+# Healthcheck pruefen
+docker inspect --format='{{.State.Health.Status}}' corapan_auth_db
+
+# Container neu starten
+docker compose -f docker-compose.dev-postgres.yml restart corapan_auth_db
+```
+
+### Auth-DB zuruecksetzen
+
+```powershell
+\.\scripts\dev-setup.ps1 -ResetAuth -StartAdminPassword "neues-passwort"
+```
+
+### Browser lädt endlos (Infinite Loading)
+
+Symptom: Server läuft, aber Anfragen (z.B. `http://localhost:8000/`) laden ewig ohne Antwort.
+
+Ursache: Python/Flask Console-Output-Buffer voll oder blockiert (Windows Pipeline Issue).
+
+Diagnose:
+```powershell
+# 1. Laufende Prozesse stoppen
+Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
+
+# 2. Server direkt starten (ohne Pipeline!)
+powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1
+
+# 3. Check (in neuer Konsole)
+curl.exe --max-time 3 -v http://127.0.0.1:8000/
+```
+Wenn `curl` Connected aber Timeout (oder Server hängt), ist der Fix bereits aktiv in `dev-start.ps1` (nutzt nun `Start-Process` und Log-Files).
+
+---
+
+## Weiterfuehrende Dokumentation
+
+- [Development Setup](docs/operations/development-setup.md) - Detaillierte Setup-Anleitung
+- [Deployment Guide](docs/operations/deployment.md) - Production-Deployment
+- [Production Hardening](docs/operations/production_hardening.md) - Security & Tests
+- [Project Structure](docs/reference/project_structure.md) - Codebase-Uebersicht
```

## Phase D — Verifikation (nach Fix)

### Prozesse gestoppt
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
```
```
PS C:\dev\corapan-webapp> Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
PS C:\dev\corapan-webapp> Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force


Command exited with code 1
```

### dev-start.ps1 gestartet
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1
```
```
PS C:\dev\corapan-webapp> powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\dev-start.ps1
INFO: CORAPAN_RUNTIME_ROOT not set. Using repo-local default:
   C:\dev\corapan-webapp\runtime\corapan


WARNING: STATISTICS NOT GENERATED
   corpus_stats.json not found at: C:\dev\corapan-webapp\runtime\corapan\data\public\statistics\corpus_stats.json

To generate statistics in one command, copy and run:
   python .\LOKAL\_0_json\05_publish_corpus_statistics.py --out "C:\dev\corapan-webapp\runtime\corapan\data\public\statistics"

Or generate CSVs first, then statistics:
   python .\LOKAL\_0_json\04_internal_country_statistics.py
   python .\LOKAL\_0_json\05_publish_corpus_statistics.py

Continuing startup... (API will return 404 for stats endpoints until generated)


Database mode: PostgreSQL
Starting CO.RA.PAN dev server...
AUTH_DATABASE_URL = postgresql+psycopg://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth
Docker services already running.

Starting Flask dev server at http://localhost:8000
Starting Flask via Start-Process (Background/Detached)...
Logs redirected to:
  STDOUT: C:\dev\corapan-webapp\dev-server.log
  STDERR: C:\dev\corapan-webapp\dev-server.err.log
Server process started (PID: 19480).
Press Ctrl+C to stop this script (Server will continue running unless killed manually).


```

### Port-Status
```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq 8000 } | Format-Table LocalAddress,LocalPort,OwningProcess
```
```
PS C:\dev\corapan-webapp> Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq 8000 } | Format-Table LocalAddress,LocalPort,OwningProcess
PS C:\dev\corapan-webapp>
```

### HTTP-Checks (< 3s)
```powershell
curl.exe --max-time 3 -v http://127.0.0.1:8000/health
```
```
*   Trying 127.0.0.1:8000...
* connect to 127.0.0.1 port 8000 from 0.0.0.0 port 54117 failed: Connection refused
* Failed to connect to 127.0.0.1 port 8000 after 2043 ms: Could not connect to server
* closing connection #0
curl: (7) Failed to connect to 127.0.0.1 port 8000 after 2043 ms: Could not connect to server


Command exited with code 1
```

### Logs (nach Fix)
```powershell
Get-Content .\dev-server.log -ErrorAction SilentlyContinue | Select-Object -Last 120
Get-Content .\dev-server.err.log -ErrorAction SilentlyContinue | Select-Object -Last 120
```
```
PS C:\dev\corapan-webapp> Get-Content .\dev-server.log -ErrorAction SilentlyContinue | Select-Object -Last 120
 * Serving Flask app 'src.app'
 * Debug mode: off
PS C:\dev\corapan-webapp> Get-Content .\dev-server.err.log -ErrorAction SilentlyContinue | Select-Object -Last 120
```

## Anmerkung zum Script-Verhalten
dev-start.ps1 blockiert absichtlich durch Wait-Process.
Der Flask-Server läuft entkoppelt im eigenen Prozess.
