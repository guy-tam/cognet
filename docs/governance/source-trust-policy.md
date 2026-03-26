# Source Trust Policy — COGNET LDI Engine

## Overview

Every demand signal in the COGNET LDI Engine originates from an external or internal data source. The quality of the engine's outputs depends entirely on the quality and reliability of those sources. This document defines how sources are classified, how their trust level affects scoring and review, and how new sources are added, maintained, and removed.

---

## 1. Source Trust Tiers

Sources are classified into three trust tiers. The tier assignment reflects the reliability, verifiability, and consistency of the source — not simply its size or popularity.

### Tier 1 — High Trust

**Definition:** Authoritative, primary sources with documented methodology, stable APIs or data structures, and identifiable institutional provenance.

**Examples:**

| Source | Type | Notes |
|---|---|---|
| LinkedIn Job Search API | Employer job postings | Direct employer-posted data |
| Israeli Employment Service (Taasuka) | Official labor statistics | Government source |
| Israeli Central Bureau of Statistics | Labor force surveys | Official, methodologically documented |
| Bureau of Labor Statistics (US) | Official labor statistics | Reference market data |
| Glassdoor Job Listings API | Employer job postings | Verified employer accounts |
| Indeed Jobs API | Employer job postings | High-volume, direct employer postings |
| O*NET Online (US DOL) | Occupational data | Authoritative taxonomy and skill data |

**Requirements to qualify as Tier 1:**
- Institutional identity is verifiable
- Data collection methodology is documented and publicly available
- API or data feed is stable with a defined SLA or update cadence
- Data represents primary observations (employer posted, government measured) rather than aggregated inference

---

### Tier 2 — Medium Trust

**Definition:** Reputable aggregated platforms or well-maintained commercial APIs where the underlying data is generally reliable but involves aggregation, indexing, or algorithmic processing that introduces uncertainty.

**Examples:**

| Source | Type | Notes |
|---|---|---|
| Google Trends API | Search volume trends | Relative index, not absolute volume |
| Lightcast (formerly Burning Glass) | Labor market analytics | Aggregates job postings; strong methodology but proprietary |
| Coursera/LinkedIn Learning catalog | Content supply signal | Inferred supply from competitor catalogs |
| Stack Overflow Developer Survey | Developer technology adoption | Self-reported; large sample |
| GitHub repository activity | Technology adoption proxy | Indirect signal; requires interpretation |
| SimilarWeb | Web traffic trends | Aggregated and estimated, not raw |

**Requirements to qualify as Tier 2:**
- Source has a publicly identified organization behind it
- Methodology is described, even if not fully transparent
- Data represents real observations with known aggregation or inference layers
- Source has a track record of use in industry analysis

---

### Tier 3 — Experimental

**Definition:** Sources that are scraped, inferred, crowdsourced, or provided by unknown third parties. These sources may contain signal, but cannot be assumed reliable without cross-validation.

**Examples:**

| Source | Type | Notes |
|---|---|---|
| Scraped job board data (non-API) | Job postings | Structure and completeness not guaranteed |
| Third-party data brokers | Aggregated signals | Provenance often unclear |
| Reddit/HackerNews topic mining | Community interest | Noisy; highly context-dependent |
| Social media trend monitoring | Interest signals | Easily distorted by viral events |
| Internal sales inquiry logs | Customer interest | Small sample; not statistically representative |
| LLM-generated market estimates | Inferred demand | Must never be used as primary evidence |

**Requirements for Tier 3 use:**
- Source must be explicitly documented before use
- All evidence items from Tier 3 sources are flagged in the UI
- Tier 3 signals trigger automatic analyst review flags (see §4)
- LLM-generated content must never be classified as Tier 3 — it is excluded from evidence entirely

---

## 2. How Trust Tier Affects Confidence Scoring

Trust tier is a direct input to the confidence scoring function.

### 2.1 Per-Signal Trust Weight

When computing the confidence score, each evidence item contributes to a weighted coverage metric. The weight assigned to each evidence item depends on its source tier:

| Trust Tier | Evidence Weight |
|---|---|
| Tier 1 | 1.0 |
| Tier 2 | 0.6 |
| Tier 3 | 0.25 |

The confidence score benefits more from a single Tier 1 source than from four Tier 3 sources.

### 2.2 Tier-Based Confidence Penalties

In addition to weighted evidence contributions, the following automatic penalties apply:

| Condition | Confidence Downgrade |
|---|---|
| All contributing sources are Tier 3 | −0.20 |
| No Tier 1 source contributes any signal | −0.10 |
| Tier 3 sources are the only job-market signal | −0.15 |
| Mix of Tier 1 and Tier 3 with no Tier 2 | −0.05 |

