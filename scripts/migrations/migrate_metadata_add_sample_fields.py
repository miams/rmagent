"""
Add sample_only and sample_lines columns to census_field_metadata table.

Migration to support tracking which fields are only collected for sample lines
(e.g., 1940 census supplemental questions on lines 14 and 29).
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from rmagent.config.config import load_app_config


def migrate():
    """Add sample_only and sample_lines columns."""
    config = load_app_config()
    census_db_url = os.getenv("CENSUS_DB_URL", config.census.db_url)

    if not census_db_url:
        print("❌ CENSUS_DB_URL not configured")
        return

    print("Migrating census_field_metadata table...")
    print("Adding: sample_only (BOOLEAN), sample_lines (JSONB)\n")

    conn = psycopg2.connect(census_db_url)
    cur = conn.cursor()

    try:
        # Add sample_only column
        print("1. Adding sample_only column...")
        cur.execute("""
            ALTER TABLE census_field_metadata
            ADD COLUMN IF NOT EXISTS sample_only BOOLEAN DEFAULT FALSE
        """)
        print("   ✅ sample_only column added")

        # Add sample_lines column
        print("2. Adding sample_lines column...")
        cur.execute("""
            ALTER TABLE census_field_metadata
            ADD COLUMN IF NOT EXISTS sample_lines JSONB
        """)
        print("   ✅ sample_lines column added")

        # Create index for sample_only
        print("3. Creating index on sample_only...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_metadata_sample
            ON census_field_metadata(sample_only)
            WHERE sample_only = TRUE
        """)
        print("   ✅ Index created")

        conn.commit()
        print("\n✅ Migration complete!")

        # Verify columns exist
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'census_field_metadata'
            ORDER BY ordinal_position
        """)
        print("\n📋 Table schema:")
        for row in cur.fetchall():
            col_name, data_type, nullable = row
            nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
            print(f"   {col_name:25} {data_type:15} {nullable_str}")

    except psycopg2.Error as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    migrate()
