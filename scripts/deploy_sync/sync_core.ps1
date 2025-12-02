# =============================================================================
# CO.RA.PAN Sync Core Library
# =============================================================================
#
# Gemeinsame Funktionen fuer Data- und Media-Synchronisation Dev -> Prod
#
# Funktionen:
#   - New-DirectoryManifest: Erzeugt JSON-Manifest fuer lokales Verzeichnis
#   - Compare-Manifests: Vergleicht lokales und remote Manifest
#   - Sync-DirTarBase64: Synchronisiert Verzeichnis via tar+base64+SSH (Fallback)
#   - Sync-DirectoryWithRsync: Synchronisiert Verzeichnis via rsync (bevorzugt)
#   - Sync-DirectoryWithDiff: Vollstaendiger Sync mit Diff-Vorschau
#
# Transport-Entscheidung:
#   - Wenn rsync lokal verfuegbar und lauffaehig -> rsync (echter Delta-Sync)
#   - Sonst -> tar+base64 Fallback
#
# rsync Pfad-Logik (Windows/cwRsync):
#   - cwRsync erwartet Cygwin-Pfade: /cygdrive/c/dev/...
#   - Die Funktion Convert-ToRsyncPath konvertiert automatisch.
#   - cwRsync-Pfad: C:\dev\corapan-webapp\tools\cwrsync\bin
#
# SSH-Authentifizierung:
#   - Dedizierter Deploy-Key: $env:USERPROFILE\.ssh\marele (OHNE Passphrase)
#   - Der Key ist passwortlos fuer automatisierte Sync-/Deploy-Operationen
#   - Kein ssh-agent erforderlich
#
# Fehlerhandling:
#   - rsync-Fehler sind kritisch und fuehren zum Abbruch
#   - Manifest-/Post-Sync-Fehler geben Warnung aus, aber kein Fehler-Exit
#
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -----------------------------------------------------------------------------
# Konfiguration
# -----------------------------------------------------------------------------

$script:SyncConfig = @{
    ServerHost     = "marele.online.uni-marburg.de"
    ServerIP       = "137.248.186.51"
    ServerUser     = "root"
    # Deploy-Key ohne Passphrase - 8.3-Format fuer cwRsync-Kompatibilitaet
    SSHKeyPath     = "C:\Users\FELIXT~1\.ssh\marele"
    # Voller Pfad zum Key (fuer Windows OpenSSH)
    SSHKeyPathFull = "$env:USERPROFILE\.ssh\marele"
    # Windows OpenSSH fuer direkte SSH-Aufrufe
    WindowsSSHPath = "C:\Windows\System32\OpenSSH\ssh.exe"
    AppUser        = "hrzadmin"
    AppUid         = 1000
    AppGid         = 1000
    CwRsyncPath    = "C:\dev\corapan-webapp\tools\cwrsync\bin"
}

# Flag um rsync-Verfuegbarkeits-Log nur einmal auszugeben
$script:RsyncAvailabilityLogged = $false

# -----------------------------------------------------------------------------
# rsync-Verfuegbarkeit und Pfadlogik
# -----------------------------------------------------------------------------

function Test-RsyncAvailable {
    [OutputType([bool])]
    param()
    
    # Stelle sicher, dass cwRsync im PATH ist
    if ($script:SyncConfig.CwRsyncPath -and (Test-Path $script:SyncConfig.CwRsyncPath)) {
        if ($env:Path -notlike "*$($script:SyncConfig.CwRsyncPath)*") {
            $env:Path = "$($script:SyncConfig.CwRsyncPath);$env:Path"
        }
    }
    
    try {
        $cmd = Get-Command rsync -ErrorAction Stop
        
        if (-not $script:RsyncAvailabilityLogged) {
            Write-Host "[Sync] rsync verfuegbar ($($cmd.Source)) - rsync-Modus aktiv" -ForegroundColor DarkGreen
            $script:RsyncAvailabilityLogged = $true
        }
        return $true
    }
    catch {
        if (-not $script:RsyncAvailabilityLogged) {
            Write-Host "[Sync] rsync nicht gefunden - verwende tar+base64 Fallback" -ForegroundColor DarkYellow
            $script:RsyncAvailabilityLogged = $true
        }
        return $false
    }
}

