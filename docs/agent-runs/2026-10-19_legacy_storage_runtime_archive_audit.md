# Legacy-CO.RA.PAN – Read-only Storage-, Runtime- und Archiv-Audit

Datum: 2026-10-19 · Repo-HEAD: `713629bd3b85cf6739db4cb689314879074493bc` (Branch `main`)
Art: reiner Audit. Keine Bereinigung, kein Deployment, kein Commit, kein Push.

Legende: **VERIFIED** (durch Inspektion bestätigt) · **REPORTED** (aus Doku/Berichten übernommen) · **INFERRED** (plausibler Schluss) · **UNKNOWN** (nicht belegt).
Größen: lokale Werte in MiB/GiB (1024er-Basis), Serverwerte wie in der Quelle (`du -h`, ebenfalls 1024er-Basis).

## 0. Gesamtbewertung

| Bereich | Bewertung | Grund |
|---|---|---|
| A Architektur / Code-Abhängigkeiten | **PASS** | Code, Compose, Workflow und Deploy-Skript gelesen |
| B Audio / Splits | **PASS** (Code) / **PARTIAL** (Laufzeitevidenz) | Eindeutiger Codebefund, aber keine Server-Logs/Zugriffsstatistik, keine Dekodier-Äquivalenzprüfung |
| C Lokale Bestände / Duplikate | **PASS** für `legacy/corapan`; **PARTIAL** für Nachbarverzeichnisse | Hash-Prüfung durchgeführt; Nachbarordner nur oberflächlich |
| D Zenodo | **PARTIAL** | Metadaten und Sample verifiziert; Full-Corpus-Record ist restricted, Dateiliste/Checksummen öffentlich nicht sichtbar |
| E Minimalarchitektur | **PASS** (als Vorschlag) | stützt sich teilweise auf REPORTED-Serverstand von März 2026 |
| Server / Produktion live | **BLOCKED** | Kein zulässiger lesender Zugriffsweg in dieser Session. Alle Serverzahlen sind REPORTED (Stand 2026-03-25, ~7 Monate alt). |

Ein Restore wurde **nicht** getestet. Es gibt keinen Restore-Nachweis.

## 1. Ausgangsstand und Scope

- Geprüft: `legacy/corapan` komplett (`app/`, `docs/`, `scripts/`, `.github/`, `data/`, `media/`, `tmp/`, `maintenance_pipelines/`, `.git`, `.venv`).
- Nachbarn unter `panhispanic_media_corpora/` nur oberflächlich (Größen/Namen): `corapan_storage`, `corapan_workspace/legacy_checkout_runtime`, `legacy/coprepan`, `legacy/corapan_coprepan_studies`. Sie gehören zu CO.RA.PAN_v3 / CO.PRE.PAN und wurden nicht bewertet oder verändert.
- Nicht geprüft: das in `git remote` eingetragene lokale Backup-Repo `C:\dev\corapan_git_backups\…` (liegt außerhalb des erlaubten Bereichs).
- Git-Status zu Beginn: 35 Einträge (`M`/`D`/`??`), vorher schon vorhanden (laufende Annotationsarbeit in `maintenance_pipelines/_0_json`). Am Ende unverändert (siehe §13).
- Nicht gelesen: `passwords.env`, `.env`-Dateien, Datenbankinhalte, Tokens.
- Ausgeführt wurden nur: Dateisystem-Inventar, CRC32/SHA-256-Berechnung auf lokalen Dateien, Lesen von ZIP-Zentralverzeichnissen, öffentliche Zenodo-API-Abfragen (Metadaten). Keine Projektskripte, keine Container, keine Tests.
- Hilfsskripte lagen ausschließlich im Session-Scratchpad (nicht im Repo).

## 2. Quellen und tatsächliche Zugriffsreichweite

| Quelle | Reichweite |
|---|---|
| Repo-Code/Config (`app/src`, `app/infra`, `.github/workflows/deploy.yml`, `app/scripts/*`) | vollständig lesbar |
| Doku (`docs/*`, besonders `docs/rsync/server-agent_rsync_audit.md`, `docs/rsync/blacklab_publish_proof_run.md`) | lesbar; Serverzahlen daraus = REPORTED (2026-03-25) |
| Lokales Dateisystem | lesbar |
| Produktivserver, Docker, Postgres-Volume, nginx, Cron | **kein Zugriff** |
| Zenodo öffentliche API | 4 Records abgefragt; Restricted-Record liefert keine Dateiliste |
| GitHub | nicht abgefragt (nur lokale Tags/Remotes) |

## 3. Architektur und produktive Datenabhängigkeiten

**Deploy-Pfad (VERIFIED, Code):** Push auf `main` → Self-hosted Runner auf dem Server → `git reset --hard $GITHUB_SHA` im Checkout → `app/scripts/deploy_prod.sh` → `docker compose … up -d --force-recreate --build` für **`db` (postgres:14) und `web`**. Danach werden Mounts, Schreibtest und `/health` geprüft.

**Bind-Mounts des Web-Containers (VERIFIED):** `/srv/webapps/corapan/{data,media,logs}` → `/app/{data,media,logs}`, `/srv/webapps/corapan/data/config` → `/app/config`. Postgres liegt im **benannten Docker-Volume** `corapan_postgres_prod`, also nicht unter `/srv`.

