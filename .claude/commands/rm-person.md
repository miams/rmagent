---
description: Query person details from RootsMagic database
---

Query detailed information about a person using rmagent CLI.

Usage:
- `/rm-person 1` - Basic person info
- `/rm-person 1 --events` - Include all events
- `/rm-person 1 --family` - Include family relationships
- `/rm-person 1 --ancestors` - Include ancestors
- `/rm-person 1 --descendants` - Include descendants

```bash
if [ -z "$1" ]; then
  echo "❌ Error: Person ID required"
  echo "Usage: /rm-person <person_id> [--options]"
  exit 1
fi

echo "👤 Querying person $1..."
uv run rmagent person $@
```
