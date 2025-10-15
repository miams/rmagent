# Biography Citation & Footnote Implementation Plan

**Date:** 2025-10-12
**Author:** Claude Code
**Status:** Design Review

---

## Overview

Enhance biography generation to support proper academic footnote citations following Evidence Explained practices, with automatic footnote numbering, per-source deduplication, and alphabetically sorted bibliographies.

## Goals

1. **Footnote Support**: Insert `[^N]` markers in biography text with corresponding footnote section
2. **Citation Formatting**: Use RootsMagic's formatted citations (free-form) or show placeholders (template-based)
3. **Source Tracking**: First citation uses full footnote, subsequent use short footnote (per source)
4. **Bibliography**: Alphabetically sorted bibliography entries using Bibliography field
5. **LLM Integration**: Guide LLM to insert `{{cite:CitationID}}` markers during generation

---

## Architecture

### Data Flow

```
1. Extract person context with citations
   └─> PersonContext with all_citations list
       └─> Each citation has: CitationID, SourceID, Footnote, ShortFootnote, Bibliography, TemplateID

2. LLM generates biography with {{cite:123}} markers
   └─> Example: "John was born in 1850{{cite:456}} and married Mary{{cite:789}}."

3. Post-process biography text
   └─> Track source-level citations (first vs subsequent)
   └─> Replace {{cite:123}} with [^N] footnote markers
   └─> Build footnote list (ordered by appearance)

4. Generate sections
   ├─> Biography text (with [^N] markers)
   ├─> Footnotes section (ordered by citation appearance)
   └─> Sources section (alphabetical by source bibliography)
```

### Citation Types

**Free-Form Sources** (TemplateID = 0):
- Use `CitationTable.Footnote` for first citation
- Use `CitationTable.ShortFootnote` for subsequent
- Use `SourceTable.ActualText` for bibliography
- If NULL, generate from Fields BLOB (fallback)

**Template-Based Sources** (TemplateID > 0):
- Show placeholder: `[Citation {CitationID}, Template: {TemplateName}]`
- Bibliography: `[Source {SourceID}, Template: {TemplateName}]`

---

## Implementation Plan

### Phase 1: Citation Collection & Formatting

**Files:** `rmagent/generators/biography.py`

#### 1.1 Update `_get_citations_for_event()`

Change from simple query to using `QueryService.get_event_citations()`:

```python
def _get_citations_for_event(self, db: RMDatabase, event_id: int) -> list[dict]:
    """Get all citations for an event with formatted text."""
    query = QueryService(db)
    return query.get_event_citations(event_id)
```

**Returns:** List with CitationID, SourceID, Footnote, ShortFootnote, CitationBibliography, SourceBibliography, TemplateID, TemplateName

#### 1.2 Add Citation Formatting Helpers