**BlackLab ist nicht Teil des Compose-Stacks (VERIFIED).** Der Container `corapan-blacklab` wird separat per `app/scripts/blacklab/run_bls_prod.sh` gestartet (`docker run`, Index read-only aus `/srv/webapps/corapan/data/blacklab/index`, Config aus dem Checkout). `deploy_prod.sh` startet ihn nicht.

| Datenbestand | Erzeuger | Leser | Runtime | Rebuild-Deploy braucht ihn | Rekonstruierbar | Folge bei Fehlen |
|---|---|---|---|---|---|---|
| `media/mp3-full` | Operator-Sync (`sync_media.ps1`, rsync) | `/media/full/*` (Player, Editor, Overview), Fallback in `build_snippet` | **ja** | ja (nicht im Git) | nur aus Quellaufnahmen/Zenodo-ZIP (Bytes identisch, §7) | Player und Snippets fallen aus |
| `media/mp3-split` | `maintenance_pipelines/_0_mp3/mp3_prepare_and_split.py` | nur `build_snippet` (Beschleunigung) und JWT-Route `/media/split/*` | **nein, funktional entbehrlich** (§5) | nein | ja, aus `mp3-full` (§5) | Snippets langsamer, kein Funktionsverlust |
| `media/mp3-temp` | `build_snippet` (Cache, Cleanup nach 30 min) | `/media/temp`, `/media/play_audio` | ja (Cache) | nein | ja | Cache baut sich neu auf |
| `media/transcripts` | Pipeline `_0_json` → Sync | `/media/transcripts/*`, Editor (schreibt Edits und `backup/`), Player | **ja**, vom Editor beschreibbar | ja | nur eingeschränkt: Editor-Änderungen auf dem Server sind eine eigene Wahrheit | Player/Editor ohne Text |
| `data/blacklab/index` | `build_blacklab_index_prod.sh` oder Publish von lokal | BlackLab-Container | ja (Suche) | ja | rebuildbar aus TSV-Export (1,5 GiB) + Config | Suche tot |
| `data/blacklab/export/tsv` | Pipeline lokal | nur Index-Rebuild | nein | nein | aus Transkripten (INFERRED) | Rebuild nicht ohne Neuerzeugung möglich |
| `data/db/public/*.db` (SQLite, 2 Dateien) | `03_build_metadata_stats.py` | Atlas/Editor/Stats | ja | ja | ja (Skript) | Atlas/Stats leer |
| `data/public/{metadata,statistics}` | `05_publish…`, Export-Skripte | Download-/Stats-Routen | ja | ja | ja | Downloads/Charts fehlen |
| Postgres-Volume (Auth, Nutzer, Analytics) | App | App | **ja** | ja | **nicht rekonstruierbar** | Nutzerverwaltung verloren |
| `config/passwords.env` | Operator | Compose | ja | ja | nein | Deploy bricht ab |

**Differenz Betrieb vs. reproduzierbares Redeployment (VERIFIED aus Code, INFERRED in der Wirkung):** Ein frischer Lauf von `deploy_prod.sh` auf leerem Host baut nur Web und DB. Es fehlen dann Medien, Transkripte, BlackLab-Container und -Index, öffentliche Metadaten/Statistik, die SQLite-DBs, `passwords.env` und die Postgres-Daten. Auch nginx/TLS ist nicht im Repo (UNKNOWN). Die Doku behauptet teils Gegenteiliges (`docs/architecture/deployment-runtime.md` und `overview.md` beschreiben ein altes `docker-compose.yml`, ein Verzeichnis `~/corapan/…` und Port 8000; `production.md` hat einen Cron-Platzhalter ohne Pfad). Maßgeblich ist der Code (`app/infra/docker-compose.prod.yml`).

**Backup-Realität (VERIFIED im Code, UNKNOWN im Betrieb):** `app/scripts/backup.sh` verwendet Pfade wie `~/corapan/backups` und `/root/…`, die nicht dem aktuellen `/srv/webapps/corapan`-Layout entsprechen. Es sichert standardmäßig nur Counter-Daten. Ob ein Cronjob läuft und ob ein Postgres-Dump existiert, ist nicht belegt. Serverseitig war `backups` (BlackLab) am 2026-03-25 leer (REPORTED).

## 4. Speicherinventar

### 4.1 Lokal (`legacy/corapan`), VERIFIED

Gesamt ≈ **31,6 GiB** logisch. Allokiert = logisch (keine Hardlinks, Reparse-Points, Cloud-Platzhalter oder Kompression festgestellt).

| Pfad | Klasse | Dateien | Größe |
|---|---|---:|---:|
| `media/mp3-split` | Audio-Derivat | 2.706 | 7.821 MiB |
| `media/mp3-full` | Audio-Original | 147 (146 MP3) | 6.609 MiB |
| `media/transcripts` | annotierte JSON | 149 | 731 MiB |
| `media/mp3-temp` | Cache | 6 | 0,6 MiB |
| `maintenance_pipelines/_1_zenodo-repos/Zenodo Full Corpus` | 25 ZIPs | 25 | 6.546 MiB |
| `maintenance_pipelines/_0_json/backups` | JSON-Sicherungen | 398 | 2.378 MiB |
| `data/blacklab/quarantine` | Index-Reste | 1.190 | 2.277 MiB |
| `data/blacklab/export` | TSV-Export | 738 | 1.466 MiB |
| `data/blacklab/backups` | Index-Backups | 148 | 557 MiB |
| `data/blacklab/index` | aktiver Index | 74 | 279 MiB |
| `data/exports/tsv` | TSV (anderes Schema?) | 146 | 162 MiB |
| `data/db` | Dev-Postgres + 2 SQLite | 2.598 | 92 MiB |
| `tmp/` | Validierungsreste | 114 | 1.694 MiB |
| `.venv` | Python-Umgebung | 34.043 | 1.501 MiB |
| `.git` | Historie | 1.306 | 194 MiB |
| `maintenance_pipelines` sonst (`bfg.jar`, Docs, Results, Logs) | | ~100 | ~45 MiB |
| `app/` (Code, tools/cwrsync 12 MiB) | | 484 | 21 MiB |

