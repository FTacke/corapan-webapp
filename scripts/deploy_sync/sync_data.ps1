# =============================================================================
# CO.RA.PAN Data Sync: Dev -> Prod
# =============================================================================
#
# Zweck:
#   Synchronisiert die CO.RA.PAN-Daten vom Dev-Rechner auf den Prod-Server.
#   Der Sync erfolgt als Delta-Sync: nur neue oder geaenderte Dateien werden
#   uebertragen, geaenderte Dateien ueberschreiben die Version auf dem Server.
#
# -----------------------------------------------------------------------------
# SYNCHRONISIERTE VERZEICHNISSE (unter data/):
# -----------------------------------------------------------------------------
#
#   Folgende Verzeichnisse werden als Ganzes synchronisiert:
#   - db_public       -> Oeffentliche Datenbank-Exports
#   - metadata        -> Metadaten zu Korpus-Dateien
#   - exports         -> Generierte Exports
#   - blacklab_export -> BlackLab-Export-Dateien
#
# -----------------------------------------------------------------------------
# STATS-DATENBANKEN (aus data/db/):
# -----------------------------------------------------------------------------
#
#   Zusaetzlich werden folgende Stats-DBs einzeln synchronisiert:
#   - stats_files.db    -> Atlas-Statistiken pro Datei
#   - stats_country.db  -> Atlas-Statistiken pro Land
#
#   ERKLAERUNG: Das Verzeichnis data/db wird als Ganzes NICHT synchronisiert,
#   weil es die Auth- und Transkriptions-Datenbanken enthaelt, die auf dem
#   Prod-Server unabhaengig verwaltet werden. Die Stats-DBs sind jedoch
#   logisch Teil des regulaeren Data-Syncs - sie werden nur technisch in
#   einem separaten Abschnitt behandelt, um die Ausschlussregel fuer data/db
#   zu umgehen. Fuer den Anwender verhalten sie sich wie jedes andere
#   synchronisierte Element: Delta-Sync bei Aenderungen.
#
# -----------------------------------------------------------------------------
# NICHT SYNCHRONISIERT (bewusst ausgeschlossen):
# -----------------------------------------------------------------------------
#
#   - blacklab_index         -> wird auf dem Server neu gebaut
#   - blacklab_index.backup  -> nur lokal relevant
#   - stats_temp             -> temporaere Verarbeitungsdateien
#   - db/auth.db             -> Prod-Auth-DB wird separat verwaltet
#   - db/transcription.db    -> Prod-Transkriptions-DB ist unabhaengig
#   - db/auth_e2e.db         -> nur fuer lokale E2E-Tests
#
# -----------------------------------------------------------------------------
# PROTECTED PRODUCTION STATE (NEVER synced by default):
# -----------------------------------------------------------------------------
#
#   - counters/              -> Runtime state (page views, downloads, etc.)
#   - db/auth.db             -> Production authentication database
#
#   These contain production runtime state and must NEVER be overwritten
#   by a data deploy. To sync them (DANGEROUS), you must explicitly use:
#     -IncludeCounters and/or -IncludeAuthDb
#     AND -IUnderstandThisWillOverwriteProductionState
#
# -----------------------------------------------------------------------------
# FORCE-MODUS (-Force):
# -----------------------------------------------------------------------------
#
#   Mit dem Parameter -Force werden alle Dateien uebertragen, unabhaengig
#   vom Manifest-Zustand. Nuetzlich nach Manifest-Korruption oder zur
#   vollstaendigen Resynchronisation.
#   
#   Beispiel: .\sync_data.ps1 -Force
#
# -----------------------------------------------------------------------------
# VERWENDUNG:
# -----------------------------------------------------------------------------
#
#   cd C:\dev\corapan-webapp
#   .\scripts\deploy_sync\sync_data.ps1           # Normal (Delta-Sync)
#   .\scripts\deploy_sync\sync_data.ps1 -Force    # Force (alle Dateien)
#
# DRY-RUN:
#   Kein Dry-Run-Modus (echter Sync).
#
# Siehe auch:
#   - update_data_media.ps1  -> Interaktiver Maintenance-Runner
#   - sync_media.ps1         -> Media-Verzeichnisse synchronisieren
#
# =============================================================================

