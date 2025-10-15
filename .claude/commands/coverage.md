---
description: Run tests with coverage report
---

Run the full test suite with coverage analysis. Shows which lines are covered and identifies gaps.

```bash
uv run pytest --cov=rmagent --cov-report=term-missing --cov-report=html
echo ""
echo "📊 Coverage report generated at: file://$(pwd)/htmlcov/index.html"
```
