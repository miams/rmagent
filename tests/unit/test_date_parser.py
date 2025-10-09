"""
Unit tests for rmlib.parsers.date_parser module.

Tests the RootsMagic 24-character date format parser for:
- Date component extraction
- Date modifiers and qualifiers
- Date ranges
- Partial dates
- BC/AD dates
- Display formatting
- Datetime conversion
"""

import pytest
from datetime import datetime

from rmagent.rmlib.parsers.date_parser import (
    parse_rm_date,
    is_unknown_date,
    RMDate,
    DateType,
    DateModifier,
    DateQualifier,
    UNKNOWN_SORT_DATE,
)


class TestBasicDates:
    """Test basic date parsing."""

    def test_null_date(self):
        """Test parsing null/empty dates."""
        # Null date (all periods)
        date = parse_rm_date("........................")
        assert date.is_null is True
        assert date.date_type == DateType.NULL
        assert date.format_display() == ""

        # Empty string
        date2 = parse_rm_date("")
        assert date2.is_null is True

        # None
        date3 = parse_rm_date(None)
        assert date3.is_null is True

    def test_complete_date(self):
        """Test parsing complete date."""
        # 2 Mar 1896
        date = parse_rm_date("D.+18960302..+00000000..")
        assert date.date_type == DateType.STANDARD
        assert date.modifier == DateModifier.NONE
        assert date.year == 1896
        assert date.month == 3
        assert date.day == 2
        assert date.is_bc is False
        assert date.qualifier is None
        assert date.is_range is False
        assert date.format_display() == "2 Mar 1896"

    def test_year_only(self):
        """Test parsing year-only date."""
        # 1900
        date = parse_rm_date("D.+19000000..+00000000..")
        assert date.year == 1900
        assert date.month is None
        assert date.day is None
        assert date.is_partial is True
        assert date.format_display() == "1900"

    def test_month_year(self):
        """Test parsing month and year."""
        # Jan 1900
        date = parse_rm_date("D.+19000100..+00000000..")
        assert date.year == 1900
        assert date.month == 1
        assert date.day is None
        assert date.is_partial is True
        assert date.format_display() == "Jan 1900"

    def test_day_month_no_year(self):
        """Test parsing day and month without year."""
        # 15 Mar
        date = parse_rm_date("D.+00000315..+00000000..")
        assert date.year is None
        assert date.month == 3
        assert date.day == 15
        assert date.format_display() == "15 Mar"


class TestDateModifiers:
    """Test date modifiers (before, after, between, etc.)."""

    def test_before_modifier(self):
        """Test 'Before' modifier."""
        # Bef 1 Jan 1900
        date = parse_rm_date("DB+19000101..+00000000..")
        assert date.modifier == DateModifier.BEFORE
        assert date.format_display() == "Bef 1 Jan 1900"

    def test_after_modifier(self):
        """Test 'After' modifier."""
        # Aft 1 Jan 1900
        date = parse_rm_date("DA+19000101..+00000000..")
        assert date.modifier == DateModifier.AFTER
        assert date.format_display() == "Aft 1 Jan 1900"

    def test_from_modifier(self):
        """Test 'From' modifier."""
        # From 1 Jan 1900
        date = parse_rm_date("DF+19000101..+00000000..")
        assert date.modifier == DateModifier.FROM
        assert date.format_display() == "From 1 Jan 1900"

    def test_to_modifier(self):
        """Test 'To' modifier."""
        # To 1 Jan 1900
        date = parse_rm_date("DT+19000101..+00000000..")
        assert date.modifier == DateModifier.TO
        assert date.format_display() == "To 1 Jan 1900"


class TestDateRanges:
    """Test date ranges."""

    def test_between_range(self):
        """Test 'Between...and' range."""
        # Bet 1 Jan 1900 and 5 Jan 1900
        date = parse_rm_date("DR+19000101..+19000105..")
        assert date.modifier == DateModifier.BETWEEN
        assert date.year == 1900
        assert date.month == 1
        assert date.day == 1
        assert date.year2 == 1900
        assert date.month2 == 1
        assert date.day2 == 5
        assert date.is_range is True
        assert date.format_display() == "Bet 1 Jan 1900 and 5 Jan 1900"

    def test_from_to_range(self):
        """Test 'From...to' range."""
        # From 1 Jan 1900 to 31 Dec 1900
        date = parse_rm_date("DS+19000101..+19001231..")
        assert date.modifier == DateModifier.FROM_TO
        assert date.format_display() == "From 1 Jan 1900 to 31 Dec 1900"

    def test_or_range(self):
        """Test 'or' range."""
        # 1 Jan 1900 or 5 Jan 1900
        date = parse_rm_date("DO+19000101..+19000105..")
        assert date.modifier == DateModifier.OR
        assert date.format_display() == "1 Jan 1900 or 5 Jan 1900"

    def test_range_modifier(self):
        """Test simple range with dash."""
        # 1 Jan 1900–5 Jan 1900
        date = parse_rm_date("D-+19000101..+19000105..")
        assert date.modifier == DateModifier.RANGE
        assert date.format_display() == "1 Jan 1900–5 Jan 1900"


