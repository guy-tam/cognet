# COGNET LDI Engine — Domain Model

**Version:** 1.0
**Status:** Active
**Last Updated:** 2026-03-26
**Owner:** Engineering

---

## 1. Overview

This document defines all persistent entities in the LDI Engine, their fields, relationships, and the design decisions behind them. All entities are backed by PostgreSQL tables managed via SQLAlchemy 2.x models and Alembic migrations.

### Naming Conventions

- Table names are `snake_case` plurals
- Primary keys are UUIDs (`uuid` type, server-default `gen_random_uuid()`)
- Timestamps are `timestamptz` (timestamp with time zone), stored in UTC
- Soft deletes are implemented via `archived_at` timestamp (not a boolean `is_deleted` flag)
- JSONB is used for flexible/evolving fields that do not need indexing at the column level
- All foreign keys have explicit names following the pattern `fk_{table}_{column}`

---

## 2. Entity Families

### Family A: Pipeline Infrastructure
`source_runs`, `raw_source_records`, `pipeline_runs`

### Family B: Normalization
`normalized_records`

### Family C: Taxonomy — Canonical Entities
`skills`, `topics`, `roles`, `industries`, `countries`, `regions`, `languages`

### Family D: Taxonomy — Aliases
`skill_aliases`, `topic_aliases`, `role_aliases`

### Family E: Junction / Enrichment Links
`normalized_record_skills`, `normalized_record_topics`, `normalized_record_roles`, `normalized_record_industries`, `normalized_record_locations`

### Family F: Internal Supply
`internal_learning_assets`, `asset_topics`, `asset_skills`

### Family G: Signals and Ranking
`signal_snapshots`

### Family H: Opportunities
`opportunity_briefs`, `opportunity_evidence_items`

### Family I: Governance
`review_decisions`, `pipeline_run_stage_logs`

---

## 3. Family A: Pipeline Infrastructure

### 3.1 `source_runs`

Tracks each execution of a specific source connector (one row per source per pipeline run).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `pipeline_run_id` | uuid | FK → `pipeline_runs.id`, NOT NULL | Parent pipeline run |
| `source_name` | varchar(100) | NOT NULL | Identifier for the source (e.g., `adzuna_il`, `google_trends`) |
| `source_type` | varchar(50) | NOT NULL | Enum: `job_posting`, `trend_signal`, `internal_supply` |
| `status` | varchar(30) | NOT NULL, DEFAULT `pending` | Enum: `pending`, `running`, `completed`, `failed` |
| `started_at` | timestamptz | | |
| `completed_at` | timestamptz | | |
| `records_fetched` | int | DEFAULT 0 | Raw records returned by the source |
| `records_landed` | int | DEFAULT 0 | Records successfully written to `raw_source_records` |
| `fetch_window_start` | timestamptz | | Start of the time window fetched |
| `fetch_window_end` | timestamptz | | End of the time window fetched |
| `error_message` | text | | Populated if `status = 'failed'` |
| `metadata` | jsonb | | Source-specific metadata (e.g., API pagination state) |
| `created_at` | timestamptz | NOT NULL, DEFAULT now() | |

**Indexes:** `(pipeline_run_id)`, `(source_name, status)`, `(started_at DESC)`

---

### 3.2 `raw_source_records`

Append-only landing table for all ingested raw data. Records are never modified after insertion.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `source_run_id` | uuid | FK → `source_runs.id`, NOT NULL | |
| `source_type` | varchar(50) | NOT NULL | Mirrors `source_runs.source_type` (denormalized for query convenience) |
| `source_name` | varchar(100) | NOT NULL | Mirrors `source_runs.source_name` |
| `external_id` | varchar(500) | | Source system's own ID for this record |
| `fetched_at` | timestamptz | NOT NULL | When the record was fetched |
| `raw_payload` | jsonb | NOT NULL | Original response payload, fully preserved |
| `detected_language` | varchar(10) | | ISO 639-1 (e.g., `en`, `he`) |
| `detected_country` | varchar(10) | | ISO 3166-1 alpha-2 (e.g., `IL`, `US`) |
| `dedup_hash` | varchar(64) | | SHA-256 of canonical dedup fields |
| `normalization_status` | varchar(30) | NOT NULL, DEFAULT `pending` | Enum: `pending`, `normalized`, `failed`, `skipped` |
| `normalization_error` | text | | Error detail if `normalization_status = 'failed'` |
| `created_at` | timestamptz | NOT NULL, DEFAULT now() | |

