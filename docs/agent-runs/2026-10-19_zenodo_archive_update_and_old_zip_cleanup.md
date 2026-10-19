# Legacy-CO.RA.PAN – Zenodo-Archivaktualisierung und kontrollierte Alt-ZIP-Bereinigung

Datum: 2026-10-19 · Repo-HEAD: `713629bd3b85cf6739db4cb689314879074493bc` (Branch `main`, = `origin/main` laut letztem lokalen Fetch)
Vorgänger: `docs/agent-runs/2026-10-19_legacy_storage_runtime_archive_audit.md`
Legende: **VERIFIED** (Inspektion/Hash) · **REPORTED** (aus Doku) · **INFERRED** · **UNKNOWN**

## 0. Ergebnis

| Teil | Status |
|---|---|
| Wissenschaftlicher Datenstand bestimmt | **PASS** (mit dokumentierten Grenzen, §2) |
| Full-Corpus-Pakete (Version 4) | **PASS**: 25 ZIPs, 146 Aufnahmen, 6.983.407.386 Bytes, validiert |
| Softwarearchiv | **PASS**: Stand `713629b`, Archivbezeichnung `archive-2026-06-14-713629b`, MIT (§3, §12) |
| v3.2-Provenienz-Supplement | **PASS** mit dokumentierten Reproduzierbarkeitsgrenzen (§12.2) |
| Upload-Kit (README, Notes, Manifest, Prüfsummen, Metadaten, Anleitung) | **PASS** |
| Alt-ZIPs löschen | **PASS**: alle 9 Gates erfüllt, 25 ZIPs gelöscht (§6) |
| Retention-Evidenz | **PARTIAL**: D:-Sekundärkopie verifiziert; NEW_FS-Primary für Legacy existiert nicht (§7) |
| Zenodo (Erweiterung) | **PASS**: beide Versionen nach Operatorfreigabe veröffentlicht und verifiziert – Full Corpus 10.5281/zenodo.23470771, Software 10.5281/zenodo.23470763 (§12, §13) |

Kein Commit, kein Push, kein Tag, kein Deployment. Zenodo: nur autorisierte Draft-Operationen, keine Veröffentlichung.

> Die Abschnitte 1–11 beschreiben den Stand vor der Erweiterung. Wo §3 noch `main@713629b` oder offene Lizenzfragen nennt, gilt §12.

## 1. Preflight

