# Release notes – Full Corpus version 4 (against version 3, 2026-02-26)

All statements below were checked by comparing SHA-256 checksums or field-by-field content of the files in this record with the files of version 3, unless marked *(reported)*.

## What is unchanged

- **Recordings and identities:** the same 146 recordings in the same 25 packages with the same member names. No recording was added or removed.
- **Audio:** all 146 MP3 files are byte-identical to version 3 (SHA-256).
- **Token identity and timing:** for all 1,488,019 word entries, `token_id`, `text` and `start_ms` are identical to version 3; `end_ms` is identical except for one token (see below).
- **Segment structure:** segment boundaries, speaker codes and the number of word entries per file are identical to version 3.
- Package structure (`mp3-files/`, `json-transcripts/`) and file names.

## What changed

All 146 JSON transcripts differ from version 3 (SHA-256 differs for every file). The linguistic annotation was regenerated with annotation pipeline `corapan-transcript-ann-v3.2` (spaCy `es_dep_news_trf`) and rule-based tense labelling `tense-v4-coprepan-compatible` (2026-06-14).

Number of word entries (out of 1,488,019) whose value differs from version 3:

| Field | Differs |
|---|---:|
| `dep` (dependency relation) | 187,380 |
| `head_text` | 162,420 |
| `morph` (incl. tense/voice labels) | 88,974 |
| `pos` | 63,295 |
| `lemma` | 35,282 |
| `norm` | 12,817 |
| `end_ms` | 1 |

Further, 899 word entries that lacked `pos`/`lemma`/`dep`/`head_text` in version 3 have these fields in version 4, and 272 word entries carry a new `foreign` field. The transcripts now include an `ann_meta` block with pipeline, model, rule and validation versions and audit counters. Version 3 files carried no pipeline version.

Tense/role labelling *(reported in the project's internal run documentation, not independently re-run)*: the tense label scheme was aligned with the scheme of the sister corpus CO.PRE.PAN. Role values used by the earlier CO.RA.PAN scheme (`finite_past`, generic `auxiliary`, `compound_participle`, `future_infinitive`, `VoiceType=resultative`) no longer occur; the roles `finite_verb`, `copula_or_aux`, `aux_passive`, `aux_pass_chain`, `copula_resultative`, `aux_nonfinite_perfect`, `nonfinite_perfect`, `lexical_participle` are used instead, with the lemma stored in `VerbLemma`. **Consequence:** analyses that selected tokens by the old role labels cannot be repeated unchanged on version 4; use version 3 (its DOI remains valid) to reproduce earlier results.

One timing correction: in `2025-02-07_ARG-SDE_RPanorama` the token `ARGSDE85c6d3522` (`con`) had `end_ms` (354450) earlier than `start_ms` (354840); `end_ms` was set to 354840 *(reported in the project's repair note)*. This is the single `end_ms` difference to version 3.

## Not claimed

No improvement of annotation quality is claimed. The changes reflect a regenerated automatic annotation and a different tense label scheme; no new manual verification was performed for this release, and no accuracy evaluation was run.

## Known limitations

1. **Annotation provenance.** The scripts that produced pipeline v3.2 were never committed to the project repository and are not part of the software record (version `archive-2026-06-14-713629b`, which contains the committed pipeline v3.1). They are archived, with run records, logs and library versions, in the provenance supplement `CORAPAN_FullCorpus_v4_annotation-v3.2_provenance.zip` of this record. Limits stated there: the archived `02_annotate_transcripts_v3.py` was modified about five minutes after the tense-migration run and is therefore not proven identical to the executed version; hardware and numerical determinism of the transformer model were not recorded. The annotation is documented, not reproducible bit-for-bit. Pipeline and rule versions are recorded in every transcript (`ann_meta`).
2. **Source of the transcripts.** The transcripts are the project's local archive state of 2026-06-14. Whether the transcripts on the production web server are identical could not be verified; edits made exclusively on the server after the local copy was taken (the local editor log contains 38 entries from 2025-10-25 to 2025-10-30) are not covered by any check made for this release.
3. **Recording `2025-01-27_NIC_RCorp`.** The file name and the metadata field `date` say 2025-01-27, but the internal `file_id` and `filename` fields read `2024-01-27_NIC_RCorp`. This inconsistency exists in version 3 and in the public Metadata record (10.5281/zenodo.17843469, `file_id`); it was not changed so that identifiers stay stable.
4. **One transcript with a documented non-blocking warning** *(reported)*: `COL/2024-01-03_COL_Caracol.json` (internal validation: no hard-gate or validation errors).
5. The annotation is automatic. Lemma, POS, morphology, dependency and tense labels contain errors; the tense labelling is rule-based.
6. Version 3 transcripts and the version-3 packages remain available under DOI 10.5281/zenodo.18782190.

## Compatibility with the public records

- Metadata record 10.5281/zenodo.17843469 (v1.0.0, 2025-12-06): same 146 recordings and the same total of 1,488,019 word entries; its descriptive fields (date, station, duration, words transcribed) were not affected. Its annotation fields still describe the annotation generically (`corapan-ann/v3`).
- Sample Corpus 10.5281/zenodo.15378479: one sample JSON file, not changed by this release. Whether its annotation state corresponds to version 3 or 4 was not checked.
- Software record 10.5281/zenodo.17834023: see the separate record.