class TestDateQualifiers:
    """Test date qualifiers (about, estimated, etc.)."""

    def test_about_qualifier(self):
        """Test 'About' qualifier."""
        # Abt 1 Jan 1900
        date = parse_rm_date("D.+19000101.A+00000000..")
        assert date.qualifier == DateQualifier.ABOUT
        assert date.format_display() == "Abt 1 Jan 1900"

    def test_estimated_qualifier(self):
        """Test 'Estimated' qualifier."""
        # Est 1 Jan 1900
        date = parse_rm_date("D.+19000101.E+00000000..")
        assert date.qualifier == DateQualifier.ESTIMATED
        assert date.format_display() == "Est 1 Jan 1900"

    def test_circa_qualifier(self):
        """Test 'Circa' qualifier."""
        # Ca 1 Jan 1900
        date = parse_rm_date("D.+19000101.C+00000000..")
        assert date.qualifier == DateQualifier.CIRCA
        assert date.format_display() == "Ca 1 Jan 1900"

    def test_calculated_qualifier(self):
        """Test 'Calculated' qualifier."""
        # Calc 1 Jan 1900
        date = parse_rm_date("D.+19000101.L+00000000..")
        assert date.qualifier == DateQualifier.CALCULATED
        assert date.format_display() == "Calc 1 Jan 1900"

    def test_probably_qualifier(self):
        """Test 'Probably' qualifier."""
        # Prob 1 Jan 1900
        date = parse_rm_date("D.+19000101.5+00000000..")
        assert date.qualifier == DateQualifier.PROBABLY
        assert date.format_display() == "Prob 1 Jan 1900"

    def test_possibly_qualifier(self):
        """Test 'Possibly' qualifier."""
        # Poss 1 Jan 1900
        date = parse_rm_date("D.+19000101.4+00000000..")
        assert date.qualifier == DateQualifier.POSSIBLY
        assert date.format_display() == "Poss 1 Jan 1900"


class TestBCDates:
    """Test BC (Before Christ) dates."""

    def test_bc_date(self):
        """Test BC date."""
        # 1 Jan 1900 BC
        date = parse_rm_date("D.-19000101..+00000000..")
        assert date.is_bc is True
        assert date.year == 1900
        assert date.format_display() == "1 Jan 1900 BC"

    def test_bc_range(self):
        """Test BC date range."""
        # Bet 1 Jan 100 BC and 1 Jan 50 BC
        date = parse_rm_date("DR-01000101..-00500101..")
        assert date.is_bc is True
        assert date.is_bc2 is True
        assert date.year == 100
        assert date.year2 == 50
        assert date.format_display() == "Bet 1 Jan 100 BC and 1 Jan 50 BC"


class TestDoubleDates:
    """Test double dates (for calendar transitions)."""

    def test_double_date(self):
        """Test double date."""
        # 1 Jan 1583/84
        date = parse_rm_date("D.+15830101/.+00000000..")
        assert date.is_double_date is True
        assert date.year == 1583
        assert date.format_display() == "1 Jan 1583/84"

    def test_double_date_year_only(self):
        """Test double date with year only."""
        # 1583/84
        date = parse_rm_date("D.+15830000/.+00000000..")
        assert date.is_double_date is True
        assert date.format_display() == "1583/84"


class TestTextDates:
    """Test free-text dates."""

    def test_text_date(self):
        """Test text date."""
        # "the first Wednesday after the big fire"
        date = parse_rm_date("Tthe first Wednesday after the big fire")
        assert date.date_type == DateType.TEXT
        assert date.text == "the first Wednesday after the big fire"
        assert date.format_display() == "the first Wednesday after the big fire"

    def test_empty_text_date(self):
        """Test empty text date."""
        date = parse_rm_date("T")
        assert date.date_type == DateType.TEXT
        assert date.text == ""


