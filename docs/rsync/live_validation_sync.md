# Live Validation: Production Sync Lane

Datum: 2026-03-25

Scope:
- kontrollierte Live-Validierung der lokalen Windows-/PowerShell-Operator-Strecke
- nur nichtdestruktive Transfers in `/srv/webapps/corapan/tmp_sync_test/`
- kein Einsatz von `--delete`
- keine produktiven Zielpfade, keine Deploy-Skripte, keine Service-Starts/-Stops

## A. Executive Summary

Kurzfazit:

- Der technisch belastbarste Standardweg in der hier getesteten Operator-Umgebung ist `rsync` ueber das repo-gebundelte cwRsync-`ssh.exe`.
- `rsync` mit Windows-OpenSSH bzw. mit der normalen lokalen SSH-Konfiguration war in derselben Umgebung nicht benutzbar und brach reproduzierbar mit `code 12` vor Datenfluss ab.
- `rsync`-Resume fuer eine 1-GiB-Datei funktionierte real: nach manuellem Abbruch blieb ein partielles Remote-Ziel mit rund 316 MB bestehen, der zweite Lauf vervollstaendigte die Datei korrekt, und die SHA256-Pruefsumme stimmte.
- `scp` funktioniert hier nur im Legacy-Modus `-O`; der Default-Modus scheitert sofort mit `subsystem request failed on channel 0`.
- `tar|ssh` ist nicht pauschal stabil: der funktionierende `cmd`-basierte Pfad lieferte fuer die mittelgrosse Datei korrekte Hashes, die PowerShell-Pipeline korrumpierte dieselbe Datei, und der 1-GiB-Lauf ueber `cmd` endete mit gekuerzter Datei und Hash-Mismatch.
- Striktes Host-Key-Checking ist technisch moeglich, aber nur mit vorab befuelltem `known_hosts`; mit leerer Datei schlagen `ask` und `yes` reproduzierbar fehl.

Gesamturteil:

- `rsync + cwRsync ssh.exe`: stabil, resume-faehig, reproduzierbar, bester Standardweg
- `scp -O`: brauchbarer Fallback, aber ohne Resume und nur mittelmaessig attraktiv
- `tar|ssh`: nur als begrenzter Fallback fuer kleinere bis mittlere Transfers belastbar; fuer grosse Dateien in dieser Umgebung nicht als Standard geeignet

## B. Testumgebung (lokal + Server)

### Lokal

- OS: Windows
- Shell: PowerShell
- Verfuegbare Binaries:
  - `C:\Windows\System32\OpenSSH\ssh.exe`
  - `C:\Windows\System32\OpenSSH\scp.exe`
  - `C:\Windows\System32\tar.exe`
  - `C:\dev\corapan\app\tools\cwrsync\bin\rsync.exe` (rsync 3.4.1)
  - `C:\dev\corapan\app\tools\cwrsync\bin\ssh.exe`
- Lokale SSH-Realitaet:
  - in `~/.ssh/config` existiert ein Alias `vhrz2184`
  - Alias-Ziel: `137.248.186.51`
  - User: `root`
  - Identity: `~/.ssh/id_ed25519`
  - `IdentitiesOnly yes`
- Wichtige Abweichung zum Repo-Code:
  - der in `app/scripts/deploy_sync/_lib/ssh.ps1` angenommene Key `~/.ssh/marele` existierte lokal nicht
  - der hartkodierte 8.3-Pfad `C:\Users\FELIXT~1\...` war auf dieser Maschine nicht als kurzer Namenspfad sichtbar/nutzbar

### Server

- Gegenstelle erreichbar per SSH ueber `vhrz2184`
- Remote-rsync vorhanden: `/usr/bin/rsync`, Version 3.2.7
- Dedizierter Testpfad: `/srv/webapps/corapan/tmp_sync_test/`

### Testdesign vor Ausfuehrung

Es wurden vier lokale Testkategorien vorbereitet:

1. klein
- `src-small/small.bin`
- 524,288 Bytes

2. mittel
- `src-medium/medium.mp3`
- 89,432,109 Bytes

