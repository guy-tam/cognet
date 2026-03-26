# Taxonomy Service

## Purpose
Canonical taxonomy management — resolves raw labels to canonical entities.

## Key Files
- `resolver.py` — In-memory alias resolution for skills, topics, countries, languages
- `seed.py` — Initial seed data for taxonomy bootstrap

## Inputs
Raw skill/topic/role/country/language labels from connectors and enrichment.

## Outputs
`ResolvedSkill`, `ResolvedTopic` with canonical names and confidence scores.

## Governance
Adding new canonical entities requires updating the alias maps AND documenting in `docs/data/taxonomy-model.md`.
