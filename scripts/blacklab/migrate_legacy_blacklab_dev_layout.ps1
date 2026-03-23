 $implementation = Join-Path $PSScriptRoot "..\..\app\scripts\blacklab\migrate_legacy_blacklab_dev_layout.ps1"
if (-not (Test-Path $implementation)) {
	throw "Could not resolve BlackLab migration implementation: $implementation"
}

& $implementation @args
exit $LASTEXITCODE