Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-SyncSourceExists {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,

        [string]$Label = 'Source path'
    )

    if (-not (Test-Path $Path)) {
        throw "$Label does not exist: $Path"
    }
}

function Assert-SyncDirectoryNotEmpty {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,

        [string]$Reason = 'refusing risky sync with empty source'
    )

    Assert-SyncSourceExists -Path $Path -Label 'Source directory'

    $fileCount = (Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    if ($fileCount -eq 0) {
        throw ("{0}: {1}" -f $Reason, $Path)
    }
}

function Assert-SyncRemotePathPlausible {
    param(
        [Parameter(Mandatory=$true)]
        [string]$RemotePath,

        [switch]$AllowTestPath
    )

    $allowedPrefixes = @(
        '/srv/webapps/corapan/data',
        '/srv/webapps/corapan/media',
        '/srv/webapps/corapan/logs',
        '/srv/webapps/corapan/config'
    )

    if ($AllowTestPath) {
        $allowedPrefixes += '/srv/webapps/corapan/tmp_sync_test'
    }

    foreach ($prefix in $allowedPrefixes) {
        if ($RemotePath.StartsWith($prefix)) {
            return
        }
    }

    throw "Refusing implausible remote path: $RemotePath"
}

function Assert-TarSshAllowed {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Lane,

        [long]$TotalBytes = 0
    )

    if ($Lane -eq 'Media') {
        throw 'tar|ssh is not an allowed standard transport for Media lane.'
    }

    if ($TotalBytes -ge 1GB) {
        throw 'tar|ssh is not allowed as a standard path for large transfers.'
    }
}