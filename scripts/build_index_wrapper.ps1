# Temporary wrapper to run build script with Java in PATH
$env:Path = "C:\Program Files\Microsoft\jdk-17.0.17.10-hotspot\bin;$env:Path"

Write-Host "Java verfuegbar: $((Get-Command java -ErrorAction SilentlyContinue).Source)" -ForegroundColor Green
Write-Host ""

.\scripts\build_blacklab_index.ps1 -Force