function Convert-ToRsyncPath {
    param(
        [Parameter(Mandatory=$true)]
        [string]$WindowsPath,
        
        [switch]$PreserveShortName
    )
    
    if ($PreserveShortName) {
        # Behalte 8.3-Namen bei (wichtig fuer Pfade mit Leerzeichen)
        $path = $WindowsPath
    }
    else {
        # Volle Normalisierung (loest 8.3-Namen auf)
        $path = [System.IO.Path]::GetFullPath($WindowsPath)
    }
    
    # Laufwerksbuchstabe und Rest trennen
    if ($path -match '^([a-zA-Z]):(.*)$') {
        $drive = $Matches[1].ToLower()
        $rest = $Matches[2] -replace '\\', '/'
        
        # cwRsync / Cygwin-Style Pfad
        return "/cygdrive/$drive$rest"
    }
    
    # Falls kein Laufwerkspfad, einfach Backslashes ersetzen
    return $path -replace '\\', '/'
}

function Sync-DirectoryWithRsync {
    param(
        [Parameter(Mandatory=$true)]
        [string]$LocalBasePath,
        
        [Parameter(Mandatory=$true)]
        [string]$RemoteBasePath,
        
        [Parameter(Mandatory=$true)]
        [string]$DirName
    )
    
    $localPath = Join-Path $LocalBasePath $DirName
    $remotePath = "$RemoteBasePath/$DirName"
    
    if (-not (Test-Path $localPath)) {
        throw "Lokales Verzeichnis existiert nicht: $localPath"
    }
    
    $server = "$($script:SyncConfig.ServerUser)@$($script:SyncConfig.ServerHost)"
    
    Write-Host "    [rsync] $DirName -> ${server}:$remotePath" -ForegroundColor Cyan
    
    # Konvertiere lokalen Pfad fuer rsync (mit trailing slash fuer Inhalt)
    $rsyncSource = (Convert-ToRsyncPath $localPath) + "/"
    
    # cwRsync verwendet sein eigenes ssh - Key-Pfad in Cygwin-Format
    # Verwende 8.3-Pfad um Leerzeichen zu vermeiden
    $sshKeyCygwin = Convert-ToRsyncPath $script:SyncConfig.SSHKeyPath -PreserveShortName
    
    # SSH-Optionen: Key ohne Passphrase, Timeout-Schutz
    $sshCmd = "ssh -i '$sshKeyCygwin' -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3"
    
    # rsync-Befehl zusammenbauen
    $rsyncArgs = @(
        "-avz",
        "--delete",
        "-e", $sshCmd,
        "--exclude", "blacklab_index",
        "--exclude", "blacklab_index.backup",
        "--exclude", "stats_temp",
        "--exclude", "db",
        "$rsyncSource",
        "${server}:$remotePath/"
    )
    
    Write-Host "    Fuehre aus: rsync $($rsyncArgs -join ' ')" -ForegroundColor DarkGray
    
    # rsync ausfuehren
    & rsync @rsyncArgs
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        throw "rsync fuer $DirName fehlgeschlagen (Exit-Code: $exitCode)"
    }
    
    Write-Host "    [rsync] $DirName - OK" -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# Helper: SSH-Befehl ausfuehren (Windows OpenSSH)
# -----------------------------------------------------------------------------

function Invoke-SSHCommand {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command,
        [switch]$PassThru,
        [switch]$NoThrow
    )
    
    # Verwende Windows OpenSSH mit dem passwortlosen Deploy-Key
    $sshExe = $script:SyncConfig.WindowsSSHPath
    $sshKeyPath = $script:SyncConfig.SSHKeyPathFull
    
    $sshArgs = @(
        "-i", $sshKeyPath,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=60",
        "-o", "ServerAliveCountMax=3",
        "-o", "ConnectTimeout=30",
        "$($script:SyncConfig.ServerUser)@$($script:SyncConfig.ServerHost)",
        $Command
    )
    
    if ($PassThru) {
        $result = & $sshExe @sshArgs 2>&1
        if ($LASTEXITCODE -ne 0) {
            if ($NoThrow) {
                return $null
            }
            throw "SSH command failed (exit code $LASTEXITCODE): $result"
        }
        return $result
    }
    else {
        & $sshExe @sshArgs
        if ($LASTEXITCODE -ne 0) {
            if ($NoThrow) {
                return $false
            }
            throw "SSH command failed with exit code $LASTEXITCODE"
        }
        return $true
    }
}

