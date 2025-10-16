# Python 3.11 Downgrade Branch - Notes

**Branch:** `feature/census-extraction-py311`
**Parent:** `feature/census-extraction`
**Date:** 2025-10-16
**Reason:** Test TrOCR installation (blocked by numpy 2.0.2 build failure on Python 3.13)

## What We're Doing

Testing Python 3.11 to resolve numpy/torch installation issues for TrOCR handwriting recognition.

## Changes Made

1. **pyproject.toml:** Changed `requires-python = ">=3.11"` to `">=3.11,<3.13"`
2. **Virtual environment:** Recreated with Python 3.11
3. **Dependencies:** Reinstalled with `uv sync`

## How to Revert

If this breaks things or doesn't help:

```bash
# Switch back to main branch
git checkout feature/census-extraction

# The old venv is still there on that branch
# Just delete this branch
git branch -D feature/census-extraction-py311
```

## How to Merge Back (If Successful)

If TrOCR works on Python 3.11:

```bash
# From feature/census-extraction-py311
git checkout feature/census-extraction
git merge feature/census-extraction-py311

# Resolve conflicts (likely just pyproject.toml Python version)
# Test that everything still works
# Delete the py311 branch
git branch -d feature/census-extraction-py311
```

## Risk Assessment

**Low Risk:**
- Only dependency/environment changes
- No code changes
- Easy to revert (just switch branches)

**What Could Break:**
- Python 3.13 features if we used any (we haven't)
- Dependency compatibility (unlikely, most packages support 3.11)

## Success Criteria

1. ✅ `uv sync` completes without errors
2. ✅ `torch` and `transformers` install successfully
3. ✅ TrOCR model loads and runs inference
4. ✅ OCR accuracy improves significantly over Tesseract

If all pass, merge back to main branch.
