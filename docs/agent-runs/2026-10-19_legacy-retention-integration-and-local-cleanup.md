# Legacy-CO.RA.PAN – Retention-Integration, lokale Speicherbereinigung und Abschluss

Datum: 2026-10-19 · Repo-HEAD: `713629bd3b85cf6739db4cb689314879074493bc` (Branch `main`) · Vorgänger: `2026-10-19_legacy_storage_runtime_archive_audit.md`, `2026-10-19_zenodo_archive_update_and_old_zip_cleanup.md`

## 0. Ergebnis

| Teil | Status |
|---|---|
| Retention-Primary auf NEW_FS | **BLOCKED** – erfordert eine Änderung von `crosscorpus-storage/v1` in beiden Repositories (§2); nichts auf NEW_FS angelegt |
| D:-Sekundärkopie | **PARTIAL** – bestehende verifizierte Kopie (2026-10-15) heute für den gesamten Retentionsbestand erneut per SHA-256 bestätigt (1.402/1.402); ein Abgleich gegen einen Primary ist mangels Primary nicht möglich |
| Lokaler Cleanup | **PASS** für alle nicht vom Primary abhängigen Klassen: 18,50 GiB entfernt (Repo + Staging) |
| Entfernung lokaler Original-MP3 | **BLOCKED** (Gate: NEW_FS-Primary) – `media/mp3-full` bleibt |
| Zenodo-Restarbeiten | **PASS** – Staging geprüft und entfernt, alte offene Bearbeitung von 17828582 verworfen, Token-Datei gelöscht |
| Git | unverändert bis auf neue untracked Dokumentation (§10); kein Commit, kein Push |

Kein Zugriff auf den Produktivserver, kein Deployment, keine Änderung an CO.RA.PAN_v3 oder CO.PRE.PAN_v3 (nur lesend), keine neue Korpusverarbeitung.

## 1. Ausgangszustand

- Legacy-Repo: HEAD `713629b`, Git-Status 36 Einträge (die 35 vorbestehenden + `docs/agent-runs/`). Kein Prozess mit Arbeitsverzeichnis oder Kommandozeile in `legacy\corapan` (Prüfung per Prozessliste; die laufenden Python-Prozesse gehören zu CO.RA.PAN_v3: Reservoir-Controller, Working-Copy-Planung, pytest).
- Größen vor dem Run: `legacy\corapan` **25,224 GiB** (45.015 Dateien; der Audit-Wert 31,6 GiB lag vor dem Löschen der alten ZIPs), Zenodo-Staging **6,514 GiB**; C: frei 149,91 GiB, D: frei 3.015 GiB.
- CO.RA.PAN_v3: Storage-Run „C: release activation“ abgeschlossen und als Docs-Commit gemeldet; lokales `main` 61 Commits vor `origin/main` (Push ausstehend, laufende Controller-Wellen). Kein laufender Cutover, keine aktive Migration der Legacy-Bestände.

## 2. Geltende Speicherstruktur und die Retention-Entscheidung

Gelesen (nur lesend) im CO.RA.PAN-Repository: `config/storage_targets.yml`, `docs/architecture/STORAGE_AND_RETENTION_POLICY.md` (§13g), `docs/architecture/STORAGE_REDUNDANCY_INVENTORY.md` (§3, §4), `docs/plans/2026-10-19_newfs-legacy-evidence-archive-proposal.md`, `docs/agent-runs/2026-10-19_c-storage-release-activation-and-worktree-closure.md` (§10).

