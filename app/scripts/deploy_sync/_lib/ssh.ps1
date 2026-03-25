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

$coreSsh = Join-Path (Split-Path -Parent $PSScriptRoot) 'core\ssh.ps1'
if (Test-Path $coreSsh) {
    . $coreSsh
}

function Get-DefaultSshKeyPath {
    $candidates = @(
        (Join-Path $env:USERPROFILE '.ssh\marele'),
        (Join-Path $env:USERPROFILE '.ssh\id_ed25519')
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $candidates[0]
}

function Get-DefaultSshKeyPathShort {
    param(
        [string]$ResolvedKeyPath = (Get-DefaultSshKeyPath)
    )

    $legacyShortPath = 'C:\Users\FELIXT~1\.ssh\marele'
    if ($ResolvedKeyPath -like '*\\marele' -and (Test-Path $legacyShortPath)) {
        return $legacyShortPath
    }

    return $ResolvedKeyPath
}

$script:DefaultSSHKeyPath = Get-DefaultSshKeyPath
$script:DefaultSSHKeyPathShort = Get-DefaultSshKeyPathShort -ResolvedKeyPath $script:DefaultSSHKeyPath

# -----------------------------------------------------------------------------
# Konfiguration
# -----------------------------------------------------------------------------

$script:SSHConfig = @{
    # Defaults - koennen ueberschrieben werden
    Hostname        = "marele.online.uni-marburg.de"
    User            = "root"
    Port            = 22
    SSHExe          = "C:\Windows\System32\OpenSSH\ssh.exe"
    # Full path for OpenSSH
    SSHKeyPath      = $script:DefaultSSHKeyPath
    # Short path for cwRsync (8.3 format) when available; otherwise use the resolved full path.
    SSHKeyPathShort = $script:DefaultSSHKeyPathShort
    DryRun          = $false
}

$script:RemotePaths = @{
    RuntimeRoot = "/srv/webapps/corapan"
    DataRoot    = "/srv/webapps/corapan/data"
    MediaRoot   = "/srv/webapps/corapan/media"
    BlackLabDataRoot = "/srv/webapps/corapan/data/blacklab"
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
        [string]$SSHKeyPath = $script:DefaultSSHKeyPath,
        [string]$SSHKeyPathShort = $script:DefaultSSHKeyPathShort,
        [switch]$DryRun
    )
    
    if ($Hostname) { $script:SSHConfig.Hostname = $Hostname }
    if ($User) { $script:SSHConfig.User = $User }
    if ($Port) { $script:SSHConfig.Port = $Port }
    if ($SSHExe) { $script:SSHConfig.SSHExe = $SSHExe }
    if ($SSHKeyPath) { $script:SSHConfig.SSHKeyPath = $SSHKeyPath }
    if ($SSHKeyPathShort) { $script:SSHConfig.SSHKeyPathShort = $SSHKeyPathShort }
    $script:SSHConfig.DryRun = $DryRun.IsPresent
}

# -----------------------------------------------------------------------------
# Remote path configuration (runtime roots)
# -----------------------------------------------------------------------------

function Set-RemotePaths {
    param(
        [string]$RuntimeRoot,
        [string]$BlackLabDataRoot
    )

    if ($RuntimeRoot) {
        $script:RemotePaths.RuntimeRoot = $RuntimeRoot
        $script:RemotePaths.DataRoot = "$RuntimeRoot/data"
        $script:RemotePaths.MediaRoot = "$RuntimeRoot/media"
    }

    if ($BlackLabDataRoot) {
        $script:RemotePaths.BlackLabDataRoot = $BlackLabDataRoot
    }
}

function Get-RemotePaths {
    return $script:RemotePaths
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
    
    $effectiveConfig = @{
        Hostname   = $Hostname
        User       = $User
        Port       = $Port
        SSHExe     = $script:SSHConfig.SSHExe
        SSHKeyPath = $script:SSHConfig.SSHKeyPath
        DryRun     = ($DryRun.IsPresent -or $script:SSHConfig.DryRun)
    }

    return Invoke-SyncOpenSshCommand -SSHConfig $effectiveConfig -Command $Command -PassThru:$PassThru -NoThrow:$NoThrow -DryRun:$DryRun
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
    
    $effectiveConfig = @{
        Hostname   = $Hostname
        User       = $User
        Port       = $Port
        SSHExe     = $script:SSHConfig.SSHExe
        SSHKeyPath = $script:SSHConfig.SSHKeyPath
        DryRun     = ($DryRun.IsPresent -or $script:SSHConfig.DryRun)
    }

    return Invoke-SyncRemoteBash -SSHConfig $effectiveConfig -Script $Script -PassThru:$PassThru -NoThrow:$NoThrow -DryRun:$DryRun
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
    
    $effectiveConfig = @{
        Hostname   = $Hostname
        User       = $User
        Port       = $Port
        SSHExe     = $script:SSHConfig.SSHExe
        SSHKeyPath = $script:SSHConfig.SSHKeyPath
        DryRun     = ($DryRun.IsPresent -or $script:SSHConfig.DryRun)
    }

    return Invoke-SyncScpLegacy -SSHConfig $effectiveConfig -LocalPath $LocalPath -RemotePath $RemotePath -Recursive:$Recursive -DryRun:$DryRun
}

# Note: Functions are automatically available when dot-sourced
# Export-ModuleMember is only needed if this is imported as a module
