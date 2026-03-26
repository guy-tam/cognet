# services/signals

## Purpose
Deterministic signal computation from enriched source data. Aggregates normalized records and enrichment data into `SignalVector` objects, one per topic/skill/market combination, ready for the `RankingEngine`.

## Inputs
- Normalized records (`NormalizedRecord`) from the normalization layer
- Enrichment data (taxonomy mappings, localization metadata) — stub in MVP

## Outputs
`SignalVector` per topic/skill/market — each vector carries:
- `scores: ScoreBreakdown` — all 8 dimension scores (demand, growth, job market, trend, content gap, localization fit, teachability, strategic fit)
- `confidence_score` — based on source family coverage and evidence count
- `evidence_count` and `source_families` — for downstream confidence adjustment

## Key File
| File | Responsibility |
|---|---|
| `computer.py` | `SignalComputer` — compute_demand_score, compute_growth_score, compute_content_gap_score, build_signal_vector |

## Rules
- All computation must be deterministic: same inputs → same outputs, always.
- No LLM calls, no network access, no database reads inside `SignalComputer`.
- Localization fit, teachability, and strategic fit scores are stubbed at 0.7 in MVP — replace with real computation before production.
