# services/ranking

## Purpose
Deterministic scoring and ranking of learning opportunities. Given a list of `SignalVector` objects, the engine applies weighted dimension scores to produce a total opportunity score and a ranked, explainable output.

## Inputs
`list[SignalVector]` — each vector carries pre-computed dimension scores (demand, growth, job market, trend, content gap, localization fit, teachability, strategic fit).

## Outputs
Ranked `list[tuple[SignalVector, total_score: float, ScoreBreakdown]]` sorted descending by total score.

## Key Files
| File | Responsibility |
|---|---|
| `engine.py` | `RankingEngine` — compute_score, compute_confidence, classify, rank_signals |
| `weights.py` | `ScoringWeights` dataclass + `DEFAULT_WEIGHTS` constant |

## Governance
Weight changes **require compliance** with `docs/governance/scoring-governance.md`. Do not modify `DEFAULT_WEIGHTS` without a documented, reviewed rationale. All weight changes must be traceable to a governance record.

## Testing
Pure unit tests — no database or network dependencies required. Tests live in `tests/unit/ranking/`. Run with `pytest tests/unit/ranking/`.
