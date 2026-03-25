param(
    [Alias('Host')]
    [string]$Hostname,
    [string]$User,
    [int]$Port = 22,
    [string]$DataDir,
    [string]$ConfigDir = '/srv/webapps/corapan/app/config/blacklab',
    [switch]$DryRun,
    [int]$KeepBackups = 2,
    [switch]$NoBackupCleanup
)

$legacyScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'publish_blacklab_index.ps1'
& $legacyScript @PSBoundParameters
exit $LASTEXITCODE