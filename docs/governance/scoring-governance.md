# Scoring Governance — COGNET LDI Engine

## Overview

This document defines how learning opportunities are scored, ranked, classified, and audited in the COGNET LDI Engine. Scoring is the core output of the system. It must be deterministic, explainable, versioned, and protected against drift or manipulation.

---

## 1. Scoring Principle

**Deterministic first. LLM optional for summaries only.**

The scoring engine produces numerical outputs through explicit, rule-based formulas. Given identical inputs, it must produce identical outputs. This is not negotiable.

LLM usage in the scoring pipeline is restricted to:
- Generating the `why_now_summary` narrative (clearly labeled as AI-generated)
- Generating `market_context` and `language_context` descriptive text

LLMs must never:
- Determine or influence any numerical score
- Make classification decisions
- Override deterministic scoring outputs
- Contribute to the ranking order

The reason for this constraint: scores must be explainable and auditable. An analyst must be able to trace every score component back to a specific signal, formula, and weight. LLM-influenced numbers cannot be traced.

---

## 2. Score Families

Each opportunity is assigned nine individual scores, each on a normalized 0.0–1.0 scale.

### 2.1 Score Definitions

| Score Family | Field Name | Range | Definition |
|---|---|---|---|
| Demand Score | `demand_score` | 0–1 | Frequency and volume of demand signals across all sources. Measures how often and how strongly this topic is being requested in the target market. |
| Growth Score | `growth_score` | 0–1 | Momentum trend over the analysis time window. Measures whether demand is accelerating, flat, or declining. |
| Job Market Score | `job_market_score` | 0–1 | Employer demand in job postings. Measures how prominently this skill appears in active job listings in the target market. |
| Trend Score | `trend_score` | 0–1 | Search and trend signal strength. Derived from search trend APIs, social listening, or publication volume. |
| Content Gap Score | `content_gap_score` | 0–1 | Gap between observed demand and internal supply. High score indicates strong demand with no equivalent internal content to serve it. |
| Localization Fit Score | `localization_fit_score` | 0–1 | Appropriateness of the opportunity for the target market and language. Considers cultural fit, regulatory environment, and local market maturity. |
| Teachability Score | `teachability_score` | 0–1 | Estimated feasibility of producing content for this topic. Considers SME availability, topic complexity, content production lead time, and IP constraints. |
| Strategic Fit Score | `strategic_fit_score` | 0–1 | Alignment with declared company strategic priorities. Derived from a curated priority topic list and market focus areas. |
| Confidence Score | `confidence_score` | 0–1 | Quality and coverage of evidence. Reflects how many sources contributed, their trust tiers, inter-source agreement, and signal freshness. |

### 2.2 Score Computation Rules

Each score is computed by a dedicated scoring function in the scoring module. Scoring functions are pure functions: same inputs always produce same outputs.

- All inputs to scoring functions are typed and validated before use
- Scoring functions must not make external API calls
- Scoring functions must not read from the database directly — inputs are passed explicitly
- All intermediate calculation values must be logged alongside final scores

---

## 3. Total Opportunity Score Formula

The total opportunity score is a weighted average of the eight primary score families (confidence score is not included in the weighted average — it is a meta-score).

### 3.1 Formula

```
total_score = (
  w_demand       × demand_score       +
  w_growth       × growth_score       +
  w_job_market   × job_market_score   +
  w_trend        × trend_score        +
  w_gap          × content_gap_score  +
  w_loc_fit      × localization_fit_score +
  w_teachability × teachability_score +
  w_strategic    × strategic_fit_score
) / sum(all_weights)
```

Where all weights are positive real numbers and the formula normalizes to a 0–1 result.

### 3.2 Default Weight Configuration

| Score Family | Default Weight | Rationale |
|---|---|---|
| `demand_score` | 0.25 | Primary signal — actual observed demand volume |
| `job_market_score` | 0.20 | Employer demand is a strong proxy for real skill need |
| `content_gap_score` | 0.15 | Business value depends on whether we can serve unmet demand |
| `growth_score` | 0.15 | Momentum indicates whether opportunity is emerging or fading |
| `trend_score` | 0.10 | Supporting signal — corroborates demand from a different angle |
| `strategic_fit_score` | 0.08 | Company alignment modulates what we act on |
| `localization_fit_score` | 0.05 | Market-specific viability filter |
| `teachability_score` | 0.02 | Low weight — a low teachability score informs planning, not ranking |

**Sum of default weights: 1.00**

