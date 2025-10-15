# Installation Guide - RMAgent

Complete installation instructions for RMAgent, an AI-powered genealogy agent for RootsMagic databases.

## Table of Contents

- [System Requirements](#system-requirements)
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Platform-Specific Instructions](#platform-specific-instructions)

---

## System Requirements

### Minimum Requirements

- **Operating System:** macOS 10.15+, Linux (Ubuntu 20.04+), Windows 10+ (WSL2)
- **Python:** 3.11 or higher
- **Memory:** 2 GB RAM minimum (4 GB recommended)
- **Disk Space:** 500 MB for installation + space for database files
- **Network:** Internet connection for LLM API calls

### Software Dependencies

- Python 3.11+
- pip or uv (package manager)
- Git (for installation from source)
- SQLite 3.x (usually pre-installed)
- RootsMagic 11 database (.rmtree file)

### LLM Provider Requirements

You need an API key for at least one provider:

- **Anthropic Claude:** https://console.anthropic.com/
- **OpenAI GPT:** https://platform.openai.com/
- **Ollama (Local):** https://ollama.com/ (no API key needed)

---

## Prerequisites

### 1. Install Python 3.11+

#### macOS

```bash
# Using Homebrew
brew install python@3.11

# Verify installation
python3 --version  # Should show 3.11.x or higher
```

#### Linux (Ubuntu/Debian)

```bash
# Add deadsnakes PPA (if needed)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Verify installation
python3.11 --version
```

#### Windows (WSL2)

```bash
# Install WSL2 first (if not already installed)
wsl --install

# Then follow Linux instructions above
```

### 2. Install uv (Recommended) or pip

#### Install uv (Fast Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal or source shell config
source ~/.bashrc  # or ~/.zshrc

# Verify installation
uv --version
```

#### Alternative: Use pip

```bash
# Upgrade pip
python3 -m pip install --upgrade pip
```

### 3. Install Git

```bash
# macOS
brew install git

# Linux
sudo apt install git

# Verify
git --version
```

---

## Installation Steps

### Method 1: Install with uv (Recommended)

This is the recommended method for development and active use.

```bash
# 1. Clone the repository
git clone https://github.com/miams/rmagent.git
cd rmagent

# 2. Install dependencies
uv sync

# This creates a virtual environment in .venv/ and installs all dependencies

# 3. Verify installation
uv run rmagent --version
```

### Method 2: Install with pip

```bash
# 1. Clone the repository
git clone https://github.com/miams/rmagent.git
cd rmagent

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows

# 4. Install dependencies
pip install -e .

# 5. Verify installation
rmagent --version
```

### Method 3: Install Development Dependencies

For contributors and developers:

```bash
# With uv
uv sync --extra dev

# With pip
pip install -e ".[dev]"
```

This installs additional tools:
- pytest, pytest-cov, pytest-mock (testing)
- black, ruff, mypy (code quality)
- Additional development utilities

---

## Configuration

### 1. Create Configuration File

```bash
# Copy example configuration
cp config/.env.example config/.env
```

### 2. Edit config/.env

Open `config/.env` in your text editor and configure:

#### Basic Configuration

```bash
# Database path (required)
RM_DATABASE_PATH=data/your-database.rmtree

# SQLite extension path (usually default is fine)
SQLITE_ICU_EXTENSION=./sqlite-extension/icu.dylib
```

#### LLM Provider Configuration

Choose **one** provider and configure:

##### Option 1: Anthropic Claude (Recommended)

```bash
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Get from https://console.anthropic.com/
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929  # or claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=3000
```

##### Option 2: OpenAI GPT

```bash
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxx  # Get from https://platform.openai.com/
OPENAI_MODEL=gpt-4o-mini  # or gpt-5-chat-latest
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=3000
```

##### Option 3: Ollama (Local)

```bash
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1  # or other model
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=3000
```

#### Output Configuration

```bash
# Output directories
OUTPUT_DIR=output
EXPORT_DIR=exports

# Privacy settings
RESPECT_PRIVATE_FLAG=true
APPLY_110_YEAR_RULE=true

# Citation style
DEFAULT_CITATION_STYLE=footnote  # or parenthetical, narrative
```

#### Logging Configuration

```bash
# Logging levels: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Log file location
LOG_FILE=rmtool.log

# LLM debugging (JSON traces)
LLM_DEBUG_LOG_FILE=logs/llm_debug.jsonl
```

### 3. Obtain LLM API Keys

#### Anthropic Claude

1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. Paste into `config/.env` as `ANTHROPIC_API_KEY`

**Pricing:** ~$3/million input tokens, ~$15/million output tokens

#### OpenAI GPT

1. Visit https://platform.openai.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create new secret key"
5. Copy the key (starts with `sk-proj-` or `sk-`)
6. Paste into `config/.env` as `OPENAI_API_KEY`

**Pricing:** Varies by model (~$0.15-$2.50/million tokens for GPT-4o)

#### Ollama (Local)

1. Install Ollama: https://ollama.com/download
2. Pull a model:
   ```bash
   ollama pull llama3.1
   ```
3. Start Ollama server:
   ```bash
   ollama serve
   ```
4. Verify it's running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

**Pricing:** Free (runs locally)

### 4. Prepare Your Database

```bash
# Create data directory
mkdir -p data

# Copy your RootsMagic database
cp /path/to/your/database.rmtree data/

# Update config/.env with correct path
# RM_DATABASE_PATH=data/your-database.rmtree
```

---

## Verification

### 1. Test Database Connection

```bash
# Query a person (replace 1 with a valid PersonID)
uv run rmagent person 1

# Should display person information without errors
```

### 2. Test Data Quality

```bash
# Run quality checks (no LLM required)
uv run rmagent quality --severity critical

# Should show database statistics and any critical issues
```

### 3. Test LLM Integration (Optional)

```bash
# Test biography generation
uv run rmagent bio 1 --length short

# Should generate AI-powered biography
```

### 4. Run Test Suite

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=rmagent --cov-report=html

# Open htmlcov/index.html to view coverage
```

### Expected Output

```
======================== 279 passed in 25.43s =========================

Coverage report:
rmagent/agent/llm_provider.py     90%
rmagent/rmlib/quality.py          91%
rmagent/rmlib/database.py         76%
... (more modules)
```

---

## Troubleshooting

### Common Issues

#### 1. SQLite Extension Not Loading

**Error:**
```
Error: Could not load ICU extension
```

**Solution:**

- **macOS:** Extension included at `sqlite-extension/icu.dylib` (should work by default)
- **Linux:** You may need to compile the extension:
  ```bash
  sudo apt install libsqlite3-dev libicu-dev
  # See sqlite-extension/README.md for compilation instructions
  ```
- **Windows/WSL2:** Follow Linux instructions

#### 2. Python Version Too Old

**Error:**
```
python_requires = ">=3.11"
```

**Solution:**
```bash
# Install Python 3.11+
# macOS
brew install python@3.11

# Linux
sudo apt install python3.11
```

#### 3. API Key Not Working

**Error:**
```
AuthenticationError: Invalid API key
```

**Solution:**
1. Verify the API key is correct (no extra spaces)
2. Check the key hasn't expired
3. Verify your account has billing enabled (Anthropic/OpenAI)
4. Test the key directly:
   ```bash
   # Anthropic
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: $ANTHROPIC_API_KEY" \
     -H "anthropic-version: 2023-06-01"
   ```

#### 4. Database Not Found

**Error:**
```
FileNotFoundError: data/Iiams.rmtree not found
```

**Solution:**
1. Check the database file exists:
   ```bash
   ls -lh data/*.rmtree
   ```
2. Verify the path in `config/.env` matches the actual file location
3. Use absolute paths if relative paths don't work:
   ```bash
   RM_DATABASE_PATH=/full/path/to/database.rmtree
   ```

#### 5. Ollama Connection Failed

**Error:**
```
ConnectionError: Could not connect to Ollama at http://localhost:11434
```

**Solution:**
1. Verify Ollama is running:
   ```bash
   ollama serve
   ```
2. Check the model is pulled:
   ```bash
   ollama list
   ```
3. Test connection:
   ```bash
   curl http://localhost:11434/api/tags
   ```

#### 6. Tests Failing

**Error:**
```
FAILED tests/unit/test_quality.py::test_rule_5_1_date_validation
```

**Solution:**
```bash
# Clear pytest cache
rm -rf .pytest_cache

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_quality.py -v
```

#### 7. Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'rmagent'
```

**Solution:**
```bash
# Reinstall in development mode
uv sync

# Or with pip
pip install -e .

# Verify installation
python -c "import rmagent; print(rmagent.__version__)"
```

---

## Platform-Specific Instructions

### macOS

1. Install Homebrew (if not installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install Python 3.11:
   ```bash
   brew install python@3.11
   ```

3. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. Follow standard installation steps above

**SQLite Extension:** Included at `sqlite-extension/icu.dylib` (works by default)

### Linux (Ubuntu/Debian)

1. Update packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Install Python 3.11:
   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt install python3.11 python3.11-venv python3.11-dev
   ```

3. Install build tools (for SQLite extension):
   ```bash
   sudo apt install build-essential libsqlite3-dev libicu-dev
   ```

4. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

5. Follow standard installation steps

**SQLite Extension:** May need to compile (see `sqlite-extension/README.md`)

### Windows (WSL2)

1. Install WSL2:
   ```powershell
   wsl --install
   ```

2. Restart computer

3. Open WSL2 terminal (Ubuntu):
   ```bash
   wsl
   ```

4. Follow Linux installation instructions above

**Note:** WSL2 is strongly recommended over native Windows installation due to better SQLite extension support.

---

## Next Steps

Once installation is complete:

1. **Read the User Guide:** `docs/USER_GUIDE.md` or `docs/RMAgent_User_Guide.pdf`
2. **Try the Tutorial:** `docs/TUTORIAL.md` (getting started walkthrough)
3. **Explore Examples:** `EXAMPLES.md` (real-world usage scenarios)
4. **Check Configuration:** `CONFIGURATION.md` (advanced settings)

---

## Getting Help

- **Documentation:** https://github.com/miams/rmagent/tree/main/docs
- **Issues:** https://github.com/miams/rmagent/issues
- **FAQ:** `FAQ.md` (common questions)
- **User Guide:** `docs/USER_GUIDE.md`

---

## Uninstallation

To remove RMAgent:

```bash
# With uv
cd rmagent
rm -rf .venv

# With pip
pip uninstall rmagent

# Remove configuration (optional)
rm config/.env

# Remove the entire directory
cd ..
rm -rf rmagent
```

---

**Installation complete!** You're now ready to use RMAgent for genealogy research and biography generation.

See `docs/USER_GUIDE.md` for comprehensive usage instructions.
