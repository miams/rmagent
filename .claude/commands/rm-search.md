---
description: Search RootsMagic database by name or place
---

Search the RootsMagic database for people by name or place.

Usage:
- `/rm-search --name "John Smith"` - Search by name
- `/rm-search --place "Baltimore"` - Search by place
- `/rm-search --name "Smith" --limit 10` - Limit results

```bash
if [ -z "$ARGUMENTS" ]; then
  echo "❌ Error: Search parameters required"
  echo "Usage: /rm-search --name \"Name\" or /rm-search --place \"Place\""
  exit 1
fi

echo "🔎 Searching database..."
uv run rmagent search $ARGUMENTS
```
