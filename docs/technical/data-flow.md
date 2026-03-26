# COGNET LDI Engine — Data Flow

**Version:** 1.0
**Status:** Active
**Last Updated:** 2026-03-26
**Owner:** Engineering

---

## 1. End-to-End Pipeline Overview

The LDI Engine pipeline transforms raw external signals into ranked, human-reviewable learning opportunity briefs. The pipeline is linear with clear stage boundaries and explicit handoffs.

```
┌──────────────────────────────────────────────────────────────────┐
│                    PIPELINE RUN (orchestration)                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  [1] Source Fetch        External APIs / Files                    │
│         ↓                                                          │
│  [2] Raw Landing         raw_source_records (append-only)         │
│         ↓                                                          │
│  [3] Normalization       normalized_records (universal schema)    │
│         ↓                                                          │
│  [4] Enrichment          taxonomy tagging, skill/role extraction  │
│         ↓                                                          │
│  [5] Signal Computation  signal_snapshots (per topic/market/time) │
│         ↓                                                          │
│  [6] Ranking             composite scores per snapshot            │
│         ↓                                                          │
│  [7] Opportunity Gen     opportunity_briefs + evidence_items      │
│         ↓                                                          │
│  [8] Serving             REST API → Admin UI                      │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

Each stage is implemented as a Celery task. The orchestration domain chains these tasks in dependency order. Each stage reports to the `pipeline_runs` table: start time, end time, records in, records out, errors encountered.

---

## 2. Source Families

The LDI Engine ingests from three primary source families. Each family has different schemas, cadences, and signal types.

### 2.1 Job Postings

**What they provide:** Direct evidence of employer demand for skills, roles, and locations. The highest-signal source for understanding what the labor market is currently requiring.

**Source examples:**
- Job board aggregator APIs (e.g., Adzuna, JSearch via RapidAPI, direct LinkedIn API if available)
- Israeli job boards (Drushim, AllJobs) — Hebrew-language sources
- Direct employer career pages (via structured data parsing)

**Key fields extracted:** job title, company, location, country, required skills (raw text), preferred skills (raw text), seniority level, industry/sector, date posted, language of posting

**Ingestion cadence:** Daily (full re-fetch for rolling 30-day window)

**Volume estimate:** 5,000–50,000 records per run depending on market scope

### 2.2 Trend and Search Signals

**What they provide:** Evidence of curiosity and emerging awareness — what people are searching for, what topics are trending in developer/professional communities.

**Source examples:**
- Google Trends API (relative search interest over time by keyword and geography)
- Stack Overflow Trends (technology tag activity)
- GitHub repository star velocity (proxy for technology adoption)
- Twitter/X tech keyword volume (if API access available)
- Israeli tech community forums (e.g., Reversim, Dev.il activity signals)

**Key fields extracted:** keyword/topic, geographic scope, relative interest score, time series data points, trend direction (rising/stable/falling)

**Ingestion cadence:** Weekly (trend data has lower update frequency than job postings)

**Volume estimate:** 100–500 topic/keyword combinations per run

### 2.3 Internal Learning Supply

**What they provide:** What Cognet already offers. Essential for computing supply gap — the difference between market demand and available content.

**Source examples:**
- Cognet CMS/LMS export or API (course catalog, topic coverage, module metadata)
- Internal taxonomy of existing content topics and skills covered

**Key fields extracted:** asset title, topics covered, skills covered, language, quality score, last updated date, enrollment/completion data (if available)

**Ingestion cadence:** Weekly or on-demand (when content catalog changes)

**Volume estimate:** Hundreds to low thousands of internal assets

---

## 3. Raw Landing Contract

All ingested records — regardless of source type — are written to the `raw_source_records` table in a standardized envelope. The envelope preserves the original payload while adding system metadata.

### Raw Record Envelope Schema

```json
{
  "id": "uuid",
  "source_run_id": "uuid",
  "source_type": "job_posting | trend_signal | internal_supply",
  "source_name": "string (e.g., 'adzuna_il', 'google_trends', 'cognet_cms')",
  "external_id": "string (source's own ID for this record, if available)",
  "fetched_at": "ISO 8601 timestamp",
  "raw_payload": "jsonb (original response, unparsed)",
  "detected_language": "string (ISO 639-1, e.g., 'en', 'he')",
  "detected_country": "string (ISO 3166-1 alpha-2, e.g., 'IL', 'US')",
  "normalization_status": "pending | normalized | failed | skipped",
  "normalization_error": "string | null"
}
```

### Raw Landing Rules

1. **Write-once.** Raw records are never modified after insertion. If re-ingestion is needed, a new `source_run` is created and new raw records are written. Deduplication happens in normalization.
2. **Preserve everything.** The `raw_payload` JSONB column stores the complete original response. Nothing is discarded at this stage.
3. **Fail gracefully.** If a single record fails to land (e.g., malformed JSON), it is logged and skipped. It does not fail the entire source run.
4. **Source run isolation.** Every batch of fetched records is tied to a `source_run` record. If a source run fails midway, its partial records are marked with the run's failure status.

---

## 4. Normalization Step

**Input:** `raw_source_records` with `normalization_status = 'pending'`
**Output:** `normalized_records` rows; raw records updated to `normalized` or `failed`

### Purpose
Normalization converts source-specific schemas into a universal intermediate schema. Each source type has a dedicated normalizer class that knows how to extract the universal fields from that source's raw payload format.

### Universal Normalized Schema

```json
{
  "id": "uuid",
  "raw_record_id": "uuid (FK to raw_source_records)",
  "source_type": "job_posting | trend_signal | internal_supply",
  "source_name": "string",
  "pipeline_run_id": "uuid",
  "title": "string",
  "description_text": "string | null (cleaned, no HTML)",
  "raw_skills_text": "string | null (concatenated skill mentions)",
  "location_raw": "string | null (as-written in source)",
  "country_code": "string | null (ISO 3166-1 alpha-2)",
  "region_raw": "string | null",
  "language_code": "string (ISO 639-1)",
  "seniority_level": "entry | mid | senior | lead | unknown | null",
  "date_published": "date | null",
  "normalized_at": "ISO 8601 timestamp",
  "enrichment_status": "pending | enriched | failed | skipped",
  "dedup_hash": "string (SHA-256 of canonical fields for deduplication)"
}
```

### Normalization Rules

- **HTML stripping:** All HTML tags are stripped from text fields. Only plain text is stored in `description_text`.
- **Encoding normalization:** All text is normalized to UTF-8 NFC. Special characters in Hebrew text must be preserved correctly.
- **Seniority inference:** If not explicitly stated, seniority is inferred from job title keywords (e.g., "Junior", "Lead", "Staff", "Principal", "Senior") using a configurable pattern library.
- **Country inference:** If not explicitly stated, country is inferred from location text using a location-to-country lookup table (city/region → country mapping).
- **Language detection:** If not provided by the source, language is detected using `langdetect` or `lingua` library. Hebrew detection must be reliable.
- **Deduplication hash:** Computed over `(source_name, external_id)` or over `(title, country_code, date_published)` if no external ID exists. Prevents the same job posting from being processed twice across source runs.

### Normalization Logging

At completion of each batch, log:
```
[normalization] pipeline_run_id=<uuid> source=<name> total=<N> normalized=<N> failed=<N> skipped=<N> duration_ms=<N>
```

---

## 5. Enrichment Step

**Input:** `normalized_records` with `enrichment_status = 'pending'`
**Output:** Junction table entries linking normalized records to taxonomy entities

### Purpose
Enrichment annotates normalized records with structured taxonomy entities. A normalized job posting, for example, transitions from having a `raw_skills_text` field to having a set of linked `Skill` entities from the canonical taxonomy.

### Enrichment Sub-Steps

#### 5.1 Skill Extraction and Matching

**Method:** Two-pass approach
1. **Pass 1 — Dictionary matching:** Run `raw_skills_text` and `description_text` against all known skill names and aliases. Exact and fuzzy matches (Levenshtein distance ≤ 2 for tokens of length ≥ 5) produce `skill_record_links`.
2. **Pass 2 — LLM extraction (agents domain):** For records where Pass 1 yields fewer than 3 skill matches, send `description_text` to the LLM skill extractor. LLM output is a list of skill names validated against the taxonomy.

**Output:** `normalized_record_skills` junction table with columns: `normalized_record_id`, `skill_id`, `match_method` (dictionary | llm), `confidence` (0.0–1.0)

#### 5.2 Topic Classification

**Method:** Embedding similarity against canonical topic embeddings
1. Embed `description_text` using `text-embedding-3-small`
2. Compute cosine similarity against pre-computed topic embeddings
3. Topics with similarity ≥ 0.75 are linked; top-5 by similarity per record maximum

**Output:** `normalized_record_topics` junction table: `normalized_record_id`, `topic_id`, `similarity_score`

#### 5.3 Role Matching

**Method:** Title-based matching
1. Normalize job title (lowercase, remove punctuation, expand abbreviations)
2. Match against canonical role names and aliases
3. If no direct match, use LLM to map to nearest canonical role

**Output:** `normalized_record_roles` junction table: `normalized_record_id`, `role_id`, `match_method`

#### 5.4 Industry Classification

**Method:** Company + description heuristics
1. Company name → industry lookup (cached lookup table from trusted source)
2. Description keywords → industry pattern matching
3. LLM fallback for ambiguous cases

**Output:** `normalized_record_industries` junction table

#### 5.5 Location Enrichment

**Method:** Hierarchical geo lookup
1. `location_raw` → `(country, region, city)` via geo lookup table
2. Attach `country_id` and `region_id` from taxonomy (countries/regions tables)

**Output:** `normalized_record_locations` junction table + updates to `normalized_records.country_code` if not already set

#### 5.6 Language Context

Already set during normalization (`language_code`). Enrichment step validates and optionally overrides if normalization detection was low-confidence. The final `language_code` drives downstream bilingual handling.

### Enrichment Logging

At completion:
```
[enrichment] pipeline_run_id=<uuid> total=<N> skills_linked=<N> topics_linked=<N> roles_linked=<N> llm_calls=<N> duration_ms=<N>
```

---

## 6. Signal Computation Step

**Input:** Enriched normalized records (via junction tables), taxonomy entities
**Output:** `signal_snapshots` rows

### Purpose
Signal computation aggregates enriched records into quantitative signals for each `(entity, entity_type, market_context, time_window)` combination. This is the step where individual records become aggregate intelligence.

### Signal Dimensions

For each combination of `(topic_or_skill_id, country_code, language_code, time_window_days)`:

| Signal Field | Computation | Notes |
|---|---|---|
| `posting_volume` | COUNT of job postings linked to this entity in this window | Raw volume |
| `posting_volume_30d_prior` | COUNT for the equivalent prior 30-day window | For velocity calculation |
| `trend_velocity` | `(current_volume - prior_volume) / prior_volume` | Percentage change; capped at ±200% |
| `search_interest_score` | Normalized (0–100) mean search interest from trend signals | 0 if no trend data |
| `search_interest_velocity` | 30-day change in `search_interest_score` | |
| `supply_coverage_score` | Fraction of demand covered by internal learning assets | 0.0 (no coverage) to 1.0 (full coverage) |
| `supply_gap_score` | `1.0 - supply_coverage_score` | Primary gap signal |
| `seniority_distribution` | JSONB histogram: `{entry: N, mid: N, senior: N, lead: N}` | Distribution of demand by seniority |
| `record_count` | Total enriched records contributing to this snapshot | Quality indicator |

### Time Windows

Signals are computed for multiple time windows per run. Default windows: 30d, 90d, 180d. Configurable via environment variable `SIGNAL_TIME_WINDOWS=30,90,180`.

### Snapshot Append Strategy

Signal snapshots are **append-only**. Each pipeline run generates new snapshot rows rather than updating existing ones. This preserves historical signal trajectories and allows the ranking step to compare current vs. prior snapshots.

The latest snapshot per `(entity_id, entity_type, market_context, time_window)` is identified by `computed_at` timestamp.

### Signal Logging

```
[signals] pipeline_run_id=<uuid> snapshots_created=<N> entities_covered=<N> time_windows=<list> duration_ms=<N>
```

---

## 7. Ranking Step

**Input:** Latest `signal_snapshots` per entity/market combination
**Output:** `score_breakdown` fields populated on signal snapshots; ranked order materialized

### Composite Score Formula

```
composite_score = (
    w_demand   * normalize(posting_volume)         +
    w_velocity * normalize(trend_velocity)          +
    w_gap      * supply_gap_score                   +
    w_search   * normalize(search_interest_score)
) * confidence_multiplier
```

**Default weights (v1):**

| Weight | Default Value | Environment Variable |
|---|---|---|
| `w_demand` | 0.35 | `RANK_WEIGHT_DEMAND` |
| `w_velocity` | 0.25 | `RANK_WEIGHT_VELOCITY` |
| `w_gap` | 0.30 | `RANK_WEIGHT_GAP` |
| `w_search` | 0.10 | `RANK_WEIGHT_SEARCH` |

**Normalization:** Each raw signal dimension is normalized to [0, 1] using min-max normalization within the current snapshot cohort. This makes scores relative to the current distribution, not absolute values.

**Confidence Multiplier:**
```
confidence_multiplier = min(1.0, record_count / CONFIDENCE_RECORD_THRESHOLD)
```
Default `CONFIDENCE_RECORD_THRESHOLD = 50`. A snapshot with fewer than 50 contributing records is penalized proportionally.

### Score Breakdown Storage

The composite score and all component scores are stored on the `signal_snapshot` row. This enables analysts to understand why a particular opportunity scored highly.

---

## 8. Opportunity Generation Step

**Input:** Ranked `signal_snapshots` above configurable thresholds
**Output:** `opportunity_briefs`, `opportunity_evidence_items`

### Generation Trigger Conditions

A signal snapshot triggers opportunity generation when ALL of:
- `composite_score >= OPPORTUNITY_SCORE_THRESHOLD` (default: 0.55)
- `record_count >= OPPORTUNITY_MIN_RECORDS` (default: 20)
- `supply_gap_score >= OPPORTUNITY_MIN_GAP` (default: 0.30)

### Deduplication

Before generating a new brief, the system checks for an existing non-rejected, non-archived brief for the same `(topic_or_skill_id, country_code, language_code, time_window)`. If one exists:
- If the existing brief is in `draft` or `surfaced` state: update its score fields and refresh evidence items. Do not create a duplicate.
- If the existing brief is in `approved` state: create a new `draft` brief that can be reviewed independently. The approved brief is not modified.

### Brief Generation Process

1. **Collect evidence items:** Query all normalized records that contributed to the snapshot. Select the top-N (default 10) most representative records as evidence items.
2. **Generate text content:** Call the `agents` domain to generate: `title` (EN + HE), `summary` (EN + HE), `why_now` text (EN + HE). LLM output is validated against a schema before storage.
3. **Populate metrics:** Attach all score fields, confidence, record count, seniority distribution, time window.
4. **Set initial state:** New briefs are created in `draft` state. The governance domain runs quality checks; if passed, state transitions to `surfaced`.

### Evidence Item Types

| Evidence Type | Source | Example |
|---|---|---|
| `job_posting` | Normalized job record | "Senior Python Engineer at Wix, Tel Aviv" |
| `trend_signal` | Trend snapshot record | "Python search interest +34% in IL (90d)" |
| `supply_gap` | Internal supply record | "0 existing Cognet courses cover this topic" |
| `skill_cluster` | Signal aggregation | "Skill appears in 847 postings this month" |

### Opportunity Generation Logging

```
[opportunities] pipeline_run_id=<uuid> candidates=<N> new_briefs=<N> updated_briefs=<N> skipped_duplicates=<N> llm_calls=<N> duration_ms=<N>
```

---

## 9. Pipeline Run Tracking

Every execution of the full pipeline (or any individual stage) is associated with a `pipeline_run` record.

### Pipeline Run Lifecycle

```
pending → running → completed
                 → failed
                 → partially_failed