3. gross
- `src-large/large-1GiB.bin`
- 1,073,741,824 Bytes

4. viele kleine Dateien
- `src-many/`
- 100 Dateien aus `media/transcripts`
- 515,164,839 Bytes lokal gesamt

SHA256 der Einzeldateien wurde lokal erfasst; bei erfolgreichen Einzeldatei-Transfers wurden die Remote-Hashes gegengeprueft.

## C. Ergebnisse rsync

### 1. Windows-OpenSSH als Transportkommando

Getestet:
- cwRsync `rsync.exe` mit `-e ssh`
- cwRsync `rsync.exe` mit explizitem Windows-OpenSSH-Pfad
- cwRsync `rsync.exe` mit separater Test-SSH-Config

Ergebnis:
- alle Varianten brachen reproduzierbar mit `rsync: connection unexpectedly closed (0 bytes received so far)` und Exitcode 12 ab
- SSH allein funktionierte in derselben Umgebung
- Remote-`rsync --version` funktionierte ebenfalls

Bewertung:
- in dieser Operator-Umgebung ist nicht nur der Keypfad, sondern die Kombination cwRsync + Windows-OpenSSH praktisch unbrauchbar

### 2. cwRsync mit gebundeltem `ssh.exe`

Getestet:
- `-e /cygdrive/c/dev/corapan/app/tools/cwrsync/bin/ssh.exe`

Ergebnis:
- klein: erfolgreich
- mittel: erfolgreich
- gross: erfolgreich, inklusive Resume-Test
- viele kleine Dateien: erfolgreich

Messwerte:

| Kategorie | Ergebnis | Zeit |
|---|---|---:|
| klein | erfolgreich | 0.91 s |
| mittel | erfolgreich | 37.38 s |
| gross Resume-Vervollstaendigung | erfolgreich | 305.27 s |
| viele kleine Dateien | erfolgreich | 235.06 s |
| mittel No-Change Wiederholung | erfolgreich | 0.71 s |

Integritaet:

- `small.bin`: SHA256 lokal = remote
- `medium.mp3`: SHA256 lokal = remote
- `large-1GiB.bin`: SHA256 lokal = remote

Technische Bedeutung:

- der repo-eigene cwRsync-Stack ist hier nicht nur Komfort, sondern funktional notwendig
- Delta-/No-Change-Verhalten ist gut: der zweite Medium-Lauf war subsekundaer bis knapp subsekundaer

## D. Ergebnisse tar|ssh

### 1. PowerShell-Pipeline

Getestet:
- `tar -cf - ... | ssh ... "tar -xpf - -C ..."`

Ergebnis:
- Datei erschien remote
- Hash war falsch
- damit ist die PowerShell-Pipeline in dieser Umgebung fuer binare Integritaet nicht belastbar

Mitteldatei:
- Transferdauer: 46.73 s
- Hash-Mismatch

### 2. `cmd`-basierter tar|ssh-Pfad

Getestet:
- `cmd /c "tar -cf - ... | ssh ... tar -xpf - -C ..."`

Ergebnis fuer mittelgrosse Datei:
- erfolgreich
- 33.08 s
- SHA256 lokal = remote

Ergebnis fuer 1-GiB-Datei:
- nicht belastbar erfolgreich
- Remote-Datei groesserer Lauf endete instabil
- Remote-Dateigroesse nur 1,040,301,056 Bytes statt 1,073,741,824 Bytes
- SHA256-Mismatch

Bewertung:
- `tar|ssh` kann in dieser Umgebung fuer mittlere Dateien funktionieren, aber ist nicht durchgaengig robust
- fuer grosse Dateien ist dieser Weg hier kein sicherer Standardweg

## E. Ergebnisse scp

### 1. Default-Modus

Ergebnis:
- sofortiger Fehler
- Meldung: `subsystem request failed on channel 0`

Bewertung:
- moderner Default-SCP/SFTP-Modus ist gegen diese Gegenstelle in der getesteten Umgebung nicht verwendbar

### 2. Legacy-Modus `scp -O`