```python
@dataclass
class CitationInfo:
    """Formatted citation information."""
    citation_id: int
    source_id: int
    footnote: str  # Full footnote (first use)
    short_footnote: str  # Short footnote (subsequent use)
    bibliography: str  # Bibliography entry
    is_freeform: bool  # True if TemplateID == 0
    template_name: str | None  # Template name if not free-form

def _format_citation_info(self, citation: dict) -> CitationInfo:
    """Format citation into CitationInfo with all text versions."""
    citation_id = _get_row_value(citation, "CitationID", 0)
    source_id = _get_row_value(citation, "SourceID", 0)
    template_id = _get_row_value(citation, "TemplateID", 0)
    template_name = _get_row_value(citation, "TemplateName")

    is_freeform = (template_id == 0)

    if is_freeform:
        # Use formatted fields if available
        footnote = _get_row_value(citation, "Footnote", "")
        short_footnote = _get_row_value(citation, "ShortFootnote", "")
        bibliography = _get_row_value(citation, "SourceBibliography", "")

        # Fallback: Generate from Fields BLOB if NULL
        if not footnote:
            footnote = self._generate_citation_from_fields(citation)
        if not short_footnote:
            short_footnote = footnote  # Use full as fallback
        if not bibliography:
            bibliography = self._generate_bibliography_from_fields(citation)
    else:
        # Template-based: Show placeholders
        footnote = f"[Citation {citation_id}, Template: {template_name}]"
        short_footnote = footnote
        bibliography = f"[Source {source_id}, Template: {template_name}]"

    return CitationInfo(
        citation_id=citation_id,
        source_id=source_id,
        footnote=footnote,
        short_footnote=short_footnote,
        bibliography=bibliography,
        is_freeform=is_freeform,
        template_name=template_name,
    )

def _generate_citation_from_fields(self, citation: dict) -> str:
    """Generate basic citation from Fields BLOB (fallback)."""
    # Parse CitationFields BLOB
    fields_blob = _get_row_value(citation, "CitationFields")
    if not fields_blob:
        return f"[Citation {_get_row_value(citation, 'CitationID')}]"

    # Use blob_parser to extract fields
    from rmagent.rmlib.parsers.blob_parser import parse_citation_fields
    try:
        fields = parse_citation_fields(fields_blob)
        # Simple format: Page field is most common
        page = fields.get("Page", "")
        return f"p. {page}" if page else "[No citation details]"
    except Exception:
        return f"[Citation {_get_row_value(citation, 'CitationID')}]"

def _generate_bibliography_from_fields(self, citation: dict) -> str:
    """Generate bibliography entry from SourceFields BLOB (fallback)."""
    fields_blob = _get_row_value(citation, "SourceFields")
    if not fields_blob:
        return _get_row_value(citation, "SourceName", "[Unknown Source]")

    from rmagent.rmlib.parsers.blob_parser import parse_source_fields
    try:
        fields = parse_source_fields(fields_blob)
        # Evidence Explained basic format: Author. Title. Publisher, Year.
        author = fields.get("Author", "")
        title = fields.get("Title", "")
        publisher = fields.get("Publisher", "")
        year = fields.get("Year", "")

        parts = []
        if author:
            parts.append(f"{author}.")
        if title:
            parts.append(f"*{title}.*")
        if publisher and year:
            parts.append(f"{publisher}, {year}.")
        elif publisher:
            parts.append(f"{publisher}.")
        elif year:
            parts.append(f"{year}.")

        return " ".join(parts) if parts else _get_row_value(citation, "SourceName", "[Unknown Source]")
    except Exception:
        return _get_row_value(citation, "SourceName", "[Unknown Source]")
```

#### 1.3 Add Source-Level Citation Tracking

```python
@dataclass
class CitationTracker:
    """Track citations for footnote numbering and deduplication."""

    # Map: CitationID -> FootnoteNumber
    citation_to_footnote: dict[int, int] = field(default_factory=dict)

    # Map: SourceID -> first CitationID encountered
    source_first_citation: dict[int, int] = field(default_factory=dict)

    # Ordered list of citations as they appear in text
    citation_order: list[int] = field(default_factory=list)

    def add_citation(self, citation_id: int, source_id: int) -> int:
        """
        Add citation to tracker, returns footnote number.
        Tracks first citation per source for full vs short footnote logic.
        """
        if citation_id in self.citation_to_footnote:
            # Already encountered, return existing number
            return self.citation_to_footnote[citation_id]

        # New citation
        footnote_num = len(self.citation_order) + 1
        self.citation_to_footnote[citation_id] = footnote_num
        self.citation_order.append(citation_id)

        # Track first citation for this source
        if source_id not in self.source_first_citation:
            self.source_first_citation[source_id] = citation_id

        return footnote_num

    def is_first_for_source(self, citation_id: int, source_id: int) -> bool:
        """Check if this is the first citation for a given source."""
        return self.source_first_citation.get(source_id) == citation_id
```

---

### Phase 2: LLM Prompt Enhancement

**Files:** `config/prompts/biography.yaml`

#### 2.1 Update Prompts to Include Citation Guidance

