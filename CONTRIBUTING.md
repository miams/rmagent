# Contributing to RMAgent

Thank you for your interest in contributing to RMAgent! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior:**
- Harassment, trolling, or discriminatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- uv (recommended) or pip
- Git
- Text editor or IDE
- RootsMagic 11 database for testing

### Fork and Clone

1. **Fork the repository** on GitHub

2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/rmagent.git
   cd rmagent
   ```

3. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/miams/rmagent.git
   ```

4. **Verify remotes:**
   ```bash
   git remote -v
   # origin    https://github.com/YOUR_USERNAME/rmagent.git (fetch)
   # origin    https://github.com/YOUR_USERNAME/rmagent.git (push)
   # upstream  https://github.com/miams/rmagent.git (fetch)
   # upstream  https://github.com/miams/rmagent.git (push)
   ```

---

## Development Setup

### Install Development Dependencies

```bash
# With uv (recommended)
uv sync --extra dev

# With pip
pip install -e ".[dev]"
```

This installs:
- Core dependencies
- Testing tools (pytest, pytest-cov, pytest-mock)
- Code quality tools (black, ruff, mypy)

### Configure Environment

```bash
# Copy example configuration
cp config/.env.example config/.env

# Edit with your settings
nano config/.env
```

For development, you can use Ollama (free, local) or get test API keys.

### Verify Setup

```bash
# Run tests
uv run pytest

# Check code formatting
uv run black --check .

# Check linting
uv run ruff check .

# Type checking
uv run mypy rmagent/
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test improvements
- `refactor/` - Code refactoring

### 2. Make Changes

- Write code following [Coding Standards](#coding-standards)
- Add tests for new functionality
- Update documentation as needed
- Commit frequently with clear messages

### 3. Commit Changes

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat: add support for custom timeline phases"
git commit -m "fix: resolve database connection timeout"
git commit -m "docs: update installation instructions"
git commit -m "test: add integration tests for export command"
```

**Commit types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding or updating tests
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `style`: Code style changes (formatting, missing semi-colons, etc.)
- `chore`: Changes to build process or auxiliary tools

### 4. Keep Branch Updated

```bash
# Fetch upstream changes
git fetch upstream

# Rebase on upstream/main
git rebase upstream/main

# Resolve conflicts if any
# Then push to your fork
git push origin feature/your-feature-name
```

### 5. Run Tests and Quality Checks

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=rmagent --cov-report=html

# Format code
uv run black .

# Check linting
uv run ruff check .

# Type checking
uv run mypy rmagent/
```

**All checks must pass before submitting PR.**

### 6. Create Pull Request

See [Pull Request Process](#pull-request-process) below.

---

## Coding Standards

### Python Style Guide

We follow **PEP 8** with these tools:

- **black** - Code formatting (line length: 100)
- **ruff** - Fast Python linter
- **mypy** - Static type checking

### Code Formatting

```bash
# Format all code
uv run black .

# Check formatting without changes
uv run black --check .
```

**Black configuration** (pyproject.toml):
```toml
[tool.black]
line-length = 100
target-version = ["py311"]
```

### Linting

```bash
# Check for linting issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### Type Hints

- **Use type hints for all function signatures**
- **Use type hints for complex variables**
- **Run mypy before committing**

```python
# Good
def get_person(person_id: int) -> Person | None:
    """Get person by ID."""
    return db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (person_id,))

# Bad (no type hints)
def get_person(person_id):
    return db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (person_id,))
```

### Docstrings

Use Google-style docstrings:

```python
def generate_biography(
    person_id: int,
    length: BiographyLength = BiographyLength.STANDARD,
    citation_style: CitationStyle = CitationStyle.FOOTNOTE,
) -> Biography:
    """Generate biographical narrative for a person.

    Args:
        person_id: PersonID from RootsMagic database
        length: Biography length (short, standard, comprehensive)
        citation_style: Citation format (footnote, parenthetical, narrative)

    Returns:
        Biography object with text, sources, and metadata

    Raises:
        PersonNotFoundError: If person_id doesn't exist
        DatabaseError: If database query fails
    """
    pass
```

### Import Organization

Order imports as:
1. Standard library
2. Third-party packages
3. Local imports

```python
# Standard library
import json
import logging
from pathlib import Path
from typing import Any

# Third-party
from pydantic import BaseModel
import click

# Local
from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.queries import QueryService
from rmagent.agent.llm_provider import get_provider
```

### Error Handling

```python
# Use specific exceptions
try:
    person = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (person_id,))
except sqlite3.OperationalError as e:
    logger.error(f"Database query failed: {e}")
    raise DatabaseError(f"Failed to query person {person_id}") from e

# Provide helpful error messages
if person is None:
    raise PersonNotFoundError(
        f"Person with ID {person_id} not found in database. "
        f"Use 'rmagent search --name' to find PersonIDs."
    )
```

---

## Testing Guidelines

See [TESTING.md](TESTING.md) for complete testing documentation.

### Test Requirements