Ergebnis fuer mittelgrosse Datei:
- erfolgreich
- 35.36 s
- SHA256 lokal = remote

Bewertung:
- `scp -O` ist ein realer, funktionierender Fallback
- es gibt keinen Resume-Mechanismus und keine Delta-Semantik

## F. Resume-Verhalten

Getestet wurde `rsync --partial --progress` mit der 1-GiB-Datei.

Testablauf:

1. grosser rsync-Lauf gestartet
2. Transfer manuell abgebrochen
3. partieller Remote-Zustand geprueft
4. derselbe Lauf erneut gestartet

Befunde:

- beim Abbruch waren ca. 29 Prozent erreicht
- Remote-Datei nach Abbruch: `large-1GiB.bin 316,178,432 bytes`
- zweiter Lauf vervollstaendigte die Datei
- finaler Remote-Hash entsprach exakt dem lokalen Hash

Bewertung:
- Resume ist hier real belegt
- das ist der staerkste technische Vorteil von rsync gegenueber `scp -O` und `tar|ssh`

## G. Verhalten bei Fehlern

### 1. leere Quelle bei rsync

Test:
- leeres lokales Verzeichnis auf isolierten Remote-Zielpfad

Ergebnis:
- erfolgreich
- Remote-Zielverzeichnis wurde angelegt
- keine Dateien uebertragen
- keine Loeschungen, da bewusst ohne `--delete`

Bewertung:
- ohne `--delete` ist leere Quelle technisch unkritisch

### 2. fehlende Quelle bei rsync

Test:
- nicht existierender lokaler Pfad

Ergebnis:
- Exitcode 23
- klare Fehlermeldung `change_dir ... failed: No such file or directory`
- Remote-Zielverzeichnis wurde trotzdem angelegt

Bewertung:
- Fehler ist sichtbar, aber der Nebeneffekt "Remote-Verzeichnis bereits erzeugt" sollte bei kuenftiger Härtung beachtet werden

### 3. tar|ssh mit nicht existierendem Remote-Ziel

Ergebnis:
- laute Fehlermeldung von `tar`
- kein stilles Weiterlaufen

Bewertung:
- Fehlersemantik ist brauchbar, aber nicht besonders komfortabel

## H. SSH-Kompatibilitaet

### 1. reale lokale SSH-Wahrheit

- der operative Zugriff lief ueber `vhrz2184`
- der Repo-Default `marele` plus `~/.ssh/marele` war auf dieser Maschine nicht die aktive Realitaet

### 2. Host-Key-Checks mit isoliertem `known_hosts`

Mit leerem temporaeren `known_hosts`:

- `StrictHostKeyChecking=ask`: fehlgeschlagen
- `StrictHostKeyChecking=yes`: fehlgeschlagen
- `StrictHostKeyChecking=no`: erfolgreich, Host-Key wurde automatisch eingetragen

Bewertung:
- `ask` und `yes` sind nicht kaputt, sondern brauchen vorbereitete Host-Key-Verteilung
- jede spaetere Sicherheits-Haertung muss deshalb einen echten `known_hosts`-Bootstrap enthalten

### 3. cwRsync-Besonderheit

- cwRsync funktionierte hier erst mit dem gebundelten `ssh.exe`
- Windows-OpenSSH war fuer rsync in dieser Umgebung nicht interoperabel
- 8.3-Kurzpfad war lokal nicht verifizierbar

## I. Technische Grenzen

1. `rsync` ist in dieser Umgebung nicht transportneutral
- funktional gebunden an cwRsync plus bundeltes `ssh.exe`

2. `scp` braucht Legacy-Modus
- moderner SCP-/SFTP-Weg steht hier nicht zur Verfuegung

3. `tar|ssh` ist groessenabhaengig fragil
- mittlere Datei via `cmd`: gut
- grosse Datei via `cmd`: korrupt/gekürzt
- PowerShell-Pipeline: bereits bei Mitteldatei nicht integritaetssicher

4. Host-Key-Haertung ist nicht kostenlos
- `StrictHostKeyChecking=yes` ohne vorbefuelltes `known_hosts` blockiert sofort