param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot,
    
    [switch]$Force,
    
    # PRODUCTION STATE PROTECTION
    # These switches allow syncing of runtime state (normally excluded for safety)
    # REQUIRES -IUnderstandThisWillOverwriteProductionState to be set as well
    [switch]$IncludeCounters,
    
    [switch]$IncludeAuthDb,
    
    [switch]$IUnderstandThisWillOverwriteProductionState
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -----------------------------------------------------------------------------
# Konfiguration
# -----------------------------------------------------------------------------
$runtimeRoot = $env:CORAPAN_RUNTIME_ROOT
if (-not $runtimeRoot) {
    Write-Host "FEHLER: CORAPAN_RUNTIME_ROOT ist nicht gesetzt. Abbruch." -ForegroundColor Red
    exit 1
}

$LOCAL_BASE_PATH  = Join-Path $runtimeRoot "data"
$REMOTE_BASE_PATH = "/srv/webapps/corapan/data"

# Zu synchronisierende Verzeichnisse
# WICHTIG: blacklab_index, blacklab_index.backup, stats_temp, db sind bewusst NICHT enthalten!
# WICHTIG: counters ist NICHT enthalten (Production State Protection)
$DATA_DIRECTORIES = @(
    "db_public",
    "metadata",
    "exports",
    "blacklab_export"
)

# Selektiv zu synchronisierende DB-Dateien aus data/db
# Diese werden fuer die Atlas-/Stats-Funktionen auf dem Server benoetigt
$STATS_DB_FILES = @(
    "stats_files.db",
    "stats_country.db"
)

# -----------------------------------------------------------------------------
# PRODUCTION STATE PROTECTION: Hard Blocklist
# -----------------------------------------------------------------------------

# These MUST NEVER be synced (production runtime state)
$HARD_BLOCKED_PATHS = @(
    "counters",     # Runtime state: page views, downloads, etc.
    "db"            # Contains auth.db, transcription.db (prod databases)
)

# Allowed individual files from data/db/ (override to main db/ exclusion)
$ALLOWED_STATS_DBS = @(
    "stats_files.db",
    "stats_country.db"
)

# Additional unwanted paths
$EXCLUDED_PATHS = @(
    "blacklab_index",
    "blacklab_index.backup",
    "stats_temp"
)

# -----------------------------------------------------------------------------
# SAFETY CHECKS: Validate production state protection
# -----------------------------------------------------------------------------

# FUNCTION: Legacy production state test (no longer used - guardrails are inline now)
# Kept for historical reference but not called
function Test-ProductionStateProtection {
    param(
        [string[]]$Directories,
        [string[]]$DbFiles,
        [bool]$IncludeCounters,
        [bool]$IncludeAuthDb,
        [bool]$AcknowledgeOverwrite
    )
    
    # DEPRECATED: Hard guardrails are now inline in main program
    # This function is kept for backward compatibility only
    # It is never called
}

