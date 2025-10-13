"""
Citation processing and formatting logic.

Handles citation formatting, footnote generation, and bibliography creation.
"""

from __future__ import annotations

import re

from .models import CitationInfo, CitationStyle, CitationTracker, PersonContext, get_row_value


class CitationProcessor:
    """Handles citation formatting and processing."""

    @staticmethod
    def strip_source_type_prefix(source_name: str) -> str:
        """
        Remove source type prefixes like 'Book: ', 'Newspapers: ', etc.

        Examples:
            "Book: Smith Family History" -> "Smith Family History"
            "Newspapers: Baltimore Sun" -> "Baltimore Sun"
            "US Census Records" -> "US Census Records" (no change)
        """
        # Common source type prefixes in RootsMagic
        prefixes = [
            "Book: ",
            "Books: ",
            "Newspaper: ",
            "Newspapers: ",
            "Cemetery: ",
            "Cemeteries: ",
            "Census: ",
            "Church Records: ",
            "Court Records: ",
            "Military Records: ",
            "Vital Records: ",
            "Website: ",
            "Websites: ",
            "Document: ",
            "Documents: ",
            "Letter: ",
            "Letters: ",
            "Photo: ",
            "Photos: ",
        ]

        for prefix in prefixes:
            if source_name.startswith(prefix):
                return source_name[len(prefix):]

        return source_name

    def format_citation_info(self, citation: dict) -> CitationInfo:
        """
        Format citation into CitationInfo with all text versions.
        Handles free-form (TemplateID=0) and template-based citations.
        """
        citation_id = get_row_value(citation, "CitationID", 0)
        source_id = get_row_value(citation, "SourceID", 0)
        template_id = get_row_value(citation, "TemplateID", 0)
        template_name = get_row_value(citation, "TemplateName")

        is_freeform = template_id == 0

        if is_freeform:
            # Use formatted fields from CitationTable if available
            footnote = get_row_value(citation, "Footnote")
            short_footnote = get_row_value(citation, "ShortFootnote")
            bibliography = get_row_value(citation, "CitationBibliography")

            # Fallback: Generate from Fields BLOB if NULL
            if not footnote:
                footnote = self._generate_citation_from_fields(citation)
            if not short_footnote:
                short_footnote = self._generate_short_footnote_from_fields(citation, footnote)
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
        """
        Generate footnote text from BLOB fields (fallback).
        First checks SourceFields for pre-formatted Footnote, then CitationFields for page/details.
        Returns citation with WARNING only if all approaches fail.
        """
        citation_id = get_row_value(citation, "CitationID", 0)

        # First, check SourceFields BLOB for pre-formatted Footnote
        source_fields_blob = get_row_value(citation, "SourceFields")
        if source_fields_blob:
            from rmagent.rmlib.parsers.blob_parser import parse_source_fields

            try:
                source_fields = parse_source_fields(source_fields_blob)
                footnote = source_fields.get("Footnote", "")
                if footnote:
                    return footnote
            except Exception:
                pass  # Continue to next approach

        # Fallback: Check CitationFields BLOB for page/details
        citation_fields_blob = get_row_value(citation, "CitationFields")
        if citation_fields_blob:
            from rmagent.rmlib.parsers.blob_parser import parse_citation_fields

            try:
                fields = parse_citation_fields(citation_fields_blob)
                # Simple format: Page field is most common
                page = fields.get("Page", "")
                if page:
                    return f"p. {page}"
                # If no page, show first non-empty field
                for key, value in fields.items():
                    if value:
                        return f"{key}: {value}"
            except Exception:
                pass

        return f"[Citation {citation_id}] ⚠️ WARNING: Missing citation fields"

    def _generate_short_footnote_from_fields(self, citation: dict, full_footnote: str) -> str:
        """
        Generate short footnote text from BLOB fields (fallback).
        First checks SourceFields for pre-formatted ShortFootnote, then falls back to full footnote.
        """
        # Check SourceFields BLOB for pre-formatted ShortFootnote
        source_fields_blob = get_row_value(citation, "SourceFields")
        if source_fields_blob:
            from rmagent.rmlib.parsers.blob_parser import parse_source_fields

            try:
                source_fields = parse_source_fields(source_fields_blob)
                short_footnote = source_fields.get("ShortFootnote", "")
                if short_footnote:
                    return short_footnote
            except Exception:
                pass

        # Fallback: use full footnote
        return full_footnote

    def _generate_bibliography_from_fields(self, citation: dict) -> str:
        """
        Generate bibliography entry from SourceFields BLOB (fallback).
        First checks for pre-formatted Bibliography field, then constructs from individual fields.
        Returns source name with WARNING only if all approaches fail.
        """
        source_id = get_row_value(citation, "SourceID", 0)
        source_name = get_row_value(citation, "SourceName", "[Unknown Source]")
        fields_blob = get_row_value(citation, "SourceFields")

        if not fields_blob:
            return f"{source_name} ⚠️ WARNING: Missing source fields"

        from rmagent.rmlib.parsers.blob_parser import parse_source_fields

        try:
            fields = parse_source_fields(fields_blob)

            # First, check for pre-formatted Bibliography field (RootsMagic stores formatted text here)
            bibliography = fields.get("Bibliography", "")
            if bibliography:
                return bibliography

            # Fallback: Evidence Explained basic format: Author. Title. Publisher, Year.
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

            if parts:
                return " ".join(parts)
            return f"{source_name} ⚠️ WARNING: No source details in fields"
        except Exception as e:
            return f"{source_name} ⚠️ WARNING: Failed to parse source fields ({e})"

    def process_citations_in_text(
        self, text: str, all_citations: list[dict]
    ) -> tuple[str, list[tuple[int, CitationInfo]], CitationTracker]:
        """
        Process {{cite:ID}} markers in text, replace with [^N] footnote markers.

        Returns:
            - Modified text with [^N] markers
            - List of (footnote_num, CitationInfo) in order of appearance
            - CitationTracker with all citation metadata
        """
        tracker = CitationTracker()

        # Build lookup: CitationID -> CitationInfo
        citation_lookup = {}
        for citation in all_citations:
            cid = get_row_value(citation, "CitationID", 0)
            citation_lookup[cid] = self.format_citation_info(citation)

        # Find all {{cite:ID}} markers (double braces as specified in prompt)
        pattern = r"\{\{cite:(\d+)\}\}"
        matches = list(re.finditer(pattern, text))

        # Replace markers with footnote numbers (in reverse to preserve positions)
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

    def generate_footnotes_section(
        self, footnotes: list[tuple[int, CitationInfo]], tracker: CitationTracker
    ) -> str:
        """
        Generate footnotes section with numbered entries and 3-character indent.
        First citation per source uses full footnote, subsequent use short.
        """
        lines = []

        for footnote_num, citation_info in footnotes:
            # Determine if first citation for this source
            is_first = tracker.is_first_for_source(citation_info.citation_id, citation_info.source_id)

            # Use full or short footnote
            footnote_text = citation_info.footnote if is_first else citation_info.short_footnote

            # Add 3-character indent to each footnote
            lines.append(f"   [^{footnote_num}]: {footnote_text}")

        return "\n".join(lines)

    def generate_sources_section(self, all_citations: list[dict]) -> str:
        """
        Generate alphabetically sorted bibliography using SourceTable.ActualText.
        Deduplicate by SourceID.
        Uses hanging indent format (3 spaces for continuation lines).
        """
        # Build unique sources map: SourceID -> CitationInfo
        sources = {}
        for citation in all_citations:
            source_id = get_row_value(citation, "SourceID", 0)
            if source_id not in sources:
                citation_info = self.format_citation_info(citation)
                sources[source_id] = citation_info

        # Sort alphabetically by bibliography text
        sorted_sources = sorted(sources.values(), key=lambda c: c.bibliography.lower())

        # Format with 3-character indent (no bullets)
        lines = []
        for citation_info in sorted_sources:
            # 3-character indent, no bullet
            lines.append(f"   {citation_info.bibliography}")

        return "\n".join(lines)

    def format_sources_section(self, context: PersonContext, citation_style: CitationStyle) -> str:
        """Format sources section based on citation style."""
        if not context.all_citations:
            return ""

        lines = []
        for i, citation in enumerate(context.all_citations, 1):
            source_name_raw = get_row_value(citation, "SourceName", "Unknown Source")
            citation_name = get_row_value(citation, "CitationName", "")

            # Remove source type prefixes like "Book: " or "Newspapers: "
            source_name = self.strip_source_type_prefix(source_name_raw)

            if citation_style == CitationStyle.FOOTNOTE:
                lines.append(f"{i}. *{source_name}*")
                if citation_name:
                    lines.append(f"   {citation_name}")
            elif citation_style == CitationStyle.PARENTHETICAL:
                lines.append(f"- *{source_name}*")
                if citation_name:
                    lines.append(f"  ({citation_name})")
            else:  # NARRATIVE
                if citation_name:
                    lines.append(f"- *{source_name}*: {citation_name}")
                else:
                    lines.append(f"- *{source_name}*")

        return "\n".join(lines)