These penalties are cumulative with other confidence downgrade triggers defined in the Scoring Governance document.

---

## 3. How Trust Tier Affects Evidence Weight

In score family computations (demand_score, job_market_score, trend_score), individual signal values are weighted by source tier before aggregation:

```
weighted_signal = signal_value × tier_weight

aggregated_signal = sum(weighted_signals) / sum(tier_weights)
```

This means that a Tier 1 job posting count has four times the weight of a Tier 3 scraped estimate when both contribute to the same score. The formula prevents Tier 3 sources from dominating even if they produce high-volume but unreliable data.

---

## 4. How Trust Tier Affects Review Urgency

### 4.1 Analyst Review Flags

Any opportunity where Tier 3 sources contributed more than 30% of the total evidence weight is automatically flagged for analyst review.

The flag appears in the admin UI:
- In the opportunity list: an orange "Review needed" badge
- In the opportunity detail: a prominent warning panel above the evidence list

The warning text reads: *"One or more evidence items for this opportunity are from experimental sources. Verify independently before approving."*

### 4.2 Classification Gate

Opportunities flagged due to Tier 3 source dominance cannot be classified as `immediate` without a manual analyst override. The system enforces this by requiring explicit confirmation with a reason.

---

## 5. Source Addition Policy

Adding a new source to the COGNET pipeline requires completing the following documentation before any signals from that source are used in scoring.

### 5.1 Required Documentation Fields

| Field | Description |
|---|---|
| `source_id` | Unique identifier (snake_case, English only) |
| `source_name` | Human-readable name |
| `source_url` | Homepage or API documentation URL |
| `provider_organization` | Legal entity responsible for the source |
| `trust_tier` | 1, 2, or 3 — with written justification |
| `signal_types` | List: job_postings, search_trends, content_catalog, labor_stats, etc. |
| `access_method` | API, file download, scrape, manual upload |
| `data_format` | JSON, CSV, XML, HTML, etc. |
| `update_frequency` | How often fresh data is available |
| `freshness_sla` | Maximum acceptable data age for use in scoring |
| `geographic_coverage` | Markets the source covers |
| `language_coverage` | Languages the source covers |
| `legal_review_status` | pending / approved / conditionally_approved |
| `terms_of_service_url` | Link to ToS relevant to our use |
| `pii_assessment` | Does the source contain PII? If yes, what and how handled? |
| `rate_limits` | Documented rate limits or usage quotas |
| `authentication_method` | API key, OAuth, IP allowlist, none |
| `added_by` | Identifier of the person adding the source |
| `added_at` | ISO date |
| `notes` | Any additional context |

No new source may contribute to scoring until all required fields are complete and legal review is approved or conditionally approved.

### 5.2 Tier Assignment Review

Tier assignment is reviewed by at least one person other than the submitter. Disagreements about tier assignment are resolved by discussing the rationale explicitly — the more conservative (lower-trust) tier is used when there is uncertainty.

---

## 6. Source Decommission Policy

When a source is no longer suitable for use, it must be formally decommissioned — not silently removed.

### 6.1 Decommission Triggers

- Terms of service change that prohibits our current use
- Source stops being updated or becomes unreliable
- Source is superseded by a higher-quality alternative
- Legal or compliance issue is discovered

### 6.2 Decommission Process

1. Flag the source as `decommissioning` in the source registry
2. Assess what opportunities have evidence from this source — document the impact
3. Determine whether affected opportunities need re-scoring
4. Remove the source from active pipeline configuration
5. Mark source as `decommissioned` with a date and reason
6. Existing evidence records referencing this source are preserved but labeled with decommission status

Decommissioned source records are retained for audit purposes. They are never deleted.

---

## 7. Data Freshness Requirements Per Tier

Stale data degrades signal quality. Each tier has a maximum age for data used in active scoring:

| Trust Tier | Maximum Data Age for Scoring |
|---|---|
| Tier 1 | 60 days |
| Tier 2 | 45 days |
| Tier 3 | 30 days |

Data older than these thresholds triggers a confidence downgrade of −0.10 (as documented in Scoring Governance §6.1).

**Note on Tier 3 strictness:** Experimental sources are held to a tighter freshness window because their signal quality is more volatile. An old Tier 3 signal has compounding uncertainty.

Data age is computed from the signal's reported collection date, not from when COGNET ingested it. If a source does not report a collection date, the ingest date is used but a Tier 3 freshness penalty is applied regardless of tier.

---

## 8. Conflict Resolution Between Sources

When two sources provide contradictory demand signals for the same topic in the same market, a structured resolution process applies.

