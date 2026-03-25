# Transport Matrix

## Standard

- Data: `rsync-cwrsync`
- Media: `rsync-cwrsync`

Meaning:

- use repo-bundled `rsync.exe`
- use repo-bundled cwRSync `ssh.exe`
- preserve `--partial` for resumable large transfers

## Fallbacks

- common SSH fallback: `scp -O`
- compatibility fallback for existing Data and Media code: `tar-base64-legacy`
- limited fallback for BlackLab upload: `tar-ssh`

## Disallowed Assumptions

- generic Windows OpenSSH is equivalent to cwRSync transport
- `tar|ssh` is safe for large files by default
- host-key strict mode can be enabled without a bootstrap path