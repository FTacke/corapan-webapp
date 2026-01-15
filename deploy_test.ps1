# =============================================================================
# CO.RA.PAN Full Production Deployment
# =============================================================================
#
# End-to-End Deployment: Data + Media Sync + Server Deploy + Health Check
#
# Schritte:
#   1. Data-Verzeichnisse synchronisieren
#   2. Media-Verzeichnisse synchronisieren
#   3. Deploy-Script auf Server ausfÃ¼hren (--rebuild-index --skip-git)
#   4. Health-Check durchfÃ¼hren
#
# Verwendung:
#   cd C:\dev\corapan-webapp
#   .\scripts\deploy_sync\deploy_full_prod.ps1
#
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Konfiguration
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

$SERVER_HOST    = "137.248.186.51"
$SERVER_USER    = "root"
$SSH_KEY_PATH   = "$env:USERPROFILE\.ssh\marele"
$DEPLOY_SCRIPT  = "/srv/webapps/corapan/app/scripts/deploy_prod.sh"
$HEALTH_URL     = "https://corapan.online.uni-marburg.de/health"
$HEALTH_URL_LOCAL = "http://localhost:6000/health"
$WAIT_SECONDS   = 15

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Helper-Funktionen
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function Write-Header {
    param([string]$Text, [string]$Color = "White")
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor $Color
    Write-Host " $Text" -ForegroundColor $Color
    Write-Host ("=" * 60) -ForegroundColor $Color
    Write-Host ""
}

function Write-Step {
    param([int]$Number, [string]$Text)
    Write-Host ""
    Write-Host "[$Number/4] $Text" -ForegroundColor White
    Write-Host ("-" * 40) -ForegroundColor DarkGray
}

function Invoke-ServerCommand {
    param([string]$Command)
    
    $sshArgs = @(
        "-i", $SSH_KEY_PATH,
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "$SERVER_USER@$SERVER_HOST",
        $Command
    )
    
    & ssh @sshArgs
    return $LASTEXITCODE
}

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Hauptprogramm
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

$startTime = Get-Date

Write-Header "CO.RA.PAN Full Production Deployment" "Cyan"
Write-Host "Server:    $SERVER_HOST" -ForegroundColor DarkGray
Write-Host "Startzeit: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Schritt 1: Data Sync
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Write-Step 1 "Data-Verzeichnisse synchronisieren"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataSyncScript = Join-Path $scriptDir "sync_data.ps1"

if (-not (Test-Path $dataSyncScript)) {
    Write-Host "FEHLER: sync_data.ps1 nicht gefunden: $dataSyncScript" -ForegroundColor Red
    exit 1
}

