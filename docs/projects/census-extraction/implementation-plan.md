# RM11 census extraction roadmap

## Purpose and scope
- Document the end-to-end plan for extracting genealogical facts from 1,400 census JPG images linked inside RootsMagic.
- Keep automation local-first (OCR, layout, matching) with optional LLM assistance for handwriting interpretation and validation.
- Deliver a separate SQLite sidecar that stores structured census data, provenance, and reviewer decisions without touching the proprietary RootsMagic database.

## Guiding principles
- Preserve provenance: capture source image path, row, column, and OCR confidence for every extracted field.
- Human-in-the-loop verification: surface OCR output next to highlighted image snippets so reviewers can approve or correct rapidly.
- Reproducible workflows: script each stage (preprocess, OCR, parsing, review, export) with explicit inputs/outputs for auditability.
- Offline friendly: prefer open-source OCR/layout models; use LLM APIs only where they add measurable accuracy.

## Assumptions and constraints
- 1,400 locally stored JPG images covering U.S. Federal census years 1790–1950 (1890 excluded) with year-specific column schemas.
- RootsMagic media links provide `PersonID`, census year, and filenames; no additional transcriptions or household metadata are assumed.
- No custom handwriting ground-truth datasets will be produced unless absolutely necessary; rely on pretrained models and rule-based corrections.
- Single-reviewer human-in-the-loop workflow; no multi-user conflict resolution or automated deduplication required.
- Local execution on MacBook M3 Pro with permission to install native libraries; avoid third-party paid services beyond optional LLM API calls for difficult images.

## Target deliverables
- Census sidecar SQLite schema with shared `PersonID` indexes plus household, address, and cross-page tracking.
- Batch processor that ingests census images, runs preprocessing, segmentation, OCR, and produces structured candidate rows.
- Lightweight review UI serving local files that shows image segments, extracted text, confidence, and edit tools.
- Integration hooks so RMAgent queries can join RootsMagic persons with census sidecar entries for research agents and timeline enrichment.

## Architecture overview
- **Ingestion layer:** Load image metadata from RootsMagic media links, normalize file paths, assign persistent `media_id`.
- **Image preprocessing:** Deskew, denoise, enhance contrast via OpenCV; persist cleaned derivatives alongside originals.
- **Layout segmentation:** Use layoutparser or doctr to detect table grids, row boundaries, and column labels; store cell coordinates plus census-year column metadata.
- **OCR and handwriting recognition:** Apply Tesseract (printed columns) or handwriting models (kraken/calamari pretrained weights); optionally fall back to GPT-4o Vision for low-confidence cells.
- **Field parsing and person matching:** Normalize names, ages, relationships, addresses per census schema; fuzzy-match to RootsMagic `PersonID`, flag uncertainty for review.
- **Review workflow:** Serve a local web UI (FastAPI + HTMX/Alpine) that highlights image regions, shows extracted text, enables corrections, and records reviewer ID and timestamp.
- **Sidecar persistence:** Populate normalized tables plus raw OCR dumps, confidence scores, and review decisions; create indexes for `PersonID`, household, census year.
- **Analytics and export:** Provide scripts to summarize coverage, export CSV extracts, and integrate with LangChain tools for downstream agents.
- See the [architecture diagram](RM11_CensusExtraction_Architecture.md) for a visual summary of component interactions.

## Milestones
- **M0: Foundation (target weeks 0-2)**
  - [ ] Complete hardware/software readiness checklist (Python env, OpenCV, Tesseract, kraken models).
  - [ ] Catalog census media linked in RootsMagic and confirm file paths, counts, and metadata.
  - [ ] Draft sidecar SQLite schema and ER diagram (page, household, entry, provenance tables).
  - [ ] Create census-year configuration stubs documenting expected columns and header strings.
- **M1: Working prototype (target weeks 3-6)**
  - [ ] Implement preprocessing + layout pipeline that outputs cell bounding boxes and sample crops.
  - [ ] Run OCR (printed + handwriting models) on a 10-image pilot set; log confidence metrics.
  - [ ] Build basic parser that maps OCR output to census fields and links to candidate `PersonID`.
  - [ ] Stand up minimal reviewer UI showing image snippet + extracted text with approve/edit workflow.
  - [ ] Populate sidecar with pilot data and validate against known family records.
  - [ ] Iterate on matcher heuristics using reviewer feedback from pilot dataset.
- **M2: MVP release (target weeks 7-12)**
  - [ ] Expand batch processing to full 1,400-image set with progress reporting and resumable jobs.
  - [ ] Integrate AI-assisted validation (LLM summarization, discrepancy detection) with cached results.
  - [ ] Enhance reviewer UI with keyboard shortcuts, confidence coloring, cross-page household handling.
  - [ ] Add export and reporting scripts (coverage, unresolved items, discrepancy logs).
  - [ ] Document end-to-end runbook, reviewer guide, and integration notes for RMAgent tooling.
  - [ ] Backfill historical runs into sidecar and reconcile outstanding review backlog.

