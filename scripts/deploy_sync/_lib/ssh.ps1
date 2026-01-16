# =============================================================================
# CO.RA.PAN SSH Helper Library
# =============================================================================
#
# Zentralisierte SSH/SCP-Funktionen fuer Deploy/Sync-Scripts
# Basiert auf dem robusten Pattern aus sync_core.ps1
#
# Funktionen:
#   - Invoke-SSHCommand:   Fuehrt einzelnen SSH-Befehl aus
#   - Invoke-RemoteBash:   Fuehrt mehrzeiliges Bash-Script via stdin aus
#   - Invoke-SCP:          SCP-Upload (optional)
#
# Vorteile:
#   - Array-basierte Args (keine String-Interpolation-Probleme)
#   - Kein Invoke-Expression (keine Parse-Fehler)
#   - Konsistente SSH-Optionen (Timeouts, Keepalive)
#   - DryRun-Unterstuetzung
#   - Robustes Exitcode-Handling
#
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -----------------------------------------------------------------------------
# Konfiguration
# -----------------------------------------------------------------------------

$script:SSHConfig = @{
    # Defaults - koennen ueberschrieben werden
    Hostname    = $null
    User        = $null
    Port        = 22
    SSHExe      = "C:\Windows\System32\OpenSSH\ssh.exe"
    SSHKeyPath  = "$env:USERPROFILE\.ssh\marele"
    DryRun      = $false
}

# -----------------------------------------------------------------------------
# Set-SSHConfig: Konfiguriert SSH-Verbindungsparameter
# -----------------------------------------------------------------------------

function Set-SSHConfig {
    param(
        [string]$Hostname,
        [string]$User,
        [int]$Port = 22,
        [string]$SSHExe = "C:\Windows\System32\OpenSSH\ssh.exe",
        [string]$SSHKeyPath = "$env:USERPROFILE\.ssh\marele",
        [switch]$DryRun
    )
    
    if ($Hostname) { $script:SSHConfig.Hostname = $Hostname }
    if ($User) { $script:SSHConfig.User = $User }
    if ($Port) { $script:SSHConfig.Port = $Port }
    if ($SSHExe) { $script:SSHConfig.SSHExe = $SSHExe }
    if ($SSHKeyPath) { $script:SSHConfig.SSHKeyPath = $SSHKeyPath }
    $script:SSHConfig.DryRun = $DryRun.IsPresent
}

# -----------------------------------------------------------------------------
# Invoke-SSHCommand: Fuehrt einzelnen SSH-Befehl aus
# -----------------------------------------------------------------------------

function Invoke-SSHCommand {
    <#
    .SYNOPSIS
        Executes a single SSH command on remote host
    .PARAMETER Command
        The command to execute (single string, will be passed as-is to bash)
    .PARAMETER Hostname
        Remote hostname (overrides config)
    .PARAMETER User
        SSH user (overrides config)
    .PARAMETER Port
        SSH port (overrides config)
    .PARAMETER PassThru
        Return command output as string
    .PARAMETER NoThrow
        Don't throw on non-zero exit code
    .PARAMETER DryRun
        Only print what would be executed
    .EXAMPLE
        Invoke-SSHCommand -Command "hostname"
    .EXAMPLE
        Invoke-SSHCommand -Command "test -d /srv && echo OK" -PassThru
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command,
        
        [string]$Hostname = $script:SSHConfig.Hostname,
        [string]$User = $script:SSHConfig.User,
        [int]$Port = $script:SSHConfig.Port,
        
        [switch]$PassThru,
        [switch]$NoThrow,
        [switch]$DryRun
    )
    
    # DryRun from config or parameter
    $isDryRun = $DryRun.IsPresent -or $script:SSHConfig.DryRun
    
    # Validate required params
    if (-not $Hostname -or -not $User) {
        throw "Hostname and User must be set via Set-SSHConfig or parameters"
    }
    
    # Build SSH args array
    $sshArgs = @(
        "-i", $script:SSHConfig.SSHKeyPath,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=60",
        "-o", "ServerAliveCountMax=3",
        "-o", "ConnectTimeout=30"
    )
    
    if ($Port -ne 22) {
        $sshArgs += @("-p", $Port)
    }
    
    $sshArgs += @("${User}@${Hostname}", $Command)
    
    if ($isDryRun) {
        Write-Host "  [DRY-RUN] SSH: $Command" -ForegroundColor DarkYellow
        if ($PassThru) {
            return ""
        }
        return $true
    }
    
    # Execute
    if ($PassThru) {
        $result = & $script:SSHConfig.SSHExe @sshArgs 2>&1
        if ($LASTEXITCODE -ne 0 -and -not $NoThrow) {
            throw "SSH command failed (exit code $LASTEXITCODE): $result"
        }
        return $result
    }
    else {
        & $script:SSHConfig.SSHExe @sshArgs
        if ($LASTEXITCODE -ne 0 -and -not $NoThrow) {
            throw "SSH command failed with exit code $LASTEXITCODE"
        }
        return $true
    }
}

# -----------------------------------------------------------------------------
# Invoke-RemoteBash: Fuehrt mehrzeiliges Bash-Script via stdin aus
# -----------------------------------------------------------------------------

