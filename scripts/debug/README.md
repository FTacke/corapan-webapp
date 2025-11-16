# Debug & Troubleshooting Tools

This directory contains debug utilities and troubleshooting scripts for the CO.RA.PAN project.

## Scripts

### `debug_api_mapping.py`
**Purpose**: Debug API field mapping between BlackLab hits and canonical DataTables format

**Usage**:
```bash
python scripts/debug/debug_api_mapping.py
```

**What it does**:
- Makes test queries to BlackLab
- Shows how fields are mapped from BlackLab response to canonical format
- Helps troubleshoot missing or incorrectly mapped fields

**When to use**:
- DataTables shows missing or empty fields
- Investigating field mapping issues
- Validating `_hit_to_canonical()` logic

---

### `check_db.py`
**Purpose**: Check database structure and content

**Usage**:
```bash
python scripts/debug/check_db.py
```

**What it does**:
- Connects to SQLite database
- Shows table structure
- Validates data consistency
- Reports statistics

**When to use**:
- Investigating database issues
- Validating database schema
- Troubleshooting data inconsistencies

---

### `build_index_test.ps1`
**Purpose**: Test index building with a small subset of files

**Usage**:
```powershell
.\scripts\debug\build_index_test.ps1
```

**What it does**:
- Builds BlackLab index with only a few TSV files
- Useful for quick iteration when debugging index issues
- Faster than full index build

**When to use**:
- Debugging index build errors
- Testing BLF configuration changes
- Investigating file-specific indexing issues

**Referenced in**: `docs/blacklab_stack.md` (section 5: Debugging VEN TSV)

---

## General Troubleshooting Workflow

### BlackLab Index Issues

1. **Check TSV schema**: `python scripts/check_tsv_schema.py`
2. **Test with subset**: `.\scripts\debug\build_index_test.ps1`
3. **Review logs**: Check `data/blacklab_index/build.log`
4. **Validate BLF**: Review `config/blacklab/corapan-tsv.blf.yaml`

### API/Mapping Issues

1. **Debug mapping**: `python scripts/debug/debug_api_mapping.py`
2. **Check logs**: Review Flask logs for errors
3. **Test directly**: Use `curl` or Postman to test endpoints
4. **Validate response**: Compare BlackLab response to canonical format

### Database Issues

1. **Check structure**: `python scripts/debug/check_db.py`
2. **Review schema**: Check `src/app/models/`
3. **Test queries**: Use sqlite3 CLI to test queries directly

## Adding Debug Scripts

When creating new debug scripts:

1. **Name clearly**: Use `debug_*` or `check_*` prefix
2. **Add usage docs**: Include header comment with usage
3. **Keep simple**: One purpose per script
4. **Add to this README**: Document what it does and when to use it

## Related Documentation

- `docs/blacklab_stack.md` - BlackLab troubleshooting guide
- `docs/troubleshooting/` - General troubleshooting docs
- `scripts/README.md` - Main scripts documentation