**Indexes:** `(source_run_id)`, `(dedup_hash)` (UNIQUE conditional on non-null), `(normalization_status)`, `(source_name, fetched_at DESC)`

**Partitioning consideration:** Partition by `fetched_at` monthly once volume exceeds ~5M rows.

---

### 3.3 `pipeline_runs`

Top-level tracking entity for each full pipeline execution.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `triggered_by` | varchar(50) | NOT NULL | Enum: `schedule`, `manual`, `api` |
| `triggered_at` | timestamptz | NOT NULL | When trigger was received |
| `started_at` | timestamptz | | When execution began |
| `completed_at` | timestamptz | | When execution finished |
| `status` | varchar(30) | NOT NULL, DEFAULT `pending` | Enum: `pending`, `running`, `completed`, `failed`, `partially_failed` |
| `stages_summary` | jsonb | | Per-stage status snapshot (see data-flow.md section 9) |
| `config_snapshot` | jsonb | | Copy of active config at run time (weights, thresholds) |
| `error_summary` | text | | Human-readable failure summary |
| `created_at` | timestamptz | NOT NULL, DEFAULT now() | |

**Indexes:** `(status)`, `(triggered_at DESC)`, `(started_at DESC)`

---

## 4. Family B: Normalization

### 4.1 `normalized_records`

Universal intermediate schema. One row per raw source record (1:1 mapping after successful normalization).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `raw_record_id` | uuid | FK → `raw_source_records.id`, NOT NULL, UNIQUE | |
| `pipeline_run_id` | uuid | FK → `pipeline_runs.id`, NOT NULL | |
| `source_type` | varchar(50) | NOT NULL | |
| `source_name` | varchar(100) | NOT NULL | |
| `title` | varchar(500) | NOT NULL | Job title, trend topic, or asset title |
| `description_text` | text | | Cleaned plain text description |
| `raw_skills_text` | text | | Extracted raw skill mentions (pre-enrichment) |
| `location_raw` | varchar(300) | | As-written location string |
| `country_code` | varchar(10) | FK → `countries.code` | |
| `region_raw` | varchar(200) | | As-written region/state |
| `language_code` | varchar(10) | NOT NULL | ISO 639-1 |
| `seniority_level` | varchar(30) | | Enum: `entry`, `mid`, `senior`, `lead`, `unknown` |
| `date_published` | date | | Publication or posting date |
| `dedup_hash` | varchar(64) | | SHA-256 for cross-run deduplication |
| `enrichment_status` | varchar(30) | NOT NULL, DEFAULT `pending` | Enum: `pending`, `enriched`, `failed`, `skipped` |
| `enrichment_error` | text | | |
| `normalized_at` | timestamptz | NOT NULL | |

**Indexes:** `(raw_record_id)`, `(pipeline_run_id)`, `(dedup_hash)`, `(enrichment_status)`, `(country_code, language_code)`, `(source_type, date_published DESC)`

---

## 5. Family C: Taxonomy — Canonical Entities

All taxonomy entities follow a common base pattern:
- `id` (uuid PK)
- `slug` (varchar UNIQUE NOT NULL, immutable) — machine-readable identifier
- `name_en` (varchar NOT NULL) — English canonical name
- `name_he` (varchar) — Hebrew translation
- `created_at`, `updated_at` timestamps
- `archived_at` (timestamptz, nullable) — soft delete

---

### 5.1 `skills`

