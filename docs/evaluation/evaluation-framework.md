# Evaluation Framework — COGNET LDI Engine

## Overview

The COGNET LDI Engine produces ranked learning opportunity recommendations. Like any intelligence system, it can be wrong: it may surface topics that aren't actually in demand, miss real opportunities, or assign confidence levels that don't reflect actual reliability. This evaluation framework exists to detect and correct those failures — systematically, over time.

**Evaluation is defined from the start, even if the initial implementation is lightweight.**

An evaluation framework defined on day one, even if run manually and informally, is vastly more valuable than a sophisticated framework built after months of unreviewed output. The first version is documentation-first: checklists, analyst review logs, and manually tracked metrics. Formal tooling is deferred until the data volume justifies it.

---

## 1. Evaluation Principle

The engine's outputs must be evaluated against real-world outcomes, not just internal consistency. A system that consistently produces well-formatted, high-confidence recommendations is not good if those recommendations don't lead to valuable content production decisions.

The ultimate evaluation question: **Did acting on this opportunity produce value?**

This question cannot be answered immediately — it requires a feedback loop that closes months after the opportunity was generated. The evaluation framework must accommodate both short-cycle leading indicators (signal quality, ranking sanity) and long-cycle lagging indicators (production outcomes).

---

## 2. What to Evaluate

### 2.1 Evaluation Targets

| Target | Question |
|---|---|
| Opportunity relevance | Is this topic genuinely in demand in this market? |
| False positive rate | How often does a high-ranked topic turn out not to be worth pursuing? |
| Signal usefulness | Are the signals behind the score actually informative, or are they noise? |
| Confidence reliability | When the engine reports high confidence, is it actually right more often? |
| Evidence adequacy | Are the specific evidence items credible, specific, and informative to an analyst? |
| Opportunity-to-production usefulness | Do approved opportunities actually get built into courses? |
| Ranking sanity | In the top 10 opportunities, do the ranks feel correct to domain-knowledgeable analysts? |

---

## 3. Evaluation Dimensions

### Dimension 1: Signal Quality

**Question:** Are the raw signals ingested by the engine reflecting real, current market demand?

Signal quality evaluation checks whether the inputs are sound before examining whether the outputs are sound.

**What to examine:**
- Job posting counts for top-ranked topics: do they match what analysts observe when manually browsing job boards?
- Search trend indices for top topics: do they correspond to known market trends?
- Content gap assessments: is the internal content inventory scan accurate?
- Are Tier 3 sources introducing outlier values that distort scores?

**Evaluation method:**
For the top 20 opportunities in any given pipeline run, manually verify at least 2 signal values per opportunity using an independent source lookup. Record agreement or disagreement. Track the agreement rate over time.

**Target (MVP):** Manual spot-check of top 20 opportunities after each pipeline run, documented in the evaluation log.

---

### Dimension 2: Ranking Sanity

**Question:** Do the topics at the top of the ranked list deserve to be there?

This is a judgment-based evaluation. It requires analysts with genuine knowledge of the target market to review whether the ordering makes intuitive sense.

**What to examine:**
- Top 10 opportunities: do they represent genuinely high-demand topics?
- Are there obvious high-demand topics that are missing entirely (false negatives)?
- Are there obviously weak topics that appear near the top (false positives)?
- Does the rank order reflect relative demand, or does it feel arbitrary?

**Evaluation method:**
After each pipeline run, at least one market-knowledgeable analyst reviews the top 10 ranked opportunities and rates each as: Correct rank, Too high, Too low, Shouldn't be here. Results are logged.

Track the percentage of "Correct rank" ratings over time. An acceptable target for a calibrated system is >70% correct rank in the top 10.

**Red flag:** If more than 3 of the top 10 are rated "Shouldn't be here," the scoring configuration requires urgent review.

---

### Dimension 3: Confidence Reliability

**Question:** When the engine reports high confidence, is it actually more often correct than when it reports low confidence?

Confidence reliability is a calibration question. A well-calibrated system's high-confidence opportunities should have a meaningfully higher hit rate than its low-confidence opportunities.

**What to examine:**
- Among opportunities eventually approved for production: what was their confidence level at time of generation?
- Among opportunities that were reviewed and rejected by analysts: what was their original confidence level?
- Does high confidence correlate with analyst approval?

**Evaluation method:**
Track the analyst approval rate by confidence tier:

| Confidence Tier | Expected Approval Rate |
|---|---|
| High (≥ 0.70) | > 65% |
| Medium (0.45–0.69) | 35%–65% |
| Low (< 0.45) | < 35% |

If high-confidence opportunities are approved at the same rate as low-confidence ones, the confidence scoring is not providing useful signal and must be recalibrated.

**Note:** This evaluation requires enough historical data to be statistically meaningful. Defer rate calculations until at least 50 opportunities have been reviewed. Until then, record raw counts.

---

### Dimension 4: Evidence Adequacy

