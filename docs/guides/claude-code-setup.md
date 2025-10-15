# Claude Code Setup for RMAgent

This guide documents the slash commands and hooks configured for the RMAgent project.

## Slash Commands

All slash commands are defined in `.claude/commands/`. RMAgent-specific commands use the `rm-` prefix.

**Total Commands: 12** (6 RMAgent-specific, 3 development, 3 utility)

### RMAgent Commands (AI & Data)

Commands that interact with RootsMagic database and AI features:

#### `/rm-bio <person_id> [length]`
**Description:** Generate a biography for a person using AI

**Options:**
- `show-prompt: true` - Shows the AI prompt
- `meta: true` - Shows token usage and timing

**Usage:**
```
/rm-bio 1                    # Standard biography
/rm-bio 1 short              # Short biography
/rm-bio 1 comprehensive      # Comprehensive biography
```

**Output:** Markdown file in `reports/biographies/`

---

#### `/rm-ask "<question>"`
**Description:** Ask natural language questions about genealogy data using AI

**Options:**
- `show-prompt: true` - Shows the AI prompt
- `meta: true` - Shows token usage and timing

**Usage:**
```
/rm-ask "Who are the ancestors of John Smith?"
/rm-ask "Find everyone born in Baltimore"
/rm-ask "Show family relationships for person 1"
```

**Output:** AI-generated answer with data from database

---

#### `/rm-person <person_id> [options]`
**Description:** Query person details from RootsMagic database

**Usage:**
```
/rm-person 1                    # Basic info
/rm-person 1 --events           # Include all events
/rm-person 1 --family           # Include family relationships
/rm-person 1 --ancestors        # Include ancestors
/rm-person 1 --descendants      # Include descendants
```

**Output:** Formatted person information with requested details

---

#### `/rm-search [--name "Name"] [--place "Place"] [--limit N]`
**Description:** Search database by name or place

**Usage:**
```
/rm-search --name "John Smith"
/rm-search --place "Baltimore"
/rm-search --name "Smith" --limit 10
```

**Output:** List of matching persons with IDs

---

#### `/rm-quality [category]`
**Description:** Run data quality validation

**Categories:**
- `dates` - Date format and range issues
- `names` - Missing or invalid names
- `places` - Place format issues
- `relationships` - Relationship inconsistencies
- `sources` - Citation and source issues
- `events` - Event data issues

**Usage:**
```
/rm-quality                  # All checks
/rm-quality dates            # Only date issues
/rm-quality names            # Only name issues
```

**Output:** Formatted table of data quality issues

---

#### `/rm-timeline <person_id> [options]`
**Description:** Generate timeline visualization

**Usage:**
```
/rm-timeline 1                      # JSON format
/rm-timeline 1 --format html        # HTML format
/rm-timeline 1 --include-family     # Include family events
/rm-timeline 1 --group-by-phase     # Group by life phases
```

**Output:** TimelineJS3 JSON or HTML file

---

### Development Commands

Generic development and testing commands (no `rm-` prefix):

#### `/test [filter]`
**Description:** Run pytest tests with optional filters

**Usage:**
```
/test                    # Run all tests
/test unit               # Run unit tests only
/test integration        # Run integration tests only
/test test_queries.py    # Run specific test file
```

**Output:** Test results with pass/fail status

---

#### `/coverage`
**Description:** Run tests with coverage analysis

**Usage:**
```
/coverage
```

**Output:** Coverage report with line-by-line analysis. HTML report at `htmlcov/index.html`

---

#### `/lint [fix]`
**Description:** Run code quality checks (ruff + black)

**Usage:**
```
/lint           # Check only
/lint fix       # Auto-fix issues
```

**Output:** Linting errors and warnings

---

### Utility Commands

#### `/docs [topic]`
**Description:** Quick access to documentation

**Usage:**
```
/docs                # Show INDEX.md
/docs schema         # Schema reference
/docs data-formats   # Data formats reference
/docs dev            # Developer guide
```

**Output:** Documentation preview (first 50-80 lines)

---

#### `/doc-review [mode]`
**Description:** Review documentation for accuracy and completeness using AI

**Options:**
- `show-prompt: true` - Shows the AI prompt
- `meta: true` - Shows token usage and timing

**Usage:**
```
/doc-review          # Brief mode: review root docs + INDEX.md
/doc-review brief    # Same as above
/doc-review deep     # Deep mode: review ALL documentation files
```

**Brief Mode Reviews:**
- CLAUDE.md, README.md, AGENTS.md, CONTRIBUTING.md, CHANGELOG.md
- docs/INDEX.md
- Verifies INDEX.md accurately references all docs

**Deep Mode Reviews:**
- All files from brief mode
- All documentation in docs/ directory
- Cross-references and consistency checks

**Output:** AI assessment with critical issues, recommendations, and specific fixes

---

#### `/check-db`
**Description:** Verify database file exists and is accessible

**Usage:**
```
/check-db
```

**Output:** Database path, status, and basic statistics (person/event/source counts)

---

## Claude Code Hooks

Hooks are configured in `.claude/settings.local.json` and run automatically at specific events.

### PostToolUse Hooks

#### Coverage Reminder Hook
**Trigger:** After running pytest with coverage (`uv run pytest --cov`)

**Action:** Extracts coverage percentage and reminds to update CLAUDE.md and README.md if significantly changed

**Output:**
```
📊 Test coverage: 88%
💡 Reminder: Update coverage stats in CLAUDE.md and README.md if significantly changed
```