### 4.2 Produktivserver, REPORTED (Stand 2026-03-25, Quelle `docs/rsync/server-agent_rsync_audit.md`, `blacklab_publish_proof_run.md`)

| Pfad | Größe |
|---|---:|
| `/srv/webapps/corapan` gesamt | 20 G |
| `media` | 15 G (`mp3-full` 6,5 G · `mp3-split` 7,7 G · `transcripts` 738 M · `mp3-temp` 5 M) |
| `data` | 1,8 G (`blacklab/export` 1,5 G · `blacklab/index` 279 M · `public` 7,2 M · `tsv_json_test` 9,3 M) |
| `runner` (Self-hosted Runner inkl. zweitem Code-Checkout) | 2,4 G |
| `app` (Checkout) | 232 M |
| `logs` | 4,5 M |
| Dateisystem `/dev/sda2` | 50 G, belegt 40 G, frei 9,5 G (die übrigen ~20 G außerhalb `/srv/webapps/corapan` sind unbekannt, vermutlich Docker-Images/Volumes/OS) |

Die Serverwerte decken sich größenmäßig mit den lokalen Beständen für `mp3-full`, `mp3-split` und den Index. Gleiche Bytes sind das aber nicht (UNKNOWN). Einzige Ausnahme: der BlackLab-Index wurde laut Proof-Run von lokal publiziert (278,6 MiB, 74 Dateien, Bytezahl der Quelle dokumentiert).

## 5. Audioanalyse und Rekonstruktionsmöglichkeiten

**Codebefund (VERIFIED):**
- Der Player und der Editor laden ausschließlich `/media/full/<datei>.mp3` (`player-overview.js`, `editor-player.js`, Template `search/_results.html`, `routes/player.py`). Gestreamt wird die komplette Aufnahme.
- `mp3-split` wird nur an einer Stelle gelesen: `audio_snippets.build_snippet()` → `find_split_file()`. Die Funktion nutzt ein fest einkodiertes Raster `SPLIT_TIMES` (4-Minuten-Chunks mit 30 s Überlappung, `_01`…`_29`) und schneidet per ffmpeg das Snippet aus dem passenden Split. Findet sie keinen, fällt sie auf `safe_audio_full_path()` zurück („slower but always works“). Das Ergebnis wird als Cache in `mp3-temp` abgelegt.
- Die zweite Stelle ist die JWT-geschützte Route `GET /media/split/<datei>`. Im gesamten App-Frontend (JS/HTML/Templates) gibt es dafür **keinen Aufrufer** (VERIFIED für `app/`). Externe Nutzer der Route sind UNKNOWN.
- ffmpeg ist im Image installiert (`Dockerfile`) und zusätzlich über `imageio-ffmpeg` in `requirements.txt`.
- Erzeugung der Splits (VERIFIED, Skript gelesen, nicht ausgeführt): `_0_mp3/mp3_prepare_and_split.py` konvertiert VBR→CBR, normalisiert Lautheit (-18 LUFS) **in place** auf den Fulls und splittet dann in 4-Minuten-Stücke mit 30 s Überlappung. Chunk-Dauer, Überlappung und Normalisierung sind per CLI-Parameter änderbar. Die tatsächlich verwendeten Parameter sind nicht protokolliert.

**Einordnung nach Schema A–E:** am nächsten bei **D**. Die Original-MP3 sind produktiv notwendig; die Splits sind ein reiner Latenz-Cache für Snippets, der vollständig aus den Fulls rekonstruierbar ist und funktional nicht benötigt wird. Es ist weder A (nicht temporär im Laufzeitsinn: sie liegen dauerhaft und werden nie aufgeräumt) noch B, C oder E.

**Offene Punkte vor jeder Entfernung (UNKNOWN):**
- Es gibt keine Hash-/Dekodier-Äquivalenzprüfung zwischen Split-Snippet und Full-Snippet. Das Ergebnis ist praktisch gleich, aber das Rastermapping (z. B. Encoder-Delay, 1-Frame-Versatz) wurde nicht gemessen.
- Es gibt keine Zugriffs-/Latenzdaten dafür, wie häufig Snippets entstehen und wie viel langsamer der Fallback ist. Der Quellcode-Kommentar nennt „~6–10× schneller“ (REPORTED, nicht gemessen).
- Der Web-Container ist auf 2 CPUs und 2 GB RAM limitiert (Compose). Ein ffmpeg-Seek in ~1 h langen MP3 ist bei CBR gut machbar, wurde aber nicht gemessen.
- Die Fulls sind laut Skript bereits normalisiert/CBR; ob die Server-Fulls dasselbe sind wie lokale Fulls, ist nicht belegt.
- Lokale Daten: Split-Anzahl 2.706 (≈ 18,4 pro Full). Für **PER (4 Fulls)** und **CHL/ARG-CBA (5)** sind weniger Splits vorhanden. Das passt zu weniger Fulls (INFERRED).

