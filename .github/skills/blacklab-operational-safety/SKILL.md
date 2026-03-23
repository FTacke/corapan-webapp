---
name: blacklab-operational-safety
description: "Use when diagnosing BlackLab hits failures, validating BlackLab mount/index state, or changing BlackLab rebuild/start/health guardrails in corapan-webapp."
---

# BlackLab Operational Safety Skill

## Use This Skill When

Use this skill whenever a task involves any of the following:
- BlackLab hits returning HTTP 500 or inconsistent results
- BlackLab rebuild or startup guardrails
- active index path, mount, or corpus validation
- deciding whether a failure is caused by app logic, BLF/config, or active-index corruption
- validating whether BlackLab is actually safe to serve after rebuild/start

## Do Not Use When

Do not use this skill for:
- generic backend work with no BlackLab runtime impact
- documentation-only cleanup that does not change operational guidance
- historical notes that do not affect current BlackLab behavior

## Required Check Order

1. inspect live BlackLab behavior if observable
2. run or inspect a real hits query, not only `/blacklab-server/`
3. inspect container logs for `InvalidIndex`, `CorruptIndexException`, file mismatch, or mount errors
4. inspect canonical dev compose/start/build sources
5. inspect active BLF/config and only then inspect app CQL/backend logic

## Hard Rules

- do not rebuild or replace the active index while `blacklab-server-v3` is serving it
- do not treat root HTTP readiness as proof that the mounted index is healthy
- do not assume a valid build log proves the active index is readable
- do not blame CQL or field logic before checking logs and active mounts when valid hits return 500
- do not treat legacy path trees as equal to `data/blacklab/{index,export,backups,quarantine}` without explicit reclassification

## Canonical Local BlackLab Model

Workspace root:
- `CORAPAN/`

Canonical local BlackLab dev tree:
- `data/blacklab/index`
- `data/blacklab/export`
- `data/blacklab/backups`
- `data/blacklab/quarantine`

Legacy or suspicious local alternatives:
- `app/data`
- `app/runtime`
- `data/blacklab_index`
- `data/blacklab_export`

## Required Output

State explicitly:
- whether the failure is classified as index/mount/runtime, config/BLF, export/input, or app/backend logic
- which path is active
- which competing paths are legacy, dangerous, or redundant
- whether a real hits query succeeded or failed
- what evidence was stronger than generic readiness