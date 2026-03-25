Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$guardsModule = Join-Path $PSScriptRoot 'guards.ps1'
if (Test-Path $guardsModule) {
    . $guardsModule
}

function Resolve-SyncTransport {
    param(
        [Parameter(Mandatory=$true)]
        [ValidateSet('Data', 'Media', 'BlackLab')]
        [string]$Lane,

        [bool]$RsyncAvailable = $true,
        [bool]$AllowTarSsh = $false,
        [bool]$AllowLegacyTarBase64 = $false,
        [long]$TotalBytes = 0
    )

    if ($Lane -in @('Data', 'Media')) {
        if ($RsyncAvailable) {
            return [PSCustomObject]@{ Name = 'rsync-cwrsync'; Fallback = $false }
        }

        if ($AllowLegacyTarBase64) {
            return [PSCustomObject]@{ Name = 'tar-base64-legacy'; Fallback = $true }
        }

        return [PSCustomObject]@{ Name = 'scp-legacy'; Fallback = $true }
    }

    if ($AllowTarSsh) {
        Assert-TarSshAllowed -Lane $Lane -TotalBytes $TotalBytes
        return [PSCustomObject]@{ Name = 'tar-ssh'; Fallback = $true }
    }

    return [PSCustomObject]@{ Name = 'scp-legacy'; Fallback = $true }
}