**Question:** Are the evidence items attached to each opportunity specific, credible, and useful to an analyst making a decision?

Evidence adequacy can be evaluated immediately after each pipeline run — it does not require a long feedback loop.

**What to examine:**
- Are evidence items specific (actual numbers, named sources, dated signals) or generic?
- Are Tier 1 and Tier 2 sources well-represented in evidence?
- Are there opportunities with fewer than 3 evidence items (sparse evidence)?
- Do evidence items genuinely support the claimed demand, or do they feel tangentially related?

**Evaluation rubric per evidence item:**

| Rating | Criteria |
|---|---|
| Strong | Specific data point from a named, verifiable source with a date |
| Adequate | General reference to a verifiable source; lacks specificity |
| Weak | Vague claim without traceable source; indirect relevance |
| Invalid | LLM-generated or unverifiable; must not appear |

Target: > 80% of evidence items across top-20 opportunities rated Strong or Adequate.

**Evaluation method:**
For each pipeline run, review evidence items for the top 20 opportunities. Rate each using the rubric above. Log counts by rating.

---

### Dimension 5: Production Usefulness

**Question:** Are the opportunities that analysts approve actually turned into content? And when they are, does that content succeed?

This is the long-cycle evaluation dimension. It closes the feedback loop between the intelligence system and business outcomes.

**What to examine:**
- What percentage of `immediate`-classified opportunities are approved by analysts?
- What percentage of approved opportunities enter the content production pipeline?
- What percentage of produced courses correspond to opportunities flagged by COGNET?
- When COGNET-driven content is produced, how does it perform relative to non-COGNET-driven content?

**Tracking mechanism:**
Each opportunity should have a lifecycle state that tracks its journey: `generated → reviewed → approved / rejected → in_production → launched`. The evaluation framework reads these states to compute conversion rates.

**Baseline (MVP):** Simply track whether each approved opportunity eventually enters production. No performance metrics yet — that requires course performance data from production systems.

**Target (mature):** > 50% of `immediate` opportunities that are approved eventually enter production within 12 months.

---

## 4. False Positive Detection

False positives are opportunities that appear high-demand but are not genuinely worth pursuing. They are more harmful than false negatives because they consume analyst attention and potentially content production resources.

### 4.1 False Positive Patterns

| Pattern | Description | Detection |
|---|---|---|
| Spike vs. sustained demand | A topic spikes briefly (news event, viral moment) but demand is not sustained | Compare 30-day and 90-day trend windows; flag large divergence |
| Clickbait topics | High search volume topics driven by entertainment interest, not learning intent | Cross-validate search trends with job postings; require both signals |
| Oversaturated market | Demand exists but the market is fully served by competitor content | Content gap score should catch this; verify manually for top opportunities |
| Seasonality artifacts | Demand appears high due to annual seasonality at ingest time | Use year-over-year trend comparison, not raw recent volume |
| Geographic leakage | Global signals inflating a specific market's score | Ensure signals are filtered to target market; verify for top opportunities |
| LLM hallucination contamination | Summarization artifacts that don't reflect actual signals | LLMs must never generate signal values; this is an architectural enforcement |

### 4.2 False Positive Rate Tracking

After analyst review of each pipeline run, record:
- Number of opportunities reviewed
- Number rated as false positives by the analyst
- The false positive pattern category if identifiable

Track the false positive rate per pipeline run over time. Target: < 20% false positive rate in the top 20 opportunities. A sustained rate above 30% requires a review of the signal ingestion or scoring configuration.

---

## 5. Evaluation Methods

### 5.1 Manual Analyst Review

The primary evaluation method in MVP. After each pipeline run:

