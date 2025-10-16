"""
Validate that sample-only census fields are used correctly.

Checks:
1. Sample-only fields should be NULL for non-sample lines
2. Sample lines should have some supplementary data (if collected)
3. Reports statistics on sample data availability
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from rmagent.config.config import load_app_config


def validate_sample_data(census_year=1940):
    """Validate sample-only field usage."""
    config = load_app_config()
    census_db_url = os.getenv("CENSUS_DB_URL", config.census.db_url)

    if not census_db_url:
        print("❌ CENSUS_DB_URL not configured")
        return

    conn = psycopg2.connect(census_db_url)
    cur = conn.cursor()

    print(f"\n{'='*80}")
    print(f"CENSUS SAMPLE DATA VALIDATION - {census_year}")
    print(f"{'='*80}\n")

    # 1. Get sample-only fields for this year
    cur.execute("""
        SELECT field_path, display_name, sample_lines
        FROM census_field_metadata
        WHERE census_year = %s AND sample_only = TRUE
    """, (census_year,))

    sample_fields = cur.fetchall()
    if not sample_fields:
        print(f"No sample-only fields defined for {census_year}")
        return

    sample_lines = sample_fields[0][2] if sample_fields else []
    print(f"📋 Sample Lines: {sample_lines}")
    print(f"📋 Sample-Only Fields: {len(sample_fields)}")
    for field_path, display_name, _ in sample_fields:
        print(f"   • {field_path}: {display_name}")
    print()

    # 2. Count total entries
    cur.execute("""
        SELECT COUNT(*)
        FROM census_entry e
        JOIN census_household h ON e.household_id = h.household_id
        JOIN census_page p ON h.page_id = p.page_id
        WHERE p.census_year = %s
    """, (census_year,))
    total_entries = cur.fetchone()[0]

    # 3. Count entries on sample lines
    if sample_lines:
        cur.execute("""
            SELECT COUNT(*)
            FROM census_entry e
            JOIN census_household h ON e.household_id = h.household_id
            JOIN census_page p ON h.page_id = p.page_id
            WHERE p.census_year = %s
              AND e.line_number = ANY(%s)
        """, (census_year, sample_lines))
        sample_line_entries = cur.fetchone()[0]
    else:
        sample_line_entries = 0

    print(f"📊 Entry Statistics:")
    print(f"   Total entries: {total_entries}")
    print(f"   Sample line entries: {sample_line_entries}")
    if total_entries > 0:
        sample_pct = (sample_line_entries / total_entries) * 100
        print(f"   Sample percentage: {sample_pct:.1f}%")
    print()

    # 4. Check for violations: sample-only fields on non-sample lines
    print(f"🔍 Checking for Data Quality Issues...\n")

    issues_found = 0
    for field_path, display_name, _ in sample_fields:
        # Extract JSONB field name (e.g., "fields.veteran_status" -> "veteran_status")
        field_name = field_path.split('.')[-1] if '.' in field_path else field_path

        if sample_lines:
            cur.execute(f"""
                SELECT
                    e.entry_id,
                    e.line_number,
                    e.name,
                    e.fields->>%s as field_value
                FROM census_entry e
                JOIN census_household h ON e.household_id = h.household_id
                JOIN census_page p ON h.page_id = p.page_id
                WHERE p.census_year = %s
                  AND e.line_number IS NOT NULL
                  AND e.line_number NOT IN ({','.join(map(str, sample_lines))})
                  AND (e.fields->>%s) IS NOT NULL
                LIMIT 10
            """, (field_name, census_year, field_name))

            violations = cur.fetchall()
            if violations:
                issues_found += len(violations)
                print(f"❌ {display_name} ({field_path})")
                print(f"   Found on {len(violations)} non-sample lines (should be NULL):")
                for entry_id, line_num, name, value in violations[:5]:
                    print(f"   • Entry #{entry_id}, Line {line_num}: {name} = {value}")
                if len(violations) > 5:
                    print(f"   ... and {len(violations) - 5} more")
                print()

    if issues_found == 0:
        print("✅ No data quality issues found!")
        print("   All sample-only fields are NULL for non-sample lines.\n")
    else:
        print(f"⚠️  Found {issues_found} data quality issues")
        print(f"   Sample-only fields should be NULL for lines NOT in {sample_lines}\n")

    # 5. Check sample line coverage: do sample lines have supplementary data?
    if sample_lines:
        print(f"📈 Sample Line Data Availability:\n")

        for field_path, display_name, _ in sample_fields[:5]:  # Check first 5 fields
            field_name = field_path.split('.')[-1] if '.' in field_path else field_path

            cur.execute(f"""
                SELECT COUNT(*)
                FROM census_entry e
                JOIN census_household h ON e.household_id = h.household_id
                JOIN census_page p ON h.page_id = p.page_id
                WHERE p.census_year = %s
                  AND e.line_number = ANY(%s)
                  AND (e.fields->>%s) IS NOT NULL
            """, (census_year, sample_lines, field_name))

            with_data = cur.fetchone()[0]
            coverage_pct = (with_data / sample_line_entries * 100) if sample_line_entries > 0 else 0

            print(f"   {display_name:35} {with_data:4}/{sample_line_entries} ({coverage_pct:.1f}%)")

    print(f"\n{'='*80}\n")

    cur.close()
    conn.close()


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 1940
    validate_sample_data(year)
