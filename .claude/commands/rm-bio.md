---
description: Generate a biography for a person using rmagent
show-prompt: true
meta: true
---

Generate a biography using the rmagent CLI. Requires a person ID.

Usage:
- `/rm-bio 1` - Generate standard biography for person 1
- `/rm-bio 1 short` - Generate short biography
- `/rm-bio 1 comprehensive` - Generate comprehensive biography

```bash
if [ -z "$1" ]; then
  echo "❌ Error: Person ID required"
  echo "Usage: /rm-bio <person_id> [length]"
  echo "Example: /rm-bio 1 standard"
  exit 1
fi

PERSON_ID=$1
LENGTH=${2:-standard}

echo "📝 Generating $LENGTH biography for person $PERSON_ID..."
uv run rmagent bio $PERSON_ID --length $LENGTH --output reports/biographies/
```