# -----------------------------------------------------------------------------
# New-DirectoryManifest: Erzeugt JSON-Manifest fuer lokales Verzeichnis
# -----------------------------------------------------------------------------

function New-DirectoryManifest {
    param(
        [Parameter(Mandatory=$true)]
        [string]$BasePath,
        
        [Parameter(Mandatory=$true)]
        [string]$DirName
    )
    
    $fullPath = Join-Path $BasePath $DirName
    
    if (-not (Test-Path $fullPath)) {
        throw "Verzeichnis nicht gefunden: $fullPath"
    }
    
    $manifest = @()
    $files = Get-ChildItem -Path $fullPath -Recurse -File -ErrorAction SilentlyContinue
    
    foreach ($file in $files) {
        $relativePath = $file.FullName.Substring($fullPath.Length + 1) -replace '\\', '/'
        $mtime = [int][double]::Parse(
            (Get-Date $file.LastWriteTimeUtc -UFormat %s)
        )
        
        $manifest += [PSCustomObject]@{
            path  = "$DirName/$relativePath"
            size  = $file.Length
            mtime = $mtime
        }
    }
    
    return $manifest
}

# -----------------------------------------------------------------------------
# Get-RemoteManifest: Liest oder erzeugt Manifest auf dem Server
# -----------------------------------------------------------------------------

function Get-RemoteManifest {
    param(
        [Parameter(Mandatory=$true)]
        [string]$RemoteBasePath,
        
        [Parameter(Mandatory=$true)]
        [string]$DirName
    )
    
    $syncStateDir = "$RemoteBasePath/.sync_state"
    $manifestFile = "$syncStateDir/${DirName}_manifest.json"
    $targetDir = "$RemoteBasePath/$DirName"
    
    # Python-Skript zum Erzeugen des Manifests auf dem Server
    $pythonScript = @"
import json
import os
import sys

base_path = '$targetDir'
manifest = []

if os.path.exists(base_path):
    for root, dirs, files in os.walk(base_path):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, os.path.dirname(base_path))
            stat = os.stat(full)
            manifest.append({
                'path': rel.replace('\\\\', '/'),
                'size': stat.st_size,
                'mtime': int(stat.st_mtime)
            })

print(json.dumps(manifest))
"@
    
    $escapedPython = $pythonScript -replace "'", "'\\''"
    $command = "python3 -c '$escapedPython'"
    
    try {
        $result = Invoke-SSHCommand -Command $command -PassThru
        $manifest = $result | ConvertFrom-Json
        # Sicherstellen dass immer ein Array zurueckgegeben wird
        if ($null -eq $manifest) {
            return ,@()
        }
        # Einzelnes Objekt in Array wrappen
        if ($manifest -isnot [array]) {
            return ,@($manifest)
        }
        return ,$manifest
    }
    catch {
        Write-Host "    Info: Konnte Remote-Manifest nicht lesen (Verzeichnis evtl. neu)" -ForegroundColor DarkGray
        return ,@()
    }
}

# -----------------------------------------------------------------------------
# Compare-Manifests: Vergleicht lokales und remote Manifest
# -----------------------------------------------------------------------------

