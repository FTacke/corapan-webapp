Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$pathsModule = Join-Path $PSScriptRoot 'paths.ps1'
if (Test-Path $pathsModule) {
    . $pathsModule
}

function New-SyncRunRecord {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Lane,

        [Parameter(Mandatory=$true)]
        [string]$Source,

        [Parameter(Mandatory=$true)]
        [string]$Target,

        [string]$Transport = 'unknown',
        [bool]$DryRun = $false,
        [string]$RepoRoot = (Get-SyncRepoRoot)
    )

    return [ordered]@{
        lane = $Lane
        source = $Source
        target = $Target
        transport = $Transport
        dryRun = $DryRun
        startTime = (Get-Date).ToString('o')
        endTime = $null
        exitCode = $null
        noChange = $false
        changeCount = 0
        deleteCount = 0
        fallbackUsed = $false
        notes = @()
        details = @()
        summaryFile = (Get-SyncSummaryFilePath -Lane $Lane -RepoRoot $RepoRoot)
    }
}

function Add-SyncRunNote {
    param(
        [Parameter(Mandatory=$true)]
        [System.Collections.IDictionary]$Run,

        [Parameter(Mandatory=$true)]
        [string]$Note
    )

    $Run.notes += $Note
}

function Add-SyncRunDetail {
    param(
        [Parameter(Mandatory=$true)]
        [System.Collections.IDictionary]$Run,

        [Parameter(Mandatory=$true)]
        $Detail
    )

    $Run.details += $Detail
}

function Complete-SyncRunRecord {
    param(
        [Parameter(Mandatory=$true)]
        [System.Collections.IDictionary]$Run,

        [Parameter(Mandatory=$true)]
        [int]$ExitCode,

        [bool]$NoChange = $false,
        [int]$ChangeCount = 0,
        [int]$DeleteCount = 0,
        [bool]$FallbackUsed = $false
    )

    $Run.endTime = (Get-Date).ToString('o')
    $Run.exitCode = $ExitCode
    $Run.noChange = $NoChange
    $Run.changeCount = $ChangeCount
    $Run.deleteCount = $DeleteCount
    $Run.fallbackUsed = $FallbackUsed

    $json = $Run | ConvertTo-Json -Depth 8
    $json | Out-File -FilePath $Run.summaryFile -Encoding utf8

    return $Run.summaryFile
}