Add to `template` section (all variants):

```yaml
CRITICAL CITATION INSTRUCTIONS:
- When referencing information from the timeline, notes, or sources, insert citation markers using this format: {{cite:CitationID}}
- Available citations are listed in "Available Citations" section below
- Example: "John was born in Baltimore{{cite:123}} and later moved to Virginia{{cite:456}}."
- Place citation markers at the end of sentences or clauses
- Multiple facts from same source can reuse same citation: {{cite:123}}
- Follow Elizabeth Shown Mills' "Evidence Explained" best practices for genealogical citations
- Do NOT create footnote text yourself - just insert the {{cite:ID}} markers

Available Citations:
{available_citations}
```

#### 2.2 Update `_build_biography_context()` in `genealogy_agent.py`

```python
def _build_biography_context(self, person_id: int) -> dict:
    # ... existing context building ...

    # Format available citations for LLM
    available_citations = self._format_available_citations(all_citations)

    return {
        "person_summary": person_summary,
        "person_notes": person_notes_formatted,
        "timeline_overview": timeline_overview,
        "relationship_notes": relationship_notes,
        "family_overview": family_overview,
        "early_life_overview": early_life_overview,
        "family_loss_notes": family_loss_notes,
        "sibling_summary": sibling_summary,
        "source_notes": "Sources include citations extracted from RootsMagic events.",
        "available_citations": available_citations,  # NEW
    }

def _format_available_citations(self, citations: list[dict]) -> str:
    """Format citations for LLM prompt."""
    lines = []
    for citation in citations:
        cid = citation.get("CitationID")
        source_name = citation.get("SourceName", "Unknown")
        citation_name = citation.get("CitationName", "")
        event_type = citation.get("EventType", "")

        desc = f"- {{cite:{cid}}}: {source_name}"
        if citation_name:
            desc += f" ({citation_name})"
        if event_type:
            desc += f" [Used for: {event_type}]"
        lines.append(desc)

    return "\n".join(lines) if lines else "No citations available."
```

---

### Phase 3: Post-Processing & Section Generation

**Files:** `rmagent/generators/biography.py`

#### 3.1 Add Post-Processing Method

```python
def _process_citations_in_text(
    self,
    text: str,
    all_citations: list[dict]
) -> tuple[str, list[tuple[int, CitationInfo]], CitationTracker]:
    """
    Process {{cite:ID}} markers in text, replace with [^N] footnote markers.

    Returns:
        - Modified text with [^N] markers
        - List of (footnote_num, CitationInfo) in order of appearance
        - CitationTracker with all citation metadata
    """
    import re

    tracker = CitationTracker()

    # Build lookup: CitationID -> CitationInfo
    citation_lookup = {}
    for citation in all_citations:
        cid = _get_row_value(citation, "CitationID", 0)
        citation_lookup[cid] = self._format_citation_info(citation)

    # Find all {{cite:ID}} markers (double braces)
    pattern = r'\{\{cite:(\d+)\}\}'
    matches = re.finditer(pattern, text)

    # Replace markers with footnote numbers
    replacements = []
    for match in matches:
        citation_id = int(match.group(1))

        if citation_id not in citation_lookup:
            # Citation not found, leave placeholder
            footnote_marker = f"[^{citation_id}?]"
        else:
            citation_info = citation_lookup[citation_id]
            source_id = citation_info.source_id

            # Get or assign footnote number
            footnote_num = tracker.add_citation(citation_id, source_id)
            footnote_marker = f"[^{footnote_num}]"

        replacements.append((match.span(), footnote_marker))

    # Apply replacements in reverse order to preserve positions
    modified_text = text
    for (start, end), replacement in reversed(replacements):
        modified_text = modified_text[:start] + replacement + modified_text[end:]

    # Build ordered footnote list
    footnotes = []
    for citation_id in tracker.citation_order:
        citation_info = citation_lookup.get(citation_id)
        if citation_info:
            footnote_num = tracker.citation_to_footnote[citation_id]
            footnotes.append((footnote_num, citation_info))

    return modified_text, footnotes, tracker
```