5. CPU-Last wurde in dieser Validierung nicht instrumentiert gemessen
- Fokus lag auf Ende-zu-Ende-Belastbarkeit, Integritaet, Abbruchverhalten und Reproduzierbarkeit

## J. Empfohlener Standardweg

Empfohlener Standard fuer produktive Syncs von der hier getesteten Operator-Maschine:

1. Standard
- `rsync` ueber repo-gebundeltes cwRsync-`ssh.exe`
- mit `--partial` fuer grosse Dateien

2. Fallback 1
- `scp -O`
- nur wenn rsync temporär nicht verfuegbar ist

3. Fallback 2
- `tar|ssh` nur fuer kleinere bis mittlere Transfers und nur ueber den funktionierenden `cmd`-Pfad
- nicht fuer grosse Einzeldateien als Standard verwenden

## K. Was unbedingt erhalten bleiben muss (Workarounds!)

1. Trennung zwischen Standardweg und Fallbacks
- nicht auf einen einzigen Transferweg reduzieren

2. cwRsync-eigene SSH-Toolchain als explizite Option
- diese Validierung zeigt, dass Windows-OpenSSH fuer rsync hier nicht ausreicht

3. `scp -O`-Fallback
- moderner Default-SCP funktioniert nicht

4. `--partial`/Resume fuer grosse Dateien
- technisch real bestaetigt und betriebsrelevant

5. isolierte Testpfade und explizite Nicht-Produktiv-Ziele
- fuer jede kuenftige Validierung oder Refactor-Pruefung beibehalten

6. Host-Key-Bootstrap als eigener Migrationsschritt
- nie einfach `StrictHostKeyChecking=yes` erzwingen ohne vorbereitete Known-Hosts-Verteilung

## L. Was optional entfernt werden kann

1. Annahme, dass Windows-OpenSSH automatisch als rsync-Transport reicht
- diese Annahme ist in der getesteten Umgebung widerlegt

2. Annahme, dass PowerShell-`tar|ssh` binarintegrer Standardweg ist
- in dieser Umgebung widerlegt

3. Annahme, dass der Repo-Keypfad `~/.ssh/marele` aktuelle Betriebsrealitaet ist
- lokal nicht bestaetigt; operative SSH-Konfiguration lief anders

4. pauschale Hoffnung auf 8.3-Pfad-Abhaengigkeit als universelle Loesung
- auf dieser Maschine nicht einmal belastbar nachweisbar

## Reproduktionskern

Die wichtigsten reproduzierbaren Kommandotypen aus dieser Validierung waren:

1. rsync Standardweg
```powershell
& 'C:\dev\corapan\app\tools\cwrsync\bin\rsync.exe' -av --partial --progress \
  -e /cygdrive/c/dev/corapan/app/tools/cwrsync/bin/ssh.exe \
  /cygdrive/c/dev/corapan/tmp/sync-validation/src-large/ \
  vhrz2184:/srv/webapps/corapan/tmp_sync_test/rsync-large/
```

2. scp Fallback
```powershell
scp -O C:\dev\corapan\tmp\sync-validation\src-medium\medium.mp3 \
  vhrz2184:/srv/webapps/corapan/tmp_sync_test/scp-medium/
```

3. tar|ssh nur eingeschraenkt brauchbar
```powershell
cmd /c "tar -cf - -C C:\dev\corapan\tmp\sync-validation\src-medium . | ssh vhrz2184 tar -xpf - -C /srv/webapps/corapan/tmp_sync_test/tar-medium-cmd2"
```

## Skill-Ableitung

Aus dieser Live-Validierung folgt fuer Agenten/Skills:

- `rsync` darf auf Windows nicht gegen generisches `ssh` "vereinfacht" werden, ohne dass die cwRsync-SSH-Interoperabilitaet live nachgewiesen ist
- `scp -O` darf nicht entfernt werden, solange Default-SCP am Zielhost scheitert
- `tar|ssh` darf nicht fuer grosse Dateien als gleichwertiger Ersatz zu rsync dargestellt werden
- Host-Key-Haertung braucht vorbereitete `known_hosts`-Strategie