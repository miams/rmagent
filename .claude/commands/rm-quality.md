---
description: Run data quality validation on RootsMagic database
---

Run data quality checks on the RootsMagic database.

Usage:
- `/rm-quality` - Run all quality checks
- `/rm-quality dates` - Check only date issues
- `/rm-quality names` - Check only name issues
- `/rm-quality places` - Check only place issues
- `/rm-quality relationships` - Check only relationship issues

```bash
if [ -z "$ARGUMENTS" ]; then
  echo "🔍 Running all data quality checks..."
  uv run rmagent quality --format table
else
  echo "🔍 Running quality checks for category: $ARGUMENTS"
  uv run rmagent quality --category $ARGUMENTS --format table
fi
```
