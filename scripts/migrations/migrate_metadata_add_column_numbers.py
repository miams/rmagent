"""
Add column_number and column_range to census_field_metadata table.

Migration to track official column numbers from census enumeration forms.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from rmagent.config.config import load_app_config


def migrate():
    """Add column_number and column_range columns."""
    config = load_app_config()
    census_db_url = os.getenv("CENSUS_DB_URL", config.census.db_url)

    if not census_db_url:
        print("❌ CENSUS_DB_URL not configured")
        return

    print("Migrating census_field_metadata table...")
    print("Adding: column_number (INTEGER), column_range (TEXT)\n")

    conn = psycopg2.connect(census_db_url)
    cur = conn.cursor()

    try:
        # Add column_number
        print("1. Adding column_number column...")
        cur.execute("""
            ALTER TABLE census_field_metadata
            ADD COLUMN IF NOT EXISTS column_number INTEGER
        """)
        print("   ✅ column_number column added")

        # Add column_range
        print("2. Adding column_range column...")
        cur.execute("""
            ALTER TABLE census_field_metadata
            ADD COLUMN IF NOT EXISTS column_range TEXT
        """)
        print("   ✅ column_range column added")

        conn.commit()
        print("\n✅ Migration complete!")

        # Verify columns exist
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'census_field_metadata'
            ORDER BY ordinal_position
        """)
        print("\n📋 Table schema:")
        for row in cur.fetchall():
            col_name, data_type = row
            print(f"   {col_name:25} {data_type:15}")

    except psycopg2.Error as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    migrate()
