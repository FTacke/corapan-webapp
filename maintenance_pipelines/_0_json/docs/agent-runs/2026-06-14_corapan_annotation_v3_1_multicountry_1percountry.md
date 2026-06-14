# Corapan Annotation v3.1 Multi-Country Smoke, 1 File Per Country

Date: 2026-06-14

## 1. Goal

Controlled multi-country smoke test for the Corapan transcript annotation pipeline v3.1.

Scope:

- exactly one JSON transcript per country folder under `media/transcripts`
- real spaCy annotation required with `--require-spacy`
- no full-country or full-corpus run
- existing `token_id` values protected
- validation, audit, idempotence check, progress/state update, and pytest check

## 2. Selection Rule

Selection was deterministic:

- inspect all country folders under `media/transcripts`
- choose the smallest valid JSON file per country by file size
- for ARG, exclude the already-smoked `2023-08-12_ARG_Mitre.json` when another valid file exists
- create a backup and token-id snapshot before any write

## 3. Selected Files

| Country | File | Radio | Date | Segments | Words |
| --- | --- | --- | --- | ---: | ---: |
| ARG | `media/transcripts/ARG/2025-02-08_ARG_Mitre.json` | Radio Mitre | 2025-02-08 | 572 | 9869 |
| ARG-CBA | `media/transcripts/ARG-CBA/2025-06-24_ARG-CBA_RSuquia.json` | Radio Suquia | 2025-06-24 | 112 | 5147 |
| ARG-CHU | `media/transcripts/ARG-CHU/2025-06-25_ARG-CHU_RChubut.json` | Radio Chubut | 2025-06-25 | 99 | 8276 |
| ARG-SDE | `media/transcripts/ARG-SDE/2025-06-20_ARG-SDE_RPanorama.json` | Radio Panorama | 2025-06-20 | 165 | 5210 |
| BOL | `media/transcripts/BOL/2024-04-08_BOL_Erbol.json` | Radio Erbol | 2024-04-08 | 99 | 8285 |
| CHL | `media/transcripts/CHL/2023-10-06_CHL_ADN.json` | ADN | 2023-10-06 | 193 | 10520 |
| COL | `media/transcripts/COL/2023-12-29_COL_Caracol.json` | Caracol | 2023-12-29 | 151 | 9639 |
| CRI | `media/transcripts/CRI/2024-08-08_CRI_Monumental.json` | Radio Monumental | 2024-08-08 | 136 | 9782 |
| CUB | `media/transcripts/CUB/2024-05-16_CUB_Rebelde.json` | Radio Rebelde | 2024-05-16 | 135 | 9691 |
| DOM | `media/transcripts/DOM/2024-05-01_DOM_Z101.json` | Z101 | 2024-05-01 | 89 | 8374 |
| ECU | `media/transcripts/ECU/2024-08-02_ECU_RQuito.json` | Radio Quito | 2024-08-02 | 95 | 7289 |
| ESP | `media/transcripts/ESP/2024-12-18_ESP_CadenaSer.json` | Cadena Ser | 2024-12-18 | 233 | 11168 |
| ESP-CAN | `media/transcripts/ESP-CAN/2024-02-13_ESP-CAN_RCT.json` | Radio Club Tenerife | 2024-02-13 | 147 | 10902 |
| ESP-SEV | `media/transcripts/ESP-SEV/2024-02-22_ESP-SEV_RSev.json` | Radio Sevilla | 2024-02-22 | 212 | 11113 |
| GTM | `media/transcripts/GTM/2024-06-17_GTM_EmUnidas.json` | Emisoras Unidas | 2024-06-17 | 90 | 9651 |
| HND | `media/transcripts/HND/2024-01-16_HND_HRN.json` | HRN | 2024-01-16 | 160 | 8839 |
| MEX | `media/transcripts/MEX/2023-11-16_MEX_Formula.json` | Radio Formula | 2023-11-16 | 220 | 9497 |
| NIC | `media/transcripts/NIC/2025-02-10_NIC_RCorp.json` | Radio Corporacion | 2024-02-10 | 145 | 7382 |
| PAN | `media/transcripts/PAN/2024-05-08_PAN_RPanama.json` | Radio Panama | 2024-05-08 | 98 | 8395 |
| PER | `media/transcripts/PER/2023-10-09_PER_RPP.json` | RPP | 2023-10-09 | 263 | 14109 |
| PRY | `media/transcripts/PRY/2024-04-09_PRY_abc.json` | Radio ABC | 2024-04-09 | 196 | 8512 |
| SLV | `media/transcripts/SLV/2024-11-04_SLV_YSKL.json` | Radio YSKL | 2024-11-04 | 165 | 8413 |
| URY | `media/transcripts/URY/2023-08-10_URY_Sarandi.json` | Radio Sarandi | 2023-08-10 | 242 | 14488 |
| USA | `media/transcripts/USA/2025-04-16_USA_Univision.json` | Univision | 2025-04-16 | 207 | 8900 |
| VEN | `media/transcripts/VEN/2022-01-18_VEN_RCR.json` | Radio Caracas Radio | 2022-01-18 | 63 | 9401 |

