"""
Census year configuration templates.

Defines column layouts, expected headers, and parsing rules for each
U.S. Federal census year from 1790-1950 (excluding 1890).
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CensusColumn(BaseModel):
    """Represents a single column in a census year."""

    name: str  # Internal field name
    display_name: str  # User-friendly name
    expected_headers: list[str]  # Possible header text variations
    column_index: Optional[int] = None  # Expected position (0-based)
    data_type: str = "text"  # "text", "integer", "date"
    required: bool = False
    ocr_hints: Optional[dict] = None  # OCR-specific guidance


class CensusYearConfig(BaseModel):
    """Configuration for a specific census year."""

    year: int
    description: str
    columns: list[CensusColumn]
    special_notes: Optional[str] = None


# Census year configurations (1790-1950, excluding 1890)
CENSUS_YEARS = {
    1850: CensusYearConfig(
        year=1850,
        description="First census to record all household members by name",
        columns=[
            CensusColumn(
                name="dwelling_number",
                display_name="Dwelling Number",
                expected_headers=["Dwelling houses numbered in the order of visitation"],
                column_index=0,
                data_type="integer",
            ),
            CensusColumn(
                name="family_number",
                display_name="Family Number",
                expected_headers=["Families numbered in the order of visitation"],
                column_index=1,
                data_type="integer",
            ),
            CensusColumn(
                name="name",
                display_name="Name",
                expected_headers=["The Name of every Person", "Name"],
                column_index=2,
                required=True,
            ),
            CensusColumn(
                name="age",
                display_name="Age",
                expected_headers=["Age"],
                column_index=3,
                data_type="integer",
                required=True,
            ),
            CensusColumn(
                name="sex",
                display_name="Sex",
                expected_headers=["Sex"],
                column_index=4,
            ),
            CensusColumn(
                name="race",
                display_name="Color",
                expected_headers=["Color", "Race"],
                column_index=5,
            ),
            CensusColumn(
                name="occupation",
                display_name="Profession, Occupation, or Trade",
                expected_headers=["Profession, Occupation, or Trade"],
                column_index=6,
            ),
            CensusColumn(
                name="birthplace",
                display_name="Place of Birth",
                expected_headers=["Place of Birth"],
                column_index=7,
            ),
            CensusColumn(
                name="married_within_year",
                display_name="Married within the year",
                expected_headers=["Married within the year"],
                column_index=8,
            ),
            CensusColumn(
                name="school_attendance",
                display_name="Attended School",
                expected_headers=["Attended School within the year"],
                column_index=9,
            ),
            CensusColumn(
                name="literacy",
                display_name="Cannot Read & Write",
                expected_headers=["Persons over 20 yrs who cannot read & write"],
                column_index=10,
            ),
        ],
        special_notes="First census to name all household members. No relationship to head recorded.",
    ),
    1900: CensusYearConfig(
        year=1900,
        description="Added relationship to head, birth month/year, and citizenship",
        columns=[
            CensusColumn(
                name="sheet_number",
                display_name="Sheet No.",
                expected_headers=["Sheet No."],
                column_index=0,
                data_type="integer",
            ),
            CensusColumn(
                name="line_number",
                display_name="Line No.",
                expected_headers=["Line No."],
                column_index=1,
                data_type="integer",
            ),
            CensusColumn(
                name="dwelling_number",
                display_name="Dwelling Number",
                expected_headers=["Number of dwelling house"],
                column_index=2,
                data_type="integer",
            ),
            CensusColumn(
                name="family_number",
                display_name="Family Number",
                expected_headers=["Number of family"],
                column_index=3,
                data_type="integer",
            ),
            CensusColumn(
                name="name",
                display_name="Name",
                expected_headers=["Name of each person"],
                column_index=4,
                required=True,
            ),
            CensusColumn(
                name="relationship_to_head",
                display_name="Relationship",
                expected_headers=["Relationship of each person to the head of the family"],
                column_index=5,
                required=True,
            ),
            CensusColumn(
                name="race",
                display_name="Color or Race",
                expected_headers=["Color or race"],
                column_index=6,
            ),
            CensusColumn(
                name="sex",
                display_name="Sex",
                expected_headers=["Sex"],
                column_index=7,
            ),
            CensusColumn(
                name="birth_month",
                display_name="Birth Month",
                expected_headers=["Month of birth"],
                column_index=8,
            ),
            CensusColumn(
                name="birth_year",
                display_name="Birth Year",
                expected_headers=["Year of birth"],
                column_index=9,
                data_type="integer",
            ),
            CensusColumn(
                name="age",
                display_name="Age",
                expected_headers=["Age at last birthday"],
                column_index=10,
                data_type="integer",
                required=True,
            ),
            CensusColumn(
                name="marital_status",
                display_name="Marital Status",
                expected_headers=["Whether single, married, widowed, or divorced"],
                column_index=11,
            ),
            CensusColumn(
                name="years_married",
                display_name="Years Married",
                expected_headers=["Number of years married"],
                column_index=12,
                data_type="integer",
            ),
            CensusColumn(
                name="mother_children_born",
                display_name="Mother of how many children",
                expected_headers=["Mother of how many children"],
                column_index=13,
                data_type="integer",
            ),
            CensusColumn(
                name="mother_children_living",
                display_name="Number of children living",
                expected_headers=["Number of these children living"],
                column_index=14,
                data_type="integer",
            ),
            CensusColumn(
                name="birthplace",
                display_name="Place of Birth",
                expected_headers=["Place of birth of this person"],
                column_index=15,
            ),
            CensusColumn(
                name="father_birthplace",
                display_name="Father's Birthplace",
                expected_headers=["Place of birth of Father of this person"],
                column_index=16,
            ),
            CensusColumn(
                name="mother_birthplace",
                display_name="Mother's Birthplace",
                expected_headers=["Place of birth of Mother of this person"],
                column_index=17,
            ),
            CensusColumn(
                name="immigration_year",
                display_name="Year of Immigration",
                expected_headers=["Year of immigration to the United States"],
                column_index=18,
                data_type="integer",
            ),
            CensusColumn(
                name="years_in_us",
                display_name="Years in US",
                expected_headers=["Number of years in the United States"],
                column_index=19,
                data_type="integer",
            ),
            CensusColumn(
                name="naturalization",
                display_name="Naturalization",
                expected_headers=["Naturalization"],
                column_index=20,
            ),
            CensusColumn(
                name="occupation",
                display_name="Occupation",
                expected_headers=["Occupation, trade, or profession"],
                column_index=21,
            ),
            CensusColumn(
                name="months_unemployed",
                display_name="Months Unemployed",
                expected_headers=["Months not employed"],
                column_index=22,
                data_type="integer",
            ),
            CensusColumn(
                name="school_attendance",
                display_name="School Attendance",
                expected_headers=["Attended school (in months)"],
                column_index=23,
                data_type="integer",
            ),
            CensusColumn(
                name="literacy_read",
                display_name="Can Read",
                expected_headers=["Can read"],
                column_index=24,
            ),
            CensusColumn(
                name="literacy_write",
                display_name="Can Write",
                expected_headers=["Can write"],
                column_index=25,
            ),
            CensusColumn(
                name="english_speaking",
                display_name="Speaks English",
                expected_headers=["Can speak English"],
                column_index=26,
            ),
            CensusColumn(
                name="home_ownership",
                display_name="Owned or Rented",
                expected_headers=["Owned or rented", "Home"],
                column_index=27,
            ),
            CensusColumn(
                name="home_mortgage",
                display_name="Owned Free or Mortgaged",
                expected_headers=["Owned free or mortgaged"],
                column_index=28,
            ),
            CensusColumn(
                name="farm_or_house",
                display_name="Farm or House",
                expected_headers=["Farm or house"],
                column_index=29,
            ),
        ],
        special_notes="Major expansion with nativity, citizenship, and detailed household statistics.",
    ),
    1940: CensusYearConfig(
        year=1940,
        description="Most recent publicly available census (72-year rule)",
        columns=[
            CensusColumn(
                name="street_address",
                display_name="Street Address",
                expected_headers=["Street, avenue, road, etc."],
                column_index=0,
            ),
            CensusColumn(
                name="house_number",
                display_name="House Number",
                expected_headers=["House number"],
                column_index=1,
            ),
            CensusColumn(
                name="dwelling_number",
                display_name="Dwelling Number",
                expected_headers=["Number of household"],
                column_index=2,
                data_type="integer",
            ),
            CensusColumn(
                name="home_ownership",
                display_name="Home Owned or Rented",
                expected_headers=["Home owned or rented"],
                column_index=3,
            ),
            CensusColumn(
                name="home_value",
                display_name="Value of Home",
                expected_headers=["Value of home, if owned"],
                column_index=4,
                data_type="integer",
            ),
            CensusColumn(
                name="farm_residence",
                display_name="Farm Residence",
                expected_headers=["Does this household live on a farm?"],
                column_index=5,
            ),
            CensusColumn(
                name="name",
                display_name="Name",
                expected_headers=["Name of each person"],
                column_index=6,
                required=True,
            ),
            CensusColumn(
                name="relationship_to_head",
                display_name="Relationship",
                expected_headers=["Relationship"],
                column_index=7,
                required=True,
            ),
            CensusColumn(
                name="sex",
                display_name="Sex",
                expected_headers=["Sex"],
                column_index=8,
            ),
            CensusColumn(
                name="race",
                display_name="Color or Race",
                expected_headers=["Color or race"],
                column_index=9,
            ),
            CensusColumn(
                name="age",
                display_name="Age",
                expected_headers=["Age at last birthday"],
                column_index=10,
                data_type="integer",
                required=True,
            ),
            CensusColumn(
                name="marital_status",
                display_name="Marital Status",
                expected_headers=["Marital status"],
                column_index=11,
            ),
            CensusColumn(
                name="school_attendance",
                display_name="Attended School",
                expected_headers=["Attended school or college?"],
                column_index=12,
            ),
            CensusColumn(
                name="education_level",
                display_name="Highest Grade",
                expected_headers=["Highest grade of school completed"],
                column_index=13,
            ),
            CensusColumn(
                name="birthplace",
                display_name="Place of Birth",
                expected_headers=["Place of birth"],
                column_index=14,
            ),
            CensusColumn(
                name="citizenship",
                display_name="Citizenship",
                expected_headers=["Citizenship of the foreign born"],
                column_index=15,
            ),
            CensusColumn(
                name="residence_1935_city",
                display_name="City of Residence in 1935",
                expected_headers=["City, town, or village"],
                column_index=16,
            ),
            CensusColumn(
                name="residence_1935_county",
                display_name="County of Residence in 1935",
                expected_headers=["County"],
                column_index=17,
            ),
            CensusColumn(
                name="residence_1935_state",
                display_name="State of Residence in 1935",
                expected_headers=["State (or foreign country)"],
                column_index=18,
            ),
            CensusColumn(
                name="farm_residence_1935",
                display_name="Farm Residence in 1935",
                expected_headers=["On a farm?"],
                column_index=19,
            ),
            CensusColumn(
                name="employment_status",
                display_name="Employment Status",
                expected_headers=["At work or with a job?"],
                column_index=20,
            ),
            CensusColumn(
                name="seeking_work",
                display_name="Seeking Work",
                expected_headers=["Seeking work?"],
                column_index=21,
            ),
            CensusColumn(
                name="emergency_work",
                display_name="Emergency Work",
                expected_headers=["If not, were you on public emergency work?"],
                column_index=22,
            ),
            CensusColumn(
                name="hours_worked",
                display_name="Hours Worked",
                expected_headers=["Hours worked in week"],
                column_index=23,
                data_type="integer",
            ),
            CensusColumn(
                name="duration_unemployment",
                display_name="Duration of Unemployment",
                expected_headers=["Duration of unemployment"],
                column_index=24,
            ),
            CensusColumn(
                name="occupation",
                display_name="Occupation",
                expected_headers=["Occupation"],
                column_index=25,
            ),
            CensusColumn(
                name="industry",
                display_name="Industry",
                expected_headers=["Industry"],
                column_index=26,
            ),
            CensusColumn(
                name="class_of_worker",
                display_name="Class of Worker",
                expected_headers=["Class of worker"],
                column_index=27,
            ),
            CensusColumn(
                name="weeks_worked",
                display_name="Weeks Worked in 1939",
                expected_headers=["Weeks worked in 1939"],
                column_index=28,
                data_type="integer",
            ),
            CensusColumn(
                name="income_wages",
                display_name="Wage/Salary Income",
                expected_headers=["Income - Wages or salary"],
                column_index=29,
                data_type="integer",
            ),
            CensusColumn(
                name="income_self_employment",
                display_name="Self-Employment Income",
                expected_headers=["Income - Other sources"],
                column_index=30,
                data_type="integer",
            ),
        ],
        special_notes="Includes detailed employment, income, and migration questions. Last fully public census.",
    ),
}


# Helper function to get census year config
def get_census_year_config(year: int) -> Optional[CensusYearConfig]:
    """Get configuration for a specific census year."""
    return CENSUS_YEARS.get(year)


# List of all configured census years
CONFIGURED_YEARS = sorted(CENSUS_YEARS.keys())
