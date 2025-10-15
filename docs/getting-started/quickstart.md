# RMAgent Quick Start

## Installation

```bash
# Clone repository
git clone git@github.com:miams/rmagent.git
cd rmagent

# Install dependencies
uv sync --extra dev

# Configure environment
cp config/.env.example config/.env
# Edit config/.env with your API keys and database path
```

## CLI Setup (One-Time)

```bash
# Run automated setup
./setup_cli.sh

# Add to your ~/.zshrc (as instructed by setup script):
export PATH="/Users/miams/Code/RM11/.venv/bin:$PATH"
fpath=(~/.zfunc $fpath)
autoload -Uz compinit && compinit

# Reload shell
source ~/.zshrc
```

## Usage

After setup, use `rmagent` directly (no `uv run` needed):

```bash
# Query person
rmagent person 1 --events --family

# Generate biography
rmagent bio 1 --length standard --output bio.md

# Data quality checks
rmagent quality --severity critical

# Ask questions (requires LLM)
rmagent ask "Who were John Smith's parents?"

# Generate timeline
rmagent timeline 1 --output timeline.json

# Export to Hugo
rmagent export hugo 1 --output-dir content/people

# Search database (includes alternate names automatically)
rmagent search --name "Smith"
rmagent search --name "Lucy Virginia Dorsey"
rmagent search --name "Janet Bross"  # Finds alternate names

# Search with surname variations (bracket syntax)
rmagent search --name "John Iiams [Ijams]"       # Searches 2 variations
rmagent search --name "John Iams [Ijams] [Imes]" # Searches 3 variations
rmagent search --name "John [ALL]"               # Searches all configured variants

# Search by married name (for women)
rmagent search --name "Janet Iiams" --married-name
```

## Tab Completion

Tab completion is enabled for:
- Commands: `rmagent <TAB>`
- Options: `rmagent bio --<TAB>`
- Choices: `rmagent quality --severity <TAB>`

## Development

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=rmagent --cov-report=html

# Code quality
uv run black .           # Format
uv run ruff check .      # Lint
uv run mypy rmagent/     # Type check
```

## Documentation

- **[docs/CLI_SETUP.md](docs/CLI_SETUP.md)** - Complete CLI setup guide
- **[USAGE.md](USAGE.md)** - CLI reference with 50+ examples
- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** - Comprehensive user guide
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Architecture and API reference

## Getting Help

```bash
rmagent --help              # Show all commands
rmagent person --help       # Command-specific help
rmagent completion zsh      # Setup instructions for completion
```

## Common Tasks

**Query person with full context:**
```bash
rmagent person 1 --events --family --ancestors
```

**Generate comprehensive biography with footnotes:**
```bash
rmagent bio 1 --length comprehensive --citation-style footnote --output bio.md
```

**Run quality checks on critical issues:**
```bash
rmagent quality --severity critical --format html --output critical_issues.html
```

**Interactive Q&A session:**
```bash
rmagent ask --interactive
```

**Export batch of people to Hugo:**
```bash
rmagent export hugo --batch-ids 1,2,3,4,5 --output-dir content/people
```

## Troubleshooting

**Command not found:**
```bash
# Check PATH includes .venv/bin
echo $PATH | grep ".venv/bin"

# Verify binary exists
ls -la .venv/bin/rmagent

# Reload shell configuration
source ~/.zshrc
```

**Tab completion not working:**
```bash
# Verify completion script exists
ls -la ~/.zfunc/_rmagent

# Check fpath
echo $fpath

# Regenerate if needed
./setup_cli.sh
```

## Support

- **Issues:** https://github.com/miams/rmagent/issues
- **Documentation:** [docs/README.md](docs/README.md)
- **FAQ:** [FAQ.md](FAQ.md)
