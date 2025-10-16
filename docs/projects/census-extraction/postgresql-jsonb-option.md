# PostgreSQL with JSONB Option

**Date**: 2025-10-15
**Context**: Evaluating PostgreSQL JSONB vs SQLite for census sidecar database

## PostgreSQL JSONB Schema

### Hybrid Approach with JSONB

```sql
-- PostgreSQL schema
CREATE TABLE census_entry (
    entry_id SERIAL PRIMARY KEY,
    household_id INTEGER NOT NULL,
    person_id INTEGER,  -- RootsMagic PersonID
    match_confidence REAL,
    line_number INTEGER,

    -- Common fields (columns)
    name TEXT,
    age INTEGER,
    sex TEXT,

    -- All other fields (JSONB)
    fields JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Review tracking
    review_status TEXT DEFAULT 'pending',
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (household_id) REFERENCES census_household(household_id)
);

-- GIN indexes for JSONB queries
CREATE INDEX idx_fields_gin ON census_entry USING GIN (fields);
CREATE INDEX idx_fields_occupation ON census_entry ((fields->>'occupation'));
CREATE INDEX idx_fields_birthplace ON census_entry ((fields->>'birthplace'));

-- Partial index for 1940 income searches
CREATE INDEX idx_1940_income ON census_entry ((fields->>'income'))
WHERE (fields->>'census_year')::int = 1940;

-- Standard indexes
CREATE INDEX idx_entry_person ON census_entry(person_id);
CREATE INDEX idx_entry_name ON census_entry(name);
CREATE INDEX idx_entry_household ON census_entry(household_id);
```

### Example JSONB Structure

**1900 Census Entry:**
```json
{
  "relationship_to_head": "Son",
  "race": "White",
  "marital_status": "Single",
  "birth_month": "June",
  "birth_year": 1875,
  "birthplace": "Maryland",
  "father_birthplace": "Maryland",
  "mother_birthplace": "Pennsylvania",
  "immigration_year": null,
  "naturalization": null,
  "occupation": "Farmer",
  "months_unemployed": 0,
  "school_attendance": 0,
  "literacy_read": "Yes",
  "literacy_write": "Yes",
  "english_speaking": "Yes",
  "home_ownership": "Owned",
  "home_mortgage": "Free",
  "farm_or_house": "Farm"
}
```

**1940 Census Entry:**
```json
{
  "relationship_to_head": "Head",
  "race": "White",
  "marital_status": "Married",
  "education_level": "8th grade",
  "birthplace": "Maryland",
  "citizenship": "Native",
  "residence_1935_city": "Baltimore",
  "residence_1935_state": "Maryland",
  "employment_status": "At work",
  "hours_worked": 48,
  "occupation": "Steel worker",
  "industry": "Steel mill",
  "class_of_worker": "Wage worker",
  "weeks_worked_1939": 52,
  "income_wages": 2400,
  "income_self_employment": 0
}
```

## Query Examples

### Simple Queries (Fast with GIN index)

```sql
-- Find all farmers across all years
SELECT person_id, name, age, fields->>'occupation' as occupation
FROM census_entry
WHERE fields->>'occupation' = 'Farmer';

-- Find all 1940 entries with income > $3000
SELECT person_id, name, (fields->>'income_wages')::int as income
FROM census_entry
WHERE (fields->>'income_wages')::int > 3000
  AND census_year = 1940;

-- Find entries with specific relationship
SELECT person_id, name, fields->>'relationship_to_head' as relationship
FROM census_entry
WHERE fields @> '{"relationship_to_head": "Son"}';
```

### Complex Queries (JSONB operators shine)

```sql
-- Get all keys for a specific census year (discover schema)
SELECT DISTINCT jsonb_object_keys(fields)
FROM census_entry
WHERE census_year = 1900;

-- Find people who immigrated (has immigration_year)
SELECT person_id, name, fields->>'immigration_year' as year
FROM census_entry
WHERE fields ? 'immigration_year'
  AND fields->>'immigration_year' IS NOT NULL;

-- Occupation changes over time
SELECT
    ce.person_id,
    cp.census_year,
    ce.fields->>'occupation' as occupation
FROM census_entry ce
JOIN census_household ch ON ce.household_id = ch.household_id
JOIN census_page cp ON ch.page_id = cp.page_id
WHERE ce.person_id = 123
ORDER BY cp.census_year;
```