## Workstreams
- **WS1: Data modeling**
  - [ ] Finalize SQLite schema with tables (`census_page`, `census_household`, `census_entry`, `census_field_provenance`, `census_review_log`).
  - [ ] Define indexes for `PersonID`, census year, location, household span, reviewer status, and unresolved flags.
  - [ ] Ship migrations using sqlite-utils (preferred) or alembic and add schema integrity tests.
  - [ ] Document per-year column dictionaries (1790–1950) and map them to normalized fields (e.g., `income_1940`, `relation_1910`).
- **WS2: Image pipeline**
  - [ ] Implement preprocessing module (OpenCV deskew, denoise, adaptive histogram equalization/CLAHE, border trimming).
  - [ ] Benchmark layout detection (doctr TableTransformer, layoutparser Detectron2) on sample pages; select defaults per era.
  - [ ] Persist cell geometry, row IDs, and cropped PNG snippets to `output/census_cache/` for reviewer consumption.
  - [ ] Record preprocessing metadata (timestamp, parameters) in sidecar for traceability.
- **WS3: OCR and handwriting models**
  - [ ] Configure Tesseract with custom language data tuned for census abbreviations and numeric columns.
  - [ ] Evaluate pretrained kraken/calamari models; tune segmentation/post-processing instead of full fine-tuning.
  - [ ] Implement adaptive model routing: printed schedules → Tesseract, dense handwriting → kraken, degraded cells → GPT-4o Vision fallback (cached).
  - [ ] Capture OCR confidence per cell and log raw text before normalization.
- **WS4: Parsing and entity matching**
  - [ ] Normalize extracted text into structured columns (name, relation, age, occupation, birthplace, dwelling/family numbers, address).
  - [ ] Create census-year-specific parser modules to interpret column order, abbreviations, and derived metrics (e.g., age vs. birth year).
  - [ ] Implement hierarchical matching pipeline (exact match → Soundex → RapidFuzz with household context) linking to RootsMagic `PersonID`.
  - [ ] Compute discrepancy metrics (age deltas, conflicting relationships) and queue them for reviewer attention.
- **WS5: Review UI**
  - [ ] Develop FastAPI backend serving local static assets, authentication (local user file), and REST endpoints for fetching/updating entries.
  - [ ] Build frontend with HTMX/Alpine.js to display image snippets (canvas overlays), OCR text, confidence scores, and inline edits.
  - [ ] Implement reviewer shortcuts (approve, edit, skip), cross-page navigation, and tooltips for census column definitions.
  - [ ] Log reviewer actions (before/after values, timestamps) to `census_review_log`.
- **WS6: AI assistance and LangChain integration**
  - [ ] Create LangChain tools (`query_census_entries`, `summarize_household`, `flag_census_discrepancies`) wrapping sidecar queries.
  - [ ] Design prompts that summarize households, cite census rows, and recommend follow-up research steps.
  - [ ] Log all AI interactions (prompt, response, confidence) per observability guidelines and persist references in sidecar.
  - [ ] Cache vision-LLM responses keyed by `media_id` + cell hash to control cost.
- **WS7: Testing and QA**
  - [ ] Establish unit/integration tests for each pipeline component (preprocessing, layout, OCR adapters, parsing, matching).
  - [ ] Create acceptance checklist for reviewer UI usability and performance (load time, keyboard flow, error handling).
  - [ ] Implement regression tests to guard against schema changes and data loss; include golden datasets for sample pages.
  - [ ] Schedule periodic QA audits comparing sidecar entries to RootsMagic data (age, relationships) to detect drift.

