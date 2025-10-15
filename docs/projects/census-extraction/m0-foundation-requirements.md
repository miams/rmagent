# M0: Foundation Requirements

**Target**: Weeks 0-2
**Status**: In Progress
**Branch**: feature/census-extraction

## Objectives

- [ ] Complete hardware/software readiness checklist
- [x] Catalog census media linked in RootsMagic
- [x] Draft sidecar SQLite schema and ER diagram
- [x] Create census-year configuration stubs

## Hardware Requirements

### Confirmed Available
- **Machine**: MacBook M3 Pro
- **OS**: macOS (Darwin 24.6.0)
- **Python**: 3.11+ (confirmed: Python 3.13 via uv)
- **Storage**: Local filesystem for 1,400 census JPG images

### Performance Assumptions
- M3 Pro Neural Engine available for on-device ML inference (if needed)
- 16GB+ RAM for batch processing and model loading
- SSD storage for fast image I/O during preprocessing

## Software Dependencies

### Core Python Stack (Already Installed)
- ✅ Python 3.11+ (using 3.13)
- ✅ `uv` package manager
- ✅ `pydantic` for data models
- ✅ `sqlite3` (Python standard library)

### Required New Dependencies

#### Essential (M0)
```toml
# Image processing
opencv-python = ">=4.8.0"  # Preprocessing (deskew, denoise, CLAHE)
Pillow = ">=10.0.0"        # Lightweight image ops
numpy = ">=1.24.0"         # Array operations

# Database
sqlite-utils = ">=3.35.0"  # Schema migrations and inspection

# String matching
rapidfuzz = ">=3.0.0"      # Fuzzy name matching
```

#### OCR/Layout (M1 - Working Prototype)
```toml
# OCR engines
pytesseract = ">=0.3.10"   # Tesseract OCR wrapper
tesseract = "system"       # Install via: brew install tesseract

# Layout detection
doctr = {extras = ["torch"], version = ">=0.7.0"}  # Document layout
# OR layoutparser = ">=0.3.4"  # Alternative

# Handwriting recognition
kraken = ">=4.3.0"         # HTR models (requires isolated env)
```

#### Review UI (M1)
```toml
# Web framework
fastapi = ">=0.104.0"      # Already installed
uvicorn = ">=0.24.0"       # ASGI server
htmx = "system"            # Client-side (CDN)
alpinejs = "system"        # Client-side (CDN)
```

#### Optional AI/LLM (M2)
- Vision LLM fallback already supported via existing LangChain integration
- GPT-4o or Claude 3.5 Vision for difficult handwriting cells
- Cache responses to control costs

### System Tools

#### Homebrew Installations
```bash
brew install tesseract       # OCR engine
brew install tesseract-lang  # Additional language data (if needed)
```

#### ICU Extension (Already Available)
- ✅ `./sqlite-extension/icu.dylib` for RMNOCASE collation
- Required for querying RootsMagic database

## Census Media Catalog

### Database Query Strategy

Census images are identified by:

1. **Direct event links**: Media linked to Census events (FactType GEDCOM tag = 'CENS')
2. **Caption/description keywords**: Media with "census" in Caption or Description fields
3. **Filename patterns**: Media files with census year patterns (e.g., "1900_census.jpg")

### Year Extraction

Census year determined using hierarchical strategy:
1. Linked census event date (EventTable.Date)
2. Caption/Description text parsing (regex for 4-digit years)
3. Filename pattern matching
4. Manual review for unmatched media

### Valid Census Years
- U.S. Federal Census: 1790, 1800, ..., 1950 (every 10 years)
- **Excluding 1890** (destroyed by fire)
- Total: 17 census years

## Sidecar Database Schema

### Tables Created
- ✅ `census_page` - Image metadata and layout
- ✅ `census_household` - Household groups with cross-page tracking
- ✅ `census_entry` - Individual person entries
- ✅ `census_field_provenance` - OCR metadata per field
- ✅ `census_review_log` - Audit trail for reviewer actions

### Indexes
- ✅ Performance indexes on common queries (person_id, census_year, review_status)

See [sidecar-schema-diagram.md](sidecar-schema-diagram.md) for full ER diagram.

## Census Year Configurations

