"""
Rendering logic for biography output.

Handles Markdown formatting and metadata generation.
"""

from __future__ import annotations

from pathlib import Path

from .models import Biography, BiographyLength, CitationStyle


class BiographyRenderer:
    """Handles rendering Biography objects to various formats."""

    def __init__(self, media_root_directory: Path | None = None):
        """
        Initialize renderer with optional media root directory.

        Args:
            media_root_directory: Root directory for media files (replaces ? in MediaPath)
        """
        self.media_root_directory = media_root_directory

    @staticmethod
    def format_tokens(count: int) -> str:
        """Format token count with k suffix."""
        if count >= 1000:
            return f"{count/1000:.1f}k"
        return str(count)

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration as Xm Ys or Xs."""
        if seconds >= 60:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m{secs}s" if secs > 0 else f"{minutes}m"
        return f"{int(seconds)}s"

    def render_metadata(self, bio: Biography) -> str:
        """Render Hugo-style front matter metadata."""
        lines = ["---"]

        # Title with years
        years_str = ""
        if bio.birth_year or bio.death_year:
            birth = bio.birth_year or "????"
            death = bio.death_year or "????"
            years_str = f" ({birth}-{death})"
        lines.append(f'Title: "Biography of {bio.full_name}{years_str}"')

        # Timestamp in ISO 8601 format with timezone (format as -05:00)
        tz_str = bio.generated_at.strftime("%z")
        tz_formatted = f"{tz_str[:3]}:{tz_str[3:]}" if tz_str else ""
        date_str = bio.generated_at.strftime("%Y-%m-%dT%H:%M:%S") + tz_formatted
        lines.append(f'Date: {date_str}')

        # Person ID
        lines.append(f'PersonID: {bio.person_id}')

        # LLM Metadata (if available)
        if bio.llm_metadata:
            lines.append(f'TokensIn: {self.format_tokens(bio.llm_metadata.prompt_tokens)}')
            lines.append(f'TokensOut: {self.format_tokens(bio.llm_metadata.completion_tokens)}')
            lines.append(f'TotalTokens: {self.format_tokens(bio.llm_metadata.total_tokens)}')
            lines.append(f'LLM: {bio.llm_metadata.provider.capitalize()}')
            lines.append(f'Model: {bio.llm_metadata.model}')
            lines.append(f'PromptTime: {self.format_duration(bio.llm_metadata.prompt_time)}')
            lines.append(f'LLMTime: {self.format_duration(bio.llm_metadata.llm_time)}')

        # Biography stats (calculate word count dynamically)
        word_count = bio.calculate_word_count()
        lines.append(f'Words: {word_count:,}')
        lines.append(f'Citations: {bio.citation_count}')
        lines.append(f'Sources: {bio.source_count}')

        lines.append("---\n")
        return "\n".join(lines)

    def render_markdown(self, bio: Biography, include_metadata: bool = True) -> str:
        """Render complete biography as Markdown with optional front matter."""
        sections = []

        # Hugo-style front matter metadata
        if include_metadata:
            sections.append(self.render_metadata(bio))

        # Title with lifespan years
        years_str = ""
        if bio.birth_year or bio.death_year:
            birth = bio.birth_year or "????"
            death = bio.death_year or "????"
            years_str = f" ({birth}-{death})"
        sections.append(f"# Biography of {bio.full_name}{years_str}\n")

        # Separate primary and additional images (only for STANDARD and COMPREHENSIVE)
        primary_image = None
        additional_images = []
        if bio.length != BiographyLength.SHORT and bio.media_files:
            for media in bio.media_files:
                is_primary = media.get("IsPrimary", 0) == 1 if hasattr(media, 'get') else media["IsPrimary"] == 1
                if is_primary and primary_image is None:
                    primary_image = media
                elif not is_primary:
                    additional_images.append(media)

        # Introduction
        if bio.introduction:
            sections.append("## Introduction\n")

            # Add primary portrait image with text wrapping (if available)
            if primary_image:
                image_path = self._format_image_path(primary_image)
                caption = self._format_image_caption(bio.full_name, bio.birth_year, bio.death_year)
                # Use HTML for text wrapping - align right with width constraint
                sections.append(f'<img src="{image_path}" alt="{caption}" align="right" width="300" />\n')

            sections.append(bio.introduction)
            sections.append("")

        # Early Life & Family Background
        if bio.early_life:
            sections.append("## Early Life & Family Background\n")
            sections.append(bio.early_life)
            sections.append("")

        # Education
        if bio.education:
            sections.append("## Education\n")
            sections.append(bio.education)
            sections.append("")

        # Career & Accomplishments
        if bio.career:
            sections.append("## Career & Accomplishments\n")
            sections.append(bio.career)
            sections.append("")

        # Marriage & Family
        if bio.marriage_family:
            sections.append("## Marriage & Family\n")
            sections.append(bio.marriage_family)
            sections.append("")

        # Later Life & Activities
        if bio.later_life:
            sections.append("## Later Life & Activities\n")
            sections.append(bio.later_life)
            sections.append("")

        # Death & Legacy
        if bio.death_legacy:
            sections.append("## Death & Legacy\n")
            sections.append(bio.death_legacy)
            sections.append("")

        # Photos (additional non-primary images)
        if additional_images:
            sections.append("## Photos\n")
            for media in additional_images:
                image_path = self._format_image_path(media)
                caption = self._format_image_caption(bio.full_name, bio.birth_year, bio.death_year)
                # Standard markdown image format (no text wrapping for additional images)
                sections.append(f"![{caption}]({image_path})\n")
                sections.append(f"*{caption}*\n")
            sections.append("")

        # Footnotes (only for FOOTNOTE citation style)
        if bio.footnotes and bio.citation_style == CitationStyle.FOOTNOTE:
            sections.append("## Footnotes\n")
            sections.append(bio.footnotes)
            sections.append("")

        # Sources
        if bio.sources:
            sections.append("## Sources\n")
            sections.append(bio.sources)
            sections.append("")

        content = "\n".join(sections)
        # Update word_count for consistency (though metadata renders dynamically)
        bio.word_count = bio.calculate_word_count()
        return content

    def _format_image_path(self, media: dict) -> str:
        """Format media path for Markdown, using media_root_directory if configured."""
        media_path = media.get("MediaPath", "") if hasattr(media, 'get') else media["MediaPath"]
        media_file = media.get("MediaFile", "") if hasattr(media, 'get') else media["MediaFile"]

        # Handle RootsMagic's ?\ or ?/ prefix (placeholder for media root)
        if media_path.startswith("?\\") or media_path.startswith("?/"):
            relative_path = media_path[2:]  # Strip ? and \ or /

            # If media_root_directory is configured, prepend it
            if self.media_root_directory:
                full_path = self.media_root_directory / relative_path / media_file
            else:
                # Fallback: use relative path (original behavior)
                full_path = Path(relative_path) / media_file
        else:
            # No ? prefix - use path as-is
            if media_path:
                full_path = Path(media_path) / media_file
            else:
                full_path = Path(media_file)

        # Convert to POSIX-style path for Markdown
        return full_path.as_posix()

    @staticmethod
    def _format_image_caption(full_name: str, birth_year: int | None, death_year: int | None) -> str:
        """Format caption for images."""
        caption = full_name
        if birth_year or death_year:
            birth = birth_year or "????"
            death = death_year or "????"
            caption += f" ({birth}-{death})"
        return caption
