# Ad-hoc Test Scripts

This directory contains manual test scripts and integration tests that are not part of the automated pytest suite.

## Purpose

These scripts are used for:
- Manual validation of features
- Live testing against running services
- Integration testing that requires specific setup
- Exploratory testing and debugging
- One-off test scenarios

## Scripts

### Advanced Search Tests

- **`test_advanced_api_live_counts.py`** - Test live count functionality in Advanced Search
- **`test_advanced_hardening.py`** - Test hardening features (error handling, validation)
- **`test_advanced_search_live.py`** - Live integration test for Advanced Search
- **`test_advanced_search_real.py`** - Real-world test scenarios
- **`test_advanced_search.py`** - General Advanced Search tests
- **`test_advanced_ui_smoke.py`** - UI smoke tests

### Proxy & BlackLab Tests

- **`test_proxy.py`** - Test BlackLab Server proxy (`/bls/`)
- **`test_mock_bls_direct.py`** - Test with mocked BlackLab responses

### Authentication Tests

- **`test_auth_flow_simple.py`** - Test authentication flow (Python)
- **`test_auth_curl.sh`** - Test authentication flow (curl/shell)

### Integration Tests

- **`test_docmeta_integration.ps1`** - Document metadata integration test (PowerShell)

## Running Tests

### Python Tests

Most tests can be run directly:

```bash
# Run specific test
python scripts/testing/test_advanced_search_live.py

# Run with Python module mode
python -m scripts.testing.test_advanced_search_live
```

### PowerShell Tests

```powershell
# Run PowerShell test
.\scripts\testing\test_docmeta_integration.ps1
```

### Shell Tests

```bash
# Run shell test
bash scripts/testing/test_auth_curl.sh
```

## Prerequisites

Most tests require:
- Flask app running (locally or on server)
- BlackLab Server running (for BlackLab tests)
- Valid authentication credentials (for auth tests)

Check individual test files for specific requirements.

## Differences from Automated Tests

**These scripts** (`scripts/testing/`):
- May require manual setup
- May be exploratory or one-off
- May test against live services
- May not be reproducible
- May use mocks or fixtures
- Not run in CI

**Automated tests** (`tests/`):
- Run with pytest
- Designed for CI/CD
- Skip gracefully without dependencies
- No mocks for BlackLab (skip if unavailable)
- Reproducible and deterministic

## Migration to Pytest

If a test script here becomes stable and should be part of CI:

1. Refactor it to use pytest
2. Add skip logic for missing dependencies
3. Move to `tests/` directory
4. Update `tests/README.md`
5. Remove from this directory

## Adding New Test Scripts

When adding ad-hoc test scripts:

1. **Name with `test_*` prefix** for consistency
2. **Add header comment** explaining purpose and usage
3. **Document prerequisites** (services, credentials, etc.)
4. **Keep simple** - one scenario per script
5. **Update this README** with description

## Related Documentation

- `tests/README.md` - Automated pytest tests
- `docs/search_ui/search_ui_tests.md` - Manual test cases
- `scripts/README.md` - Main scripts documentation
- `scripts/debug/README.md` - Debug tools

## Notes

- These scripts are **not** maintained to the same standard as automated tests
- They may break as the codebase evolves
- They are useful for development but not for CI validation
- Consider migrating stable tests to pytest for better coverage