**Ergebnis „schlanke Online-Audiohaltung“:** Technisch möglich: nur `mp3-full` (6,5 G) + Transkripte online, `mp3-split` (7,7 G) entfernen. Das ist ein Kategorie-C-Eingriff mit Mess- und Rückfallplan (§9). Vollständige Quellaudios *offline zu lagern* ist dagegen **nicht** möglich, ohne den Player abzuschalten, denn der Player streamt `mp3-full`.

## 6. Lokale Duplikate, Zwischenstände und Exportarchive

Alle Aussagen SHA-256 bzw. CRC32+Größe, VERIFIED, sofern nicht anders markiert.

| Befund | Ergebnis |
|---|---|
| `data/blacklab/export/tsv/tsv_for_index` vs. `…bak_20260117_002730` vs. `…bak_20260117_005855` | **146/146 Dateien pro Paar byte-identisch** (3 × 364 MiB, nur eine Kopie unabhängig) |
| `data/blacklab/index` vs. `quarantine/index.build` | **74/74 identisch** (279 MiB doppelt) |
| `data/blacklab/index` vs. `backups/index_2026-03-21_001627` und `…03-20_230703` | **verschieden** (nur 1 von 74 Dateien gleich → eigenständige Builds); `index_2026-03-20_225814` ist leer |
| `quarantine/…/blacklab_wrong_root` (279 MiB, 79 Dateien) | ≠ aktiver Index (1 von 64 Hashes gleich); `prior_unused_snapshot` (1.720 MiB) nicht verglichen: Inhalt UNKNOWN |
| `data/exports/tsv` (146 Dateien, 162 MiB) vs. `tsv_for_index` | **0/146 gleich**: anderes Schema/Stand, Verwendung UNKNOWN |
| `Zenodo Full Corpus/*.zip` MP3-Mitglieder vs. `media/mp3-full` | **146/146 MP3 byte-identisch** (Größe + CRC32) |
| `Zenodo Full Corpus/*.zip` JSON-Mitglieder vs. aktuelles `media/transcripts` | **0/146 identisch** (aktuelle JSON sind neuer und kleiner; v3.x-Tense-Schema, Migration 2026-06-14) |
| `_0_json/backups/pre-v3_1-transcripts/20260614T080916Z` vs. ZIP-JSON | **146/146 identisch** → diese Sicherung *ist* der in den ZIPs enthaltene Annotationsstand |
| `_0_json/backups/pre-tense-schema-migration/…` vs. ZIP-JSON | 0/146 (Zwischenstand) |
| `tmp/sync-validation/src-many` (100 JSON, 491 MiB) | Inhalte in `pre-v3_1-transcripts` **wiederzufinden (100/100 Hashes)** → Test-Kopien |
| `tmp/sync-validation/src-large` (1 GiB `.bin`) und `src-small` | synthetische Testdatei (INFERRED aus Name/Endung, Inhalt nicht geprüft) |
| ZIP-Pakete ≙ MP3 | ZIPs (6,4 GiB MP3-Anteil) sind inhaltlich eine zweite Kopie von `mp3-full` |
| Zusätzliche lokale Dateien außerhalb der ZIPs | `media/transcripts/edit_log.jsonl`, `…/ESP-SEV/2024-03-19_ESP-SEV_RSev.json.bak_tense` |

Hinweise: ZIPs sind komprimierte DEFLATE-Pakete; MP3 komprimieren kaum (ZIP 6,55 GiB vs. 7,17 GiB unkomprimiert). Das Speichern der ZIPs *und* der entpackten Fulls ist eine echte Doppelung (~6,4 GiB). Im Repository liegt `.gitignore` auf `data/`, `media/`, `tmp/`, also sind diese Bestände nicht in Git gesichert.

Nicht verfolgte (aber gesetzte) Bereinigungsspuren: `maintenance_pipelines/_0_json/backups/smoke-tests` (~155 MiB, ~35 Mini-Sicherungen) und `multicountry-smoke` (142 MiB) sind Testläufe vom 2026-06-14 (Inhalt nicht auf Redundanz geprüft).

## 7. Zenodo-Abgleich und Archivvollständigkeit

Abfrage der öffentlichen Zenodo-API am 2026-10-19 (nur Metadaten).

| Record | Concept-DOI | Aktuelle Version-DOI | Datum | Zugriff | Dateien (öffentlich sichtbar) |
|---|---|---|---|---|---|
| Full Corpus | 10.5281/zenodo.15360942 | 10.5281/zenodo.18782190 (Version 3, „last“) | 2026-02-26 | **restricted** | **Liste leer/unsichtbar**, keine Checksummen abrufbar |
| Sample Corpus | 10.5281/zenodo.15378479 | 10.5281/zenodo.17847425 | 2025-12-07 | open | 3 Dateien, MD5 sichtbar |
| Metadata | 10.5281/zenodo.17843469 | 10.5281/zenodo.17843470 (v1.0.0) | 2025-12-06 | open (CC-BY) | 56 Dateien, MD5 sichtbar |
| Web App & Code | 10.5281/zenodo.17834023 | 10.5281/zenodo.19202684 (v1.1.0) | 2026-03-24 | open | 1 ZIP (26.406.252 B, MD5 `b8ef9d33…`) |

