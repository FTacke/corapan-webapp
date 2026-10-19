$ErrorActionPreference = "Stop"
Set-Location "C:\dev\corapan"

$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"

$stamp = Get-Date -Format "yyyyMMddTHHmmss"
$logDir = "maintenance_pipelines\_0_json\logs\annotation"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$transcriptLog = Join-Path $logDir "full_annotation_$stamp.transcript.txt"

Start-Transcript -Path $transcriptLog

try {
    .venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py `
        --force `
        --require-spacy `
        --check-corpus-token-ids `
        --verbose
}
finally {
    Stop-Transcript
}