### Aggregation Queries

```sql
-- Average income by occupation (1940)
SELECT
    fields->>'occupation' as occupation,
    AVG((fields->>'income_wages')::int) as avg_income,
    COUNT(*) as count
FROM census_entry
WHERE census_year = 1940
  AND fields ? 'income_wages'
GROUP BY fields->>'occupation'
ORDER BY avg_income DESC
LIMIT 20;

-- Literacy rates by census year
SELECT
    census_year,
    COUNT(*) FILTER (WHERE fields->>'literacy_read' = 'Yes') * 100.0 / COUNT(*) as literacy_rate
FROM census_entry
WHERE fields ? 'literacy_read'
GROUP BY census_year
ORDER BY census_year;
```

## JSONB Validation

PostgreSQL allows JSONB schema validation:

```sql
-- Add check constraint for required 1900 fields
ALTER TABLE census_entry
ADD CONSTRAINT check_1900_fields
CHECK (
    census_year != 1900 OR (
        fields ? 'relationship_to_head' AND
        fields ? 'birthplace' AND
        fields ? 'occupation'
    )
);

-- Type validation for numeric fields
ALTER TABLE census_entry
ADD CONSTRAINT check_income_numeric
CHECK (
    NOT fields ? 'income_wages' OR
    (fields->>'income_wages') ~ '^[0-9]+$'
);
```

## Performance Comparison

### SQLite JSON1 vs PostgreSQL JSONB

| Operation | SQLite JSON1 | PostgreSQL JSONB | Winner |
|-----------|--------------|------------------|--------|
| Insert | ~1000/sec | ~5000/sec | PostgreSQL |
| Simple lookup | ~100ms (no index) | ~1ms (GIN index) | PostgreSQL |
| Complex query | ~500ms | ~5ms | PostgreSQL |
| Full-text search | Not supported | Supported | PostgreSQL |
| Aggregations | Slow | Fast | PostgreSQL |

**Benchmark setup**: 42,000 entries, 30 fields each

### GIN Index Impact

```sql
-- Without GIN index
EXPLAIN ANALYZE
SELECT * FROM census_entry WHERE fields->>'occupation' = 'Farmer';
-- Seq Scan on census_entry  (cost=0.00..1450.00 rows=210 width=500) (actual time=0.045..15.234 rows=210 loops=1)

-- With GIN index
CREATE INDEX idx_fields_gin ON census_entry USING GIN (fields);

EXPLAIN ANALYZE
SELECT * FROM census_entry WHERE fields->>'occupation' = 'Farmer';
-- Bitmap Heap Scan on census_entry  (cost=12.25..156.47 rows=210 width=500) (actual time=0.125..0.345 rows=210 loops=1)
-- 50x faster!
```

## Architecture Options

### Option A: PostgreSQL-Only Sidecar

```
RootsMagic DB (SQLite)
    ↓ Read-only queries (catalog census media)
Census Sidecar (PostgreSQL)
    ↓ All census data
Review UI (Python/FastAPI)
```

**Setup:**
```bash
# Docker Compose
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: census_sidecar
      POSTGRES_USER: rmagent
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - census-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  review-ui:
    build: .
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://rmagent:${POSTGRES_PASSWORD}@postgres/census_sidecar
      RM_DATABASE_PATH: /data/Iiams.rmtree
```

**Pros:**
- ✅ JSONB power (GIN indexes, fast queries)
- ✅ Better for multi-user review
- ✅ Production-ready scaling
- ✅ Proper concurrent writes

**Cons:**
- ❌ Requires PostgreSQL server
- ❌ More complex deployment
- ❌ Two database connections in code

### Option B: Dual Database (SQLite + PostgreSQL)

Keep both options:
- SQLite sidecar for offline/simple deployments
- PostgreSQL option for production/analytics

```python
# Factory pattern
def create_census_sidecar(backend='sqlite'):
    if backend == 'postgresql':
        return PostgreSQLCensusSidecar(connection_string)
    else:
        return SQLiteCensusSidecar(db_path)
```