### Implemented
- ✅ **1850** - First census with all household members named (11 columns)
- ✅ **1900** - Added relationship to head, nativity, citizenship (30 columns)
- ✅ **1940** - Most recent public census with employment/income (31 columns)

### Remaining Years
- **High Priority** (common in datasets):
  - 1880, 1910, 1920, 1930
- **Medium Priority**:
  - 1860, 1870, 1890 (N/A - destroyed), 1950
- **Low Priority** (simple formats):
  - 1790-1840 (household head only, limited columns)

Configuration structure in `rmagent/census/config/census_years.py`:
- Column definitions (name, display name, headers, data types)
- Expected header text variations for OCR matching
- Year-specific parsing rules

## Project Structure

### Created Directories
```
rmagent/census/
├── __init__.py
├── catalog.py                    # Media cataloging from RootsMagic
├── sidecar.py                    # Sidecar database management
├── config/
│   ├── __init__.py
│   └── census_years.py          # Year-specific column configs
├── models/
│   ├── __init__.py
│   └── schema.py                # Pydantic models and SQL schema
├── pipelines/
│   ├── __init__.py
│   ├── preprocessing/           # Image preprocessing
│   ├── ocr/                     # OCR engines
│   ├── parsing/                 # Field parsing
│   └── matching/                # Person matching
└── review/                      # Review UI components

data/census/
├── README.md
├── sidecar/                     # Census sidecar database
├── images/
│   └── processed/               # Preprocessed images
└── cache/                       # Cell crops and OCR cache
```

## Testing Strategy

### Unit Tests (M0)
- [ ] Test sidecar database creation and schema
- [ ] Test census year config parsing
- [ ] Test media catalog queries
- [ ] Test year extraction logic
- [ ] Test valid census year validation

### Integration Tests (M1)
- [ ] Test full catalog workflow on pilot dataset (10 images)
- [ ] Test RootsMagic database connection with ICU
- [ ] Test image path resolution (handle ?/ prefix)

### Data Quality Tests (M1)
- [ ] Verify all census media have valid years
- [ ] Check for duplicate media_id entries
- [ ] Validate person_id links to RootsMagic

## Risks and Mitigations

### Risk: Media Files Not Accessible
**Mitigation**: Catalog script handles missing files gracefully, logs warnings

### Risk: Census Year Ambiguity
**Mitigation**: Multi-strategy year extraction with manual review queue

### Risk: ICU Extension Load Failure
**Mitigation**: Warning issued, but doesn't block cataloging (RMNOCASE may not work)

### Risk: Large Dependency Footprint
**Mitigation**: Stage installations across milestones (M0 minimal, M1 adds OCR, M2 adds AI)

## Next Steps (M1: Working Prototype)

1. **Preprocessing Pipeline**
   - Implement OpenCV deskew, denoise, CLAHE
   - Generate preprocessed derivatives
   - Store in `data/census/images/processed/`

2. **Layout Detection**
   - Evaluate doctr vs layoutparser on sample pages
   - Extract cell bounding boxes
   - Persist layout metadata to sidecar

3. **OCR Pilot**
   - Run Tesseract + kraken on 10-image pilot
   - Log confidence metrics
   - Identify difficult handwriting cases

4. **Person Matching**
   - Implement fuzzy name matching with RapidFuzz
   - Use household context for disambiguation
   - Calculate match confidence scores

5. **Review UI MVP**
   - FastAPI backend serving image snippets
   - HTMX frontend with approve/edit workflow
   - Persist reviewer decisions to sidecar

## Success Criteria

M0 is complete when:
- ✅ All census media cataloged in sidecar database
- ✅ Census years determined for >90% of images
- ✅ Sidecar schema created and documented
- ✅ Census year configurations created for key years (1850, 1900, 1940)
- [ ] Dependency installation tested and documented
- [ ] Unit tests passing for catalog and schema modules
- [ ] CLI command for running catalog available

## Current Status

**Completed**:
- ✅ Directory structure created
- ✅ Sidecar database schema designed with ER diagram
- ✅ Census year configurations for 1850, 1900, 1940
- ✅ Media catalog script implemented
- ✅ Database utilities created

**In Progress**:
- 🔄 Dependency installation and testing
- 🔄 CLI command structure

**Pending**:
- ⏳ Unit tests
- ⏳ Full catalog run on real database
- ⏳ Validation of image file accessibility