#### 3.2 Generate Footnotes Section

```python
def _generate_footnotes_section(
    self,
    footnotes: list[tuple[int, CitationInfo]],
    tracker: CitationTracker
) -> str:
    """
    Generate footnotes section with numbered entries.
    First citation per source uses full footnote, subsequent use short.
    """
    lines = []

    for footnote_num, citation_info in footnotes:
        # Determine if first citation for this source
        is_first = tracker.is_first_for_source(
            citation_info.citation_id,
            citation_info.source_id
        )

        # Use full or short footnote
        footnote_text = citation_info.footnote if is_first else citation_info.short_footnote

        lines.append(f"[^{footnote_num}]: {footnote_text}")

    return "\n".join(lines)
```

#### 3.3 Generate Sources Section (Bibliography)

```python
def _generate_sources_section(self, all_citations: list[dict]) -> str:
    """
    Generate alphabetically sorted bibliography using SourceTable.ActualText.
    Deduplicate by SourceID.
    """
    # Build unique sources map: SourceID -> CitationInfo
    sources = {}
    for citation in all_citations:
        source_id = _get_row_value(citation, "SourceID", 0)
        if source_id not in sources:
            citation_info = self._format_citation_info(citation)
            sources[source_id] = citation_info

    # Sort alphabetically by bibliography text
    sorted_sources = sorted(sources.values(), key=lambda c: c.bibliography.lower())

    # Format as list
    lines = []
    for citation_info in sorted_sources:
        lines.append(f"- {citation_info.bibliography}")

    return "\n".join(lines)
```

#### 3.4 Update `Biography` Dataclass

```python
@dataclass
class Biography:
    """Generated biography with structured sections."""

    person_id: int
    full_name: str
    length: BiographyLength
    citation_style: CitationStyle

    # Generated content
    introduction: str
    early_life: str
    education: str
    career: str
    marriage_family: str
    later_life: str
    death_legacy: str
    footnotes: str  # NEW: Footnotes section (only for FOOTNOTE style)
    sources: str

    # ... rest unchanged ...

    def render_markdown(self) -> str:
        """Render complete biography as Markdown."""
        sections = []

        # Title
        sections.append(f"# {self.full_name}\n")

        # ... existing sections ...

        # Death & Legacy
        if self.death_legacy:
            sections.append("## Death & Legacy\n")
            sections.append(self.death_legacy)
            sections.append("")

        # Footnotes (NEW - only for FOOTNOTE citation style)
        if self.footnotes and self.citation_style == CitationStyle.FOOTNOTE:
            sections.append("## Footnotes\n")
            sections.append(self.footnotes)
            sections.append("")

        # Sources
        if self.sources:
            sections.append("## Sources\n")
            sections.append(self.sources)
            sections.append("")

        # ... rest unchanged ...
```

#### 3.5 Update `_generate_with_ai()` Integration

```python
def _generate_with_ai(
    self,
    context: PersonContext,
    length: BiographyLength,
    citation_style: CitationStyle,
    include_sources: bool,
) -> Biography:
    """Generate biography using AI agent."""
    if not self.agent:
        raise ValueError("AI generation requested but no agent provided")

    # Use agent's generate_biography method
    result = self.agent.generate_biography(person_id=context.person_id, style=length.value)

    # Parse AI response into sections
    sections = self._parse_ai_response(result.text)

    # Process citations in each section (for FOOTNOTE style only)
    footnotes_text = ""
    sources_text = ""

    if citation_style == CitationStyle.FOOTNOTE:
        # Combine all section text
        full_text = "\n\n".join(sections.values())

        # Process citations
        modified_text, footnotes, tracker = self._process_citations_in_text(
            full_text, context.all_citations
        )

        # Re-split modified text back into sections (approximate)
        sections = self._parse_ai_response(modified_text)

        # Generate footnotes section
        footnotes_text = self._generate_footnotes_section(footnotes, tracker)

        # Generate sources section
        if include_sources:
            sources_text = self._generate_sources_section(context.all_citations)
    else:
        # For other citation styles, use existing format
        if include_sources:
            sources_text = self._format_sources_section(context, citation_style)

    return Biography(
        person_id=context.person_id,
        full_name=context.full_name,
        length=length,
        citation_style=citation_style,
        introduction=sections.get("introduction", ""),
        early_life=sections.get("early_life", ""),
        education=sections.get("education", ""),
        career=sections.get("career", ""),
        marriage_family=sections.get("marriage_family", ""),
        later_life=sections.get("later_life", ""),
        death_legacy=sections.get("death_legacy", ""),
        footnotes=footnotes_text,
        sources=sources_text,
        privacy_applied=getattr(context, "privacy_applied", False),
    )
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/unit/test_biography_generator.py`

