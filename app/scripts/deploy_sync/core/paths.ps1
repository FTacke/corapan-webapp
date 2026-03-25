Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-SyncRepoRoot {
    param(
        [string]$AnchorPath = $PSScriptRoot
    )

    return Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $AnchorPath))
}

function Get-SyncToolPaths {
    param(
        [string]$RepoRoot = (Get-SyncRepoRoot)
    )

    return @{
        RsyncExe         = Join-Path $RepoRoot 'tools\cwrsync\bin\rsync.exe'
        TransportSSHExe  = Join-Path $RepoRoot 'tools\cwrsync\bin\ssh.exe'
        TransportKeygen  = Join-Path $RepoRoot 'tools\cwrsync\bin\ssh-keygen.exe'
        OpenSSHExe       = 'C:\Windows\System32\OpenSSH\ssh.exe'
        ScpExe           = 'C:\Windows\System32\OpenSSH\scp.exe'
        TarExe           = 'C:\Windows\System32\tar.exe'
    }
}

function Get-SyncLogRoot {
    param(
        [string]$RepoRoot = (Get-SyncRepoRoot)
    )

    $logRoot = Join-Path $RepoRoot 'scripts\deploy_sync\_logs'
    if (-not (Test-Path $logRoot)) {
        New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
    }

    return $logRoot
}

function Get-SyncSummaryFilePath {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Lane,

        [string]$RepoRoot = (Get-SyncRepoRoot)
    )

    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    return Join-Path (Get-SyncLogRoot -RepoRoot $RepoRoot) ("{0}_{1}.json" -f $Lane, $stamp)
}