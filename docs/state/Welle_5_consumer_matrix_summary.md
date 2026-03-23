# Welle 5 Consumer Matrix Summary

Datum: 2026-03-20
Umgebung: Production live, read-only
Scope: Leser-, Schreiber- und Deploy-Ziel-Matrix fuer kritische und doppelte PROD-Pfade
Methodik: Live-Mounts, Container-Analyse, Code-Analyse, Deploy-Orchestratoren, deploy_sync-Unterbau, Logs, mtime-Spuren

## 5. Klassifikationslegende

- READ_ACTIVE: aktiver Leser belegt
- WRITE_ACTIVE: aktiver Schreiber belegt
- READ_ONLY_ACTIVE: aktiver Leser belegt, kein aktueller Standardschreiber belegt
- WRITE_ONLY: aktiver Schreiber belegt, kein aktiver Leser belegt
- UNUSED: kein aktiver Leser/Schreiber belegt
- UNKNOWN: Beleglage nicht stark genug fuer UNUSED oder aktiv

Deploy-Zusatzklassifikation:

- DEPLOY_TARGET_ACTIVE: aktueller Orchestrator/Unterbau schreibt aktiv dorthin
- DEPLOY_TARGET_LEGACY: nur alte, manuelle oder abweichende Flows schreiben dorthin
- DEPLOY_TARGET_PROTECTED: Ziel oder Teilpfad ist bewusst vor normalem Deploy geschuetzt
- DEPLOY_TARGET_HIGH_RISK: Deploy-Ziel und Live-Verbraucher sind widerspruechlich oder der Pfad ist produktiv besonders sensibel

## 6. Pflichtfragen

1. Wird runtime/.../blacklab_index ueberhaupt genutzt?

Ja, aber nur als aktuelles Deploy-Ziel des BlackLab-Publish-Unterbaus. Ein aktiver Live-Leser in PROD wurde nicht belegt. Der laufende BlackLab-Container liest top-level /srv/webapps/corapan/data/blacklab_index.

2. Wer liest docmeta.jsonl - runtime oder top-level?

Der aktuelle Web-App-Code liest runtime/corapan/data/blacklab_export/docmeta.jsonl ueber get_docmeta_path(). Ein aktiver Top-Level-Leser wurde im Web-App- oder BlackLab-Live-Pfad nicht belegt.

3. Werden Logs doppelt geschrieben oder nur parallel gehalten?

Aktiv geschrieben wird runtime/corapan/logs/corapan.log durch die Web-App. Top-level /srv/webapps/corapan/logs/corapan.log ist vorhanden, aber die aktuelle Code- und mtime-Lage zeigt keine laufende Doppelbeschriftung.

4. Gibt es irgendeinen Schreiber auf top-level data ausser BlackLab?

Im aktuellen Standard-Deploy-Pfad nein. Aktive Standard-Orchestratoren deployen data nach runtime/corapan/data. Top-level data hat nur BlackLab-nahe oder legacy/manuelle Skriptbezuge, zum Beispiel run_bls_prod.sh, retain_blacklab_backups_prod.sh und das deaktivierte build_blacklab_index_prod.sh. zusaetzlich existiert scripts/ops/setup_db_public.sh als manueller legacy Ops-Helfer fuer top-level data/db/public.

5. Greift die Web-App irgendwo noch indirekt auf top-level data zu?

Im aktuellen App-Code nein. Die produktive Web-App loest DATA_ROOT, PUBLIC_STATS_DIR, STATS_TEMP_DIR, METADATA_DIR, db/public und docmeta ueber runtime/corapan auf.

6. Gibt es stille Abhaengigkeiten durch Scripts, Cron, Runner oder Deploy-Sync?

Ja, durch Runner und deploy_sync. Belegt sind:

