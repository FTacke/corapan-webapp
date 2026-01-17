# Pre-Commit Hooks

This directory contains optional Git pre-commit hooks to enforce repository standards.

## Available Hooks

### `pre-commit-check-statistics.sh`

**Purpose:** Prevents runtime-generated statistics files from being accidentally committed.

**What it checks:**
- Prevents staging of `static/img/statistics/*.png` files
- Prevents staging of `static/img/statistics/corpus_stats.json`

**Why:** These files are generated at runtime and should never be in Git.
See [Legacy Static Statistics](../../docs/operations/legacy_static_statistics.md) for context.

**Installation:**

```bash
# One-time setup
cp scripts/hooks/pre-commit-check-statistics.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Testing:**

```bash
# Try to commit a statistics file (will be blocked)
echo "test" > static/img/statistics/test.txt
git add static/img/statistics/test.txt
git commit -m "test"  # ❌ Will fail

# Unstage if blocked
git reset HEAD static/img/statistics/*
```

## Implementation Notes

- Hooks are **not** automatically installed (intentional, to respect user preference)
- Consider adding to CI/CD pipeline instead of local hooks
- PowerShell equivalent can be added for Windows developers

---

For more details on runtime statistics, see:
- `docs/operations/runtime_statistics_deploy.md`
- `docs/operations/legacy_static_statistics.md`
