# CO.RA.PAN Web Application – archive snapshot `archive-2026-06-14-713629b`

Version label: `archive-2026-06-14-713629b` (dated archive label: the date of the commit and its short SHA). The project's release tags follow `vX.Y.Z` (`v1.0.0`, `v1.0.1`, `v1.1.0`); no tag exists for this commit and none was created, so a dated label is used instead of a release number.

Source snapshot of the CO.RA.PAN web application (Corpus Radiofónico Panhispánico), taken from the committed Git state

- repository: https://github.com/FTacke/corapan-webapp
- branch: `main`
- commit: `713629bd3b85cf6739db4cb689314879074493bc` (committed 2026-06-14)
- previous Zenodo version of this record: `v1.1.0` (tag `v1.1.0`, commit `b05d931`, 2026-03-24), DOI 10.5281/zenodo.19202684
- concept DOI of all versions: 10.5281/zenodo.17834023

The archive is the output of `git archive` for exactly that commit, with the exclusions listed below. It is reproducible: the same command yields a byte-identical file (SHA-256 in `SHA256SUMS`; the commit SHA is also stored as the ZIP comment).

## Contents

`corapan-webapp-713629b.zip` (top-level folder `corapan-webapp-713629b/`):

- `app/` – Flask application (code, templates, static assets, tests, Dockerfile, production compose file, deploy scripts, requirements and lockfiles, configuration templates without secrets, `LICENSE`, `CITATION.cff`, `CHANGELOG.md`)
- `maintenance_pipelines/` – corpus processing tools: JSON preprocessing and annotation (`_0_json`), MP3 preparation/splitting (`_0_mp3`), BlackLab export, metadata export, Zenodo packaging and deploy scripts
- `docs/`, `.github/` – maintainer documentation, CI/deploy workflows
- `scripts/`, `docker-compose.dev-postgres.yml` – development entry points

## Not contained

- Git history (`.git`); it remains in the GitHub repository.
- Any corpus data: audio, transcripts, databases, BlackLab indexes (the corpus is archived separately, see the Full Corpus record 10.5281/zenodo.15360942).
- Operator secrets (`passwords.env` is only present as a template).
- Third-party binaries and local state, excluded from this snapshot: `app/tools/cwrsync/bin/` (cwRsync/Cygwin binaries), `maintenance_pipelines/bfg.jar`, `maintenance_pipelines/_0_json/backups/` (contains an editor log), `maintenance_pipelines/_0_json/state/` (annotation state database).
- Uncommitted working-tree changes. **Important:** the annotation pipeline version `corapan-transcript-ann-v3.2` that produced the current Full Corpus transcripts (tense rules `tense-v4-coprepan-compatible`) was, at the time of this snapshot, **not yet committed** in the repository. This snapshot therefore contains the committed pipeline version `corapan-transcript-ann-v3.1` / `tense-v3-corapan-adapter-v1` in `maintenance_pipelines/_0_json/02_annotate_transcripts_v3.py`. The v3.2 sources and run records are archived as provenance supplement `CORAPAN_FullCorpus_v4_annotation-v3.2_provenance.zip` in Full Corpus version 4 (concept DOI 10.5281/zenodo.15360942). See `RELEASE_NOTES.md`.

## Relationship to the live service

The service at https://corapan.hispanistica.com/ is deployed automatically from pushes to `main` by the GitHub Actions workflow in `.github/workflows/deploy.yml`. This snapshot is the repository state, not a proof of what is running at any given moment.

## Licence and citation

Software licence of the project code: **MIT** (`app/LICENSE`, © 2025–2026 Felix Tacke). Earlier versions of this Zenodo record were published with the licence field CC-BY-4.0; those versions are not changed. The research data (Full Corpus) are **not** covered by this licence and are restricted.

Third-party components included in the archive keep their own licences (as stated in their file headers or upstream):

| Path | Component | Licence |
|---|---|---|
| `app/static/vendor/jquery-3.7.1.min.js` | jQuery 3.7.1 | MIT (jquery.org/license) |
| `app/static/vendor/jquery.dataTables.min.js` | DataTables 1.13.7 | MIT (datatables.net/license) |
| `app/static/vendor/select2.min.js` | Select2 4.1.0-rc.0 | MIT |
| `app/static/vendor/htmx-1.9.10.min.js`, `htmx.min.js` | htmx | upstream licence of htmx (0BSD / BSD-2-Clause, depending on version) |
| `app/static/fonts/MaterialSymbolsRounded.woff2` | Material Symbols (Google) | Apache-2.0 |
| `app/tools/cwrsync/` (text and configuration files only; binaries excluded) | cwRsync / rsync documentation | rsync: GPL-3.0; cwRsync: see `README.cwrsync.txt` |

JavaScript test dependencies are only referenced (`app/package.json`, `package-lock.json`), not included.
Cite via the DOI shown on Zenodo for this version, or the concept DOI 10.5281/zenodo.17834023; see `app/CITATION.cff`.

## Integrity

`sha256sum -c SHA256SUMS` (Linux/macOS/Git Bash) or `Get-FileHash -Algorithm SHA256` (PowerShell).
