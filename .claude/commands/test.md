---
description: Run pytest tests with optional filters
---

Run the test suite using pytest. You can optionally specify a test file or pattern.

Usage:
- `/test` - Run all tests
- `/test unit` - Run only unit tests
- `/test integration` - Run only integration tests
- `/test test_queries.py` - Run specific test file

```bash
if [ -z "$ARGUMENTS" ]; then
  uv run pytest -v
else
  uv run pytest -v tests/$ARGUMENTS*
fi
```
