# Local Workflow Boundary

This directory is now the versioned workflow truth for the root repository under `CORAPAN/`.

Canonical repository model after the root lift:

- `CORAPAN/.github/workflows`
  - active versioned CI/deploy truth
  - authoritative for real push/deploy behavior from the root repo
- `CORAPAN/app/`
  - versioned application/deploy implementation

Historical workflow files that lived under the former `webapp/.github/workflows` path are no longer the governing source.