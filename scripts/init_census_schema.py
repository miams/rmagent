"""
Initialize census sidecar database schema.

Ensures all tables exist, including newly added census_field_metadata table.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rmagent.census.sidecar import CensusSidecarDB
from rmagent.config.config import load_app_config


def initialize_schema():
    """Initialize census sidecar database schema."""
    config = load_app_config()
    census_db_url = os.getenv("CENSUS_DB_URL", config.census.db_url)

    if not census_db_url:
        print("❌ CENSUS_DB_URL not configured")
        print("   Set in config/.env: CENSUS_DB_URL=postgresql://user:pass@localhost:5432/census_sidecar")
        return

    print(f"Initializing census sidecar database schema...")
    print(f"Database: {census_db_url.split('@')[-1]}")  # Show host/db only

    try:
        sidecar = CensusSidecarDB(census_db_url)
        sidecar.connect()
        sidecar.initialize_schema()
        print("✅ Schema initialized successfully")

        # Verify new table exists
        with sidecar.conn.cursor() as cur:
            cur.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename LIKE 'census%'
                ORDER BY tablename
            """)
            tables = [row['tablename'] for row in cur.fetchall()]

        print(f"\n📊 Census tables ({len(tables)}):")
        for table in tables:
            print(f"   ✓ {table}")

        sidecar.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    initialize_schema()
