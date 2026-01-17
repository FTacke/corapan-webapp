<#
.SYNOPSIS
    Publish BlackLab index from local staging to production server
.DESCRIPTION
    Uploads data/blacklab_index.new to production, validates it, performs atomic swap,
    and verifies production server health. Designed for Windows with SSH+tar fallback.
.PARAMETER Host
    Production server hostname or IP address
.PARAMETER User
    SSH user for production server
.PARAMETER Port
    SSH port (default: 22)
.PARAMETER DataDir
    Remote data directory path
.PARAMETER ConfigDir
    Remote BlackLab config directory path
.PARAMETER DryRun
    Perform checks and show what would be done without making changes
.EXAMPLE
    .\scripts\publish_blacklab_index.ps1
.EXAMPLE
    .\scripts\publish_blacklab_index.ps1 -Host 192.168.1.100 -DryRun
#>

[CmdletBinding()]
param(
    [Alias('Host')]
    [string]$Hostname = "137.248.186.51",
    [string]$User = "root",
    [int]$Port = 22,
    [string]$DataDir = "/srv/webapps/corapan/data",
    [string]$ConfigDir = "/srv/webapps/corapan/app/config/blacklab",
    [switch]$DryRun,
    [int]$KeepBackups = 2,
    [switch]$NoBackupCleanup
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# ============================================================================
# LOAD SSH HELPER LIBRARY
# ============================================================================

. "$PSScriptRoot\_lib\ssh.ps1"

# ============================================================================
# CONFIGURATION
# ============================================================================

$BLACKLAB_IMAGE = "instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7"
$VALIDATE_PORT = 18092
$PROD_PORT = 8081
$MIN_FILES = 10
$MIN_SIZE_MB = 50

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "  > $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor Gray
}

function Exit-WithError {
    param([string]$Message, [int]$Code = 1)
    Write-Host ""
    Write-Error $Message
    exit $Code
}