- NEW_FS (`CORAPAN_PRESERVATION_ROOT`, HRZ-Gruppenshare) kennt nur die Rollen PRODUCTION und HISTORIC. `STORAGE_AND_RETENTION_POLICY.md` §13g: „`projects/panhispanic_media_corpora/legacy/<corpus>` … `legacy` is neither a role nor a holding and §5.2 of `crosscorpus-storage/v1` knows two namespace forms only: it needs a contract amendment adopted in both repositories. Proposed, not activated, nothing created on NEW_FS.“
- `storage_targets.yml`, Budgetklasse `legacy` (Präfix `legacy`): `release_requires: verified secondary copy, institutional archive copy (needs a contract amendment), recorded decision`.
- `STORAGE_REDUNDANCY_INVENTORY.md` §4: Bis zur Entscheidung bleibt jedes Original auf C:.
- D:-Sekundärkopien lokaler Einzelkopie-Bestände liegen unter `D:\projects\panhispanic_media_corpora\corapan\archive\protected_secondary\<set>\` (schreibgeschütztes Werkzeug `archive_secondary_copy_v1.py`, write-once-Journal). Sie sind keine Vertragsrolle und allein kein Freigabegrund für Originale.

**Entscheidung dieses Runs:** Eine Legacy-Retention auf NEW_FS ist in der geltenden Architektur nicht als eigenständiger Bestand möglich, ohne `crosscorpus-storage/v1` zu ändern. Das darf ich nicht einseitig tun; ein provisorischer Root wäre eine Umgehung. Der Primary-Teil ist **BLOCKED**, ebenso alles, was von ihm abhängt (Löschung der Original-MP3, Auslagerung der historischen JSON-Stände und historischen Index-Builds). Die D:-Sekundärkopie wurde nicht beschrieben (write-once-Set eines anderen Werkzeugs; nichts fehlte, §4).

**Benötigte Entscheidung (gemeinsam für beide Repositories):** Annahme des Vorschlags `2026-10-19_newfs-legacy-evidence-archive-proposal.md` (ARCHIVE-Holding `LEGACY` unter `projects/panhispanic_media_corpora/legacy/<corpus>/<source-root-name>/`, write-once, `ARCHIVE_MANIFEST.json`, T1-Identitätsmarker, D: als Sekundärkopie), d. h. Ergänzung von `crosscorpus-storage/v1` §5.2 um eine Archiv-Namensform, mit neuem Bundle-Digest in beiden Repositories. Danach ist der Primary für den Bestand aus §3 ein einzelner Kopier-/Verifikationslauf; das Manifest `docs/agent-runs/2026-10-19_legacy_retention_manifest.csv` ist die Eingabe.

## 3. Retentionsinventar (archivwürdig; lokal erhalten)

Manifest mit SHA-256 je Datei und D:-Abgleich: `docs/agent-runs/2026-10-19_legacy_retention_manifest.csv` (1.402 Dateien, 10.558.627.595 Bytes = 9,83 GiB).

| Klasse | Bestand | Dateien | Einordnung |
|---|---|---:|---|
| 1 irreproduzierbare Primärdaten | `media/mp3-full` (146 MP3; = Zenodo v3/v4-Audio, SHA-256) | 147 | Original-Audio |
| 1 Annotationsergebnis aktuell | `media/transcripts` (146 JSON v3.2 = Zenodo v4) + `edit_log.jsonl` + `.bak_tense` | 149 | inkl. Editor-Log (38 Einträge 2025-10) |
| 2 historische wissenschaftliche Version | `backups/pre-v3_1-transcripts` (= Zenodo v3 JSON) | 153 | |
| 2 Zwischenstand | `backups/pre-tense-schema-migration` (v3.1 vor Tense-Migration; nirgends sonst) | 152 | nur lokal + D: |
| 2 Bearbeitungsnachweis | `backups/manual-repairs` (Timestamp-Reparatur) | 2 | |
| 3 Rekonstruktion/Restore | `data/blacklab/index` (= produktiv publizierter Index, laut Proof-Run), `export/tsv/tsv_for_index`, `export/metadata` | 366 | |
| 3 Metadaten/Statistik | `data/db/public` (2 SQLite), `data/public` (Metadaten, Statistik) | 433 | |
| 2/3 Provenienz | v3.2-Provenienz (Zenodo v4) + lokale Quellen (uncommittet, §10) + Run-Berichte `maintenance_pipelines/_0_json/docs/agent-runs` | – | Git-Arbeitsstand bzw. Zenodo |

Zusätzlich lokal erhalten, aber nicht im Manifest (historisch/unklar; Ziel: späteres Archiv oder Entscheidung): `data/blacklab/quarantine/webapp_legacy_blacklab_invalid_20260320` (1,95 GiB: `prior_unused_snapshot` mit Index-Ständen „backup“/„bad“ vom Jan. 2026, `blacklab_wrong_root`, Altbackup), `data/blacklab/backups` (0,52 GiB, zwei eigenständige Builds vom 2026-03-20/21, ein leerer Ordner), `data/exports/tsv` (0,15 GiB, älteres Exportschema vom Nov. 2025, in `deploy_data.ps1` genannt), 36 einzigartige Smoke-/Multicountry-Zwischenstände (Token-ID-Snapshots, Test-Zwischenstände), `data/db/restricted/postgres_dev*` (Dev-Datenbank).

## 4. NEW_FS-Primary und D:-Sekundärkopie

**NEW_FS:** nicht angelegt (BLOCKED, §2). Kein Objekt, kein Byte.

**D: `…\corapan\archive\protected_secondary\legacy_corapan`** (Receipt `SECONDARY_COPY_VERIFIED` 2026-10-15: 45.030 Objekte, 33.947.564.625 Bytes, uncached re-read, Restore-Test 25/25):

| Prüfung heute | Ergebnis |
|---|---|
| Retentionsbestand (§3), SHA-256 lokal vs. D: | 1.402/1.402 identisch, 0 fehlend, 0 abweichend |
| `media/mp3-split` (vor dem Löschen) | 2.705/2.705 identisch |
| Alte Full-Corpus-ZIPs (vorheriger Run) | 25/25 identisch |
| Zusätzliche ältere Objekte auf D: | ja – D: bewahrt den Stand vom 2026-10-15 (inkl. alter ZIPs, Splits, `tmp`, `.venv`, Backups); nichts gelöscht |
| Nicht auf D: | die Berichte und das Release-Record vom 2026-10-19 (klein; Zenodo bzw. Git-Arbeitsstand) |

Status D:: **PARTIAL** – Fixity des Retentionsbestands bestätigt; kein Abgleich gegen einen Primary möglich; keine Off-Site-Eigenschaft (gleicher Rechner). Ein vollständiger Restore wurde **nicht** durchgeführt; Nachweis = SHA-256-Readback aller Retentionsdateien von beiden Orten.

## 5. Wissenschaftliche Versionen – wo sie vollständig erhalten sind

| Stand | Lokal (C:) | D: | Zenodo |
|---|---|---|---|
| Audio (146 MP3) | `media/mp3-full` | ja | v3 + v4 (restricted) |
| Annotation v3 (Feb. 2026) | `pre-v3_1-transcripts` | ja | v3 (10.5281/zenodo.18782190) |
| Zwischenstand v3.1 (vor Tense-Migration) | `pre-tense-schema-migration` | ja | – |
| Annotation v3.2 | `media/transcripts` | ja | v4 (10.5281/zenodo.23470771) |
| v3.2-Provenienz | Quellen im Git-Arbeitsstand; Paket im Release-Record | Quellen ja (Stand 2026-10-15) | v4 Supplement |
| Software | Git | – | 10.5281/zenodo.23470763 |

## 6. Entfernte lokale Dateien (nach Klassen)

Alle Gates vor dem Löschen im Plan-Lauf (SHA-256, frisch) geprüft; Journal: `maintenance_pipelines/_1_zenodo-repos/releases/2026-10-19_…/local_reports/cleanup_journal.jsonl`, Plan: `…/cleanup_plan.json`.

| Klasse | Dateien | Bytes | Gate / Nachweis |
|---|---:|---:|---|
| Zenodo-Staging (`legacy\corapan_zenodo_staging`, komplett) | 75 | 6.994.155.930 | veröffentlichte Dateien (31 + 4) MD5/Größe = lokal; Quellen (146 MP3 + 146 JSON) SHA-256 = `MANIFEST.csv`; 42 kompakte Dateien vorher ins Release-Record kopiert und per SHA-256 geprüft |
| `media/mp3-split` | 2.705 (+ 25 leere Ordner) | 8.200.720.408 | 2.705/2.705 SHA-256 = D:; Fulls lokal + D: identisch; Produktionsserver unberührt (Splits dort bleiben); Rekonstruktion: `maintenance_pipelines/_0_mp3/mp3_prepare_and_split.py` (4 min/30 s, Fenster wie `SPLIT_TIMES` in `app/src/app/services/audio_snippets.py`); lokal fällt die Snippet-Erzeugung auf `mp3-full` zurück |
| `tsv_for_index.bak_20260117_002730` / `_005855` | 2 × 146 | 2 × 381.955.540 | 146/146 SHA-256 = `tsv_for_index` |
| `data/blacklab/quarantine/index.build` | 74 | 292.150.609 | 74/74 SHA-256 = `data/blacklab/index`; wird für ein Publish wieder durch Kopie des Index erzeugt (`publish_blacklab_index.ps1` erwartet diesen Pfad) |
| `tmp/` (komplett) | 114 | 1.776.222.857 | 108 Kopien behaltener Dateien, 6 synthetische Sync-Testdateien (1 GiB Zufallsdaten, SSH-Testconfigs, leere Dateien) |
| Smoke-/Multicountry-Backups, nur byte-identische Kopien | 55 | 264.876.217 | SHA-256 = behaltene Retentionsdatei; 36 einzigartige behalten |
| `.venv` | 34.043 | 1.573.907.641 | kein Prozess lief aus der venv; Paketliste gesichert: `docs/agent-runs/2026-10-19_legacy_venv_package_list.txt`; neu aufbaubar aus `app/requirements*.txt` bzw. `maintenance_pipelines/requirements-lokal.txt` (der erste Löschversuch traf eine kurzzeitige Sperre auf `Scripts\python.exe`, der Rest wurde beim zweiten Versuch entfernt) |
| **Summe** | **37.358** | **19.865.944.742** (≈ **18,50 GiB**) | |

Umbenannt (nicht gelöscht): `maintenance_pipelines/_1_zenodo-repos/zip_process.log` → `zip_process.history_v3_2026-02-26.log`. Damit ist das historische Log vom Resume-State getrennt; `zenodo_full-corpus.py` findet keinen Zustand mehr und würde bei einem neuen Lauf alle Pakete neu bauen statt sie stillschweigend zu überspringen. `metadata_process.log` beschreibt noch vorhandene Dateien und blieb.

## 7. Speicherbilanz

| Bereich | Vorher | Nachher | Ergebnis |
|---|---:|---:|---|
| Lokales Legacy-Repository `legacy\corapan` | 25,224 GiB | 13,238 GiB | 11,99 GiB freigegeben |
| Separates Zenodo-Staging | 6,514 GiB | 0 | 6,51 GiB freigegeben (42 kompakte Dateien, ≈ 1,6 MiB, ins Release-Record übernommen) |
| NEW_FS Legacy | 0 | 0 | BLOCKED, nichts angelegt |
| D: Legacy-Backup | 31,6 GiB (Stand 2026-10-15) | unverändert | Retentionsbestand heute verifiziert, nichts neu benötigt |

- Freigegeben auf C: durch diesen Run: **18,50 GiB** (Summe der entfernten Bytes). Freier Platz C: 149,91 → 164,27 GiB (+14,36 GiB; die Differenz ist parallele Belegung durch CO.RA.PAN_v3-Prozesse).
- Neu benötigt auf NEW_FS: 0. Neu benötigt auf D:: 0.
- Gegenüber dem Audit-Stand (31,6 GiB Repo, vor Löschung der alten ZIPs) ist das Repo um 18,4 GiB kleiner.

## 8. Verbleibende große lokale Bestände (13,24 GiB)

| Bestand | GiB | Grund |
|---|---:|---|
| `media/mp3-full` | 6,45 | Original-Audio; Löschung erst nach NEW_FS-Primary (BLOCKED) |
| `data/blacklab/quarantine` (Rest) + `backups` | 2,47 | historische Index-Builds; Archivziel BLOCKED |
| `maintenance_pipelines/_0_json/backups` | 2,10 | historische Annotationsstände (v3, v3.1-Zwischenstand), einzigartige Smoke-Zwischenstände |
| `media/transcripts` | 0,71 | aktuelle Annotation (Entwicklungsdaten der Webapp) |
| `data/blacklab/export` (TSV + Metadaten), `data/exports/tsv` | 0,53 | Rekonstruktionsgrundlage des Index; älterer Export unklar |
| `.git` | 0,19 | Historie |
| Rest (App, Doku, Metadaten, Dev-DB) | ≈ 0,8 | Software und kleine Artefakte |

Nach dem Inkrafttreten der Archiv-Holding wären weitere ≈ 11 GiB (Original-MP3, historische Index-Builds, JSON-Backups) auslagerbar; das Repo läge dann bei ≈ 2 GiB.

## 9. Zenodo und Token

- Staging: vor dem Entfernen wurden die veröffentlichten Dateien (Full Corpus v4: 31, Software: 4) per API mit Größe und MD5 gegen die lokalen Dateien geprüft – identisch. Upload-Manifeste, Prüfsummen, Release Notes, Metadaten, Verifikationsberichte und Skripte liegen jetzt in `maintenance_pipelines/_1_zenodo-repos/releases/2026-10-19_fullcorpus-v4_software-archive-2026-06-14-713629b/` (README dort).
- Alte offene Bearbeitung: Deposition 17828582 war `submitted=true`, `state=inprogress` (offene Bearbeitungssitzung seit 2026-02-23). Verworfen mit `POST /api/deposit/depositions/17828582/actions/discard` (HTTP 204) → `state=done`. Nachgewiesen unverändert: DOI, 25 Dateien (Namen, Größen, Prüfsummen), veröffentlichte Metadaten (anonyme Sicht), Revision 12 vorher/nachher.
- Veröffentlichte Records Full Corpus v4 und Software: nicht verändert.
- Token: `%LOCALAPPDATA%\corapan_zenodo\token.dpapi` gelöscht, der Ordner ebenfalls; keine Umgebungsvariable gesetzt; kein Tokenwert in Logs, Berichten oder Release-Record (Musterprüfung). **Der Operator muss das Token zusätzlich im Zenodo-Konto widerrufen** – das lokale Löschen widerruft es nicht.

## 10. Git-Arbeitsstand

Unverändert gegenüber Run-Beginn bis auf neue untracked Dateien: `docs/agent-runs/` (Berichte dieses Tages, Retention-Manifest, Paketliste, Alt-ZIP-Inventar) und `maintenance_pipelines/_1_zenodo-repos/releases/` (Release-Record). Kein Reset, kein Clean, kein Commit, kein Push.

Klassifikation der vorbestehenden Änderungen (alle erhalten):

| Zustand | Klasse | Empfehlung |
|---|---|---|
| `M _0_json/02_annotate_transcripts_v3.py`, `03_build_metadata_stats.py`, `tests/test_annotate_transcripts_v3_1.py`, `?? _0_json/tools/` | Wartungs-/Quellcode **und** wissenschaftliche Provenienz (v3.2; auch im Zenodo-v4-Supplement) | committen (bewusst, ohne Push auf `main`, da Push einen Produktiv-Rebuild auslöst) |
| `M _0_json/state/annotation/annotation_state.sqlite` | generierter Zustand des Annotationslaufs | nicht committen; ggf. aus Git entfernen (Entscheidung) |
| `D _0_json/run_full_transcripts_annotation.ps1`, `D start_full_annotation.txt` (2×) | in `docs/agent-runs/archive_commands/` verschoben (Cleanup vom 2026-06-14) | Verschiebung committen |
| `D _0_json/docs/agent-runs/…` (6 alte v3.1-Smoke-Audits) | im Cleanup vom 2026-06-14 entfernt (überholte Smoke-Berichte; noch in Git-Historie) | Löschung committen oder wiederherstellen |
| `?? _0_json/docs/agent-runs/…` (v3.2-Berichte, Audits) | Provenienz | committen |
| `?? _0_json/backups/pre-tense-schema-migration/` | historischer Zwischenstand (1 GiB JSON) | nicht committen; in das künftige Archiv |

## 11. Wartbarkeit

Software, Konfiguration, Doku, Skripte und Git-Historie sind vollständig. `media/mp3-full`, `media/transcripts`, Index, Metadaten und SQLite-DBs bleiben – die lokale Entwicklungs-Webapp ist damit weiter vollständig startbar; Audiosnippets fallen ohne Splits auf die Full-MP3 zurück (langsamer). Neu nötig vor lokaler Arbeit: Python-Umgebung neu aufbauen (`scripts/dev-setup.ps1` bzw. `uv pip sync app/requirements-dev.txt`; für die Annotationspipeline zusätzlich `maintenance_pipelines/requirements-lokal.txt` und das Modell `es_dep_news_trf` 3.8.0, Versionen siehe Paketliste). Vor einem BlackLab-Publish `data/blacklab/index` nach `data/blacklab/quarantine/index.build` kopieren. Tests wurden in diesem Run nicht ausgeführt.

## 12. Blockaden, offene Entscheidungen, Risiken

1. **Vertragsänderung `crosscorpus-storage/v1`** (beide Repositories) für eine LEGACY-Archiv-Holding auf NEW_FS – Voraussetzung für Primary, Löschung der Original-MP3 und Auslagerung der historischen Stände.
2. Bis dahin liegen Retentionsbestände nur auf C: und D: desselben Rechners (kein institutioneller, kein Off-Site-Nachweis); Zenodo deckt Audio und die Annotationsversionen v3/v4 ab, nicht den v3.1-Zwischenstand und nicht die historischen Index-Builds.
3. `STORAGE_REDUNDANCY_INVENTORY.md` im CO.RA.PAN-Repository führt `legacy corapan` noch mit 31,6 GiB; die Aktualisierung gehört dem dortigen Owner (hier nicht geändert).
4. Token-Widerruf im Zenodo-Konto (Operator).
5. Commit-Entscheidungen zu §10 (ohne Push auf `main`).

## 13. Bestätigung

Kein Server-Zugriff, kein Deployment, kein Commit, kein Push. CO.RA.PAN_v3 und CO.PRE.PAN_v3 nur gelesen. Keine Original-MP3, keine wissenschaftlich eigenständigen Annotationsstände und keine D:-Bestände gelöscht. Veröffentlichte Zenodo-Records unverändert; nur die offene Bearbeitungssitzung von 17828582 verworfen.


---

## 14. Fortsetzung 2026-10-19 (ab 15:38): Vertrags-Gate, NEW_FS-Retention, B1-Backup und abschließende Bereinigung

Die BLOCKED-Befunde der Abschnitte 0–13 galten für den Stand vor der Vertragsänderung. Sie bleiben unverändert stehen; ihre Auflösung ist hier dokumentiert.

### 14.1 Ergebnis

| Teil | Status |
|---|---|
| Vertrag | **READY** – `crosscorpus-storage/v1` Revision 2 (LEGACY) in beiden Repositories in Kraft |
| NEW_FS-Primary (LEGACY) | **PASS** – Baum `corapan` PRESERVED (A5), 3.082 Dateien / 13.494.502.346 Bytes |
| D:-Backup (B1) | **PASS** – vom Primary erzeugt, voll verifiziert, A5 auf der Kopie ohne Codes, Read-back 41/41, Beleg `complete` |
| Lokaler Cleanup | **PARTIAL** – 5,09 GiB freigegeben; `media/mp3-full` (6,45 GiB) nicht freigegeben (A7: Leser in CO.RA.PAN_v3 noch nicht umgestellt) |
| Git | **PASS** für den autorisierten Scope – 3 lokale Commits auf `legacy/v3.2-provenance-and-retention`; kein Push |

### 14.2 Beobachtung und Nachweis des Vertrags-Gates

- Beobachtet wurden ausschließlich die Haupt-Checkouts `C:\dev\panhispanic_media_corpora\corapan` und `…\coprepan`, nur lesend: Pin, Vertragstext, später auch die Worktrees `worktrees\{corapan,coprepan}\legacy-archive-contract`. Abstand 90 s, insgesamt 44 Prüfungen von 15:39 bis 16:45 (`local_reports/gate_probe.log` im Release-Record).
- Signal um 16:45: beide `main` pinnen `crosscorpus-storage/v1` = **`49a3ca88c084eee26e40caa1dd987155bf8062c99c81d8cb734a7990a8afb036`** (vorher `8d17fc21…`), Status IN_FORCE.
- Die vollständige Prüfung der acht Start-Gates:
  1. Normativ übernommen: D127 (CO.RA.PAN, `docs/decisions/2026-10-19_D127_…`) und CPD-0031 (CO.PRE.PAN).
  2. Digests gleich in beiden Pin-Dateien. Laut Adoptionsbericht sind die Bundles byte-identisch (`compare-sibling` exit 0, `compare-sister` OK aus den Haupt-Checkouts).
  3. Konformität: CO.RA.PAN 144 + 364 passed, CO.PRE.PAN 299 bzw. 209 passed nach Fix (Adoptionsbericht §6; in diesem Run nicht neu ausgeführt).
  4. Integriert: Merge-Commits `003ec84d5`/`a046db310`/`03d70ed35` (CO.RA.PAN `main`), `7fcd6d7`/`17fac47` (CO.PRE.PAN `main`).
  5. Abschlussbericht `docs/agent-runs/2026-10-19_crosscorpus-legacy-archive-contract-adoption.md`: `LEGACY_ARCHIVE_CONTRACT_READY = true`.
  6. NEW_FS-Root `\\dfs.hrz.uni-marburg.de\PROJEKTE\FB10\TACKE_FORSCHUNGSDATEN` erreichbar, Namensraum `legacy` vorher nicht vorhanden. Anlage durch den Archivierungslauf ist laut §19.10 vorgesehen.
  7. Der Backup-Pfad `D:\projects\panhispanic_media_corpora\legacy\corapan\preservation_backup` und die B1-Regel sind in D127/§19.10 festgelegt.
  8. Keine konkurrierende Migration (Adoptionsbericht; Namensraum leer).
- Nicht verwendet wurde `K:` (`\\dfs…\FREMDSPRACHEN\gruppen`, der frühere Gruppen-Share). Dort wurde nur gelesen, um den Share zu identifizieren, und nichts geschrieben. Das Archivskript bricht ab, wenn ein Zielpfad nicht unter `TACKE_FORSCHUNGSDATEN\projects\panhispanic_media_corpora\legacy\corapan` liegt oder `FREMDSPRACHEN`/`K:` enthält.

### 14.3 NEW_FS-Zielstruktur und Primary

```
\\dfs.hrz.uni-marburg.de\PROJEKTE\FB10\TACKE_FORSCHUNGSDATEN\projects\panhispanic_media_corpora\legacy\corapan\
├── corapan_preservation_target.json   T1: target_id corapan-archive-newfs-legacy, holding LEGACY (written with write_marker of CO.RA.PAN)
└── corapan\                           archived tree (A2), mirrors the repository layout
    ├── ARCHIVE_MANIFEST.json           written last (A3), tree_sha256 f70bcbb38899be150c30195cb5c14b14243a925f35ec98b885369fca1980ae5f
    ├── media\{mp3-full,transcripts}\
    ├── data\{blacklab,exports,public,db\public}\
    ├── maintenance_pipelines\…\
    └── docs\agent-runs\…
