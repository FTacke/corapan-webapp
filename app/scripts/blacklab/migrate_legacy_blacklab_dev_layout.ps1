<#
.SYNOPSIS
    Explicitly migrate legacy local BlackLab paths into the canonical dev layout.

.DESCRIPTION
    Merges relevant export payload from wrong-root or flat legacy paths into
    CORAPAN\data\blacklab\export and archives invalid BlackLab artifacts from
    app\data under app\data\_legacy_blacklab_invalid.

    Default mode is dry-run. Use -Apply to perform the migration.

.EXAMPLE
    .\scripts\blacklab\migrate_legacy_blacklab_dev_layout.ps1

.EXAMPLE
    .\scripts\blacklab\migrate_legacy_blacklab_dev_layout.ps1 -Apply

.EXAMPLE
    .\scripts\blacklab\migrate_legacy_blacklab_dev_layout.ps1 -Apply -Copy
#>

[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$Copy,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$webappRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$workspaceRoot = Split-Path -Parent $webappRoot
$workspaceDataRoot = Join-Path $workspaceRoot "data"
$webappDataRoot = Join-Path $webappRoot "data"

$blacklabRoot = Join-Path $workspaceDataRoot "blacklab"
$exportRoot = Join-Path $blacklabRoot "export"
$indexRoot = Join-Path $blacklabRoot "index"
$backupRoot = Join-Path $blacklabRoot "backups"
$quarantineRoot = Join-Path $blacklabRoot "quarantine"
$legacyInvalidRoot = Join-Path $quarantineRoot "webapp_legacy_blacklab_invalid_20260320"

$canonicalRoots = @($blacklabRoot, $exportRoot, $indexRoot, $backupRoot, $quarantineRoot, $legacyInvalidRoot)
foreach ($directory in $canonicalRoots) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

$plan = [System.Collections.Generic.List[object]]::new()

function Add-PlanItem {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Reason,
        [string]$Action
    )

    if (Test-Path $Source) {
        $plan.Add([pscustomobject]@{
            Source = $Source
            Destination = $Destination
            Reason = $Reason
            Action = $Action
        }) | Out-Null
    }
}

Add-PlanItem -Source (Join-Path $workspaceDataRoot "blacklab_export") -Destination $exportRoot -Reason "Merge flat root export into canonical export" -Action "merge-dir-contents"
Add-PlanItem -Source (Join-Path $webappDataRoot "blacklab\export") -Destination $exportRoot -Reason "Merge wrong-root export into canonical export" -Action "merge-dir-contents"
Add-PlanItem -Source (Join-Path $webappDataRoot "blacklab") -Destination (Join-Path $legacyInvalidRoot "blacklab_wrong_root") -Reason "Archive wrong-root active BlackLab tree" -Action "move-path"
Add-PlanItem -Source (Join-Path $webappDataRoot "_legacy_blacklab_unused") -Destination (Join-Path $legacyInvalidRoot "prior_unused_snapshot") -Reason "Keep previous isolated artifacts under explicit invalid path" -Action "move-path"

Get-ChildItem -Path $webappDataRoot -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $name = $_.Name
    if ($name -in @("blacklab", "_legacy_blacklab_invalid", "_legacy_blacklab_unused")) {
        return
    }
    if ($name -like "blacklab*") {
        Add-PlanItem -Source $_.FullName -Destination (Join-Path $legacyInvalidRoot $name) -Reason "Archive wrong-root BlackLab artifact" -Action "move-path"
    }
}

if ($plan.Count -eq 0) {
    Write-Host "No legacy BlackLab directories found under $workspaceDataRoot or $webappDataRoot" -ForegroundColor Green
    exit 0
}

Write-Host "Legacy BlackLab dev migration plan" -ForegroundColor Cyan
Write-Host "Workspace Root: $workspaceRoot" -ForegroundColor Gray
Write-Host "App Root: $webappRoot" -ForegroundColor Gray
Write-Host "Mode: $($(if ($Apply) { if ($Copy) { 'apply-copy' } else { 'apply-move' } } else { 'dry-run' }))" -ForegroundColor Gray
Write-Host ""

foreach ($item in $plan) {
    Write-Host ("- {0}`n  -> {1}`n  Action: {2}`n  Reason: {3}" -f $item.Source, $item.Destination, $item.Action, $item.Reason) -ForegroundColor Yellow
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "Dry-run only. Re-run with -Apply to perform the migration." -ForegroundColor Cyan
    exit 0
}

foreach ($item in $plan) {
    $destinationParent = Split-Path -Parent $item.Destination
    if ($destinationParent) {
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
    }

    if ($item.Action -eq "merge-dir-contents") {
        $entries = @(Get-ChildItem -Path $item.Source -Force -ErrorAction SilentlyContinue)
        foreach ($entry in $entries) {
            $destination = Join-Path $item.Destination $entry.Name
            if ((Test-Path $destination) -and -not $Force) {
                Write-Host ("Skipping existing canonical entry (use -Force to overwrite): {0}" -f $destination) -ForegroundColor Yellow
                continue
            }

            if ($Copy) {
                Copy-Item -Path $entry.FullName -Destination $destination -Recurse -Force
                Write-Host ("Copied {0} -> {1}" -f $entry.FullName, $destination) -ForegroundColor Green
            } else {
                Move-Item -Path $entry.FullName -Destination $destination -Force
                Write-Host ("Moved {0} -> {1}" -f $entry.FullName, $destination) -ForegroundColor Green
            }
        }
        continue
    }

    if ((Test-Path $item.Destination) -and -not $Force) {
        Write-Host ("Skipping existing destination (use -Force to replace): {0}" -f $item.Destination) -ForegroundColor Yellow
        continue
    }

    if ($Copy) {
        Copy-Item -Path $item.Source -Destination $item.Destination -Recurse -Force
        Write-Host ("Copied {0} -> {1}" -f $item.Source, $item.Destination) -ForegroundColor Green
    } else {
        Move-Item -Path $item.Source -Destination $item.Destination -Force
        Write-Host ("Moved {0} -> {1}" -f $item.Source, $item.Destination) -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Canonical active BlackLab layout is rooted at data/blacklab." -ForegroundColor Cyan
Write-Host "Wrong-root artifacts are archived under data/blacklab/quarantine/webapp_legacy_blacklab_invalid_20260320." -ForegroundColor Cyan