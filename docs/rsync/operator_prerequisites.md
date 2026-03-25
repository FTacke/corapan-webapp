# Operator Prerequisites

Local Windows operator prerequisites for the productive sync lanes:

- OpenSSH client available for direct SSH and `scp -O`
- repo-bundled cwRSync available under `app/tools/cwrsync/bin/`
- SSH access already validated from the real operator machine
- `CORAPAN_RUNTIME_ROOT` set for Data and Media lanes
- local BlackLab staging index present under `data/blacklab/quarantine/index.build` for BlackLab publish

Operator-specific SSH identity is not assumed to be the historical `marele` key.
Validate the real alias, host, and key path on the machine before changing scripts.