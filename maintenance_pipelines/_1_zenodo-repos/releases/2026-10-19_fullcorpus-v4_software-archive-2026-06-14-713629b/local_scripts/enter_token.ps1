# Prompts for the Zenodo token (hidden input) and stores it DPAPI-encrypted for the current Windows user only.
$dir = Join-Path $env:LOCALAPPDATA 'corapan_zenodo'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Write-Host 'Zenodo-Token einfuegen (Eingabe bleibt unsichtbar), dann Enter:'
$s = Read-Host -AsSecureString
if ($s.Length -lt 20) { Write-Host 'Eingabe zu kurz - nichts gespeichert.'; Read-Host 'Enter zum Schliessen'; exit 1 }
$s | ConvertFrom-SecureString | Set-Content -Encoding ascii -Path (Join-Path $dir 'token.dpapi')
Write-Host 'Gespeichert (verschluesselt, nur fuer dein Windows-Konto lesbar). Du kannst das Fenster schliessen.'
Read-Host 'Enter zum Schliessen'