Canonical skill entities. Skills are atomic, specific capabilities.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `slug` | varchar(200) | UNIQUE NOT NULL | e.g., `python-programming`, `react-hooks` |
| `name_en` | varchar(300) | NOT NULL | e.g., "Python Programming" |
| `name_he` | varchar(300) | | Hebrew name |
| `description_en` | text | | |
| `description_he` | text | | |
| `skill_type` | varchar(50) | | Enum: `technical`, `soft`, `domain`, `tool`, `framework`, `language` |
| `parent_skill_id` | uuid | FK → `skills.id`, self-ref | For skill hierarchies (e.g., "React" is child of "JavaScript") |
| `external_ids` | jsonb | | Mappings to ESCO, O*NET, etc.: `{"esco": "...", "onet": "..."}` |
| `created_at` | timestamptz | NOT NULL | |
| `updated_at` | timestamptz | NOT NULL | |
| `archived_at` | timestamptz | | |

**Indexes:** `(slug)` UNIQUE, `(parent_skill_id)`, `(skill_type)`, GIN index on `external_ids`

---

### 5.2 `topics`

Broader learning domains. Topics contain multiple skills and map to course/content categories.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `slug` | varchar(200) | UNIQUE NOT NULL | e.g., `machine-learning`, `cloud-infrastructure` |
| `name_en` | varchar(300) | NOT NULL | |
| `name_he` | varchar(300) | | |
| `description_en` | text | | |
| `description_he` | text | | |
| `parent_topic_id` | uuid | FK → `topics.id`, self-ref | Topic hierarchy |
| `embedding_vector` | vector(1536) | | Pre-computed embedding for similarity matching (pgvector) |
| `created_at` | timestamptz | NOT NULL | |
| `updated_at` | timestamptz | NOT NULL | |
| `archived_at` | timestamptz | | |

**Note on `embedding_vector`:** Requires `pgvector` PostgreSQL extension. If not available, embeddings are stored as JSONB float arrays as a fallback.

---

### 5.3 `roles`

Canonical job roles and professional titles.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `slug` | varchar(200) | UNIQUE NOT NULL | e.g., `backend-software-engineer`, `data-scientist` |
| `name_en` | varchar(300) | NOT NULL | |
| `name_he` | varchar(300) | | |
| `seniority_levels` | varchar[] | | Array of applicable seniority levels |
| `typical_skills` | uuid[] | | Array of `skill_ids` typically associated (informational) |
| `created_at` | timestamptz | NOT NULL | |
| `updated_at` | timestamptz | NOT NULL | |
| `archived_at` | timestamptz | | |

---

### 5.4 `industries`

Industry/sector classification.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `slug` | varchar(200) | UNIQUE NOT NULL | e.g., `fintech`, `healthcare-it`, `cybersecurity` |
| `name_en` | varchar(300) | NOT NULL | |
| `name_he` | varchar(300) | | |
| `parent_industry_id` | uuid | FK → `industries.id` | |
| `created_at` | timestamptz | NOT NULL | |
| `updated_at` | timestamptz | NOT NULL | |
| `archived_at` | timestamptz | | |

---

### 5.5 `countries`

ISO 3166-1 country entities.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `code` | varchar(10) | UNIQUE NOT NULL | ISO 3166-1 alpha-2 (e.g., `IL`, `US`) |
| `name_en` | varchar(200) | NOT NULL | |
| `name_he` | varchar(200) | | |
| `is_primary_market` | boolean | NOT NULL, DEFAULT false | Flag for markets with dedicated signal tracking |
| `default_language_code` | varchar(10) | | |
| `created_at` | timestamptz | NOT NULL | |

---

### 5.6 `regions`

Sub-national regions (states, provinces, districts).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `country_code` | varchar(10) | FK → `countries.code`, NOT NULL | |
| `slug` | varchar(200) | NOT NULL | e.g., `tel-aviv-district`, `california` |
| `name_en` | varchar(200) | NOT NULL | |
| `name_he` | varchar(200) | | |
| `created_at` | timestamptz | NOT NULL | |

