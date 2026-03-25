param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot,
    [switch]$Force,
    [switch]$ForceMP3,
    [switch]$DryRun
)

$legacyScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'sync_media.ps1'
& $legacyScript @PSBoundParameters
exit $LASTEXITCODE