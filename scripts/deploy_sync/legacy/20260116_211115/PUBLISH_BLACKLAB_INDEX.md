# BlackLab Index Publishing

## Overview

`publish_blacklab_index.ps1` automates the complete workflow for deploying a locally-built BlackLab index to production:

1. **Preflight checks** (local + remote)
2. **Binary-safe upload** (tar+ssh streaming)
3. **Critical validation gate** (temporary container test)
4. **Atomic swap** (with automatic backup)
5. **Production sanity check** (with rollback instructions)

## Prerequisites

**Local machine (Windows):**
- PowerShell 5.1 or later
- SSH client (OpenSSH for Windows)
- `tar` command (Git Bash, WSL, or Windows tar)
- Optional: `scp` for fallback

**Remote server (Linux):**
- SSH access with key-based auth
- Docker installed and running
- Standard tools: `tar`, `curl`, `find`, `du`

## Usage

### Basic Usage

```powershell
# Standard deployment (uses data/blacklab_index.new)
.\scripts\deploy_sync\publish_blacklab_index.ps1
```

### Dry-Run Mode

```powershell
# Test without making changes
.\scripts\deploy_sync\publish_blacklab_index.ps1 -DryRun
```

### Backup Retention

```powershell
# Keep only the latest 2 backups (default)
.\scripts\deploy_sync\publish_blacklab_index.ps1

# Keep the latest 5 backups
.\scripts\deploy_sync\publish_blacklab_index.ps1 -KeepBackups 5

# Disable automatic cleanup (keep all backups)
.\scripts\deploy_sync\publish_blacklab_index.ps1 -NoBackupCleanup
```

### Custom Configuration

```powershell
# Custom host and user
.\scripts\deploy_sync\publish_blacklab_index.ps1 -Host 192.168.1.100 -User admin

# Custom SSH port
.\scripts\deploy_sync\publish_blacklab_index.ps1 -Port 2222

# Custom remote paths
.\scripts\deploy_sync\publish_blacklab_index.ps1 -DataDir /opt/corapan/data -ConfigDir /opt/corapan/config
```

## Workflow Details

### Production-Only Validation & Swap Policy

⚠️ **Production is NOT allowed to build indices.** This is enforced (Variante B).

The correct workflow is:

| Step | Location | Allowed |
|------|----------|---------|
| 1. Export corpus data | Local (dev machine) | ✓ |
| 2. **Build index** | Local (dev machine) | ✓ |
| 3. **Build on prod** | Production server | ✗ **DISABLED** |
| 4. Validate index | Production server (temp) | ✓ (read-only) |
| 5. Atomic swap | Production server | ✓ |
| 6. Backup & cleanup | Production server | ✓ |

**Why?** Building requires CPU/memory. Production is for serving only. This separation ensures:
- Build stability is controlled locally
- Production resources are reserved for users
- No index format drift between build environments
- Reproducible deployments

See [scripts/blacklab/build_blacklab_index_prod.sh](../blacklab/build_blacklab_index_prod.sh) — this script will **exit immediately with an error** if ever run on production.

### Step 1: Local Preflight
- Verifies `data/blacklab_index.new` exists
- Counts files (minimum: 10)
- Calculates size (minimum: 50 MB)
- Ensures index is complete before upload

### Step 2: Remote Connectivity
- Tests SSH connection
- Verifies remote paths exist
- Checks required tools: `docker`, `curl`, `tar`

### Step 3: Upload (Binary-Safe)
**Primary method:** tar+ssh streaming
```bash
tar -cf - -C <local> . | ssh <remote> "tar -xpf - -C <remote_new>"
```
- No temporary files
- No memory issues
- Binary-safe (no encoding problems)
- Progress visible in real-time

**Fallback:** scp (if tar unavailable)
```bash
scp -O -r <local> <remote>
```

### Step 4: Remote Verification
- Counts uploaded files
- Verifies size in bytes (precise)
- Ensures upload completed successfully

