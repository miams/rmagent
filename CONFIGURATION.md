# Configuration Guide - RMAgent

Complete configuration reference for customizing RMAgent behavior.

## Table of Contents

- [Configuration File Location](#configuration-file-location)
- [Environment Variables](#environment-variables)
- [LLM Provider Configuration](#llm-provider-configuration)
- [Database Configuration](#database-configuration)
- [Output Configuration](#output-configuration)
- [Privacy Settings](#privacy-settings)
- [Logging Configuration](#logging-configuration)
- [Advanced Configuration](#advanced-configuration)
- [Prompt Customization](#prompt-customization)
- [Configuration Examples](#configuration-examples)

---

## Configuration File Location

RMAgent uses a `.env` file for configuration:

```
config/.env
```

**Create from example:**

```bash
cp config/.env.example config/.env
```

Then edit `config/.env` with your text editor.

---

## Environment Variables

### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEFAULT_LLM_PROVIDER` | Default LLM provider (anthropic, openai, ollama) | anthropic | Yes |
| `LLM_TEMPERATURE` | LLM temperature (0.0-1.0, lower = more deterministic) | 0.2 | No |
| `LLM_MAX_TOKENS` | Maximum tokens per LLM response | 3000 | No |
| `RM_DATABASE_PATH` | Path to RootsMagic database file | data/Iiams.rmtree | Yes |
| `SQLITE_ICU_EXTENSION` | Path to SQLite ICU extension | ./sqlite-extension/icu.dylib | No |

### Output Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `OUTPUT_DIR` | Directory for generated outputs | output |
| `EXPORT_DIR` | Directory for Hugo exports | exports |

### Privacy Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `RESPECT_PRIVATE_FLAG` | Honor IsPrivate flags in database | true |
| `APPLY_110_YEAR_RULE` | Apply 110-year living person privacy rule | true |

### Citation Settings

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `DEFAULT_CITATION_STYLE` | Default citation style | footnote | footnote, parenthetical, narrative |

### Logging Settings

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Logging verbosity | INFO | DEBUG, INFO, WARNING, ERROR |
| `LOG_FILE` | Main log file location | rmtool.log | Any path |
| `LLM_DEBUG_LOG_FILE` | LLM trace log (JSON lines) | logs/llm_debug.jsonl | Any path |

---

## LLM Provider Configuration

### Anthropic Claude

**Best for:** Genealogical narratives, detailed analysis, source citations

```bash
# Provider selection
DEFAULT_LLM_PROVIDER=anthropic

# API credentials
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Get from https://console.anthropic.com/

# Model selection
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929  # Latest Sonnet 4.5
# OR
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022  # Sonnet 3.5

# Parameters
LLM_TEMPERATURE=0.2  # Lower = more consistent, higher = more creative
LLM_MAX_TOKENS=3000  # Maximum response length
```

**Pricing (as of 2025-10):**
- Input: ~$3/million tokens
- Output: ~$15/million tokens
- Typical biography: ~$0.01-0.05

**Recommended Settings:**
```bash
# For biographies (balance quality/cost)
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=3000

# For comprehensive analysis (best quality)
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000
```

### OpenAI GPT

**Best for:** Fast responses, lower cost, general queries

```bash
# Provider selection
DEFAULT_LLM_PROVIDER=openai

# API credentials
OPENAI_API_KEY=sk-proj-xxxxx  # Get from https://platform.openai.com/

# Model selection
OPENAI_MODEL=gpt-4o-mini  # Fast, affordable
# OR
OPENAI_MODEL=gpt-5-chat-latest  # Latest GPT-5
# OR
OPENAI_MODEL=gpt-4o  # GPT-4 Optimized

# Parameters
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=3000
```

**Pricing (approximate):**
- GPT-4o-mini: ~$0.15-0.60/million tokens
- GPT-4o: ~$2.50-10/million tokens
- GPT-5: Variable pricing

**Recommended Settings:**
```bash
# For cost-effective biographies
OPENAI_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000

# For best quality
OPENAI_MODEL=gpt-5-chat-latest
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=3000
```

### Ollama (Local)

**Best for:** Privacy, no API costs, offline use

```bash
# Provider selection
DEFAULT_LLM_PROVIDER=ollama

# Server configuration
OLLAMA_BASE_URL=http://localhost:11434

# Model selection
OLLAMA_MODEL=llama3.1  # Llama 3.1 (8B or 70B)
# OR
OLLAMA_MODEL=mistral   # Mistral 7B
# OR
OLLAMA_MODEL=mixtral   # Mixtral 8x7B

# Parameters
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=3000
```

**Setup:**

```bash
# Install Ollama
# https://ollama.com/download

# Pull a model
ollama pull llama3.1

# Start server
ollama serve  # Runs on http://localhost:11434

# Verify
curl http://localhost:11434/api/tags
```

**Recommended Models:**
```bash
# Best quality (requires 40GB+ RAM)
ollama pull llama3.1:70b
OLLAMA_MODEL=llama3.1:70b

# Balanced (requires 8GB+ RAM)
ollama pull llama3.1
OLLAMA_MODEL=llama3.1

# Fast/low memory (requires 4GB+ RAM)
ollama pull llama3.1:7b
OLLAMA_MODEL=llama3.1:7b
```

---

## Database Configuration

### Basic Database Path

```bash
# Relative path
RM_DATABASE_PATH=data/your-database.rmtree

# Absolute path
RM_DATABASE_PATH=/Users/username/Documents/Genealogy/family.rmtree
```

### SQLite Extension

The ICU extension is required for RMNOCASE collation:

```bash
# macOS (included)
SQLITE_ICU_EXTENSION=./sqlite-extension/icu.dylib

# Linux (may need to compile)
SQLITE_ICU_EXTENSION=./sqlite-extension/icu.so

# Custom path
SQLITE_ICU_EXTENSION=/usr/local/lib/sqlite3/icu.so
```

**Troubleshooting:**

If you get "Could not load ICU extension" error:

1. **macOS:** Extension should work out of the box
2. **Linux:** See `sqlite-extension/README.md` for compilation instructions
3. **Custom SQLite:** You may need to compile against your SQLite version

---

## Output Configuration

### Output Directories

```bash
# Generated outputs (biographies, reports, timelines)
OUTPUT_DIR=output

# Hugo exports
EXPORT_DIR=exports
```

**Directory Structure:**

```
output/
├── biographies/
├── reports/
└── timelines/

exports/
└── hugo/
    ├── content/people/
    └── static/timelines/
```

### Media Path Configuration (Hugo Export)

```bash
# Default: /media/
# Used for Hugo blog media URLs

# Example: Media in Hugo static directory
--media-base-path /static/genealogy-photos/

# Example: External CDN
--media-base-path https://cdn.example.com/genealogy/
```

---

## Privacy Settings

### IsPrivate Flag

```bash
# Respect IsPrivate flag in database
RESPECT_PRIVATE_FLAG=true  # Exclude people/events marked private
RESPECT_PRIVATE_FLAG=false  # Include all data
```

**Default:** `true` (recommended)

**Effect:**
- When `true`: Excludes people with `IsPrivate=1` from biographies and exports
- When `false`: Includes all data regardless of privacy flags

### 110-Year Living Person Rule

```bash
# Apply 110-year privacy rule for living persons
APPLY_110_YEAR_RULE=true  # Protect recent living persons
APPLY_110_YEAR_RULE=false  # Include all persons
```

**Default:** `true` (recommended)

**Effect:**
- When `true`: Excludes persons born <110 years ago with no death event
- When `false`: Includes all persons regardless of age

**Privacy Best Practices:**

```bash
# Recommended for public sharing
RESPECT_PRIVATE_FLAG=true
APPLY_110_YEAR_RULE=true

# For private research only
RESPECT_PRIVATE_FLAG=false
APPLY_110_YEAR_RULE=false
```

---

## Logging Configuration

### Log Levels

```bash
# Logging verbosity
LOG_LEVEL=DEBUG    # Very verbose (all operations)
LOG_LEVEL=INFO     # Normal operations
LOG_LEVEL=WARNING  # Warnings and errors only
LOG_LEVEL=ERROR    # Errors only
```

**Recommended:**
- Development: `DEBUG`
- Production: `INFO`
- Silent mode: `ERROR`

### Log Files

```bash
# Main application log
LOG_FILE=rmtool.log  # Default location

# Custom path
LOG_FILE=/var/log/rmtool/app.log
```

### LLM Debug Logging

```bash
# LLM trace log (JSON lines format)
LLM_DEBUG_LOG_FILE=logs/llm_debug.jsonl
```

**Contents:**
- Model name
- Provider (anthropic, openai, ollama)
- Token counts (input, output)
- Cost calculation
- Latency
- Full prompt text
- Full completion text
- Timestamp

**Example Entry:**

```json
{
  "timestamp": "2025-10-12T10:30:45.123Z",
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-20241022",
  "prompt_tokens": 1234,
  "completion_tokens": 567,
  "cost": 0.0123,
  "latency_ms": 1234,
  "prompt": "Generate a biography for...",
  "completion": "John Smith was born..."
}
```

**Uses:**
- Debug prompt engineering
- Track API costs
- Reproduce LLM responses
- Audit AI-generated content

---

## Advanced Configuration

### Programmatic Configuration

For Python integrations:

```python
from rmagent.config.config import load_app_config

# Load configuration
config = load_app_config()

# Access settings
db_path = config.database.database_path
llm_temp = config.llm.temperature
provider = config.llm.default_provider

# Build LLM provider
provider = config.build_provider()

# Override settings
config.llm.temperature = 0.5
config.output.output_dir = "custom_output"
```

### Environment Variable Overrides

You can override config/.env settings with environment variables:

```bash
# Temporary override
export RM_DATABASE_PATH=/path/to/other/database.rmtree
uv run rmagent person 1

# One-time override
RM_DATABASE_PATH=/path/to/other/database.rmtree uv run rmagent person 1
```

### Command-Line Overrides

Some settings can be overridden at runtime:

```bash
# Override database path
uv run rmagent --database /path/to/database.rmtree person 1

# Override LLM provider
uv run rmagent --llm-provider openai bio 1

# Enable verbose logging
uv run rmagent --verbose quality
```

---

## Prompt Customization

RMAgent allows you to customize AI prompts for different workflows without modifying code. Prompts are stored as YAML files with support for provider-specific variants.

### Prompt System Overview

**Default Prompts:** `config/prompts/`
- `biography.yaml` - Biography generation
- `quality.yaml` - Data quality analysis
- `qa.yaml` - Q&A conversations
- `timeline.yaml` - Timeline synthesis

**Custom Prompts:** `config/prompts/custom/` (optional, not tracked in git)
- Override any default prompt
- Takes precedence over defaults
- Same YAML format

### Provider-Specific Variants

Each prompt file can include provider-specific variants optimized for different LLM capabilities:

- **Anthropic Claude:** Detailed instructions, academic tone, complex reasoning
- **OpenAI GPT:** Direct instructions, efficient phrasing
- **Ollama (local):** Simpler prompts, concrete examples

**Example Structure:**

```yaml
# config/prompts/biography.yaml

key: biography
version: "2025-01-08"
description: "Structured biography generation"

# Default prompt (works for all providers)
template: |
  You are a professional genealogist creating a narrative biography.
  Follow the standard ten-section outline...

  Person Summary: {person_summary}
  Timeline: {timeline_overview}
  ...

# Provider-specific variants (optional)
provider_overrides:
  anthropic:
    template: |
      You are a professional genealogist with expertise in academic writing...
      [More detailed instructions for Claude]

  ollama:
    template: |
      Create a biography following this structure...
      [Simpler instructions for local models]

# Few-shot examples
few_shots:
  - user: "Generate biography for John Smith..."
    assistant: "## Introduction\nJohn Smith was born..."
```

### Creating Custom Prompts

**Step 1: Create custom directory**

```bash
mkdir -p config/prompts/custom
```

**Step 2: Copy and modify default prompt**

```bash
# Copy default biography prompt
cp config/prompts/biography.yaml config/prompts/custom/biography.yaml

# Edit with your preferred text editor
nano config/prompts/custom/biography.yaml
```

**Step 3: Customize prompt text**

Edit the `template:` section to match your style:

```yaml
# config/prompts/custom/biography.yaml

key: biography
version: "2025-01-08"
description: "Custom biography generation"

# Your custom prompt
template: |
  Write a genealogical biography in a narrative storytelling style.
  Focus on family relationships and historical context.

  Person Information:
  {person_summary}

  Life Events:
  {timeline_overview}

  [Your additional instructions here]
```

**Step 4: Test custom prompt**

```bash
# Generate biography (uses your custom prompt)
uv run rmagent bio 1 --output test.md
```

### Prompt Customization Examples

#### Example 1: Formal Academic Style

```yaml
# config/prompts/custom/biography.yaml

template: |
  Compose a scholarly biographical essay following academic conventions.

  Requirements:
  - Formal, third-person narrative voice
  - Chronological organization by life phase
  - Source citations in Chicago Manual of Style format
  - Analysis of social and historical context
  - Critical evaluation of conflicting evidence

  Subject Information:
  {person_summary}

  Chronological Evidence:
  {timeline_overview}

  Family Context:
  {family_overview}

  Source Documentation:
  {source_notes}
```

#### Example 2: Creative Storytelling Style

```yaml
# config/prompts/custom/biography.yaml

template: |
  Write an engaging narrative biography that brings history to life.

  Style Guidelines:
  - Use vivid, descriptive language
  - Begin with a compelling scene or anecdote
  - Weave family stories throughout
  - Connect personal events to historical context
  - End with legacy and descendants

  Available Information:
  {person_summary}
  {timeline_overview}
  {relationship_notes}
  {source_notes}
```

#### Example 3: Concise Summary Style

```yaml
# config/prompts/custom/biography.yaml

template: |
  Create a concise biographical summary (200-300 words).

  Include:
  - Birth (date, place, parents)
  - Key life events (marriage, children, occupation, migration)
  - Death (date, place, age)
  - Legacy (2-3 sentences)

  Data:
  {person_summary}
  {timeline_overview}
```

#### Example 4: Provider-Specific Optimization

```yaml
# config/prompts/custom/quality.yaml

# Default for all providers
template: |
  Analyze RootsMagic data quality issues.
  Dataset: {quality_summary}
  Critical Issues: {critical_issues}
  ...

provider_overrides:
  # Anthropic: Detailed analysis with research suggestions
  anthropic:
    template: |
      You are a genealogical data quality expert.
      Provide comprehensive analysis with:
      1. Issue categorization by severity
      2. Genealogical impact assessment
      3. Specific remediation steps
      4. Research strategies for resolution
      5. Estimated effort for each fix

      Dataset: {quality_summary}
      ...

  # Ollama: Simplified analysis
  ollama:
    template: |
      List data quality issues and fixes.
      For each issue: what's wrong, why it matters, how to fix it.

      Database: {quality_summary}
      Critical: {critical_issues}
      ...
```

### Prompt Template Variables

Each prompt type expects specific variables:

**Biography Prompt:**
- `{person_summary}` - Name, dates, parents
- `{timeline_overview}` - Life events chronology
- `{early_life_overview}` - Birth/childhood context
- `{family_overview}` - Spouse, children
- `{sibling_summary}` - Birth order, relationships
- `{relationship_notes}` - Key relationships
- `{family_loss_notes}` - Deaths in family
- `{source_notes}` - Citation information

**Quality Prompt:**
- `{quality_summary}` - Database statistics
- `{critical_issues}` - Critical severity issues
- `{high_issues}` - High severity issues
- `{medium_issues}` - Medium severity issues
- `{low_issues}` - Low severity issues

**Q&A Prompt:**
- `{question}` - User's question
- `{context_snippets}` - Relevant database records

**Timeline Prompt:**
- `{person_name}` - Subject name
- `{events_json}` - Life events (JSON format)

### Testing Custom Prompts

**Compare default vs custom:**

```bash
# Use default prompt
uv run rmagent bio 1 --output default.md

# Copy and edit to custom
cp config/prompts/biography.yaml config/prompts/custom/biography.yaml
nano config/prompts/custom/biography.yaml

# Use custom prompt
uv run rmagent bio 1 --output custom.md

# Compare outputs
diff default.md custom.md
```

**Test with different providers:**

```bash
# Test Anthropic
DEFAULT_LLM_PROVIDER=anthropic uv run rmagent bio 1 --output anthropic.md

# Test OpenAI
DEFAULT_LLM_PROVIDER=openai uv run rmagent bio 1 --output openai.md

# Test Ollama
DEFAULT_LLM_PROVIDER=ollama uv run rmagent bio 1 --output ollama.md
```

### Prompt Version Control

**Best Practices:**

1. **Don't commit custom prompts:** `config/prompts/custom/` is in `.gitignore`
2. **Document your customizations:** Keep notes on why you changed prompts
3. **Test thoroughly:** Verify output quality before relying on custom prompts
4. **Share carefully:** Custom prompts may contain personal style preferences

**Sharing Custom Prompts:**

```bash
# Export your custom prompt
cp config/prompts/custom/biography.yaml ~/my-custom-bio-prompt.yaml

# Share with collaborators
# They can import it as:
cp ~/my-custom-bio-prompt.yaml config/prompts/custom/biography.yaml
```

### Troubleshooting Prompts

**Problem:** Custom prompt not loading

```bash
# Check file location
ls -la config/prompts/custom/biography.yaml

# Verify YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config/prompts/custom/biography.yaml'))"
```

**Problem:** Provider-specific variant not working

Check that provider name matches exactly:
- ✅ `anthropic` (lowercase)
- ❌ `Anthropic` (incorrect)
- ✅ `openai`
- ❌ `OpenAI` (incorrect)
- ✅ `ollama`
- ❌ `Ollama` (incorrect)

**Problem:** Missing template variables

Ensure all required variables are in your custom prompt:

```yaml
# Biography requires all 8 variables:
template: |
  {person_summary}
  {timeline_overview}
  {early_life_overview}
  {family_overview}
  {sibling_summary}
  {relationship_notes}
  {family_loss_notes}
  {source_notes}
```

**Problem:** LLM output quality degraded

- Try reverting to default prompt
- Compare outputs side-by-side
- Simplify custom prompt incrementally
- Test with different providers

---

## Configuration Examples

### Example 1: Development Configuration

```bash
# config/.env - Development setup

# LLM Provider (using Ollama for cost-free development)
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=3000

# Database
RM_DATABASE_PATH=data/test-database.rmtree
SQLITE_ICU_EXTENSION=./sqlite-extension/icu.dylib

# Output
OUTPUT_DIR=output
EXPORT_DIR=exports

# Privacy (permissive for testing)
RESPECT_PRIVATE_FLAG=false
APPLY_110_YEAR_RULE=false

# Logging (verbose)
LOG_LEVEL=DEBUG
LOG_FILE=rmtool.log
LLM_DEBUG_LOG_FILE=logs/llm_debug.jsonl

# Citation
DEFAULT_CITATION_STYLE=footnote
```

### Example 2: Production Configuration (Anthropic)

```bash
# config/.env - Production setup

# LLM Provider (Anthropic Claude)
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=3000

# Database
RM_DATABASE_PATH=/home/genealogy/databases/family-tree.rmtree
SQLITE_ICU_EXTENSION=./sqlite-extension/icu.so

# Output
OUTPUT_DIR=/var/www/genealogy/output
EXPORT_DIR=/var/www/genealogy/hugo/content

# Privacy (strict for public sharing)
RESPECT_PRIVATE_FLAG=true
APPLY_110_YEAR_RULE=true

# Logging (normal)
LOG_LEVEL=INFO
LOG_FILE=/var/log/rmtool/app.log
LLM_DEBUG_LOG_FILE=/var/log/rmtool/llm_debug.jsonl

# Citation
DEFAULT_CITATION_STYLE=footnote
```

### Example 3: Cost-Optimized Configuration (OpenAI)

```bash
# config/.env - Cost-optimized setup

# LLM Provider (OpenAI GPT-4o-mini for low cost)
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2000  # Lower limit to reduce costs

# Database
RM_DATABASE_PATH=data/genealogy.rmtree
SQLITE_ICU_EXTENSION=./sqlite-extension/icu.dylib

# Output
OUTPUT_DIR=output
EXPORT_DIR=exports

# Privacy
RESPECT_PRIVATE_FLAG=true
APPLY_110_YEAR_RULE=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=rmtool.log
LLM_DEBUG_LOG_FILE=logs/llm_debug.jsonl

# Citation
DEFAULT_CITATION_STYLE=footnote
```

### Example 4: Multi-Provider Configuration

You can maintain multiple config files and switch between them:

```bash
# config/.env.anthropic
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
# ... other settings ...

# config/.env.openai
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_MODEL=gpt-4o-mini
# ... other settings ...

# config/.env.ollama
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
# ... other settings ...
```

**Switch providers:**

```bash
# Use Anthropic
cp config/.env.anthropic config/.env

# Use OpenAI
cp config/.env.openai config/.env

# Use Ollama
cp config/.env.ollama config/.env
```

---

## Configuration Validation

### Check Current Configuration

```python
# test_config.py
from rmagent.config.config import load_app_config

config = load_app_config()

print(f"Database: {config.database.database_path}")
print(f"Provider: {config.llm.default_provider}")
print(f"Model: {config.llm.anthropic_model or config.llm.openai_model or config.llm.ollama_model}")
print(f"Temperature: {config.llm.temperature}")
print(f"Max Tokens: {config.llm.max_tokens}")
print(f"Log Level: {config.logging.log_level}")
```

### Validate LLM Provider

```bash
# Test Anthropic
uv run rmagent ask "Say 'test successful'"

# Test OpenAI
uv run rmagent --llm-provider openai ask "Say 'test successful'"

# Test Ollama
uv run rmagent --llm-provider ollama ask "Say 'test successful'"
```

---

## Next Steps

- **Usage Guide:** See `USAGE.md` for command reference
- **Examples:** See `EXAMPLES.md` for real-world configurations
- **FAQ:** See `FAQ.md` for troubleshooting configuration issues

---

**Questions?** Check `FAQ.md` or open an issue on GitHub.
