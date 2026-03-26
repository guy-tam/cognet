# services/opportunities

## Purpose
Generate structured `OpportunityBrief` objects from ranked signals. Applies filtering, deduplication, and sorting to produce a clean, prioritized list of learning opportunities ready for review or downstream publishing.

## Inputs
- Ranked `SignalVector` list (output of `RankingEngine.rank_signals`)
- `RankingEngine` instance (for score and confidence computation)
- `min_score` threshold (default: 0.35) — vectors below this are filtered out
- `min_confidence` threshold (default: 0.20) — low-confidence signals are excluded

## Outputs
`list[OpportunityBrief]` — sorted descending by `opportunity_score`. Each brief includes:
- Canonical topic name, country/language, audience segment, recommended format
- `opportunity_score`, `score_breakdown`, `confidence_score`, `classification`
- `why_now_summary` — deterministic text summary (no LLM)
- `evidence` — list of `EvidenceItem` per source family
- `lifecycle_state` — starts at `surfaced`

## Key File
| File | Responsibility |
|---|---|
| `generator.py` | `OpportunityGenerator` — generate, dedup, filter, sort |

## Deduplication
Dedup key: `(canonical_topic_name, country_code, language_code)`. When duplicates exist, the highest-scoring brief is kept.
