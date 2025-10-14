"""
Unit tests for rmlib.parsers.place_parser module.

Tests place name parsing for:
- Comma-delimited hierarchy parsing
- Level extraction (city, county, state, country)
- Formatting (short, medium, full)
- Coordinate conversion
- Validation
"""

from rmagent.rmlib.parsers.place_parser import (
    PlaceType,
    convert_coordinates,
    format_place_medium,
    format_place_short,
    get_place_level,
    get_place_short,
    parse_place_name,
    reverse_place_name,
    validate_place_format,
)


class TestParsePlaceName:
    """Test parse_place_name function."""

    def test_parse_empty_place(self):
        """Test parsing empty/null place."""
        assert parse_place_name(None) is None
        assert parse_place_name("") is None
        assert parse_place_name("   ") is None

    def test_parse_4_level_us_place(self):
        """Test parsing standard 4-level US place."""
        place = parse_place_name("Baltimore, Baltimore, Maryland, United States")

        assert place is not None
        assert place.full == "Baltimore, Baltimore, Maryland, United States"
        assert place.count == 4
        assert place.city == "Baltimore"
        assert place.county == "Baltimore"
        assert place.state == "Maryland"
        assert place.country == "United States"
        assert place.is_us_place is True
        assert place.is_standard_hierarchy is True

    def test_parse_3_level_place(self):
        """Test parsing 3-level place."""
        place = parse_place_name("Abbeville, South Carolina, United States")

        assert place is not None
        assert place.count == 3
        assert place.city == "Abbeville"
        assert place.county == "South Carolina"  # Actually state, but stored as level 1
        assert place.state == "United States"  # Actually country, stored as level 2
        assert place.country is None
        assert place.is_standard_hierarchy is False

    def test_parse_2_level_place(self):
        """Test parsing 2-level place."""
        place = parse_place_name("Alabama, United States")

        assert place is not None
        assert place.count == 2
        assert place.city == "Alabama"
        assert place.county == "United States"
        assert place.state is None
        assert place.country is None

    def test_parse_1_level_place(self):
        """Test parsing single-level place."""
        place = parse_place_name("Ireland")

        assert place is not None
        assert place.count == 1
        assert place.city == "Ireland"
        assert place.county is None
        assert place.state is None
        assert place.country is None

    def test_parse_5_level_detailed_place(self):
        """Test parsing 5-level place (cemetery, address)."""
        place = parse_place_name("Old Iams Cemetery, Trotwood, Montgomery, Ohio, United States")

        assert place is not None
        assert place.count == 5
        assert place.city == "Old Iams Cemetery"
        assert place.county == "Trotwood"
        assert place.state == "Montgomery"
        assert place.country == "Ohio"
        assert len(place.levels) == 5

    def test_parse_with_extra_whitespace(self):
        """Test parsing with extra whitespace."""
        place = parse_place_name(" Baltimore , Baltimore , Maryland , United States ")

        assert place is not None
        assert place.count == 4
        assert place.city == "Baltimore"
        assert place.state == "Maryland"

    def test_parse_international_place(self):
        """Test parsing international place (UK)."""
        place = parse_place_name("London, London, England, United Kingdom")

        assert place is not None
        assert place.count == 4
        assert place.city == "London"
        assert place.state == "England"
        assert place.country == "United Kingdom"
        assert place.is_us_place is False


class TestShortFormProperty:
    """Test ParsedPlace.short_form property."""

    def test_short_form_us_4_level(self):
        """Test short form for 4-level US place."""
        place = parse_place_name("Baltimore, Baltimore, Maryland, United States")
        assert place.short_form == "Baltimore, Maryland"

    def test_short_form_international_4_level(self):
        """Test short form for 4-level international place."""
        place = parse_place_name("London, London, England, United Kingdom")
        assert place.short_form == "London, England"

    def test_short_form_3_level(self):
        """Test short form for 3-level place."""
        place = parse_place_name("Abbeville, South Carolina, United States")
        assert place.short_form == "Abbeville, United States"

    def test_short_form_1_level(self):
        """Test short form for single-level place."""
        place = parse_place_name("Ireland")
        assert place.short_form == "Ireland"


class TestMediumFormProperty:
    """Test ParsedPlace.medium_form property."""

    def test_medium_form_4_level(self):
        """Test medium form for 4-level place."""
        place = parse_place_name("Baltimore, Baltimore, Maryland, United States")
        assert place.medium_form == "Baltimore, Baltimore, Maryland"

    def test_medium_form_3_level(self):
        """Test medium form for 3-level place."""
        place = parse_place_name("Abbeville, South Carolina, United States")
        assert place.medium_form == "Abbeville, South Carolina, United States"

    def test_medium_form_1_level(self):
        """Test medium form for single-level place."""
        place = parse_place_name("Ireland")
        assert place.medium_form == "Ireland"


