---
description: Verify RootsMagic database file exists and is accessible
---

Check that the RootsMagic database file is present and can be queried.

```bash
DB_PATH="${RM_DATABASE_PATH:-data/Iiams.rmtree}"

if [ ! -f "$DB_PATH" ]; then
  echo "❌ Database file not found: $DB_PATH"
  echo ""
  echo "Set RM_DATABASE_PATH in config/.env"
  exit 1
fi

echo "✅ Database found: $DB_PATH"
echo ""

# Get basic stats
PERSON_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM PersonTable;")
EVENT_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM EventTable;")
SOURCE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM SourceTable;")

echo "📊 Database Statistics:"
echo "  • Persons: $PERSON_COUNT"
echo "  • Events: $EVENT_COUNT"
echo "  • Sources: $SOURCE_COUNT"
```
