---
description: Generate timeline visualization for a person
---

Generate a TimelineJS3 timeline for a person's life events.

Usage:
- `/rm-timeline 1` - Generate JSON timeline for person 1
- `/rm-timeline 1 --format html` - Generate HTML timeline
- `/rm-timeline 1 --include-family` - Include family events
- `/rm-timeline 1 --group-by-phase` - Group events by life phases

```bash
if [ -z "$1" ]; then
  echo "❌ Error: Person ID required"
  echo "Usage: /rm-timeline <person_id> [options]"
  exit 1
fi

echo "📅 Generating timeline for person $1..."
uv run rmagent timeline $@
```