**Indexes:** `(country_code)`, `(slug, country_code)` UNIQUE

---

### 5.7 `languages`

Languages relevant to content and signal processing.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `code` | varchar(10) | UNIQUE NOT NULL | ISO 639-1 (e.g., `en`, `he`) |
| `name_en` | varchar(100) | NOT NULL | |
| `name_native` | varchar(100) | | Name in the language itself |
| `is_rtl` | boolean | NOT NULL, DEFAULT false | Right-to-left layout flag |
| `is_active` | boolean | NOT NULL, DEFAULT true | Whether LDI Engine processes this language |

---

## 6. Family D: Taxonomy Aliases

Aliases enable flexible matching against taxonomy entities without polluting the canonical namespace.

### 6.1 `skill_aliases`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `skill_id` | uuid | FK → `skills.id`, NOT NULL | |
| `alias` | varchar(500) | NOT NULL | The alternative name or abbreviation |
| `language_code` | varchar(10) | NOT NULL, DEFAULT `en` | Language of the alias |
| `alias_type` | varchar(50) | | Enum: `abbreviation`, `alternate_spelling`, `colloquial`, `translation` |
| `created_at` | timestamptz | NOT NULL | |

**Indexes:** `(skill_id)`, `(alias)` — consider trigram index (pg_trgm) for fuzzy search

### 6.2 `topic_aliases`

Same structure as `skill_aliases`, referencing `topics.id`.

### 6.3 `role_aliases`

Same structure as `skill_aliases`, referencing `roles.id`.

---

## 7. Family E: Junction / Enrichment Links

These tables are written during the enrichment stage and record which taxonomy entities were linked to each normalized record.

### 7.1 `normalized_record_skills`

| Column | Type | Constraints |
|---|---|---|
| `id` | uuid | PK |
| `normalized_record_id` | uuid | FK → `normalized_records.id`, NOT NULL |
| `skill_id` | uuid | FK → `skills.id`, NOT NULL |
| `pipeline_run_id` | uuid | FK → `pipeline_runs.id`, NOT NULL |
| `match_method` | varchar(50) | `dictionary`, `fuzzy`, `llm`, `embedding` |
| `confidence` | numeric(4,3) | 0.000–1.000 |
| `created_at` | timestamptz | NOT NULL |

**Indexes:** `(normalized_record_id)`, `(skill_id, pipeline_run_id)`, `(pipeline_run_id)`

`normalized_record_topics`, `normalized_record_roles`, `normalized_record_industries` follow the same structure with their respective FK targets.

### 7.2 `normalized_record_locations`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `normalized_record_id` | uuid | FK → `normalized_records.id`, NOT NULL | |
| `country_code` | varchar(10) | FK → `countries.code` | |
| `region_id` | uuid | FK → `regions.id` | |
| `pipeline_run_id` | uuid | FK → `pipeline_runs.id`, NOT NULL | |
| `location_confidence` | numeric(4,3) | | Confidence in location resolution |
| `created_at` | timestamptz | NOT NULL | |

---

## 8. Family F: Internal Learning Supply

### 8.1 `internal_learning_assets`

Catalog of Cognet's existing learning content. Ingested from the internal CMS/LMS.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `external_asset_id` | varchar(300) | UNIQUE NOT NULL | CMS/LMS system ID |
| `title` | varchar(500) | NOT NULL | |
| `asset_type` | varchar(100) | | Enum: `course`, `module`, `assessment`, `learning_path`, `article` |
| `language_code` | varchar(10) | NOT NULL | Primary language of content |
| `status` | varchar(50) | | Enum: `published`, `draft`, `archived`, `deprecated` |
| `quality_score` | numeric(4,3) | | Internal quality rating (0–1) |
| `last_updated_date` | date | | When content was last substantively updated |
| `enrollment_count` | int | | Historical enrollment total (if available) |
| `completion_rate` | numeric(4,3) | | Fraction of enrollees who completed (if available) |
| `metadata` | jsonb | | Flexible storage for CMS-specific fields |
| `ingested_at` | timestamptz | NOT NULL | |
| `updated_at` | timestamptz | NOT NULL | |

