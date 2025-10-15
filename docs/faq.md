# Frequently Asked Questions (FAQ)

Common questions and troubleshooting for RMAgent.

## Table of Contents

- [General Questions](#general-questions)
- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Database Issues](#database-issues)
- [LLM Provider Issues](#llm-provider-issues)
- [Performance Issues](#performance-issues)
- [Output Quality Issues](#output-quality-issues)
- [Privacy & Ethics](#privacy--ethics)

---

## General Questions

### What is RMAgent?

RMAgent is an AI-powered command-line tool for analyzing RootsMagic databases, generating biographical narratives, and conducting genealogical research. It uses large language models (Claude, GPT, or local Llama) to create natural-language biographies and answer questions about your family tree.

### Do I need a RootsMagic subscription?

No. RMAgent works with RootsMagic database files (`.rmtree`), but you don't need an active RootsMagic subscription. You just need access to your database file.

### Which RootsMagic versions are supported?

Currently only **RootsMagic 11** is supported. The `.rmtree` database format is specific to RM11.

**Note:** Earlier versions (RM7, RM8, RM9, RM10) use different database formats and are not compatible.

### Do I need an AI API key?

**For most features: No.** You can use:
- Data quality checks (no AI required)
- Template-based biographies (`--no-ai` flag)
- Person queries
- Timeline generation
- Hugo exports

**For AI-powered features: Yes.** You need an API key for:
- AI-generated biographies
- Interactive Q&A (`ask` command)

**Cost-free option:** Use Ollama with local models (no API key needed).

### How much does it cost to use?

**Software:** RMAgent is free and open-source.

**LLM API Costs:**
- **Anthropic Claude:** ~$0.01-0.05 per biography (typical)
- **OpenAI GPT-4o-mini:** ~$0.005-0.02 per biography
- **Ollama:** Free (runs locally)

### Can I use this offline?

**Partial offline use:**
- Database queries: ✅ Yes (offline)
- Data quality checks: ✅ Yes (offline)
- Template biographies: ✅ Yes (offline)
- AI biographies: ❌ No (requires API call)
- Q&A: ❌ No (requires API call)

**Full offline use with Ollama:**
- Install Ollama and download models locally
- All features work offline

---

## Installation Issues

### Python version error: "requires Python >=3.11"

**Problem:** Your Python version is too old.

**Solution:**

```bash
# Check current version
python3 --version

# Install Python 3.11 or higher
# macOS
brew install python@3.11

# Linux
sudo apt install python3.11
```

### "uv: command not found"

**Problem:** uv is not installed or not in PATH.

**Solution:**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal
source ~/.bashrc  # or ~/.zshrc

# Verify
uv --version
```

**Alternative:** Use pip instead:

```bash
pip install -e .
```

### "Could not load ICU extension"

**Problem:** SQLite ICU extension not found or incompatible.

**Solution:**

**macOS:**
```bash
# Extension should be included
ls -l sqlite-extension/icu.dylib  # Verify file exists
```

**Linux:**
```bash
# You may need to compile the extension
sudo apt install libsqlite3-dev libicu-dev
cd sqlite-extension
# Follow compilation instructions in sqlite-extension/README.md
```

**Workaround:** Contact support if the extension won't load.

### Installation hangs during "uv sync"

**Problem:** Network issues or slow dependency resolution.

**Solution:**

```bash
# Try with verbose output
uv sync -v

# Try with pip instead
pip install -e .

# Check network connection
curl -I https://pypi.org/
```

---

## Configuration Issues

### "No module named 'rmagent'"

**Problem:** Package not installed or virtual environment not activated.

**Solution:**

**With uv:**
```bash
# Reinstall
uv sync

# Run with uv prefix
uv run rmagent person 1
```

**With pip:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Reinstall
pip install -e .

# Run
rmagent person 1
```

### "config/.env not found"

**Problem:** Configuration file doesn't exist.

**Solution:**

```bash
# Create from example
cp config/.env.example config/.env

# Edit with your settings
nano config/.env  # or use your text editor
```

### "AuthenticationError: Invalid API key"

**Problem:** LLM API key is incorrect, expired, or not set.

**Solution:**

1. Check your `config/.env` file:
   ```bash
   cat config/.env | grep API_KEY
   ```

2. Verify no extra spaces or quotes:
   ```bash
   # Wrong
   ANTHROPIC_API_KEY="sk-ant-xxxxx"  # Remove quotes
   ANTHROPIC_API_KEY= sk-ant-xxxxx   # Remove space

   # Correct
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   ```

3. Get a new API key:
   - Anthropic: https://console.anthropic.com/
   - OpenAI: https://platform.openai.com/

4. Check billing is enabled (Anthropic/OpenAI require valid payment method)

### Environment variables not loading

**Problem:** Config file exists but settings aren't applied.

**Solution:**

1. Verify file location:
   ```bash
   ls -l config/.env  # Must be in config/ directory
   ```

2. Check file contents:
   ```bash
   cat config/.env
   ```

3. Try absolute path:
   ```bash
   RM_DATABASE_PATH=/full/path/to/database.rmtree
   ```

4. Use command-line override:
   ```bash
   uv run rmagent --database /path/to/database.rmtree person 1
   ```

---

## Database Issues

### "FileNotFoundError: data/Iiams.rmtree not found"

**Problem:** Database file doesn't exist at specified path.

**Solution:**

1. Check file exists:
   ```bash
   ls -lh data/*.rmtree
   ```

2. Update `config/.env` with correct path:
   ```bash
   RM_DATABASE_PATH=data/your-actual-database.rmtree
   ```

3. Copy database to correct location:
   ```bash
   mkdir -p data
   cp /path/to/your/database.rmtree data/
   ```

### "database disk image is malformed"

**Problem:** Database file is corrupted.

**Solution:**

1. **Make a backup first:**
   ```bash
   cp data/database.rmtree data/database-backup.rmtree
   ```

2. Try opening in RootsMagic and run "Database Tools > Test Database Integrity"

3. If RootsMagic can repair it, export and reimport your data

4. Restore from backup if available

### "no such table: PersonTable"

**Problem:** Wrong database version or file is not a RootsMagic database.

**Solution:**

1. Verify it's a RootsMagic 11 database (.rmtree extension)

2. Check database in SQLite:
   ```bash
   sqlite3 data/database.rmtree ".tables"
   ```

   Should show tables like: `PersonTable`, `EventTable`, `NameTable`, etc.

3. If tables are missing, the file may be corrupted

### "RMNOCASE collation not found"

**Problem:** RMNOCASE collation not loaded (ICU extension issue).

**Solution:**

See "Could not load ICU extension" above.

---

## LLM Provider Issues

### Anthropic: "rate limit exceeded"

**Problem:** Too many API requests in short time.

**Solution:**

1. Wait a few seconds and retry

2. Reduce batch size:
   ```bash
   # Instead of exporting 100 people at once
   uv run rmagent export hugo --batch-ids 1,2,3,4,5
   # Process in smaller batches
   ```

3. Increase delay between requests (programmatic use only)

### OpenAI: "model not found"

**Problem:** Model name is incorrect or model is deprecated.

**Solution:**

1. Check current models at https://platform.openai.com/docs/models

2. Update `config/.env`:
   ```bash
   # If using old model name
   OPENAI_MODEL=gpt-4o-mini  # Current model
   ```

3. Common current models:
   - `gpt-4o-mini` (fast, cheap)
   - `gpt-4o` (balanced)
   - `gpt-5-chat-latest` (if you have access)

### Ollama: "Connection refused"

**Problem:** Ollama server not running.

**Solution:**

1. Start Ollama server:
   ```bash
   ollama serve
   ```

2. Verify it's running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. Check if model is downloaded:
   ```bash
   ollama list
   ```

4. Pull model if missing:
   ```bash
   ollama pull llama3.1
   ```

### Ollama: "model not found"

**Problem:** Requested model not downloaded.

**Solution:**

```bash
# List available models
ollama list

# Pull the model you need
ollama pull llama3.1

# Update config/.env
OLLAMA_MODEL=llama3.1
```

---

## Performance Issues

### Tests are very slow (>60 seconds)

**Problem:** Quality tests processing large database.

**Solution:**

**Already fixed in Phase 5!** The persistent caching system speeds this up dramatically:

```bash
# First run may be slow (builds cache)
uv run pytest tests/unit/test_quality.py  # ~40s

# Subsequent runs are fast (uses cache)
uv run pytest tests/unit/test_quality.py  # ~0.3s
```

Cache is automatically invalidated when database file changes.

### Biography generation is slow

**Problem:** LLM API latency.

**Solution:**

1. **Use faster model:**
   ```bash
   # OpenAI GPT-4o-mini is fastest
   OPENAI_MODEL=gpt-4o-mini
   ```

2. **Use Ollama locally:**
   ```bash
   # No network latency
   DEFAULT_LLM_PROVIDER=ollama
   ```

3. **Reduce max tokens:**
   ```bash
   LLM_MAX_TOKENS=2000  # Faster than 3000+
   ```

4. **Use template mode for testing:**
   ```bash
   uv run rmagent bio 1 --no-ai  # Instant, no API call
   ```

### Quality checks are slow on large databases

**Problem:** Processing tens of thousands of records.

**Solution:**

1. **Use category filters to check specific areas:**
   ```bash
   uv run rmagent quality --category logical  # Fast
   ```

2. **Cache results are automatic** (see above)

3. **Focus on high-severity issues:**
   ```bash
   uv run rmagent quality --severity critical  # Very fast
   ```

---

## Output Quality Issues

### Biographies are too short/generic

**Problem:** Not enough data in database or LLM parameters too restrictive.

**Solution:**

1. **Use comprehensive length:**
   ```bash
   uv run rmagent bio 1 --length comprehensive
   ```

2. **Increase max tokens:**
   ```bash
   LLM_MAX_TOKENS=4000  # Allow longer responses
   ```

3. **Increase temperature (more creative):**
   ```bash
   LLM_TEMPERATURE=0.5  # Default is 0.2
   ```

4. **Check database has sufficient data:**
   ```bash
   uv run rmagent person 1 --events --family
   ```

5. **Try different provider:**
   - Anthropic Claude generally produces better genealogical narratives
   - OpenAI GPT-4o-mini may be too concise

### Biographies contain factual errors

**Problem:** AI hallucination or database data quality issues.

**Solution:**

1. **Check source data:**
   ```bash
   uv run rmagent person 1 --events --family
   ```

2. **Run quality checks:**
   ```bash
   uv run rmagent quality --person 1  # Check for inconsistencies
   ```

3. **Lower temperature (more factual):**
   ```bash
   LLM_TEMPERATURE=0.1  # More deterministic
   ```

4. **Use template mode first to verify data:**
   ```bash
   uv run rmagent bio 1 --no-ai  # Pure database facts
   ```

5. **Always verify AI-generated content** before publishing

### Citations are missing or incorrect

**Problem:** Database missing source data or citation style issue.

**Solution:**

1. **Check source data in database:**
   ```bash
   # Run quality check for source documentation
   uv run rmagent quality --category sources
   ```

2. **Try different citation style:**
   ```bash
   uv run rmagent bio 1 --citation-style narrative  # More readable
   ```

3. **Check RootsMagic database has citations linked to events**

4. **Use footnote style for academic work:**
   ```bash
   uv run rmagent bio 1 --citation-style footnote
   ```

### Timeline is empty or missing events

**Problem:** Events missing dates or marked private.

**Solution:**

1. **Check person has dated events:**
   ```bash
   uv run rmagent person 1 --events
   ```

2. **Include family events:**
   ```bash
   uv run rmagent timeline 1 --include-family
   ```

3. **Check privacy settings:**
   - Events marked `IsPrivate=1` are excluded by default
   - Adjust `config/.env` if needed (see Privacy section)

4. **Verify dates are valid:**
   ```bash
   uv run rmagent quality --category dates
   ```

---

## Privacy & Ethics

### How do I protect living persons' privacy?

**Solution:**

1. **Enable privacy settings in `config/.env`:**
   ```bash
   RESPECT_PRIVATE_FLAG=true  # Honor IsPrivate flags
   APPLY_110_YEAR_RULE=true   # Protect recent living persons
   ```

2. **Mark people private in RootsMagic:**
   - Right-click person → Edit Person → Privacy tab → Check "Private"

3. **Review before publishing:**
   ```bash
   # Check what will be exported
   uv run rmagent bio 1  # Review content
   ```

### Does my data get sent to AI companies?

**Yes, when using cloud LLM providers (Anthropic, OpenAI):**
- Prompts (person data, events, places) are sent to API
- Responses are generated by their servers
- Follow their data retention policies

**No, when using Ollama:**
- Everything runs locally on your machine
- No data sent to external servers
- Complete privacy

**Recommendation:** Use Ollama for sensitive/private data.

### Can I use this for commercial genealogy services?

Yes, but:

1. **Software license:** Check LICENSE file (MIT license - generally permissive)

2. **LLM provider terms:**
   - Anthropic: Check https://www.anthropic.com/legal/consumer-terms
   - OpenAI: Check https://openai.com/policies/terms-of-use
   - Ollama: No restrictions (local)

3. **Verify AI-generated content:** Always review before publishing

4. **Respect copyright:** Source citations must be accurate

5. **Privacy laws:** Comply with GDPR, CCPA, etc.

### Should I trust AI-generated biographies?

**No - always verify!**

**Best practices:**

1. **Use AI as a writing assistant, not a source of truth**

2. **Verify all facts against database:**
   ```bash
   uv run rmagent person 1 --events --family
   ```

3. **Check for logical consistency:**
   ```bash
   uv run rmagent quality --category logical
   ```

4. **Review sources and citations**

5. **Use lower temperature for factual content:**
   ```bash
   LLM_TEMPERATURE=0.1  # More deterministic
   ```

6. **Compare with template output:**
   ```bash
   uv run rmagent bio 1 --no-ai  # Facts only
   uv run rmagent bio 1           # AI version
   ```

---

## Getting More Help

### Documentation

- **Installation:** `INSTALL.md`
- **Usage:** `USAGE.md`
- **Configuration:** `CONFIGURATION.md`
- **Examples:** `EXAMPLES.md`
- **User Guide:** `docs/USER_GUIDE.md`

### Community

- **GitHub Issues:** https://github.com/miams/rmagent/issues
- **Discussions:** https://github.com/miams/rmagent/discussions

### Reporting Bugs

When reporting bugs, include:

1. RMAgent version: `uv run rmagent --version`
2. Python version: `python3 --version`
3. Operating system
4. Full error message
5. Steps to reproduce
6. Contents of `config/.env` (remove API keys!)

### Feature Requests

Open an issue with:

1. Use case description
2. Expected behavior
3. Why existing features don't meet the need
4. Proposed solution (if any)

---

**Still have questions?** Open an issue on GitHub: https://github.com/miams/rmagent/issues
