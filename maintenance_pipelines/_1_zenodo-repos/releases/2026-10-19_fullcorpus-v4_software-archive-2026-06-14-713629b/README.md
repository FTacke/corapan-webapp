# Release record – Zenodo publication of 2026-10-19

Compact record of the Zenodo release prepared and published on 2026-10-19. The upload staging (`legacy/corapan_zenodo_staging`) was removed after verification; the large ZIP packages are not kept here.

| Record | Published version |
|---|---|
| CO.RA.PAN Full Corpus (Restricted), version 4 | https://doi.org/10.5281/zenodo.23470771 (concept DOI 10.5281/zenodo.15360942) |
| CO.RA.PAN Web Application, `archive-2026-06-14-713629b` | https://doi.org/10.5281/zenodo.23470763 (concept DOI 10.5281/zenodo.17834023) |

Contents:

- `full-corpus/` – the uploaded README, RELEASE_NOTES, MANIFEST.csv, FILE_INVENTORY.json, SHA256SUMS and the provenance supplement (the 25 country ZIPs are on Zenodo only; their SHA-256 are in `SHA256SUMS` and `FILE_INVENTORY.json`)
- `software/` – the uploaded README, RELEASE_NOTES and SHA256SUMS (the archive itself is on Zenodo and reproducible with `git archive`, see README)
- `zenodo_metadata/` – the metadata applied to both records
- `local_reports/` – build, verification, old-ZIP inventory, deletion log, Zenodo draft/publish verification, cleanup plan and journal
- `local_scripts/` – the scripts used (packaging, verification, Zenodo API; they read the token only from the environment or a local DPAPI file, which has been deleted)
- `ZENODO_UPLOAD_GUIDE.md`, `README_STAGING.md` – documents of the staging phase (historical)

Run reports: `docs/agent-runs/2026-10-19_zenodo_archive_update_and_old_zip_cleanup.md`, `docs/agent-runs/2026-10-19_legacy-retention-integration-and-local-cleanup.md`.

`../zip_process.history_v3_2026-02-26.log` is the historical packaging log of Full Corpus version 3; `zenodo_full-corpus.py` no longer finds a resume state and would rebuild all packages on a new run.
