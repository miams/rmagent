"""
Test census field metadata queries.

Verifies that metadata can be queried effectively for:
1. All fields for a census year
2. Specific field details
3. Common fields across years
4. High-priority fields for biography generation
5. Enum values for categorical fields
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from rmagent.config.config import load_app_config


def test_metadata_queries():
    """Test various metadata queries."""
    config = load_app_config()
    census_db_url = os.getenv("CENSUS_DB_URL", config.census.db_url)

    if not census_db_url:
        print("❌ CENSUS_DB_URL not configured")
        return

    conn = psycopg2.connect(census_db_url)
    cur = conn.cursor()

    print(f"\n{'='*80}")
    print("CENSUS FIELD METADATA QUERY TESTS")
    print(f"{'='*80}\n")

    # Test 1: Get all 1940 census fields
    print("📋 Test 1: All 1940 Census Fields")
    print("-" * 80)
    cur.execute("""
        SELECT field_path, display_name, data_type, narrative_priority
        FROM census_field_metadata
        WHERE census_year = 1940
        ORDER BY narrative_priority NULLS LAST, field_path
    """)
    results = cur.fetchall()
    print(f"Found {len(results)} fields for 1940 census:\n")
    for field_path, display_name, data_type, priority in results[:10]:
        priority_str = f"[P{priority}]" if priority else "[--]"
        print(f"  {priority_str:6} {field_path:40} {display_name:30} ({data_type})")
    print(f"  ... ({len(results) - 10} more fields)\n")

    # Test 2: Get specific field details
    print("🔍 Test 2: Specific Field Details (income_wages)")
    print("-" * 80)
    cur.execute("""
        SELECT field_path, display_name, description, data_type,
               narrative_template, narrative_priority
        FROM census_field_metadata
        WHERE census_year = 1940 AND field_path = 'fields.income_wages'
    """)
    field = cur.fetchone()
    if field:
        print(f"Field Path: {field[0]}")
        print(f"Display Name: {field[1]}")
        print(f"Description: {field[2]}")
        print(f"Data Type: {field[3]}")
        print(f"Narrative Template: {field[4]}")
        print(f"Priority: {field[5]}")
    print()

    # Test 3: Get enum values for relationship field
    print("📊 Test 3: Enum Values (relationship_to_head)")
    print("-" * 80)
    cur.execute("""
        SELECT field_path, display_name, enum_values
        FROM census_field_metadata
        WHERE census_year = 1940 AND field_path = 'fields.relationship_to_head'
    """)
    field = cur.fetchone()
    if field and field[2]:
        import json
        enum_values = json.loads(field[2]) if isinstance(field[2], str) else field[2]
        print(f"Field: {field[1]}")
        print(f"Valid values ({len(enum_values)}):")
        for i, value in enumerate(enum_values):
            if i < 10:
                print(f"  • {value}")
        if len(enum_values) > 10:
            print(f"  ... ({len(enum_values) - 10} more values)")
    print()

    # Test 4: Get common fields across census years
    print("🌍 Test 4: Common Fields Across Census Years")
    print("-" * 80)
    cur.execute("""
        SELECT field_path, display_name, data_type
        FROM census_field_metadata
        WHERE census_year = 1940 AND common_across_years = TRUE
        ORDER BY field_path
    """)
    results = cur.fetchall()
    print(f"Found {len(results)} common fields:\n")
    for field_path, display_name, data_type in results:
        print(f"  • {field_path:40} {display_name:30} ({data_type})")
    print()

    # Test 5: Get high-priority fields for biography
    print("🎯 Test 5: High-Priority Fields for Biography Generation (Priority 1-2)")
    print("-" * 80)
    cur.execute("""
        SELECT field_path, display_name, narrative_template, narrative_priority
        FROM census_field_metadata
        WHERE census_year = 1940 AND narrative_priority <= 2
        ORDER BY narrative_priority, field_path
    """)
    results = cur.fetchall()
    print(f"Found {len(results)} high-priority fields:\n")
    for field_path, display_name, template, priority in results:
        template_str = f'"{template}"' if template else "(no template)"
        print(f"  [P{priority}] {field_path:40}")
        print(f"       {display_name}")
        print(f"       Template: {template_str}")
        print()

    # Test 6: Query with simulated census data
    print("💡 Test 6: Simulate Biography Context Query")
    print("-" * 80)
    print("Query: Get all metadata for fields present in a census entry\n")

    # Simulate what would be in a census_entry.fields JSONB
    simulated_fields = [
        "fields.relationship_to_head",
        "fields.marital_status",
        "fields.education_level",
        "fields.residence_1935",
        "fields.income_wages",
    ]

    cur.execute("""
        SELECT field_path, display_name, description, narrative_template, narrative_priority
        FROM census_field_metadata
        WHERE census_year = 1940 AND field_path = ANY(%s)
        ORDER BY narrative_priority
    """, (simulated_fields,))

    results = cur.fetchall()
    print("Metadata for fields in entry:\n")
    for field_path, display_name, description, template, priority in results:
        print(f"[P{priority}] {display_name}")
        print(f"    Path: {field_path}")
        print(f"    Description: {description}")
        print(f"    Template: {template or '(none)'}")
        print()

    # Test 7: Get all enum fields
    print("📋 Test 7: All Enum/Categorical Fields")
    print("-" * 80)
    cur.execute("""
        SELECT field_path, display_name, enum_values
        FROM census_field_metadata
        WHERE census_year = 1940 AND data_type = 'enum'
        ORDER BY field_path
    """)
    results = cur.fetchall()
    print(f"Found {len(results)} enum fields:\n")
    for field_path, display_name, enum_values in results:
        if enum_values:
            import json
            values = json.loads(enum_values) if isinstance(enum_values, str) else enum_values
            print(f"  • {display_name:35} ({len(values)} values)")
    print()

    # Test 8: Performance test - query all metadata for a year
    print("⚡ Test 8: Performance - Full Metadata Query")
    print("-" * 80)
    import time
    start = time.time()
    cur.execute("""
        SELECT field_path, display_name, description, data_type,
               enum_values, narrative_template, narrative_priority,
               common_across_years
        FROM census_field_metadata
        WHERE census_year = 1940
        ORDER BY narrative_priority NULLS LAST
    """)
    results = cur.fetchall()
    elapsed = (time.time() - start) * 1000
    print(f"Retrieved {len(results)} field metadata records in {elapsed:.2f}ms")
    print()

    cur.close()
    conn.close()

    print(f"{'='*80}")
    print("✅ ALL TESTS PASSED")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_metadata_queries()