# =============================================================================
# FUNCTION: Sync-StatisticsFiles
# =============================================================================
#
# Synchronizes statistics files (corpus_stats.json, viz_*.png) to production.
# Remote location: /srv/webapps/corapan/data/public/statistics
#
# HARDENED SECURITY:
# - Hard guards prevent syncing from repo root or parent directories
# - Allowlist-based: only corpus_stats.json and viz_*.png are transferred
# - No directory structures, no recursive syncs
# - Post-upload verification ensures no unwanted files are present
#
# Features:
# - Validates local statistics files exist before syncing
# - Syncs only specific files via explicit file list (overwrite-only, no delete)
# - Prevents accidental repo root deployment (guards against misconfiguration)
# - Handles missing local stats gracefully with warning (not error)
# - Sets remote ownership after upload
# - Verifies remote content after upload
#
# Behavior:
# - If PUBLIC_STATS_DIR env var is set, use that (for backward compatibility)
# - Else use CORAPAN_RUNTIME_ROOT/data/public/statistics
# - Else SKIP with warning
#
function Sync-StatisticsFiles {
    param(
        [string]$LocalStatsDir,
        [string]$RepoRoot,
        [string]$RemoteRuntimeRoot = "/srv/webapps/corapan",
        [switch]$DryRun = $false
    )
    
    Write-Host ""
    Write-Host "[Statistics Files]" -ForegroundColor Cyan
    Write-Host ""
    
    # =========================================================================
    # PHASE 1: Determine local statistics directory
    # =========================================================================
    
    if (-not $LocalStatsDir) {
        if ($env:PUBLIC_STATS_DIR) {
            $LocalStatsDir = $env:PUBLIC_STATS_DIR
            Write-Host "Using PUBLIC_STATS_DIR (env var): $LocalStatsDir" -ForegroundColor DarkGray
        }
        elseif ($env:CORAPAN_RUNTIME_ROOT) {
            $LocalStatsDir = Join-Path $env:CORAPAN_RUNTIME_ROOT "data\public\statistics"
            Write-Host "Using CORAPAN_RUNTIME_ROOT/data/public/statistics: $LocalStatsDir" -ForegroundColor DarkGray
        }
        else {
            Write-Host "SKIP: No statistics directory specified" -ForegroundColor Yellow
            Write-Host "  Reason: CORAPAN_RUNTIME_ROOT not set" -ForegroundColor DarkGray
            Write-Host ""
            return $true
        }
    }
    
    # =========================================================================
    # PHASE 2: HARD GUARDS - Prevent repo root / parent directory sync
    # =========================================================================
    
    # Resolve to absolute paths
    if (-not (Test-Path $LocalStatsDir)) {
        Write-Host "SKIP: Statistics directory does not exist" -ForegroundColor Yellow
        Write-Host "  Path: $LocalStatsDir" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "  To generate statistics:" -ForegroundColor DarkGray
        Write-Host "    python .\LOKAL\_0_json\05_publish_corpus_statistics.py" -ForegroundColor DarkGray
        Write-Host ""
        return $true
    }
    
    try {
        $LocalStatsDirResolved = (Resolve-Path -LiteralPath $LocalStatsDir -ErrorAction Stop).Path
    }
    catch {
        Write-Host "ERROR: Cannot resolve statistics directory path: $LocalStatsDir" -ForegroundColor Red
        Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    # Guard 1: Prevent syncing if LocalStatsDir looks like repo root
    $repoIndicators = @('.git', 'src', 'package.json', 'Dockerfile', 'templates', 'pyproject.toml', '.venv')
    $suspiciousItems = @()
    
    foreach ($indicator in $repoIndicators) {
        $testPath = Join-Path $LocalStatsDirResolved $indicator
        if (Test-Path $testPath) {
            $suspiciousItems += $indicator
        }
    }
    
    if ($suspiciousItems.Count -gt 0) {
        Write-Host "REFUSED: Refusing to deploy statistics from non-statistics directory" -ForegroundColor Red
        Write-Host "  Path: $LocalStatsDirResolved" -ForegroundColor Red
        Write-Host "  Reason: Found repo-like items: $($suspiciousItems -join ', ')" -ForegroundColor Red
        Write-Host ""
        Write-Host "  This guard prevents accidental repo sync. Ensure your stats directory" -ForegroundColor Yellow
        Write-Host "  contains ONLY: corpus_stats.json and viz_*.png files." -ForegroundColor Yellow
        Write-Host ""
        return $false
    }
    
    # =========================================================================
    # PHASE 3: Validate local statistics files (allowlist)
    # =========================================================================
    
    if (-not (Test-Path $LocalStatsDir)) {
        Write-Host "SKIP: Statistics directory does not exist" -ForegroundColor Yellow
        Write-Host "  Path: $LocalStatsDir" -ForegroundColor DarkGray
        Write-Host ""
        return $true
    }
    
    # Build allowlist: exactly 1 corpus_stats.json + all viz_*.png files
    $corpusStatsJson = Join-Path $LocalStatsDir "corpus_stats.json"
    $vizFiles = @(Get-ChildItem -Path $LocalStatsDir -Filter "viz_*.png" -File -ErrorAction SilentlyContinue)
    
    if (-not (Test-Path $corpusStatsJson)) {
        Write-Host "SKIP: corpus_stats.json not found" -ForegroundColor Yellow
        Write-Host "  Expected: $corpusStatsJson" -ForegroundColor DarkGray
        Write-Host ""
        return $true
    }
    
    if ($vizFiles.Count -eq 0) {
        Write-Host "SKIP: No viz_*.png files found" -ForegroundColor Yellow
        Write-Host "  Expected: $LocalStatsDir\\viz_*.png" -ForegroundColor DarkGray
        Write-Host ""
        return $true
    }
    
    # Count total files to be uploaded
    $fileCount = 1 + $vizFiles.Count
    
    Write-Host "Local statistics validated:" -ForegroundColor Green
    Write-Host "  - corpus_stats.json: OK" -ForegroundColor DarkGray
    Write-Host "  - viz_*.png files: $($vizFiles.Count) images" -ForegroundColor DarkGray
    Write-Host "  - Total files to upload: $fileCount" -ForegroundColor DarkGray
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "[DRY RUN] Would upload:" -ForegroundColor Cyan
        Write-Host "  - corpus_stats.json" -ForegroundColor DarkGray
        foreach ($viz in $vizFiles) {
            Write-Host "  - $($viz.Name)" -ForegroundColor DarkGray
        }
        Write-Host ""
        return $true
    }
    
    # =========================================================================
    # PHASE 4: Prepare remote target
    # =========================================================================
    
    $RemoteStatsDir = "$RemoteRuntimeRoot/data/public/statistics"
    Write-Host "Remote target: $RemoteStatsDir" -ForegroundColor DarkGray
    Write-Host ""
    
    # =========================================================================
    # PHASE 5: Upload via scp (per-file allowlist - most robust)
    # =========================================================================
    
    Write-Host "Uploading statistics files..." -ForegroundColor Cyan
    
    try {
        # Create remote directory
        Write-Host "  Creating remote directory..." -ForegroundColor DarkGray
        Invoke-SSHCommand -Command "mkdir -p '$RemoteStatsDir'" | Out-Null
        Write-Host "  Remote directory ready." -ForegroundColor DarkGray
        Write-Host ""
        
        # Get SSH config
        $server = "$($script:SyncConfig.ServerUser)@$($script:SyncConfig.ServerHost)"
        $sshKeyCygwin = Convert-ToRsyncPath $script:SyncConfig.SSHKeyPath -PreserveShortName
        
        # Upload corpus_stats.json
        Write-Host "  Uploading corpus_stats.json..." -ForegroundColor DarkGray
        $corpusJsonRsyncPath = Convert-ToRsyncPath $corpusStatsJson
        $rsyncArgs = @(
            "-avz",
            "-e", "ssh -i '$sshKeyCygwin' -o StrictHostKeyChecking=no -o ServerAliveInterval=60",
            "$corpusJsonRsyncPath",
            "${server}:$RemoteStatsDir/"
        )
        & rsync @rsyncArgs 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "rsync failed for corpus_stats.json (exit code $LASTEXITCODE)"
        }
        Write-Host "  corpus_stats.json: OK" -ForegroundColor Green
        
        # Upload each viz_*.png file
        Write-Host "  Uploading $($vizFiles.Count) visualization files..." -ForegroundColor DarkGray
        foreach ($viz in $vizFiles) {
            $vizRsyncPath = Convert-ToRsyncPath $viz.FullName
            $rsyncArgs = @(
                "-avz",
                "-e", "ssh -i '$sshKeyCygwin' -o StrictHostKeyChecking=no -o ServerAliveInterval=60",
                "$vizRsyncPath",
                "${server}:$RemoteStatsDir/"
            )
            & rsync @rsyncArgs 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "rsync failed for $($viz.Name) (exit code $LASTEXITCODE)"
            }
        }
        Write-Host "  All visualization files: OK" -ForegroundColor Green
        Write-Host ""
        
        # =====================================================================
        # PHASE 6: Post-upload verification (CRITICAL)
        # =====================================================================
        
        Write-Host "  Verifying uploaded content..." -ForegroundColor DarkGray
        
        # Check that remote directory contains ONLY expected files
        # Note: Use explicit bash -lc to ensure stdout is captured as string
        $remoteCheckCmd = "bash -lc 'ls -1 ""$RemoteStatsDir"" | grep -vE ""^(corpus_stats\.json|viz_.*\.png)$"" || true'"
        $unexpectedFilesRaw = Invoke-SSHCommand -Command $remoteCheckCmd
        
        # Robustly normalize output (Invoke-SSHCommand may return bool, array, or string)
        $unexpectedFiles = ""
        if ($null -eq $unexpectedFilesRaw) {
            $unexpectedFiles = ""
        }
        elseif ($unexpectedFilesRaw -is [bool]) {
            # If boolean, treat true as "has content", false as "empty"
            $unexpectedFiles = if ($unexpectedFilesRaw) { "true" } else { "" }
        }
        elseif ($unexpectedFilesRaw -is [System.Object[]] -and $unexpectedFilesRaw.Count -gt 1) {
            # If array, join with newlines
            $unexpectedFiles = $unexpectedFilesRaw -join "`n"
        }
        else {
            # Otherwise convert to string
            $unexpectedFiles = [string]$unexpectedFilesRaw
        }
        $unexpectedFiles = $unexpectedFiles.Trim()
        
        if ($unexpectedFiles) {
            Write-Host "  VERIFICATION FAILED: Unexpected files found on remote:" -ForegroundColor Red
            Write-Host "$unexpectedFiles" -ForegroundColor Red
            Write-Host ""
            return $false
        }
        
        # Count files on remote
        $remoteCountCmd = "bash -lc 'ls -1 ""$RemoteStatsDir"" | wc -l'"
        $remoteCountRaw = Invoke-SSHCommand -Command $remoteCountCmd
        
        # Robustly normalize count output
        $remoteCountStr = ""
        if ($null -eq $remoteCountRaw) {
            $remoteCountStr = "0"
        }
        elseif ($remoteCountRaw -is [bool]) {
            $remoteCountStr = if ($remoteCountRaw) { "1" } else { "0" }
        }
        else {
            $remoteCountStr = [string]$remoteCountRaw
        }
        $remoteCountStr = $remoteCountStr.Trim()
        $remoteCountNum = [int]$remoteCountStr
        
        if ($remoteCountNum -ne $fileCount) {
            Write-Host "  WARNING: Remote file count mismatch (expected $fileCount, found $remoteCountNum)" -ForegroundColor Yellow
            Write-Host "  This may be OK if remote directory had pre-existing files." -ForegroundColor DarkGray
        }
        
        Write-Host "  Remote verification: OK" -ForegroundColor Green
        Write-Host ""
        
        # =====================================================================
        # PHASE 7: Set ownership
        # =====================================================================
        
        try {
            Write-Host "  Setting ownership..." -ForegroundColor DarkGray
            Set-RemoteOwnership -RemotePath "$RemoteRuntimeRoot/data/public" | Out-Null
            Write-Host "  Ownership: OK" -ForegroundColor Green
        }
        catch {
            Write-Host "  WARNING: Could not set ownership (non-critical)" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Statistics files synced successfully" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "  ERROR: Statistics upload failed" -ForegroundColor Red
        Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

# ---
# -----------------------------------------------------------------------------
# Core-Bibliothek laden
# -----------------------------------------------------------------------------

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$coreScript = Join-Path $scriptDir "sync_core.ps1"

if (-not (Test-Path $coreScript)) {
    Write-Host "FEHLER: sync_core.ps1 nicht gefunden: $coreScript" -ForegroundColor Red
    exit 1
}

. $coreScript

# -----------------------------------------------------------------------------
# Hauptprogramm
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " CO.RA.PAN Data Sync: Dev -> Prod" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle:  $LOCAL_BASE_PATH" -ForegroundColor DarkGray
Write-Host "Ziel:    $REMOTE_BASE_PATH" -ForegroundColor DarkGray
Write-Host "Datum:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray
if ($Force) {
    Write-Host "Modus:   FORCE (alle Dateien uebertragen)" -ForegroundColor Yellow
} else {
    Write-Host "Modus:   Delta-Sync (nur Aenderungen)" -ForegroundColor DarkGray
}
Write-Host ""

# Pruefen ob lokales Verzeichnis existiert
if (-not (Test-Path $LOCAL_BASE_PATH)) {
    Write-Host "FEHLER: Lokales Datenverzeichnis nicht gefunden: $LOCAL_BASE_PATH" -ForegroundColor Red
    exit 1
}

# Display protection status
Write-Host ""
Write-Host "Protected Production State:" -ForegroundColor Yellow
Write-Host "  - data/counters (runtime state) - NEVER synced" -ForegroundColor Yellow
Write-Host "  - data/db (auth, transcription) - NEVER synced" -ForegroundColor Yellow
Write-Host "  - Stats DBs only (stats_files.db, stats_country.db) - synced if found" -ForegroundColor DarkGray
Write-Host ""

# GUARDRAIL: Hard block against production state overwrite
if ($IncludeCounters) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  PRODUCTION STATE PROTECTION" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "ERROR: counters/ sync is PERMANENTLY DISABLED." -ForegroundColor Red
    Write-Host ""
    Write-Host "This directory contains production runtime state" -ForegroundColor White
    Write-Host "(page views, downloads, etc.) and must NEVER be" -ForegroundColor White
    Write-Host "overwritten by a data deploy." -ForegroundColor White
    Write-Host ""
    Write-Host "If you have a critical need to restore production" -ForegroundColor Yellow
    Write-Host "state, use manual SSH restore procedures instead." -ForegroundColor Yellow
    Write-Host ""
    exit 3
}