function Compare-Manifests {
    param(
        [Parameter(Mandatory=$true)]
        [AllowNull()]
        [AllowEmptyCollection()]
        $LocalManifest,
        
        [Parameter(Mandatory=$true)]
        [AllowNull()]
        [AllowEmptyCollection()]
        $RemoteManifest
    )
    
    # Null-Safety: Sicherstellen dass wir mit Arrays arbeiten
    if ($null -eq $LocalManifest) { $LocalManifest = @() }
    if ($null -eq $RemoteManifest) { $RemoteManifest = @() }
    
    # Hashmaps fuer schnellen Zugriff
    $localMap = @{}
    foreach ($item in $LocalManifest) {
        if ($null -ne $item) { $localMap[$item.path] = $item }
    }
    
    $remoteMap = @{}
    foreach ($item in $RemoteManifest) {
        if ($null -ne $item) { $remoteMap[$item.path] = $item }
    }
    
    $newFiles = @()
    $changedFiles = @()
    $deletedFiles = @()
    
    # Neue und geaenderte Dateien finden
    foreach ($path in $localMap.Keys) {
        if (-not $remoteMap.ContainsKey($path)) {
            $newFiles += $path
        }
        else {
            $local = $localMap[$path]
            $remote = $remoteMap[$path]
            # Geaendert wenn Groesse oder mtime unterschiedlich
            if ($local.size -ne $remote.size -or $local.mtime -ne $remote.mtime) {
                $changedFiles += $path
            }
        }
    }
    
    # Geloeschte Dateien finden (auf Remote, nicht mehr lokal)
    foreach ($path in $remoteMap.Keys) {
        if (-not $localMap.ContainsKey($path)) {
            $deletedFiles += $path
        }
    }
    
    # Zusammenfassung erstellen
    $summaryLines = @()
    $summaryLines += "    Dateien lokal: $($LocalManifest.Count), remote: $($RemoteManifest.Count)"
    $summaryLines += "    Neu: $($newFiles.Count), Geaendert: $($changedFiles.Count), Geloescht: $($deletedFiles.Count)"
    
    # Beispieldateien anzeigen (max 3 pro Kategorie)
    if ($newFiles.Count -gt 0) {
        $examples = ($newFiles | Select-Object -First 3) -join ", "
        if ($newFiles.Count -gt 3) { $examples += ", ..." }
        $summaryLines += "      + Neu: $examples"
    }
    if ($changedFiles.Count -gt 0) {
        $examples = ($changedFiles | Select-Object -First 3) -join ", "
        if ($changedFiles.Count -gt 3) { $examples += ", ..." }
        $summaryLines += "      ~ Geaendert: $examples"
    }
    if ($deletedFiles.Count -gt 0) {
        $examples = ($deletedFiles | Select-Object -First 3) -join ", "
        if ($deletedFiles.Count -gt 3) { $examples += ", ..." }
        $summaryLines += "      - Geloescht: $examples"
    }
    
    $summary = $summaryLines -join "`n"
    
    return [PSCustomObject]@{
        New        = $newFiles
        Changed    = $changedFiles
        Deleted    = $deletedFiles
        Summary    = $summary
        HasChanges = ($newFiles.Count -gt 0 -or $changedFiles.Count -gt 0 -or $deletedFiles.Count -gt 0)
    }
}

# -----------------------------------------------------------------------------
# Sync-DirTarBase64: Synchronisiert Verzeichnis via tar+base64+SSH (Fallback)
# -----------------------------------------------------------------------------

function Sync-DirTarBase64 {
    param(
        [Parameter(Mandatory=$true)]
        [string]$LocalBasePath,
        
        [Parameter(Mandatory=$true)]
        [string]$DirName,
        
        [Parameter(Mandatory=$true)]
        [string]$RemoteBasePath
    )
    
    $tarFile = Join-Path $env:TEMP "$DirName.tar.gz"
    
    try {
        # Zum Basisverzeichnis wechseln
        Push-Location $LocalBasePath
        
        # tar erstellen
        & tar -czf $tarFile $DirName 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "tar-Erstellung fehlgeschlagen fuer $DirName"
        }
        
        $sizeMB = [math]::Round((Get-Item $tarFile).Length / 1MB, 2)
        Write-Host "    [tar+base64] Uploading ($sizeMB MB)..." -ForegroundColor DarkGray
        
        # base64-encode und via SSH uebertragen
        # Verwende Windows OpenSSH mit dem passwortlosen Deploy-Key
        $sshExe = $script:SyncConfig.WindowsSSHPath
        $sshArgs = @(
            "-i", $script:SyncConfig.SSHKeyPathFull,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=60",
            "-o", "ServerAliveCountMax=3",
            "$($script:SyncConfig.ServerUser)@$($script:SyncConfig.ServerHost)",
            "python3 -c 'import base64,sys; sys.stdout.buffer.write(base64.b64decode(sys.stdin.read()))' > /tmp/$DirName.tar.gz && cd $RemoteBasePath && tar -xzf /tmp/$DirName.tar.gz && rm /tmp/$DirName.tar.gz"
        )
        
        # Python fuer base64-Encoding
        $base64Data = & python -c "import base64; print(base64.b64encode(open(r'$tarFile','rb').read()).decode())"
        if ($LASTEXITCODE -ne 0) {
            throw "base64-Encoding fehlgeschlagen"
        }
        
        $base64Data | & $sshExe @sshArgs
        if ($LASTEXITCODE -ne 0) {
            throw "SSH-Upload fehlgeschlagen fuer $DirName"
        }
        
        Write-Host "    [tar+base64] $DirName - OK" -ForegroundColor Green
        
    }
    finally {
        Pop-Location
        # Aufraeumen
        if (Test-Path $tarFile) {
            Remove-Item $tarFile -ErrorAction SilentlyContinue
        }
    }
}