## Tooling stack
- **Python runtime & package management**
  - `Python 3.11+` — core language runtime aligned with repo tooling.
  - `uv` (https://github.com/astral-sh/uv) — fast package manager and runner already adopted in the project.
- **Image preprocessing & numeric stack**
  - `OpenCV` (https://github.com/opencv/opencv) — deskew, denoise, perspective correction (powerful but heavier dependency).
  - `Pillow` (https://github.com/python-pillow/Pillow) — lightweight image manipulations; simpler but limited compared to OpenCV.
  - `numpy` (https://github.com/numpy/numpy) — array operations; backbone for OpenCV interoperability.
  - `scikit-image` (https://github.com/scikit-image/scikit-image) — optional; provides alternative filters if OpenCV routines underperform.
- **Data wrangling & storage**
  - `pandas` (https://github.com/pandas-dev/pandas) — tabular transformations, CSV exports.
  - `sqlite-utils` (https://github.com/simonw/sqlite-utils) — schema migrations, inserts, inspection for the sidecar DB; favors CLI scripting.
  - `sqlmodel` or `SQLAlchemy` (optional) — if an ORM-style layer is preferred for sidecar operations; adds complexity but improves type safety.
- **String similarity & genealogy heuristics**
  - `rapidfuzz` (https://github.com/maxbachmann/RapidFuzz) — fast fuzzy matching for name reconciliation.
  - `usaddress` (https://github.com/datamade/usaddress) and `censusnameparser` (future consideration) — optional helpers for parsing addresses and historic name patterns.
- **OCR / Handwriting recognition**
  - `Tesseract` + `pytesseract` (https://github.com/tesseract-ocr/tesseract) — open-source OCR; excels on printed text, struggles with cursive but easy to install.
  - `kraken` (https://github.com/mittagessen/kraken) — neural handwriting recognition with segmentation; strong on cursive but requires Python virtualenv isolation.
  - `calamari-ocr` (https://github.com/Calamari-OCR/calamari) — alternative HTR; GPU acceleration available but setup heavier.
  - Vision LLM fallback (GPT-4o or Claude 3.5 Vision via LangChain) — accurate on tough handwriting; introduces API cost and latency, so use sparingly and cache results.
- **Layout analysis**
  - `docTR` (https://github.com/mindee/doctr) — deep-learning document structure detection; good accuracy, requires PyTorch.
  - `layoutparser` + Detectron2 (https://github.com/Layout-Parser/layout-parser) — flexible layout detection with pretrained models; heavier install but customizable.
  - `unstructured` (https://github.com/Unstructured-IO/unstructured) — quick start for table partitioning; easier CLI but less control over census-specific quirks.
- **Web application framework & frontend**
  - `FastAPI` (https://github.com/tiangolo/fastapi) — async Python web framework used across project; ideal for reviewer API.
  - `HTMX` (https://github.com/bigskysoftware/htmx) + `Alpine.js` (https://github.com/alpinejs/alpine) — lightweight progressive enhancement for interactive forms; minimal build tooling.
  - `React` via Vite (https://github.com/vitejs/vite) — optional if richer component state is required; more setup overhead, especially for single-reviewer workflow.
- **CLI orchestration & scheduling**
  - `invoke` (https://github.com/pyinvoke/invoke) or `typer` (https://github.com/tiangolo/typer) — command runners for pipeline tasks; Typer integrates nicely with Click-style CLI.
  - `Prefect` (https://github.com/PrefectHQ/prefect) — optional workflow orchestration if retries, scheduling, or monitoring are needed.
- **Logging, tracing, and QA**
  - Built-in `logging` module writing to `logs/` paths; ensure structured JSON for OCR events.
  - `rich` (https://github.com/Textualize/rich) — console progress and tables.
  - `LangSmith` (https://github.com/langchain-ai/langsmith-sdk) — optional SaaS tracing for LangChain calls; skip if staying offline.
- **Testing & validation**
  - `pytest` (https://github.com/pytest-dev/pytest) — existing project standard for unit/integration tests.
  - `hypothesis` (https://github.com/HypothesisWorks/hypothesis) — optional property-based testing for parsers/matching rules.
  - `playwright` (https://github.com/microsoft/playwright-python) — optional automated review-UI testing; heavier but useful for regression coverage.

## Review and QA workflow
- Batch runs produce pending review queues grouped by census year and confidence tier.
- Reviewers confirm or correct entries; every action stores reviewer ID, timestamp, and diff of changes.
- Discrepancies flagged by AI or parsing rules feed into a “needs attention” queue.
- Periodic QA scripts compare sidecar entries against RootsMagic data (birth year, relationships) to highlight unresolved issues.

## Risks and mitigations
- **Handwriting accuracy ceiling:** Without fine-tuning, certain surnames or abbreviations may be misread. Mitigate with enhanced preprocessing, census-aware dictionaries, and reviewer checkpoints for all low-confidence fields.
- **Layout variability:** Column layouts change dramatically year-to-year. Maintain per-year configuration files and automated header detection to select the correct template.
- **Reviewer fatigue:** Large review volume can introduce errors. Prioritize queues by confidence, offer keyboard shortcuts, and batch approve high-confidence entries.
- **LLM cost exposure:** Vision-model fallbacks can inflate costs. Cache outputs, gate usage behind confidence thresholds, and allow manual overrides.
- **Cross-page households:** Family groups spanning adjacent images may lose context. Store forward/back pointers and preload both pages in the review UI for confirmation.

## Resolved considerations
- Handwriting fine-tuning data is unlikely; focus on pretrained models plus rule-based clean-up and reviewer verification.
- Scope limited to U.S. Federal census years 1790–1950 (excluding 1890); treat each column layout as a separate template module.
- Workflow assumes a single reviewer; no collaborative features or conflict resolution states are planned.
- Household deduplication remains manual; system stores cross-page links but does not auto-merge.

## References
- [Ground Truth Data Standards](ground-truth-standards.md) - Standards for creating and using ground truth datasets for LLM prompt validation
- [Row Detection Analysis - October 18, 2025](row-detection-analysis-2025-10-18.md) - **CRITICAL**: Current state analysis revealing fundamental flaws in morphological detection approach
- OpenCV documentation on deskewing and adaptive thresholding.
- kraken OCR toolkit: https://github.com/mittagessen/kraken
- doctr (document text recognition): https://github.com/mindee/doctr
- LangChain documentation for custom tools and structured output parsers.