# GUARDRAIL: Hard block against auth DB overwrite
if ($IncludeAuthDb) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  PRODUCTION STATE PROTECTION" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "ERROR: db/auth.db sync is PERMANENTLY DISABLED." -ForegroundColor Red
    Write-Host ""
    Write-Host "This contains production authentication database" -ForegroundColor White
    Write-Host "and must NEVER be overwritten by a data deploy." -ForegroundColor White
    Write-Host ""
    Write-Host "If you have a critical need to restore production" -ForegroundColor Yellow
    Write-Host "auth state, use manual SSH restore procedures instead." -ForegroundColor Yellow
    Write-Host ""
    exit 3
}

# Verify DATA_DIRECTORIES do not contain hard-blocked paths
$invalid = @()
foreach ($dir in $DATA_DIRECTORIES) {
    if ($HARD_BLOCKED_PATHS -contains $dir) {
        $invalid += $dir
    }
}

if ($invalid.Count -gt 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  INTERNAL ERROR" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Refusing to sync protected production state paths:" -ForegroundColor Red
    foreach ($dir in $invalid) {
        Write-Host "  - data/$dir" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "This is a configuration error (report to maintainer)." -ForegroundColor White
    Write-Host ""
    exit 3
}

# Verify STATS_DB_FILES only contains allowed DBs
$invalidDBs = @()
foreach ($dbFile in $STATS_DB_FILES) {
    if (-not ($ALLOWED_STATS_DBS -contains $dbFile)) {
        $invalidDBs += $dbFile
    }
}

if ($invalidDBs.Count -gt 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  INTERNAL ERROR" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Refusing to sync non-allowed database files:" -ForegroundColor Red
    foreach ($dbFile in $invalidDBs) {
        Write-Host "  - data/db/$dbFile" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Allowed DB files:" -ForegroundColor White
    foreach ($allowed in $ALLOWED_STATS_DBS) {
        Write-Host "  - data/db/$allowed" -ForegroundColor DarkGray
    }
    Write-Host ""
    exit 3
}

# Verify no data directory is excluded inadvertently
$excluded = @()
foreach ($dir in $DATA_DIRECTORIES) {
    if ($EXCLUDED_PATHS -contains $dir) {
        $excluded += $dir
    }
}

if ($excluded.Count -gt 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  INTERNAL ERROR" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Configuration conflict - attempting to sync excluded paths:" -ForegroundColor Red
    foreach ($dir in $excluded) {
        Write-Host "  - data/$dir" -ForegroundColor Red
    }
    Write-Host ""
    exit 3
}

# All guardrails passed - continue to synchronization
Write-Host "Pre-sync validation: OK" -ForegroundColor Green
Write-Host ""

# -----------------------------------------------------------------------------
# SYNCHRONIZATION
# -----------------------------------------------------------------------------

# Synchronisation fuer jedes Verzeichnis
$errorCount = 0
foreach ($dir in $DATA_DIRECTORIES) {
    $localDir = Join-Path $LOCAL_BASE_PATH $dir
    
    if (-not (Test-Path $localDir)) {
        Write-Host ""
        Write-Host "[$dir]" -ForegroundColor Yellow
        Write-Host "  WARNUNG: Lokales Verzeichnis nicht gefunden - uebersprungen" -ForegroundColor Yellow
        continue
    }
    
    try {
        Sync-DirectoryWithDiff `
            -LocalBasePath $LOCAL_BASE_PATH `
            -RemoteBasePath $REMOTE_BASE_PATH `
            -DirName $dir `
            -Force:$Force
    } catch {
        $errorCount++
        Write-Host "  FEHLER bei $dir : $($_.Exception.Message)" -ForegroundColor Red
    }
}

# -----------------------------------------------------------------------------
# Selektiver Sync der Stats-DBs aus data/db
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[Stats-DBs aus data/db]" -ForegroundColor Cyan

$dbLocalPath = Join-Path $LOCAL_BASE_PATH "db"
$dbRemotePath = "$REMOTE_BASE_PATH/db"

foreach ($dbFile in $STATS_DB_FILES) {
    $localFile = Join-Path $dbLocalPath $dbFile
    
    if (-not (Test-Path $localFile)) {
        Write-Host "  WARNUNG: $dbFile nicht gefunden - uebersprungen" -ForegroundColor Yellow
        continue
    }
    
    $fileSizeKB = [math]::Round((Get-Item $localFile).Length / 1KB, 1)
    Write-Host "  Synchronisiere $dbFile ($fileSizeKB KB)..." -ForegroundColor DarkGray
    
    try {
        # rsync fuer einzelne Datei verwenden
        $rsyncSource = (Convert-ToRsyncPath $localFile)
        $server = "$($script:SyncConfig.ServerUser)@$($script:SyncConfig.ServerHost)"
        $sshKeyCygwin = Convert-ToRsyncPath $script:SyncConfig.SSHKeyPath -PreserveShortName
        $sshCmd = "ssh -i '$sshKeyCygwin' -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3"
        
        # Stelle sicher, dass das Zielverzeichnis existiert
        Invoke-SSHCommand -Command "mkdir -p '$dbRemotePath'" | Out-Null
        
        # rsync fuer einzelne Datei
        $rsyncArgs = @(
            "-avz",
            "-e", $sshCmd,
            "$rsyncSource",
            "${server}:$dbRemotePath/"
        )
        
        & rsync @rsyncArgs 2>&1 | Out-Null
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -ne 0) {
            throw "rsync fehlgeschlagen (Exit-Code: $exitCode)"
        }
        
        Write-Host "  $dbFile - OK" -ForegroundColor Green
    } catch {
        $errorCount++
        Write-Host "  FEHLER bei $dbFile : $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Rechte auf Server setzen
if ($errorCount -eq 0) {
    Set-RemoteOwnership -RemotePath $REMOTE_BASE_PATH
}

# Zusammenfassung
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Data Sync abgeschlossen" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

if ($errorCount -gt 0) {
    Write-Host "WARNUNG: $errorCount Fehler aufgetreten!" -ForegroundColor Red
    exit 1
} else {
    $totalSynced = $DATA_DIRECTORIES.Count + $STATS_DB_FILES.Count
    Write-Host "Alle $totalSynced Elemente erfolgreich synchronisiert." -ForegroundColor Green
    Write-Host "  - $($DATA_DIRECTORIES.Count) Verzeichnisse" -ForegroundColor DarkGray
    Write-Host "  - $($STATS_DB_FILES.Count) Stats-DBs aus data/db" -ForegroundColor DarkGray
    exit 0
}
