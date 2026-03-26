# Enrichment Service

## Purpose
Extract and map skills, topics, roles from normalized records.

## Strategy
Rule-based for MVP using TaxonomyResolver. Designed for optional LLM augmentation later.

## Key Files
- `enricher.py` — Main enrichment logic with skill/topic extraction

## Inputs
`NormalizedRecord` from normalization pipeline stage.

## Outputs
`EnrichmentOutput` containing `EnrichedSkillRef`, `EnrichedTopicRef` lists with confidence scores.

## Dependencies
Uses `TaxonomyResolver` from `services/taxonomy/`.
