# Zenodo guide – CO.RA.PAN Legacy: review and publish the prepared drafts

Status: both new-version **drafts were created and filled via the Zenodo API on 2026-10-19 and are NOT published.** Publishing is your decision and is done by you in the web interface.

| Record family | Draft | Version | Files | Access / licence |
|---|---|---|---|---|
| Full Corpus (concept DOI 10.5281/zenodo.15360942) | https://zenodo.org/deposit/23470771 | `4` | 31: 25 ZIPs + provenance supplement + README.md, RELEASE_NOTES.md, MANIFEST.csv, FILE_INVENTORY.json, SHA256SUMS | **Restricted**, access conditions taken over from version 3; no licence field |
| Software (concept DOI 10.5281/zenodo.17834023) | https://zenodo.org/deposit/23470763 | `archive-2026-06-14-713629b` | 4: corapan-webapp-713629b.zip + README.md, RELEASE_NOTES.md, SHA256SUMS | Open, MIT |

The local files in `full-corpus/` and `software/` are exactly what is in the drafts (checked by file count, size and MD5 against Zenodo). `zenodo_metadata/` holds the earlier templates; the metadata actually applied is in `local_only/reports/zenodo_*_metadata_to_apply.json`.

## 1. Review (both drafts)

1. Open the draft link while logged in to Zenodo.
2. Check title, version, publication date (set to 2026-10-19 – change it to the actual publication day if you prefer), description, creators, keywords, related identifiers.
3. Full Corpus: access must show **Restricted**; access conditions present; the file list shows 31 files, no file of version 3 is left in the draft.
4. Software: access **Open**, licence **MIT**; 4 files.
5. Optional integrity check of the local copies: `sha256sum -c SHA256SUMS` in `full-corpus/` and `software/`.

## 2. Publish (only after your review)

Click **Publish** in each draft. A published version cannot be removed; files can only be changed by publishing another version. Note the two new version DOIs (shown after publishing); the concept DOIs stay the same. Earlier versions keep their DOIs and files.

## 3. After publishing

1. Open both records once and confirm the file lists (the Full Corpus files are visible to you as owner).
2. Optional: correct the Metadata record (10.5281/zenodo.17843469) description if it references the Full Corpus generically – a metadata-only edit, no new version needed.
3. Update the DOI/citation text of the web application if it names a version DOI (not part of this run).
4. Only then, and only after your separate approval, remove the local upload ZIPs in `zenodo_upload_ready/full-corpus/`. Keep `local_only/` (evidence) until no longer needed.

## Notes

- One unpublished new-version draft per record family is allowed by Zenodo; re-running the preparation reuses these drafts.
- An older Full Corpus version (deposition 17828582, published 2025-12-05) has an open, unsaved edit session since 2026-02-23 (state `inprogress`). It was not touched. You may want to discard that edit in the web interface.