# -----------------------------------------------------------------------------
# Update-RemoteManifest: Aktualisiert das Manifest auf dem Server
# Gibt $true bei Erfolg, $false bei Fehler zurueck (kein throw)
# Bei grossen Manifests wird das JSON in eine temporaere Datei geschrieben
# und dann via SCP/rsync uebertragen
# -----------------------------------------------------------------------------

function Update-RemoteManifest {
    param(
        [Parameter(Mandatory=$true)]
        [string]$RemoteBasePath,
        
        [Parameter(Mandatory=$true)]
        [string]$DirName,
        
        [Parameter(Mandatory=$true)]
        [AllowEmptyCollection()]
        [array]$Manifest
    )
    
    $syncStateDir = "$RemoteBasePath/.sync_state"
    $manifestFile = "$syncStateDir/${DirName}_manifest.json"
    
    $json = $Manifest | ConvertTo-Json -Compress
    if ([string]::IsNullOrEmpty($json) -or $json -eq "null") {
        $json = "[]"
    }
    
    # Bei grossen Manifests (>7KB) via temporaere Datei + rsync uebertragen
    # Windows-Limit ist ca. 8191 Zeichen
    $MAX_INLINE_SIZE = 7000
    
    try {
        # Ensure .sync_state directory exists
        Invoke-SSHCommand -Command "mkdir -p '$syncStateDir'" -NoThrow | Out-Null
        
        if ($json.Length -lt $MAX_INLINE_SIZE) {
            # Kleines Manifest: inline via echo
            $escapedJson = $json -replace "'", "'\\''"
            $command = "echo '$escapedJson' > '$manifestFile'"
            $result = Invoke-SSHCommand -Command $command -NoThrow
            return [bool]$result
        }
        else {
            # Grosses Manifest: via temporaere Datei + rsync
            Write-Host "    Info: Grosses Manifest ($($json.Length) bytes) - uebertrage via rsync" -ForegroundColor DarkGray
            
            $tempFile = Join-Path $env:TEMP "${DirName}_manifest.json"
            try {
                # Schreibe Manifest in temporaere Datei
                $json | Out-File -FilePath $tempFile -Encoding utf8 -NoNewline
                
                # Konvertiere Pfad fuer rsync
                $rsyncSource = Convert-ToRsyncPath $tempFile
                
                # rsync SSH-Optionen
                $sshKeyCygwin = Convert-ToRsyncPath $script:SyncConfig.SSHKeyPath -PreserveShortName
                $sshCmd = "ssh -i '$sshKeyCygwin' -o StrictHostKeyChecking=no -o ServerAliveInterval=60"
                
                $server = "$($script:SyncConfig.ServerUser)@$($script:SyncConfig.ServerHost)"
                
                # rsync ausfuehren
                & rsync -avz -e $sshCmd "$rsyncSource" "${server}:$manifestFile" 2>&1 | Out-Null
                $result = ($LASTEXITCODE -eq 0)
                return $result
            }
            finally {
                # Aufraeumen
                if (Test-Path $tempFile) {
                    Remove-Item $tempFile -ErrorAction SilentlyContinue
                }
            }
        }
    }
    catch {
        Write-Host "    WARNUNG: Manifest-Update fuer $DirName fehlgeschlagen: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

# -----------------------------------------------------------------------------
# Sync-DirectoryWithDiff: Vollstaendiger Sync mit Diff-Vorschau
# Gibt ein Objekt mit RsyncSuccess und ManifestSuccess zurueck
# -----------------------------------------------------------------------------

function Sync-DirectoryWithDiff {
    param(
        [Parameter(Mandatory=$true)]
        [string]$LocalBasePath,
        
        [Parameter(Mandatory=$true)]
        [string]$RemoteBasePath,
        
        [Parameter(Mandatory=$true)]
        [string]$DirName,
        
        [switch]$SkipIfNoChanges,
        
        [switch]$ForceTarFallback
    )
    
    $result = [PSCustomObject]@{
        DirName         = $DirName
        RsyncSuccess    = $false
        ManifestSuccess = $false
        Skipped         = $false
    }
    
    Write-Host ""
    Write-Host "[$DirName]" -ForegroundColor Cyan
    Write-Host "  Analysiere Aenderungen..." -ForegroundColor DarkGray
    
    # Lokales Manifest erzeugen
    $localManifest = New-DirectoryManifest -BasePath $LocalBasePath -DirName $DirName
    
    # Remote Manifest lesen (Fehler hier sind nicht kritisch)
    $remoteManifest = Get-RemoteManifest -RemoteBasePath $RemoteBasePath -DirName $DirName
    
    # Vergleichen
    $diff = Compare-Manifests -LocalManifest $localManifest -RemoteManifest $remoteManifest
    
    # Diff-Zusammenfassung ausgeben
    Write-Host ""
    Write-Host "  Diff-Zusammenfassung:" -ForegroundColor Yellow
    Write-Host $diff.Summary
    Write-Host ""
    
    # Optional: Ueberspringen wenn keine Aenderungen
    if ($SkipIfNoChanges -and -not $diff.HasChanges) {
        Write-Host "  Status: Keine Aenderungen - uebersprungen" -ForegroundColor Green
        $result.Skipped = $true
        $result.RsyncSuccess = $true
        $result.ManifestSuccess = $true
        return $result
    }
    
    # Transport-Methode waehlen: rsync bevorzugt, tar+base64 als Fallback
    $useRsync = (Test-RsyncAvailable) -and (-not $ForceTarFallback)
    
    if ($useRsync) {
        Write-Host "  Starte Upload (rsync)..." -ForegroundColor DarkGray
    }
    else {
        Write-Host "  Starte Upload (tar+base64 Fallback)..." -ForegroundColor DarkGray
    }
    
    # Rsync/Upload - kritischer Schritt
    try {
        if ($useRsync) {
            Sync-DirectoryWithRsync `
                -LocalBasePath $LocalBasePath `
                -RemoteBasePath $RemoteBasePath `
                -DirName $DirName
        }
        else {
            Sync-DirTarBase64 `
                -LocalBasePath $LocalBasePath `
                -DirName $DirName `
                -RemoteBasePath $RemoteBasePath
        }
        
        $result.RsyncSuccess = $true
        Write-Host "  Daten-Sync: OK" -ForegroundColor Green
    }
    catch {
        Write-Host "  Daten-Sync: FEHLER" -ForegroundColor Red
        Write-Host "    $($_.Exception.Message)" -ForegroundColor Red
        $result.RsyncSuccess = $false
        # Bei rsync-Fehler direkt zurueckgeben - nicht weiter versuchen
        return $result
    }
    
    # Manifest-Update - nicht kritisch
    $result.ManifestSuccess = Update-RemoteManifest -RemoteBasePath $RemoteBasePath -DirName $DirName -Manifest $localManifest
    
    if ($result.ManifestSuccess) {
        Write-Host "  Status: OK" -ForegroundColor Green
    }
    else {
        Write-Host "  Status: Daten synchronisiert (Manifest-Update fehlgeschlagen)" -ForegroundColor Yellow
    }
    
    return $result
}

# -----------------------------------------------------------------------------
# Set-RemoteOwnership: Setzt Besitzer auf dem Server
# Gibt $true bei Erfolg, $false bei Fehler zurueck (kein throw)
# -----------------------------------------------------------------------------

function Set-RemoteOwnership {
    param(
        [Parameter(Mandatory=$true)]
        [string]$RemotePath
    )
    
    $uid = $script:SyncConfig.AppUid
    $gid = $script:SyncConfig.AppGid
    
    Write-Host ""
    Write-Host "Setze Besitzer auf $RemotePath..." -ForegroundColor Cyan
    
    $result = Invoke-SSHCommand -Command "chown -R ${uid}:${gid} '$RemotePath'" -NoThrow
    if ($result) {
        Write-Host "  Ownership: ${uid}:${gid} - OK" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "  WARNUNG: Ownership-Aenderung fehlgeschlagen" -ForegroundColor Yellow
        return $false
    }
}
