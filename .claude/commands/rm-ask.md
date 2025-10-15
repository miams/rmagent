---
description: Ask a question about the genealogy database using AI
show-prompt: true
meta: true
---

Ask natural language questions about your genealogy data. Uses AI to query and analyze the database.

Usage:
- `/rm-ask "Who are the ancestors of John Smith?"`
- `/rm-ask "Find everyone born in Baltimore"`
- `/rm-ask "Show family relationships for person 1"`

```bash
if [ -z "$ARGUMENTS" ]; then
  echo "❌ Error: Question required"
  echo "Usage: /rm-ask \"Your question here\""
  exit 1
fi

echo "🤔 Asking AI about your genealogy data..."
uv run rmagent ask "$ARGUMENTS"
```
