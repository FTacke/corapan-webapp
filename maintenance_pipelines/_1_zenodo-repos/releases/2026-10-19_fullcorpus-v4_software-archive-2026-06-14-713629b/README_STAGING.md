# corapan_zenodo_staging

Staging for the Zenodo update of Legacy CO.RA.PAN (prepared 2026-10-19). Not a runtime directory, not part of Git.

- `zenodo_upload_ready/` – everything to upload manually (see `ZENODO_UPLOAD_GUIDE.md`)
- `local_only/` – build/verification scripts, reports (old-ZIP inventory, deletion log, verification results) and a provenance snapshot of uncommitted pipeline sources. Do not upload.

Canonical run report: `legacy/corapan/docs/agent-runs/2026-10-19_zenodo_archive_update_and_old_zip_cleanup.md`.
Remove this directory only after the Zenodo versions are published and checked (guide, section 4).
