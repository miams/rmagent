---
description: Run linting checks (ruff and black)
---

Run code quality checks using ruff and black formatters.

Usage:
- `/lint` - Check code without modifying
- `/lint fix` - Auto-fix issues where possible

```bash
if [ "$ARGUMENTS" = "fix" ]; then
  echo "🔧 Auto-fixing issues..."
  uv run ruff check --fix .
  uv run black .
  echo "✅ Fixes applied"
else
  echo "🔍 Checking code quality..."
  uv run ruff check .
  uv run black --check .
fi
```
