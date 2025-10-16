"""
Add processing_status, ocr_completed_at, and error_message to census_page table.

Migration to track pipeline processing status per page.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
from rmagent.config.config import load_app_config


def migrate():
    """Add processing status columns to census_page."""
    config = load_app_config(require_llm_credentials=False)
    census_db_url = os.getenv("CENSUS_DB_URL", config.census.db_url)

    if not census_db_url:
        print("❌ CENSUS_DB_URL not configured")
        return

    print("Migrating census_page table...")
    print("Adding: processing_status, ocr_completed_at, error_message\n")

    conn = psycopg2.connect(census_db_url)
    cur = conn.cursor()

    try:
        # Add processing_status
        print("1. Adding processing_status column...")
        cur.execute("""
            ALTER TABLE census_page
            ADD COLUMN IF NOT EXISTS processing_status TEXT DEFAULT 'pending'
                CHECK (processing_status IN ('pending', 'processing', 'complete', 'failed'))
        """)
        print("   ✅ processing_status column added")

        # Add ocr_completed_at
        print("2. Adding ocr_completed_at column...")
        cur.execute("""
            ALTER TABLE census_page
            ADD COLUMN IF NOT EXISTS ocr_completed_at TIMESTAMP
        """)
        print("   ✅ ocr_completed_at column added")

        # Add error_message
        print("3. Adding error_message column...")
        cur.execute("""
            ALTER TABLE census_page
            ADD COLUMN IF NOT EXISTS error_message TEXT
        """)
        print("   ✅ error_message column added")

        # Create index on processing_status
        print("4. Creating index on processing_status...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_page_status
            ON census_page(processing_status)
        """)
        print("   ✅ Index created")

        conn.commit()
        print("\n✅ Migration complete!")

        # Verify columns exist
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'census_page'
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
