<#
Maintenance wrapper: Export -> Build -> Publish

- runs the canonical BlackLab sequence serially
- auto-detects the active app repository under the workspace
- supports WhatIf/DryRun (DryRun is forwarded to publish)
- writes a transcript log

Examples:
  .\publish_blacklab.ps1
  .\publish_blacklab.ps1 -AppRepoPath "C:\dev\corapan\app" -SkipExport
  .\publish_blacklab.ps1 -DryRun
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
  # Pfad zum aktiven versionierten App-Repo (lokal)
  [Parameter(Mandatory = $false)]
  [ValidateNotNullOrEmpty()]
  [Alias("WebappRepoPath")]
  [string]$AppRepoPath,

  # Optional: Python executable
  [Parameter(Mandatory = $false)]
  [string]$PythonExe = "python",

  # Optional: Export-Script
  [Parameter(Mandatory = $false)]
  [string]$ExportScriptPath = (Join-Path (Split-Path -Parent $PSScriptRoot) "_1_blacklab\blacklab_export.py"),

  # Optional: Build-Script im Webapp-Repo (lokaler Build)
  [Parameter(Mandatory = $false)]
  [string]$BuildScriptRelPath = "scripts\blacklab\build_blacklab_index.ps1",

  # Optional: Publish-Script im Webapp-Repo
  [Parameter(Mandatory = $false)]
  [string]$PublishScriptRelPath = "scripts\deploy_sync\tasks\publish_blacklab_index.ps1",

  # Build-Parameter (wird an build_blacklab_index.ps1 weitergegeben)
  [Parameter(Mandatory = $false)]
  [switch]$Force,

  [Parameter(Mandatory = $false)]
  [switch]$Activate,

  # Pipeline switches
  [Parameter(Mandatory = $false)]
  [switch]$SkipExport,

  [Parameter(Mandatory = $false)]
  [switch]$SkipBuild,

  [Parameter(Mandatory = $false)]
  [switch]$SkipPublish,

  # Publish Dry-Run (wird an publish_blacklab_index.ps1 weitergereicht)
  [Parameter(Mandatory = $false)]
  [switch]$DryRun,

  # Backup-Retention (Publish)
  [Parameter(Mandatory = $false)]
  [ValidateRange(0, 100)]
  [int]$KeepBackups = 2,

  [Parameter(Mandatory = $false)]
  [switch]$NoBackupCleanup,

  # Logging
  [Parameter(Mandatory = $false)]
  [string]$LogDir = (Join-Path $PSScriptRoot "_logs")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$WorkspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$RemoteAppRoot = "/srv/webapps/corapan/app"
$RemoteBlackLabDataRoot = "/srv/webapps/corapan/data/blacklab"

function Resolve-FullPath([string]$PathLike) {
  if ([System.IO.Path]::IsPathRooted($PathLike)) {
    return (Resolve-Path -LiteralPath $PathLike).Path
  }
  return (Resolve-Path -LiteralPath (Join-Path (Get-Location) $PathLike)).Path
}

function Test-AppRepoRoot([string]$CandidatePath) {
  if (-not (Test-Path -LiteralPath $CandidatePath -PathType Container)) {
    return $false
  }

  $requiredFiles = @(
    "src\scripts\blacklab_index_creation.py",
    "scripts\blacklab\build_blacklab_index.ps1",
    "scripts\deploy_sync\tasks\publish_blacklab_index.ps1"
  )

  foreach ($relativePath in $requiredFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $CandidatePath $relativePath) -PathType Leaf)) {
      return $false
    }
  }

  return $true
}

function Resolve-AppRepoRoot([string]$CandidatePath, [string]$WorkspaceRootPath) {
  $candidates = @()
  if ($CandidatePath) {
    $candidates += (Resolve-FullPath $CandidatePath)
  }
  else {
    $defaultApp = Join-Path $WorkspaceRootPath "app"
    $candidates += $defaultApp
  }

  foreach ($candidate in $candidates) {
    if (Test-AppRepoRoot $candidate) {
      return $candidate
    }
  }

  throw "Could not resolve active app repository. Checked: $($candidates -join ', ')"
}

function Assert-File([string]$p, [string]$label) {
  if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {
    throw "Missing ${label}: $p"
  }
}

function Assert-Dir([string]$p, [string]$label) {
  if (-not (Test-Path -LiteralPath $p -PathType Container)) {
    throw "Missing ${label}: $p"
  }
}

function Invoke-Step {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][scriptblock]$Action
  )
  $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  Write-Host "== [$ts] $Name =="

  & $Action
}

# --- Prep paths ---
$AppRepoPath = Resolve-AppRepoRoot -CandidatePath $AppRepoPath -WorkspaceRootPath $WorkspaceRoot
Assert-Dir $AppRepoPath "AppRepoPath"

$ExportScriptPath = (Resolve-Path -LiteralPath $ExportScriptPath).Path
Assert-File $ExportScriptPath "ExportScriptPath"

$BuildScriptPath  = Join-Path $AppRepoPath $BuildScriptRelPath
$PublishScriptPath = Join-Path $AppRepoPath $PublishScriptRelPath

