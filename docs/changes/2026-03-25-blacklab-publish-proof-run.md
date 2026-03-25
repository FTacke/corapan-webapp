# 2026-03-25 BlackLab Publish Proof Run

## Summary

Executed a controlled BlackLab publish proof run with an explicit storage preflight and post-run production validation.

## What Changed

- added a documented publish proof run with host-space calculations, retry cleanup evidence, and production hits validation
- tightened BlackLab operational governance so publishes require space checks and explicit residue handling
- fixed repository-side validation bugs in the BlackLab publish script uncovered during the proof run
- fixed the repository-side retention script bug caused by invalid top-level `local` usage

## Operational Notes

- the production host had enough capacity for the observed publish run, but repeated retries created removable `index.upload_*` residues
- the proof run created one backup directory: `backups/index_2026-03-25_155317`
- production search served a healthy post-swap hits response after the proof run
- the deployed retention script on the production host still needs the repository fix deployed before automated retention can be trusted there

## Compatibility Notes

- no BlackLab layout migration was performed
- the canonical contracts remain:
  - DEV: `app/config/blacklab -> /etc/blacklab`
  - PROD: `/srv/webapps/corapan/app/app/config/blacklab -> /etc/blacklab`