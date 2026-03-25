# 2026-03-25 BlackLab Config Path Cleanup Audit

## Summary

Audited BlackLab config-path references across scripts, docs, and governance after the production repair.

## What Changed

- corrected active publish-path defaults from the stale outer production path to `/srv/webapps/corapan/app/app/config/blacklab`
- aligned the BlackLab publish wrapper with the root-lifted production checkout contract
- updated central BlackLab and rsync docs to state the explicit DEV/PROD mount contract
- tightened governance to forbid returning to the stale outer path for cosmetic consistency alone

## Active Contract

- DEV: `app/config/blacklab -> /etc/blacklab`
- PROD: `/srv/webapps/corapan/app/app/config/blacklab -> /etc/blacklab`

## Notes

- the stale outer production path `/srv/webapps/corapan/app/config/blacklab` remains a documented dangerous legacy reference
- larger architecture-history documents may still contain historical root-lift notes and should be treated according to the cleanup audit, not as current mount truth