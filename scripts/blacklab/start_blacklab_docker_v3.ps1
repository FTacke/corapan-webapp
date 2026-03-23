 $implementation = Join-Path $PSScriptRoot "..\..\app\scripts\blacklab\start_blacklab_docker_v3.ps1"
if (-not (Test-Path $implementation)) {
	throw "Could not resolve BlackLab start implementation: $implementation"
}

& $implementation @args
exit $LASTEXITCODE