function Invoke-RemoteBash {
    <#
    .SYNOPSIS
        Executes multi-line bash script via stdin (no PowerShell interpolation)
    .PARAMETER Script
        Bash script text (literal - no PowerShell variable expansion)
    .PARAMETER Hostname
        Remote hostname (overrides config)
    .PARAMETER User
        SSH user (overrides config)
    .PARAMETER Port
        SSH port (overrides config)
    .PARAMETER PassThru
        Return script output
    .PARAMETER NoThrow
        Don't throw on non-zero exit code
    .PARAMETER DryRun
        Only print what would be executed
    .EXAMPLE
        Invoke-RemoteBash -Script @'
if [ -d /srv/data ]; then
    echo "OK"
else
    echo "MISSING"
fi
'@
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Script,
        
        [string]$Hostname = $script:SSHConfig.Hostname,
        [string]$User = $script:SSHConfig.User,
        [int]$Port = $script:SSHConfig.Port,
        
        [switch]$PassThru,
        [switch]$NoThrow,
        [switch]$DryRun
    )
    
    # DryRun from config or parameter
    $isDryRun = $DryRun.IsPresent -or $script:SSHConfig.DryRun
    
    # Validate
    if (-not $Hostname -or -not $User) {
        throw "Hostname and User must be set via Set-SSHConfig or parameters"
    }
    
    # Build SSH args for bash -s
    $sshArgs = @(
        "-i", $script:SSHConfig.SSHKeyPath,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=60",
        "-o", "ServerAliveCountMax=3",
        "-o", "ConnectTimeout=30"
    )
    
    if ($Port -ne 22) {
        $sshArgs += @("-p", $Port)
    }
    
    $sshArgs += @("${User}@${Hostname}", "bash", "-s")
    
    if ($isDryRun) {
        Write-Host "  [DRY-RUN] Remote Bash Script:" -ForegroundColor DarkYellow
        Write-Host "  ---" -ForegroundColor DarkGray
        $Script -split "`n" | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
        Write-Host "  ---" -ForegroundColor DarkGray
        if ($PassThru) {
            return ""
        }
        return $true
    }
    
    # Execute: pipe script to stdin
    if ($PassThru) {
        $result = $Script | & $script:SSHConfig.SSHExe @sshArgs 2>&1
        if ($LASTEXITCODE -ne 0 -and -not $NoThrow) {
            throw "Remote bash script failed (exit code $LASTEXITCODE): $result"
        }
        return $result
    }
    else {
        $Script | & $script:SSHConfig.SSHExe @sshArgs
        if ($LASTEXITCODE -ne 0 -and -not $NoThrow) {
            throw "Remote bash script failed with exit code $LASTEXITCODE"
        }
        return $true
    }
}

# -----------------------------------------------------------------------------
# Invoke-SCP: SCP file upload
# -----------------------------------------------------------------------------

function Invoke-SCP {
    <#
    .SYNOPSIS
        Upload file or directory via SCP
    .PARAMETER LocalPath
        Local file or directory path
    .PARAMETER RemotePath
        Remote destination path
    .PARAMETER Hostname
        Remote hostname (overrides config)
    .PARAMETER User
        SSH user (overrides config)
    .PARAMETER Port
        SSH port (overrides config)
    .PARAMETER Recursive
        Recursive copy for directories
    .PARAMETER DryRun
        Only print what would be executed
    .EXAMPLE
        Invoke-SCP -LocalPath "C:\data\file.txt" -RemotePath "/srv/data/"
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$LocalPath,
        
        [Parameter(Mandatory=$true)]
        [string]$RemotePath,
        
        [string]$Hostname = $script:SSHConfig.Hostname,
        [string]$User = $script:SSHConfig.User,
        [int]$Port = $script:SSHConfig.Port,
        
        [switch]$Recursive,
        [switch]$DryRun
    )
    
    # DryRun from config or parameter
    $isDryRun = $DryRun.IsPresent -or $script:SSHConfig.DryRun
    
    # Validate
    if (-not $Hostname -or -not $User) {
        throw "Hostname and User must be set via Set-SSHConfig or parameters"
    }
    
    if (-not (Test-Path $LocalPath)) {
        throw "Local path does not exist: $LocalPath"
    }
    
    # Build SCP args
    $scpArgs = @(
        "-i", $script:SSHConfig.SSHKeyPath,
        "-o", "StrictHostKeyChecking=no"
    )
    
    if ($Port -ne 22) {
        $scpArgs += @("-P", $Port)  # Note: SCP uses -P (uppercase)
    }
    
    if ($Recursive) {
        $scpArgs += "-r"
    }
    
    $scpArgs += @($LocalPath, "${User}@${Hostname}:${RemotePath}")
    
    if ($isDryRun) {
        Write-Host "  [DRY-RUN] SCP: $LocalPath -> ${User}@${Hostname}:${RemotePath}" -ForegroundColor DarkYellow
        return $true
    }
    
    # Execute
    & "scp" @scpArgs
    
    if ($LASTEXITCODE -ne 0) {
        throw "SCP failed with exit code $LASTEXITCODE"
    }
    
    return $true
}

# Note: Functions are automatically available when dot-sourced
# Export-ModuleMember is only needed if this is imported as a module
