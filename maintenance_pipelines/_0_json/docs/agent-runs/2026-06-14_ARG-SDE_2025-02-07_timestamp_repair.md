# ARG-SDE Timestamp Repair

Date: 2026-06-14

## File

`media/transcripts/ARG-SDE/2025-02-07_ARG-SDE_RPanorama.json`

## Target Token

- Segment: 81
- Word index: 15
- Text: `con`
- Token ID: `ARGSDE85c6d3522`
- Old `start_ms`: 354840
- Old `end_ms`: 354450
- New `start_ms`: 354840
- New `end_ms`: 354840

## Neighbor Tokens Before

| word_index | text | token_id | start_ms | end_ms |
| ---: | --- | --- | ---: | ---: |
| 13 | `con,` | `ARGSDEc02d75126` | 353720 | 353850 |
| 14 | `con,` | `ARGSDEf3b00e4c0` | 354450 | 354840 |
| 15 | `con` | `ARGSDE85c6d3522` | 354840 | 354450 |
| 16 | `una` | `ARGSDE24b6af84e` | 354450 | 354450 |
| 17 | `hay` | `ARGSDEb0fff92ab` | 354450 | 354450 |

## Neighbor Tokens After

| word_index | text | token_id | start_ms | end_ms |
| ---: | --- | --- | ---: | ---: |
| 13 | `con,` | `ARGSDEc02d75126` | 353720 | 353850 |
| 14 | `con,` | `ARGSDEf3b00e4c0` | 354450 | 354840 |
| 15 | `con` | `ARGSDE85c6d3522` | 354840 | 354840 |
| 16 | `una` | `ARGSDE24b6af84e` | 354450 | 354450 |
| 17 | `hay` | `ARGSDEb0fff92ab` | 354450 | 354450 |

## Reason

The target token had `start_ms > end_ms`. The next token exists, but starts at `354450`, earlier than the target `start_ms`, so it is not usable as a later endpoint. The repair therefore sets `end_ms` to `354840`, equal to `start_ms`, creating a minimal valid zero-length interval while changing only one timestamp field. No token IDs, text, lemma, POS, dependency, or morphology fields were changed.

## Backup

`maintenance_pipelines/_0_json/backups/manual-repairs/20260614T081443Z/ARG-SDE/2025-02-07_ARG-SDE_RPanorama.before_timestamp_repair.json`

## Token-ID Snapshot

`maintenance_pipelines/_0_json/backups/manual-repairs/20260614T081443Z/ARG-SDE/2025-02-07_ARG-SDE_RPanorama.token_ids.before.json`

## Confirmation

Token ID unchanged: `True`