class TestQuakerDates:
    """Test Quaker dates."""

    def test_quaker_date(self):
        """Test Quaker date format."""
        # 12da 5mo 1588
        date = parse_rm_date("Q.+15880512..+00000000..")
        assert date.date_type == DateType.QUAKER
        assert date.year == 1588
        assert date.month == 5
        assert date.day == 12
        # Display should still work (may differ from Quaker format)
        assert "1588" in date.format_display()


class TestDateTimeConversion:
    """Test conversion to Python datetime."""

    def test_complete_date_to_datetime(self):
        """Test converting complete date to datetime."""
        date = parse_rm_date("D.+18960302..+00000000..")
        dt = date.to_datetime()
        assert dt is not None
        assert dt.year == 1896
        assert dt.month == 3
        assert dt.day == 2
        assert isinstance(dt, datetime)

    def test_partial_date_no_datetime(self):
        """Test that partial dates don't convert to datetime."""
        # Year only
        date1 = parse_rm_date("D.+19000000..+00000000..")
        assert date1.to_datetime() is None

        # Month/year only
        date2 = parse_rm_date("D.+19000100..+00000000..")
        assert date2.to_datetime() is None

    def test_bc_date_no_datetime(self):
        """Test that BC dates don't convert to datetime."""
        date = parse_rm_date("D.-19000101..+00000000..")
        assert date.to_datetime() is None

    def test_range_no_datetime(self):
        """Test that ranges don't convert to datetime."""
        date = parse_rm_date("DR+19000101..+19000105..")
        assert date.to_datetime() is None

    def test_null_date_no_datetime(self):
        """Test that null dates don't convert to datetime."""
        date = parse_rm_date("........................")
        assert date.to_datetime() is None

    def test_text_date_no_datetime(self):
        """Test that text dates don't convert to datetime."""
        date = parse_rm_date("Tsometime in 1900")
        assert date.to_datetime() is None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_short_date_string(self):
        """Test handling of date strings shorter than 24 characters."""
        # Should pad with periods
        date = parse_rm_date("D.+18960302")
        assert date.year == 1896
        assert date.month == 3
        assert date.day == 2

    def test_invalid_month(self):
        """Test handling of invalid month."""
        # Month 00 (not specified)
        date = parse_rm_date("D.+19000001..+00000000..")
        assert date.month is None
        assert date.day == 1

    def test_invalid_day(self):
        """Test handling of invalid day."""
        # Day 00 (not specified)
        date = parse_rm_date("D.+19000100..+00000000..")
        assert date.day is None
        assert date.month == 1

    def test_unknown_month_display(self):
        """Test display of unknown month."""
        # 1 ??? 1900 (day with no month)
        date = parse_rm_date("D.+19000001..+00000000..")
        # Should show year and day but handle missing month gracefully
        display = date.format_display()
        assert "1900" in display


class TestUnknownSortDate:
    """Test is_unknown_date helper function."""

    def test_unknown_sort_date_constant(self):
        """Test that unknown sort date is recognized."""
        assert is_unknown_date(UNKNOWN_SORT_DATE) is True

    def test_none_sort_date(self):
        """Test that None is recognized as unknown."""
        assert is_unknown_date(None) is True

    def test_valid_sort_date(self):
        """Test that valid sort dates are not unknown."""
        assert is_unknown_date(18960302000000) is False
        assert is_unknown_date(0) is False


class TestRealWorldExamples:
    """Test with real-world date examples from RootsMagic databases."""

    def test_birth_date_example(self):
        """Test typical birth date."""
        # 15 Jun 1850
        date = parse_rm_date("D.+18500615..+00000000..")
        assert date.format_display() == "15 Jun 1850"
        assert date.to_datetime() == datetime(1850, 6, 15)

    def test_death_date_example(self):
        """Test typical death date with qualifier."""
        # Abt 1920
        date = parse_rm_date("D.+19200000.A+00000000..")
        assert date.format_display() == "Abt 1920"
        assert date.qualifier == DateQualifier.ABOUT

    def test_marriage_date_range(self):
        """Test marriage date range."""
        # Bet 1870 and 1875
        date = parse_rm_date("DR+18700000..+18750000..")
        assert date.format_display() == "Bet 1870 and 1875"

    def test_census_date(self):
        """Test census date (usually complete)."""
        # 1 Jun 1900
        date = parse_rm_date("D.+19000601..+00000000..")
        assert date.format_display() == "1 Jun 1900"
        assert date.to_datetime() == datetime(1900, 6, 1)

    def test_estimated_birth_from_age(self):
        """Test estimated birth date (calculated from age)."""
        # Calc 1845
        date = parse_rm_date("D.+18450000.L+00000000..")
        assert date.format_display() == "Calc 1845"
        assert date.qualifier == DateQualifier.CALCULATED