### 8.1 Conflict Detection

A conflict is detected when:
- Two sources of the same signal type report values that differ by more than 40% relative to the higher value
- One source reports a strong upward trend while another reports flat or downward movement for the same topic

### 8.2 Resolution Rules

| Scenario | Resolution |
|---|---|
| Tier 1 vs Tier 2 conflict | Tier 1 value used; Tier 2 retained as context |
| Tier 1 vs Tier 1 conflict | Average used; confidence downgraded by −0.15 |
| Tier 2 vs Tier 2 conflict | Average used; analyst review flag set |
| Tier 1 vs Tier 3 conflict | Tier 1 value used; Tier 3 evidence quarantined (not used in score) |
| Tier 2 vs Tier 3 conflict | Tier 2 value used; Tier 3 evidence quarantined |
| Tier 3 vs Tier 3 conflict | No signal used from either; analyst review flag set |

**Quarantined evidence** is preserved in the audit record but excluded from scoring calculations. The admin UI shows quarantined evidence items with a visual indicator and the reason for quarantine.

### 8.3 Conflict Log

All detected conflicts are written to a conflict log with:
- The two conflicting sources and their values
- The resolution applied
- The confidence impact
- The pipeline run ID and timestamp

The conflict log is accessible via the pipeline status page in the admin UI.

---

## 9. Legal and Compliance Checklist Per Source

Before a source may be used in production, the following compliance checklist must be completed:

| Requirement | Check |
|---|---|
| Terms of service reviewed for data use restrictions | |
| Commercial use permitted (or not required) | |
| Attribution requirements identified and met | |
| No prohibition on automated access (for scraping) | |
| Data residency requirements assessed | |
| Export control laws assessed (for international data) | |
| Source does not violate robots.txt (for web sources) | |
| Rate limits documented and respected | |
| No personal data is collected or stored (see §10) | |
| Data retention obligations from ToS documented | |

Legal review is performed by or approved by the designated legal/compliance contact. The reviewer's name and approval date are recorded in the source registry.

---

## 10. PII Avoidance Policy

The COGNET LDI Engine is a market intelligence tool. It must never collect, store, or process personally identifiable information.

### 10.1 What Is Prohibited

- Individual job-seeker names, emails, or profile data
- Individual employer contact information
- User-level search or browsing data
- Any data that can be linked to a specific natural person

### 10.2 Aggregate vs. Individual Data

All ingested data must be aggregate or anonymized before storage:

- Job posting counts, not individual posting details with applicant information
- Trend indices, not individual user search histories
- Market-level statistics, not company-level data that could identify small organizations

### 10.3 Source-Level PII Screening

Before any new source is activated, its data output must be reviewed to confirm it contains no PII fields. If PII is found:
1. The source is suspended from ingestion immediately
2. Any data already ingested that contains PII is deleted
3. The source's PII assessment in the source registry is updated
4. The source may only be re-activated after implementing a filtering layer that strips PII before storage

### 10.4 Storage Prohibition

No component of the COGNET pipeline (ingestion, enrichment, scoring, storage) may write PII to any database, log, audit record, or temporary file.

---

## 11. Rate Limiting and Respectful Access Policy

### 11.1 Principles

COGNET must not cause harm or disruption to data providers, including those providing data voluntarily through open access.

### 11.2 Rate Limit Compliance

- All API sources must have their rate limits documented in the source registry
- The ingestion pipeline must enforce these limits programmatically — not rely on human operators to avoid violations
- Rate limit violations must be logged and reviewed; repeated violations may result in source suspension

### 11.3 Scraping Guidelines (Tier 3 sources)

When scraping is used for Tier 3 sources:
- Respect `robots.txt` directives at all times
- Use a crawl delay of at least 2 seconds between requests
- Identify the crawler with a descriptive User-Agent string that includes contact information
- Do not scrape during peak usage hours unless explicitly permitted
- Cease scraping immediately upon receiving a 429 or 503 response and implement exponential backoff

### 11.4 API Key Security

- All API keys and credentials are stored in the secrets management system (never in code or configuration files)
- API keys are rotated at least annually or immediately upon suspected compromise
- Each source uses a dedicated API key where possible — shared keys across sources are prohibited

---

## 12. Source Registry Summary

The source registry is the authoritative record of all data sources. It must be:

- Stored in version control alongside the codebase
- Updated as part of any PR that adds or modifies source integrations
- Reviewed quarterly for accuracy and freshness
- The single source of truth for trust tier assignments, legal status, and freshness requirements

Sources are never informally "added" by engineers without going through this documented process. Undocumented sources discovered in the pipeline are treated as a security and compliance incident.
