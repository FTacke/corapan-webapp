# =============================================================================
# CO.RA.PAN Media Sync: Dev -> Prod
# =============================================================================
#
# Synchronisiert die Media-Verzeichnisse vom Dev-Rechner auf den Prod-Server.
# Der Sync erfolgt als Delta-Sync: nur neue oder geaenderte Dateien werden
# uebertragen, geaenderte Dateien ueberschreiben die Version auf dem Server.
#
# SYNCHRONISIERTE VERZEICHNISSE (unter media/):
#   - transcripts   -> Transkript-Dateien (JSON, TSV, etc.)
#   - mp3-full      -> Vollstaendige Audio-Aufnahmen (kann mehrere GB umfassen)
#   - mp3-split     -> Aufgeteilte Audio-Segmente (kann mehrere GB umfassen)
#
# MANIFEST-SPEICHERUNG:
#   Jedes Verzeichnis hat sein eigenes Manifest zur Aenderungsverfolgung:
#     media/transcripts/.sync_state/transcripts_manifest.json
#     media/mp3-full/.sync_state/mp3-full_manifest.json
#     media/mp3-split/.sync_state/mp3-split_manifest.json
#
#   Alte globale Manifeste (unter media/.sync_state/) werden automatisch
#   in die korrekten verzeichnisspezifischen Pfade migriert.
#
# NICHT SYNCHRONISIERT:
#   - mp3-temp      -> temporaere Dateien (lokale Verarbeitung)
#
# HINWEIS ZU GROSSEN DATENMENGEN:
#   Die Audio-Verzeichnisse (mp3-full, mp3-split) koennen mehrere Gigabyte
#   enthalten. Der Sync verwendet rsync mit folgenden Optimierungen:
#   - Delta-Transfer: nur tatsaechliche Aenderungen werden uebertragen
#   - --partial: unterbrochene Transfers koennen fortgesetzt werden
#   - Fortschrittsanzeige: zeigt globalen Fortschritt waehrend des Uploads
#   - Kompression (-z): ist fuer rsync-Effizienz aktiviert
#
#   Bei sehr grossen Erstuebertragungen kann der Sync mehrere Stunden dauern.
#   Der Fortschritt wird im Terminal angezeigt.
#
# FORCE-MODUS (-Force):
#   Mit dem Parameter -Force werden alle Dateien uebertragen, unabhaengig
#   vom Manifest-Zustand. Nuetzlich nach Manifest-Korruption oder zur
#   vollstaendigen Resynchronisation.
#   
#   Beispiel: .\sync_media.ps1 -Force
#
# FORCE-MP3-MODUS (-ForceMP3):
#   Mit dem Parameter -ForceMP3 werden nur die MP3-Verzeichnisse
#   (mp3-full, mp3-split) vollstaendig uebertragen. Transcripts bleiben
#   im Delta-Modus. Nuetzlich wenn nur Audio-Dateien resynchronisiert
#   werden sollen.
#   
#   Beispiel: .\sync_media.ps1 -ForceMP3
#
# VERWENDUNG:
#   cd C:\dev\corapan-webapp
#   .\scripts\deploy_sync\sync_media.ps1              # Normal (Delta-Sync)
#   .\scripts\deploy_sync\sync_media.ps1 -Force       # Force (alle Dateien)
#   .\scripts\deploy_sync\sync_media.ps1 -ForceMP3    # Force nur MP3s
#   .\scripts\deploy_sync\sync_media.ps1 -DryRun      # Dry-Run (nur Zielpfade)
#
# DRY-RUN:
#   -DryRun zeigt nur Zielpfade und transferiert keine Dateien.
#
# Siehe auch:
#   - update_data_media.ps1  -> Interaktiver Maintenance-Runner
#   - sync_data.ps1          -> Data-Verzeichnisse synchronisieren
#   - sync_core.ps1          -> Gemeinsame Sync-Funktionen
#
# =============================================================================

param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot,
    
    [switch]$Force,
    [switch]$ForceMP3,
    [switch]$DryRun
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

$LOCAL_BASE_PATH  = Join-Path $runtimeRoot "media"

# Zu synchronisierende Verzeichnisse
# Alle aktiven Media-Verzeichnisse inkl. grosser Audio-Ordner:
$MEDIA_DIRECTORIES = @(
    "transcripts",
    "mp3-full",
    "mp3-split"
)

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

$remotePaths = Get-RemotePaths
$REMOTE_RUNTIME_ROOT = $remotePaths.RuntimeRoot
$REMOTE_MEDIA_ROOT = $remotePaths.MediaRoot

$mediaRunRecord = New-SyncRunRecord -Lane 'media' -Source $LOCAL_BASE_PATH -Target $REMOTE_MEDIA_ROOT -Transport 'rsync-cwrsync' -DryRun:$DryRun

# Runtime-first guard (fail fast if prod mounts drift)
Assert-RemoteRuntimeFirstMounts -RuntimeRoot $REMOTE_RUNTIME_ROOT

