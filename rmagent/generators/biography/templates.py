"""
Template-based biography generation.

Provides simple template-based biographies when AI is not available.
"""

from __future__ import annotations

from rmagent.rmlib.parsers.date_parser import is_unknown_date, parse_rm_date
from rmagent.rmlib.parsers.name_parser import format_full_name

from .models import PersonContext, get_row_value


class BiographyTemplates:
    """Generates biography sections using templates (no AI)."""

    def __init__(self):
        """Initialize template generator."""
        pass

    def generate_introduction(self, context: PersonContext) -> str:
        """Generate introduction section."""
        lines = []

        # Basic intro: Name was born on [date] in [place]
        birth_info = ""
        if context.birth_date:
            birth_info = f" on {context.birth_date}"
        if context.birth_place:
            birth_info += f" in {context.birth_place}"

        if birth_info:
            lines.append(f"{context.full_name} was born{birth_info}.")
        else:
            lines.append(f"{context.full_name}'s birth date and place are not recorded.")

        # Parents
        if context.father_name or context.mother_name:
            parent_info = []
            if context.father_name:
                parent_info.append(context.father_name)
            if context.mother_name:
                parent_info.append(context.mother_name)
            parent_str = " and ".join(parent_info)
            pronoun = "He" if context.sex == 0 else "She" if context.sex == 1 else "They"
            verb = "was" if context.sex != 2 else "were"
            lines.append(f"{pronoun} {verb} the child of {parent_str}.")

        # Death information (if applicable)
        if context.death_date or context.death_place:
            death_info = ""
            pronoun = "He" if context.sex == 0 else "She" if context.sex == 1 else "They"
            verb = "died" if context.sex != 2 else "died"

            if context.death_date:
                death_info = f" on {context.death_date}"
            if context.death_place:
                death_info += f" in {context.death_place}"

            # Calculate age at death if both years available
            age = self._calculate_age_at_death(context.birth_year, context.death_year)
            if age is not None:
                death_info += f" at the age of {age}"

            lines.append(f"{pronoun} {verb}{death_info}.")

        return " ".join(lines)

    def generate_early_life(self, context: PersonContext) -> str:
        """Generate early life section."""
        if not context.siblings:
            return ""

        sibling_count = len(context.siblings)
        pronoun = "He" if context.sex == 0 else "She" if context.sex == 1 else "They"
        verb = "grew" if context.sex != 2 else "grew"

        if sibling_count == 0:
            return f"{pronoun} {verb} up as an only child."
        elif sibling_count == 1:
            return f"{pronoun} had one sibling."
        else:
            return f"{pronoun} had {sibling_count} siblings."

    def generate_education(self, context: PersonContext) -> str:
        """Generate education section."""
        if not context.education_events:
            return ""

        lines = []
        for event in context.education_events:
            event_desc = f"{event.date}" if event.date else "At an unknown date"
            if event.place:
                event_desc += f" in {event.place}"
            if event.details:
                event_desc += f", {event.details}"
            lines.append(event_desc + ".")

        return " ".join(lines)

    def generate_career(self, context: PersonContext) -> str:
        """Generate career section."""
        if not context.occupation_events:
            return ""

        lines = []
        for event in context.occupation_events:
            if event.details:
                desc = f"{context.given_name} worked as {event.details}"
                if event.date:
                    desc += f" in {event.date}"
                if event.place:
                    desc += f" in {event.place}"
                lines.append(desc + ".")

        return " ".join(lines)

    def generate_marriage_family(self, context: PersonContext) -> str:
        """Generate marriage and family section."""
        lines = []

        # Marriages
        if context.spouses:
            for spouse in context.spouses:
                spouse_name = format_full_name(
                    given=get_row_value(spouse, "Given"),
                    surname=get_row_value(spouse, "Surname"),
                )
                marriage_date = get_row_value(spouse, "MarriageDate")
                if marriage_date and not is_unknown_date(marriage_date):
                    try:
                        parsed = parse_rm_date(marriage_date)
                        date_str = parsed.format_display()
                        lines.append(f"{context.given_name} married {spouse_name} on {date_str}.")
                    except Exception:
                        lines.append(f"{context.given_name} married {spouse_name}.")
                else:
                    lines.append(f"{context.given_name} married {spouse_name}.")

        # Children
        if context.children:
            child_count = len(context.children)
            if child_count == 1:
                lines.append("They had one child.")
            else:
                lines.append(f"They had {child_count} children.")

        return " ".join(lines)

    def generate_later_life(self, context: PersonContext) -> str:
        """Generate later life section."""
        # Could include residence changes, later events
        if context.residence_events:
            places = [e.place for e in context.residence_events if e.place]
            if places:
                return f"{context.given_name} resided in {', '.join(places[:3])}."
        return ""

    def generate_death_legacy(self, context: PersonContext) -> str:
        """Generate death and legacy section."""
        if not context.death_date and not context.death_place:
            return ""

        death_info = ""
        if context.death_date:
            death_info = f" on {context.death_date}"
        if context.death_place:
            death_info += f" in {context.death_place}"

        pronoun = "He" if context.sex == 0 else "She" if context.sex == 1 else "They"
        verb = "died" if context.sex != 2 else "died"

        return f"{pronoun} {verb}{death_info}."

    def parse_ai_response(self, response_text: str) -> dict[str, str]:
        """Parse AI-generated biography into sections."""
        # Simple parser - looks for section headers
        sections = {
            "introduction": "",
            "early_life": "",
            "education": "",
            "career": "",
            "marriage_family": "",
            "later_life": "",
            "death_legacy": "",
        }

        # Split by markdown headers and categorize
        # This is a simplified version - production would use more robust parsing
        lines = response_text.split("\n")
        current_section = None
        current_text = []

        for line in lines:
            if line.startswith("##"):
                # Save previous section
                if current_section and current_text:
                    sections[current_section] = "\n".join(current_text).strip()

                # Detect new section
                header = line.lower()
                if "introduction" in header or "birth" in header:
                    current_section = "introduction"
                elif "early life" in header or "family background" in header:
                    current_section = "early_life"
                elif "education" in header:
                    current_section = "education"
                elif "career" in header or "occupation" in header:
                    current_section = "career"
                elif "marriage" in header or "family" in header:
                    current_section = "marriage_family"
                elif "later life" in header:
                    current_section = "later_life"
                elif "death" in header or "legacy" in header:
                    current_section = "death_legacy"
                else:
                    current_section = None

                current_text = []
            elif current_section:
                current_text.append(line)

        # Save final section
        if current_section and current_text:
            sections[current_section] = "\n".join(current_text).strip()

        return sections

    @staticmethod
    def _calculate_age_at_death(birth_year: int | None, death_year: int | None) -> int | None:
        """Calculate age at death from birth and death years."""
        if birth_year and death_year:
            return death_year - birth_year
        return None