function Test-Command {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

# SSH functions now provided by _lib/ssh.ps1
# Invoke-SSHCommand: single command execution
# Invoke-RemoteBash: multi-line bash script via stdin

function Invoke-BackupCleanup {
    param(
        [string]$RemoteDataDir,
        [int]$Keep,
        [bool]$IsPublished
    )
    
    Write-Section "STEP 8: BACKUP RETENTION (Server-side)"
    
    if (-not $IsPublished) {
        Write-Info "Skipping backup retention (deployment did not complete successfully)"
        return
    }
    
    if ($NoBackupCleanup) {
        Write-Info "Backup retention skipped (-NoBackupCleanup flag set)"
        return
    }
    
    Write-Step "Invoking server-side retention script..."
    
    # Build environment variables for remote script
    $deleteFlag = if ($DryRun) { 0 } else { 1 }
    
    # Remote script path (injected into webapp at deployment time)
    $remoteScript = "/srv/webapps/corapan/app/scripts/blacklab/retain_blacklab_backups_prod.sh"
    
    # Build retention command with environment variables
    $retentionCmd = @"
BLACKLAB_KEEP_BACKUPS=$Keep \
BLACKLAB_RETENTION_DELETE=$deleteFlag \
DATA_ROOT='$RemoteDataDir' \
bash '$remoteScript'
"@
    
    if ($DryRun) {
        Write-Info "[DRY-RUN] Would run server-side retention script"
        Write-Info "Command: $retentionCmd"
        Write-Success "Retention would execute in dry-run mode (no actual deletions)"
        return
    }
    
    try {
        Write-Step "Executing retention on server..."
        $output = Invoke-RemoteBash -Script $retentionCmd -PassThru
        
        # Log server output
        if ($output) {
            Write-Host $output -ForegroundColor Gray
        }
        
        Write-Success "Server-side retention completed"
    }
    catch {
        Write-Error "Backup retention failed: $_"
        Write-Info "Continuing despite retention error (index is safe, backups may accumulate)"
    }
}


# ============================================================================
# MAIN SCRIPT
# ============================================================================

Write-Host ""
Write-Host "BlackLab Index Publisher" -ForegroundColor Magenta
Write-Host "=========================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Target:    ${User}@${Hostname}:$Port" -ForegroundColor Gray
Write-Host "Data Dir:  $DataDir" -ForegroundColor Gray
Write-Host "Config:    $ConfigDir" -ForegroundColor Gray
if ($DryRun) {
    Write-Host "Mode:      DRY-RUN (no changes will be made)" -ForegroundColor Yellow
}
Write-Host ""

# Configure SSH helper
Set-SSHConfig -Hostname $Hostname -User $User -Port $Port -DryRun:$DryRun

# ============================================================================
# STEP 1: LOCAL PREFLIGHT
# ============================================================================

Write-Section "STEP 1: LOCAL PREFLIGHT"

# Calculate repo root (script is now in scripts/deploy_sync/)
$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$localNew = Join-Path $repoRoot "data\blacklab_index.new"

Write-Step "Checking local staging index: $localNew"

if (-not (Test-Path $localNew)) {
    Exit-WithError "Local staging index not found: $localNew`nMake sure you run this script from the repository root or that data/blacklab_index.new exists."
}

Write-Success "Directory exists"

Write-Step "Counting files and calculating size..."

$files = Get-ChildItem -Path $localNew -Recurse -File
$fileCount = $files.Count
$sizeMB = [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1MB, 1)

Write-Success "Files: $fileCount"
Write-Success "Size:  $sizeMB MB"

if ($fileCount -lt $MIN_FILES) {
    Exit-WithError "File count too low ($fileCount < $MIN_FILES). Index appears incomplete."
}

if ($sizeMB -lt $MIN_SIZE_MB) {
    Exit-WithError "Index size too small ($sizeMB MB < $MIN_SIZE_MB MB). Index appears incomplete."
}

Write-Success "Local preflight passed"

# ============================================================================
# STEP 2: REMOTE CONNECTIVITY & PREREQUISITES
# ============================================================================

Write-Section "STEP 2: REMOTE CONNECTIVITY & PREREQUISITES"

Write-Step "Checking SSH connectivity..."

if (-not (Test-Command "ssh")) {
    Exit-WithError "SSH command not found. Please install OpenSSH."
}

try {
    $remoteHostname = Invoke-SSHCommand -Command "hostname" -PassThru
    Write-Success "Connected to: $($remoteHostname.Trim())"
}
catch {
    Exit-WithError "SSH connection failed: $_"
}

Write-Step "Verifying remote paths..."

$remoteActive = "$DataDir/blacklab_index"
$remoteNew = "$DataDir/blacklab_index.new"

if ($DryRun) {
    Write-Info "[DRY-RUN] Would verify paths: $DataDir, $ConfigDir"
    Write-Success "Remote paths verified (dry-run)"
}
else {
    $pathCheck = Invoke-SSHCommand -Command "test -d '$DataDir' && test -d '$ConfigDir' && echo 'OK' || echo 'FAIL'" -PassThru
    if ($pathCheck -notmatch "OK") {
        Exit-WithError "Remote paths do not exist: $DataDir or $ConfigDir"
    }
    Write-Success "Remote paths verified"
}

Write-Step "Checking remote tools (docker, curl, tar)..."

if ($DryRun) {
    Write-Info "[DRY-RUN] Would check for: docker, curl, tar"
    Write-Success "Remote tools verified (dry-run)"
}
else {
    $toolCheck = Invoke-SSHCommand -Command "command -v docker >/dev/null && command -v curl >/dev/null && command -v tar >/dev/null && echo 'OK' || echo 'FAIL'" -PassThru
    if ($toolCheck -notmatch "OK") {
        Exit-WithError "Required tools missing on remote server (need: docker, curl, tar)"
    }
    Write-Success "Remote tools verified"
}

# ============================================================================
# STEP 3: UPLOAD
# ============================================================================

Write-Section "STEP 3: UPLOAD INDEX TO STAGING"

Write-Step "Preparing upload (tar+ssh streaming method)..."

if (-not (Test-Command "tar")) {
    Write-Info "Warning: tar not found, attempting scp fallback..."
    
    if (-not (Test-Command "scp")) {
        Exit-WithError "Neither tar nor scp available. Cannot upload."
    }
    
    # SCP fallback (copy entire directory, no wildcards)
    Write-Step "Using scp fallback (slower, no streaming)..."
    
    if ($DryRun) {
        Write-Info "[DRY-RUN] Would execute: scp -O -r `"$localNew`" `"${User}@${Hostname}:$DataDir/`""
    }
    else {
        Write-Info "Preparing remote directory..."
        Invoke-SSHCommand -Command "rm -rf '$remoteNew'" | Out-Null
        
        Write-Info "Uploading via scp (this may take 5-15 minutes)..."
        # Use SCP helper
        try {
            Invoke-SCP -LocalPath $localNew -RemotePath "$DataDir/" -Recursive
            Write-Success "Upload completed"
        }
        catch {
            Exit-WithError "SCP upload failed: $_"
        }
    }
}
else {
    Write-Step "Using tar+ssh streaming method (recommended)..."
    
    if ($DryRun) {
        Write-Info "[DRY-RUN] Would stream tar archive to remote via SSH"
        Write-Info "Command: tar -cf - -C `"$localNew`" . | ssh ${User}@${Hostname} `"mkdir -p '$remoteNew'; rm -rf '$remoteNew'/*; tar -xpf - -C '$remoteNew'`""
    }
    else {
        Write-Info "Streaming index to remote (this may take 5-15 minutes)..."
        
        # Prepare remote directory first
        $prepareScript = @"
set -euo pipefail
mkdir -p '$remoteNew'
rm -rf '$remoteNew'/*
"@
        Invoke-RemoteBash -Script $prepareScript | Out-Null
        
        # Stream tar via SSH using cmd pipeline (most reliable on Windows)
        Write-Info "Executing tar | ssh pipeline..."
        
        try {
            $sshTarget = "$User@$Hostname"
            if ($Port -ne 22) {
                $sshTarget = "-p $Port $sshTarget"
            }
            
            $remoteCmd = "tar -xpf - -C '$remoteNew'"
            $pipelineCmd = "tar -cf - -C `"$localNew`" . | ssh $sshTarget `"$remoteCmd`""
            
            $output = cmd /c $pipelineCmd 2>&1
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Pipeline output: $output"
                throw "Upload failed with exit code $LASTEXITCODE"
            }
            
            Write-Success "Upload completed"
        }
        catch {
            Exit-WithError "tar+ssh upload failed: $_"
        }
    }
}

# ============================================================================
# STEP 4: REMOTE VERIFICATION
# ============================================================================

Write-Section "STEP 4: REMOTE VERIFICATION"

Write-Step "Verifying uploaded files..."

if ($DryRun) {
    Write-Info "[DRY-RUN] Would verify uploaded files"
    Write-Success "Remote verification passed (dry-run)"
}
else {
    $statsScript = @"
find '$remoteNew' -type f | wc -l
du -sb '$remoteNew' | awk '{print \$1}'
"@
    $remoteStats = Invoke-RemoteBash -Script $statsScript -PassThru
    $lines = $remoteStats -split "`n"
    $remoteFileCount = [int]($lines[0].Trim())
    $remoteSizeBytes = [long]($lines[1].Trim())
    $remoteSizeMB = [math]::Round($remoteSizeBytes / 1MB, 1)

    Write-Success "Remote files: $remoteFileCount"
    Write-Success "Remote size:  $remoteSizeMB MB ($remoteSizeBytes bytes)"

    if ($remoteFileCount -lt $MIN_FILES) {
        Exit-WithError "Remote file count too low ($remoteFileCount < $MIN_FILES). Upload incomplete."
    }

    if ($remoteSizeMB -lt $MIN_SIZE_MB) {
        Exit-WithError "Remote size too small ($remoteSizeMB MB < $MIN_SIZE_MB MB). Upload incomplete."
    }

    Write-Success "Remote verification passed"
}

# ============================================================================
# STEP 5: VALIDATE NEW INDEX (GATE)
# ============================================================================

Write-Section "STEP 5: VALIDATE NEW INDEX (CRITICAL GATE)"

Write-Step "Starting temporary validation container..."

if ($DryRun) {
    Write-Info "[DRY-RUN] Would start validation container on port $VALIDATE_PORT"
}
else {
    # Stop any existing validation container
    Invoke-SSHCommand -Command "docker rm -f bl-validate-new >/dev/null 2>&1 || true" -NoThrow | Out-Null
    
    # Start validation container
    # Build Docker command - use string format to avoid : parsing issues
    $dockerCmd = "docker run -d --rm --name bl-validate-new -p 127.0.0.1:${VALIDATE_PORT}:8080 " +
                 "-v '${remoteNew}:/data/index/corapan:ro' " +
                 "-v '${ConfigDir}:/etc/blacklab:ro' " +
                 "'$BLACKLAB_IMAGE'"
    
    $containerIdRaw = Invoke-SSHCommand -Command $dockerCmd -PassThru
    $containerId = ($containerIdRaw | Out-String).Trim()
    
    # Safe substring for display
    if ($containerId.Length -ge 12) {
        $shortId = $containerId.Substring(0, 12)
    }
    else {
        $shortId = $containerId
    }
    
    Write-Success "Container started: $shortId"
    
    Write-Step "Waiting for container to initialize..."
    Start-Sleep -Seconds 4
    
    Write-Step "Testing validation endpoints..."
    
    try {
        # Test server health
        $healthUrl = "http://127.0.0.1:$VALIDATE_PORT/blacklab-server/?outputformat=json"
        $healthJson = Invoke-SSHCommand -Command "curl -fsS '$healthUrl' 2>/dev/null" -PassThru
        
        if ([string]::IsNullOrWhiteSpace($healthJson)) {
            throw "Health endpoint returned empty response"
        }
        
        Write-Success "Health endpoint OK"
        
        # Test corpora endpoint (CRITICAL)
        $corporaUrl = "http://127.0.0.1:$VALIDATE_PORT/blacklab-server/corpora/?outputformat=json"
        $corporaJson = Invoke-SSHCommand -Command "curl -fsS '$corporaUrl' 2>/dev/null" -PassThru
        
        if ([string]::IsNullOrWhiteSpace($corporaJson)) {
            throw "Corpora endpoint returned empty response"
        }
        
        Write-Success "Corpora endpoint OK"
        
        # Parse and verify corpus exists (robust check for both "corpora" and "corapan")
        if ($corporaJson -notmatch '"corpora"') {
            Write-Error "VALIDATION FAILED: Response does not contain corpora data"
            Write-Info "Response preview: $($corporaJson.Substring(0, [Math]::Min(500, $corporaJson.Length)))"
            throw "Invalid corpora response format"
        }
        
        if ($corporaJson -notmatch '"corapan"') {
            Write-Error "VALIDATION FAILED: Corpus 'corapan' not found in index"
            Write-Info "Response preview: $($corporaJson.Substring(0, [Math]::Min(500, $corporaJson.Length)))"
            throw "Corpus validation failed"
        }
        
        # Additional check: ensure corpus is available (not empty)
        if ($corporaJson -match '"corpora":\s*\{\s*\}') {
            Write-Error "VALIDATION FAILED: Corpora object is empty"
            throw "No corpora found in index"
        }
        
        Write-Success "Corpus 'corapan' found and available"
        
        # Extract document count if possible
        if ($corporaJson -match '"documents":(\d+)') {
            $docCount = $Matches[1]
            Write-Success "Documents: $docCount"
        }
        
        if ($corporaJson -match '"tokens":(\d+)') {
            $tokenCount = $Matches[1]
            Write-Success "Tokens: $tokenCount"
        }
    }
    catch {
        Write-Error "Validation failed: $_"
        Write-Step "Cleaning up validation container..."
        Invoke-SSHCommand -Command "docker rm -f bl-validate-new >/dev/null 2>&1 || true" -NoThrow | Out-Null
        Exit-WithError "Index validation failed. ABORTING before swap." 2
    }
    finally {
        # Always cleanup validation container
        Write-Step "Cleaning up validation container..."
        Invoke-SSHCommand -Command "docker rm -f bl-validate-new >/dev/null 2>&1 || true" -NoThrow | Out-Null
    }
    
    Write-Success "Validation passed - index is healthy"
}

# ============================================================================
# STEP 6: ATOMIC SWAP
# ============================================================================

Write-Section "STEP 6: ATOMIC INDEX SWAP"

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$remoteBak = "$DataDir/blacklab_index.bak_$timestamp"

Write-Step "Performing atomic swap..."
Write-Info "ACTIVE -> BAK:    $remoteActive -> $remoteBak"
Write-Info "NEW -> ACTIVE:    $remoteNew -> $remoteActive"

if ($DryRun) {
    Write-Info "[DRY-RUN] Would execute swap commands"
}
else {
    try {
        $swapScript = @"
set -euo pipefail
mv '$remoteActive' '$remoteBak'
mv '$remoteNew' '$remoteActive'
"@
        Invoke-RemoteBash -Script $swapScript | Out-Null
        Write-Success "Swap completed successfully"
    }
    catch {
        Exit-WithError "Swap failed: $_" 3
    }
    
    # Verify swap
    $swapCheck = Invoke-SSHCommand -Command "ls -lhd '$remoteActive' '$remoteBak' 2>/dev/null" -PassThru
    Write-Info "Post-swap directories:"
    Write-Host $swapCheck -ForegroundColor DarkGray
}

# ============================================================================
# STEP 7: PRODUCTION SANITY CHECK
# ============================================================================

Write-Section "STEP 7: PRODUCTION SANITY CHECK"

Write-Step "Testing production endpoint..."

if ($DryRun) {
    Write-Info "[DRY-RUN] Would test production endpoint on port $PROD_PORT"
}
else {
    Start-Sleep -Seconds 2
    
    try {
        $prodCorporaUrl = "http://127.0.0.1:$PROD_PORT/blacklab-server/corpora/?outputformat=json"
        $prodJson = Invoke-SSHCommand -Command "curl -fsS '$prodCorporaUrl' 2>/dev/null" -PassThru
        
        if ([string]::IsNullOrWhiteSpace($prodJson)) {
            throw "Production endpoint returned empty response"
        }
        
        Write-Success "Production endpoint responding"
        
        # Verify corpus
        if ($prodJson -notmatch '"corapan"') {
            Write-Error "PRODUCTION SANITY FAILED: Corpus 'corapan' not found"
            Write-Host ""
            Write-Host "ROLLBACK REQUIRED:" -ForegroundColor Red
            Write-Host "ssh ${User}@${Hostname}" -ForegroundColor Yellow
            Write-Host ("mv $remoteActive " + $remoteActive + ".bad_$timestamp && mv $remoteBak $remoteActive") -ForegroundColor Yellow
            Exit-WithError "Production sanity check failed" 4
        }
        
        Write-Success "Corpus 'corapan' available in production"
        
        # Extract metrics
        if ($prodJson -match '"documents":(\d+)') {
            $prodDocs = $Matches[1]
            Write-Success "Production documents: $prodDocs"
        }
        
        if ($prodJson -match '"tokens":(\d+)') {
            $prodTokens = $Matches[1]
            Write-Success "Production tokens: $prodTokens"
        }
    }
    catch {
        Write-Error "Production check failed: $_"
        Write-Host ""
        Write-Host "ROLLBACK COMMAND:" -ForegroundColor Red
        Write-Host "ssh $User@$Hostname" -ForegroundColor Yellow
        Write-Host ("mv $remoteActive " + $remoteActive + ".bad_$timestamp && mv $remoteBak $remoteActive") -ForegroundColor Yellow
        Exit-WithError "Production sanity check failed" 4
    }
}

# ============================================================================
# STEP 8: BACKUP RETENTION CLEANUP
# ============================================================================

Invoke-BackupCleanup -RemoteDataDir $DataDir -Keep $KeepBackups -IsPublished $true

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Section "DEPLOYMENT COMPLETED SUCCESSFULLY"

Write-Host ""
Write-Host "Summary:" -ForegroundColor Green
Write-Host "  Local files:    $fileCount ($sizeMB MB)" -ForegroundColor Gray
if (-not $DryRun) {
    Write-Host "  Remote files:   $remoteFileCount" -ForegroundColor Gray
    Write-Host "  Backup:         $remoteBak" -ForegroundColor Gray
    Write-Host "  Active index:   $remoteActive" -ForegroundColor Gray
}
else {
    Write-Host "  Mode:           DRY-RUN (no actual changes made)" -ForegroundColor Yellow
}
Write-Host ""

if (-not $DryRun) {
    Write-Host "Rollback command (if needed within 24h):" -ForegroundColor Yellow
    Write-Host "ssh $User@$Hostname" -ForegroundColor Cyan
    Write-Host ("mv $remoteActive " + $remoteActive + ".bad_$timestamp && mv $remoteBak $remoteActive") -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "[OK] BlackLab index successfully published to production!" -ForegroundColor Green
Write-Host ""

exit 0