**Verifiziert gegen lokale Pakete:**
- *Metadata*: Größen aller sichtbaren Dateien und MD5 von 6 stichprobenhaft geprüften Dateien (`corapan_recordings.json/.tsv/.jsonld`, `tei_headers.zip`, `corapan_corpus_metadata.json`, `…_CRI.tsv`) stimmen mit dem lokalen Ordner `Zenodo Metadata` überein (VERIFIED für diese 6; die restlichen 50 INFERRED über gleiche Größen).
- *Sample*: MD5 aller 3 Dateien stimmen überein (VERIFIED).
- *Full Corpus*: Der Zenodo-Record ist restricted. Ein Abgleich lokaler ZIPs ↔ hochgeladene ZIPs ist **nicht möglich** (UNKNOWN). Indizien: ZIP-Zeitstempel (2026-02-26) = Publikationsdatum von Version 3; `zip_process.log` dokumentiert die Zusammenstellung. Das spricht dafür, dass die lokalen ZIPs der hochgeladene Stand sind (INFERRED, nicht bewiesen).
- *Software*: Der archivierte Tag ist `v1.1.0` (Commit vom 2026-03-24). `main` liegt **19 Commits weiter** (u. a. GoatCounter, Health/Ready-Split, Rate-Limit-Ausnahme, BlackLab-Pfadvalidierung). Diese Änderungen sind **nicht** in Zenodo archiviert (VERIFIED lokal, Archivinhalt nur über Größe/Tag).

**Inhaltliche Abdeckung (laut ZIP-Struktur, VERIFIED lokal):** 25 Länder-/Regionspakete (292 Mitglieder = 146 MP3 + 146 JSON, 7,17 GiB unkomprimiert) mit `mp3-files/` und `json-transcripts/`. Beschreibung des Records (REPORTED): MP3 + annotierte JSON mit spaCy-Annotation und Tense-Kategorisierung.

**Was Zenodo NICHT abdeckt (VERIFIED aus Pakettiteln/-struktur, INFERRED für die Wirkung):**
- `mp3-split` (nicht nötig).
- Aktuellen Annotationsstand v3.2 (Juni 2026): ZIP enthält den Stand vor der Migration (siehe §6). Entweder ist Version 4 nötig, oder es muss bewusst entschieden werden, welcher Stand der wissenschaftliche Referenzstand ist.
- Serverseitige Editor-Änderungen an Transkripten (`edit_log.jsonl`, `backup/`) – falls es solche gibt (UNKNOWN).
- BlackLab-Index und TSV-Export, SQLite-Statistik-DBs, öffentliche Statistik-Artefakte.
- Postgres/Nutzerdaten, Secrets, nginx-/Server-Konfiguration.
- Commits nach v1.1.0.
- Das Sample-Corpus-README verweist noch auf die alte Webapp-URL (`corapan.online.uni-marburg.de`); der Full-Corpus-Record verweist auf einen nie ersetzten DOI-Platzhalter für das Metadata-Paket (REPORTED aus Record-Beschreibung).

**Drei Anforderungen getrennt:**
- *Wissenschaftliche Langzeitarchivierung*: weitgehend gedeckt (Audio + Transkripte Stand Feb 2026, Metadaten, Sample, Code v1.1.0). Lücken: v3.2-Annotation, Dateiliste/Checksummen des Restricted-Records nicht unabhängig prüfbar, Commits nach v1.1.0.
- *Produktionswiederherstellung*: **nicht** durch Zenodo gedeckt (Index, DBs, Auth, Config, Server-State).
- *Disaster Recovery*: kein belegtes Backup für Postgres, Server-Transkripte, `passwords.env`. **Kein Restore-Nachweis.**

## 8. Risiken für Betrieb, Redeployment und Restore

1. **Auth-/Nutzerdaten ohne belegtes Backup** (Postgres-Volume; `backup.sh` veraltet) – höchstes Risiko, klein im Volumen.
2. **Server ist Single Point of Truth** für den Live-Zustand von Transkripten (Editor schreibt dort), `data/config`, nginx/TLS. Ob dieser Stand lokal oder auf Zenodo existiert, ist UNKNOWN. Serverseitig `transcripts` = 738 M (Stand Nov 2025) vs. lokal 731 MiB nach Migration.
3. **Zustandsdivergenz**: Lokal laufen seit 2026-06-14 Annotation-v3.x/Tense-Migrationen (uncommitted). Live-Index stammt von 2026-03-21/22. Es ist nicht belegt, ob die Produktion davon betroffen ist oder bleibt. Vor jedem Sync/Publish ist das zu klären (insbesondere, weil `sync_media.ps1` mit `--delete` arbeitet; Quelle `docs/rsync/2026-03-25_server-sync-audit.md`).
4. **Kein vollautomatischer Wiederaufbau**: BlackLab-Start, Medien-Sync, Index-Publish sind manuelle Operatorschritte.
5. **Platz**: 9,5 G frei (Stand März); Index-Rebuild verlangt Platz für alten + neuen Index + Backup (~0,8 GiB). Aktuelle Auslastung UNKNOWN.
6. **Self-hosted Runner** (2,4 G, zweiter Code-Checkout) dauerhaft auf dem Produktivserver: Sicherheits-/Wartungsthema für den eingefrorenen Betrieb (Token, Updates).
7. **Doku-Drift**: `deployment-runtime.md`/`overview.md` beschreiben einen alten Stack (siehe §3). Wer danach rekonstruiert, baut falsch.
8. **Verwaiste Doku-Verweise**: Zenodo-DOIs inkonsistent beschrieben (Metadata-DOI im README als „folgt“, im Record vergeben).