```python
def test_citation_info_freeform():
    """Test formatting free-form citation with populated fields."""
    citation = {
        "CitationID": 123,
        "SourceID": 456,
        "TemplateID": 0,
        "Footnote": "John Smith, *History*, p. 45.",
        "ShortFootnote": "Smith, *History*, 45.",
        "SourceBibliography": "Smith, John. *History.* Press, 2020.",
    }

    generator = BiographyGenerator()
    info = generator._format_citation_info(citation)

    assert info.is_freeform is True
    assert info.footnote == "John Smith, *History*, p. 45."
    assert info.short_footnote == "Smith, *History*, 45."
    assert info.bibliography == "Smith, John. *History.* Press, 2020."

def test_citation_info_template_based():
    """Test template-based citation shows placeholder."""
    citation = {
        "CitationID": 789,
        "SourceID": 101,
        "TemplateID": 42,
        "TemplateName": "US Census Template",
        "Footnote": None,
        "ShortFootnote": None,
        "SourceBibliography": None,
    }

    generator = BiographyGenerator()
    info = generator._format_citation_info(citation)

    assert info.is_freeform is False
    assert info.template_name == "US Census Template"
    assert "[Citation 789" in info.footnote
    assert "[Source 101" in info.bibliography

def test_citation_tracker_first_vs_subsequent():
    """Test citation tracker identifies first vs subsequent per source."""
    tracker = CitationTracker()

    # First citation for source 1
    fn1 = tracker.add_citation(citation_id=100, source_id=1)
    assert fn1 == 1
    assert tracker.is_first_for_source(100, 1) is True

    # Second citation for source 1 (different citation, same source)
    fn2 = tracker.add_citation(citation_id=101, source_id=1)
    assert fn2 == 2
    assert tracker.is_first_for_source(101, 1) is False

    # First citation for source 2
    fn3 = tracker.add_citation(citation_id=102, source_id=2)
    assert fn3 == 3
    assert tracker.is_first_for_source(102, 2) is True

def test_process_citations_in_text():
    """Test {{cite:ID}} replacement with [^N] markers."""
    text = "John was born{{cite:123}} and married{{cite:456}}."
    citations = [
        {"CitationID": 123, "SourceID": 1, "TemplateID": 0,
         "Footnote": "Birth cert.", "ShortFootnote": "Birth cert.",
         "SourceBibliography": "Birth Records."},
        {"CitationID": 456, "SourceID": 2, "TemplateID": 0,
         "Footnote": "Marriage cert.", "ShortFootnote": "Marriage cert.",
         "SourceBibliography": "Marriage Records."},
    ]

    generator = BiographyGenerator()
    modified_text, footnotes, tracker = generator._process_citations_in_text(text, citations)

    assert modified_text == "John was born[^1] and married[^2]."
    assert len(footnotes) == 2
    assert footnotes[0][0] == 1  # First footnote number
    assert footnotes[1][0] == 2  # Second footnote number

def test_generate_footnotes_section():
    """Test footnote section generation with full vs short."""
    # Setup tracker with two citations from same source
    tracker = CitationTracker()
    tracker.add_citation(100, source_id=1)
    tracker.add_citation(101, source_id=1)  # Same source, different citation

    citation_info_1 = CitationInfo(
        citation_id=100, source_id=1,
        footnote="Full footnote text here.",
        short_footnote="Short footnote.",
        bibliography="Bibliography entry.",
        is_freeform=True, template_name=None
    )
    citation_info_2 = CitationInfo(
        citation_id=101, source_id=1,
        footnote="Full footnote text here.",
        short_footnote="Short footnote.",
        bibliography="Bibliography entry.",
        is_freeform=True, template_name=None
    )

    footnotes = [(1, citation_info_1), (2, citation_info_2)]

    generator = BiographyGenerator()
    result = generator._generate_footnotes_section(footnotes, tracker)

    assert "[^1]: Full footnote text here." in result
    assert "[^2]: Short footnote." in result  # Should use short for subsequent

def test_generate_sources_alphabetical():
    """Test sources section is alphabetically sorted."""
    citations = [
        {"CitationID": 1, "SourceID": 1, "TemplateID": 0,
         "SourceBibliography": "Zebra, A. *Last Book.* 2020."},
        {"CitationID": 2, "SourceID": 2, "TemplateID": 0,
         "SourceBibliography": "Apple, B. *First Book.* 2019."},
        {"CitationID": 3, "SourceID": 1, "TemplateID": 0,
         "SourceBibliography": "Zebra, A. *Last Book.* 2020."},  # Duplicate source
    ]

    generator = BiographyGenerator()
    result = generator._generate_sources_section(citations)

    lines = result.split("\n")
    assert len(lines) == 2  # Should deduplicate by SourceID
    assert "Apple" in lines[0]  # Alphabetically first
    assert "Zebra" in lines[1]  # Alphabetically second
```