- **All new features must have tests**
- **Bug fixes must include regression tests**
- **Maintain 80%+ code coverage on new code**
- **All tests must pass before PR is merged**

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_database.py

# Run with coverage
uv run pytest --cov=rmagent --cov-report=html

# Run integration tests (requires API keys)
uv run pytest tests/integration/ -m ""
```

### Writing Tests

```python
import pytest
from rmagent.rmlib.database import RMDatabase

def test_database_connection():
    """Test database connects successfully."""
    with RMDatabase("data/Iiams.rmtree") as db:
        result = db.query_value("SELECT COUNT(*) FROM PersonTable")
        assert result > 0

def test_person_not_found():
    """Test PersonNotFoundError is raised."""
    with pytest.raises(PersonNotFoundError):
        query_service.get_person_with_primary_name(99999999)
```

---

## Documentation

### Documentation Requirements

- **Update README.md** if adding major features
- **Update USAGE.md** if adding CLI commands or options
- **Update CONFIGURATION.md** if adding config options
- **Add docstrings** to all public functions and classes
- **Update CHANGELOG.md** with your changes

### Documentation Files

- `README.md` - Project overview and quick start
- `INSTALL.md` - Installation instructions
- `USAGE.md` - CLI command reference
- `CONFIGURATION.md` - Configuration guide
- `FAQ.md` - Common questions
- `EXAMPLES.md` - Real-world usage examples
- `CHANGELOG.md` - Version history

### Docstring Examples

```python
class BiographyGenerator:
    """Generate biographical narratives from RootsMagic data.

    The BiographyGenerator extracts person information from a RootsMagic
    database and generates structured biographical narratives using
    either template-based or AI-powered approaches.

    Attributes:
        db_path: Path to RootsMagic database file
        agent: Optional GenealogyAgent for AI generation
        respect_private: Honor IsPrivate flags in database

    Example:
        >>> generator = BiographyGenerator(db_path="data/family.rmtree")
        >>> bio = generator.generate(person_id=1, length=BiographyLength.STANDARD)
        >>> print(bio.render_markdown())
    """
    pass
```

---

## Pull Request Process

### Before Submitting

1. **✅ All tests pass:**
   ```bash
   uv run pytest
   ```

2. **✅ Code is formatted:**
   ```bash
   uv run black .
   ```

3. **✅ No linting errors:**
   ```bash
   uv run ruff check .
   ```

4. **✅ Type checking passes:**
   ```bash
   uv run mypy rmagent/
   ```

5. **✅ Documentation updated**

6. **✅ CHANGELOG.md updated**

### Creating the PR

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open PR on GitHub**

3. **Fill out PR template:**
   - Description of changes
   - Related issue numbers (#123)
   - Testing performed
   - Breaking changes (if any)

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Related Issues
Fixes #123
Closes #456

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing Performed
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] All tests passing

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review performed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Tests added for new functionality
```

### Review Process

1. **Automated checks run** (tests, linting, type checking)
2. **Maintainer reviews code**
3. **Feedback addressed** (if any)
4. **PR approved and merged**

### After Merge

1. **Delete your feature branch:**
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your main:**
   ```bash
   git checkout main
   git pull upstream main
   ```

---

## Issue Reporting

### Before Creating an Issue

1. **Search existing issues** - Your issue may already be reported
2. **Check FAQ.md** - Common issues are documented there
3. **Try latest version** - Issue may be fixed in recent release

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. See error

**Expected behavior**
What you expected to happen.

**Environment**
- RMAgent version: [e.g., 0.2.0]
- Python version: [e.g., 3.11.5]
- OS: [e.g., macOS 14.0, Ubuntu 22.04]
- LLM provider: [e.g., Anthropic Claude]

**Error message**
```
Full error message here
```

**Additional context**
Any other relevant information.
```

### Feature Requests

Use the feature request template:

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other approaches you've thought about.

**Additional context**
Any other relevant information.
```

---

## Development Guidelines

### Project Structure

```
rmagent/
├── rmagent/              # Main package
│   ├── rmlib/           # Core library (database, parsers, queries)
│   ├── agent/           # AI agent (LLM providers, prompts)
│   ├── generators/      # Output generators
│   ├── cli/             # Command-line interface
│   └── config/          # Configuration
├── tests/               # Test suite
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── docs/                # Documentation
└── data_reference/      # Schema documentation
```

### Module Dependencies

- **rmlib/** - No dependencies on other rmagent modules (core library)
- **agent/** - Depends on rmlib
- **generators/** - Depends on rmlib and agent
- **cli/** - Depends on all other modules

### Adding New Features

1. **Start with tests** (TDD approach)
2. **Implement core functionality in rmlib/**
3. **Add AI integration in agent/** (if needed)
4. **Add generator in generators/** (if creating output)
5. **Add CLI command in cli/** (if user-facing)
6. **Update documentation**

---

## Questions?

- **Documentation:** Check README.md, INSTALL.md, USAGE.md, FAQ.md
- **Issues:** https://github.com/miams/rmagent/issues
- **Discussions:** https://github.com/miams/rmagent/discussions

Thank you for contributing to RMAgent! 🎉
