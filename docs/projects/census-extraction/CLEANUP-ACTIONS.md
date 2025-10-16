# Census Extraction Cleanup Actions

**Date:** 2025-10-15
**Status:** Ready for execution
**Time Required:** 5-10 minutes

---

## Immediate Cleanup (Execute Now)

### 1. Remove Redundant Script Versions

**Current State:**
- `populate_1940_census_metadata.py` - Original (obsolete, no sample_only support)
- `populate_1940_census_metadata_v2.py` - Active version (has sample_only) ✓
- `populate_1940_census_metadata_v3.py` - Experimental (not used)

**Action:**
```bash
# Keep v2 (confirmed working), delete v1 and v3
cd /Users/miams/Code/RM11
rm scripts/populate_1940_census_metadata.py      # Delete original
rm scripts/populate_1940_census_metadata_v3.py   # Delete experimental
mv scripts/populate_1940_census_metadata_v2.py scripts/populate_1940_census_metadata.py  # Rename to canonical
```

**Verification:**
```bash
ls -1 scripts/populate_1940_census_metadata*.py
# Should show only: scripts/populate_1940_census_metadata.py
```

### 2. Archive One-Time Migration Scripts

**Action:**
```bash
mkdir -p scripts/migrations
mv scripts/migrate_metadata_add_sample_fields.py scripts/migrations/
```

**Rationale:**
- This migration was a one-time schema change
- Should be archived, not deleted (useful historical record)
- Keeps scripts/ cleaner

---

## Optional Cleanup (Can Defer)

### 3. Create Master Documentation Index

**Action:**
```bash
cd docs/projects/census-extraction
cat > README.md << 'EOF'
# Census Extraction Documentation

## 🎯 Start Here
- **[Implementation Plan](implementation-plan.md)** - Roadmap (M0-M3)
- **[Pre-OCR Cleanup Review](pre-ocr-cleanup-review.md)** - Current status, ready for OCR

## 📐 Architecture
- [Architecture v2](census-architecture-v2.md) - Current hybrid schema design
- [Sidecar Schema Diagram](sidecar-schema-diagram.md) - ER diagram, relationships
- [Final Architecture Decision](final-architecture-decision.md) - Performance benchmarks

## 🧪 Testing
- [Integration Test Results](integration-test-results.md) - Jesse Dorsey Iams household
- [Next Steps: Integration](next-steps-integration.md) - Integration testing roadmap

## 📋 Metadata System
- [Field Metadata Implementation](census-field-metadata-implementation.md) - Metadata table
- [1940 Census Sampling](1940-census-sampling-methodology.md) - Lines 14 & 29
- [Sample Fields Summary](SUMMARY-sample-fields-added.md) - Quick reference

## 📊 Data & Validation
- [Census Catalog Query Solution](census-catalog-query-solution.md) - Pre-1850 discovery
- [Census Fields Verification](census-fields-verification.md) - Field validation

## 🏛️ Historical Context
- [M0 Foundation Requirements](m0-foundation-requirements.md) - Foundation specs
- [M1 Implementation Summary](M1-implementation-summary.md) - OCR pipeline components

## 📖 Session Notes
- [Session 2025-10-15 Summary](session-2025-10-15-summary.md) - Complete session log

## 🔄 Decision Documents
- [Schema Alternatives Analysis](schema-alternatives-analysis.md) - EAV vs JSONB vs hybrid
- [PostgreSQL JSONB Option](postgresql-jsonb-option.md) - JSONB exploration

---

**Last Updated:** 2025-10-15
**Current Phase:** M0 Complete, Ready for M1 (OCR)
EOF
```

---

## Script Inventory (Post-Cleanup)

### Keep (Active Use)
```
scripts/
├── populate_1940_census_metadata.py         # Metadata population (renamed from v2)
├── test_1940_census_integration.py          # Integration test
├── test_census_catalog.py                   # Catalog functionality test
├── test_census_metadata_queries.py          # Metadata query tests
├── validate_census_sample_data.py           # Sample data validation
└── init_census_schema.py                    # Schema initialization
```

### Archive (Historical Reference)
```
scripts/migrations/
└── migrate_metadata_add_sample_fields.py    # One-time schema migration
```

### Delete (Redundant)
```
scripts/
├── populate_1940_census_metadata.py         # Original version (obsolete)
└── populate_1940_census_metadata_v3.py      # Experimental version (unused)
```

---

## Verification Steps

After cleanup, verify everything still works:

```bash
# 1. Schema initialization
.venv/bin/python3 scripts/init_census_schema.py
# Should show: ✅ Schema initialized successfully

# 2. Metadata population
.venv/bin/python3 scripts/populate_1940_census_metadata.py
# Should show: ✅ Inserted/updated 34 field metadata records

# 3. Metadata queries
.venv/bin/python3 scripts/test_census_metadata_queries.py
# Should show: ✅ ALL TESTS PASSED

# 4. Sample validation
.venv/bin/python3 scripts/validate_census_sample_data.py
# Should show: ✅ No data quality issues found

# 5. Integration test (optional, takes longer)
.venv/bin/python3 scripts/test_1940_census_integration.py
# Should show: ✅ Integration test SUCCESSFUL
```

---

## Cleanup Checklist

- [ ] Delete `populate_1940_census_metadata.py` (original)
- [ ] Delete `populate_1940_census_metadata_v3.py` (experimental)
- [ ] Rename `populate_1940_census_metadata_v2.py` to canonical name
- [ ] Create `scripts/migrations/` directory
- [ ] Move `migrate_metadata_add_sample_fields.py` to migrations/
- [ ] Verify all scripts still run correctly
- [ ] Optional: Create `docs/projects/census-extraction/README.md`
- [ ] Git commit cleanup changes

---

## Git Commit Message

```
chore(census): clean up redundant scripts and organize migrations

- Remove obsolete populate_1940_census_metadata.py (v1)
- Remove experimental populate_1940_census_metadata_v3.py
- Rename v2 to canonical populate_1940_census_metadata.py
- Archive one-time migration to scripts/migrations/
- Add census-extraction documentation index (optional)

No functional changes, pure cleanup.
```

---

**Status:** Ready to execute
**Risk Level:** Low (no functional changes, only file organization)
**Time Required:** 5-10 minutes