### Integration Tests

**File:** `tests/integration/test_biography_citations.py`

```python
def test_biography_with_footnotes_end_to_end(sample_db):
    """Full integration test with real database and citations."""
    # Find a person with citations in test database
    # Generate biography with footnote style
    # Verify footnotes section exists
    # Verify sources section exists
    # Verify footnote numbering is correct
    pass

def test_biography_with_template_citations(sample_db):
    """Test that template-based citations show placeholders."""
    pass

def test_biography_mixed_citations(sample_db):
    """Test biography with mix of free-form and template citations."""
    pass
```

---

## Edge Cases

1. **Citation Missing Formatted Text**
   - **Scenario:** Free-form citation with NULL Footnote/ShortFootnote/Bibliography
   - **Handling:** Fallback to generating from Fields BLOB or simple placeholder

2. **Template-Based Citations**
   - **Scenario:** Citation uses RootsMagic template (TemplateID > 0)
   - **Handling:** Show placeholder with template name

3. **Multiple Citations Same Source**
   - **Scenario:** Two different citations from same source in biography
   - **Handling:** First uses full footnote, second uses short footnote

4. **LLM Doesn't Insert Citation Markers**
   - **Scenario:** AI-generated text lacks {{cite:ID}} markers
   - **Handling:** Biography generated without footnotes (still show sources section)

5. **Invalid Citation ID in Marker**
   - **Scenario:** Text contains {{cite:999}} but citation 999 doesn't exist
   - **Handling:** Leave placeholder `[^999?]` in text with warning

6. **No Citations Available**
   - **Scenario:** Person has no citations in database
   - **Handling:** Biography generates normally, footnotes section omitted

7. **Citation Appears Multiple Times**
   - **Scenario:** Same {{cite:123}} appears 3 times in text
   - **Handling:** All get same `[^N]` number, footnote appears once

---

## File Change Summary

### Modified Files