class TestGetPlaceLevel:
    """Test get_place_level function."""

    def test_get_level_0_city(self):
        """Test getting level 0 (city)."""
        assert get_place_level("Baltimore, Baltimore, Maryland, United States", 0) == "Baltimore"

    def test_get_level_1_county(self):
        """Test getting level 1 (county)."""
        assert get_place_level("Baltimore, Baltimore, Maryland, United States", 1) == "Baltimore"

    def test_get_level_2_state(self):
        """Test getting level 2 (state)."""
        assert get_place_level("Baltimore, Baltimore, Maryland, United States", 2) == "Maryland"

    def test_get_level_3_country(self):
        """Test getting level 3 (country)."""
        assert get_place_level("Baltimore, Baltimore, Maryland, United States", 3) == "United States"

    def test_get_level_out_of_range(self):
        """Test getting level that doesn't exist."""
        assert get_place_level("Ireland", 1) is None
        assert get_place_level("Ireland", 5) is None

    def test_get_level_empty_place(self):
        """Test getting level from empty place."""
        assert get_place_level(None, 0) is None
        assert get_place_level("", 0) is None


class TestGetPlaceShort:
    """Test get_place_short function."""

    def test_get_short_us_place_2_levels(self):
        """Test short form for US place (skips county)."""
        assert get_place_short("Baltimore, Baltimore, Maryland, United States", 2) == "Baltimore, Maryland"

    def test_get_short_international_place_2_levels(self):
        """Test short form for international place."""
        assert get_place_short("London, London, England, United Kingdom", 2) == "London, London"

    def test_get_short_3_levels(self):
        """Test short form with 3 levels."""
        place = "Baltimore, Baltimore, Maryland, United States"
        assert get_place_short(place, 3) == "Baltimore, Baltimore, Maryland"

    def test_get_short_empty_place(self):
        """Test short form of empty place."""
        assert get_place_short(None, 2) is None
        assert get_place_short("", 2) is None


class TestFormatPlaceShort:
    """Test format_place_short function."""

    def test_format_us_4_level(self):
        """Test formatting US 4-level place."""
        assert format_place_short("Baltimore, Baltimore, Maryland, United States") == "Baltimore, Maryland"

    def test_format_us_3_level(self):
        """Test formatting US 3-level place."""
        # 3-level place: City, State, Country - format returns City, Country (level 0 and 2)
        assert format_place_short("Abbeville, South Carolina, United States") == "Abbeville, United States"

    def test_format_international_4_level(self):
        """Test formatting international 4-level place."""
        assert format_place_short("London, London, England, United Kingdom") == "London, England"

    def test_format_1_level(self):
        """Test formatting single-level place."""
        assert format_place_short("Ireland") == "Ireland"

    def test_format_empty_place(self):
        """Test formatting empty place."""
        assert format_place_short(None) == ""
        assert format_place_short("") == ""


class TestFormatPlaceMedium:
    """Test format_place_medium function."""

    def test_format_medium_4_level(self):
        """Test medium format for 4-level place."""
        assert format_place_medium("Baltimore, Baltimore, Maryland, United States") == "Baltimore, Baltimore, Maryland"

    def test_format_medium_3_level(self):
        """Test medium format for 3-level place."""
        assert (
            format_place_medium("Abbeville, South Carolina, United States")
            == "Abbeville, South Carolina, United States"
        )

    def test_format_medium_1_level(self):
        """Test medium format for single-level place."""
        assert format_place_medium("Ireland") == "Ireland"

    def test_format_medium_empty(self):
        """Test medium format for empty place."""
        assert format_place_medium(None) == ""
        assert format_place_medium("") == ""


class TestConvertCoordinates:
    """Test convert_coordinates function."""

    def test_convert_valid_coordinates(self):
        """Test converting valid coordinates."""
        lat, lon = convert_coordinates(392904000, -766224000)
        assert lat == 39.2904
        assert lon == -76.6224

    def test_convert_zero_coordinates(self):
        """Test handling zero coordinates."""
        lat, lon = convert_coordinates(0, 0)
        assert lat is None
        assert lon is None

    def test_convert_none_coordinates(self):
        """Test handling None coordinates."""
        lat, lon = convert_coordinates(None, None)
        assert lat is None
        assert lon is None

    def test_convert_partial_none(self):
        """Test handling partial None coordinates."""
        lat, lon = convert_coordinates(392904000, None)
        assert lat is None
        assert lon is None

        lat, lon = convert_coordinates(None, -766224000)
        assert lat is None
        assert lon is None

    def test_convert_negative_latitude(self):
        """Test converting negative latitude (southern hemisphere)."""
        lat, lon = convert_coordinates(-334610000, 1512920000)
        assert lat == -33.461
        assert lon == 151.292  # Sydney, Australia


