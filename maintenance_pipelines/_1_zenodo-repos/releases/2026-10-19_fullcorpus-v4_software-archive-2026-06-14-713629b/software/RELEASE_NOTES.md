# Release notes – CO.RA.PAN Web Application, archive snapshot `archive-2026-06-14-713629b`

Commit `713629bd3b85cf6739db4cb689314879074493bc` (branch `main`, 2026-06-14). Compared with `v1.1.0` (commit `b05d931…`, 2026-03-24): 19 commits, 2026-03-24 – 2026-06-14. Derived from `git log v1.1.0..713629b`; nothing below was run or re-tested for this snapshot.

## Version label

Release tags of the project follow `vX.Y.Z`; no tag exists after `v1.1.0` and none was created for this archive. The snapshot is therefore labelled with a dated archive label: `archive-2026-06-14-713629b` (commit date + short SHA). `app/pyproject.toml`, `app/package.json` and `app/CITATION.cff` inside the archive still state version `1.0.0` (they were not bumped at v1.1.0 either).

## Licence

Project code: MIT (`app/LICENSE`). The previous Zenodo versions of this record carried the licence field CC-BY-4.0; they remain unchanged. From this version on the Zenodo licence field matches the repository licence (MIT). Third-party components keep their own licences (see `README.md`).

## Three different states

1. This archive: the committed repository state `713629b`.
2. The annotation pipeline v3.2 that produced the transcripts of Full Corpus version 4: archived separately as provenance supplement inside the Full Corpus record (`CORAPAN_FullCorpus_v4_annotation-v3.2_provenance.zip`), not part of this software archive.
3. The production deployment: not verified; this archive does not claim to be the running state.

## Changes since v1.1.0 (grouped)

Application / UI (2026-03-24, committed after the `v1.1.0` tag was created the same day)
- Template harmonisation using canonical skeletons, centralised branding/layout, advanced-search and stats UI CSS/JS refactoring, audio player control and accessibility refactoring, removal of outdated UI texts, update of the citation year on the project citation page, removal of a legacy token shim, idempotent registration of Jinja context processors.

Operations / BlackLab
- 2026-03-25 – 2026-03-28: BlackLab configuration paths and production setup documentation refactored; strict canonical path validation and verification for BlackLab index operations; documentation of sync constraints and transport matrix.
- 2026-04-28: optional GoatCounter tracking support in the Flask configuration and templates (disabled unless `GOATCOUNTER_URL` is set).
- 2026-05-01/02: liveness (`/health`) and readiness (`/ready`) split into separate endpoints; both exempt from rate limiting.

Maintenance pipelines / tests
- 2026-06-14: unit tests for the transcript annotation and audit scripts (committed pipeline: `corapan-transcript-ann-v3.1`).

Documentation
- Production deploy/runtime documentation, change notes under `docs/changes/`, sync-lane documentation under `docs/rsync/`.

No breaking API changes were identified from the commit messages (not verified by a test run).

## Known gaps – please read

1. **Annotation pipeline v3.2 is not in this snapshot.** The transcripts of Full Corpus version 4 carry `pipeline_version = corapan-transcript-ann-v3.2` and `tense_rules_version = tense-v4-coprepan-compatible` (migration of 2026-06-14). The scripts that produced them were uncommitted working-tree changes and are deliberately **not** part of this archive; they are archived as a provenance supplement in the Full Corpus record (concept DOI 10.5281/zenodo.15360942, version 4).
2. Whether `713629b` is what runs in production is not verified here. The repository state equals `origin/main` as last fetched locally; success of the corresponding GitHub Actions run was not checked.
3. The snapshot contains the production server's IP address in deployment scripts and documentation (as does the public repository and previous archives). No credentials, tokens or private keys were found by a pattern scan (private-key blocks, GitHub/AWS/Slack tokens, passwords in connection URLs other than development defaults and placeholders).