## 4. Backup Path

Backup root:

`maintenance_pipelines/_0_json/backups/multicountry-smoke/20260614T072618Z`

Manifest:

`maintenance_pipelines/_0_json/backups/multicountry-smoke/20260614T072618Z/selection_manifest.json`

Each selected file has:

- original JSON backup under `<backup_root>/<country>/<filename>.json`
- token-id snapshot under `<backup_root>/<country>/<filename>.token_ids.before.json`

## 5. Commands

Annotation pattern, executed once per selected file:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --file <selected_file> --force --require-spacy --check-corpus-token-ids --verbose
```

Validation pattern, executed once per selected file:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --file <selected_file> --validate-only --require-spacy --verbose
```

Combined audit:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\audit_transcript_annotation_quality.py --file <selected_file> ... --out maintenance_pipelines\_0_json\docs\agent-runs\audits\2026-06-14_multicountry_1percountry_annotation_audit_spacy_real.md --json-out maintenance_pipelines\_0_json\docs\agent-runs\audits\2026-06-14_multicountry_1percountry_annotation_audit_spacy_real.json
```

Idempotence pattern, executed once per selected file:

```powershell
.venv\Scripts\python.exe maintenance_pipelines\_0_json\02_annotate_transcripts_v3.py --file <selected_file> --require-spacy --verbose
```

Tests:

```powershell
.venv\Scripts\python.exe -m pytest maintenance_pipelines\_0_json\tests -q
```

## 6. Result Per File

| Country | Process | Validation | Audit | Existing IDs changed | Duplicate IDs | Missing IDs | Legacy tense fields | spaCy | Idempotence |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| ARG | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| ARG-CBA | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| ARG-CHU | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| ARG-SDE | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| BOL | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| CHL | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| COL | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| CRI | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| CUB | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| DOM | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| ECU | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| ESP | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| ESP-CAN | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| ESP-SEV | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| GTM | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| HND | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| MEX | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| NIC | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| PAN | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| PER | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| PRY | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| SLV | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| URY | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| USA | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |
| VEN | processed | passed | GREEN | 0 | 0 | 0 | 0 | 3.8.14, es_dep_news_trf, model | skipped up-to-date |

Audit artifacts:

- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_annotation_audit_spacy_real.md`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_annotation_audit_spacy_real.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_token_id_check.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_idempotence_results.json`
- `maintenance_pipelines/_0_json/docs/agent-runs/audits/2026-06-14_multicountry_1percountry_annotation_run_results.json`

## 7. Aggregated Summary

| Metric | Value |
| --- | ---: |
| Countries | 25 |
| Files | 25 |
| Total words | 232852 |
| GREEN audits | 25 |
| YELLOW audits | 0 |
| RED audits | 0 |
| Existing token IDs changed | 0 |
| Duplicate token IDs | 0 |
| Missing token IDs | 0 |
| Legacy `past_type` / `future_type` fields | 0 |
| Files idempotent | 25 |

The final state database contains updated v3.1 rows and no recorded existing-token-id changes for this run. Progress JSON/JSONL were updated under `maintenance_pipelines/_0_json/logs`.

## 8. Test Result

```text
6 passed in 1.44s
```

## 9. Rest Problems

The first attempt exposed a transcript-structure edge case: some files contain a trailing segment without a `words` list. The failing ARG file was restored from its backup before continuing. The annotator now normalizes missing or non-list `segment.words` to an empty list during transcript preparation, preserving the Corapan segment structure while satisfying validation. After this fix, all 25 selected country files processed, validated, audited GREEN, and skipped on the idempotence pass.

No `.tmp` files were left under `maintenance_pipelines/_0_json`.

## 10. Recommendation

The next staged run can safely be a larger but still bounded sample, for example `--country <COUNTRY> --limit 3` or `--limit 5` with `--require-spacy --check-corpus-token-ids`, followed by the same validation, audit, and idempotence checks. Do not start a full-corpus annotation until one more bounded multi-country batch has been reviewed.