Assert-File $BuildScriptPath "BuildScriptPath"
Assert-File $PublishScriptPath "PublishScriptPath"

# --- Logging ---
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$logFile = Join-Path $LogDir ("publish_blacklab_wrapper_{0}.log" -f $stamp)

# Tee all output (PowerShell transcript is reliable for PS output; external process output is also captured in host stream)
Start-Transcript -Path $logFile -Force | Out-Null

try {
  Write-Host "Wrapper:"
  Write-Host "  Workspace root:  $WorkspaceRoot"
  Write-Host "  App repo:        $AppRepoPath"
  Write-Host "  Export script:   $ExportScriptPath"
  Write-Host "  Build script:    $BuildScriptPath"
  Write-Host "  Publish script:  $PublishScriptPath"
  Write-Host "  Remote app:      $RemoteAppRoot"
  Write-Host "  Remote BL data:  $RemoteBlackLabDataRoot"
  Write-Host "  Log file:        $logFile"
  Write-Host "  Workflow:        export -> build -> publish (serial only)"
  Write-Host ""

  # --- Step 1: Export ---
  if (-not $SkipExport) {
    Invoke-Step -Name "EXPORT (python $ExportScriptPath)" -Action {
      $exportArgs = @(
        $ExportScriptPath,
        "--workspace-root", $WorkspaceRoot,
        "--app-repo-path", $AppRepoPath
      )

      if ($PSCmdlet.ShouldProcess("Export", "$PythonExe $($exportArgs -join ' ')")) {
        & $PythonExe @exportArgs
        $rc = $LASTEXITCODE
        if ($rc -ne 0) { throw "EXPORT failed with exit code $rc" }
      } else {
        Write-Host "[WhatIf] Would run: $PythonExe $($exportArgs -join ' ')"
      }
    }
  } else {
    Write-Host "== Skipping EXPORT =="
  }

  # --- Step 2: Build (local) ---
  if (-not $SkipBuild) {
    Invoke-Step -Name "BUILD (local index build in webapp repo)" -Action {
      Push-Location $AppRepoPath
      try {
        # Use & directly to invoke the script in the current PS context instead of spawning a new process
        # This avoids pwsh/powershell lookup issues
        $BuildScriptArgs = @()

        # Pass through known flags (only if present)
        if ($Force.IsPresent)   { $BuildScriptArgs += @("-Force") }

        # Some build scripts expect -Activate:$false style; we support both by only sending if user set.
        if ($PSBoundParameters.ContainsKey("Activate")) {
          # Default is false if user passed -Activate:$false; but in PS, switch is either present or not.
          # If user wants activation, they pass -Activate. Otherwise not.
          $BuildScriptArgs += @("-Activate:$true")
        } else {
          $BuildScriptArgs += @("-Activate:$false")
        }

        if ($PSCmdlet.ShouldProcess("Build", "$BuildScriptPath $($BuildScriptArgs -join ' ')")) {
          & $BuildScriptPath @BuildScriptArgs
          $rc = $LASTEXITCODE
          if ($rc -ne 0) { throw "BUILD failed with exit code $rc" }
        } else {
          Write-Host "[WhatIf] Would run in $AppRepoPath`: $BuildScriptPath $($BuildScriptArgs -join ' ')"
        }
      } finally {
        Pop-Location
      }
    }
  } else {
    Write-Host "== Skipping BUILD =="
  }

  # --- Step 3: Publish (prod) ---
  if (-not $SkipPublish) {
    Invoke-Step -Name "PUBLISH (upload + validate + atomic swap on prod)" -Action {
      Push-Location $AppRepoPath
      try {
        # Build parameter hashtable for direct invocation
        $PublishParams = @{
          DataDir = $RemoteBlackLabDataRoot
          ConfigDir = "$RemoteAppRoot/app/config/blacklab"
        }
        
        # Pass through flags that were explicitly set by user
        if ($DryRun.IsPresent) { $PublishParams["DryRun"] = $true }
        if ($PSBoundParameters.ContainsKey("KeepBackups")) { $PublishParams["KeepBackups"] = $KeepBackups }
        if ($NoBackupCleanup.IsPresent) { $PublishParams["NoBackupCleanup"] = $true }

        $paramList = ($PublishParams.Keys | ForEach-Object { "-$_" }) -join " "
        if ($PSCmdlet.ShouldProcess("Publish", "$PublishScriptPath $paramList")) {
          & $PublishScriptPath @PublishParams
          $rc = $LASTEXITCODE
          if ($rc -ne 0) { throw "PUBLISH failed with exit code $rc" }
        } else {
          Write-Host "[WhatIf] Would run in $AppRepoPath`: $PublishScriptPath $paramList"
        }
      } finally {
        Pop-Location
      }
    }
  } else {
    Write-Host "== Skipping PUBLISH =="
  }

  Write-Host ""
  Write-Host "SUCCESS: Export/Build/Publish wrapper completed."
  Write-Host "Log: $logFile"
  exit 0

} catch {
  Write-Error $_
  Write-Host ""
  Write-Host "FAILED. Log: $logFile"
  exit 1
} finally {
  try { Stop-Transcript | Out-Null } catch {}
}
