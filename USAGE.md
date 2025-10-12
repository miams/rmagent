# Usage Guide - RMAgent

Complete command-line interface reference for RMAgent.

## Table of Contents

- [Command Overview](#command-overview)
- [Global Options](#global-options)
- [Person Command](#person-command)
- [Biography Command](#biography-command)
- [Quality Command](#quality-command)
- [Ask Command](#ask-command)
- [Timeline Command](#timeline-command)
- [Export Command](#export-command)
- [Search Command](#search-command)
- [Common Workflows](#common-workflows)
- [Tips & Best Practices](#tips--best-practices)

---

## Command Overview

RMAgent provides 7 main commands for interacting with your RootsMagic database:

```bash
# Using uv (default project workflow)
uv run rmagent [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]

# Using a local Python interpreter (no uv)
python -m rmagent.cli.main [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

| Command | Purpose | Requires LLM |
|---------|---------|--------------|
| `person` | Query person information | No |
| `bio` | Generate biography | Optional |
| `quality` | Run data quality checks | No |
| `ask` | Ask questions about the database | Yes |
| `timeline` | Generate interactive timeline | No |
| `export` | Export to Hugo blog format | Optional |
| `search` | Search database by name/place | No |

---

## Global Options

These options work with all commands:

```bash
uv run rmagent [OPTIONS] COMMAND [ARGS]

Options:
  --database PATH         Path to RootsMagic database (.rmtree)
                         Overrides RM_DATABASE_PATH in config/.env

  --llm-provider TEXT    LLM provider: anthropic, openai, or ollama
                         Overrides DEFAULT_LLM_PROVIDER in config/.env

  --verbose              Enable verbose logging
                         Shows detailed execution information

  --help                 Show help message and exit
  --version              Show version and exit
```

### Examples

```bash
# Use alternative database
uv run rmagent --database data/other.rmtree person 1

# Use different LLM provider
uv run rmagent --llm-provider openai bio 1

# Enable verbose logging
uv run rmagent --verbose quality

# Show version
uv run rmagent --version

# Same commands without uv (activate .venv first)
python -m rmagent.cli.main --version
```

### Shell autocompletion

The CLI ships with a `completion` helper that prints shell-specific completion scripts. Install it once per machine:

```bash
# Bash
python -m rmagent.cli.main completion bash > ~/.config/bash_completion/rmagent.bash
source ~/.config/bash_completion/rmagent.bash

# Zsh
python -m rmagent.cli.main completion zsh > "${ZDOTDIR:-$HOME}/.zfunc/_rmagent"
autoload -U compinit && compinit

# Fish
python -m rmagent.cli.main completion fish > ~/.config/fish/completions/rmagent.fish

# PowerShell
python -m rmagent.cli.main completion powershell | Out-String | Invoke-Expression
```

Once installed, press `Tab` to complete command names, options, and subcommands.

---

## Person Command

Query and display information about a person.

### Basic Usage

```bash
uv run rmagent person <PERSON_ID> [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--events` | Show all events for the person | False |
| `--family` | Show immediate family (parents, spouses, children) | False |
| `--ancestors` | Show ancestor tree | False |
| `--generations N` | Number of ancestor generations to show | 3 |
| `--descendants` | Show descendant tree | False |

### Examples

#### Basic Person Information

```bash
uv run rmagent person 1
```

**Output:**
```
📋 Person: Michael Dorsey Iams (1968-)

PersonID: 1
Sex: Male
Living: Yes
Birth: 30 Apr 1968 in Palo Alto, California
```

#### Show All Events

```bash
uv run rmagent person 1 --events
```

**Output:**
```
📋 Person: Michael Dorsey Iams (1968-)
─────────────────────────────────────────

Events:
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Date      ┃ Type         ┃ Place                  ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 30 Apr 68 │ Birth        │ Palo Alto, California  │
│ 1988      │ Education    │ Tucson, Arizona        │
│ 29 May 17 │ DNA test     │                        │
│ 2008      │ Genealogist  │                        │
└───────────┴──────────────┴────────────────────────┘
```

#### Show Immediate Family

```bash
uv run rmagent person 1 --family
```

**Output:**
```
📋 Person: Michael Dorsey Iams (1968-)
─────────────────────────────────────────

Family:
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Relation ┃ Name                  ┃ Birth-Death  ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Father   │ Donald Richard Iams   │ 1937-2017    │
│ Mother   │ Gail Cynthia Shepherd │ 1943-        │
│ Spouse   │ Jennifer L. Cubbage   │ 1971-        │
│ Child    │ Elena Dorsey Iams     │ 2001-        │
│ Child    │ Natalie Grace Iams    │ 2004-        │
└──────────┴───────────────────────┴──────────────┘
```

#### Show Ancestors (3 Generations)

```bash
uv run rmagent person 1 --ancestors --generations 3
```

Shows direct ancestors for 3 generations (parents, grandparents, great-grandparents).

#### Show Descendants

```bash
uv run rmagent person 1 --descendants
```

Shows all descendants (children, grandchildren, etc.).

---

## Biography Command

Generate biographical narratives about a person.

### Basic Usage

```bash
uv run rmagent bio <PERSON_ID> [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--length` | Biography length: short, standard, comprehensive | standard |
| `--citation-style` | Citation style: footnote, parenthetical, narrative | footnote |
| `--output PATH` | Write to file instead of stdout | - |
| `--no-ai` | Use template-based generation (no LLM required) | False |
| `--no-sources` | Exclude sources section | False |

### Length Options

- **short:** 2-3 paragraphs, key facts only (~300 words)
- **standard:** 5-7 paragraphs, complete narrative (~800 words)
- **comprehensive:** 9+ sections, detailed analysis (~1500+ words)

### Citation Styles

- **footnote:** `John was born in 1850.[1]`
- **parenthetical:** `John was born in 1850 (Smith 2020, p. 45).`
- **narrative:** `According to Smith's research, John was born in 1850.`

### Examples

#### Basic Biography (AI-Powered)

```bash
uv run rmagent bio 1
```

Generates standard-length biography using AI.

#### Template-Based Biography (No AI)

```bash
uv run rmagent bio 1 --no-ai
```

Generates biography using templates only (no LLM API call required).

#### Short Biography

```bash
uv run rmagent bio 1 --length short
```

#### Comprehensive Biography

```bash
uv run rmagent bio 1 --length comprehensive --output bio_comprehensive.md
```

#### Different Citation Styles

```bash
# Footnote style (default)
uv run rmagent bio 1 --citation-style footnote

# Parenthetical style
uv run rmagent bio 1 --citation-style parenthetical

# Narrative style
uv run rmagent bio 1 --citation-style narrative
```

#### Save to File

```bash
uv run rmagent bio 1 --output biographies/john_smith.md
```

#### Without Sources Section

```bash
uv run rmagent bio 1 --no-sources
```

---

## Quality Command

Run data quality validation checks on your database.

### Basic Usage

```bash
uv run rmagent quality [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--category` | Filter by category (see below) | all |
| `--severity` | Filter by severity: critical, high, medium, low | all |
| `--format` | Output format: markdown, html, csv | markdown |
| `--output PATH` | Write to file instead of stdout | - |

### Categories

- `required` - Required Field Combinations (5 rules)
- `logical` - Logical Consistency (6 rules)
- `integrity` - Referential Integrity (4 rules)
- `sources` - Source Documentation Quality (3 rules)
- `dates` - Date Validity (3 rules)
- `values` - Value Range Constraints (4 rules)

### Examples

#### Run All Quality Checks

```bash
uv run rmagent quality
```

**Output:**
```
📊 Data Quality Summary

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric          ┃  Count ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Total People    │ 11,571 │
│ Total Events    │ 29,543 │
│ Total Sources   │    337 │
│ Total Citations │ 10,838 │
└─────────────────┴────────┘

┏━━━━━━━━━━━┳━━━━━━━━┓
┃ Severity  ┃  Count ┃
┡━━━━━━━━━━━╇━━━━━━━━┩
│ 🔴 Critical │      7 │
│ 🟠 High     │ 32,665 │
│ 🟡 Medium   │ 15,643 │
│ 🟢 Low      │    742 │
└───────────┴────────┘

⚠️  Total Issues: 49,057
```

#### Filter by Severity

```bash
# Show only critical issues
uv run rmagent quality --severity critical

# Show high priority issues
uv run rmagent quality --severity high
```

#### Filter by Category

```bash
# Check logical consistency only
uv run rmagent quality --category logical

# Check source documentation
uv run rmagent quality --category sources

# Check date validity
uv run rmagent quality --category dates
```

#### Generate Different Formats

```bash
# Markdown report
uv run rmagent quality --format markdown --output quality_report.md

# HTML report
uv run rmagent quality --format html --output quality_report.html

# CSV for spreadsheet analysis
uv run rmagent quality --format csv --output quality_issues.csv
```

#### Combined Filters

```bash
# Critical logical consistency issues
uv run rmagent quality --category logical --severity critical

# High severity source quality issues
uv run rmagent quality --category sources --severity high --output source_issues.md
```

---

## Ask Command

Interactive Q&A about your database using AI.

### Basic Usage

```bash
uv run rmagent ask "<QUESTION>" [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--interactive` | Enter conversation mode (multiple questions) | False |

### Important Notes

- **Requires LLM provider:** This command always requires an LLM API key
- **Conversation memory:** The agent maintains context across questions in interactive mode
- **Database queries:** The AI can query your database to answer questions

### Examples

#### Single Question

```bash
uv run rmagent ask "Who were John Smith's parents?"
```

**Output:**
```
⠋ Searching database...

John Smith's parents were:

👨 Father: William Smith (1820-1890)
  - Born: 15 Mar 1820 in Maryland
  - Died: 22 Nov 1890 in Pennsylvania

👩 Mother: Mary Jones (1825-1895)
  - Born: 3 Jul 1825 in Virginia
  - Died: 10 Jan 1895 in Pennsylvania

Source: FamilyTable (FamilyID: 145), PersonTable
```

#### More Examples

```bash
# Ask about family relationships
uv run rmagent ask "How many children did William Smith have?"

# Ask about locations
uv run rmagent ask "Which families lived in Baltimore, Maryland?"

# Ask about time periods
uv run rmagent ask "Show me all births between 1850 and 1860"

# Ask about sources
uv run rmagent ask "What census records do we have for the Smith family?"
```

#### Interactive Mode

```bash
uv run rmagent ask --interactive
```

**Output:**
```
🤖 RMAgent Interactive Q&A
Type 'quit' or 'exit' to end the session.

You: Who were John Smith's parents?
Assistant: John Smith's parents were William Smith (1820-1890)...

You: When did William die?
Assistant: William Smith died on 22 Nov 1890 in Pennsylvania...

You: exit
Goodbye!
```

---

## Timeline Command

Generate interactive timelines in TimelineJS3 format.

### Basic Usage

```bash
uv run rmagent timeline <PERSON_ID> [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--format` | Output format: json, html | json |
| `--output PATH` | Write to file instead of stdout | - |
| `--group-by-phase` | Group events by life phases | False |
| `--include-family` | Include spouse/children events | False |

### Formats

- **json:** TimelineJS3 JSON format (for embedding in websites)
- **html:** Standalone HTML viewer (open in browser)

### Life Phases (with --group-by-phase)

- Early Life (0-17 years)
- Education (college years)
- Early Career (20s-30s)
- Family Formation (marriage, children)
- Mid Career (40s-50s)
- Later Life (60s+)
- Death & Legacy

### Examples

#### Basic Timeline (JSON)

```bash
uv run rmagent timeline 1 --output timeline.json
```

Creates `timeline.json` that can be embedded using TimelineJS3 library.

#### Standalone HTML Viewer

```bash
uv run rmagent timeline 1 --format html --output timeline.html
```

Creates standalone HTML file. Open `timeline.html` in any web browser for interactive viewing.

#### Group by Life Phases

```bash
uv run rmagent timeline 1 --group-by-phase --output timeline.json
```

Events are color-coded and grouped by life phases.

#### Include Family Events

```bash
uv run rmagent timeline 1 --include-family --output timeline.html
```

Includes events for spouse and children alongside the person's events.

#### Full Featured Timeline

```bash
uv run rmagent timeline 1 \
  --format html \
  --group-by-phase \
  --include-family \
  --output john_smith_timeline.html
```

---

## Export Command

Export biographies to Hugo blog format.

### Basic Usage

```bash
uv run rmagent export hugo <PERSON_ID> [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output-dir PATH` | Output directory | exports |
| `--bio-length` | Biography length: short, standard, comprehensive | standard |
| `--include-timeline` | Include timeline files | True |
| `--media-base-path` | Base path for media URLs | /media/ |
| `--batch-ids` | Comma-separated list of PersonIDs | - |
| `--all` | Export all persons (use with caution!) | False |

### Output Files

For each person, creates:
- `{person-name}.md` - Hugo blog post with YAML front matter
- `static/timelines/{person-name}.json` - Timeline JSON (if --include-timeline)
- `static/timelines/{person-name}.html` - Timeline HTML (if --include-timeline)

### Examples

#### Export Single Person

```bash
uv run rmagent export hugo 1 --output-dir content/people
```

Creates `content/people/john-smith.md`

#### Export with Comprehensive Biography

```bash
uv run rmagent export hugo 1 \
  --output-dir content/people \
  --bio-length comprehensive
```

#### Export Multiple People (Batch)

```bash
uv run rmagent export hugo \
  --batch-ids 1,2,3,4,5 \
  --output-dir content/people
```

Creates 5 blog posts and generates an index page.

#### Export All Persons

```bash
# WARNING: This may take a long time for large databases!
uv run rmagent export hugo --all --output-dir content/people
```

#### Without Timeline

```bash
uv run rmagent export hugo 1 \
  --output-dir content/people \
  --include-timeline=false
```

#### Custom Media Base Path

```bash
uv run rmagent export hugo 1 \
  --output-dir content/people \
  --media-base-path /static/genealogy-photos/
```

### Hugo Integration

The exported files are ready for Hugo static site generator:

1. Place exported `.md` files in `content/people/`
2. Place timeline files in `static/timelines/`
3. Run `hugo server` to preview
4. Run `hugo` to build the site

---

## Search Command

Search your database by name or place.

### Basic Usage

```bash
uv run rmagent search [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--name TEXT` | Search by name (surname or full name) | - |
| `--place TEXT` | Search by place name | - |
| `--limit N` | Maximum results to return | 10000 |
| `--exact` | Disable phonetic matching | False |
| `--married-name` | Include married surnames for women | False |

### Search Types

- **Name Search:** Searches primary and alternate names with phonetic (Metaphone) matching
- **Surname Variations:** Use bracket syntax `[variant]` or `[ALL]` for multiple variations
- **Married Names:** Use `--married-name` to find women by spouse surnames
- **Place Search:** Searches all place names with LIKE pattern matching
- **Exact Match:** Uses exact string matching (no phonetics)

### Surname Variation Syntax

Use bracket syntax to search multiple surname spellings:

- **Single variation:** `"John Iiams [Ijams]"` → searches "John Iiams" and "John Ijams"
- **Multiple variations:** `"John Iams [Ijams] [Imes]"` → searches "John Iams", "John Ijams", "John Imes"
- **[ALL] keyword:** `"John [ALL]"` → searches all configured variants

**Configure variants** in `config/.env`:
```bash
SURNAME_VARIANTS_ALL=Iams,Iames,Iiams,Iiames,Ijams,Ijames,Imes,Eimes
```

### Examples

#### Search by Surname

```bash
uv run rmagent search --name "Smith"
```

**Output:**
```
🔍 Found 247 person(s) matching 'Smith':
────────────────────────────────────────────────────────────
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID       ┃ Name               ┃ Birth      ┃ Death      ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 145      │ John Smith         │ 1825       │ 1890       │
│ 146      │ William Smith      │ 1850       │ 1920       │
│ 147      │ Mary Smith         │ 1855       │ 1932       │
│ ...      │ ...                │ ...        │ ...        │
└──────────┴────────────────────┴────────────┴────────────┘
```

#### Search by Full Name

```bash
uv run rmagent search --name "John Smith"
```

Searches for people with given name "John" and surname "Smith".

#### Search with Surname Variations

```bash
# Search two surname spellings
uv run rmagent search --name "John Iiams [Ijams]"
```

**Output:**
```
Searching 2 name variations...

🔍 Found 82 person(s) matching 'John Iiams [Ijams]':
────────────────────────────────────────────────────────────
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID       ┃ Name               ┃ Birth      ┃ Death      ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 85       │ John Iiams         │ 1816       │ 1878       │
│ 106      │ John Iiams         │ 1782       │ 1827       │
│ 501      │ John Iiams         │ 1747       │ 1785       │
│ 3916     │ John Ijams         │ 1825       │ 1890       │
│ ...      │ ...                │ ...        │ ...        │
└──────────┴────────────────────┴────────────┴────────────┘
```

```bash
# Search multiple variations
uv run rmagent search --name "John Iams [Ijams] [Imes]"
```

Searches for "John Iams", "John Ijams", and "John Imes".

```bash
# Search ALL configured variants
uv run rmagent search --name "John [ALL]"
```

Searches for all 8 configured surname variants (Iams, Iames, Iiams, Iiames, Ijams, Ijames, Imes, Eimes).

#### Search by Place

```bash
uv run rmagent search --place "Maryland"
```

Finds all people with events in Maryland.

#### Limit Results

```bash
uv run rmagent search --name "Smith" --limit 10
```

Returns only the first 10 matches.

#### Exact Match (No Phonetics)

```bash
uv run rmagent search --name "Smith" --exact
```

Uses exact string matching instead of phonetic (Metaphone) matching.

#### Combined Search

```bash
# Find Smiths in Maryland (first 20 results)
uv run rmagent search --name "Smith" --place "Maryland" --limit 20
```

---

## Common Workflows

### Workflow 1: Research a Single Person

```bash
# 1. Find the person
uv run rmagent search --name "John Smith"

# 2. View detailed information (use PersonID from search)
uv run rmagent person 145 --events --family

# 3. Generate biography
uv run rmagent bio 145 --length comprehensive --output john_smith_bio.md

# 4. Create timeline
uv run rmagent timeline 145 --format html --group-by-phase --output john_smith_timeline.html

# 5. Export to Hugo
uv run rmagent export hugo 145 --output-dir content/people
```

### Workflow 2: Data Quality Assessment

```bash
# 1. Run complete quality check
uv run rmagent quality --output quality_full.md

# 2. Review critical issues
uv run rmagent quality --severity critical --output quality_critical.md

# 3. Check logical consistency
uv run rmagent quality --category logical --severity high

# 4. Generate CSV for spreadsheet analysis
uv run rmagent quality --format csv --output quality_issues.csv
```

### Workflow 3: Batch Biography Generation

```bash
# 1. Search for family surname
uv run rmagent search --name "Smith"

# 2. Export multiple biographies
uv run rmagent export hugo --batch-ids 145,146,147,148,149 --output-dir content/people

# 3. Verify exports
ls -l content/people/
ls -l static/timelines/
```

### Workflow 4: Interactive Research Session

```bash
# Start interactive Q&A
uv run rmagent ask --interactive

# Example questions:
# > Who were the children of John Smith?
# > When did they get married?
# > Where did the Smith family live in 1880?
# > What census records do we have?
# > exit
```

---

## Tips & Best Practices

### Performance Tips

1. **Use --no-ai for testing:** Test biography generation without LLM calls:
   ```bash
   uv run rmagent bio 1 --no-ai
   ```

2. **Limit search results:** Use --limit to avoid overwhelming output:
   ```bash
   uv run rmagent search --name "Smith" --limit 10
   ```

3. **Save output to files:** Redirect long output to files:
   ```bash
   uv run rmagent quality > quality_report.txt
   ```

### Cost Management

1. **Use template-based biographies:** Save API costs with --no-ai
2. **Use Ollama for testing:** Free local LLM for development
3. **Cache LLM responses:** RMAgent logs all LLM calls to `logs/llm_debug.jsonl`

### Data Quality

1. **Run quality checks regularly:** Identify issues early
2. **Fix critical issues first:** Focus on `--severity critical` first
3. **Export to CSV:** Easier to review in spreadsheet software

### Biography Quality

1. **Use comprehensive length for featured people:**
   ```bash
   uv run rmagent bio 1 --length comprehensive
   ```

2. **Choose appropriate citation style:**
   - Academic: `--citation-style footnote`
   - Narrative: `--citation-style narrative`

3. **Review AI-generated content:** Always verify facts and sources

### Workflow Efficiency

1. **Create shell scripts for common tasks:**
   ```bash
   #!/bin/bash
   # generate_family_biographies.sh
   for id in 145 146 147 148 149; do
     uv run rmagent bio $id --output bio_$id.md
   done
   ```

2. **Use configuration file:** Set defaults in `config/.env` to avoid repetitive flags

3. **Combine commands with pipes:**
   ```bash
   uv run rmagent quality --format csv | grep "Critical"
   ```

---

## Next Steps

- **Configuration Guide:** See `CONFIGURATION.md` for advanced settings
- **Examples:** See `EXAMPLES.md` for real-world usage scenarios
- **FAQ:** See `FAQ.md` for troubleshooting
- **API Reference:** See `API.md` for programmatic usage

---

**Happy researching!** If you have questions, check `FAQ.md` or open an issue on GitHub.