### 8.2 `asset_topics` and `asset_skills`

Junction tables linking assets to taxonomy:

`asset_topics`: `(asset_id, topic_id, coverage_level)` — `coverage_level` enum: `primary`, `secondary`, `incidental`

`asset_skills`: `(asset_id, skill_id, coverage_level)`

---

## 9. Family G: Signals and Ranking

### 9.1 `signal_snapshots`

Central output of signal computation. Append-only: one row per `(entity, market, time_window, pipeline_run_id)`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `pipeline_run_id` | uuid | FK → `pipeline_runs.id`, NOT NULL | |
| `entity_id` | uuid | NOT NULL | FK to `skills.id` or `topics.id` depending on entity_type |
| `entity_type` | varchar(50) | NOT NULL | Enum: `skill`, `topic` |
| `country_code` | varchar(10) | FK → `countries.code` | NULL means global |
| `language_code` | varchar(10) | NOT NULL | |
| `time_window_days` | int | NOT NULL | e.g., 30, 90, 180 |
| `computed_at` | timestamptz | NOT NULL | |
| `window_start` | date | NOT NULL | Start of the signal window |
| `window_end` | date | NOT NULL | End of the signal window |
| `posting_volume` | int | NOT NULL, DEFAULT 0 | Job postings in window |
| `posting_volume_prior` | int | DEFAULT 0 | Postings in equivalent prior window |
| `trend_velocity` | numeric(6,4) | | Percentage change in posting volume |
| `search_interest_score` | numeric(5,2) | | Normalized 0–100 |
| `search_interest_velocity` | numeric(6,4) | | 30-day change in search interest |
| `supply_coverage_score` | numeric(4,3) | NOT NULL, DEFAULT 0 | 0–1, fraction of demand with internal supply |
| `supply_gap_score` | numeric(4,3) | NOT NULL, DEFAULT 1 | 1 - supply_coverage_score |
| `seniority_distribution` | jsonb | | `{"entry": N, "mid": N, "senior": N, "lead": N, "unknown": N}` |
| `record_count` | int | NOT NULL, DEFAULT 0 | Contributing normalized records |
| `composite_score` | numeric(5,4) | | Final weighted score (0–1) |
| `score_demand` | numeric(5,4) | | Demand component score |
| `score_velocity` | numeric(5,4) | | Velocity component score |
| `score_gap` | numeric(5,4) | | Gap component score |
| `score_search` | numeric(5,4) | | Search component score |
| `confidence` | numeric(4,3) | | Based on record_count / threshold |
| `rank_within_window` | int | | Rank among all snapshots in this pipeline run + time window |

**Indexes:** `(pipeline_run_id)`, `(entity_id, entity_type)`, `(country_code, language_code)`, `(composite_score DESC)`, `(computed_at DESC)`, composite `(entity_id, entity_type, country_code, language_code, time_window_days, pipeline_run_id)` UNIQUE

---

## 10. Family H: Opportunities

### 10.1 `opportunity_briefs`

