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
#   - db                 → Dev-Datenbank
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
    Write-Host "Alle $($DATA_DIRECTORIES.Count) Verzeichnisse erfolgreich synchronisiert." -ForegroundColor Green
    exit 0
}
