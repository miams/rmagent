---
description: Review documentation for accuracy and completeness
show-prompt: true
meta: true
---

Review project documentation to ensure it's concise, current, and accurate.

**Modes:**
- `/doc-review` or `/doc-review brief` - Review root docs and INDEX.md
- `/doc-review deep` - Review ALL documentation files

This command reads documentation files and asks the LLM to verify:
1. Content is concise and well-organized
2. Information is current (no outdated references)
3. Cross-references and links are accurate
4. No contradictions between documents
5. INDEX.md accurately reflects documentation structure

```bash
MODE="${1:-brief}"

if [ "$MODE" = "deep" ]; then
  cat <<'PROMPT'
Please perform a DEEP documentation review of the RMAgent project.

Review ALL documentation files for:
1. **Accuracy** - Are all statements, commands, and examples correct?
2. **Currency** - Is information up-to-date? Any outdated references?
3. **Consistency** - Do documents contradict each other?
4. **Completeness** - Are there gaps in documentation coverage?
5. **Conciseness** - Can any content be condensed without losing value?
6. **Organization** - Is content in the right location?

**Root Documentation Files:**
PROMPT

  echo ""
  echo "=== CLAUDE.md ==="
  head -100 CLAUDE.md
  echo ""
  echo "=== README.md ==="
  head -100 README.md
  echo ""
  echo "=== AGENTS.md ==="
  head -50 AGENTS.md
  echo ""
  echo "=== CONTRIBUTING.md ==="
  head -50 CONTRIBUTING.md
  echo ""
  echo "=== CHANGELOG.md ==="
  head -30 CHANGELOG.md

  cat <<'PROMPT'

**Documentation Index:**
PROMPT

  echo ""
  echo "=== docs/INDEX.md ==="
  cat docs/INDEX.md

  cat <<'PROMPT'

**All Documentation Files:**
PROMPT

  echo ""
  find docs -name "*.md" -type f | sort | while read file; do
    echo ""
    echo "=== $file ==="
    head -80 "$file"
    echo "... [file continues]"
  done

  cat <<'PROMPT'

Please provide:
1. **Overall Assessment** - General state of documentation
2. **Critical Issues** - Must-fix problems (inaccuracies, broken links, outdated info)
3. **Recommendations** - Suggestions for improvement
4. **Specific Fixes** - Line-by-line corrections needed

Focus on actionable feedback that improves documentation quality.
PROMPT

else
  # Brief mode - just check root docs + INDEX.md
  cat <<'PROMPT'
Please perform a BRIEF documentation review of the RMAgent project's core files.

Review the following files for:
1. **Accuracy** - Are statements, commands, and statistics correct?
2. **Currency** - Any outdated references or old information?
3. **Consistency** - Do these files contradict each other?
4. **Conciseness** - Is content appropriately detailed (not too verbose)?
5. **INDEX.md Accuracy** - Does INDEX.md correctly reference all docs in the repository?

**Root Documentation Files:**
PROMPT

  echo ""
  echo "=== CLAUDE.md ==="
  cat CLAUDE.md
  echo ""
  echo "=== README.md ==="
  cat README.md
  echo ""
  echo "=== AGENTS.md ==="
  cat AGENTS.md
  echo ""
  echo "=== CONTRIBUTING.md ==="
  cat CONTRIBUTING.md
  echo ""
  echo "=== CHANGELOG.md ==="
  cat CHANGELOG.md

  cat <<'PROMPT'

**Documentation Index:**
PROMPT

  echo ""
  echo "=== docs/INDEX.md ==="
  cat docs/INDEX.md

  cat <<'PROMPT'

**Verify INDEX.md Completeness:**
Check that docs/INDEX.md accurately references all documentation files in the repository.
PROMPT

  echo ""
  echo "=== All docs files in repository ==="
  find docs -name "*.md" -type f | sort

  cat <<'PROMPT'

Please provide:
1. **Quick Assessment** - Overall state of core documentation
2. **Critical Issues** - Any inaccuracies, broken references, or outdated info
3. **INDEX.md Status** - Is it complete and accurate?
4. **Quick Wins** - Easy improvements to make immediately

Be concise and actionable. Focus on what needs fixing right now.
PROMPT

fi
```
