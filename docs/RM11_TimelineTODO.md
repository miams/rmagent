# RM11 timeline enhancement roadmap

## Purpose
- Capture requirements and design direction for the next-generation TimelineJS pipeline.
- Align data, AI, and presentation workstreams before implementation begins.

## Reference materials
- Baseline exports: `samples/timeline_1475.json`, `samples/timeline_1475.html`
- Aspirational example: `samples/John Dorsey Iams TimelineJS3 - od1.csv`
- Schema sources: `data/Iiams.rmtree`, `data_reference/RM11_Timeline_Construction.md`

## Observed gaps in current generator
- Generic headlines (`Event Census`) instead of human-friendly titles.
- Minimal narrative text; lacks historical framing or synthesized insights.
- No inline media beyond a single hero asset; ignores linked photographs/documents.
- Styling is barebones (default KnightLab skin, no typography or color system aligned to RM11 brand).
- Timeline excludes contextual world events and family milestones (spouses, children) that enrich storytelling.

## Design pillars for improved experience
- **Narrative depth**: Expand each timeline card with concise prose, key takeaways, and citation hover states.
- **Rich media**: Prioritize RootsMagic-linked media, fall back to AI-curated public-domain assets with attribution.
- **Contextual layers**: Blend personal events with AI-selected historical milestones relevant to time/place.
- **Audience-friendly language**: Replace internal labels with readable, genealogist-approved phrasing.
- **Accessible presentation**: Ensure color contrast, keyboard navigation, captions, and alt text.
- **Reproducibility**: Capture every AI decision (prompt, model, source links) for audit trails.

## Proposed architecture
- **Data extraction layer**
  - Extend `TimelineGenerator` (or create `TimelineBuilder`) to assemble enriched fact objects.
  - Pull structured data: events, media links, citations, relationships, residences, occupations.
  - Normalize geospatial data for region matching (county/state/country codes).
- **AI enrichment layer**
  - Persona-aware prompt templates (timeline narrative, historical context, caption rewriting).
  - Tooling to fetch candidate historical events/images using time/place queries (requires future API research).
  - Deterministic caching of AI outputs (SQLite/JSONL) keyed by person/event hash.
- **Presentation layer**
  - JSON schema upgrade: custom metadata fields (`topic_tags`, `summary`, `related_people`).
  - HTML renderer: bespoke CSS theme, optional embeds (map, photo gallery, callouts).
  - Export adapters: TimelineJS3 JSON, HTML viewer, CSV for KnightLab Google Sheets template.
- **Governance**
  - Logging of AI calls (prompt text, model ID, response metadata) per repository observability standards.
  - Validation scripts to ensure required fields and citation coverage.

## Workstreams & TODOs
- [ ] Requirements grooming with stakeholders (confirm personas, output formats).
- [ ] Data audit of RootsMagic events/media coverage (quantify gaps, private flag handling).
- [ ] Design prompt templates for narrative synthesis and historical context.
- [ ] Evaluate third-party data sources for contextual events (e.g., Wikidata, HistoryMakers) under restricted network policy.
- [ ] Prototype AI-assisted event labeling (rename `Event Census` -> `Enumerated in 1850 census`).
- [ ] Implement media prioritization rules (person-specific primary media, event attachments, AI-sourced imagery).
- [ ] Build caching strategy for AI outputs and media URLs.
- [ ] Redesign HTML/CSS theme; create CSS tokens for phase coloring, typography, spacing.
- [ ] Add regression suite (snapshot tests / JSON schema validation) to ensure deterministic exports.
- [ ] Document reproducible pipeline in `tools/export_schema.sh` or dedicated timeline exporter script.

## Open questions
- How to source historical events offline within current network restrictions?
- What licensing constraints apply to AI-suggested imagery and text?
- Should AI enrichment run at export time or via background preprocessing queue?
- What review workflow ensures genealogists approve AI-generated context before publication?

## Next steps
- Gather stakeholder feedback on this roadmap.
- Prioritize MVP slice (e.g., headline rewriting + narrative expansion) before layering external context.