class TestReversePlaceName:
    """Test reverse_place_name function."""

    def test_reverse_4_level_place(self):
        """Test reversing 4-level place."""
        reversed_place = reverse_place_name("Baltimore, Baltimore, Maryland, United States")
        assert reversed_place == "United States, Maryland, Baltimore, Baltimore"

    def test_reverse_3_level_place(self):
        """Test reversing 3-level place."""
        reversed_place = reverse_place_name("Abbeville, South Carolina, United States")
        assert reversed_place == "United States, South Carolina, Abbeville"

    def test_reverse_1_level_place(self):
        """Test reversing single-level place."""
        reversed_place = reverse_place_name("Ireland")
        assert reversed_place == "Ireland"

    def test_reverse_empty_place(self):
        """Test reversing empty place."""
        assert reverse_place_name(None) is None
        assert reverse_place_name("") is None


class TestValidatePlaceFormat:
    """Test validate_place_format function."""

    def test_validate_valid_place(self):
        """Test validating valid place format."""
        issues = validate_place_format("Baltimore, Maryland")
        assert len(issues) == 0

    def test_validate_leading_trailing_whitespace(self):
        """Test detecting leading/trailing whitespace."""
        issues = validate_place_format(" Baltimore, Maryland ")
        assert "Leading or trailing whitespace" in issues

    def test_validate_double_comma(self):
        """Test detecting empty hierarchy level."""
        issues = validate_place_format("Baltimore,, Maryland")
        assert "Empty hierarchy level (double comma)" in issues

    def test_validate_missing_space_after_comma(self):
        """Test detecting missing space after comma."""
        issues = validate_place_format("Baltimore,Maryland")
        assert "Missing space after comma" in issues

    def test_validate_multiple_issues(self):
        """Test detecting multiple issues."""
        issues = validate_place_format(" Baltimore,Maryland,, United States ")
        assert len(issues) >= 2
        assert "Leading or trailing whitespace" in issues
        # Double comma issue is detected first, so we don't also detect missing space
        assert "Empty hierarchy level (double comma)" in issues


class TestPlaceTypeEnum:
    """Test PlaceType enumeration."""

    def test_place_type_values(self):
        """Test PlaceType enum values."""
        assert PlaceType.STANDARD == 0
        assert PlaceType.OTHER == 1
        assert PlaceType.DETAIL == 2

    def test_place_type_names(self):
        """Test PlaceType enum names."""
        assert PlaceType.STANDARD.name == "STANDARD"
        assert PlaceType.OTHER.name == "OTHER"
        assert PlaceType.DETAIL.name == "DETAIL"


class TestRealWorldExamples:
    """Test with real-world place examples."""

    def test_pittsburgh_place(self):
        """Test Pittsburgh place."""
        place = parse_place_name("Pittsburgh, Allegheny, Pennsylvania, United States")

        assert place.city == "Pittsburgh"
        assert place.county == "Allegheny"
        assert place.state == "Pennsylvania"
        assert place.country == "United States"
        assert place.short_form == "Pittsburgh, Pennsylvania"

    def test_cemetery_detail_place(self):
        """Test cemetery detail place."""
        place = parse_place_name("Old Iams Cemetery, Trotwood, Montgomery, Ohio, United States")

        assert place.count == 5
        assert place.levels[0] == "Old Iams Cemetery"
        assert place.levels[4] == "United States"

    def test_address_detail_place(self):
        """Test address detail place."""
        place = parse_place_name("12 Alcazar Ave, Kingston, Ulster, New York, United States")

        assert place.count == 5
        assert place.levels[0] == "12 Alcazar Ave"

    def test_international_uk_place(self):
        """Test UK place."""
        place = parse_place_name("London, London, England, United Kingdom")

        assert place.city == "London"
        assert place.country == "United Kingdom"
        assert place.is_us_place is False
        assert place.short_form == "London, England"

    def test_state_only_place(self):
        """Test state-only place."""
        place = parse_place_name("Pennsylvania")

        assert place.count == 1
        assert place.city == "Pennsylvania"
        assert place.short_form == "Pennsylvania"