These weights represent the current best estimate of relative signal value. They are not arbitrary — each has a documented rationale. Changes to weights must go through the governance process defined in §4.

### 3.3 Weight Storage

Weights are stored in a versioned configuration object, not hardcoded in scoring logic.

```ts
interface ScoringWeightConfig {
  version: string;               // semver, e.g. "1.2.0"
  effective_from: string;        // ISO date
  changed_by: string;            // analyst or engineer identifier
  change_reason: string;         // required free text
  weights: {
    demand_score: number;
    growth_score: number;
    job_market_score: number;
    trend_score: number;
    content_gap_score: number;
    localization_fit_score: number;
    teachability_score: number;
    strategic_fit_score: number;
  };
}
```

The active weight configuration is referenced by version in each scoring run's audit record.

---

## 4. Weight Change Governance

Weights are not tuning knobs to be adjusted casually. Every change to scoring weights changes the relative ranking of every opportunity in the system and must be treated as a consequential decision.

### 4.1 Process for Changing Weights

1. **Proposal:** The proposing party submits a weight change proposal in writing, specifying: current weights, proposed weights, rationale, expected impact, and how the change will be validated.

2. **Back-test:** Before applying, simulate the new weights against the last 3 pipeline runs. Review whether the ranking order changes in expected and acceptable ways.

3. **Review:** At least one other analyst reviews the proposal and back-test results.

4. **Approval:** A lead analyst or product owner approves the change.

5. **Documentation:** The new weight configuration is committed to the configuration store with all metadata fields populated (version, effective_from, changed_by, change_reason).

6. **Announcement:** All analysts using the system are notified of the weight change before it takes effect.

### 4.2 Prohibited Weight Changes

- Weights may not be changed to surface a specific desired topic
- Weights may not be changed retroactively to justify a past decision
- Emergency weight changes bypassing the review step are prohibited

---

## 5. Classification Thresholds

Each opportunity is assigned a classification tier based on its total score and confidence score.

### 5.1 Default Classification Rules

| Classification | Condition | Meaning |
|---|---|---|
| `immediate` | total_score ≥ 0.80 AND confidence_score ≥ 0.70 | Strong demand, high confidence. Ready for production consideration. |
| `near_term` | total_score ≥ 0.65 AND confidence_score ≥ 0.55 | Solid signal, reasonable confidence. Worth planning for in the next cycle. |
| `watchlist` | total_score ≥ 0.50 AND confidence_score ≥ 0.40 | Emerging signal. Monitor for development. Not yet ready to act on. |
| `low_priority` | total_score ≥ 0.35 OR confidence_score < 0.40 | Weak signal or low confidence. Record for completeness only. |
| `rejected` | total_score < 0.35 | Insufficient signal. Not worth tracking currently. |

### 5.2 Classification Override

Classification may be manually overridden by an analyst with a documented reason. Overrides are logged in the audit trail with:
- Original classification
- Override classification
- Analyst identifier
- Timestamp
- Free-text reason (required)

Manual overrides do not change the underlying scores — they only change the displayed classification.

### 5.3 Threshold Change Governance

Classification thresholds follow the same governance process as weight changes. Changes must be back-tested and documented.

---

## 6. Confidence Score and Downgrade Triggers

The confidence score reflects how much trust to place in the overall opportunity score. High scores with low confidence should be treated with caution.

### 6.1 Confidence Downgrade Triggers

The confidence score is subject to automatic downgrade when any of the following conditions are detected:

| Trigger | Downgrade Amount | Rationale |
|---|---|---|
| Only one source contributed signals | −0.20 | Single-source data is not cross-validated |
| Inter-source agreement is low (<60%) | −0.15 | Conflicting signals reduce reliability |
| All sources are Tier 3 (experimental) | −0.20 | Unverified sources carry higher uncertainty |
| Signals are older than 90 days | −0.10 | Stale signals may not reflect current demand |
| Sparse enrichment (<3 evidence items) | −0.10 | Thin evidence base |
| Job market signal absent entirely | −0.10 | Job postings are the strongest demand proxy |

Downgrades are cumulative up to a floor of 0.10. An opportunity cannot have a confidence score below 0.10 regardless of trigger count (it retains minimal signal value).

### 6.2 Confidence Display

The confidence score is always displayed alongside the total score. The UI renders a confidence level label based on the score:

| Confidence Score | Label |
|---|---|
| ≥ 0.70 | High |
| 0.45–0.69 | Medium |
| < 0.45 | Low |

