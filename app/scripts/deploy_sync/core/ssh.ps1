Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pathsModule = Join-Path $PSScriptRoot 'paths.ps1'
if (Test-Path $pathsModule) {
    . $pathsModule
}

function Get-SyncOpenSshExecutable {
    param(
        [hashtable]$SSHConfig
    )

    if ($SSHConfig -and $SSHConfig.ContainsKey('SSHExe') -and $SSHConfig.SSHExe) {
        return $SSHConfig.SSHExe
    }

    return (Get-SyncToolPaths).OpenSSHExe
}

function Get-SyncOpenSshArgs {
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$SSHConfig,

        [switch]$ForScp
    )

    $args = @(
        '-i', $SSHConfig.SSHKeyPath,
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ServerAliveInterval=60',
        '-o', 'ServerAliveCountMax=3',
        '-o', 'ConnectTimeout=30'
    )

    if ($SSHConfig.Port -and $SSHConfig.Port -ne 22) {
        if ($ForScp) {
            $args += @('-P', $SSHConfig.Port)
        }
        else {
            $args += @('-p', $SSHConfig.Port)
        }
    }

    return $args
}

function Invoke-SyncOpenSshCommand {
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$SSHConfig,

        [Parameter(Mandatory=$true)]
        [string]$Command,

        [switch]$PassThru,
        [switch]$NoThrow,
        [switch]$DryRun
    )

    $sshExe = Get-SyncOpenSshExecutable -SSHConfig $SSHConfig
    $sshArgs = Get-SyncOpenSshArgs -SSHConfig $SSHConfig
    $sshArgs += @("$($SSHConfig.User)@$($SSHConfig.Hostname)", $Command)

    if ($DryRun -or ($SSHConfig.ContainsKey('DryRun') -and $SSHConfig.DryRun)) {
        Write-Host "  [DRY-RUN] SSH: $Command" -ForegroundColor DarkYellow
        return $(if ($PassThru) { '' } else { $true })
    }

    if ($PassThru) {
        $result = & $sshExe @sshArgs 2>&1
        if ($LASTEXITCODE -ne 0 -and -not $NoThrow) {
            throw "SSH command failed (exit code $LASTEXITCODE): $result"
        }
        return $result
    }

    & $sshExe @sshArgs
    if ($LASTEXITCODE -ne 0 -and -not $NoThrow) {
        throw "SSH command failed with exit code $LASTEXITCODE"
    }

    return ($LASTEXITCODE -eq 0)
}

function Invoke-SyncRemoteBash {
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$SSHConfig,

        [Parameter(Mandatory=$true)]
        [string]$Script,

        [switch]$PassThru,
        [switch]$NoThrow,
        [switch]$DryRun
    )

    $sshExe = Get-SyncOpenSshExecutable -SSHConfig $SSHConfig
    $sshArgs = Get-SyncOpenSshArgs -SSHConfig $SSHConfig
    $sshArgs += @("$($SSHConfig.User)@$($SSHConfig.Hostname)", 'bash', '-s')

    if ($DryRun -or ($SSHConfig.ContainsKey('DryRun') -and $SSHConfig.DryRun)) {
        Write-Host '  [DRY-RUN] Remote Bash Script:' -ForegroundColor DarkYellow
        $Script -split "`n" | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
        return $(if ($PassThru) { '' } else { $true })
    }

    if ($PassThru) {
        $result = $Script | & $sshExe @sshArgs 2>&1
        if ($LASTEXITCODE -ne 0 -and -not $NoThrow) {
            throw "Remote bash script failed (exit code $LASTEXITCODE): $result"
        }
        return $result
    }

    $Script | & $sshExe @sshArgs
    if ($LASTEXITCODE -ne 0 -and -not $NoThrow) {
        throw "Remote bash script failed with exit code $LASTEXITCODE"
    }

    return ($LASTEXITCODE -eq 0)
}

function Invoke-SyncScpLegacy {
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$SSHConfig,

        [Parameter(Mandatory=$true)]
        [string]$LocalPath,

        [Parameter(Mandatory=$true)]
        [string]$RemotePath,

        [switch]$Recursive,
        [switch]$DryRun
    )

    if (-not (Test-Path $LocalPath)) {
        throw "Local path does not exist: $LocalPath"
    }

    $toolPaths = Get-SyncToolPaths
    $scpArgs = @('-O')
    $scpArgs += Get-SyncOpenSshArgs -SSHConfig $SSHConfig -ForScp
    if ($Recursive) {
        $scpArgs += '-r'
    }
    $scpArgs += @($LocalPath, "$($SSHConfig.User)@$($SSHConfig.Hostname):$RemotePath")

    if ($DryRun -or ($SSHConfig.ContainsKey('DryRun') -and $SSHConfig.DryRun)) {
        Write-Host "  [DRY-RUN] SCP -O: $LocalPath -> $($SSHConfig.User)@$($SSHConfig.Hostname):$RemotePath" -ForegroundColor DarkYellow
        return $true
    }

    & $toolPaths.ScpExe @scpArgs
    if ($LASTEXITCODE -ne 0) {
        throw "SCP -O failed with exit code $LASTEXITCODE"
    }

    return $true
}