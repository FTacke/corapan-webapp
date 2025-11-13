# BlackLab Tools

Dieses Verzeichnis enthält BlackLab-Tools für den Index-Build.

## BlackLab Server JAR

**Datei:** `blacklab-server.jar`

**Download:** https://github.com/INL/BlackLab/releases

**Verwendung:**
- Wird von `scripts/build_blacklab_index.ps1` für den Index-Build genutzt
- Enthält sowohl den Server als auch die IndexTool-CLI

**Wichtig:**
- Diese Datei ist **nicht** im Git-Repository enthalten (siehe `.gitignore`)
- Muss manuell heruntergeladen werden

## Installation

```powershell
# Download the latest BlackLab Server JAR from GitHub Releases
# Example for version 4.0.0:
Invoke-WebRequest -Uri "https://github.com/INL/BlackLab/releases/download/v4.0.0/blacklab-server-4.0.0.jar" -OutFile "tools\blacklab\blacklab-server.jar"
```

Oder:
1. Besuche https://github.com/INL/BlackLab/releases
2. Lade die neueste `blacklab-server-X.Y.Z.jar` herunter
3. Speichere sie als `tools/blacklab/blacklab-server.jar`

## Verwendung mit scripts/build_blacklab_index.ps1

Das Build-Skript sucht das JAR an zwei Stellen:

1. **Umgebungsvariable:** `$env:BLACKLAB_JAR`
   ```powershell
   $env:BLACKLAB_JAR = "C:\custom\path\to\blacklab-server.jar"
   .\scripts\build_blacklab_index.ps1
   ```

2. **Repository-Pfad:** `tools/blacklab/blacklab-server.jar`
   ```powershell
   # JAR hier ablegen, dann:
   .\scripts\build_blacklab_index.ps1
   ```

## Version-Kompatibilität

- **Erforderlich:** Lucene 9.x kompatibel
- **Empfohlen:** BlackLab 4.0.0+ (enthält Lucene 9.11.1)
- **Nicht kompatibel:** BlackLab 3.x (nutzt Lucene 8.x)

## Lizenz

BlackLab ist Open Source (Apache License 2.0).
Repository: https://github.com/INL/BlackLab
