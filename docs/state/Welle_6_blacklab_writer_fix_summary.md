# Welle 6 BlackLab Writer Fix Summary

Datum: 2026-03-20
Umgebung: Production deploy scripts, read-only live verification plus local script change
Scope: Korrektur des BlackLab-Standard-Publish-Ziels ohne Reader-, Mount-, Daten- oder Container-Aenderung

## Was geaendert wurde

- `scripts/deploy_sync/_lib/ssh.ps1`
  - neuer expliziter Remote-Pfad `BlackLabDataRoot = /srv/webapps/corapan/data`
  - `Set-RemotePaths` kann diesen Spezialpfad optional ueberschreiben, ohne `DataRoot` oder `MediaRoot` umzudeuten
- `scripts/deploy_sync/publish_blacklab_index.ps1`
  - Default fuer `-DataDir` liest jetzt `Get-RemotePaths().BlackLabDataRoot`
  - stiller Fallback auf `Get-RemotePaths().DataRoot` wurde entfernt
- `scripts/deploy_sync/README.md`
  - Default-Ziel fuer BlackLab-Publish auf Top-Level dokumentiert
  - explizit festgehalten, dass data/media weiter runtime-first bleiben

## Alter vs neuer Pfad

- alter Default-Schreibpfad:
  - `/srv/webapps/corapan/runtime/corapan/data/blacklab_index`
- neuer Default-Schreibpfad:
  - `/srv/webapps/corapan/data/blacklab_index`
- unveraenderter Live-Leser:
  - BlackLab-Container mountet `/srv/webapps/corapan/data/blacklab_index -> /data/index/corapan`

## Pre-Run Verifikation

Read-only live geprueft:

- BlackLab-Mount:
  - `docker inspect corapan-blacklab` zeigte den aktiven Mount `/srv/webapps/corapan/data/blacklab_index -> /data/index/corapan`
- aktiver Reader:
  - im laufenden Container zeigt `/data/index/corapan` auf den top-level Indexpfad
- laufender Publish:
  - kein aktiver Publish-/rsync-/scp-/blacklab_index.new-Prozess belegt
- Disk-Space:
  - `/srv` hatte zum Checkzeitpunkt rund `8.2G` frei
- Konsistenz beider Indexbaeume:
  - top-level und runtime hatten jeweils `74` Dateien
  - beide hatten jeweils `279M`
  - beide hatten denselben Manifest-Hash `036701a0d2d2b6467c059c711033cc85bdeb275f494b4d9df6bb9cf48495216a`

## Post-Run Verifikation

- statische Skriptpruefung:
  - `publish_blacklab_index.ps1` zieht den Default nicht mehr aus `DataRoot`
  - `sync_data.ps1` verwendet weiterhin `Get-RemotePaths().DataRoot`
  - `sync_media.ps1` bleibt bei runtime-first `MediaRoot`
- Wrapper-Pruefung:
  - `maintenance_pipelines/_2_deploy/publish_blacklab.ps1` uebergibt standardmaessig kein `-DataDir` und erbt damit jetzt den korrigierten Top-Level-Default
- Editor-Fehlerpruefung:
  - keine Fehler in den geaenderten Skript- und Doku-Dateien vor der Aenderung; Nachpruefung folgt nach Patch-Anwendung

## Risiken

- dieser Run korrigiert nur den Standard-Schreibpfad, fuehrt aber keinen echten Publish aus
- ein manueller Aufruf mit explizitem `-DataDir` kann weiterhin absichtlich auf einen anderen Pfad zeigen
- die Runtime-Duplikate bleiben bestehen; der Run beseitigt den stillen Standardkonflikt, aber keine Datenkopien
- Live-BlackLab, Mounts, Container und Indexinhalte wurden bewusst nicht veraendert

## Ergebnis

- BlackLab liest weiterhin top-level
- der Standard-BlackLab-Publish zeigt nun ebenfalls top-level
- data/media Deploy bleiben runtime-first
- der bisherige stille Widerspruch zwischen Live-Reader und Default-Writer ist auf Default-Ebene entfernt

## Lessons Learned

- Spezial-Deploys duerfen keinen allgemeinen Remote-Default wiederverwenden, wenn ihr Live-Zielmodell davon abweicht.
- Ein gemeinsamer Pfad-Helper braucht getrennte explizite Defaults fuer unterschiedliche Produktionsrealitaeten, statt einen Spezialfall ueber einen allgemeinen Datenpfad mitzuschleifen.