- Git-Status bei Start: 36 Einträge (die 35 bestehenden plus der Bericht des Audits). Am Ende: dieselben Einträge. Neu hinzugekommen sind nur die beiden Dateien dieses Runs unter `docs/agent-runs/` (diesen Bericht und das Inventar §6). Die vorbestehenden Änderungen (`02_annotate…`, `03_build…`, Tests, `tools/`, Löschungen) wurden nicht berührt.
- Laufende Prozesse: drei Python-Prozesse gehören zu CO.RA.PAN_v3 (`reservoir_controller`, `acquisition_working_copies`, `pytest`); keiner arbeitet im Legacy-Repo. Transkripte wurden zuletzt am 2026-06-14 geändert (keine neueren Dateien).
- Speicher: C: 116 GiB frei, D: 3 TiB frei. Staging auf C: neben dem Repo, nicht in `tmp/`.
- Staging-Pfad: `C:\dev\panhispanic_media_corpora\legacy\corapan_zenodo_staging\` (ausserhalb des Git-Repos; enthält `README_STAGING.md`).

## 2. Verwendete wissenschaftliche Datenversion

**Quelle:** `media/transcripts` (146 JSON, 25 Ordner) und `media/mp3-full` (146 MP3), Stand 2026-06-14 (Pipeline `corapan-transcript-ann-v3.2`, Tense-Regeln `tense-v4-coprepan-compatible`, Schema `corapan-transcript-json/v3`).

Beantwortung der Prüffragen:

1. **Vollständigkeit** – VERIFIED: 146 JSON ↔ 146 MP3, Namen je Land 1:1 gleich; 1.488.019 Wortobjekte; Summe stimmt mit dem öffentlichen Metadata-Record (146 Aufnahmen, 1.488.019 Wörter) überein; alle 146 Dateien tragen `pipeline_version v3.2`, `schema_version corapan-transcript-json/v3`, `tense_rules tense-v4-coprepan-compatible`.
2. **Abgeschlossener Stand** – REPORTED: die internen Läufe vom 2026-06-14 (`…v3_2_inventory_check`, `…final_corapan_internal_cleanup`) melden 0 Hard Failures, 0 fehlende/doppelte Token-IDs, Tests 9 passed. Eine Datei mit „known YELLOW“ (COL/2024-01-03_COL_Caracol, nicht blockierend). Nicht erneut ausgeführt.
3. **Zuordnung** – VERIFIED: Dateiname = `file_id` + Endung bis auf einen Fall (4.).
4. **Identitäten** – VERIFIED: Länder-/Regionsordner = `country_code` in allen 146 Dateien. **Ein Befund:** `NIC/2025-01-27_NIC_RCorp` hat intern `file_id`/`filename` = `2024-01-27_…` (Datumsfeld 2025-01-27). Dieselbe Abweichung steht in Version 3 und im öffentlichen Metadata-Record. Nicht verändert, in Release Notes dokumentiert.
5. **Uncommittete/laufende Arbeiten** – VERIFIED: Die Pipeline-Skripte, die v3.2 erzeugten (`02_annotate_transcripts_v3.py` v3.2, `03_build_metadata_stats.py`, Tests, `tools/`), sind **uncommittet**; `HEAD` enthält `v3.1`/`tense-v3`. Keine laufenden Annotationsprozesse im Legacy-Repo.
6. **Editor-Änderungen nur auf dem Server** – UNKNOWN. Lokales `edit_log.jsonl`: 38 Einträge 2025-10-25…30 (ARG-Mitre-Dateien). Server-Transkripte laut Audit zuletzt 2025-11-16 geändert (REPORTED). Ein Server-Vergleich war nicht möglich. Die lokalen Dateien werden daher nicht als identisch mit der Produktion bezeichnet.
7. **Dokumentation** – Annotationsschema und Tense-Migration sind intern dokumentiert (`maintenance_pipelines/_0_json/docs/agent-runs/2026-06-14_corapan_tense_schema_coprepan_alignment.md` u. a., teils untracked); in die Release Notes übernommen.
8. **Einschränkungen** – in `full-corpus/RELEASE_NOTES.md` aufgeführt (Provenienz, Server-Stand, NIC-Fall, automatische Annotation, geänderte Tense-Rollen).

**Vergleich mit Version 3** (VERIFIED, Feld-für-Feld gegen `pre-v3_1-transcripts` = Inhalt der v3-ZIPs, SHA-256 identisch): Token-ID, Text, `start_ms`, Segmentgrenzen und Sprecher in allen 1.488.019 Wortobjekten gleich; `end_ms` bei 1 Token geändert (dokumentierte Timestamp-Reparatur ARG-SDE); `dep` 187.380, `head_text` 162.420, `morph` 88.974, `pos` 63.295, `lemma` 35.282, `norm` 12.817 Wortobjekte unterschiedlich. Eine Qualitätsverbesserung wird **nicht** behauptet.

## 3. Erzeugte Upload-Pakete

Ort: `…\corapan_zenodo_staging\zenodo_upload_ready\`

### 3.1 Full Corpus (`full-corpus/`, 30 Dateien, ≈ 6,5 GiB)

Struktur wie Version 3 (`<CODE>.zip` mit `mp3-files/` und `json-transcripts/`). Deterministisch (sortiert, fester Zeitstempel 2026-01-01, MP3 gespeichert, JSON deflate-9; Wiederholungsbau von URY → identischer SHA-256). MP3 werden nirgends doppelt gespeichert. Das Gesamtvolumen ist etwa 120 MB grösser als die Alt-ZIPs (6.983.407.386 vs. 6.863.725.503 Bytes), weil die MP3 nicht mehr deflated werden.

| Paket | Aufn. | MP3/JSON | Bytes | SHA-256 |
|---|---:|---|---:|---|
| ARG.zip | 8 | 8/8 | 557,448,352 | `19315bde945fcaea76558dbc92e851351a392d8fd537bfad9adefc77c6b49b09` |
| ARG-CBA.zip | 5 | 5/5 | 256,111,600 | `417cdd638b8b109ae8c0642658805bd44fc8358c1ef276f464c835d2c70c8268` |
| ARG-CHU.zip | 6 | 6/6 | 206,949,069 | `287f0b1fffa6223c77bcefa155fd46f75adc2a0e4ad6362ce508c3b274fb803d` |
| ARG-SDE.zip | 6 | 6/6 | 262,043,170 | `b5ade24dcf9dae80bec764db8c7d484e9a96e782be311a2c67d7dc673356da14` |
| BOL.zip | 6 | 6/6 | 270,417,389 | `dad89998a842df0449b71f45023c5d5d724776c81177f1eab10ff3ad2d396277` |
| CHL.zip | 5 | 5/5 | 352,938,161 | `bbae92c1ebabdd8578df4e090241fd1e606ad2a0137f1779c1b44b6dc00f1350` |
| COL.zip | 6 | 6/6 | 178,192,423 | `80bf1f7ab5153af8a4c82d87229681d01ac1b358205d82fb16ca515f939122ee` |
| CRI.zip | 6 | 6/6 | 350,502,320 | `0cf1b057f9836fac134c12560081ed1858690405999dc30c5d7f3299f2223c65` |
| CUB.zip | 6 | 6/6 | 180,312,873 | `7fcc67f03db21ec3663bc40d81f4fd45fd75222143167ee3321d85d33f9e8819` |
| DOM.zip | 6 | 6/6 | 175,493,449 | `5cf6b72fafa45220b728eb0ac4799920f6d17bbf5b471f46b40f9732876d79c9` |
| ECU.zip | 6 | 6/6 | 353,078,105 | `ce226d0b539295abc12b5d27672cfc6c80961f25957b0ca2cfcfba3690153f55` |
| ESP.zip | 6 | 6/6 | 351,542,841 | `6f74ed4767c7d401db64f9e34c0a2830cd6b9b01c07a05d73ef709936a78f9f5` |
| ESP-CAN.zip | 6 | 6/6 | 176,626,183 | `c5d8e45f07c3faf7f10842ffdec59b982821e6e9022944840b03eec17c2e3c5e` |
| ESP-SEV.zip | 6 | 6/6 | 181,509,546 | `263aff43fc02e14875e7b71c474b59eda446609ab3e1a86ee3bcc18c69e9fe11` |
| GTM.zip | 6 | 6/6 | 263,305,479 | `2b3c5a3b754eb679ae53d2bb4fca5f4816a3c35fb9bb5d3a8e457b15f9e6f018` |
| HND.zip | 6 | 6/6 | 262,527,415 | `99aa45194a02268c06ecc29014061e7cb3d364f1617cc726704406473d192d90` |
| MEX.zip | 6 | 6/6 | 356,672,951 | `4daac7f495ce0df464c9298c67b6ab707828c239e07e3b3aed4d214c7b664600` |
| NIC.zip | 6 | 6/6 | 348,698,459 | `82b0e08b56810feb708136ec1fef7af5bd4a0c5bf22c41e465f73c7a46071353` |
| PAN.zip | 6 | 6/6 | 264,463,959 | `3d715f4af10d9002e7ebfa289ed3f1f8cca7c37e50cb54f055aad69655404f02` |
| PER.zip | 4 | 4/4 | 350,266,077 | `4fd0d6c18daa014de058489c579709a9569fc3dc8fcd3c7bb9b48fa662087322` |
| PRY.zip | 6 | 6/6 | 177,684,580 | `9a71cb3252c8da12bd8994bf630675d10455b0d9fb3ccee56428139d3ee0422b` |
| SLV.zip | 6 | 6/6 | 350,094,602 | `507c9b7ab4c6fab0726bbd70dd555aff74a8b9f84be9cd32953f95dfac987117` |
| URY.zip | 4 | 4/4 | 69,188,758 | `7854d6c61e2e90ecc239acb225f58948bf6a4ba15af246fa33d35c1f8f35bb13` |
| USA.zip | 6 | 6/6 | 340,570,785 | `44e2e8c045ef78059cb40d22bf3470efea5cf4a7cbd5161d16ed3f57670b2c87` |
| VEN.zip | 6 | 6/6 | 346,768,840 | `5f22ca1da150d186662d6e555eba40e5b432e74aa52601595710d0abc5d43916` |

Begleitdateien: `README.md`, `RELEASE_NOTES.md`, `MANIFEST.csv` (146 Zeilen mit Paketdaten, Member-SHA-256, Annotationsversionen, SHA-256 der v3-JSON), `FILE_INVENTORY.json`, `SHA256SUMS` (`sha256sum -c` → alle OK).

### 3.2 Software (`software/`, 4 Dateien)

| Datei | Bytes | SHA-256 |
|---|---:|---|
| `corapan-webapp-713629b.zip` | 7,494,334 | `134a71c106686f59c71c131bd59a0681775ad33ea2640de552e3802857c8fdd4` |

`git archive` von `HEAD` (zweiter Bau → identisches Ergebnis; Commit-SHA im ZIP-Kommentar), 709 Einträge. Ausgeschlossen: cwRsync-Binaries (`app/tools/cwrsync/bin`), `bfg.jar`, `_0_json/backups` (enthält Editor-Log) und `_0_json/state` (SQLite). Mustersuche nach privaten Schlüsseln, GitHub/AWS/Slack-Tokens und Passwörtern in DB-URLs: nur Entwicklungs-/Testplatzhalter. Die Server-IP steht in Deploy-Skripten/Doku (wie im öffentlichen Repo; Hinweis in den Release Notes).
- **Version:** keine Tag-Entscheidung getroffen. Vorgeschlagenes, rein faktisches Label `main@713629b`; alternativ vom Operator zu erstellender Tag. `pyproject.toml`/`CITATION.cff` stehen weiter auf `1.0.0`.
- **Änderungen seit `v1.1.0`:** 19 Commits (2026-03-24…06-14), gruppiert in `software/RELEASE_NOTES.md`.
- **Produktionsbezug:** nicht behauptet; `HEAD` = `origin/main` (lokal), ein erfolgreicher Deploy wurde nicht geprüft.
- **Lücke:** Das Archiv enthält Pipeline v3.1, nicht v3.2. Zur Provenienz liegt lokal (nicht hochzuladen) `local_only/provisional_uncommitted_pipeline_v3.2_snapshot.zip` mit SHA-256-Manifest der 7 uncommitteten Dateien. Empfehlung: committen und das Archiv neu bauen (Anleitung im Guide). Das ist Operatorentscheidung.

## 4. Validierung (VERIFIED)

Für alle 25 neuen ZIPs, unabhängig vom Bau neu gelesen: `testzip` OK; Mitgliederliste = erwartete Liste (keine fehlenden/doppelten/fremden Mitglieder); SHA-256 jedes der 292 Mitglieder = SHA-256 der Quelldatei; SHA-256 der Pakete nach dem Bau unverändert; Zuordnung MP3 ↔ JSON je Aufnahme über gleiche `recording_id`; Paketgrössen plausibel (66 MB … 557 MB). Gesamt 25 Pakete, 146 Aufnahmen, 0 Probleme. Zenodo-Grenzen (geprüft 2026-10-19): 50 GB und 100 Dateien je Record (Quotenerhöhung auf Antrag); wir liegen bei 6,5 GiB und 30 Dateien.

## 5. Abweichungen zu den bisherigen Zenodo-Versionen

| Record | Bisher | Neu |
|---|---|---|
| Full Corpus v3 (10.5281/zenodo.18782190) | JSON = Stand `pre-v3_1` (CRC/SHA-gleich mit Backup) | JSON v3.2 (alle 146 verschieden), Audio byte-identisch (146/146) |
| Software v1.1.0 (10.5281/zenodo.19202684) | GitHub-Zipball, 26,4 MB, Licence-Feld `cc-by-4.0` | `main@713629b`, 7,5 MB (ohne Binaries), Licence-Vorschlag `mit` (Repo-Lizenz) – Operatorentscheidung |
| Metadata (10.5281/zenodo.17843469) | v1.0.0, 146 Aufnahmen, 1.488.019 Wörter | konsistent; keine neue Version nötig; Beschreibung des Full-Corpus-Records hat noch Platzhalter für diese DOI |
| Sample (10.5281/zenodo.15378479) | 1 JSON | nicht geändert; Annotationsstand nicht geprüft |

Nicht lesbar: der genaue Beschreibungstext und die Dateiliste des Restricted-Records (API zeigt nur Zusammenfassungen/keine Dateien). Die Metadatenvorlage markiert diese Stellen mit CONFIRM.

## 6. Kontrollierte Alt-ZIP-Löschung

Betroffen: die 25 Dateien in `maintenance_pipelines/_1_zenodo-repos/Zenodo Full Corpus/*.zip` (6.863.725.503 Bytes = 6,39 GiB), nichts anderes. Member-Inventar (292 Zeilen, SHA-256 der Pakete und Mitglieder): `docs/agent-runs/2026-10-19_old_full_corpus_zip_inventory.csv`.

| Gate | Nachweis | Ergebnis |
|---|---|---|
| 1 Liste + SHA-256 | 25 ZIPs erfasst | erfüllt |
| 2 Mitglieder erfasst | 292 (146 MP3 + 146 JSON), keine weiteren Inhalte, `testzip` OK | erfüllt |
| 3 Audio erhalten | 146/146 SHA-256 gleich `media/mp3-full`, gleich D:-Kopie, gleich neuem Paket | erfüllt |
| 4 JSON im Backup | 146/146 SHA-256 gleich `pre-v3_1-transcripts` (lokal) und D:-Kopie | erfüllt |
| 5 Backups unverändert | nur lesend zugegriffen | erfüllt |
| 6 Zusatzinhalte | keine (nur `mp3-files/`, `json-transcripts/`) | erfüllt |
| 7 Unabhängige Erhaltung | alle 25 ZIPs auf `D:\projects\…\protected_secondary\legacy_corapan` byte-identisch (SHA-256), Sekundärkopie am 2026-10-15 verifiziert (45.030 Objekte, `ok: true`); zusätzlich Zenodo v3 (Restricted, nicht prüfbar) | erfüllt |
| 8 Neue Pakete validiert | §4 | erfüllt |
| 9 Keine Abhängigkeit | einzige Referenz: `zenodo_full-corpus.py` (erzeugt ZIPs neu) und Doku; kein CO.RA.PAN_v3-Code verweist darauf; keine laufende Arbeit | erfüllt |

Direkt vor dem Löschen wurden alle 25 ZIPs erneut gehasht (C: = Inventar = D:). **Ergebnis: 25 Dateien gelöscht, 6.863.725.503 Bytes; Ordner jetzt leer.** Log: `…\local_only\reports\deletion_log.json`.

Hinweise: (a) `maintenance_pipelines/_1_zenodo-repos/zip_process.log` bleibt (nicht ZIP) und beschreibt jetzt nicht mehr vorhandene ZIPs; `zenodo_full-corpus.py` würde bei unverändertem Log Länder überspringen, statt ZIPs neu zu bauen – vor einer erneuten Nutzung das Log aufräumen (nicht angefasst). (b) Netto auf C: spart der Run nichts: die neue Generation belegt 6,5 GiB im Staging. (c) Die D:-Sekundärkopie ist kein Off-Site-Backup und liegt auf demselben Rechner (der Receipt behauptet dies selbst nicht).

## 7. Retention-/Backup-Evidenz

| Ort | Audio (146 MP3) | JSON v3 (Zenodo-Stand) | Beleg |
|---|---|---|---|
| Lokal `media/mp3-full` | ja | – | VERIFIED |
| D: Sekundärkopie 2026-10-15 | ja, SHA-256 gleich | ja (`pre-v3_1`), SHA-256 gleich | VERIFIED + Receipt `SECONDARY_COPY_VERIFIED` |
| **NEW_FS Retention-Primary** | **nicht vorhanden für Legacy** | – | Der Vorschlag `corapan/docs/plans/2026-10-19_newfs-legacy-evidence-archive-proposal.md` ist „PROPOSAL, NOT IN FORCE“; `STORAGE_REDUNDANCY_INVENTORY.md`: `legacy corapan` = `KEEP_UNTIL_GATE`. Keine Annahme einer abgeschlossenen Migration. |
| Produktivserver | `mp3-full` 6,5 G | Transkripte 738 M | nur REPORTED (März 2026), nicht zugreifbar |
| Zenodo v3 (restricted) | laut Beschreibung ja | ja | nicht prüfbar (Dateiliste nicht öffentlich) |
| Neue Pakete im Staging | ja | v3.2 | VERIFIED (Zwischenstand bis zum Upload ohne zweite Kopie) |

Lücken: kein institutioneller Primary; keine Off-Site-Kopie; v3.2-Transkripte (neuer Stand) liegen nur lokal (+ D: Stand 2026-10-15, vor Paketbau, unverändert seit 2026-06-14) und im Staging; Serverstand unbekannt. Es wurde nichts kopiert oder migriert.

## 8. Kandidatenübersicht für den nächsten lokalen Cleanup (nichts gelöscht)

Grössen aus dem Audit (lokal, MiB), außer wo vermerkt.

| Bestand | Größe | Bemerkung / Voraussetzung |
|---|---:|---|
| `media/mp3-full` | 6.609 | erst nach NEW_FS-Primary + Verifikation; D: hat verifizierte Kopie; Staging-ZIPs enthalten sie ebenfalls |
| `media/mp3-split` | 7.821 | lokal entbehrlich; regenerierbar (Audit §5); nicht auf Server anfassen |
| `data/blacklab/export/tsv/tsv_for_index.bak_*` ×2 | 729 | hash-identisch mit `tsv_for_index` (Audit) |
| `data/blacklab/quarantine/index.build` | 279 | = aktiver Index (Audit) |
| `data/blacklab/quarantine` Rest, `backups` | 1.998 / 557 | Inhalt `prior_unused_snapshot` ungeprüft |
| `_0_json/backups` (pre-v3_1 ≙ Zenodo v3 JSON, pre-tense-migration, Smoke) | 2.378 | Provenienz; nach Zenodo-v4-Veröffentlichung und institutioneller Kopie entscheiden |
| `tmp/` | 1.694 | Testmaterial (`src-many` Kopie von pre-v3_1) |
| `.venv` | 1.501 | regenerierbar |
| Staging `corapan_zenodo_staging` | ≈ 6.700 | erst nach Veröffentlichung und Prüfung (Guide §4) |

## 9. Offene wissenschaftliche/publikationstechnische Fragen

1. Softwareversion/Tag und Lizenz (MIT vs. CC-BY-4.0 im bisherigen Zenodo-Record).
2. v3.2-Skripte committen und Softwarearchiv neu bauen oder bewusst ohne.
3. Entspricht der Produktionsstand dem lokalen v3.2-Stand (Server-Transkripte, Index)? Sollen Server/Index auf v3.2 gebracht werden? (nicht Teil dieses Auftrags)
4. NIC-Datumsfall (`2024-01-27` intern vs. `2025-01-27`): als bekannt belassen oder in späterer Version korrigieren.
5. Die geänderten Tense-Rollen machen Ergebnisse auf v3-Basis nicht direkt reproduzierbar; v3 bleibt unter eigenem DOI.
6. Wortlaut der bestehenden Zugriffsbedingungen/Beschreibung des Restricted-Records (konnte nicht vollständig gelesen werden) und Platzhalter-DOI korrigieren.

## 10. Manuelle Upload-Schritte

Vollständig in `…\zenodo_upload_ready\ZENODO_UPLOAD_GUIDE.md`. Kurzfassung: (1) Full-Corpus-Record öffnen → *New version* → alte 25 ZIPs im Draft löschen → 30 Dateien aus `full-corpus/` hochladen → Metadaten nach `zenodo_metadata/full-corpus.metadata.json`, **Restricted** beibehalten → prüfen → veröffentlichen. (2) Software-Record → *New version* → altes ZIP löschen → 4 Dateien aus `software/` → Metadaten nach `software.metadata.json` → veröffentlichen. (3) Querverweise/DOIs prüfen und dokumentieren. (4) Erst danach Staging-ZIPs lokal entfernen.

## 11. Git-Status und Bestätigung

`git status`: unverändert gegenüber dem Start bis auf die zwei neuen Dateien in `docs/agent-runs/` (dieser Bericht, `2026-10-19_old_full_corpus_zip_inventory.csv`). Kein Commit, kein Push, kein Tag, kein Deployment, kein Zenodo-Upload oder -Draft, keine Secrets gelesen, kein Server-/Produktivzugriff, keine Änderung an Annotationen, Original-MP3, JSON-Backups, D:-Kopien, CO.RA.PAN_v3 oder CO.PRE.PAN_v3. Zusätzlich angelegt: `C:\dev\panhispanic_media_corpora\legacy\corapan_zenodo_staging\`. Gelöscht: nur die 25 Alt-ZIPs (§6).


## 12. Erweiterung: Zenodo-Drafts per API, v3.2-Provenienz, Softwareversion und Lizenz (2026-10-19)

Autorisierung durch den Operator: Anlegen und Befüllen neuer Versionsentwürfe über die Zenodo-API, **ohne Veröffentlichung**. Das Token wurde über ein separates Eingabefenster DPAPI-verschlüsselt unter `%LOCALAPPDATA%\corapan_zenodo\token.dpapi` abgelegt (nur für das Windows-Konto lesbar) und vom Skript nur im Speicher entschlüsselt. Es steht in keiner Datei, keinem Log und keinem Bericht (Scan der Reports und Upload-Ordner: kein Treffer). Skript: `…\corapan_zenodo_staging\local_only\scripts\zenodo_draft.py` (Legacy-Deposit-API laut developers.zenodo.org: `actions/newversion`, Bucket-Upload, `PUT` Metadaten; ein Guard verhindert jeden Aufruf von `actions/publish`).

### 12.1 API-Aktionen

| Schritt | Full Corpus | Software |
|---|---|---|
| Inspektion (nur lesend) | 4 veröffentlichte Versionen, kein offener Versionsentwurf. Version 17828582 (2025-12-05) steht seit 2026-02-23 auf `inprogress` (offene, nicht gespeicherte Bearbeitung), nicht angefasst | 3 veröffentlichte Versionen (v1.0.0, v1.0.1, v1.1.0), kein Entwurf |
| `newversion` auf neueste Version | 18782190 → Draft **23470771** | 19202684 → Draft **23470763** |
| Geerbte Dateien im Draft gelöscht | 25 alte ZIPs | `FTacke/corapan-webapp-v1.1.0.zip` |
| Upload (Bucket-API; je Datei MD5 und Größe gegen lokal geprüft; Wiederaufnahme: identische Dateien werden übersprungen, abweichende gelöscht und neu geladen) | 31 Dateien, keine Wiederholung nötig | 4 Dateien |
| Nachträglich ersetzt (nach Abschluss des Hauptuploads) | README.md, RELEASE_NOTES.md, FILE_INVENTORY.json, SHA256SUMS; neu: Provenienz-Supplement | README.md, RELEASE_NOTES.md, SHA256SUMS |
| Metadaten (`PUT`) | siehe 12.3 | siehe 12.4 |
| Veröffentlichung | **nein** | **nein** |

### 12.2 v3.2-Provenienz-Supplement

Datei `CORAPAN_FullCorpus_v4_annotation-v3.2_provenance.zip` (1.335.144 Bytes, SHA-256 `1277df70983fb972054dbb40df83d59e26e054d69809cfa8b7a35e7d6c7bb24e`), 42 Einträge, internes `MANIFEST.sha256`, Beschreibung in `PROVENANCE.md`. Inhalt:

- `code/working_tree_v3.2/`: die 7 uncommitteten Quellen (`02_annotate_transcripts_v3.py` v3.2, `03_build_metadata_stats.py`, ein Test, 4 Tools inkl. `migrate_tense_to_coprepan_schema.py`); SHA-256 identisch mit dem früheren lokalen Snapshot.
- `code/committed_713629b/`: Vergleichsfassungen aus dem Commit (Pipeline v3.1, Audit-Skript, Pipeline-README, `requirements-lokal.txt`).
- `run_records/`: Run-Berichte, Audits und Validierungen vom 2026-06-14 (nur CO.RA.PAN-bezogen).
- `logs/`: Annotationslog, Log des angewendeten Migrationslaufs, Konsolenprotokoll des Volllaufs ohne die Kopfzeilen mit Benutzer, Rechner und Prozess.
- `environment/installed_packages.txt`: Paketliste der `.venv` (Python 3.12.10, spaCy 3.8.14, `es_dep_news_trf` 3.8.0, torch 2.12.0, transformers 4.49.0 u. a.; vor dem Lauf installiert, seither unverändert).

Ausgeschlossen: die CO.PRE.PAN-Referenzschema-Extraktion (enthält Textbeispiele aus dem fremden Korpus), Cleanup-Berichte, Annotation-State-DB, Backups. Sicherheits-Scan: keine Schlüssel, Tokens oder Passwörter, keine Benutzerpfade oder Rechnernamen. Die einzige E-Mail-Adresse ist eine öffentliche Behördenadresse aus dem Sendungstext (Funkinhalt, Restricted-Record).

**Verhältnis zum Annotationsstand (VERIFIED):** Alle 146 Transkripte tragen `pipeline_version v3.2`, `tense_rules tense-v4-coprepan-compatible`, `spacy_version 3.8.14`, `validation passed` sowie die Stufen `spacy` (≈ 08:26 UTC) und `tense`/`validate` (11:10 UTC).

**Reproduzierbarkeitsgrenzen:**
- `02_annotate_transcripts_v3.py` wurde um 11:14:52 UTC geändert, also etwa 5 Minuten nach dem Migrationslauf (11:09:46–11:10 UTC). Die archivierte Fassung ist deshalb nicht nachweislich identisch mit der ausgeführten. Das Migrationswerkzeug (11:06 UTC) stammt dagegen von vor dem Lauf.
- Die v3.1-Fassung des spaCy-Laufs (08:25 UTC) ist nur über den späteren Commit (10:56 UTC) belegt.
- Hardware und Determinismus des Transformer-Modells sind nicht protokolliert, eine unabhängige Neuausführung fand nicht statt.

Ergebnis: dokumentiert, aber nicht bit-genau reproduzierbar. So steht es auch in README, RELEASE_NOTES und PROVENANCE.md.

### 12.3 Full-Corpus-Draft (https://zenodo.org/deposit/23470771)

- Version `4`, Publikationsdatum 2026-10-19 (bei späterer Veröffentlichung anpassbar). Reservierte DOI 10.5281/zenodo.23470771, gültig erst mit Veröffentlichung.
- **Restricted** ist bestätigt. Der Rechtstext aus Version 3 ist unverändert übernommen (in Beschreibung und `access_conditions`). Die API gibt `access_conditions` wie schon bei Version 3 nicht zurück, deshalb im Webformular kontrollieren.
- Beschreibung: Der bestehende Text ist übernommen. Geändert wurde:
  - Platzhalter `<INSERT DOI OF PUBLIC METADATA RECORD>` ersetzt.
  - Falscher Skriptname durch eine Paketbeschreibung ersetzt.
  - Abschnitte „Contents (version 4)“, „Changes in version 4“ und „Provenance supplement“ ergänzt.
  - NIC-Hinweis und Server-Vorbehalt ergänzt.
  - Projektlink korrigiert: der alte `hispanistica.online.uni-marburg.de/corapan/` liefert 404, der neue `https://hispanistica.com/projects/corapan/` liefert HTTP 200.
- Related Identifiers: Sample (isSupplementedBy), Metadata 10.5281/zenodo.17843469 (isSupplementedBy, neu), Software (isRequiredBy).
- Keywords und Sprache `spa` neu gesetzt (vorher leer), Creator unverändert.
- Dateien (31, MD5 und Größe jeweils = lokal):
  - 25 Länder-ZIPs, unverändert (SHA-256 in §3.1)
  - Provenienz-Supplement
  - `README.md` (`b5ffcd68…`), `RELEASE_NOTES.md` (`5efe1952…`), `MANIFEST.csv` (`c433f3f9…`), `FILE_INVENTORY.json` (`2046c5a5…`), `SHA256SUMS`
  - Keine geerbten oder veralteten Dateien im Draft.

### 12.4 Software-Draft (https://zenodo.org/deposit/23470763)

- Version `archive-2026-06-14-713629b`. Die Release-Konvention ist `vX.Y.Z`; für diesen Commit gibt es keinen Tag, deshalb eine datierte Archivbezeichnung. Kein Tag erstellt. Commit `713629bd3b85cf6739db4cb689314879074493bc`, reservierte DOI 10.5281/zenodo.23470763.
- **Lizenz MIT** (Zenodo-ID `mit-license`), geprüft gegen `app/LICENSE` (MIT, © 2025–2026 Felix Tacke). Drittkomponenten im Archiv mit eigenen Lizenzen sind im README aufgeführt:
  - jQuery, DataTables, Select2: MIT
  - htmx: Upstream-Lizenz
  - Material Symbols: Apache-2.0
  - cwRsync/rsync-Doku: GPL-3.0, nur Textdateien
- Ältere Versionen (CC-BY-4.0) bleiben unverändert.
- Öffentlich (open). Creator um Affiliation und ORCID aus `CITATION.cff` ergänzt. Related: GitHub-Commit (isSupplementTo), Full Corpus (requires).
- Dateien (4, MD5 und Größe = lokal): `corapan-webapp-713629b.zip` (SHA-256 `134a71c1…8fdd4`), `README.md` (`97891df7…`), `RELEASE_NOTES.md` (`ec66d4dd…`), `SHA256SUMS`.
- Die drei Stände sind getrennt:
  1. committed Software = dieses Archiv
  2. v3.2-Verarbeitungssnapshot = Supplement im Full Corpus
  3. Produktion = nicht nachgewiesen und nicht behauptet

### 12.5 Abschlussprüfung (API-Rücklesung, `local_only/reports/zenodo_final_check.json`)

| Prüfung | Full Corpus | Software |
|---|---|---|
| Draft unveröffentlicht (`submitted=false`, `unsubmitted`) | ja | ja |
| Dateien vollständig, Größe + MD5 = lokal, keine Extras | 31/31 | 4/4 |
| Zugriff | restricted | open |
| Lizenz | keine (wie bisher, Daten) | MIT |
| Platzhalter / toter Link in Beschreibung | nein / nein | nein / nein |
| Alle veröffentlichten Versionen unverändert (`modified` und Dateien) | ja | ja |

### 12.6 Verbleibend

- **Veröffentlichung** beider Drafts wartet auf deine ausdrückliche Freigabe.
- `access_conditions` des Full-Corpus-Drafts im Webformular sichtprüfen (die API zeigt das Feld nicht an).
- Offene Bearbeitung der alten Full-Corpus-Version 17828582 (`inprogress` seit 2026-02-23): im Webformular verwerfen oder bewusst belassen.
- Lokale Upload-ZIPs erst nach Veröffentlichung, Verifikation und gesonderter Freigabe entfernen.
- Token-Datei `%LOCALAPPDATA%\corapan_zenodo\token.dpapi` nach Abschluss löschen (oder das Token bei Zenodo widerrufen).
- Keine weiteren lokalen Daten gelöscht oder verschoben. Der Git-Status ist bis auf die Dateien dieses Runs in `docs/agent-runs/` unverändert.


## 13. Veröffentlichung (2026-10-19, nach ausdrücklicher Operatorfreigabe)

Der Operator hat beide Drafts geprüft (Zugriffsbedingungen und Sichtbarkeit bestätigt) und die Veröffentlichung von genau diesen beiden freigegeben. Skript: `local_only/scripts/zenodo_publish.py`. Es akzeptiert nur die IDs 23470771 und 23470763 und prüft unmittelbar vor `actions/publish` erneut Draft-Status, Zugriff, Lizenz sowie Dateiliste, Größe und MD5 gegen die lokalen Dateien.

| | Full Corpus | Software |
|---|---|---|
| Veröffentlichte Version | **https://doi.org/10.5281/zenodo.23470771** (https://zenodo.org/records/23470771) | **https://doi.org/10.5281/zenodo.23470763** (https://zenodo.org/records/23470763) |
| Concept-DOI → löst auf neue Version auf | 10.5281/zenodo.15360942 → 23470771 | 10.5281/zenodo.17834023 → 23470763 |
| Versionsbeziehung (`is_last`) | ja (5. Eintrag der Familie, API-Index 4) | ja (4. Eintrag, API-Index 3) |
| Version | `4` | `archive-2026-06-14-713629b` |
| Dateien (Eigentümersicht), Größe + MD5 = lokal | 31/31 | 4/4 |
| Anonyme Sicht | `restricted`, 0 Dateien sichtbar | `open`, 4 Dateien sichtbar |
| Lizenz | keine (Daten, wie bisher) | MIT |
| Ältere veröffentlichte Versionen unverändert (`modified`) | ja (4/4) | ja (3/3) |

Hinweis zur Zählung: Die Full-Corpus-Familie umfasst jetzt 5 veröffentlichte Einträge (15360943, 17425738, 17828582, 18782190, 23470771). Die frühere Bezeichnung „Version 3“ für 18782190 entspricht dem API-Index 3 (0-basiert). Das Versionslabel `4` folgt dieser Zählung.

Ergebnisse: `local_only/reports/zenodo_fc_published_verify.json`, `local_only/reports/zenodo_sw_published_verify.json`.

**Abschlussstatus: PASS.** Keine sonstigen Zenodo-Änderungen. Die offene Bearbeitung der alten Version 17828582 bleibt unberührt. Keine lokalen Löschungen, keine Commits, Pushes oder Deployments. Offen für gesonderte Aufträge: lokale Bereinigung (Upload-ZIPs im Staging u. a.), Löschung der Token-Datei `%LOCALAPPDATA%\corapan_zenodo\token.dpapi` bzw. Widerruf des Tokens, optional die Aktualisierung der DOI-/Zitierhinweise in der Webapp.