- GitHub self-hosted runner -> deploy.yml -> scripts/deploy_prod.sh
- maintenance_pipelines/_2_deploy/*.ps1 -> scripts/deploy_sync/*
- scripts/deploy_sync/_lib/ssh.ps1 als kanonische Remote-Zielquelle fuer data/media/runtime

Kein positiver Cron- oder systemd-Timer-Beleg fuer corapan wurde in diesem Run gefunden.

7. Schreibt deploy_data.ps1 aktiv nach top-level /srv/webapps/corapan/data/...?

Nein. Der aktuelle Unterbau schreibt nach /srv/webapps/corapan/runtime/corapan/data.

8. Schreibt deploy_media.ps1 aktiv nach top-level /srv/webapps/corapan/media/... oder an einen runtime-Pfad?

An einen runtime-Pfad: /srv/webapps/corapan/runtime/corapan/media.

9. Verwendet publish_blacklab.ps1 top-level blacklab_index als kanonisches Ziel?

Nein, nicht standardmaessig. Der aktuelle Unterbau publish_blacklab_index.ps1 nimmt per Default DataDir = Get-RemotePaths().DataRoot und das ist in _lib/ssh.ps1 auf /srv/webapps/corapan/runtime/corapan/data gesetzt. Genau das ist der gefaehrliche Widerspruch zur Live-BlackLab-Instanz, die top-level /srv/webapps/corapan/data/blacklab_index liest.

10. Welche produktiven Pfade werden absichtlich vor Ueberschreiben geschuetzt?

- data/db im normalen data deploy
- auth.db implizit durch Hard-Block des db-Pfads
- blacklab_index, blacklab_index.backup, stats_temp, .sync_state im rsync-Unterbau
- mp3-temp wird von deploy_media nicht synchronisiert
- BlackLab-Publish hat Validierungs-Gate und Backup-Schema vor Aktivierung
- passwords.env ist operator-managed und kein Agent-/Deploy-Ziel in diesem Repo

## 7.1 Zusammenfassung

Die klare Wahrheit pro Pfad lautet:

- Web-App liest und schreibt produktiv unter runtime/corapan/data, runtime/corapan/media und runtime/corapan/logs.
- Daten- und Medien-Orchestratoren deployen ebenfalls runtime-first.
- docmeta fuer Advanced Search kommt aus runtime/corapan/data/blacklab_export/docmeta.jsonl.
- BlackLab liest produktiv top-level /srv/webapps/corapan/data/blacklab_index und /srv/webapps/corapan/app/config/blacklab.
- Der aktuelle BlackLab-Publish-Unterbau schreibt standardmaessig nicht auf diesen live gelesenen Top-Level-Indexpfad, sondern auf runtime/corapan/data/blacklab_index.
- Damit wird die Parallelrealitaet durch den aktuellen Deploy-Unterbau bei BlackLab aktiv fortgeschrieben.

Die klare Wahrheit pro Deploy-Ziel lautet:

- deploy_data.ps1 -> runtime/corapan/data/*
- deploy_media.ps1 -> runtime/corapan/media/*
- publish_blacklab.ps1 -> defaultmaessig runtime/corapan/data/blacklab_index*
- deploy.yml + deploy_prod.sh -> /srv/webapps/corapan/app und daraus indirekt /srv/webapps/corapan/app/config/blacklab
- /srv/webapps/corapan/config/passwords.env wird gelesen, aber von keinem der betrachteten Orchestratoren geschrieben

## 7.2 Verbraucher-Matrix

| Pfad | Leser | Schreiber | Komponente | Frequenz | Kritikalitaet | Klassifikation | Beleg |
|---|---|---|---|---|---|---|---|
| /srv/webapps/corapan/data/blacklab_index | corapan-blacklab ueber /data/index/corapan; run_bls_prod.sh Pruefpfad | kein aktueller Standardschreiber belegt; nur manueller/override-Pfad in publish_blacklab_index.ps1 mit explizitem -DataDir oder deaktivierter legacy Build-in-Prod-Pfad | BlackLab Suchindex | Lesen kontinuierlich und pro Query; Schreiben nur bei manuellem Publish/Override | sehr hoch | READ_ACTIVE; READ_ONLY_ACTIVE; DEPLOY_TARGET_LEGACY | Live docker inspect corapan-blacklab; run_bls_prod.sh DATA_ROOT=/srv/webapps/corapan/data |
| /srv/webapps/corapan/runtime/corapan/data/blacklab_index | kein aktiver Live-Leser belegt | publish_blacklab.ps1 -> publish_blacklab_index.ps1 Default-DataDir; atomic swap und Backup-Retention unter diesem Root | aktuelles BlackLab-Deploy-Ziel im Unterbau | auf BlackLab-Publish | sehr hoch | WRITE_ONLY; DEPLOY_TARGET_ACTIVE; DEPLOY_TARGET_HIGH_RISK | publish_blacklab_index.ps1 DataDir = Get-RemotePaths().DataRoot; _lib/ssh.ps1 DataRoot=runtime/corapan/data |
| /srv/webapps/corapan/data/blacklab_export | kein aktiver Web-App- oder Container-Leser belegt | kein aktueller Standardschreiber belegt; nur legacy/manuelle Top-Level-Bezuge | duplizierter Exportbaum | keine aktive Frequenz belegt | hoch | UNUSED | Web-App liest runtime docmeta; deploy_data zielt runtime DataRoot |
| /srv/webapps/corapan/runtime/corapan/data/blacklab_export | Advanced Search docmeta loader | deploy_data.ps1 -> sync_data.ps1 rsynct blacklab_export; lokale Export-Pipeline erzeugt Quelle vor Deploy | Web-App-docmeta und Exportartefakte | Lesen beim App-Import/Start; Schreiben bei Data-Deploy | hoch | READ_ACTIVE; WRITE_ACTIVE; DEPLOY_TARGET_ACTIVE | advanced_api.py -> get_docmeta_path(); sync_data.ps1 DATA_DIRECTORIES enthaelt blacklab_export |
| /srv/webapps/corapan/logs | kein aktiver App-Schreiber belegt; nur manuelle Operator-Lektuere plausibel | kein aktueller Standardschreiber belegt | paralleler Legacy-Logpfad | keine aktive Frequenz belegt | mittel | UNUSED | top-level corapan.log mtime alt; App setup_logging schreibt runtime logs |
| /srv/webapps/corapan/runtime/corapan/logs | Operatoren/Support lesen Datei-Logs; App selbst oeffnet RotatingFileHandler | Web-App RotatingFileHandler schreibt corapan.log | Applikationslogs | Schreiben kontinuierlich waehrend Laufzeit; Lesen bei Diagnose | hoch | READ_ACTIVE; WRITE_ACTIVE | src/app/__init__.py setup_logging(); Live mtime 2026-03-20 auf runtime corapan.log |
| /srv/webapps/corapan/data | corapan-blacklab liest Subpfad blacklab_index; BlackLab-nahe Ops/Retention-Skripte nutzen Top-Level DATA_ROOT; setup_db_public.sh nutzt top-level db/public | nur legacy/manuelle Top-Level-Ops-Pfade belegt; kein Standard-Data-Deploy | aggregierter Top-Level-Datenbaum | Lesen kontinuierlich ueber BlackLab; Schreiben manuell/infrequent | sehr hoch | READ_ACTIVE; DEPLOY_TARGET_LEGACY; UNKNOWN | run_bls_prod.sh, retain_blacklab_backups_prod.sh, setup_db_public.sh referenzieren top-level data |
| /srv/webapps/corapan/runtime/corapan/data | Web-App config, atlas, corpus metadata/statistics, advanced search docmeta, stats API, sqlite public DB | deploy_data; App erstellt Stats-Dirs; Stats-API schreibt Cache; deploy_prod und deploy.yml machen write-test in stats_temp | aggregierter aktiver Web-App-Datenbaum | Startup, per request, per deploy | sehr hoch | READ_ACTIVE; WRITE_ACTIVE; DEPLOY_TARGET_ACTIVE | Live web mount /app/data; src/app/config, routes/corpus.py, routes/stats.py, services/database.py; deploy_data.ps1 |
| /srv/webapps/corapan/config/passwords.env | deploy_prod.sh via docker-compose --env-file; Compose/Containerstart liest ENV daraus | kein betrachteter Repo-Orchestrator schreibt hierhin; operator-managed | Secrets-Quelle fuer Prod-Deploy | bei jedem App-Deploy/Stack-Recreate | sehr hoch | READ_ONLY_ACTIVE | deploy_prod.sh ENV_FILE; workflow deploy.yml -> bash scripts/deploy_prod.sh |
| /srv/webapps/corapan/app/config/blacklab | corapan-blacklab live; publish_blacklab validation container; run_bls_prod.sh Pruefpfad | GitHub runner deploy.yml -> deploy_prod.sh -> git fetch/reset im App-Checkout schreibt Repo-Dateien hierhin | aktive BlackLab-Konfiguration | Lesen kontinuierlich und bei Publish-Validierung; Schreiben auf Code-Deploy | sehr hoch | READ_ACTIVE; WRITE_ACTIVE | Live blacklab mount; publish_blacklab_index.ps1 ConfigDir default; deploy_prod.sh git reset --hard origin/main |
| /srv/webapps/corapan/runtime/corapan/media | media routes, transcript fetch, play_audio/snippet, editor routes | deploy_media synct transcripts/mp3-full/mp3-split; editor schreibt Transcriptdateien und edit_log; audio_snippets schreibt mp3-temp und cleanup loescht alte Snippets | aktive Medienbasis | per media request, per edit, per media deploy | sehr hoch | READ_ACTIVE; WRITE_ACTIVE; DEPLOY_TARGET_ACTIVE | Live /app/media mount; sync_media.ps1 MediaRoot; src/app/routes/media.py; src/app/routes/editor.py; services/audio_snippets.py |
| /srv/webapps/corapan/runtime/corapan/data/db/public | atlas und editor lesen stats_files.db und stats_country.db ueber sqlite | deploy_data synct genau diese beiden DBs; setup_db_public.sh ist nur legacy top-level helper | oeffentliche Stats-SQLite-DBs | per atlas/editor request; bei Data-Deploy | hoch | READ_ACTIVE; WRITE_ACTIVE; DEPLOY_TARGET_ACTIVE | services/database.py; sync_data.ps1 STATS_DB_FILES; Live recent mtime und .sync_state manifest |
| /srv/webapps/corapan/runtime/corapan/data/stats_temp | stats API liest Cachedateien | stats API schreibt/loescht Cachedateien; deploy_prod.sh und deploy.yml schreiben Touch-Tests; App legt Verzeichnis an | Stats-Cache/Temp | pro Stats-Request und pro App-Deploy | hoch | READ_ACTIVE; WRITE_ACTIVE; DEPLOY_TARGET_PROTECTED | routes/stats.py; config/__init__.py mkdir; deploy_prod.sh touch /app/data/stats_temp/.deploy_write_test |
| Docker volume corapan_postgres_prod | postgres Container direkt; Web-App indirekt ueber AUTH_DATABASE_URL und SQLAlchemy | postgres Container direkt | Auth/Core-DB | kontinuierlich | sehr hoch | READ_ACTIVE; WRITE_ACTIVE; DEPLOY_TARGET_PROTECTED | Live docker inspect db mount; infra/docker-compose.prod.yml |

## 7.3 Schreiber- und Deploy-Matrix

| Remote-Zielpfad | Lokale Quelle | Orchestrator | Unterbau-Skript | Modus | Protected/Excluded | Beleg |
|---|---|---|---|---|---|---|
| /srv/webapps/corapan/runtime/corapan/data/db/public | %CORAPAN_RUNTIME_ROOT%/data/db/public und selektiv %CORAPAN_RUNTIME_ROOT%/data/db/{stats_files.db,stats_country.db} | deploy_data.ps1 | sync_data.ps1 + sync_core.ps1 | rsync Delta, overwrite, --delete fuer Verzeichnis; einzelne Stats-DBs separat per rsync | db als Ganzes hard-blocked; nur stats_files.db und stats_country.db erlaubt | sync_data.ps1 DATA_DIRECTORIES, STATS_DB_FILES, HARD_BLOCKED_PATHS, ALLOWED_STATS_DBS |
| /srv/webapps/corapan/runtime/corapan/data/public/metadata | %CORAPAN_RUNTIME_ROOT%/data/public/metadata | deploy_data.ps1 | sync_data.ps1 + sync_core.ps1 | rsync Delta, overwrite, --delete | blacklab_index, blacklab_index.backup, stats_temp, db, .sync_state ausgeschlossen | sync_data.ps1 DATA_DIRECTORIES; sync_core.ps1 rsync excludes |
| /srv/webapps/corapan/runtime/corapan/data/exports | %CORAPAN_RUNTIME_ROOT%/data/exports | deploy_data.ps1 | sync_data.ps1 + sync_core.ps1 | rsync Delta, overwrite, --delete | wie oben | sync_data.ps1 DATA_DIRECTORIES |
| /srv/webapps/corapan/runtime/corapan/data/blacklab_export | %CORAPAN_RUNTIME_ROOT%/data/blacklab_export | deploy_data.ps1 | sync_data.ps1 + sync_core.ps1 | rsync Delta, overwrite, --delete | wie oben | sync_data.ps1 DATA_DIRECTORIES |
| /srv/webapps/corapan/runtime/corapan/data/public/statistics | PUBLIC_STATS_DIR oder %CORAPAN_RUNTIME_ROOT%/data/public/statistics | deploy_data.ps1 | Sync-StatisticsFiles in sync_data.ps1 | overwrite-only, selektive Einzeldatei-Uebertragung, kein delete | nur corpus_stats.json und viz_*.png erlaubt; Repo-Root-Guard; Post-Upload-Verifikation | sync_data.ps1 Sync-StatisticsFiles; scripts/deploy_sync/README.md |
| /srv/webapps/corapan/runtime/corapan/media/transcripts | %CORAPAN_RUNTIME_ROOT%/media/transcripts | deploy_media.ps1 | sync_media.ps1 + sync_core.ps1 | rsync Delta, overwrite, --delete, --partial | mp3-temp nicht im Deploy; .sync_state ausgeschlossen | sync_media.ps1 MEDIA_DIRECTORIES; sync_core.ps1 rsync excludes |
| /srv/webapps/corapan/runtime/corapan/media/mp3-full | %CORAPAN_RUNTIME_ROOT%/media/mp3-full | deploy_media.ps1 | sync_media.ps1 + sync_core.ps1 | rsync Delta, overwrite, --delete, --partial | mp3-temp nicht im Deploy; ForceMP3 moeglich | sync_media.ps1 MEDIA_DIRECTORIES |
| /srv/webapps/corapan/runtime/corapan/media/mp3-split | %CORAPAN_RUNTIME_ROOT%/media/mp3-split | deploy_media.ps1 | sync_media.ps1 + sync_core.ps1 | rsync Delta, overwrite, --delete, --partial | mp3-temp nicht im Deploy; ForceMP3 moeglich | sync_media.ps1 MEDIA_DIRECTORIES |
| /srv/webapps/corapan/runtime/corapan/data/blacklab_index.new und danach /srv/webapps/corapan/runtime/corapan/data/blacklab_index | RepoRoot/data/blacklab_index.new | publish_blacklab.ps1 | publish_blacklab_index.ps1 + _lib/ssh.ps1 | tar+ssh oder scp Upload, Remote-Validierung per Docker, atomischer Swap, Backup-Retention | DryRun, Validierungs-Gate, Backup-Retention; aber Live-BlackLab liest anderen Pfad -> HIGH_RISK | publish_blacklab.ps1 ruft publish_blacklab_index.ps1 ohne DataDir-Override; publish_blacklab_index.ps1 DataDir=Get-RemotePaths().DataRoot |
| /srv/webapps/corapan/app und damit /srv/webapps/corapan/app/config/blacklab | origin/main Git checkout auf dem Runner-Host | GitHub Actions deploy.yml | scripts/deploy_prod.sh | git fetch + git reset --hard + docker compose rebuild/recreate | passwords.env extern; Runtime-Mounts werden anschliessend geprueft | .github/workflows/deploy.yml; scripts/deploy_prod.sh |

## 7.4 Tote Pfade

Die folgenden Pfade sind nach aktueller Evidenz tote oder praktisch tote Ziele fuer den aktuellen Standardbetrieb:

- /srv/webapps/corapan/logs
  - alter paralleler Logpfad, aktueller App-Schreiber zeigt auf runtime/corapan/logs
- /srv/webapps/corapan/data/blacklab_export
  - kein aktiver Leser im aktuellen Web-App- oder Container-Pfad belegt
- /srv/webapps/corapan/runtime/corapan/data/blacklab_index
  - nicht tot als Deploy-Ziel, aber tot als Live-Verbraucherpfad

Blockiert, nicht als tot klassifizierbar:

- /srv/webapps/corapan/data
- /srv/webapps/corapan/runtime/corapan/data

Begruendung:

- beide sind Eltern aktiver Teilpfade
- beide enthalten gemischte aktive und inaktive Teilrealitaeten

## 7.5 Hochriskante Pfade

- Docker volume corapan_postgres_prod
- /srv/webapps/corapan/config/passwords.env
- /srv/webapps/corapan/app/config/blacklab
- /srv/webapps/corapan/data/blacklab_index
- /srv/webapps/corapan/runtime/corapan/data/blacklab_index
- /srv/webapps/corapan/runtime/corapan/media
- /srv/webapps/corapan/runtime/corapan/data/db/public
- /srv/webapps/corapan/runtime/corapan/data/stats_temp

Besonders kritisch ist die BlackLab-Kombination:

- Live-Leser: top-level blacklab_index
- Default-Deploy-Ziel: runtime/corapan/data/blacklab_index

Das ist derzeit der schwaechste Punkt der Produktionspfadrealitaet.

## 7.6 Ueberraschungen

1. Der aktuelle BlackLab-Publish-Unterbau ist nicht auf den live gelesenen BlackLab-Pfad ausgerichtet.
2. deploy_data.ps1 und deploy_media.ps1 sind sauber runtime-first; genau BlackLab faellt aus diesem Modell heraus.
3. README_STATISTICS_DEPLOY.md enthaelt noch eine Top-Level-Statistik-Zielbeschreibung, waehrend der aktuelle Code runtime-first deployt.
4. /srv/webapps/corapan/runtime/corapan/data/blacklab_index ist kein blosses Archiv, sondern ein aktives Deploy-Ziel ohne belegt aktiven Leser.
5. Der self-hosted GitHub Runner ist Teil der produktiven Pfadrealitaet, weil er /srv/webapps/corapan/app und damit app/config/blacklab aktiv fortschreibt.

## 7.7 Ableitbare sichere Moves (noch NICHT ausfuehren)

- /srv/webapps/corapan/runtime/corapan/data/blacklab_index
  - kann nicht geloescht werden
  - zuerst BlackLab-Publish-Ziel und Live-BlackLab-Leser auf denselben Pfad bringen
  - bis dahin blockiert

- /srv/webapps/corapan/data/blacklab_index
  - muss bleiben, solange der live BlackLab-Container top-level liest
  - spaetere Migration noetig, keine Loeschung

- /srv/webapps/corapan/runtime/corapan/data/blacklab_export
  - muss bleiben
  - ist aktiver Web-App-Reader- und deploy_data-Zielpfad

- /srv/webapps/corapan/data/blacklab_export
  - potentiell entfernbar, aber erst nach expliziter Bestaetigung, dass kein manueller BlackLab-/Ops-Prozess mehr darauf angewiesen ist
  - derzeit blockiert

- /srv/webapps/corapan/runtime/corapan/logs
  - muss bleiben
  - aktiver App-Logpfad

- /srv/webapps/corapan/logs
  - potentiell spaeter entfernbar
  - zuerst pruefen, ob externe Logrotate/Ops-Routinen darauf zeigen
  - derzeit blockiert mangels kompletter Host-Ops-Inventur

- /srv/webapps/corapan/runtime/corapan/data/db/public
  - muss bleiben
  - aktiver Web-App-Reader und deploy_data-Zielpfad

- /srv/webapps/corapan/runtime/corapan/data/stats_temp
  - muss bleiben
  - aktiver Cache- und Deploy-Write-Test-Pfad

## Lessons Learned – Run 2026-03-20 (Consumer Matrix)

- Problem:
  Ohne explizite Leser-/Schreiber-Matrix liessen sich doppelte PROD-Pfade weiterhin fuer gleichwertig halten, obwohl unterschiedliche Orchestratoren und Live-Verbraucher verschiedene Pfade benutzen.
- Erkenntnis:
  Deploy-Orchestratoren und Sync-Unterbau sind selbst Teil der produktiven Pfadrealitaet. Besonders kritisch ist, wenn ein Standard-Deploy-Ziel nicht mit dem live gelesenen Produktionspfad uebereinstimmt, wie aktuell bei BlackLab.
- Neue Regel:
  Ein Pfad darf erst entfernt oder vereinheitlicht werden, wenn alle Leser, Schreiber und Deploy-Ziele vollstaendig bekannt sind.
- Neue Zusatzregel:
  Deploy-Orchestratoren und Sync-Skripte sind Teil der produktiven Pfadrealitaet und duerfen nie als blosse Hilfsskripte ignoriert werden.