1. A designated analyst reviews the top 20 opportunities
2. For each opportunity, the analyst completes a short evaluation form:
   - Ranking sanity rating (Correct / Too high / Too low / Shouldn't be here)
   - Evidence quality rating (Strong / Adequate / Weak / Invalid — at least 3 items)
   - False positive assessment (Yes / No / Unsure)
   - Free-text notes (optional)
3. Results are logged to the evaluation log

This takes approximately 30–60 minutes per run. It is a required step before any opportunity advances to an approved state.

### 5.2 Back-test Against Historical Production Decisions

Periodically (quarterly), compare COGNET's outputs against historical content production decisions made before COGNET existed.

**Methodology:**
1. Compile a list of topics that were produced as courses in the past 12–24 months
2. Simulate running COGNET against signals from the same time period (using archived data if available)
3. Check: would COGNET have flagged these topics? At what rank?
4. Check: would COGNET have flagged topics that were ultimately not produced?

This retrospective analysis validates whether the scoring methodology aligns with actual human judgment in historical cases.

### 5.3 Cross-Source Agreement Analysis

High inter-source agreement is a positive indicator of real demand. Low agreement may indicate noise or a spike.

After each pipeline run, compute agreement statistics:
- For each top-20 opportunity, how many sources agree on the direction of demand (up vs. flat vs. down)?
- What is the coefficient of variation in job posting count estimates across job-market sources?

Log these statistics. High disagreement in top-ranked opportunities is a warning sign to document and investigate.

---

## 6. Evaluation Cadence

| Evaluation Activity | Frequency | Owner |
|---|---|---|
| Manual analyst review of top 20 | After every pipeline run | Designated analyst |
| Evidence quality rating | After every pipeline run | Designated analyst |
| False positive log update | After every pipeline run | Designated analyst |
| Cross-source agreement check | After every pipeline run | Engineering |
| Ranking sanity summary report | Monthly | Lead analyst |
| Confidence reliability rate calculation | Quarterly (when n ≥ 50) | Lead analyst |
| Back-test against historical decisions | Quarterly | Lead analyst + Engineering |
| Production usefulness review | Every 6 months | Product owner |
| Full evaluation framework review | Annually | All stakeholders |

---

## 7. Feedback Loop

The evaluation framework is only valuable if its findings change the system. The feedback loop connects evaluation observations to specific improvement actions.

### 7.1 Feedback Channels

**Short cycle (per-run):**
- Analyst review results feed into the manual override decision for each opportunity
- Identified false positives are logged and may trigger a review of the source or scoring configuration

**Medium cycle (monthly):**
- Ranking sanity summary may trigger scoring weight review (per weight change governance process)
- Recurring evidence quality failures from a specific source may trigger a trust tier re-assessment

**Long cycle (quarterly+):**
- Confidence reliability analysis may trigger confidence downgrade threshold adjustments
- Back-test results may reveal systematic blind spots in signal coverage

### 7.2 Closed-Loop Record

Every evaluation finding that leads to a system change must be documented:
- Observation: what was found
- Root cause assessment: why it happened
- Change made: scoring formula, weight, source tier, threshold
- Expected impact: what should improve
- Validation: in the next evaluation cycle, was the expected improvement observed?

This creates an institutional memory of how the system was improved over time.

---

## 8. Metrics to Track Over Time

The following metrics are tracked in the evaluation log for each pipeline run or period:

| Metric | Computation | Target |
|---|---|---|
| Ranking sanity rate | % of top-10 rated "Correct rank" | > 70% |
| Evidence adequacy rate | % of evidence items rated Strong or Adequate | > 80% |
| False positive rate (top 20) | % of top-20 rated as false positives | < 20% |
| Sparse evidence rate | % of top-20 with < 3 evidence items | < 10% |
| Tier 3 dominance rate | % of top-20 where Tier 3 > 30% of evidence weight | < 15% |
| Confidence reliability (High tier) | Analyst approval rate for high-confidence opps | > 65% |
| Production conversion rate | % of approved opps entering production in 12 mo | > 50% (mature) |
| Cross-source agreement (top 20) | Avg % of sources agreeing on demand direction | > 60% |

All metrics are recorded in the evaluation log with the pipeline run ID, date, analyst identifier, and any notes.

---

## 9. Documentation-First MVP Approach

For MVP, the evaluation framework is implemented as structured documentation, not automated tooling.

### 9.1 MVP Deliverables

- **Evaluation log:** A structured spreadsheet or markdown table tracking per-run metrics
- **Review checklist:** A fillable checklist for the manual analyst review step
- **Feedback log:** A record of system changes driven by evaluation observations

### 9.2 What Is Deferred

The following evaluation capabilities are valuable but deferred beyond MVP:

| Capability | Deferral Reason |
|---|---|
| Automated ranking sanity scoring | Requires labeled ground truth dataset |
| Statistical confidence calibration analysis | Requires n ≥ 50 reviewed opportunities |
| A/B testing of scoring configurations | Requires stable baseline and traffic volume |
| Course performance integration | Requires integration with LMS/production analytics |
| Evaluation dashboard in admin UI | Requires recurring manual data entry to stabilize schema |

### 9.3 Tooling Trigger

Automated evaluation tooling is built when any of the following conditions are met:
- Pipeline runs more than once per week
- More than 200 opportunities have been reviewed
- The manual review step is consistently taking more than 90 minutes per run
- The team size grows to where multiple analysts are reviewing in parallel

Until then, simple, consistently maintained documentation outperforms complex tooling that no one maintains.

---

## 10. Evaluation Log Schema

The evaluation log is a versioned record. Each row corresponds to one pipeline run's evaluation.

```
pipeline_run_id       | string
evaluated_at          | ISO date
evaluator_id          | string
opportunities_reviewed | integer
ranking_sanity_correct | integer (count rated "Correct")
ranking_sanity_total   | integer (count reviewed)
evidence_adequate      | integer (items rated Strong or Adequate)
evidence_total         | integer (total items reviewed)
false_positives        | integer
false_positive_patterns | string (comma-separated categories)
sparse_evidence_count  | integer (opps with < 3 items)
tier3_dominant_count   | integer (opps where Tier 3 > 30%)
notes                 | free text
```

This schema is stable for MVP. Fields may be added but not removed without migrating historical records.
