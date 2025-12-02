# =============================================================================
# CO.RA.PAN Media Sync: Dev → Prod
# =============================================================================
#
# Synchronisiert die Media-Verzeichnisse vom Dev-Rechner auf den Prod-Server.
#
# Synchronisierte Verzeichnisse:
#   - transcripts
#   (weitere können einfach zur Liste hinzugefügt werden)
#
# NICHT synchronisiert:
#   - mp3-full    → zu groß / separat verwaltet
#   - mp3-split   → zu groß / separat verwaltet
#   - mp3-temp    → temporäre Dateien
#
# Verwendung:
#   cd C:\dev\corapan-webapp
#   .\scripts\deploy_sync\sync_media.ps1
#
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ─────────────────────────────────────────────────────────────────────────────
# Konfiguration
# ─────────────────────────────────────────────────────────────────────────────

$LOCAL_BASE_PATH  = "C:\dev\corapan-webapp\media"
$REMOTE_BASE_PATH = "/srv/webapps/corapan/media"

# Zu synchronisierende Verzeichnisse
# Neue Verzeichnisse einfach hier hinzufügen:
$MEDIA_DIRECTORIES = @(
    "transcripts"
    # "mp3-split"  # auskommentiert - bei Bedarf aktivieren
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
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host " CO.RA.PAN Media Sync: Dev → Prod" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Quelle:  $LOCAL_BASE_PATH" -ForegroundColor DarkGray
Write-Host "Ziel:    $REMOTE_BASE_PATH" -ForegroundColor DarkGray
Write-Host "Datum:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray
Write-Host ""

# Prüfen ob lokales Verzeichnis existiert
if (-not (Test-Path $LOCAL_BASE_PATH)) {
    Write-Host "FEHLER: Lokales Medienverzeichnis nicht gefunden: $LOCAL_BASE_PATH" -ForegroundColor Red
    exit 1
}

# Synchronisation für jedes Verzeichnis
$errorCount = 0
foreach ($dir in $MEDIA_DIRECTORIES) {
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
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host " Media Sync abgeschlossen" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""

if ($errorCount -gt 0) {
    Write-Host "WARNUNG: $errorCount Fehler aufgetreten!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "Alle $($MEDIA_DIRECTORIES.Count) Verzeichnisse erfolgreich synchronisiert." -ForegroundColor Green
    exit 0
}
