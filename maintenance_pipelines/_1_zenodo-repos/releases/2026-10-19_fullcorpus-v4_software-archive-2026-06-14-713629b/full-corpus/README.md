# CO.RA.PAN Full Corpus (Restricted) – Version 4

CO.RA.PAN (Corpus Radiofónico Panhispánico) is a corpus of spoken standard Spanish from radio news broadcasts of capital-city stations in almost all Spanish-speaking countries. This record holds the complete corpus: original audio and annotated transcripts.

**Access is restricted** (copyright and broadcasting rights). Access can be requested through Zenodo. Full recordings and transcripts must not be redistributed or reused; short audio–text extracts may be displayed for scientific quotation and text-and-data-mining within the limits of the legal provisions cited in the record description.

Related records (all versions share the concept DOIs):

| Record | Concept DOI |
|---|---|
| Full Corpus (this record) | 10.5281/zenodo.15360942 |
| Sample Corpus (public, JSON only) | 10.5281/zenodo.15378479 |
| Metadata (public, CC-BY 4.0) | 10.5281/zenodo.17843469 |
| Web Application and Code | 10.5281/zenodo.17834023 |

Previous version of this record: version 3, DOI 10.5281/zenodo.18782190 (2026-02-26). It remains valid and citable.

## Contents

| Item | Description |
|---|---|
| `<CODE>.zip` (25 files) | one package per country or region |
| `MANIFEST.csv` | one row per recording: package, sizes, SHA-256 of every audio and JSON member, annotation versions, SHA-256 of the previous (v3) JSON |
| `FILE_INVENTORY.json` | machine-readable list of packages with recording IDs |
| `SHA256SUMS` | SHA-256 of all files of this record |
| `RELEASE_NOTES.md` | changes against version 3 and known limitations |
| `CORAPAN_FullCorpus_v4_annotation-v3.2_provenance.zip` | **provenance supplement**: source code of annotation pipeline v3.2 and the tense-migration tools, run records, logs and library versions with which the version-4 transcripts were produced; no audio and no transcripts; see `PROVENANCE.md` inside |

Totals of the corpus packages: 25 packages, 146 recordings (146 MP3 + 146 JSON = 292 members), 1,488,019 annotated word entries, 6,983,407,386 bytes.

Package codes: ARG, ARG-CBA, ARG-CHU, ARG-SDE, BOL, CHL, COL, CRI, CUB, DOM, ECU, ESP, ESP-CAN, ESP-SEV, GTM, HND, MEX, NIC, PAN, PER, PRY, SLV, URY, USA, VEN.

## Structure of a package

```
<CODE>.zip
├── mp3-files/<recording_id>.mp3
└── json-transcripts/<recording_id>.json
```

The structure and file names are identical to version 3. `recording_id` has the form `YYYY-MM-DD_<CODE>_<station>` (for example `2023-08-10_ARG_Mitre`). Audio and transcript of one recording share the same `recording_id`; MANIFEST.csv lists every pair. ZIP members are stored in sorted order with a fixed timestamp (2026-01-01 00:00:00); MP3 members are stored uncompressed, JSON members are deflated.

## Transcript format

Each JSON file has top-level metadata (`file_id`, `filename`, `date`, `country_code`, `country_scope`, `city`, `radio`, `revision`, …), an `ann_meta` block (annotation versions, model, hashes, audit counters) and `segments`. Each segment has `utt_start_ms`, `utt_end_ms`, a speaker and a list of `words`. Each word entry has `token_id`, `sentence_id`, `utterance_id`, `start_ms`, `end_ms`, `text`, `norm`, `pos`, `lemma`, `dep`, `head_text`, `morph`; tense, voice and role information are stored in `morph` (for example `TenseRole`, `PastType`, `FutureType`, `VoiceType`).

Annotation of this version (identical in all 146 files; see MANIFEST.csv):

- schema `corapan-transcript-json/v3`, annotation format `corapan-ann/v3`
- pipeline `corapan-transcript-ann-v3.2`, tense rules `tense-v4-coprepan-compatible`
- automatic annotation with spaCy `es_dep_news_trf`

Token IDs (`token_id`) are stable across versions 3 and 4.

The pipeline v3.2 code was never part of a software release; it is documented in the provenance supplement. The web application software record (concept DOI 10.5281/zenodo.17834023, version `archive-2026-06-14-713629b`) contains the earlier committed pipeline v3.1.

## Integrity check

Linux/macOS/Git Bash: `sha256sum -c SHA256SUMS`. Windows PowerShell: `Get-FileHash -Algorithm SHA256 <file>` and compare with `SHA256SUMS`. MANIFEST.csv contains the SHA-256 of each member; after unpacking, `sha256sum` of `mp3-files/<id>.mp3` and `json-transcripts/<id>.json` must equal `audio_sha256` / `json_sha256`.

## Known limitations

See `RELEASE_NOTES.md`, section "Known limitations". In short: one recording (`2025-01-27_NIC_RCorp`) has an internal `file_id` that differs from its file name; the annotation is automatic and was not manually re-verified for this version; the v3.2 annotation is documented by the provenance supplement but not reproducible bit-for-bit; the transcripts are the project's archived local state and were not compared with the copies on the production web server.

## Citation

Cite the DOI of the version used, or the concept DOI 10.5281/zenodo.15360942 for the whole record family. Author: Felix Tacke, Philipps-Universität Marburg (ORCID 0000-0002-6716-7839). Further information: https://hispanistica.com/projects/corapan/ · Web application: https://corapan.hispanistica.com/
