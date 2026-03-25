Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pathsModule = Join-Path $PSScriptRoot 'paths.ps1'
if (Test-Path $pathsModule) {
    . $pathsModule
}

function Convert-ToCwRsyncPath {
    param(
        [Parameter(Mandatory=$true)]
        [string]$WindowsPath,

        [switch]$PreserveShortName
    )

    if ($PreserveShortName) {
        $path = $WindowsPath
    }
    else {
        $path = [System.IO.Path]::GetFullPath($WindowsPath)
    }

    if ($path -match '^([a-zA-Z]):(.*)$') {
        $drive = $Matches[1].ToLower()
        $rest = $Matches[2] -replace '\\', '/'
        return "/cygdrive/$drive$rest"
    }

    return $path -replace '\\', '/'
}

function Get-RepoBoundRsyncTooling {
    param(
        [string]$RepoRoot = (Get-SyncRepoRoot),
        [hashtable]$SyncConfig
    )

    $toolPaths = Get-SyncToolPaths -RepoRoot $RepoRoot
    $sshKeyPath = $null
    if ($SyncConfig -and $SyncConfig.ContainsKey('SSHKeyPath') -and $SyncConfig.SSHKeyPath) {
        $sshKeyPath = $SyncConfig.SSHKeyPath
    }

    if (-not $sshKeyPath -and $SyncConfig -and $SyncConfig.ContainsKey('SSHKeyPathFull')) {
        $sshKeyPath = $SyncConfig.SSHKeyPathFull
    }

    return @{
        RsyncExe = $toolPaths.RsyncExe
        TransportSSHExe = $toolPaths.TransportSSHExe
        SSHKeyPath = $sshKeyPath
    }
}

function Test-RepoBoundRsyncAvailable {
    param(
        [string]$RepoRoot = (Get-SyncRepoRoot),
        [hashtable]$SyncConfig
    )

    $tooling = Get-RepoBoundRsyncTooling -RepoRoot $RepoRoot -SyncConfig $SyncConfig
    return (Test-Path $tooling.RsyncExe) -and (Test-Path $tooling.TransportSSHExe)
}

function New-RepoBoundRsyncSshCommand {
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$SyncConfig,

        [string]$RepoRoot = (Get-SyncRepoRoot)
    )

    $tooling = Get-RepoBoundRsyncTooling -RepoRoot $RepoRoot -SyncConfig $SyncConfig
    $transportSsh = Convert-ToCwRsyncPath $tooling.TransportSSHExe
    $sshKey = Convert-ToCwRsyncPath $tooling.SSHKeyPath -PreserveShortName

    $portClause = ''
    if ($SyncConfig.ContainsKey('Port') -and $SyncConfig.Port -and $SyncConfig.Port -ne 22) {
        $portClause = " -p $($SyncConfig.Port)"
    }

    return "'$transportSsh' -i '$sshKey'$portClause -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3"
}

function Invoke-RepoBoundRsync {
    param(
        [Parameter(Mandatory=$true)]
        [string[]]$Arguments,

        [string]$RepoRoot = (Get-SyncRepoRoot),
        [hashtable]$SyncConfig
    )

    $tooling = Get-RepoBoundRsyncTooling -RepoRoot $RepoRoot -SyncConfig $SyncConfig
    if (-not (Test-Path $tooling.RsyncExe)) {
        throw "Repo-bound rsync.exe not found: $($tooling.RsyncExe)"
    }

    $output = & $tooling.RsyncExe @Arguments 2>&1
    return @{
        ExitCode = $LASTEXITCODE
        Output = @($output)
    }
}