```

- Inventar: Retentionsmanifest (1.402 Dateien) + Zusatzinventar `docs/agent-runs/2026-10-19_legacy_retention_supplement_manifest.csv` (1.681 Dateien: historische Index-Builds 1.264, historische Exporte 153, Annotations-Zwischenstände 36, Verarbeitungsevidenz 116, Release-Records 112). Ausgenommen ist nur dieser Bericht, weil er noch geschrieben wurde; er liegt in Git.
- Kopie: write-once (exklusives Anlegen `.corapan-part` → rename, kein Überschreiben). Quelle unmittelbar vor der Kopie neu gehasht. Ergebnis: COPIED 3.082, SOURCE_CHANGED 0, CONFLICT 0, FAILED 0.
- Siegel: alle Dateien vom Primary zurückgelesen und gegen die Liste geprüft, danach `ARCHIVE_MANIFEST.json` geschrieben (`schema crosscorpus-storage/v1/archive-manifest`, `decision` = D127 + Operator-Brief, `supersedes: null`).
- A5-Abnahme mit `crosscorpus/storage_contract.archive_tree` (CO.RA.PAN-Implementierung, reine Funktion) auf einem zweiten vollständigen Rücklesen: **keine Codes → PRESERVED** (16:13 UTC), Identität `IDENTITY_OK`.
- Nicht archiviert: Git-versionierter Quellcode (Git, Zenodo-Software), die Dev-PostgreSQL-Daten `data/db/restricted/*` (mögliche Kontodaten; bleiben lokal), `.git`.
- Zugriffsschutz: LEGACY ist kein DISTRIBUTION-/EXCHANGE-Root (A8). Der Ordner liegt im projektinternen Bereich des Forschungsdaten-Shares neben PRODUCTION und HISTORIC; die Zugriffsrechte setzt die Institution (§14). Die NTFS-ACLs wurden nicht im Einzelnen geprüft.

### 14.4 D:-Backup (B1)

- Werkzeug: `scripts/preservation_backup_v1.py --holding LEGACY` von CO.RA.PAN. Ausgeführt mit den Root-Variablen nur im Prozess (keine Änderung an `.env` oder Repository von CO.RA.PAN, Python `-B`).
- `init-root` → `BACKUP_ROOT.json` (role BACKUP, holding LEGACY, anderes Volume als der Primary). `copy` (Lauf `bk20261019T181429`): 3.083 Objekte, 13.495.166.468 Bytes, 0 Probleme. `verify`: jedes Objekt der Kopie neu gelesen, gegen den beim Kopieren journalisierten Digest des Primary, `all_ok`. `receipt` (B5): `produced_from_primary`, `complete: true` (not_in_copy 0, changed 0, only_in_copy 0).
- Zusätzlich A5 auf der **Kopie**: `archive_tree` gegen das kopierte Manifest – keine Codes (3.082/3.082). Read-back: 41 Proben über 14 Datenklassen (Original-Audio, Annotation v3.2, v3, v3.1-Zwischenstand, Reparaturen, aktiver Index, historische Builds, Index-Backups, TSV-Export, alte Exporte, öffentliche Daten, Evidenz, Release-Records, Smoke-Stände) aus dem Backup in ein leeres Scratch-Verzeichnis kopiert und gehasht – 41/41 identisch, danach entfernt.
- Bewertung getrennt:
  - Fixity vollständig (Primary zweimal, Kopie zweimal).
  - Read-back nur exemplarisch.
  - Ein Teil der Kopie-Verifikation lief unmittelbar nach der Kopie und wurde wahrscheinlich aus dem Windows-Dateicache bedient. Eine ungecachte Wiederholung steht aus.
  - Ein vollständiger Restore wurde nicht durchgeführt.
  - Das Backup liegt auf demselben Arbeitsplatzrechner; Off-Site-Eigenschaft wird nicht behauptet.
- Der alte Bestand `D:\…\corapan\archive\protected_secondary\legacy_corapan` (2026-10-15, aus den lokalen Originalen) bleibt unverändert; er ist laut D127 nicht das B1-Backup.
- Werkzeugbefund für den Owner von CO.RA.PAN (nicht geändert): `init-root` mit `--holding LEGACY` schreibt in `BACKUP_ROOT.json` den Freitext „HISTORIC holding's primary“ und nennt im Hinweis `CORAPAN_HISTORIC_BACKUP_ROOT`; das Feld `holding` ist korrekt `LEGACY`. `restore-test` kennt keine LEGACY-Bäume (0 Fälle → `all_ok false`), deshalb das eigene Read-back.

### 14.5 Erhaltene wissenschaftliche Versionen (jetzt mit institutioneller Kopie)

| Stand | NEW_FS (Primary) | D: (B1) | Zenodo | lokal |
|---|---|---|---|---|
| Audio, 146 MP3 | ja | ja | v3, v4 | ja (nicht freigegeben) |
| Annotation v3.2 + Editor-Log | ja | ja | v4 | ja |
| Annotation v3 | ja | ja | v3 | nein |
| v3.1-Zwischenstand (nur hier) | ja | ja | – | nein |
| Reparatur- und Smoke-Zwischenstände | ja | ja | – | nein |
| Historische Index-Builds, Index-Backups, alte Exporte | ja | ja | – | nein |
| Verarbeitungsevidenz, Release-Records | ja | ja | v4-Supplement (teilweise) | ja (Git/klein) |

### 14.6 Entfernte lokale Dateien (Phase B)

Gate je Datei: frischer SHA-256 = Eintrag im PRESERVED-Manifest; nicht Git-versioniert; Klasse freigegeben. Journal: `local_reports/phaseb_cleanup_journal.jsonl`.

| Klasse | Dateien | Bytes |
|---|---:|---:|
| `data/blacklab/quarantine/` (historische Builds, Build-Log) | 1.116 | 2.095.488.098 |
| `data/blacklab/backups/` | 148 | 584.301.218 |
| `data/blacklab/export/tsv/tsv_for_index/` (generierte Kopie von `export/tsv`) | 146 | 381.955.540 |
| `data/exports/` (altes Exportformat) | 147 | 169.588.924 |
| `data/blacklab/export/tsv_json_test/` | 5 | 9.693.814 |
| `maintenance_pipelines/_0_json/backups/` (v3, v3.1-Zwischenstand, Reparaturen, Smoke) | 338 | 2.221.314.245 |
| **Summe** | **1.900** | **5.462.341.839 (5,09 GiB)** |

Erhalten: 5 Git-versionierte Dateien in `backups/pre-v3_1-transcripts` (README, Rekonstruktionsbericht, `.gitkeep`, Editor-Log, `.bak_tense`). 0 Dateien wegen Hash-Abweichung oder fehlendem Manifesteintrag behalten. 123 leere Ordner entfernt.

### 14.7 Nicht freigegeben – verbleibende Bestände

| Bestand | GiB | Grund |
|---|---:|---|
| `media/mp3-full` | 6,45 | A7 „readers moved“ nicht erfüllt: CO.RA.PAN_v3 liest `${CORAPAN_LEGACY_ROOT}/media/mp3-full` (`config/corpus_paths.yml`; `pipeline/recording.py: from_legacy_document`, Datenklasse `legacy_gold`; `legacy_profile.py`, `auditset.py`, Speech-Mode-Features). Die Umstellung der Variable auf den Archivbaum ist eine Konfigurationsänderung in CO.RA.PAN_v3 und nicht autorisiert. Primary, B1 und Read-back sind erfüllt; nach der Umstellung ist die Löschung ein einzelner, gated Schritt. |
| `media/transcripts` | 0,71 | ebenso (`legacy_corapan_source_json`); zudem benötigt von der lokalen Webapp und von `03_build_metadata_stats.py` (findet das Projekt-Root über `media/transcripts`) |
| `data/blacklab/index`, `export/tsv`, `export/metadata`, `data/public`, `data/db/public` | 0,64 | lokale Webapp (Suche, Atlas, Statistik), Index-Rebuild |
| `data/db/restricted/postgres_dev*` | 0,09 | Dev-Datenbank; bewusst nicht auf das Share übertragen |
| `.git`, `app`, `docs`, Pipelines, Release-Record | ≈ 0,26 | Software, Doku, Evidenz |

Ohne die nicht freigegebenen Original-MP3 läge das Repo bei ≈ 1,7 GiB (Ziel ≈ 2 GiB).

### 14.8 Speicherbilanz (Fortsetzung)

| Bereich | Vorher (14:xx) | Nachher | Ergebnis |
|---|---:|---:|---|
| Lokales Legacy-Repository | 13,238 GiB | 8,152 GiB | 5,09 GiB freigegeben |
| Separates Zenodo-Staging | 0 | 0 | (bereits im ersten Teil entfernt) |
| NEW_FS Legacy | 0 | 12,57 GiB | gesichert, PRESERVED |
| D: Legacy-Backup (B1) | 0 | 12,57 GiB | verifiziert |

- Neu belegt auf NEW_FS: 13.495.166.468 Bytes (Baum + Manifest + Marker). Neu belegt auf D:: 13.495.166.468 Bytes + Journal/Beleg. Der alte D:-Bestand vom 2026-10-15 (31,6 GiB) bleibt zusätzlich bis zu seiner eigenen Freigabe.
- Gesamt über den Tag (beide Teile dieses Runs): 18,50 + 5,09 = **23,59 GiB** auf C: freigegeben. Der freie Platz auf C: zeigt das wegen paralleler Belegung durch CO.RA.PAN_v3 nicht 1:1 (149,9 → 150,3 GiB zwischen 14:xx und 18:27).

### 14.9 Leser und Anleitungen

- Neue Anleitung `docs/operations/legacy-archive.md` (verlinkt in `docs/index.md`): Speicherorte, Inhalt des Baums, Restore (`robocopy` aus dem Baum, Prüfung gegen das Manifest), Regenerierung von `mp3-split`, `tsv_for_index`, `index.build`, Hinweis auf die Leser in CO.RA.PAN_v3.
- Für CO.RA.PAN_v3 vorbereitet, nicht ausgeführt: `CORAPAN_LEGACY_ROOT` → `\\dfs.hrz.uni-marburg.de\PROJEKTE\FB10\TACKE_FORSCHUNGSDATEN\projects\panhispanic_media_corpora\legacy\corapan\corapan` (der Baum spiegelt das Repo-Layout). Außerdem `CORAPAN_LEGACY_ARCHIVE_ROOT`, `CORAPAN_LEGACY_ARCHIVE_TARGET_ID=corapan-archive-newfs-legacy`, `CORAPAN_LEGACY_BACKUP_ROOT` in der dortigen `.env` und die Topologie §19.10 von `PLANNED` auf `PRESENT` setzen. Zu klären: ob der Legacy-Ingest (`legacy_gold`) als „Leser der Geschichte“ aus LEGACY lesen darf (A6).

### 14.10 Git

- Ausgangs-HEAD `713629bd3b85cf6739db4cb689314879074493bc` (`main`, unverändert).
- Lokaler Branch `legacy/v3.2-provenance-and-retention` (aktuell ausgecheckt), Commits:
  1. `76669b5` maintenance: v3.2 annotation pipeline (02/03-Skripte, Tests, `tools/`)
  2. `2059ff7` docs: v3.2 run records; archivierte Run-Kommandos; überholte Smoke-Audits entfernt
  3. Abschluss-Commit dieses Berichts (Run-Berichte, Manifeste, Paketliste, Alt-ZIP-Inventar, `docs/operations/legacy-archive.md`, `docs/index.md`, Release-Record)
- Nicht committet: `maintenance_pipelines/_0_json/state/annotation/annotation_state.sqlite` (generierter Zustand; modifiziert, offen).
- Kein Push. `main` enthält keinen der Commits; ein Push von `main` würde sie nicht mitnehmen.

### 14.11 Bestätigung und offene Punkte

Kein Zugriff auf den Produktivserver, kein Deployment, kein Push, keine Zenodo-Aktion, keine Korpusverarbeitung. Keine Änderung an Verträgen, Konfiguration oder Repositories von CO.RA.PAN_v3 und CO.PRE.PAN_v3; deren Werkzeuge wurden nur ausgeführt bzw. importiert. Keine Änderung an PRODUCTION-/HISTORIC-Holdings, an D39-Snapshots oder an fremden Worktrees.

Offen:
1. **Umstellung der Legacy-Leser in CO.RA.PAN_v3** (§14.9). Danach Freigabe von `media/mp3-full` (6,45 GiB) mit erneutem Hash-Gate. Owner: CO.RA.PAN.
2. Konfiguration und Topologie in CO.RA.PAN (`.env`-Variablen, §19.10 `PRESENT`), Inventarzeile `legacy corapan` in `STORAGE_REDUNDANCY_INVENTORY.md`. Owner: CO.RA.PAN.
3. Ungecachte Wiederholung der Backup-Verifikation (optional; empfohlen vor Freigabe der Original-MP3).
4. Entscheidung über den alten D:-Bestand `protected_secondary/legacy_corapan` (31,6 GiB), jetzt durch Primary + B1 abgelöst.


---

## 15. Abschluss 2026-10-19 (ab 19:23): A7-Gate, ungecachte Fixity, Original-MP3, alte D:-Sicherung, Git

Der in §14.7 als nicht freigegeben dokumentierte Stand von `media/mp3-full` ist hier aufgelöst; §14 bleibt unverändert stehen.

### 15.1 Bewertung

| Teil | Status |
|---|---|
| NEW_FS-Retention | **PASS** – Baum `corapan` A5 PRESERVED, jetzt auch nach vollständigem **ungecachtem** Rücklesen |
| B1-Backup | **PASS** – vollständig ungecacht verifiziert (3.082/3.082), Manifest byte-gleich mit dem Primary |
| A7-Freigabe | **PASS** für `media/mp3-full` (D128 + eigene Gates); `media/transcripts` bewusst lokal erhalten |
| Lokaler Cleanup | **PASS** – 146 Original-MP3 entfernt (6,45 GiB); Repo 1,70 GiB |
| Alte D:-Sicherung | **PROTECTED** – nach CO.RA.PAN-Regeln weiter `KEEP_REQUIRED`; nicht gelöscht |
| Git | **PASS** – 6 lokale Commits, lokal in `main` integriert (Fast-Forward), kein Push |

### 15.2 v3-Release-Gate (D128)

Beobachtet nur lesend (Pin auf den Bericht im Haupt-Checkout, 90 s, 19:23–20:04; `local_reports/a7_probe.log`). Bericht
`C:\dev\panhispanic_media_corpora\corapan\docs\agent-runs\2026-10-19_legacy-reader-retirement-and-c-release.md`: Status COMPLETE,
`LEGACY_C_RELEASE_READY = true` (Scope `media/{mp3-full,transcripts}`, 296 Dateien, 7,17 GiB), Entscheidung D128.

| Start-Gate | Nachweis | Ergebnis |
|---|---|---|
| 1 READY im abgeschlossenen Bericht | Kopf des Berichts | erfüllt |
| 2 integriert | `32d01a207` ist Vorfahre von CO.RA.PAN `main`; `config/corpus_paths.yml` führt die Medien nur noch unter `${CORAPAN_LEGACY_ARCHIVE_TREE}`; `paths.py` wirft `LegacyMediaRetired` | erfüllt (im Code geprüft) |
| 3 Tests, A6/A7 | D128 §4/§6: A6 PASS, A7 PASS; Tests 309/21/410/813 passed, Fehlschläge nur vorbestehend und fremd | erfüllt (laut Bericht; hier nicht neu ausgeführt) |
| 4 keine aktive v3-Komponente braucht die C:-Audios | D128 §2: „Weiterhin notwendig: nothing“; kein Produktionsmodul importiert den Zugriff | erfüllt |
| 5 NEW_FS A5 PRESERVED | ungecachtes Vollrücklesen §15.3 | erfüllt |
| 6 B1 PASS | ungecachte Verifikation §15.3 | erfüllt |
| 7 lokale Dateien = Manifest | pro Datei unmittelbar vor dem Löschen §15.4 | erfüllt (146/146) |
| 8 kein Zugriff | keine Prozess-Kommandozeile mit `mp3-full`; v3-Leser stillgelegt | erfüllt |

### 15.3 Ungecachte Fixity

Werkzeug: `corapan_playground.storage.archive_secondary.sha256_uncached` (CO.RA.PAN, Windows `FILE_FLAG_NO_BUFFERING`; meldet je Datei den Lesemodus).

- **B1** (`D:\…\legacy\corapan\preservation_backup\corapan`), 19:32: 3.082/3.082 Dateien `uncached` gelesen, alle = Manifest; keine nicht gelisteten Dateien. Primary- und Backup-Manifest byte-gleich (SHA-256 `c651f9ba572d169eba0b6180dadb373206ba7a72f8570e3eb2b35c1ac765e73b`), `tree_sha256 f70bcbb3…80ae5f`, Primary-Identität `IDENTITY_OK`, Backup-Marker `holding LEGACY`. Dauer 10 s (lokale SSD).
- **Primary** (NEW_FS), 18:14 UTC: alle 3.082 Dateien `uncached` über das Netz gelesen (561 s ≈ 23 MB/s), `archive_tree` → keine Codes, **PRESERVED**.
- Einordnung: `FILE_FLAG_NO_BUFFERING` umgeht den Windows-Dateicache des Arbeitsplatzes. Caches des Fileservers oder des Plattencontrollers sind damit nicht ausgeschlossen. Ein vollständiger Restore wurde nicht durchgeführt; Read-back-Proben: 41/41 (§14.4) und 40/40 im D128-Lauf.

### 15.4 Gelöschte lokale MP3

Journal `local_reports/phasec_mp3_full_journal.jsonl`. Gate je Datei: frischer lokaler SHA-256 = `ARCHIVE_MANIFEST.json` = ungecacht gelesene B1-Kopie (Größe und Digest).

| | Dateien | Bytes |
|---|---:|---:|
| Original-MP3 `media/mp3-full/<Land>/*.mp3` gelöscht | 146 | 6.930.281.882 |
| mitgelöscht und sofort byte-identisch aus B1 wiederhergestellt: `media/mp3-full/.gitkeep` (Platzhalter; `media/` ist gitignoriert, das Skript hatte ihn als versioniert angenommen) | 1 | 42 |
| leere Länderordner entfernt | 25 | – |
| wegen Abweichung behalten | 0 | – |

Nicht verändert: der Produktivserver (seine Full-MP3, Splits, Transkripte, Index), NEW_FS, D:. `media/mp3-temp` (6 Snippet-Cache-Dateien, 0,56 MiB, nicht archiviert, regenerierbar) bleibt lokal.

### 15.5 Alte D:-Sicherung `protected_secondary\legacy_corapan` – PROTECTED

Inhaltlicher Abgleich aller 45.030 Objekte (33.947.564.625 Bytes) über die SHA-256 ihres eigenen, 2026-10-15 ungecacht geführten Journals (`local_reports/old_secondary_classification.json`):

| Klasse | Dateien | GiB | Nachweis |
|---|---:|---:|---|
| identisch im LEGACY-Baum (NEW_FS und B1) | 4.726 | 14,81 | SHA-256 im Manifest |
| alte Zenodo-v3-ZIPs | 25 | 6,39 | ZIP-SHA = Alt-ZIP-Inventar; alle 292 Mitglieder im Baum |
| Splits (regenerierbar; auf dem Server vorhanden) | 2.706 | 7,64 | – |
| `.venv` | 22.570 | 1,27 | Paketliste in `docs/agent-runs` |
| `tmp` (synthetische Sync-Testdaten) | 4 | 1,00 | Klassifikation 2026-10-19 |
| Caches (`__pycache__`, `.pytest_cache`, `.ruff_cache`) | 10.907 | 0,20 | – |
| `.git` | 1.306 | 0,19 | alle Refs im aktuellen Repo außer einem Codex-Checkpoint (`refs/codex/turn-diffs/…`, Commit `03307845…`); dessen 641 Blobs liegen alle im aktuellen Repo |
| Dev-PostgreSQL | 2.155 | 0,09 | lokal auf C: |
| Git-versionierte Dateien | 611 | 0,03 | Blob vorhanden (130 davon nach Zeilenend-Normalisierung) |
| identisch mit noch lokalen, gitignorierten Entwicklungsresten (Snippet-Cache, `app/tmp`, Deploy-/CI-Logs, Test-TSV, Pipeline-Report) | 20 | < 0,01 | SHA = lokale Datei |
| **einzigartige wissenschaftlich relevante Dateien** | **0** | – | – |

Trotzdem nicht gelöscht: `STORAGE_REDUNDANCY_INVENTORY.md` (CO.RA.PAN) führt den Bestand als `KEEP_REQUIRED`. Ein Bestand verlässt die Tabelle nur über sein Gate und eine dort dokumentierte Operator-Freigabe. D128 §5 bestätigt den Schutz und verlangt pro Klasse eine dokumentierte Entscheidung und ein Werkzeug, das jede Datei prüft. Ein solches Werkzeug gibt es nicht (`archive_secondary_copy_v1.py` kennt nur `run`/`verify`). Damit sind Voraussetzungen 3 („v3 hat die Regeln geprüft“: ja, Ergebnis geschützt), 4 und 8 nicht erfüllt. Freigegeben auf D: in diesem Run: 0 GiB. Die Klassifikation oben ist die Evidenz für eine spätere Freigabe pro Klasse.

### 15.6 Verbleibende lokale Bestände (1,697 GiB)

| Bestand | GiB | Grund |
|---|---:|---|
| `media/transcripts` | 0,71 | lokale Webapp (Player, Editor, Atlas), `03_build_metadata_stats.py`; im Archiv und auf Zenodo v4 |
| `data/blacklab/index`, `export/{tsv,metadata}`, `data/public`, `data/db/public` | 0,63 | lokale Suche und Statistik, Index-Rebuild |
| `data/db/restricted` | 0,09 | Dev-Datenbank (bewusst nicht archiviert) |
| `.git` | 0,19 | Historie |
| `app`, `docs`, `maintenance_pipelines`, Release-Record | 0,07 | Software, Doku, Evidenz |

### 15.7 Speicherbilanz

| Bereich | Vorher (Tagesbeginn) | Nachher | Ergebnis |
|---|---:|---:|---|
| Lokales Legacy-Repository | 25,22 GiB (31,6 vor ZIP-Löschung) | **1,70 GiB** | 23,53 GiB freigegeben (+ 6,39 alte ZIPs am Vormittag) |
| Separates Zenodo-Staging | 6,51 GiB | 0 | 6,51 GiB freigegeben |
| NEW_FS Legacy | 0 | 12,57 GiB | gesichert, PRESERVED |
| D: Legacy-Backup (B1) | 0 | 12,57 GiB | verifiziert |
| D: alte Sicherung | 31,62 GiB | 31,62 GiB | geschützt, unverändert |

Dieser Abschnitt: **6,45 GiB auf C:** (146 MP3). Über den ganzen Tag auf C: (ohne Doppelzählung, nach Journalen): alte ZIPs 6,39 + Staging 6,51 + Splits/`tmp`/`.venv`/Duplikate 11,99 + Phase B 5,09 + MP3 6,45 = **36,43 GiB**. Auf D: freigegeben: 0. Neu belegt: NEW_FS 12,57 GiB, D: 12,57 GiB.

### 15.8 Git

- Ausgangs-HEAD `713629b` (`main`). Lokaler `main` jetzt per Fast-Forward auf **`b35fe13`**, identisch mit `legacy/v3.2-provenance-and-retention`:
  1. `76669b5` Pipeline v3.2 (Skripte, Tests, Tools)
  2. `2059ff7` v3.2-Run-Records, archivierte Kommandos, entfernte überholte Smoke-Audits
  3. `95ca435` Berichte, Manifeste, Release-Record, Archiv-/Restore-Anleitung
  4. `bdde85f` Annotation-Resume-Zustand nach v3.2 (`annotation_state.sqlite`: 146 Zeilen `done`, Pipeline v3.2; die Datei war schon versioniert)
  5. `b35fe13` Doku: lokale MP3 entfernt, v3-Leser stillgelegt
  6. (Abschlussbericht dieses Abschnitts)
- `main` ist lokal 6 Commits vor `origin/main`. **Kein Push.** Ein Push auf `main` würde den Produktiv-Rebuild auslösen; die Commits ändern keinen App-Code (nur `maintenance_pipelines`, `docs`).
- Arbeitsbaum sauber. Keine großen Korpusdateien in Git (größte neue Datei: Provenienz-ZIP 1,3 MiB im Release-Record); keine Secrets (Musterprüfung).
- Validierung: `pytest maintenance_pipelines/_0_json/tests` mit System-Python, ohne Cache/Bytecode-Schreiben: **9 passed**. Doku-Verweise geprüft (existieren). App-Tests nicht ausgeführt (App-Code unverändert).

### 15.9 Produktivserver und Schwester-Repositories

Kein Zugriff auf den Produktivserver, kein Deployment, kein Push. CO.RA.PAN_v3 und CO.PRE.PAN_v3 nur gelesen bzw. ihre Werkzeuge mit Prozessvariablen ausgeführt (Python `-B`); keine Datei dort geändert. Keine Zenodo-Aktion. Archivbaum auf NEW_FS und B1 nur gelesen.

### 15.10 Verbleibende Risiken und Entscheidungen

1. Alte D:-Sicherung (31,62 GiB): Freigabe nur pro Klasse mit dokumentierter Operator-Entscheidung in `STORAGE_REDUNDANCY_INVENTORY.md` (CO.RA.PAN) und einem prüfenden Werkzeug. Die Evidenz in §15.5 zeigt keinen einzigartigen wissenschaftlichen Inhalt.
2. Original-Audio liegt jetzt institutionell nur auf NEW_FS (HRZ-Backup dort nicht von hier geprüft), auf D: (B1, gleicher Rechner) und in Zenodo v3/v4 (restricted, Dateiliste öffentlich nicht prüfbar) – sowie auf dem Produktivserver.
3. Für den write-once-Baum ist kein Re-Verifikationszyklus geplant (D128 §8).
4. Ein Push des lokalen `main` löst den Produktiv-Rebuild aus; bei Bedarf bewusst und zu einem gewählten Zeitpunkt.