## 9. Einsparpotenziale ohne Doppelzählung

Zählregeln: Jede Position taucht nur einmal auf. GiB gerundet.

### 9.1 Produktivserver (REPORTED-Basis März 2026; keine Live-Prüfung)

| Position | Betrag | Voraussetzung | Kategorie |
|---|---:|---|---|
| `media/mp3-split` entfernen | **≈ 7,7 G** | Latenzmessung des Fallbacks; Rückfall = Rückkopie aus lokalem Bestand/Neuerzeugung; Server-Fulls == lokale Fulls prüfen | C |
| `data/blacklab/export` (TSV, 1,5 G) offline auslagern | ≈ 1,5 G | Nachweis, dass lokaler TSV-Satz == Server-Satz und Rebuild aus Transkripten funktioniert | B/C |
| Runner-Zweitcheckout (`runner/_work`) | nicht abschätzbar (Teil von 2,4 G) | Server-Zugriff nötig | UNKNOWN |
| Docker-Images/Volumes (~20 G außerhalb `/srv/webapps/corapan`) | nicht abschätzbar | Server-Zugriff nötig | UNKNOWN |
| **Summe belegbar** | **≈ 9,2 G** (von 40 G belegt; freier Platz 9,5 G → ≈ 18,7 G) | | |

### 9.2 Lokale Datenträger (VERIFIED, Größen in GiB)

| Position | GiB | Kategorie | Beweisniveau |
|---|---:|---|---|
| 2 identische `tsv_for_index.bak_*` | 0,71 | A | hash-identisch |
| `quarantine/index.build` (= aktiver Index) | 0,27 | A | hash-identisch |
| `tmp/` gesamt (Test-/Validierungsreste, `src-many` hash-belegt als Kopie) | 1,65 | A | teils INFERRED |
| **Kategorie A gesamt** | **≈ 2,6** | | |
| `data/blacklab/quarantine` Rest (`prior_unused_snapshot`, `wrong_root`, Altbackup) | 1,95 | B (Prüfen/Auslagern) | Inhalt von `prior_unused_snapshot` UNKNOWN |
| `data/blacklab/backups` (2 echte, 1 leer) | 0,54 | B | eigenständige Builds |
| `_0_json/backups` (Smoke-/Zwischenstände 0,30 + zwei Vollsicherungen 2,0) | 2,32 | B | pre-v3_1 == Zenodo-JSON; Rest verschieden |
| `data/exports/tsv` | 0,16 | INVESTIGATE | unklarer Zweck |
| Zenodo-ZIPs ↔ `mp3-full`: eine der beiden Mp3-Kopien (6,4 GiB) | 6,4 | B/CONSOLIDATE | je nach Primärkopie |
| `mp3-split` lokal (bei Entscheidung C auf Server) | 7,64 | C/REGENERABLE | regenerierbar |
| `.venv` | 1,47 | REGENERABLE | neu aufbaubar |
| **Summe alle Positionen** | **≈ 23,1 GiB** von 31,6 | | |

Nicht doppelt zählen: Die 6,4 GiB sind entweder die ZIPs oder `mp3-full` (nicht beide); ZIPs enthalten außerdem die *alten* JSON, die identisch zu `pre-v3_1-transcripts` sind (die 0,99 GiB JSON-Anteil der ZIPs überlappen mit der Sicherung). Realistisch entfernbar *ohne Archivverlust* nach Auslagerung auf externen Speicher: Kategorie A (2,6) + B (≈ 5,0) = **≈ 7,6 GiB**, zusätzlich REGENERABLE (`mp3-split`, `.venv`) ≈ 9,1 GiB.

### 9.3 Zusammenstellung nach Realisierungsart

| Art | Betrag |
|---|---|
| Lokal, nach reiner Hash-Verifikation (A) | ≈ 2,6 GiB |
| Nur durch Auslagerung (B) | ≈ 5,0 GiB (+ 6,4 GiB je nach Primärkopie-Entscheidung) |
| Nur durch Umstellung (C) | Server ≈ 7,7 G (`mp3-split`); lokal ≈ 7,6 GiB |
| Regenerierbar | `.venv` 1,5 GiB |
| Nicht abschätzbar | Docker, Runner, Server-Logs, tatsächlicher freier Platz heute |

## 10. Priorisierte Maßnahmenmatrix

Keine Zeile ist eine Löschfreigabe. `REMOVE_CANDIDATE` ≠ Freigabe.