### Step 5: Validation Gate (CRITICAL)
**This step must pass before swap occurs.**

Starts temporary container `bl-validate-new` on port 18092:
```bash
docker run --name bl-validate-new -p 127.0.0.1:18092:8080 \
  -v <new_index>:/data/index/corapan:ro \
  -v <config>:/etc/blacklab:ro \
  <blacklab_image>
```

Validates:
- ✓ Server responds
- ✓ Corpora endpoint returns valid JSON
- ✓ Corpus "corapan" exists
- ✓ Index is not empty

**If validation fails:** Container is stopped, script exits with code 2, NO SWAP occurs.

### Step 6: Atomic Swap
```bash
mv <active> <backup_timestamp>
mv <new> <active>
```
- Old index backed up with timestamp
- New index becomes active
- Atomic operation (no downtime)

### Step 7: Production Sanity Check
Tests production endpoint (port 8081):
- ✓ Server responds
- ✓ Corpus "corapan" available
- ✓ Document/token counts visible

**If sanity fails:** Prints rollback command, exits with code 4.

### Step 8: Backup Retention Cleanup
Runs automatically after successful deployment (when both swap and sanity checks pass):
- Lists all `blacklab_index.bak_*` backups
- Sorts by modification time
- Keeps the latest `$KeepBackups` backups (default: 2)
- Removes older backups safely

**Skipped if:**
- `-NoBackupCleanup` flag is set
- `-DryRun` mode (shows what would be deleted)
- Deployment failed before this step

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - deployment completed |
| 1 | General error (preflight, upload, verify) |
| 2 | Validation failed (index not usable) |
| 3 | Swap failed (critical) |
| 4 | Production sanity check failed |

## Rollback

If deployment succeeds but issues appear later:

```bash
ssh root@137.248.186.51
mv /srv/webapps/corapan/data/blacklab_index \
   /srv/webapps/corapan/data/blacklab_index.bad_$(date +%s)
mv /srv/webapps/corapan/data/blacklab_index.bak_<timestamp> \
   /srv/webapps/corapan/data/blacklab_index
```

The rollback command is printed at the end of each successful deployment.

## Backup Retention Policy

By default, **only the latest 2 backups are retained** on the production server. Older backups are automatically deleted after a successful deployment to prevent unbounded disk usage.

### Behavior

- **When:** Cleanup runs automatically **after a successful deployment** and production sanity check passes
- **What:** Only `${DataDir}/blacklab_index.bak_*` directories are affected
- **How many:** By default, keeps the 2 most recent backups by modification time
- **When disabled:** Use `-NoBackupCleanup` flag to prevent automatic deletion

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-KeepBackups` | int | `2` | Number of backups to retain |
| `-NoBackupCleanup` | switch | off | Disable automatic backup cleanup |

### Examples

```powershell
# Keep latest 5 backups instead of 2
.\scripts\deploy_sync\publish_blacklab_index.ps1 -KeepBackups 5

# Keep all backups (manual cleanup required)
.\scripts\deploy_sync\publish_blacklab_index.ps1 -NoBackupCleanup

# Dry-run with custom retention
.\scripts\deploy_sync\publish_blacklab_index.ps1 -DryRun -KeepBackups 3
```

### Safe Removal

- Cleanup happens **only after:**
  - Atomic swap succeeded
  - Production sanity check passed (corpus verified)
- Cleanup is **skipped if:**
  - `-NoBackupCleanup` flag is set
  - `-DryRun` mode (no actual deletion)
  - Deployment did not complete successfully
- Backup deletion uses `rm -rf -- <path>` for safety (prevents glob expansion)

### Manual Cleanup

To manually remove old backups on the production server:

```bash
ssh root@137.248.186.51
cd /srv/webapps/corapan/data

# Find all backups sorted by modification time
find . -maxdepth 1 -type d -name 'blacklab_index.bak_*' -printf '%T@ %p\n' | sort -n

