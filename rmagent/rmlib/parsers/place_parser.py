"""
RootsMagic Place Parser

Parses comma-delimited place names from RootsMagic databases.

Place Format: City, County, State/Province, Country
Example: "Baltimore, Baltimore, Maryland, United States"

Reference: RM11_Place_Format.md
"""

from dataclasses import dataclass
from enum import IntEnum


class PlaceType(IntEnum):
    """PlaceType values (from PlaceTable)."""

    STANDARD = 0  # Regular geographic location (88.8%)
    OTHER = 1  # Other/Unknown (4.3%)
    DETAIL = 2  # Detail place - specific location within master (6.9%)


@dataclass
class ParsedPlace:
    """Parsed place name with hierarchy levels."""

    # Original place name
    full: str

    # Individual hierarchy levels
    levels: list[str]

    # Number of levels
    count: int

    # Standard hierarchy components (4-level)
    city: str | None = None
    county: str | None = None
    state: str | None = None
    country: str | None = None

    @property
    def is_us_place(self) -> bool:
        """True if this appears to be a US place."""
        return self.country == "United States"

    @property
    def is_standard_hierarchy(self) -> bool:
        """True if this has 4 levels (standard hierarchy)."""
        return self.count == 4

    @property
    def short_form(self) -> str:
        """Short form: City, State (for US) or City, Country."""
        if self.count >= 4 and self.is_us_place:
            return f"{self.city}, {self.state}"
        elif self.count >= 3:
            return f"{self.city}, {self.levels[2]}"
        else:
            return self.full

    @property
    def medium_form(self) -> str:
        """Medium form: City, County, State."""
        if self.count >= 3:
            return ", ".join(self.levels[:3])
        else:
            return self.full


def parse_place_name(place_name: str | None) -> ParsedPlace | None:
    """
    Parse comma-delimited place name into hierarchy levels.

    Args:
        place_name: Place name in comma-delimited format

    Returns:
        ParsedPlace object with hierarchy levels, or None if place_name is empty

    Example:
        >>> place = parse_place_name("Baltimore, Baltimore, Maryland, United States")
        >>> place.city
        'Baltimore'
        >>> place.state
        'Maryland'
        >>> place.short_form
        'Baltimore, Maryland'
    """
    if not place_name:
        return None

    # Strip whitespace
    place_name = place_name.strip()

    if not place_name:
        return None

    # Split on comma-space
    levels = [level.strip() for level in place_name.split(",")]

    # Remove empty levels
    levels = [level for level in levels if level]

    count = len(levels)

    # Extract standard hierarchy components
    city = levels[0] if count >= 1 else None
    county = levels[1] if count >= 2 else None
    state = levels[2] if count >= 3 else None
    country = levels[3] if count >= 4 else None

    return ParsedPlace(
        full=place_name,
        levels=levels,
        count=count,
        city=city,
        county=county,
        state=state,
        country=country,
    )


def get_place_level(place_name: str | None, level: int) -> str | None:
    """
    Get specific hierarchy level from place name.

    Args:
        place_name: Place name in comma-delimited format
        level: 0=city, 1=county, 2=state, 3=country

    Returns:
        Level value or None if level doesn't exist

    Example:
        >>> get_place_level("Baltimore, Baltimore, Maryland, United States", 2)
        'Maryland'
    """
    if not place_name:
        return None

    levels = [level.strip() for level in place_name.split(",")]
    return levels[level].strip() if level < len(levels) else None


def get_place_short(place_name: str | None, max_levels: int = 2) -> str | None:
    """
    Get shortened place name (first N levels).

    Args:
        place_name: Place name in comma-delimited format
        max_levels: Maximum number of levels to include (default 2)

    Returns:
        Shortened place name or None

    Example:
        >>> get_place_short("Baltimore, Baltimore, Maryland, United States", 2)
        'Baltimore, Maryland'
    """
    if not place_name:
        return None

    levels = [level.strip() for level in place_name.split(",")]

    # For US places, skip county (level 1) to get City, State
    if len(levels) >= 4 and levels[3] == "United States" and max_levels == 2:
        return f"{levels[0]}, {levels[2]}"

    return ", ".join(levels[:max_levels])


def format_place_short(place_name: str | None) -> str:
    """
    Format place as 'City, State' for US locations.

    Args:
        place_name: Place name in comma-delimited format

    Returns:
        Short formatted place name

    Example:
        >>> format_place_short("Baltimore, Baltimore, Maryland, United States")
        'Baltimore, Maryland'
        >>> format_place_short("London, London, England, United Kingdom")
        'London, England'
    """
    if not place_name:
        return ""

    levels = [level.strip() for level in place_name.split(",")]

    if len(levels) >= 4 and levels[3] == "United States":
        return f"{levels[0]}, {levels[2]}"  # City, State
    elif len(levels) >= 3:
        return f"{levels[0]}, {levels[2]}"  # City, Country/Province
    else:
        return place_name


def format_place_medium(place_name: str | None) -> str:
    """
    Format place as 'City, County, State'.

    Args:
        place_name: Place name in comma-delimited format

    Returns:
        Medium formatted place name

    Example:
        >>> format_place_medium("Baltimore, Baltimore, Maryland, United States")
        'Baltimore, Baltimore, Maryland'
    """
    if not place_name:
        return ""

    levels = [level.strip() for level in place_name.split(",")]

    if len(levels) >= 3:
        return ", ".join(levels[:3])
    else:
        return place_name


def convert_coordinates(lat_int: int | None, lon_int: int | None) -> tuple[float | None, float | None]:
    """
    Convert integer coordinates to decimal degrees.

    RootsMagic stores coordinates as integers (degrees × 10,000,000).

    Args:
        lat_int: Latitude as integer
        lon_int: Longitude as integer

    Returns:
        Tuple of (latitude, longitude) in decimal degrees, or (None, None)

    Example:
        >>> convert_coordinates(392904000, -766224000)
        (39.2904, -76.6224)
    """
    if not lat_int or not lon_int:
        return None, None

    latitude = lat_int / 10_000_000.0
    longitude = lon_int / 10_000_000.0

    return latitude, longitude


def reverse_place_name(place_name: str | None) -> str | None:
    """
    Reverse place name hierarchy for sorting.

    Converts "City, County, State, Country" to "Country, State, County, City"

    Args:
        place_name: Place name in comma-delimited format

    Returns:
        Reversed place name or None

    Example:
        >>> reverse_place_name("Baltimore, Baltimore, Maryland, United States")
        'United States, Maryland, Baltimore, Baltimore'
    """
    if not place_name:
        return None

    levels = [level.strip() for level in place_name.split(",")]
    return ", ".join(reversed(levels))


def validate_place_format(place_name: str) -> list[str]:
    """
    Validate place name format and return list of issues.

    Args:
        place_name: Place name to validate

    Returns:
        List of validation issues (empty if valid)

    Example:
        >>> validate_place_format("Baltimore, Maryland")
        []
        >>> validate_place_format(" Baltimore,Maryland ")
        ['Leading or trailing whitespace', 'Missing space after comma']
    """
    issues = []

    if not place_name:
        return issues

    # Check for leading/trailing whitespace
    if place_name.startswith(" ") or place_name.endswith(" "):
        issues.append("Leading or trailing whitespace")

    # Check for empty hierarchy levels (double comma)
    if ",," in place_name:
        issues.append("Empty hierarchy level (double comma)")

    # Check for missing space after comma
    if ", " not in place_name and "," in place_name:
        issues.append("Missing space after comma")

    return issues
