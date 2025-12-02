# =============================================================================
# CO.RA.PAN Data Sync: Dev → Prod
# =============================================================================
#
# Synchronisiert die Daten-Verzeichnisse vom Dev-Rechner auf den Prod-Server.
#
# Synchronisierte Verzeichnisse:
#   - counters
#   - db_public
#   - metadata
#   - exports
#   - blacklab_export
#
# NICHT synchronisiert (bewusst ausgeschlossen):
#   - blacklab_index     → wird auf Server neu gebaut
#   - blacklab_index.backup → nur lokal
#   - stats_temp         → temporäre Dateien
#   - db/auth.db         → Prod-Auth-DB ist unabhängig
#   - db/transcription.db → Prod-Transkriptions-DB ist unabhängig
#   - db/auth_e2e.db     → nur für lokale E2E-Tests
#
# SELEKTIV synchronisierte Dateien aus data/db:
#   - stats_files.db     → Atlas-Statistiken pro Datei
#   - stats_country.db   → Atlas-Statistiken pro Land
#   Diese Dateien werden lokal generiert und für die Atlas-/Stats-Funktionen
#   auf dem Server benötigt (z.B. /api/v1/atlas/files).
#
# Verwendung:
#   cd C:\dev\corapan-webapp
#   .\scripts\deploy_sync\sync_data.ps1
#
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ─────────────────────────────────────────────────────────────────────────────
# Konfiguration
# ─────────────────────────────────────────────────────────────────────────────

$LOCAL_BASE_PATH  = "C:\dev\corapan-webapp\data"
$REMOTE_BASE_PATH = "/srv/webapps/corapan/data"

# Zu synchronisierende Verzeichnisse
# WICHTIG: blacklab_index, blacklab_index.backup, stats_temp, db sind bewusst NICHT enthalten!
$DATA_DIRECTORIES = @(
    "counters",
    "db_public",
    "metadata",
    "exports",
    "blacklab_export"
)

# Selektiv zu synchronisierende DB-Dateien aus data/db
# Diese werden für die Atlas-/Stats-Funktionen auf dem Server benötigt
$STATS_DB_FILES = @(
    "stats_files.db",
    "stats_country.db"
)

# ─────────────────────────────────────────────────────────────────────────────
# Core-Bibliothek laden
# ─────────────────────────────────────────────────────────────────────────────

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$coreScript = Join-Path $scriptDir "sync_core.ps1"

if (-not (Test-Path $coreScript)) {
    Write-Host "FEHLER: sync_core.ps1 nicht gefunden: $coreScript" -ForegroundColor Red
    exit 1
}

. $coreScript

# ─────────────────────────────────────────────────────────────────────────────
# Hauptprogramm
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " CO.RA.PAN Data Sync: Dev → Prod" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quelle:  $LOCAL_BASE_PATH" -ForegroundColor DarkGray
Write-Host "Ziel:    $REMOTE_BASE_PATH" -ForegroundColor DarkGray
Write-Host "Datum:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray
Write-Host ""

# Prüfen ob lokales Verzeichnis existiert
if (-not (Test-Path $LOCAL_BASE_PATH)) {
    Write-Host "FEHLER: Lokales Datenverzeichnis nicht gefunden: $LOCAL_BASE_PATH" -ForegroundColor Red
    exit 1
}

# Synchronisation für jedes Verzeichnis
$errorCount = 0
foreach ($dir in $DATA_DIRECTORIES) {
    $localDir = Join-Path $LOCAL_BASE_PATH $dir
    
    if (-not (Test-Path $localDir)) {
        Write-Host ""
        Write-Host "[$dir]" -ForegroundColor Yellow
        Write-Host "  WARNUNG: Lokales Verzeichnis nicht gefunden - übersprungen" -ForegroundColor Yellow
        continue
    }
    
    try {
        Sync-DirectoryWithDiff `
            -LocalBasePath $LOCAL_BASE_PATH `
            -RemoteBasePath $REMOTE_BASE_PATH `
            -DirName $dir
    } catch {
        $errorCount++
        Write-Host "  FEHLER bei $dir : $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Selektiver Sync der Stats-DBs aus data/db
# ─────────────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "[Stats-DBs aus data/db]" -ForegroundColor Cyan

$dbLocalPath = Join-Path $LOCAL_BASE_PATH "db"
$dbRemotePath = "$REMOTE_BASE_PATH/db"

foreach ($dbFile in $STATS_DB_FILES) {
    $localFile = Join-Path $dbLocalPath $dbFile
    
    if (-not (Test-Path $localFile)) {
        Write-Host "  WARNUNG: $dbFile nicht gefunden - übersprungen" -ForegroundColor Yellow
        continue
    }
    
    $fileSizeKB = [math]::Round((Get-Item $localFile).Length / 1KB, 1)
    Write-Host "  Synchronisiere $dbFile ($fileSizeKB KB)..." -ForegroundColor DarkGray
    
    try {
        # rsync für einzelne Datei verwenden
        $rsyncSource = (Convert-ToRsyncPath $localFile)
        $server = "$($script:SyncConfig.ServerUser)@$($script:SyncConfig.ServerHost)"
        $sshKeyCygwin = Convert-ToRsyncPath $script:SyncConfig.SSHKeyPath -PreserveShortName
        $sshCmd = "ssh -i '$sshKeyCygwin' -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3"
        
        # Stelle sicher, dass das Zielverzeichnis existiert
        Invoke-SSHCommand -Command "mkdir -p '$dbRemotePath'" | Out-Null
        
        # rsync für einzelne Datei
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