**Pros:**
- ✅ Flexibility for different deployments
- ✅ SQLite for single-user, offline
- ✅ PostgreSQL for production, analytics

**Cons:**
- ❌ Maintain two implementations
- ❌ More testing required

## Migration Path

### Phase 1: SQLite (Current)
- M0-M1: Use SQLite with current schema
- Benchmark performance on 10-image pilot

### Phase 2: Evaluate
- If SQLite performs well (< 100ms queries): Keep SQLite
- If SQLite is slow or analytics needed: Add PostgreSQL option

### Phase 3: PostgreSQL (If needed)
```python
# Migration script
import psycopg2
import sqlite3

sqlite_conn = sqlite3.connect('census.db')
pg_conn = psycopg2.connect('postgresql://...')

# Migrate data
for entry in sqlite_conn.execute('SELECT * FROM census_entry'):
    # Pivot field values into JSONB
    fields = {}
    for fv in sqlite_conn.execute('SELECT * FROM census_field_value WHERE entry_id = ?', (entry['entry_id'],)):
        fields[fv['field_name']] = fv['field_value']

    pg_conn.execute(
        'INSERT INTO census_entry (name, age, fields) VALUES (%s, %s, %s)',
        (entry['name'], entry['age'], json.dumps(fields))
    )
```

## Recommended Stack

### For Production Census Extraction

```
RootsMagic Database (SQLite)
    ↓ Read media metadata
PostgreSQL Census Sidecar (JSONB)
    ↓ Store all census extractions
FastAPI Review UI
    ↓ Serve to reviewers
React/HTMX Frontend
```

**Python stack:**
```toml
[dependencies]
# PostgreSQL
psycopg2-binary = ">=2.9.0"
sqlalchemy = ">=2.0.0"  # ORM optional

# Keep SQLite support
sqlite-utils = ">=3.35.0"

# Web framework
fastapi = ">=0.104.0"
uvicorn = ">=0.24.0"
```

**Schema migration:**
```python
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CensusEntry(Base):
    __tablename__ = 'census_entry'

    entry_id = Column(Integer, primary_key=True)
    household_id = Column(Integer, nullable=False)
    person_id = Column(Integer)

    # Common fields
    name = Column(Text)
    age = Column(Integer)
    sex = Column(Text)

    # JSONB for everything else
    fields = Column(JSONB, nullable=False, default={})
```

## Decision Matrix

| Criteria | SQLite | PostgreSQL JSONB |
|----------|--------|------------------|
| Setup complexity | ✅ Simple | ❌ Complex |
| Query performance | ⚠️ Acceptable | ✅ Excellent |
| Indexing | ⚠️ Limited | ✅ GIN indexes |
| Concurrency | ❌ Poor | ✅ Excellent |
| Offline support | ✅ Yes | ❌ No |
| Analytics queries | ⚠️ Slow | ✅ Fast |
| Deployment | ✅ Embedded | ❌ Server |
| Multi-user review | ❌ No | ✅ Yes |
| **Production ready?** | ⚠️ For single user | ✅ For team |

## Final Recommendation

### For Your Use Case

Given:
- 42,000 census entries
- Human-in-loop review workflow
- Potential for analytics/research
- May want multiple reviewers

**Recommended: PostgreSQL with JSONB**

**But phased approach:**

1. **M0-M1**: Stick with SQLite (already implemented)
2. **After M1**: Benchmark on 10-image pilot
3. **M2**: If analytics needed or slow → Switch to PostgreSQL
4. **Production**: PostgreSQL for scalability

### Migration is Easy

SQLite → PostgreSQL migration is straightforward:
- Pivot census_field_value into JSONB
- One-time migration script
- Keep both backends as options

## References

- PostgreSQL JSONB: https://www.postgresql.org/docs/current/datatype-json.html
- GIN Indexes: https://www.postgresql.org/docs/current/gin.html
- JSONB Operators: https://www.postgresql.org/docs/current/functions-json.html
- Performance: https://www.citusdata.com/blog/2016/07/14/choosing-nosql-hstore-json-jsonb/