| # | Speicherort | Klasse | Umfang | Abhängigkeit | Rekonstruierbar | Redundanz | Schutzklasse | Empfehlung | Einsparung | Risiko | Fehlende Voraussetzung |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Server `media/mp3-split` | Audio-Derivat | 7,7 G (REPORTED) | Runtime-Beschleunigung | ja (Skript + Fulls) | lokal 7,64 GiB (Größe passt, Bytes ungeprüft) | betriebsrelevant | **REGENERABLE / REMOVE_CANDIDATE** (Cat. C) | 7,7 G | niedrig technisch, mittel betrieblich (Latenz) | Snippet-Latenzmessung, Server-Zugriff, Prüfung `/media/split`-Fremdnutzung (Logs), Rückfallplan |
| 2 | Lokal `mp3-split` | Audio-Derivat | 7,64 GiB | keine | ja | s. 1 | – | **REGENERABLE** nach #1 | 7,64 GiB | niedrig | Entscheidung nach #1 |
| 3 | Lokal Zenodo-ZIPs + `mp3-full` | Archiv/Original | je 6,4 GiB | Archiv | ZIP↔MP3 hash-identisch | gegenseitig | archivpflichtig | **CONSOLIDATE** (eine Primärkopie + externe Zweitkopie) | 6,4 GiB | mittel (wissenschaftlich) | Entscheidung Primärkopie; ZIPs ≙ Upload nur INFERRED |
| 4 | Lokal `tsv_for_index.bak_*` ×2 | Export | 0,71 GiB | keine | ja | hash-identisch | – | **REMOVE_CANDIDATE** (Cat. A) | 0,71 GiB | niedrig | Operator-OK |
| 5 | `quarantine/index.build` | Index | 0,27 GiB | keine | ja | = aktiver Index | – | **REMOVE_CANDIDATE** (A) | 0,27 GiB | niedrig | Bestätigung, dass `index` live gepublizt ist |
| 6 | `tmp/` | Zwischenstände | 1,65 GiB | keine | ja | `src-many` dup | – | **REMOVE_CANDIDATE** (A) | 1,65 GiB | niedrig | Inhaltsstichprobe `src-large`/`ci-runtime` |
| 7 | `quarantine` Rest | Index-Reste | 1,95 GiB | keine | ja/unklar | nicht verglichen | – | **INVESTIGATE → MOVE** | 1,95 GiB | niedrig/mittel | Inhaltsprüfung `prior_unused_snapshot` |
| 8 | `blacklab/backups` | Index-Backups | 0,54 GiB | Rückfall | ja (Rebuild) | keine | – | **MOVE** oder behalten | 0,54 GiB | niedrig | Entscheidung zum Rückfallziel |
| 9 | `_0_json/backups` | JSON-Stände | 2,32 GiB | Provenienz | teils | `pre-v3_1` ≙ Zenodo-JSON | archivpflichtig (Provenienz) | **MOVE** (komprimiert extern); Smoke-Tests (0,3 GiB) **REMOVE_CANDIDATE** | ≈ 2,3 GiB | niedrig/mittel | Entscheidung zur Version-4-Veröffentlichung |
| 10 | `data/exports/tsv` | Export | 0,16 GiB | unklar | unklar | keine | – | **INVESTIGATE** | 0,16 GiB | niedrig | Herkunft/Nutzer klären |
| 11 | Server `blacklab/export` | Export | 1,5 G | Rebuild | ja (Pipeline) | lokal `tsv_for_index` | – | **MOVE** | 1,5 G | mittel | Gleichheitsnachweis Server↔lokal; Rebuild-Probe |
| 12 | Server Postgres-Volume | DB | klein | **Runtime** | **nein** | keine | **produktionskritisch** | **KEEP + Backup einrichten** (Cat. D) | 0 | hoch | Dump-Verfahren, Restore-Test |
| 13 | Server/lokal `media/transcripts` | JSON | 0,7 GiB | Runtime, Provenienz | teilweise | pre-v3_1 ≙ Zenodo | **produktionskritisch/archivpflichtig** | **KEEP** (Cat. D) | 0 | hoch | Divergenz Server↔lokal klären |
| 14 | `mp3-full` Server | Audio-Original | 6,5 G | Runtime | nein | Zenodo-Kopie (Restricted, unprüfbar) + lokal | produktionskritisch | **KEEP** (D) | 0 | hoch | – |
| 15 | `data/blacklab/index` Server | Index | 279 MiB | Runtime | ja (Rebuild, nicht getestet) | lokal (Publish-Quelle) | produktionskritisch | **KEEP** | 0 | mittel | – |
| 16 | `.venv` | Umgebung | 1,47 GiB | Dev | ja | – | – | **REGENERABLE** | 1,47 GiB | niedrig | – |
| 17 | Server Runner `_work`/Docker | unklar | UNKNOWN | CI | ja | – | – | **INVESTIGATE** | UNKNOWN | mittel | Server-Zugriff |

Prioritäten nach Nutzen/Risiko: #1 → #3 → #9 → #7/#11; Quick wins #4–#6 (2,6 GiB lokal) sind klein, nur nebenbei sinnvoll.

## 11. Zielarchitektur für den eingefrorenen Betrieb (Vorschlag, kein Umbau)