# -----------------------------------------------------------------------------
# Hauptprogramm
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host " CO.RA.PAN Media Sync: Dev -> Prod" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Quelle:  $LOCAL_BASE_PATH" -ForegroundColor DarkGray
Write-Host "Ziel:    $REMOTE_MEDIA_ROOT" -ForegroundColor DarkGray
Write-Host "Datum:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray
if ($Force) {
    Write-Host "Modus:   FORCE (alle Dateien uebertragen)" -ForegroundColor Yellow
} elseif ($ForceMP3) {
    Write-Host "Modus:   FORCE-MP3 (nur mp3-full/mp3-split)" -ForegroundColor Yellow
} elseif ($DryRun) {
    Write-Host "Modus:   DRY-RUN (keine Dateien werden transferiert)" -ForegroundColor Yellow
} else {
    Write-Host "Modus:   Delta-Sync (nur Aenderungen)" -ForegroundColor DarkGray
}
Write-Host ""

# Pruefen ob lokales Verzeichnis existiert
if (-not (Test-Path $LOCAL_BASE_PATH)) {
    Write-Host "FEHLER: Lokales Medienverzeichnis nicht gefunden: $LOCAL_BASE_PATH" -ForegroundColor Red
    exit 1
}

# Synchronisation fuer jedes Verzeichnis
$errorCount = 0
$mediaResults = @()
if ($DryRun) {
    Write-Host "[DRY RUN] Remote targets:" -ForegroundColor Cyan
    Write-Host "  - Base: $REMOTE_MEDIA_ROOT" -ForegroundColor DarkGray
    foreach ($dir in $MEDIA_DIRECTORIES) {
        Write-Host "  - media/$dir -> $REMOTE_MEDIA_ROOT/$dir" -ForegroundColor DarkGray
    }
    Write-Host ""
    $summaryPath = Complete-SyncRunRecord -Run $mediaRunRecord -ExitCode 0 -NoChange $true -ChangeCount 0 -DeleteCount 0 -FallbackUsed $false
    Write-Host "Dry-run summary: $summaryPath" -ForegroundColor DarkGray
    exit 0
}
foreach ($dir in $MEDIA_DIRECTORIES) {
    $localDir = Join-Path $LOCAL_BASE_PATH $dir
    
    if (-not (Test-Path $localDir)) {
        Write-Host ""
        Write-Host "[$dir]" -ForegroundColor Yellow
        Write-Host "  WARNUNG: Lokales Verzeichnis nicht gefunden - uebersprungen" -ForegroundColor Yellow
        continue
    }
    
    try {
        # Force-Logik: -Force gilt fuer alle, -ForceMP3 nur fuer mp3-*
        $useForce = $Force -or ($ForceMP3 -and $dir -like "mp3-*")
        
        $dirResult = Sync-DirectoryWithDiff `
            -LocalBasePath $LOCAL_BASE_PATH `
            -RemoteBasePath $REMOTE_MEDIA_ROOT `
            -DirName $dir `
            -Force:$useForce
        $mediaResults += $dirResult
    } catch {
        $errorCount++
        Write-Host "  FEHLER bei $dir : $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Rechte auf Server setzen
if ($errorCount -eq 0) {
    Set-RemoteOwnership -RemotePath $REMOTE_MEDIA_ROOT
}

$mediaChangeCount = (($mediaResults | Measure-Object -Property ChangeCount -Sum).Sum)
if ($null -eq $mediaChangeCount) { $mediaChangeCount = 0 }
$mediaDeleteCount = (($mediaResults | Measure-Object -Property DeleteCount -Sum).Sum)
if ($null -eq $mediaDeleteCount) { $mediaDeleteCount = 0 }
$mediaFallbackUsed = (@($mediaResults | Where-Object { $_.FallbackUsed }).Count -gt 0)

# Zusammenfassung
Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host " Media Sync abgeschlossen" -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""

if ($errorCount -gt 0) {
    $summaryPath = Complete-SyncRunRecord -Run $mediaRunRecord -ExitCode 1 -NoChange $false -ChangeCount $mediaChangeCount -DeleteCount $mediaDeleteCount -FallbackUsed $mediaFallbackUsed
    Write-Host "Run summary: $summaryPath" -ForegroundColor DarkGray
    Write-Host "WARNUNG: $errorCount Fehler aufgetreten!" -ForegroundColor Red
    exit 1
} else {
    $summaryPath = Complete-SyncRunRecord -Run $mediaRunRecord -ExitCode 0 -NoChange ($mediaChangeCount -eq 0 -and $mediaDeleteCount -eq 0) -ChangeCount $mediaChangeCount -DeleteCount $mediaDeleteCount -FallbackUsed $mediaFallbackUsed
    Write-Host "Run summary: $summaryPath" -ForegroundColor DarkGray
    Write-Host "Alle $($MEDIA_DIRECTORIES.Count) Verzeichnisse erfolgreich synchronisiert." -ForegroundColor Green
    exit 0
}