try {
    & $dataSyncScript
    if ($LASTEXITCODE -ne 0) {
        throw "Data-Sync fehlgeschlagen mit Exit-Code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "FEHLER: Data-Sync fehlgeschlagen!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Schritt 2: Media Sync
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Write-Step 2 "Media-Verzeichnisse synchronisieren"

$mediaSyncScript = Join-Path $scriptDir "sync_media.ps1"

if (-not (Test-Path $mediaSyncScript)) {
    Write-Host "FEHLER: sync_media.ps1 nicht gefunden: $mediaSyncScript" -ForegroundColor Red
    exit 1
}

try {
    & $mediaSyncScript
    if ($LASTEXITCODE -ne 0) {
        throw "Media-Sync fehlgeschlagen mit Exit-Code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "FEHLER: Media-Sync fehlgeschlagen!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Schritt 3: Server Deploy
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Write-Step 3 "Deploy auf Server starten"

Write-Host "FÃ¼hre aus: $DEPLOY_SCRIPT --rebuild-index --skip-git" -ForegroundColor DarkGray

$deployCommand = "cd /srv/webapps/corapan/app && bash scripts/deploy_prod.sh --rebuild-index --skip-git"
$exitCode = Invoke-ServerCommand -Command $deployCommand

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "FEHLER: Server-Deploy fehlgeschlagen mit Exit-Code $exitCode" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Server-Deploy erfolgreich." -ForegroundColor Green

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Schritt 4: Health Check
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Write-Step 4 "Health-Check durchfÃ¼hren"

Write-Host "Warte $WAIT_SECONDS Sekunden auf Container-Start..." -ForegroundColor DarkGray
Start-Sleep -Seconds $WAIT_SECONDS

$healthJson = $null
$healthSource = ""

# Versuch 1: Direkt Ã¼ber HTTPS
Write-Host "PrÃ¼fe Health Ã¼ber $HEALTH_URL..." -ForegroundColor DarkGray
try {
    # Ignore SSL certificate errors (self-signed or expired certs)
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        # PowerShell Core
        $response = Invoke-RestMethod -Uri $HEALTH_URL -Method Get -SkipCertificateCheck -TimeoutSec 10
    } else {
        # Windows PowerShell 5.1
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
        $response = Invoke-RestMethod -Uri $HEALTH_URL -Method Get -TimeoutSec 10
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = $null
    }
    $healthJson = $response
    $healthSource = "HTTPS (extern)"
} catch {
    Write-Host "  HTTPS-Zugriff fehlgeschlagen: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Versuch 2: Via SSH auf localhost
if (-not $healthJson) {
    Write-Host "PrÃ¼fe Health via SSH (localhost:6000)..." -ForegroundColor DarkGray
    try {
        $sshHealthCmd = "curl -s $HEALTH_URL_LOCAL"
        $sshArgs = @(
            "-i", $SSH_KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            "-o", "BatchMode=yes",
            "$SERVER_USER@$SERVER_HOST",
            $sshHealthCmd
        )
        $result = & ssh @sshArgs 2>&1
        if ($LASTEXITCODE -eq 0 -and $result) {
            $healthJson = $result | ConvertFrom-Json
            $healthSource = "SSH (localhost)"
        }
    } catch {
        Write-Host "  SSH Health-Check fehlgeschlagen: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Ergebnis auswerten
Write-Host ""
if ($healthJson) {
    $status = $healthJson.status
    $blacklabOk = $false
    
    # BlackLab-Status prÃ¼fen (verschiedene Strukturen mÃ¶glich)
    if ($healthJson.blacklab) {
        if ($healthJson.blacklab.ok -eq $true) {
            $blacklabOk = $true
        } elseif ($healthJson.blacklab.status -eq "ok" -or $healthJson.blacklab.status -eq "healthy") {
            $blacklabOk = $true
        }
    }
    
    Write-Host "Health-Check Ergebnis (via $healthSource):" -ForegroundColor White
    Write-Host ""
    
    if ($status -eq "healthy" -and $blacklabOk) {
        Write-Host "  â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—" -ForegroundColor Green
        Write-Host "  â•‘                                           â•‘" -ForegroundColor Green
        Write-Host "  â•‘   âœ“ DEPLOYMENT ERFOLGREICH               â•‘" -ForegroundColor Green
        Write-Host "  â•‘                                           â•‘" -ForegroundColor Green
        Write-Host "  â•‘   Status:   healthy                       â•‘" -ForegroundColor Green
        Write-Host "  â•‘   BlackLab: OK                            â•‘" -ForegroundColor Green
        Write-Host "  â•‘                                           â•‘" -ForegroundColor Green
        Write-Host "  â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•" -ForegroundColor Green
    } else {
        Write-Host "  â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—" -ForegroundColor Red
        Write-Host "  â•‘                                           â•‘" -ForegroundColor Red
        Write-Host "  â•‘   âœ— HEALTH-CHECK FEHLGESCHLAGEN          â•‘" -ForegroundColor Red
        Write-Host "  â•‘                                           â•‘" -ForegroundColor Red
        Write-Host "  â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•" -ForegroundColor Red
        Write-Host ""
        Write-Host "Roh-JSON:" -ForegroundColor Yellow
        $healthJson | ConvertTo-Json -Depth 5 | Write-Host
        exit 1
    }
