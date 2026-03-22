# Dev BlackLab Canonicalization 2026-03-20

## Was wurde geaendert

- kanonisches Repo-Skelett fuer `data/blacklab/{index,export,backups,quarantine}` verankert
- explizites PowerShell-Migrationsskript fuer lokale Legacy-BlackLab-Verzeichnisse hinzugefuegt
- Dev-Start und Dev-Setup brechen jetzt explizit ab, wenn alte `data/blacklab_export` oder `data/blacklab_index`-Layouts noch vorhanden sind, aber der kanonische Baum nicht migriert wurde
- aktive Tests und Debug-Helfer wurden auf kanonische BlackLab-Pfade und den kanonischen Dev-Korpus `corapan` umgestellt
- direkt betroffene Dev-Doku und Script-Referenzen wurden synchronisiert

## Warum

Der Repo-Code und die aktiven Dev-Skripte waren bereits weitgehend auf `data/blacklab/*` umgestellt, waehrend lokale Repo-Daten und einige Tests/Helper noch alte Flachpfade nutzten. Dadurch blieb in Dev eine verdeckte Mischrealitaet bestehen.

## Umgebung

- nur Development / Repository
- keine Produktivpfade und kein Server-Cutover betroffen

## Operative Auswirkung

- lokale Entwickler muessen ein noch vorhandenes altes BlackLab-Layout einmal explizit migrieren
- danach ist `data/blacklab/*` die einzige Dev-Quelle der Wahrheit fuer BlackLab-Artefakte

## Kompatibilitaet

- `BLACKLAB_BASE_URL` bleibt als Legacy-Kompatibilitaetsspiegel in den Dev-Skripten gesetzt
- `infra/docker-compose.dev.yml` bleibt als nicht-kanonische alternative Compose-Datei bestehen

## Follow-up

- optional spaeter: weitere historische BlackLab-Doku ausserhalb der direkt betroffenen Dev-Dokumente konsolidieren
- optional spaeter: `infra/docker-compose.dev.yml` separat entweder stilllegen oder vollstaendig an die kanonische Runtime-Semantik anpassen