The primary output of the LDI Engine. Human-reviewable opportunity records.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `signal_snapshot_id` | uuid | FK → `signal_snapshots.id`, NOT NULL | Source snapshot |
| `pipeline_run_id` | uuid | FK → `pipeline_runs.id`, NOT NULL | |
| `entity_id` | uuid | NOT NULL | Denormalized from snapshot |
| `entity_type` | varchar(50) | NOT NULL | |
| `country_code` | varchar(10) | | |
| `language_code` | varchar(10) | NOT NULL | |
| `time_window_days` | int | NOT NULL | |
| `title_en` | varchar(500) | NOT NULL | |
| `title_he` | varchar(500) | | |
| `summary_en` | text | NOT NULL | |
| `summary_he` | text | | |
| `why_now_en` | text | | LLM-generated urgency rationale |
| `why_now_he` | text | | |
| `composite_score` | numeric(5,4) | NOT NULL | Copied from snapshot at generation time |
| `confidence` | numeric(4,3) | NOT NULL | |
| `record_count` | int | NOT NULL | |
| `seniority_focus` | varchar(50) | | Dominant seniority level for this opportunity |
| `status` | varchar(30) | NOT NULL, DEFAULT `draft` | Enum: `draft`, `surfaced`, `analyst_review`, `approved`, `rejected`, `archived` |
| `status_changed_at` | timestamptz | NOT NULL | When status last changed |
| `dedup_key` | varchar(500) | | Deduplication key: hash of `(entity_id, entity_type, country_code, language_code, time_window_days)` |
| `generation_method` | varchar(50) | | Enum: `auto`, `manual_request` |
| `llm_generation_log_id` | uuid | | Reference to LLM call log for this brief's text generation |
| `created_at` | timestamptz | NOT NULL | |
| `updated_at` | timestamptz | NOT NULL | |
| `archived_at` | timestamptz | | |

**Indexes:** `(status)`, `(composite_score DESC)`, `(country_code, language_code)`, `(entity_id, entity_type)`, `(dedup_key)`, `(pipeline_run_id)`, `(status_changed_at DESC)`

---

### 10.2 `opportunity_evidence_items`

Each opportunity brief is backed by a set of evidence items that justify the claim.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `opportunity_brief_id` | uuid | FK → `opportunity_briefs.id`, NOT NULL | |
| `evidence_type` | varchar(50) | NOT NULL | Enum: `job_posting`, `trend_signal`, `supply_gap`, `skill_cluster` |
| `normalized_record_id` | uuid | FK → `normalized_records.id` | Source record (if record-level evidence) |
| `signal_snapshot_id` | uuid | FK → `signal_snapshots.id` | Source snapshot (if aggregate evidence) |
| `label_en` | varchar(500) | NOT NULL | Human-readable label |
| `label_he` | varchar(500) | | |
| `value` | numeric(10,4) | | Numeric value if quantitative evidence |
| `value_unit` | varchar(100) | | e.g., "job_postings_per_month", "percent_change" |
| `display_date` | date | | Date context for the evidence item |
| `metadata` | jsonb | | Additional structured evidence fields |
| `sort_order` | int | NOT NULL, DEFAULT 0 | Display order within the brief |
| `created_at` | timestamptz | NOT NULL | |

**Indexes:** `(opportunity_brief_id, sort_order)`

---

## 11. Family I: Governance

### 11.1 `review_decisions`

Append-only log of all analyst review decisions. State transitions are never in-place.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `opportunity_brief_id` | uuid | FK → `opportunity_briefs.id`, NOT NULL | |
| `from_status` | varchar(30) | NOT NULL | Prior status |
| `to_status` | varchar(30) | NOT NULL | New status |
| `decision_type` | varchar(50) | NOT NULL | Enum: `approve`, `reject`, `request_revision`, `archive`, `reopen`, `surface` |
| `reviewer_id` | varchar(200) | NOT NULL | Reviewer identifier (user ID or email) |
| `reviewer_name` | varchar(300) | | Human-readable name |
| `notes` | text | | Mandatory for `reject` decisions |
| `rejection_reason_code` | varchar(100) | | Enum: `low_quality`, `irrelevant`, `duplicate`, `too_niche`, `out_of_scope`, `other` |
| `decided_at` | timestamptz | NOT NULL | |
| `created_at` | timestamptz | NOT NULL | |

**Indexes:** `(opportunity_brief_id)`, `(reviewer_id)`, `(decided_at DESC)`, `(to_status)`

---

### 11.2 `pipeline_run_stage_logs`

