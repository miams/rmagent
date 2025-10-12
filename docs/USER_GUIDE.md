---
title: "RMAgent User Guide"
subtitle: "AI-Powered Genealogy Assistant for RootsMagic"
version: "0.2.0"
date: "October 12, 2025"
author: "RMAgent Project"
---

\newpage

# Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
   - [Basic Configuration](#basic-configuration)
   - [LLM Provider Setup](#llm-provider-setup)
   - [Advanced Settings](#advanced-settings)
4. [Using RMAgent](#using-rmAgent)
   - [Person Command](#person-command)
   - [Biography Command](#biography-command)
   - [Quality Command](#quality-command)
   - [Ask Command](#ask-command)
   - [Timeline Command](#timeline-command)
   - [Export Command](#export-command)
   - [Search Command](#search-command)
5. [Customizing Prompts](#customizing-prompts)
   - [Biography Prompts](#biography-prompts)
   - [Quality Analysis Prompts](#quality-analysis-prompts)
   - [Q&A Prompts](#qa-prompts)
6. [Troubleshooting](#troubleshooting)
7. [Quick Reference](#quick-reference)

\newpage

# Introduction

RMAgent is an AI-powered command-line tool that helps you analyze RootsMagic databases, generate biographical narratives, and conduct genealogical research. It combines the power of modern AI language models with deep integration into the RootsMagic 11 database structure.

## Key Features

- **Data Quality Analysis** - Run 24 validation rules to identify database issues
- **Biography Generation** - Create AI-generated biographical narratives with proper sourcing
- **Interactive Q&A** - Ask questions about people and families in your database
- **Timeline Creation** - Generate interactive timelines in TimelineJS3 format
- **Hugo Blog Export** - Export biographies as Hugo-compatible blog posts
- **Database Search** - Find people and places with phonetic name matching

## System Requirements

- **Python:** 3.11 or higher
- **Operating System:** macOS, Linux, or Windows
- **Database:** RootsMagic 11 (.rmtree file)
- **LLM Provider:** API key for Anthropic, OpenAI, or Ollama (local)

\newpage

# Installation

RMAgent uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

## Step 1: Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Step 2: Clone the Repository

```bash
# Using SSH (recommended)
git clone git@github.com:miams/rmagent.git
cd rmagent

# Or using HTTPS
git clone https://github.com/miams/rmagent.git
cd rmagent
```

## Step 3: Install Dependencies

```bash
# Install all dependencies
uv sync

# Install with development tools (optional)
uv sync --extra dev
```

This creates a virtual environment in `.venv/` and installs all required packages.

## Verify Installation

```bash
# Check version
uv run rmagent --version

# Display help
uv run rmagent --help
```

You should see output showing version 0.1.0 and available commands.

\newpage

# Configuration

## Basic Configuration

RMAgent uses environment variables stored in `config/.env` for configuration.

### Step 1: Copy Template

```bash
cp config/.env.example config/.env
```

### Step 2: Edit Configuration

Open `config/.env` in your text editor:

```bash
# Recommended: Use nano, vim, or your preferred editor
nano config/.env
```

### Step 3: Set Database Path

```bash
# Path to your RootsMagic database
RM_DATABASE_PATH=data/YourFamily.rmtree

# SQLite extension path (usually don't change this)
SQLITE_EXTENSION_PATH=sqlite-extension/icu.dylib
```

**Important:** Use the full path to your database or a path relative to the project root.

## LLM Provider Setup

Choose one of three LLM providers:

### Option 1: Anthropic Claude (Recommended)

Claude offers excellent genealogical reasoning and narrative generation.

```bash
# config/.env
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4096
```

**Get API Key:** https://console.anthropic.com/

**Recommended Models:**
- `claude-3-5-sonnet-20241022` - Best quality (default)
- `claude-3-haiku-20240307` - Faster, lower cost

### Option 2: OpenAI GPT-4

GPT-4 provides good quality with wide availability.

```bash
# config/.env
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4096
```

**Get API Key:** https://platform.openai.com/api-keys

**Recommended Models:**
- `gpt-4o` - Highest quality
- `gpt-4o-mini` - Good balance of speed and cost (default)
- `gpt-4-turbo` - Alternative high-quality option

### Option 3: Ollama (Local/Free)

Run models locally without API costs or internet connection.

```bash
# config/.env
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4096
```

**Setup Steps:**

1. Install Ollama: https://ollama.ai/download
2. Pull a model: `ollama pull llama3.1:8b`
3. Verify: `ollama list`

**Recommended Models:**
- `llama3.1:8b` - Good quality, moderate speed
- `llama3.1:70b` - Highest quality (requires 48GB+ RAM)
- `mistral:7b` - Faster alternative

## Advanced Settings

### Output Directories

```bash
# Where to save generated files
OUTPUT_DIR=output
EXPORT_DIR=exports
```

### Logging Configuration

```bash
# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# LLM debug log (captures all prompts/responses)
LLM_DEBUG_LOG_FILE=logs/llm_debug.jsonl
```

Set `LOG_LEVEL=DEBUG` to capture detailed prompt/response traces in JSON format for debugging.

### Privacy Settings

```bash
# Exclude living persons (110-year rule)
PRIVACY_EXCLUDE_LIVING=true

# Honor IsPrivate flags in database
PRIVACY_RESPECT_FLAGS=true
```

### Citation Defaults

```bash
# Default citation style: footnote, parenthetical, narrative
CITATION_STYLE=footnote

# Include sources section in biographies
CITATION_INCLUDE_SOURCES=true
```

\newpage

# Using RMAgent

All commands follow the pattern: `uv run rmagent [command] [options]`

## Person Command

Query information about a specific person.

### Basic Usage

```bash
# Display person summary
uv run rmagent person 1
```

**Output:**
```
📋 Person: Michael Dorsey Iams (1968–?)
──────────────────────────────────────
```

### With Events

```bash
# Show all life events
uv run rmagent person 1 --events
```

Shows events in a formatted table with dates, types, and places.

### With Family Information

```bash
# Show parents, spouses, and children
uv run rmagent person 1 --family
```

**Output includes:**
- Parents (father and mother)
- Spouses (all marriages)
- Children (sorted by birth)

### With Ancestors

```bash
# Show ancestor tree (default: 4 generations)
uv run rmagent person 1 --ancestors
```

### With Descendants

```bash
# Show descendant tree (default: 4 generations)
uv run rmagent person 1 --descendants
```

### Combined Options

```bash
# Show everything
uv run rmagent person 1 --events --family --ancestors --descendants
```

\newpage

## Biography Command

Generate biographical narratives from database information.

### Template-Based Biography (No AI)

```bash
# Generate without LLM (fastest, no API costs)
uv run rmagent bio 1 --no-ai
```

This creates a structured biography using templates only—no AI provider required.

### AI-Powered Biography

```bash
# Generate with AI enhancement (requires LLM provider)
uv run rmagent bio 1
```

### Biography Lengths

```bash
# Short biography (1-2 paragraphs)
uv run rmagent bio 1 --length short

# Standard biography (default, ~500 words)
uv run rmagent bio 1 --length standard

# Comprehensive biography (detailed, ~1500 words)
uv run rmagent bio 1 --length comprehensive
```

### Citation Styles

```bash
# Footnote style (numbered references)
uv run rmagent bio 1 --citation-style footnote

# Parenthetical style (author-date)
uv run rmagent bio 1 --citation-style parenthetical

# Narrative style (inline mentions)
uv run rmagent bio 1 --citation-style narrative
```

### Save to File

```bash
# Write biography to file
uv run rmagent bio 1 --output biographies/person-1.md

# Without sources section
uv run rmagent bio 1 --no-sources --output bio.md
```

### Example Output Structure

Biographies include 9 sections:

1. **Introduction** - Name, dates, key facts
2. **Early Life & Family Background** - Parents, birthplace, siblings
3. **Education & Training** - Schools, apprenticeships
4. **Career & Accomplishments** - Occupation, achievements
5. **Marriage & Family** - Spouse(s), children
6. **Later Life & Activities** - Post-career activities
7. **Death & Burial** - Death circumstances, burial location
8. **Legacy & Significance** - Impact, descendants
9. **Sources & Notes** - Citations and references

\newpage

## Quality Command

Run data quality validation on your database.

### Basic Quality Check

```bash
# Run all 24 validation rules
uv run rmagent quality
```

**Output includes:**
- Database statistics (people, events, sources, citations)
- Issues by severity (Critical, High, Medium, Low)
- Issues by category (6 categories)

### Filter by Severity

```bash
# Show only critical issues
uv run rmagent quality --severity critical

# Show high-priority issues
uv run rmagent quality --severity high

# Medium or low severity
uv run rmagent quality --severity medium
uv run rmagent quality --severity low
```

### Filter by Category

```bash
# Required field combinations
uv run rmagent quality --category required

# Logical consistency (dates, relationships)
uv run rmagent quality --category logical

# Referential integrity
uv run rmagent quality --category integrity

# Source documentation quality
uv run rmagent quality --category sources

# Date validity
uv run rmagent quality --category dates

# Value range constraints
uv run rmagent quality --category values
```

### Output Formats

```bash
# Markdown format (default, for documentation)
uv run rmagent quality --format markdown --output quality.md

# HTML format (for web viewing)
uv run rmagent quality --format html --output quality.html

# CSV format (for spreadsheet analysis)
uv run rmagent quality --format csv --output quality.csv
```

### Combined Filters

```bash
# Critical logical consistency issues
uv run rmagent quality --category logical --severity critical --output issues.md
```

### Sample Limit

```bash
# Limit sample issues shown per rule (default: 10)
uv run rmagent quality --sample-limit 5
```

\newpage

## Ask Command

Interactive Q&A about your genealogical database.

**Note:** This command requires an LLM provider (no `--no-ai` option).

### Single Question

```bash
# Ask one question
uv run rmagent ask "Who were John Smith's parents?"
```

**Example Output:**
```
John Smith's parents were:

👨 Father: William Smith (1820-1890)
  - Born: 15 March 1820 in Baltimore, Maryland
  - Died: 22 June 1890 in Baltimore, Maryland

👩 Mother: Mary Johnson (1825-1895)
  - Born: 8 May 1825 in Virginia
  - Died: 3 November 1895 in Baltimore, Maryland
```

### Interactive Conversation Mode

```bash
# Start interactive session
uv run rmagent ask --interactive
```

In interactive mode:
- Type questions and get answers
- Context is preserved across questions
- Type `exit`, `quit`, or press Ctrl+C to exit

**Example Session:**
```
> Who lived in Maryland?
[Lists people who lived in Maryland]

> Tell me more about the Smith family
[Provides Smith family details, remembering previous context]

> What occupations did they have?
[Answers about occupations, using conversation context]
```

### Question Examples

```bash
# Family relationships
uv run rmagent ask "How many children did Sarah Jones have?"

# Occupations and careers
uv run rmagent ask "What occupations are most common in the database?"

# Geographic patterns
uv run rmagent ask "Which families migrated from Virginia to Maryland?"

# Timeline questions
uv run rmagent ask "What events happened in 1850?"

# Source quality
uv run rmagent ask "Which people have the most documentation?"
```

\newpage

## Timeline Command

Generate interactive timelines in TimelineJS3 format.

### JSON Timeline (for embedding)

```bash
# Generate timeline JSON
uv run rmagent timeline 1 --output timeline.json
```

Use this format to embed timelines in websites or applications.

### HTML Timeline (standalone viewer)

```bash
# Generate standalone HTML viewer
uv run rmagent timeline 1 --format html --output timeline.html
```

Open `timeline.html` in a web browser for an interactive timeline.

### Group by Life Phases

```bash
# Group events by life stages
uv run rmagent timeline 1 --group-by-phase
```

**Life phases:**
- Early Life (birth - age 18)
- Education & Training (school years)
- Career & Work (employment period)
- Marriage & Family (family formation)
- Later Life (retirement)
- Death & Legacy

### Include Family Events

```bash
# Add spouse and children events
uv run rmagent timeline 1 --include-family
```

This creates a richer timeline showing family context.

### Combined Options

```bash
# Full-featured timeline
uv run rmagent timeline 1 \
  --format html \
  --group-by-phase \
  --include-family \
  --output person-1-timeline.html
```

### Viewing Timelines

**JSON Format:**
- Upload to https://timeline.knightlab.com
- Embed in your website
- Use with custom TimelineJS3 implementations

**HTML Format:**
- Double-click to open in browser
- Share the HTML file directly
- Works offline (uses CDN for TimelineJS library)

\newpage

## Export Command

Export biographies and timelines to Hugo static site format.

### Single Person Export

```bash
# Export one person to Hugo
uv run rmagent export hugo 1 --output-dir content/people
```

**Creates:**
- `content/people/person-1.md` - Biography with front matter
- `static/timelines/person-1.json` - Timeline data
- `static/timelines/person-1.html` - Timeline viewer

### Batch Export

```bash
# Export multiple people by ID
uv run rmagent export hugo --batch-ids 1,2,3,4,5 --output-dir content/people
```

### Export All People

```bash
# Export entire database (warning: may take a while)
uv run rmagent export hugo --all --output-dir content/people
```

**Note:** For large databases (>1000 people), consider batch export instead.

### Biography Length

```bash
# Short biographies for all
uv run rmagent export hugo --all --bio-length short --output-dir content

# Comprehensive biographies for select people
uv run rmagent export hugo --batch-ids 1,2,3 --bio-length comprehensive
```

### Timeline Options

```bash
# Export with timelines (default)
uv run rmagent export hugo 1 --include-timeline

# Export without timelines (faster)
uv run rmagent export hugo 1 --no-include-timeline
```

### Media Path Configuration

```bash
# Set base path for media files (default: /media/)
uv run rmagent export hugo 1 --media-base-path /static/images/
```

### Hugo Front Matter

Exported Markdown includes YAML front matter:

```yaml
---
title: "John Dorsey Iams"
date: 2025-10-10
categories: ["Iams Family"]
tags: ["Oklahoma", "Virginia", "1920s"]
person_id: 1
birth_year: 1921
death_year: 1996
---
```

### Using in Hugo

1. Copy exported files to your Hugo site
2. Ensure `content/people/` directory exists
3. Run `hugo server` to preview
4. Timelines reference: `{{< timeline src="/timelines/person-1.json" >}}`

\newpage

## Search Command

Search your database by name or place.

### Search by Name

```bash
# Search by surname
uv run rmagent search --name "Smith"

# Search by full name
uv run rmagent search --name "John Smith"
```

**Features:**
- Exact matching on surname and given name
- Automatic phonetic matching if no exact results
- Results show ID, full name, birth year, death year

### Phonetic Matching

RMAgent automatically uses Metaphone phonetic matching to find similar names:

```bash
# These might find "Smith":
uv run rmagent search --name "Smyth"
uv run rmagent search --name "Smythe"
```

To disable phonetic matching:

```bash
# Exact matches only
uv run rmagent search --name "Smith" --exact
```

### Search by Place

```bash
# Find all places containing "Maryland"
uv run rmagent search --place "Maryland"

# More specific
uv run rmagent search --place "Baltimore, Maryland"
```

### Limit Results

```bash
# Show maximum 10 results (default: 50)
uv run rmagent search --name "Smith" --limit 10
```

### Combined Search

```bash
# Search both names and places
uv run rmagent search --name "Jones" --place "Virginia" --limit 20
```

**Output:**
- Shows people matching "Jones"
- Shows places containing "Virginia"

### Example Output

```
🔍 Found 5 person(s) matching 'Smith':
────────────────────────────────────────────────────────────
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID       ┃ Name               ┃ Birth      ┃ Death      ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 234      │ Adelaide Smith     │ 1841       │ 1906       │
│ 567      │ Albert Henry Smith │ 1911       │ 1977       │
│ 890      │ Ann Smith          │ ?          │ ?          │
└──────────┴────────────────────┴────────────┴────────────┘
```

\newpage

# Customizing Prompts

RMAgent allows you to customize AI prompts for different workflows **without modifying code**. Prompts are stored as YAML files with support for provider-specific variants.

## Prompt System Overview

**Default Prompts:** Located in `config/prompts/`
- `biography.yaml` - Biography generation
- `quality.yaml` - Data quality analysis
- `qa.yaml` - Q&A conversations
- `timeline.yaml` - Timeline synthesis

**Custom Prompts:** Located in `config/prompts/custom/` (optional, not tracked in git)
- Override any default prompt
- Takes precedence over defaults
- Same YAML format

**Provider-Specific Variants:**
Each prompt can include optimizations for different LLM providers:
- **Anthropic Claude:** Detailed instructions, academic tone, complex reasoning
- **OpenAI GPT:** Direct instructions, efficient phrasing
- **Ollama (local):** Simpler prompts, concrete examples

## Biography Prompts

The biography prompt controls how AI generates biographical narratives.

### Location

File: `config/prompts/biography.yaml`

### Creating a Custom Biography Prompt

**Step 1: Create custom directory**

```bash
mkdir -p config/prompts/custom
```

**Step 2: Copy default prompt**

```bash
cp config/prompts/biography.yaml config/prompts/custom/biography.yaml
```

**Step 3: Edit with your preferred text editor**

```bash
nano config/prompts/custom/biography.yaml
```

**Step 4: Modify the template section**

```yaml
# config/prompts/custom/biography.yaml

key: biography
version: "2025-01-08"
description: "Custom biography generation"

# Your custom prompt template
template: |
  Write a genealogical biography in a narrative storytelling style.
  Focus on family relationships and historical context.

  Person Information:
  {person_summary}

  Life Events:
  {timeline_overview}

  [Your additional instructions here]
```

**Step 5: Test your custom prompt**

```bash
# Biography will automatically use your custom prompt
uv run rmagent bio 1 --output test.md
```

### Biography Prompt Customization Examples

#### Example 1: Academic Style

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

#### Example 2: Family History Style

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

### Template Variables Reference

The biography prompt receives these context variables:

- `{person_summary}` - Name, dates, parents
- `{timeline_overview}` - Life events chronology
- `{early_life_overview}` - Birth/childhood context
- `{family_overview}` - Spouse, children
- `{sibling_summary}` - Birth order, relationships
- `{relationship_notes}` - Key relationships
- `{family_loss_notes}` - Deaths in family
- `{source_notes}` - Citation information

### Testing Custom Prompts

Compare default vs custom output:

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

## Quality Analysis Prompts

Located in `config/prompts/quality.yaml`

Customize to change how data quality issues are analyzed and prioritized.

**To customize:**
```bash
cp config/prompts/quality.yaml config/prompts/custom/quality.yaml
nano config/prompts/custom/quality.yaml
```

## Q&A Prompts

Located in `config/prompts/qa.yaml`

Customize to change:
- Question interpretation style
- Answer format and structure
- Source attribution approach
- Conversation memory handling

**To customize:**
```bash
cp config/prompts/qa.yaml config/prompts/custom/qa.yaml
nano config/prompts/custom/qa.yaml
```

## Prompt Best Practices

1. **Be Specific** - Clear instructions produce better results
2. **Provide Examples** - Show desired output format
3. **Set Constraints** - Word count, style, structure
4. **Handle Uncertainty** - Define how to express unknown information
5. **Test Iteratively** - Small changes, test results, refine
6. **Version Control** - Keep old prompts commented for reference
7. **Document Changes** - Note why you made modifications

\newpage

# Troubleshooting

## Common Issues and Solutions

### Issue: "No database specified"

**Error:**
```
Error: No database specified. Use --database option or set RM_DATABASE_PATH in config/.env
```

**Solution:**
```bash
# Option 1: Set in config/.env
echo "RM_DATABASE_PATH=data/YourFamily.rmtree" >> config/.env

# Option 2: Use command-line option
uv run rmagent --database data/YourFamily.rmtree person 1
```

### Issue: "Failed to load RMNOCASE collation"

**Error:**
```
Error: Could not load SQLite extension
```

**Solution:**

1. Verify extension exists:
```bash
ls -la sqlite-extension/icu.dylib
```

2. Check configuration:
```bash
# config/.env
SQLITE_EXTENSION_PATH=sqlite-extension/icu.dylib
```

3. On Linux, you may need a different extension:
```bash
# Download or compile icu.so for Linux
SQLITE_EXTENSION_PATH=sqlite-extension/icu.so
```

### Issue: "API key not found"

**Error:**
```
Error: No API key found for provider 'anthropic'
```

**Solution:**

1. Verify API key in config/.env:
```bash
grep API_KEY config/.env
```

2. Ensure key is valid:
```bash
# Test Anthropic key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

3. Check provider spelling:
```bash
# config/.env - must match exactly
DEFAULT_LLM_PROVIDER=anthropic  # not "Anthropic" or "claude"
```

### Issue: "Person not found"

**Error:**
```
Error: Person 9999 not found
```

**Solution:**

Find valid person IDs:
```bash
# Search for people
uv run rmagent search --name "Smith"

# Or query database directly
sqlite3 data/YourFamily.rmtree "SELECT PersonID, Surname, Given FROM NameTable WHERE IsPrimary=1 LIMIT 10"
```

### Issue: Slow performance

**Symptoms:** Commands take a long time to execute

**Solutions:**

1. **Use --no-ai for biographies** (much faster):
```bash
uv run rmagent bio 1 --no-ai
```

2. **Limit search results**:
```bash
uv run rmagent search --name "Smith" --limit 10
```

3. **Use lighter LLM models**:
```bash
# config/.env
ANTHROPIC_MODEL=claude-3-haiku-20240307  # Faster than Sonnet
# or
OPENAI_MODEL=gpt-4o-mini  # Faster than gpt-4o
```

4. **Check database size**:
```bash
ls -lh data/YourFamily.rmtree
```

Large databases (>100MB) may need optimization.

### Issue: Biography lacks detail

**Symptoms:** Generated biographies are too brief or generic

**Solutions:**

1. **Use comprehensive length**:
```bash
uv run rmagent bio 1 --length comprehensive
```

2. **Check data quality**:
```bash
# Verify person has sufficient events and sources
uv run rmagent person 1 --events
uv run rmagent quality --severity high
```

3. **Increase LLM token limit**:
```bash
# config/.env
LLM_MAX_TOKENS=8192  # Allow longer outputs
```

4. **Customize biography prompt** (see Customizing Prompts section)

### Issue: Timeline not displaying

**Symptoms:** HTML timeline shows blank or error

**Solutions:**

1. **Check internet connection** - HTML timelines use CDN
2. **Verify JSON structure**:
```bash
# Check JSON is valid
python -m json.tool timeline.json
```

3. **Try regenerating**:
```bash
uv run rmagent timeline 1 --format html --output test.html
```

### Issue: Hugo export not working

**Symptoms:** Files not created or Hugo build fails

**Solutions:**

1. **Verify output directory exists**:
```bash
mkdir -p content/people
uv run rmagent export hugo 1 --output-dir content/people
```

2. **Check file permissions**:
```bash
ls -la content/people/
```

3. **Validate Markdown**:
```bash
# Check front matter is valid YAML
head -20 content/people/person-1.md
```

## Getting Help

### Debug Mode

Enable detailed logging:

```bash
# Set in config/.env
LOG_LEVEL=DEBUG
LLM_DEBUG_LOG_FILE=logs/llm_debug.jsonl

# Run command
uv run rmagent bio 1

# Check logs
tail -f logs/llm_debug.jsonl
```

### Test Database Connection

```bash
# Verify database can be opened
sqlite3 data/YourFamily.rmtree "SELECT COUNT(*) FROM PersonTable"
```

### Check Python Version

```bash
python --version  # Should be 3.11+
uv --version
```

### Report Issues

GitHub Issues: https://github.com/miams/rmagent/issues

Include:
- Command you ran
- Error message (full output)
- Operating system
- Python version
- Database size (number of people)

\newpage

# Quick Reference

## Command Syntax

```bash
uv run rmagent [OPTIONS] COMMAND [ARGS]
```

## Global Options

```
-d, --database PATH     Path to RootsMagic database
--llm-provider TEXT     LLM provider (anthropic/openai/ollama)
-v, --verbose          Enable verbose logging
--version              Show version
--help                 Show help
```

## Commands Summary

| Command | Purpose | Example |
|---------|---------|---------|
| `person` | Query person info | `uv run rmagent person 1 --events` |
| `bio` | Generate biography | `uv run rmagent bio 1 --length standard` |
| `quality` | Data quality checks | `uv run rmagent quality --severity critical` |
| `ask` | Interactive Q&A | `uv run rmagent ask "Who is person 1?"` |
| `timeline` | Generate timeline | `uv run rmagent timeline 1 --format html` |
| `export` | Export to Hugo | `uv run rmagent export hugo 1` |
| `search` | Search database | `uv run rmagent search --name "Smith"` |

## Configuration Quick Start

```bash
# 1. Copy template
cp config/.env.example config/.env

# 2. Edit configuration
nano config/.env

# 3. Set essentials
RM_DATABASE_PATH=data/YourFamily.rmtree
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 4. Test
uv run rmagent person 1
```

## Common Workflows

### Generate Complete Person Report

```bash
# All information for one person
uv run rmagent person 1 --events --family --ancestors > person-1.txt
uv run rmagent bio 1 --length comprehensive --output bio-1.md
uv run rmagent timeline 1 --format html --output timeline-1.html
```

### Data Quality Analysis

```bash
# Find critical issues
uv run rmagent quality --severity critical --output critical.md

# Check source quality
uv run rmagent quality --category sources --output sources.md

# Full report
uv run rmagent quality --format html --output quality-report.html
```

### Batch Hugo Export

```bash
# Export first 10 people
uv run rmagent export hugo --batch-ids 1,2,3,4,5,6,7,8,9,10 \
  --output-dir content/people \
  --bio-length standard \
  --include-timeline
```

### Research Workflow

```bash
# 1. Search for family
uv run rmagent search --name "Smith" --limit 20

# 2. Get details on person of interest
uv run rmagent person 234 --events --family

# 3. Ask questions
uv run rmagent ask "Tell me about the Smith family in Maryland"

# 4. Generate biography
uv run rmagent bio 234 --length comprehensive --output smith-bio.md
```

## File Locations

```
config/.env                   # Main configuration
logs/llm_debug.jsonl         # LLM debug logs
output/                      # Generated output files
exports/                     # Exported content
content/people/              # Hugo export location
static/timelines/            # Timeline files
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `RM_DATABASE_PATH` | - | Path to .rmtree file |
| `DEFAULT_LLM_PROVIDER` | - | anthropic/openai/ollama |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OLLAMA_MODEL` | llama3.1:8b | Ollama model name |
| `LLM_TEMPERATURE` | 0.2 | Creativity (0.0-1.0) |
| `LLM_MAX_TOKENS` | 4096 | Max response length |
| `LOG_LEVEL` | INFO | DEBUG/INFO/WARNING/ERROR |
| `OUTPUT_DIR` | output | Output directory |
| `EXPORT_DIR` | exports | Export directory |

## Tips & Tricks

### Use Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
alias rmag="uv run rmagent"
alias rmbio="uv run rmagent bio"
alias rmq="uv run rmagent quality"
```

Then use:
```bash
rmag person 1
rmbio 1 --length comprehensive
rmq --severity critical
```

### Batch Processing with Shell Scripts

```bash
#!/bin/bash
# generate-all-biographies.sh

for id in {1..100}; do
    echo "Processing person $id..."
    uv run rmagent bio $id --no-ai --output "bios/person-$id.md" 2>/dev/null
done
```

### Query Database Directly

```bash
# Find all people born in Maryland
sqlite3 data/YourFamily.rmtree \
  "SELECT p.PersonID, n.Surname, n.Given
   FROM PersonTable p
   JOIN NameTable n ON p.PersonID = n.OwnerID
   JOIN EventTable e ON p.PersonID = e.OwnerID
   JOIN PlaceTable pl ON e.PlaceID = pl.PlaceID
   WHERE e.EventType = 1
   AND pl.Name LIKE '%Maryland%'
   AND n.IsPrimary = 1"
```

### Monitor LLM Costs

```bash
# Check token usage in logs
grep -o '"total_tokens":[0-9]*' logs/llm_debug.jsonl | \
  awk -F: '{sum+=$2} END {print "Total tokens:", sum}'
```

---

**End of User Guide**

For more information:
- GitHub: https://github.com/miams/rmagent
- Documentation: https://github.com/miams/rmagent/tree/main/docs
- Issues: https://github.com/miams/rmagent/issues
