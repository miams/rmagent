"""
Populate census_field_metadata table with 1940 census field definitions.
Version 3: Includes official column numbers from Census Bureau forms.

Data sources:
- National Archives: https://www.archives.gov/research/census/1940
- IPUMS: https://usa.ipums.org/usa/voliii/items1940.shtml
- Census.gov: https://www.census.gov/programs-surveys/decennial-census/technical-documentation/questionnaires/1940
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import Json
from rmagent.config.config import load_app_config


def create_field(
    field_path,
    display_name,
    description,
    column_number=None,
    column_range=None,
    data_type=None,
    enum_values=None,
    narrative_template=None,
    priority=5,
    common=False,
    sample_only=False,
):
    """Helper to create field metadata tuple with column info."""
    sample_lines = [14, 29] if sample_only else None
    return (
        field_path,
        display_name,
        description,
        column_number,
        column_range,
        data_type,
        enum_values,
        narrative_template,
        priority,
        common,
        sample_only,
        sample_lines,
    )


# 1940 Census Field Metadata with Official Column Numbers
METADATA_1940 = [
    # Common fields (stored as typed columns)
    create_field(
        "name",
        "Full Name",
        "Full name of person as recorded in census",
        column_number=7,
        data_type="string",
        narrative_template="{value}",
        priority=1,
        common=True,
    ),
    create_field(
        "age",
        "Age",
        "Age at last birthday",
        column_number=11,
        data_type="integer",
        narrative_template="age {value}",
        priority=1,
        common=True,
    ),
    create_field(
        "sex",
        "Sex",
        "Sex of person",
        column_number=9,
        data_type="enum",
        enum_values=["M", "F", "Male", "Female"],
        priority=2,
        common=True,
    ),
    create_field(
        "race",
        "Race",
        "Color or race as recorded by enumerator",
        column_number=10,
        data_type="string",
        priority=3,
        common=True,
    ),
    create_field(
        "birthplace",
        "Birthplace",
        "Place of birth (state or country)",
        column_number=15,
        data_type="string",
        narrative_template="born in {value}",
        priority=2,
        common=True,
    ),
    create_field(
        "occupation",
        "Occupation",
        "Occupation, trade, or profession",
        column_number=28,
        data_type="string",
        narrative_template="working as {value}",
        priority=1,
        common=True,
    ),
    # Standard JSONB fields (all persons)
    create_field(
        "fields.relationship_to_head",
        "Relationship to Head",
        "Relationship of this person to the head of household",
        column_number=8,
        data_type="enum",
        enum_values=[
            "Head", "Wife", "Husband", "Son", "Daughter",
            "Father", "Mother", "Brother", "Sister",
            "Grandson", "Granddaughter",
            "Son-in-law", "Daughter-in-law",
            "Father-in-law", "Mother-in-law",
            "Brother-in-law", "Sister-in-law",
            "Nephew", "Niece", "Uncle", "Aunt", "Cousin",
            "Lodger", "Boarder", "Roomer", "Servant", "Hired hand",
            "Other relative", "Other non-relative",
        ],
        narrative_template="({value})",
        priority=1,
        common=True,
    ),
    create_field(
        "fields.marital_status",
        "Marital Status",
        "Marital condition",
        column_number=12,
        data_type="enum",
        enum_values=["Single", "Married", "Widowed", "Divorced", "Separated"],
        priority=3,
        common=True,
    ),
    create_field(
        "fields.education_level",
        "Education Level",
        "Highest grade of school or year of college completed",
        column_number=14,
        data_type="string",
        narrative_template="with {value} education",
        priority=3,
    ),
    create_field(
        "fields.attending_school",
        "Attending School",
        "Whether attended school or college any time since March 1, 1940",
        column_number=13,
        data_type="boolean",
        narrative_template="attending school",
        priority=4,
    ),
    create_field(
        "fields.citizenship",
        "Citizenship",
        "Citizenship status (for foreign born)",
        column_number=16,
        data_type="enum",
        enum_values=["Native", "Naturalized", "Alien", "First papers", "Has applied"],
        priority=4,
    ),
    create_field(
        "fields.residence_1935",
        "Residence in 1935",
        "Place of residence on April 1, 1935 (city, county, state combined)",
        column_range="17-19",
        data_type="string",
        narrative_template="living {value_phrase} since 1935",
        priority=3,
    ),
    create_field(
        "fields.residence_1935_farm",
        "On Farm in 1935",
        "Whether living on a farm on April 1, 1935",
        column_number=20,
        data_type="boolean",
        narrative_template="on a farm",
        priority=5,
    ),
    create_field(
        "fields.employment_status",
        "Employment Status",
        "Whether at work or seeking work during week of March 24-30, 1940",
        column_range="21-25",
        data_type="enum",
        enum_values=["At work", "With a job", "Seeking work", "Not in labor force"],
        priority=4,
    ),
    create_field(
        "fields.hours_worked",
        "Hours Worked",
        "Number of hours worked in week of March 24-30, 1940",
        column_number=26,
        data_type="integer",
        priority=6,
    ),
    create_field(
        "fields.unemployment_duration",
        "Unemployment Duration",
        "Duration of unemployment (if seeking work)",
        column_number=27,
        data_type="string",
        priority=7,
    ),
    create_field(
        "fields.industry",
        "Industry",
        "Industry in which person worked",
        column_number=29,
        data_type="string",
        narrative_template="in the {value} industry",
        priority=3,
        common=True,
    ),
    create_field(
        "fields.class_of_worker",
        "Class of Worker",
        "Class of worker",
        column_number=30,
        data_type="enum",
        enum_values=[
            "Wage or salary, private work",
            "Wage or salary, government work",
            "Employer",
            "Working on own account",
            "Unpaid family worker",
        ],
        priority=5,
    ),
    create_field(
        "fields.weeks_worked",
        "Weeks Worked in 1939",
        "Number of weeks worked in 1939 (full-time or part-time)",
        column_number=31,
        data_type="integer",
        narrative_template="worked {value} weeks in 1939",
        priority=4,
    ),
    create_field(
        "fields.income_wages",
        "Wage Income",
        "Amount of money wages or salary received in 1939",
        column_number=32,
        data_type="integer",
        narrative_template="earning ${value:,} annually",
        priority=2,
    ),
    create_field(
        "fields.income_other",
        "Other Income",
        "Other income over $50 (not wages/salary)",
        column_number=33,
        data_type="integer",
        priority=6,
    ),
    # Supplemental questions (columns 35-50) - SAMPLE ONLY (lines 14 & 29)
    create_field(
        "fields.birthplace_father",
        "Father's Birthplace",
        "Place of birth of father (state or country) - supplemental question",
        column_number=36,
        data_type="string",
        priority=5,
        common=True,
        sample_only=True,
    ),
    create_field(
        "fields.birthplace_mother",
        "Mother's Birthplace",
        "Place of birth of mother (state or country) - supplemental question",
        column_number=37,
        data_type="string",
        priority=5,
        common=True,
        sample_only=True,
    ),
    create_field(
        "fields.mother_tongue",
        "Mother Tongue",
        "Language spoken in home in earliest childhood - supplemental question",
        column_number=38,
        data_type="string",
        priority=6,
        sample_only=True,
    ),
    create_field(
        "fields.veteran_status",
        "Veteran Status",
        "Whether veteran of U.S. military or naval forces - supplemental question",
        column_number=39,
        data_type="boolean",
        narrative_template="a veteran",
        priority=4,
        sample_only=True,
    ),
    create_field(
        "fields.veteran_war",
        "War or Military Service",
        "War or military service if veteran - supplemental question",
        column_number=41,
        data_type="enum",
        enum_values=[
            "World War I",
            "Spanish-American War",
            "Philippine Insurrection",
            "Boxer Rebellion",
            "Mexican Expedition",
            "Other",
        ],
        narrative_template="served in {value}",
        priority=4,
        sample_only=True,
    ),
    create_field(
        "fields.social_security_number",
        "Social Security Number",
        "Whether person has a Federal Social Security number - supplemental question",
        column_number=42,
        data_type="boolean",
        priority=8,
        sample_only=True,
    ),
    create_field(
        "fields.deductions",
        "Social Security Deductions",
        "Amount deducted for Federal Old-Age Insurance or Railroad Retirement - supplemental question",
        column_range="43-44",
        data_type="integer",
        priority=7,
        sample_only=True,
    ),
    create_field(
        "fields.occupation_usual",
        "Usual Occupation",
        "Usual occupation (may differ from current) - supplemental question",
        column_number=45,
        data_type="string",
        priority=6,
        sample_only=True,
    ),
    create_field(
        "fields.industry_usual",
        "Usual Industry",
        "Usual industry (may differ from current) - supplemental question",
        column_number=46,
        data_type="string",
        priority=6,
        sample_only=True,
    ),
    create_field(
        "fields.class_of_worker_usual",
        "Usual Class of Worker",
        "Usual class of worker (may differ from current) - supplemental question",
        column_number=47,
        data_type="string",
        priority=7,
        sample_only=True,
    ),
    create_field(
        "fields.num_marriages",
        "Number of Marriages",
        "Whether married more than once - supplemental question",
        column_number=48,
        data_type="integer",
        priority=7,
        sample_only=True,
    ),
    create_field(
        "fields.age_first_marriage",
        "Age at First Marriage",
        "Age at first marriage (for ever-married persons) - supplemental question",
        column_number=49,
        data_type="integer",
        priority=7,
        sample_only=True,
    ),
    create_field(
        "fields.children_born",
        "Children Born",
        "Number of children ever born (for ever-married women only) - supplemental question",
        column_number=50,
        data_type="integer",
        priority=5,
        sample_only=True,
    ),
]


def populate_1940_metadata():
    """Populate census_field_metadata table with 1940 census fields."""
    config = load_app_config()
    census_db_url = os.getenv("CENSUS_DB_URL", config.census.db_url)

    if not census_db_url:
        print("❌ CENSUS_DB_URL not configured")
        return

    conn = psycopg2.connect(census_db_url)
    cur = conn.cursor()
    print(f"✅ Connected to census sidecar database")

    # Insert metadata records
    insert_query = """
    INSERT INTO census_field_metadata
        (census_year, field_path, display_name, description, column_number, column_range,
         data_type, enum_values, narrative_template, narrative_priority,
         common_across_years, sample_only, sample_lines)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (census_year, field_path) DO UPDATE SET
        display_name = EXCLUDED.display_name,
        description = EXCLUDED.description,
        column_number = EXCLUDED.column_number,
        column_range = EXCLUDED.column_range,
        data_type = EXCLUDED.data_type,
        enum_values = EXCLUDED.enum_values,
        narrative_template = EXCLUDED.narrative_template,
        narrative_priority = EXCLUDED.narrative_priority,
        common_across_years = EXCLUDED.common_across_years,
        sample_only = EXCLUDED.sample_only,
        sample_lines = EXCLUDED.sample_lines
    """

    inserted_count = 0
    for metadata_row in METADATA_1940:
        (
            field_path, display_name, description,
            column_number, column_range,
            data_type, enum_values,
            narrative_template, narrative_priority,
            common_across_years, sample_only, sample_lines,
        ) = metadata_row

        enum_values_json = Json(enum_values) if enum_values else None
        sample_lines_json = Json(sample_lines) if sample_lines else None

        cur.execute(
            insert_query,
            (
                1940, field_path, display_name, description,
                column_number, column_range,
                data_type, enum_values_json,
                narrative_template, narrative_priority,
                common_across_years, sample_only, sample_lines_json,
            ),
        )
        inserted_count += 1

    conn.commit()
    print(f"✅ Inserted/updated {inserted_count} field metadata records for 1940 census")

    # Show summary statistics
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE column_number IS NOT NULL) as with_column_num,
            COUNT(*) FILTER (WHERE column_range IS NOT NULL) as with_column_range,
            COUNT(*) FILTER (WHERE sample_only = TRUE) as sample_only
        FROM census_field_metadata
        WHERE census_year = 1940
    """)
    stats = cur.fetchone()
    print(f"\n📊 1940 Census Metadata Summary:")
    print(f"   Total fields: {stats[0]}")
    print(f"   With column numbers: {stats[1]}")
    print(f"   With column ranges: {stats[2]}")
    print(f"   Sample-only fields (lines 14 & 29): {stats[3]}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    populate_1940_metadata()
