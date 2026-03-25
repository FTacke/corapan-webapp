param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$SkipStatistics,
    [switch]$IncludeAuthDb,
    [switch]$IUnderstandThisWillOverwriteProductionState
)

$legacyScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'sync_data.ps1'
& $legacyScript @PSBoundParameters
exit $LASTEXITCODE