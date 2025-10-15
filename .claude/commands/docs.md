---
description: Open documentation in browser or show quick reference
---

Quick access to RMAgent documentation.

Usage:
- `/docs` - Show documentation index
- `/docs schema` - Open schema reference
- `/docs data-formats` - Open data formats reference
- `/docs dev` - Open developer guide

```bash
case "$ARGUMENTS" in
  schema)
    echo "📖 Schema Reference: docs/reference/schema/schema-reference.md"
    cat docs/reference/schema/schema-reference.md | head -50
    ;;
  data-formats)
    echo "📖 Data Formats: docs/reference/data-formats/"
    ls -1 docs/reference/data-formats/
    ;;
  dev)
    echo "📖 Developer Guide: docs/guides/developer-guide.md"
    cat docs/guides/developer-guide.md | head -50
    ;;
  *)
    echo "📚 RMAgent Documentation Index"
    echo ""
    cat docs/INDEX.md | head -80
    ;;
esac
```
