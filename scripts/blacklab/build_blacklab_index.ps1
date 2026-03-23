 $implementation = Join-Path $PSScriptRoot "..\..\app\scripts\blacklab\build_blacklab_index.ps1"
if (-not (Test-Path $implementation)) {
	throw "Could not resolve BlackLab build implementation: $implementation"
}

& $implementation @args
exit $LASTEXITCODE