---

### PreToolUse Hooks

#### Git Push Confirmation Hook
**Trigger:** Before git push commands

**Action:** Shows recent commits being pushed

**Output:**
```
⚠️  Pushing to remote. Recent commits:
66a29ca docs: reorganize documentation structure
4cdea76 fix: constrain caption width to match image margins
528f1ef fix: handle sqlite3.Row objects in biography rendering
```

---

## Git Pre-Commit Hook

A standard git pre-commit hook is configured at `.git/hooks/pre-commit` to remind about documentation updates.

**Triggers:**
- Documentation structure changes → Check CLAUDE.md
- Test modifications → Check README.md for coverage stats
- Core code changes → Check CLAUDE.md
- Dependency changes → Check README.md

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  DOCUMENTATION REVIEW REMINDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This commit may require updates to key documentation files:

  • Documentation structure changed

Please review and update if necessary:

  ✓ CLAUDE.md     - Already modified
  📄 README.md     - User-facing docs, badges, quick start
  📄 AGENTS.md     - LangChain patterns, agent architecture

Continue with commit? (y/n)
```

---

## Configuration Files

### `.claude/settings.local.json`
- **Permissions:** Pre-approved bash commands, web fetch domains
- **Hooks:** PostToolUse and PreToolUse hook configurations

### `.claude/commands/`
- All custom slash command definitions
- Markdown files with frontmatter and bash scripts

### `.git/hooks/pre-commit`
- Git pre-commit hook for documentation review
- Executable shell script

---

## Best Practices

### When to Use Each Command

**For Genealogy Work:**
- Use `/rm-person` to quickly explore individuals
- Use `/rm-search` to find people by name/place
- Use `/rm-bio` when you need a formatted biography
- Use `/rm-ask` for complex queries that need AI interpretation
- Use `/rm-quality` regularly to maintain data integrity

**For Development:**
- Use `/test` for quick test runs during development
- Use `/coverage` before committing to check test coverage
- Use `/lint` before committing to catch style issues
- Use `/check-db` when debugging database connection issues

**For Documentation:**
- Use `/docs` to quickly reference schema or data formats
- Use `/doc-review` regularly to ensure docs stay accurate and current
- Use `/doc-review brief` before major commits or PRs
- Use `/doc-review deep` after significant feature additions
- Keep CLAUDE.md, README.md, and AGENTS.md updated (hooks will remind you)

### show-prompt and meta Flags

Only use `show-prompt` and `meta` in commands that interact with LLMs:
- ✅ `/rm-bio` - Generates biography with AI
- ✅ `/rm-ask` - Uses AI to answer questions
- ✅ `/doc-review` - Uses AI to review documentation
- ❌ `/rm-person` - Pure database query
- ❌ `/rm-search` - Pure database query
- ❌ `/rm-quality` - Rule-based validation
- ❌ `/rm-timeline` - Data extraction and formatting

### Naming Conventions

- **RMAgent-specific commands:** Use `rm-` prefix (`/rm-bio`, `/rm-person`)
- **Generic dev commands:** No prefix (`/test`, `/lint`, `/coverage`)
- **Utility commands:** No prefix (`/docs`, `/check-db`)

---

## Testing Your Setup

After configuring slash commands and hooks:

1. **Test a slash command:**
   ```
   /check-db
   ```

2. **Test an AI command:**
   ```
   /doc-review brief
   ```

3. **Test a hook:** Run pytest with coverage to see PostToolUse hook:
   ```bash
   uv run pytest --cov=rmagent
   ```

4. **Test git hook:** Make a change to tests and try to commit:
   ```bash
   # Modify a test file
   git add tests/
   git commit -m "test: update test"
   # You should see the documentation review reminder
   ```

5. **View all commands:**
   ```
   /help
   ```

---

## Troubleshooting

### Slash commands not appearing
- Check that files exist in `.claude/commands/`
- Ensure markdown files have proper frontmatter
- Restart Claude Code

### Hooks not firing
- Verify JSON syntax in `.claude/settings.local.json`
- Check that regex matchers are properly escaped
- Use `claude --debug` for detailed hook execution info

### Git hook not running
- Verify `.git/hooks/pre-commit` exists and is executable:
  ```bash
  chmod +x .git/hooks/pre-commit
  ```
- Check that it's not being bypassed with `--no-verify`

---

## Extending This Setup

### Adding New Slash Commands

1. Create `.claude/commands/your-command.md`:
   ```markdown
   ---
   description: Your command description
   show-prompt: true  # Only if uses AI
   meta: true         # Only if uses AI
   ---

   Usage instructions here.

   ```bash
   # Your bash script
   echo "Command output"
   ```
   ```

2. Use `rm-` prefix if RMAgent-specific
3. Document in this file

### Adding New Hooks

1. Edit `.claude/settings.local.json`
2. Add to appropriate hook type (PreToolUse, PostToolUse, etc.)
3. Use regex matcher to target specific tools
4. Test thoroughly before committing

---

## References

- **Claude Code Docs:** https://docs.claude.com/en/docs/claude-code/
- **Slash Commands:** https://docs.claude.com/en/docs/claude-code/slash-commands
- **Hooks:** https://docs.claude.com/en/docs/claude-code/hooks
- **RMAgent User Guide:** [guides/user-guide.md](user-guide.md)
- **Developer Guide:** [guides/developer-guide.md](developer-guide.md)