```

### Pipeline Run Record

```json
{
  "id": "uuid",
  "triggered_by": "schedule | manual | api",
  "triggered_at": "ISO 8601 timestamp",
  "started_at": "ISO 8601 timestamp | null",
  "completed_at": "ISO 8601 timestamp | null",
  "status": "pending | running | completed | failed | partially_failed",
  "stages": {
    "ingestion": {"status": "...", "records_in": N, "records_out": N, "errors": N, "duration_ms": N},
    "normalization": {"status": "...", "records_in": N, "records_out": N, "errors": N, "duration_ms": N},
    "enrichment": {"status": "...", "records_in": N, "records_out": N, "errors": N, "duration_ms": N},
    "signals": {"status": "...", "snapshots_created": N, "duration_ms": N},
    "ranking": {"status": "...", "snapshots_ranked": N, "duration_ms": N},
    "opportunities": {"status": "...", "briefs_created": N, "briefs_updated": N, "duration_ms": N}
  },
  "error_summary": "string | null",
  "config_snapshot": "jsonb (weights, thresholds, time windows used)"
}
```

---

## 10. Failure Recovery Points

Each stage is independently resumable. The pipeline supports partial re-runs from any stage.

| Stage Failure | Recovery Strategy | Data State |
|---|---|---|
| Ingestion fails mid-fetch | Mark `source_run` as `failed`; already-landed records persist; next run creates new `source_run` | No data loss; partial run is discarded |
| Normalization fails on record | Record marked `normalization_status = 'failed'`; error stored; other records proceed | Non-blocking; failed records are retried in next run |
| Enrichment fails on record | Record marked `enrichment_status = 'failed'`; error stored; other records proceed | Non-blocking |
| LLM call fails during enrichment | Exponential backoff (3 retries); if all fail, record is enriched with dictionary-only results and flagged as `llm_enrichment_failed` | Degraded enrichment rather than failure |
| Signal computation fails | Entire signal stage marked failed; previous snapshots are unaffected; ranking uses previous cycle's snapshots | No opportunity generation this cycle |
| Opportunity generation fails on one brief | Brief creation error is logged; other briefs proceed; partial success tracked in pipeline run | Non-blocking |

---

## 11. Idempotency and Retry Logic

### Idempotency Rules

- **Ingestion:** Each raw record has a `dedup_hash` derived from `(source_name, external_id)`. Re-ingestion of the same external record produces a new raw record row with a new `source_run_id` but normalization will detect the duplicate via hash comparison and skip it.
- **Normalization:** Each normalized record's existence is checked via `dedup_hash` before insertion. Duplicate hashes are skipped (existing normalized record is reused).
- **Enrichment:** Enrichment is idempotent per `(normalized_record_id, pipeline_run_id)`. Re-running enrichment for the same pipeline run on already-enriched records is a no-op.
- **Signal computation:** Snapshots are keyed by `(entity_id, entity_type, market_context, time_window, pipeline_run_id)`. Re-running signal computation for the same pipeline run is idempotent.
- **Opportunity generation:** The deduplication check (described in section 8) prevents duplicate brief creation.

### Retry Logic

All Celery tasks are configured with:
```python
autoretry_for = (Exception,)
retry_backoff = True          # Exponential backoff
retry_backoff_max = 300       # Cap at 5 minutes
max_retries = 3
```

LLM calls (agents domain) have separate retry logic:
```python
autoretry_for = (RateLimitError, APITimeoutError)
retry_backoff = True
retry_backoff_max = 60
max_retries = 5
```

Non-retryable errors (validation failures, schema mismatches) are logged immediately and not retried.

---

## 12. Logging Hooks at Each Stage

Every stage emits structured log records at three points: start, completion, and error.

### Log Format (JSON)

```json
{
  "timestamp": "ISO 8601",
  "level": "INFO | WARNING | ERROR",
  "domain": "ingestion | normalization | enrichment | signals | ranking | opportunities",
  "event": "stage_start | stage_complete | record_error | llm_call | llm_error",
  "pipeline_run_id": "uuid | null",
  "source_run_id": "uuid | null",
  "record_id": "uuid | null",
  "message": "string",
  "metadata": {
    "duration_ms": "int | null",
    "records_processed": "int | null",
    "error_type": "string | null",
    "error_detail": "string | null"
  }
}
```

### Stage-Level Log Events

| Stage | Start Event | Complete Event | Error Event |
|---|---|---|---|
| Ingestion | `ingestion.source_run.started` | `ingestion.source_run.completed` | `ingestion.source_run.failed` |
| Normalization | `normalization.batch.started` | `normalization.batch.completed` | `normalization.record.failed` |
| Enrichment | `enrichment.batch.started` | `enrichment.batch.completed` | `enrichment.record.failed` |
| Signals | `signals.computation.started` | `signals.computation.completed` | `signals.computation.failed` |
| Ranking | `ranking.started` | `ranking.completed` | `ranking.failed` |
| Opportunities | `opportunities.generation.started` | `opportunities.generation.completed` | `opportunities.brief.failed` |

All log records are written to stdout in JSON format. In production, they are collected by a log aggregator (e.g., Datadog, Loki) for search and alerting.