Granular per-stage execution log, one row per stage per pipeline run.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | uuid | PK | |
| `pipeline_run_id` | uuid | FK → `pipeline_runs.id`, NOT NULL | |
| `stage` | varchar(100) | NOT NULL | e.g., `ingestion`, `normalization`, `enrichment`, `signals`, `ranking`, `opportunities` |
| `status` | varchar(30) | NOT NULL | Enum: `pending`, `running`, `completed`, `failed`, `skipped` |
| `started_at` | timestamptz | | |
| `completed_at` | timestamptz | | |
| `duration_ms` | int | | |
| `records_in` | int | | |
| `records_out` | int | | |
| `errors_count` | int | DEFAULT 0 | |
| `warnings_count` | int | DEFAULT 0 | |
| `details` | jsonb | | Stage-specific metrics and metadata |
| `error_message` | text | | |
| `created_at` | timestamptz | NOT NULL | |

---

## 12. Key Relationships

```
pipeline_runs
    └── source_runs (many)
    └── pipeline_run_stage_logs (many)

source_runs
    └── raw_source_records (many)

raw_source_records
    └── normalized_records (1:1, after normalization)

normalized_records
    └── normalized_record_skills (many)
    └── normalized_record_topics (many)
    └── normalized_record_roles (many)
    └── normalized_record_industries (many)
    └── normalized_record_locations (many)

skills ←→ skill_aliases (many)
topics ←→ topic_aliases (many)
roles  ←→ role_aliases  (many)
topics ←self-ref hierarchy→ topics
skills ←self-ref hierarchy→ skills
countries → regions (many)

normalized_record_skills → skills
normalized_record_topics → topics

internal_learning_assets
    └── asset_topics (many)
    └── asset_skills (many)

pipeline_runs → signal_snapshots (many)
signal_snapshots [entity_id → skills or topics]
signal_snapshots → opportunity_briefs (1:many, via dedup)
opportunity_briefs → opportunity_evidence_items (many)
opportunity_briefs → review_decisions (many, append-only)
```

---

## 13. Taxonomy Canonical Model Approach

The taxonomy is the shared vocabulary of the entire system. Its integrity directly determines signal quality and ranking coherence.

### Design Decisions

**Slugs are immutable.** Once a slug is assigned to a skill, topic, or role, it never changes. Display names (`name_en`, `name_he`) can be updated; slugs cannot. This ensures that any external system referencing a taxonomy entity by slug will never experience a broken reference.

**Aliases are the flexibility layer.** When a job posting mentions "K8s", the enrichment system matches it to the `kubernetes` skill entity via the `k8s` alias. The canonical entity is untouched.

**Hierarchies are optional.** Not every skill or topic needs a parent. Hierarchies are informational and are used for grouping in the Admin UI and for roll-up signal computation. They are not required for the core pipeline.

**External IDs are stored but not authoritative.** Mappings to ESCO, O*NET, or other external taxonomies are stored in `external_ids` JSONB. They assist in enrichment but the LDI Engine's own slug is always the primary identifier.

---

## 14. Deduplication Approach Per Entity Type

| Entity | Dedup Key | Strategy |
|---|---|---|
| `raw_source_records` | `(source_name, external_id)` or `SHA256(title + country + date)` | Hash stored in `dedup_hash`; unique constraint with conditional index |
| `normalized_records` | Same `dedup_hash` from raw record | Check before insert; skip if exists |
| `skills` | `slug` | Unique constraint on `slug` |
| `topics` | `slug` | Unique constraint on `slug` |
| `skill_aliases` | `(skill_id, alias, language_code)` | Composite unique constraint |
| `signal_snapshots` | `(entity_id, entity_type, country_code, language_code, time_window_days, pipeline_run_id)` | Composite unique constraint |
| `opportunity_briefs` | `dedup_key` = SHA256 of `(entity_id, entity_type, country_code, language_code, time_window_days)` | Checked before creation; update vs. create decision (see data-flow.md section 8) |
| `internal_learning_assets` | `external_asset_id` | Unique constraint |