| File | Changes | Lines |
|------|---------|-------|
| `rmagent/rmlib/queries.py` | ✅ Updated `_GET_EVENT_CITATIONS_SQL` | +12 |
| `rmagent/generators/biography.py` | Add citation formatting, tracking, processing | +250 |
| `rmagent/agent/genealogy_agent.py` | Update `_build_biography_context()` with citations | +30 |
| `config/prompts/biography.yaml` | Add citation instructions to all variants | +25 |
| `tests/unit/test_biography_generator.py` | Add 8+ new test cases | +150 |
| `tests/integration/test_biography_citations.py` | New file with 3 integration tests | +80 |

**Total:** ~550 lines of new/modified code

---

## Implementation Phases

### Phase 1: Foundation (2-3 hours)
- ✅ Update citation query (DONE)
- Add `CitationInfo`, `CitationTracker` dataclasses
- Implement `_format_citation_info()` with free-form/template logic
- Implement fallback generators for missing formatted text
- **Deliverable:** Citation formatting helpers working

### Phase 2: Text Processing (1-2 hours)
- Implement `_process_citations_in_text()` with regex replacement
- Implement `_generate_footnotes_section()`
- Implement `_generate_sources_section()`
- Update `Biography` dataclass with footnotes field
- **Deliverable:** Post-processing working for sample text

### Phase 3: LLM Integration (1 hour)
- Update `biography.yaml` prompts
- Update `_build_biography_context()` in genealogy_agent
- Integrate post-processing into `_generate_with_ai()`
- **Deliverable:** End-to-end AI generation with footnotes

### Phase 4: Testing (1-2 hours)
- Write unit tests for all new functions
- Write integration tests with sample database
- Fix bugs discovered during testing
- **Deliverable:** All tests passing

### Phase 5: Documentation (30 min)
- Update `USAGE.md` with footnote examples
- Update `AI_AGENT_TODO.md` completion status
- Add inline code comments
- **Deliverable:** Documentation complete

**Total Estimated Time:** 6-9 hours of focused development

---

## Success Criteria

✅ **Must Have:**
1. Free-form citations (TemplateID=0) use formatted fields
2. Template-based citations show placeholders
3. First citation per source uses full footnote, subsequent use short
4. Footnotes numbered sequentially in order of appearance
5. Sources alphabetically sorted by bibliography text
6. All existing tests still pass
7. New functionality has 80%+ test coverage

✅ **Should Have:**
8. LLM successfully inserts {{cite:ID}} markers
9. Graceful handling of missing formatted text
10. Clear error messages for invalid citations

⏭️ **Future Enhancements:**
- Support for parenthetical and narrative citation styles with {{cite:ID}}
- Citation template rendering (implement template language parser)
- Citation style guide enforcement (Evidence Explained validator)

---

## Questions for Review

1. **Fallback Strategy:** If free-form citation has NULL fields, should we:
   - A) Generate basic citation from Fields BLOB (proposed)
   - B) Show placeholder like template-based
   - C) Skip citation entirely

2. **LLM Reliability:** If LLM fails to insert {{cite:ID}} markers:
   - A) Accept biography without footnotes
   - B) Retry with stronger prompt
   - C) Show warning to user

3. **Template Citations:** For template-based sources:
   - A) Show placeholder with template name (proposed)
   - B) Attempt basic rendering from template (complex)
   - C) Skip in footnotes, show only in sources

4. **Citation Scope:** Should we support citations in:
   - A) Only AI-generated biographies
   - B) Both AI and template-based biographies
   - C) Start with AI, add template later

5. **Performance:** With 100+ citations per person:
   - A) Current approach is fine (O(n) processing)
   - B) Need optimization (caching, indexing)

---

## Recommended Decision

**Proceed with implementation?**

- ✅ **Yes, as planned** - Architecture is sound, phases are clear
- ⏸️ **Yes, but modify** - Which aspects need adjustment?
- ❌ **No, needs redesign** - What concerns need addressing?

Please provide feedback on:
1. Overall architecture
2. Edge case handling
3. Testing strategy
4. Any missing scenarios
5. Implementation priority/phasing

---

**End of Implementation Plan**
