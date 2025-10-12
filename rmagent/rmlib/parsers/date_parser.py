"""
RootsMagic Date Parser

Parses the proprietary 24-character fixed-width date format used in RootsMagic 11.

Reference: RM11_Date_Format.md

Format: D.+yyyymmdd..+yyyymmdd..
Position 1: Date type (., D, Q, T)
Position 2: Date modifier (., -, A, B, F, I, O, R, S, T, U, Y)
Position 3: First date era (+, -)
Positions 4-7: First date year (0000-9999)
Positions 8-9: First date month (00-12)
Positions 10-11: First date day (00-31)
Position 12: First date double date indicator (/, .)
Position 13: First date qualifier (., ?, 1-6, A, C, E, L, S)
Position 14: Second date era (+, -)
Positions 15-18: Second date year (0000-9999)
Positions 19-20: Second date month (00-12)
Positions 21-22: Second date day (00-31)
Position 23: Second date double date indicator (/, .)
Position 24: Second date qualifier
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Constants for unknown/missing dates
UNKNOWN_SORT_DATE = 9223372036854775807


class DateType(Enum):
    """Date type indicator (Position 1)."""

    NULL = "."
    STANDARD = "D"
    QUAKER = "Q"
    TEXT = "T"


class DateModifier(Enum):
    """Date modifier (Position 2)."""

    NONE = "."
    RANGE = "-"
    AFTER = "A"
    BEFORE = "B"
    FROM = "F"
    SINCE = "I"
    OR = "O"
    BETWEEN = "R"
    FROM_TO = "S"
    TO = "T"
    UNTIL = "U"
    BY = "Y"


class DateQualifier(Enum):
    """Date qualifier (Position 13/24)."""

    NONE = "."
    MAYBE = "?"
    PERHAPS = "1"
    APPARENTLY = "2"
    LIKELY = "3"
    POSSIBLY = "4"
    PROBABLY = "5"
    CERTAINLY = "6"
    ABOUT = "A"
    CIRCA = "C"
    ESTIMATED = "E"
    CALCULATED = "L"
    SAY = "S"


# Display mappings
MODIFIER_DISPLAY = {
    DateModifier.NONE: "",
    DateModifier.RANGE: "–",
    DateModifier.AFTER: "Aft",
    DateModifier.BEFORE: "Bef",
    DateModifier.FROM: "From",
    DateModifier.SINCE: "Since",
    DateModifier.OR: "or",
    DateModifier.BETWEEN: "Bet",
    DateModifier.FROM_TO: "From",
    DateModifier.TO: "To",
    DateModifier.UNTIL: "Until",
    DateModifier.BY: "By",
}

QUALIFIER_DISPLAY = {
    DateQualifier.NONE: "",
    DateQualifier.MAYBE: "Maybe",
    DateQualifier.PERHAPS: "Prhps",
    DateQualifier.APPARENTLY: "Appar",
    DateQualifier.LIKELY: "Lkly",
    DateQualifier.POSSIBLY: "Poss",
    DateQualifier.PROBABLY: "Prob",
    DateQualifier.CERTAINLY: "Cert",
    DateQualifier.ABOUT: "Abt",
    DateQualifier.CIRCA: "Ca",
    DateQualifier.ESTIMATED: "Est",
    DateQualifier.CALCULATED: "Calc",
    DateQualifier.SAY: "Say",
}

MONTH_NAMES = [
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


@dataclass
class RMDate:
    """Parsed RootsMagic date with all components."""

    # Date type and modifier
    date_type: DateType
    modifier: DateModifier

    # First date components
    year: int | None = None
    month: int | None = None
    day: int | None = None
    is_bc: bool = False
    is_double_date: bool = False
    qualifier: DateQualifier | None = None

    # Second date components (for ranges)
    year2: int | None = None
    month2: int | None = None
    day2: int | None = None
    is_bc2: bool = False
    is_double_date2: bool = False
    qualifier2: DateQualifier | None = None

    # Text date (for DateType.TEXT)
    text: str | None = None

    @property
    def is_null(self) -> bool:
        """True if this is a null/empty date."""
        return self.date_type == DateType.NULL

    @property
    def is_range(self) -> bool:
        """True if this is a date range (has second date)."""
        return self.year2 is not None and self.year2 > 0

    @property
    def is_partial(self) -> bool:
        """True if this is a partial date (missing day or month)."""
        if self.is_null or self.date_type == DateType.TEXT:
            return False
        return self.day is None or self.month is None

    def to_datetime(self) -> datetime | None:
        """
        Convert to Python datetime object (if possible).

        Returns None if:
        - Date is null, text, or partial
        - Date is BC
        - Date is a range
        """
        if (
            self.is_null
            or self.date_type == DateType.TEXT
            or self.is_partial
            or self.is_bc
            or self.is_range
        ):
            return None

        try:
            return datetime(self.year, self.month, self.day)
        except (ValueError, TypeError):
            return None

    def format_display(self) -> str:
        """Format date for human-readable display."""
        if self.is_null:
            return ""

        if self.date_type == DateType.TEXT:
            return self.text or ""

        # Format first date
        date1_str = self._format_single_date(
            self.year, self.month, self.day, self.is_bc, self.is_double_date, self.qualifier
        )

        # Handle ranges
        if self.is_range:
            date2_str = self._format_single_date(
                self.year2,
                self.month2,
                self.day2,
                self.is_bc2,
                self.is_double_date2,
                self.qualifier2,
            )

            # Format based on modifier
            if self.modifier == DateModifier.BETWEEN:
                return f"Bet {date1_str} and {date2_str}"
            elif self.modifier == DateModifier.FROM_TO:
                return f"From {date1_str} to {date2_str}"
            elif self.modifier == DateModifier.OR:
                return f"{date1_str} or {date2_str}"
            elif self.modifier == DateModifier.RANGE:
                return f"{date1_str}–{date2_str}"
            else:
                return f"{date1_str} to {date2_str}"

        # Single date with modifier
        modifier_prefix = MODIFIER_DISPLAY.get(self.modifier, "")
        if modifier_prefix:
            return f"{modifier_prefix} {date1_str}"

        return date1_str

    def _format_single_date(
        self,
        year: int | None,
        month: int | None,
        day: int | None,
        is_bc: bool,
        is_double_date: bool,
        qualifier: DateQualifier | None,
    ) -> str:
        """Format a single date component."""
        parts = []

        # Add qualifier prefix
        qual_str = QUALIFIER_DISPLAY.get(qualifier, "") if qualifier else ""
        if qual_str:
            parts.append(qual_str)

        # Format date parts
        if day and month and year:
            # Complete date: "2 Mar 1896"
            month_name = MONTH_NAMES[month] if 1 <= month <= 12 else "???"
            year_str = f"{year}/{(year+1) % 100:02d}" if is_double_date else str(year)
            parts.append(f"{day} {month_name} {year_str}")
        elif month and year:
            # Month and year: "Mar 1896"
            month_name = MONTH_NAMES[month] if 1 <= month <= 12 else "???"
            year_str = f"{year}/{(year+1) % 100:02d}" if is_double_date else str(year)
            parts.append(f"{month_name} {year_str}")
        elif year:
            # Year only: "1896"
            year_str = f"{year}/{(year+1) % 100:02d}" if is_double_date else str(year)
            parts.append(year_str)
        elif day and month:
            # Day and month without year: "2 Mar"
            month_name = MONTH_NAMES[month] if 1 <= month <= 12 else "???"
            parts.append(f"{day} {month_name}")
        elif month:
            # Month only: "Mar"
            month_name = MONTH_NAMES[month] if 1 <= month <= 12 else "???"
            parts.append(month_name)
        elif day:
            # Day only: "2"
            parts.append(str(day))

        # Add BC suffix
        if is_bc and year:
            parts.append("BC")

        return " ".join(parts)


def parse_rm_date(date_str: str | None) -> RMDate:
    """
    Parse a RootsMagic 24-character date string.

    Args:
        date_str: 24-character date string or None

    Returns:
        RMDate object with parsed components

    Example:
        >>> date = parse_rm_date("D.+18960302..+00000000..")
        >>> date.year, date.month, date.day
        (1896, 3, 2)
        >>> date.format_display()
        '2 Mar 1896'
    """
    # Handle null/empty dates
    if not date_str or len(date_str) == 0 or date_str[0] == ".":
        return RMDate(date_type=DateType.NULL, modifier=DateModifier.NONE)

    # Handle text dates
    if date_str[0] == "T":
        return RMDate(
            date_type=DateType.TEXT,
            modifier=DateModifier.NONE,
            text=date_str[1:] if len(date_str) > 1 else "",
        )

    # Ensure we have at least 24 characters
    if len(date_str) < 24:
        date_str = date_str.ljust(24, ".")

    # Parse date type
    date_type_char = date_str[0]
    date_type = DateType.STANDARD if date_type_char == "D" else DateType.QUAKER

    # Parse date modifier
    modifier_char = date_str[1]
    modifier = _parse_modifier(modifier_char)

    # Parse first date
    year, month, day, is_bc, is_double_date, qualifier = _parse_date_components(date_str[2:13])

    # Parse second date (for ranges)
    year2, month2, day2, is_bc2, is_double_date2, qualifier2 = _parse_date_components(
        date_str[13:24]
    )

    return RMDate(
        date_type=date_type,
        modifier=modifier,
        year=year,
        month=month,
        day=day,
        is_bc=is_bc,
        is_double_date=is_double_date,
        qualifier=qualifier,
        year2=year2,
        month2=month2,
        day2=day2,
        is_bc2=is_bc2,
        is_double_date2=is_double_date2,
        qualifier2=qualifier2,
    )


def _parse_modifier(char: str) -> DateModifier:
    """Parse date modifier character."""
    for modifier in DateModifier:
        if modifier.value == char:
            return modifier
    return DateModifier.NONE


def _parse_qualifier(char: str) -> DateQualifier | None:
    """Parse date qualifier character."""
    for qualifier in DateQualifier:
        if qualifier.value == char:
            return qualifier if qualifier != DateQualifier.NONE else None
    return None


def _parse_date_components(
    date_part: str,
) -> tuple[int | None, int | None, int | None, bool, bool, DateQualifier | None]:
    """
    Parse an 11-character date component.

    Format: +yyyymmdd..
    Position 0: Era (+/-)
    Positions 1-4: Year
    Positions 5-6: Month
    Positions 7-8: Day
    Position 9: Double date indicator
    Position 10: Qualifier

    Returns:
        (year, month, day, is_bc, is_double_date, qualifier)
    """
    if len(date_part) < 11:
        return None, None, None, False, False, None

    # Parse era
    is_bc = date_part[0] == "-"

    # Parse year (0000 = not specified)
    try:
        year = int(date_part[1:5])
        year = year if year > 0 else None
    except ValueError:
        year = None

    # Parse month (00 = not specified)
    try:
        month = int(date_part[5:7])
        month = month if month > 0 else None
    except ValueError:
        month = None

    # Parse day (00 = not specified)
    try:
        day = int(date_part[7:9])
        day = day if day > 0 else None
    except ValueError:
        day = None

    # Parse double date indicator
    is_double_date = date_part[9] == "/"

    # Parse qualifier
    qualifier = _parse_qualifier(date_part[10])

    return year, month, day, is_bc, is_double_date, qualifier


def is_unknown_date(sort_date: int | None) -> bool:
    """
    Check if a SortDate value represents an unknown date.

    Args:
        sort_date: SortDate value from database

    Returns:
        True if date is unknown/missing
    """
    return sort_date is None or sort_date == UNKNOWN_SORT_DATE