Low confidence opportunities are visually flagged in the opportunity list and detail view.

---

## 7. Score Versioning

Every scored opportunity record references the scoring configuration version used to produce it.

### 7.1 Version Fields on Scored Opportunity

```ts
interface ScoringMetadata {
  scoring_engine_version: string;   // code version, e.g. "2.1.0"
  weight_config_version: string;    // weight config version, e.g. "1.2.0"
  scored_at: string;                // ISO timestamp
  pipeline_run_id: string;          // links to pipeline run record
}
```

### 7.2 Re-scoring

When weights change, existing opportunities are not automatically re-scored. Re-scoring requires an explicit pipeline run with the new configuration. Historical scores are preserved for audit purposes.

When comparing opportunities scored under different weight versions, the UI must display the weight version used. Cross-version score comparison is misleading and must be avoided in rankings.

---

## 8. Scoring Audit Trail Requirements

Every pipeline run produces an audit record. The audit trail must be append-only — no records are deleted or modified after creation.

### 8.1 Audit Record Contents

Each opportunity's scoring audit record must contain:

- All raw signal values that were input to scoring functions
- All intermediate calculation values
- All individual score family values with their inputs
- The weight configuration version used
- The total score computed
- The classification assigned
- Any confidence downgrade triggers activated and their amounts
- The pipeline run ID
- The timestamp

### 8.2 Audit Trail Retention

Scoring audit records are retained indefinitely. They are the legal and operational record of how the system made decisions. They must not be pruned, compressed, or anonymized without explicit policy approval.

### 8.3 Audit Trail Access

The audit trail is readable by analysts through the admin UI (via the opportunity detail view, collapsed under "Scoring details"). It is also accessible via API for programmatic analysis. Write access to audit records is prohibited from all application code paths.

---

## 9. Ranking Engine Determinism Contract

The ranking engine produces an ordered list of opportunities by total score. This contract must hold:

1. **Same inputs → same output.** Given the same set of scored opportunities and the same weight configuration, the ranking order is always identical.

2. **Tie-breaking is deterministic.** When two opportunities have equal total scores, the tiebreaker is `confidence_score` descending, then `created_at` ascending. The tiebreaker is documented and invariant.

3. **Ranking does not modify scores.** The ranking engine reads scores and produces order. It does not adjust, normalize, or modify any score value.

4. **No hidden factors.** Nothing outside the declared score fields and weights affects ranking. There are no hidden boosts, editorial overrides, or recency adjustments applied silently.

5. **Ranking is reproducible.** Given a pipeline run ID, the ranking for that run can be reproduced at any future time using the audit record.

---

## 10. Anti-Fake-Scoring Rules

These rules prevent gaming, inflation, or corruption of scores:

**Rule 1: No manual score entry.**
Scores are always computed by the scoring engine from ingested signals. Analysts cannot directly enter or edit numerical score values.

**Rule 2: No retroactive signal entry.**
Signals are ingested at a point in time. Backdating signal ingestion timestamps is prohibited.

**Rule 3: Strategic fit score must reference a versioned priority list.**
`strategic_fit_score` is computed against a declared, versioned priority topic list. It cannot be set manually per opportunity. Changes to the priority list are versioned and documented.

**Rule 4: Confidence score cannot be manually raised.**
The confidence score can only be lowered by triggers. It cannot be manually increased to make a low-confidence opportunity appear more certain than it is.

**Rule 5: LLM outputs cannot modify scores.**
All LLM calls in the pipeline produce only text fields. There is no code path by which an LLM response can write to a numerical score field. This must be enforced architecturally (strict type separation between score fields and text fields).

**Rule 6: Classification overrides are logged and visible.**
Manual classification overrides are always visible in the UI alongside the original computed classification. They cannot be hidden or made to appear as the computed result.

---

## 11. Summary Reference Table

| Concept | Value / Policy |
|---|---|
| Score range | 0.0 – 1.0 for all families |
| Total score formula | Weighted average of 8 families |
| Confidence score role | Meta-score; not in weighted average; affects classification thresholds |
| Default weight sum | 1.00 |
| Weight change process | Proposal → Back-test → Review → Approval → Documentation |
| Classification tiers | immediate, near_term, watchlist, low_priority, rejected |
| Confidence floor | 0.10 (minimum, regardless of downgrades) |
| Ranking tiebreaker | confidence_score desc → created_at asc |
| Audit retention | Indefinite, append-only |
| LLM role | Text generation only — never numerical scoring |