# Remove backups older than 30 days
find . -maxdepth 1 -type d -name 'blacklab_index.bak_*' -mtime +30 -exec rm -rf {} \;
```

## Troubleshooting

### "tar command not found"
- Install Git Bash (includes tar)
- Enable WSL and use Linux tar
- Use Windows 10+ built-in tar

### "SSH connection failed"
- Verify SSH key authentication works: `ssh root@137.248.186.51`
- Check firewall rules
- Verify correct hostname/IP

### "Remote tools missing"
Server needs `docker`, `curl`, `tar`. Install:
```bash
apt-get update && apt-get install -y docker.io curl tar
```

### "Validation failed: corpora empty"
- Check BlackLab config at `/srv/webapps/corapan/app/config/blacklab`
- Verify index structure in `blacklab_index.new`
- Test locally first with validation container

### Upload very slow
- tar+ssh streaming is fastest
- Check network bandwidth
- Consider compression: `tar -czf` (but increases CPU)

## Configuration

Edit script header to change defaults:

```powershell
$BLACKLAB_IMAGE = "instituutnederlandsetaal/blacklab@sha256:..."
$VALIDATE_PORT = 18092
$PROD_PORT = 8081
$MIN_FILES = 10
$MIN_SIZE_MB = 50
```

## Security Notes

- Uses SSH key-based authentication (no passwords)
- Validates index before touching production
- Always creates backup before swap
- Atomic operations minimize downtime risk
- Read-only mounts for validation

## Related Scripts

- `scripts/blacklab/build_blacklab_index.ps1` - Build index locally
- `scripts/start_blacklab_docker_v3.ps1` - Start local BlackLab server
- `LOKAL/_1_blacklab/blacklab_export.py` - Export corpus to TSV

## Example Complete Workflow

```powershell
# 1. Export corpus data
python LOKAL/_1_blacklab/blacklab_export.py

# 2. Build index locally (with staging flag)
$env:BLACKLAB_IMAGE = "instituutnederlandsetaal/blacklab@sha256:3753dbce4fee11f8706b63c5b94bf06eac9d3843c75bf2eef6412ff47208c2e7"
.\scripts\blacklab\build_blacklab_index.ps1 -Activate:$false -Force

# 3. Validate locally (optional)
docker run --rm -p 127.0.0.1:18081:8080 \
  -v "C:\dev\corapan-webapp\data\blacklab_index.new:/data/index/corapan:ro" \
  -v "C:\dev\corapan-webapp\config\blacklab:/etc/blacklab:ro" \
  instituutnederlandsetaal/blacklab@sha256:...

# 4. Test local endpoint
Invoke-WebRequest http://127.0.0.1:18081/blacklab-server/corpora/?outputformat=json

# 5. Publish to production
.\scripts\deploy_sync\publish_blacklab_index.ps1

# 6. Test production
Invoke-WebRequest https://corapan.online.uni-marburg.de/blacklab-server/corpora/?outputformat=json
```

## Technical Improvements Over Original

1. **Binary-safe upload:** Uses tar streaming instead of `Get-Content -Raw`
2. **No wildcards:** scp fallback copies entire directory
3. **Robust size check:** Uses bytes (`du -sb`) instead of parsing `M/G/K`
4. **Remote prerequisite checks:** Validates docker/curl/tar availability
5. **Safe container ID:** Handles short/malformed IDs without crashes
6. **Enhanced validation:** Checks both "corpora" key and "corapan" corpus
7. **Clear exit codes:** Distinguishes between error types
8. **Comprehensive logging:** Color-coded progress with detailed messages

## Maintenance

- Update `$BLACKLAB_IMAGE` when new BlackLab version deployed
- Adjust `$MIN_FILES` / `$MIN_SIZE_MB` if corpus size changes significantly
- Review backup retention policy on production server
- Test dry-run mode before major changes

---

Last updated: 2026-01-16