1. **Online Runtime Minimum:** Web+DB-Container, BlackLab-Container + `index` (279 MiB), `media/mp3-full` (6,5 G), `media/transcripts` (0,7 G), `data/public`, `data/db/public/*.db`, `data/config`, Logs, `passwords.env`. `mp3-split`, `blacklab/export`, `blacklab/backups`, `quarantine` offline. Das ergibt etwa 8–9 G statt 20 G in `/srv/webapps/corapan` (zzgl. Runner/Docker).
2. **Deployment/Recovery Set (extern, versioniert):** Git-Tag des Webapp-Stands; `passwords.env` (Sicherheitsablage, nicht im Repo); Postgres-Dump (verschlüsselt); `mp3-full`, `transcripts` (Stand Produktion), `blacklab/index` oder `tsv_for_index` + Config; öffentliche Statistik/Metadaten; nginx/TLS-Konfiguration; kurze Recovery-Anleitung (`docker compose …`, `run_bls_prod.sh`, Medien-Sync). **Restore-Test auf einem leeren Host** ist Abnahmekriterium.
3. **Long-Term Research Archive (Zenodo, ohne Docker lesbar):** Full Corpus (aktualisiert auf den gewählten Annotationsstand), Metadata, Sample, Software (Tag **nach** den 19 neueren Commits oder bewusst auf v1.1.0 belassen), ein Archiv-README mit Dateilisten/Checksummen (SHA-256) für alle Pakete, Pipeline-Skripte (`maintenance_pipelines`) mit Versionen/Parametern der Audio-Aufbereitung (CBR, LUFS -18, Chunk 4 min/30 s).
4. **Regenerable/Disposable:** `mp3-split`, `mp3-temp`, `blacklab/export` (bei vorhandenem Transkript-Archiv), `quarantine`, `tmp`, `.venv`, `*.bak_*`-Duplikate.

Bei der späteren Stilllegung genügt das Research Archive (3) plus Recovery Set (2) auf kaltem Speicher; kein laufender Stack nötig.

## 12. Evidenzlücken und benötigte Entscheidungen

Lücken (UNKNOWN):
1. Aktueller Serverzustand (freier Platz, Docker-Images/Volumes, Cron/Backups, Logs, tatsächliche Datei-Identität Server↔lokal).
2. Postgres-Backup und Umfang der Auth-/Analytics-Daten.
3. Inhalt des Zenodo-Restricted-Records (Dateiliste/Checksummen) – bräuchte Eigentümer-Sicht (Zenodo-Login/Token des Operators) oder Zugriffsanfrage; **keine** Beschaffung durch mich.
4. Dekodier-Äquivalenz von Split- und Full-Snippets sowie Latenz des Fallbacks.
5. Externe Nutzung von `/media/split/*` (nur Zugriffslogs).
6. Herkunft von `data/exports/tsv`, Inhalt `prior_unused_snapshot`.
7. Ob die Produktion den Annotationsstand v3.2 (Juni 2026) bekommen soll oder bei Stand 2025/2026-03 bleibt.
8. nginx/TLS/Runner-Konfiguration und Wiederbeschaffbarkeit.

Entscheidungen des Operators:
- Primärkopie für `mp3-full` lokal: entpackt oder ZIPs.
- Soll `mp3-split` serverseitig entfallen (nach Messung)?
- Welcher Annotationsstand ist der wissenschaftliche Referenzstand; neue Zenodo-Version (Full Corpus v4, Software nach v1.1.0)?
- Ziel für Cold Storage (externer Speicher/Institution).
- Postgres-Backup-Verfahren und Aufbewahrung.

## 13. Vorschlag für einen kontrollierten späteren Bereinigungs-Run

Reihenfolge, jeweils nur nach ausdrücklicher Freigabe:
1. **Lesender Server-Audit** (SSH read-only, vom Operator freigegeben): `df`, `docker system df`, Volumen, Cron, Zugriffsstatistik `/media/split`, Latenz der Snippet-Erzeugung, Hash-Vergleich Server↔lokal für `mp3-full`/`transcripts`/`index` (Stichprobe + Manifest).
2. **Manifest + Cold-Storage-Kopie:** SHA-256-Manifest aller Archivbestände (Fulls, ZIPs, Transkripte, Backups, Index); Kopie auf externen Speicher; Lese-Verifikation per Hash.
3. **Postgres-Dump + Restore-Test** auf frischem Host (Compose lokal im Test; Daten nicht in Berichte übernehmen).
4. **Kategorie A lokal** (2,6 GiB): nur nach erneuter Hash-Verifikation direkt vor dem Löschen; Verschiebung in eine Quarantäne statt sofortigem Löschen.
5. **Kategorie B** (Auslagerung): nach verifizierter Kopie (Schritt 2).
6. **Kategorie C `mp3-split`:** zuerst Rückfall-Test in einer Kopie der Laufzeit: Verzeichnis umbenennen (nicht löschen), Smoke-Test von `/media/play_audio`, Latenz messen, nach Abnahmezeit erst entfernen. Rückfall: Verzeichnis zurückbenennen bzw. Re-Sync.
7. **Zenodo:** Full-Corpus-Version 4 (falls gewünscht) mit Checksummenliste; Software-Archiv mit neuem Release.

Abnahmekriterien: `/health` und `/ready` ok; Player lädt und spielt alle Länder; Snippet-Funktion für mindestens 1 Beispiel pro Land; Suche liefert Treffer; Login funktioniert; Hash-Manifest bestätigt Cold-Copy.

## 14. Git-Status

- `git status` zu Beginn: 35 Einträge (vorbestehend, nicht von mir).
- Am Ende: neu hinzugekommen ist nur diese Berichtsdatei `docs/agent-runs/2026-10-19_legacy_storage_runtime_archive_audit.md` (neues Verzeichnis `docs/agent-runs/` – im Root-`docs/` existierte es bisher nicht; es existiert nur unter `maintenance_pipelines/_0_json/docs/agent-runs/`. Der Ort folgt der Aufgabenvorgabe.).
- **Kein Commit, kein Push, kein Reset, keine sonstige Git-Mutation.** Keine Dateien gelöscht, verschoben oder verändert; keine Container, Tests oder Projektskripte ausgeführt.
