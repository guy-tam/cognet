# COGNET LDI Engine — Technical Architecture

**Version:** 1.0
**Status:** Active
**Last Updated:** 2026-03-26
**Owner:** Engineering

---

## 1. System Overview

The LDI Engine is implemented as a **modular monolith** — a single deployable backend application with strong internal domain boundaries enforced by module structure and explicit interface contracts.

This is a deliberate architectural choice, not a limitation. Microservices would introduce distributed systems complexity (network partitions, distributed transactions, service discovery, inter-service auth) that is not justified at the current scale and team size. A well-structured monolith with domain-oriented modules is faster to develop, easier to test, simpler to operate, and can be decomposed into independent services later if scale demands it.

### Architectural Constraints

- **No shared database access across domains.** Each domain owns its tables. Cross-domain access happens through Python interfaces, not raw SQL queries across module boundaries.
- **No circular imports.** Domain dependency graph is a DAG. If circular dependency emerges, it indicates a missing abstraction.
- **LLM calls are isolated.** All calls to language models are confined to the `agents` domain. No LLM invocations in deterministic pipeline stages.
- **All external I/O is isolated.** HTTP calls to external data sources, job board APIs, and trend APIs are confined to the `ingestion` domain.
- **Schema migrations are centralized.** Alembic manages all migrations in a single migrations directory, even though tables belong to different domains.

---

## 2. Core Domains

The system is decomposed into the following named domains. Each domain maps to a Python package under `backend/src/cognet/`.

### 2.1 `ingestion`
**Responsibility:** Connect to external data sources, fetch raw data, and land it in the raw storage layer.
**Inputs:** External APIs, file drops, webhook endpoints
**Outputs:** `raw_source_records` table rows, `source_runs` table rows
**Key Rules:**
- Must be idempotent: re-running an ingestion for the same time window should not create duplicates
- Must not perform normalization or enrichment — only fetch and store
- Source credentials are injected via environment variables, never hardcoded

### 2.2 `normalization`
**Responsibility:** Transform raw source records into a consistent internal schema.
**Inputs:** `raw_source_records`
**Outputs:** `normalized_records`
**Key Rules:**
- One normalized record per raw record (1:1 mapping)
- Normalization is source-specific but output schema is universal
- Must preserve the original raw record ID as a foreign key

### 2.3 `enrichment`
**Responsibility:** Attach structured taxonomy entities to normalized records (skills, topics, roles, industries, geo, language).
**Inputs:** `normalized_records`
**Outputs:** Junction tables linking normalized records to taxonomy entities
**Key Rules:**
- Enrichment is additive — does not modify normalized records
- Can use deterministic matching (exact/fuzzy) or LLM-assisted extraction via the `agents` domain
- Must be re-runnable; enrichment results are versioned per pipeline run

### 2.4 `taxonomy`
**Responsibility:** Own and manage the canonical entity library: skills, topics, roles, industries, countries, regions, languages, and their aliases.
**Inputs:** Admin UI operations, bulk import, agent-assisted creation
**Outputs:** Taxonomy entity tables
**Key Rules:**
- Every entity has a canonical slug (immutable once created)
- Aliases allow flexible matching without polluting the canonical namespace
- Taxonomy is the shared vocabulary across all other domains — treat it as a core dependency

### 2.5 `signals`
**Responsibility:** Compute quantitative signals per (topic/skill, market, time_window) combination. Signals include demand score, trend velocity, posting volume, and others.
**Inputs:** Enriched normalized records, taxonomy entities
**Outputs:** `signal_snapshots`
**Key Rules:**
- Signal computation is fully deterministic (no LLM calls)
- Signal snapshots are append-only (new snapshot per run, not in-place update)
- Signals are computed over configurable time windows (e.g., 30d, 90d, 180d)

### 2.6 `agents`
**Responsibility:** Isolate all LLM-based operations: skill extraction from free text, topic classification, opportunity brief generation, translation assistance.
**Inputs:** Text payloads from enrichment or opportunity generation
**Outputs:** Structured extraction results or generated text
**Key Rules:**
- All LLM calls go through a single `AgentClient` abstraction that can be swapped or mocked
- LLM outputs are always parsed and validated before being written to any table
- Every LLM call is logged with input hash, model name, latency, and output
- Hallucination mitigation: LLM outputs for taxonomy matching are validated against existing taxonomy entries

### 2.7 `ranking`
**Responsibility:** Combine multiple signals into a composite opportunity score.
**Inputs:** `signal_snapshots`, taxonomy metadata, internal supply data
**Outputs:** Ranked score records attached to signal snapshots
**Key Rules:**
- Ranking algorithm is deterministic and version-pinned
- Weights are configurable via environment variables or admin settings
- Score breakdowns are stored per dimension (demand, velocity, gap, confidence) — not just a single float

### 2.8 `opportunities`
**Responsibility:** Generate and manage `opportunity_brief` records from ranked signals.
**Inputs:** Ranked signal snapshots, taxonomy entities, internal supply data
**Outputs:** `opportunity_briefs`, `opportunity_evidence_items`
**Key Rules:**
- One opportunity brief per (topic_or_skill, market_context, time_window) cluster
- Deduplication logic prevents duplicate briefs for the same market+topic combination
- Opportunity lifecycle state machine is enforced here (draft → surfaced → analyst_review → approved/rejected)
- Briefs include both English and Hebrew fields where applicable

### 2.9 `serving`
**Responsibility:** Expose data via the REST API. Owns all FastAPI routers and response serialization.
**Inputs:** Queries against domain data via service interfaces
**Outputs:** JSON API responses
**Key Rules:**
- Serving layer never writes data (read-only)
- Response schemas are defined as Pydantic models, versioned under `/v1/`
- Pagination is cursor-based for large result sets

### 2.10 `orchestration`
**Responsibility:** Define and schedule pipeline runs. Coordinate domain execution order.
**Inputs:** Schedules, manual triggers, admin UI commands
**Outputs:** `pipeline_runs` records, task execution logs
**Key Rules:**
- Pipeline stages are executed in dependency order (ingestion → normalization → enrichment → signals → ranking → opportunities)
- Each stage reports status back to the pipeline run record
- Orchestration uses Celery (with Redis as broker) for async job execution

### 2.11 `observability`
**Responsibility:** Centralize structured logging, metrics, and alerting hooks.
**Inputs:** Log events from all domains
**Outputs:** Structured log records, metric counters, alert triggers
**Key Rules:**
- All log entries include: domain, stage, pipeline_run_id, record_count, status, duration_ms
- Metric counters are exposed on `/metrics` (Prometheus-compatible)
- Failure events emit to a configurable alert channel (Slack webhook or email)

### 2.12 `localization`
**Responsibility:** Manage i18n string resources, RTL metadata, and language-specific rendering hints for the API layer.
**Inputs:** Locale preference from request context
**Outputs:** Localized field variants in API responses
**Key Rules:**
- Every user-facing string has an English (`en`) and Hebrew (`he`) variant
- API responses include a `locale_hints` block indicating RTL status
- Localization does not translate dynamic content — only managed UI strings

### 2.13 `admin_ui`
**Responsibility:** Next.js frontend application for analysts and administrators.
**Technology:** Next.js 14+, TypeScript, Tailwind CSS, ShadCN/UI
**Key Features:**
- Opportunity queue with filters, search, and sorting
- Opportunity review workflow (approve / reject / annotate)
- Pipeline run status dashboard
- Taxonomy management interface
- RTL layout support for Hebrew locale

### 2.14 `governance`
**Responsibility:** Enforce data quality rules, flag anomalies, and maintain review decision audit logs.
**Inputs:** Pipeline run outputs, review decisions
**Outputs:** Quality flags, audit log entries
**Key Rules:**
- Every approved or rejected opportunity has a mandatory review decision record
- Data quality checks run post-normalization and post-enrichment
- Governance rules are configurable (e.g., minimum evidence items per opportunity, minimum confidence score for surfacing)

### 2.15 `evaluation`
**Responsibility:** Measure system accuracy over time. Track signal-to-outcome correlation, ranking quality, and analyst override rates.
**Inputs:** Analyst decisions, downstream content performance data (future)
**Outputs:** Evaluation metric snapshots
**Key Rules:**
- Evaluation is passive (observational) in v1 — it reads decisions but does not feed back into ranking
- Override rate (analyst rejection rate per signal source) is a primary quality metric
- Evaluation reports are accessible via the Admin UI

---

## 3. Technology Stack

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| API Framework | FastAPI | 0.111+ | Async, Pydantic-native, excellent OpenAPI support |
| Database | PostgreSQL | 16+ | JSONB for flexible schemas, full-text search, proven reliability |
| ORM | SQLAlchemy 2.x | 2.0+ | Async support, type-safe, industry standard |
| Migrations | Alembic | 1.13+ | First-class SQLAlchemy integration, reliable schema versioning |
| Cache / Broker | Redis | 7+ | Job queue broker for Celery, response caching for API layer |
| Task Queue | Celery | 5.3+ | Mature, well-documented, Redis-compatible async job runner |
| Admin Frontend | Next.js | 14+ | React Server Components, App Router, TypeScript native |
| Frontend Styling | Tailwind CSS | 3.4+ | Utility-first, RTL-friendly with `dir` attribute support |
| UI Components | ShadCN/UI | Latest | Accessible, unstyled-base components; Radix UI primitives |
| Validation | Pydantic v2 | 2.0+ | Fast, type-safe data validation throughout the stack |
| Config Management | python-dotenv + Pydantic Settings | — | Environment-based config with type validation |
| Testing (backend) | pytest + pytest-asyncio | — | Async test support for FastAPI and SQLAlchemy |
| Testing (frontend) | Vitest + Testing Library | — | Fast unit and integration tests for React components |
| Containerization | Docker + Docker Compose | — | Local dev parity; production deployment target |
| Reverse Proxy | Nginx or Caddy | — | TLS termination, routing to API and admin containers |

### LLM Integration (Agents Domain Only)

| Component | Technology | Notes |
|---|---|---|
| LLM Provider | OpenAI API (default) | Abstracted behind `AgentClient`; swappable |
| Embedding Model | text-embedding-3-small | Used for semantic skill/topic matching |
| Structured Output | OpenAI function calling / JSON mode | Enforces schema compliance on LLM outputs |
| Prompt Templates | Jinja2 | Version-controlled prompt templates with variable injection |

---

## 4. Repository Structure

```
cognet/
├── backend/
│   ├── src/
│   │   └── cognet/
│   │       ├── ingestion/          # Source connectors, raw landing
│   │       ├── normalization/      # Schema normalization per source type
│   │       ├── enrichment/         # Taxonomy tagging, skill/role extraction
│   │       ├── taxonomy/           # Canonical entity management
│   │       ├── signals/            # Signal computation
│   │       ├── agents/             # LLM calls, prompt templates
│   │       ├── ranking/            # Composite scoring
│   │       ├── opportunities/      # Brief generation, lifecycle management
│   │       ├── serving/            # FastAPI routers, response models
│   │       ├── orchestration/      # Pipeline coordination, Celery tasks
│   │       ├── observability/      # Logging, metrics
│   │       ├── localization/       # i18n string management
│   │       ├── governance/         # Quality rules, audit log
│   │       ├── evaluation/         # Accuracy tracking
│   │       ├── shared/             # Shared types, base models, utilities
│   │       └── main.py             # FastAPI app factory
│   ├── migrations/                 # Alembic migration scripts (all domains)
│   ├── tests/
│   │   ├── unit/                   # Domain-level unit tests
│   │   ├── integration/            # Cross-domain integration tests
│   │   └── fixtures/               # Shared test fixtures and factories
│   ├── pyproject.toml
│   └── Dockerfile
├── admin-ui/
│   ├── src/
│   │   ├── app/                    # Next.js App Router pages
│   │   ├── components/             # Reusable UI components
│   │   ├── features/               # Feature-scoped component trees
│   │   │   ├── opportunities/
│   │   │   ├── pipeline/
│   │   │   └── taxonomy/
│   │   ├── lib/                    # API client, utilities
│   │   ├── hooks/                  # Custom React hooks
│   │   └── i18n/                   # Translation files (en.json, he.json)
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── docs/
│   ├── product/
│   │   └── vision.md
│   └── technical/
│       ├── architecture.md         # This file
│       ├── data-flow.md
│       ├── domain-model.md
│       └── api-contracts.md
├── infra/
│   ├── docker-compose.yml          # Local development stack
│   ├── docker-compose.prod.yml     # Production compose override
│   └── nginx/
│       └── cognet.conf
├── scripts/
│   ├── seed_taxonomy.py            # Seed initial taxonomy data
│   ├── run_pipeline.py             # Manual pipeline trigger
│   └── health_check.sh
└── .env.example
```

---

## 5. Deployment Topology

```
                    ┌─────────────────────────────────────┐
                    │           Reverse Proxy              │
                    │       (Nginx / Caddy, TLS)           │
                    └──────────┬──────────────┬────────────┘
                               │              │
                    ┌──────────▼──┐    ┌──────▼──────────┐
                    │  FastAPI    │    │   Admin UI       │
                    │  Backend    │    │   (Next.js)      │
                    │  :8000      │    │   :3000          │
                    └──────┬──────┘    └─────────────────-┘
                           │
              ┌────────────┼────────────┐
              │            │            │
    ┌─────────▼──┐  ┌──────▼──────┐  ┌─▼─────────────┐
    │ PostgreSQL │  │    Redis     │  │  Celery        │
    │   :5432    │  │    :6379     │  │  Workers       │
    │            │  │  (broker +  │  │  (1..N)        │
    │            │  │   cache)    │  │                │
    └────────────┘  └─────────────┘  └────────────────┘
```

### Container Summary

| Container | Role | Replicas |
|---|---|---|
| `cognet-api` | FastAPI backend, serves REST API | 1 (v1), horizontally scalable |
| `cognet-admin` | Next.js admin frontend | 1 |
| `cognet-worker` | Celery workers for pipeline tasks | 1–4 depending on load |
| `cognet-beat` | Celery Beat scheduler for periodic tasks | 1 (singleton) |
| `postgres` | PostgreSQL 16 | 1 (managed DB in production) |
| `redis` | Redis 7, message broker + cache | 1 (managed in production) |
| `nginx` | Reverse proxy, TLS termination | 1 |

### Environment Variables (key)

```
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/cognet
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=sk-...
SECRET_KEY=<random 64-char hex>
ALLOWED_ORIGINS=https://admin.cognet.internal
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## 6. Domain Boundary Contracts

Cross-domain communication follows explicit rules:

### Rule 1: Service Interface Pattern
Each domain exposes a `service.py` module with typed Python functions. Other domains import and call these functions. No domain reaches directly into another domain's ORM models.

```python
# ALLOWED
from cognet.taxonomy.service import get_skill_by_slug
skill = await get_skill_by_slug("python-programming")

# FORBIDDEN
from cognet.taxonomy.models import Skill
skill = await db.get(Skill, id=42)  # called from outside taxonomy domain
```

### Rule 2: Shared Types in `shared/`
Types shared across more than one domain (e.g., `MarketContext`, `LanguageCode`, `PipelineRunRef`) live in `cognet/shared/types.py`. No domain-specific logic in `shared/`.

### Rule 3: Event-Driven Decoupling (Post-MVP)
In v1, domain calls are synchronous Python function calls. In a future version, high-volume cross-domain interactions (e.g., "new normalized record available") can be replaced with internal events via a lightweight in-process event bus or Celery tasks.

---

## 7. Integration-First Rule

Before building a custom ingestion connector or enrichment model, the team must evaluate whether an existing integration (API, library, or data vendor) can serve the need.

Preference order:
1. **Commercial data vendor** (e.g., job posting aggregator API) — buy data rather than scrape
2. **Open dataset** (e.g., ESCO skills taxonomy, O*NET) — use authoritative public sources
3. **Custom scraper or connector** — build only when no acceptable source exists

This rule minimizes maintenance burden and ensures data quality is delegated to sources with more capacity to maintain it.

---

## 8. Deterministic vs. LLM Boundary

The LDI Engine draws a hard line between deterministic and LLM-driven operations.

| Operation | Approach | Reason |
|---|---|---|
| Signal computation | Deterministic (SQL aggregations) | Must be reproducible and auditable |
| Taxonomy lookup (exact match) | Deterministic (database lookup) | Speed, zero cost, perfect accuracy |
| Fuzzy taxonomy matching | Deterministic (fuzzy string match / embedding similarity) | Reproducible without API cost |
| Skill extraction from job postings | LLM-assisted (agents domain) | Free text requires language understanding |
| Opportunity brief generation (text) | LLM-assisted (agents domain) | Narrative generation requires language model |
| Translation (EN ↔ HE) | LLM-assisted (agents domain) | No viable deterministic alternative |
| Ranking score computation | Deterministic (weighted formula) | Reproducibility is essential for analyst trust |
| Deduplication | Deterministic (canonical slug matching) | Must be consistent across runs |

**The golden rule:** If the output will be stored in a scored or ranked result that humans rely on, it must be deterministic or LLM output must be validated against a deterministic schema before storage.

---

## 9. Modular Monolith Extraction Paths

The monolith is designed to be extractable. Each domain is a candidate for future extraction into an independent service.

| Domain | Extraction Trigger | Likely Form |
|---|---|---|
| `ingestion` | Multiple teams owning separate connectors | Data ingestion microservice or event producer |
| `agents` | LLM call volume requires dedicated scaling | LLM gateway service |
| `serving` | API traffic exceeds monolith capacity | API service with read replicas |
| `taxonomy` | Taxonomy becomes a shared company-wide asset | Internal taxonomy service / API |
| `admin_ui` | Already a separate Next.js app | Already independently deployable |

Extraction is not planned for v1 or v2. The trigger is always operational need, not architectural preference.

---

## 10. Security Considerations

| Concern | Approach |
|---|---|
| Auth (MVP) | Internal network only; basic HTTP auth or IP allowlist |
| Auth (Post-MVP) | JWT tokens, role-based access (analyst, admin, read-only) |
| Secrets management | Environment variables; no secrets in code or config files |
| SQL injection | SQLAlchemy parameterized queries; no raw string interpolation |
| LLM prompt injection | Input sanitization before prompt construction; no user-supplied text in privileged prompts |
| Audit logging | All review decisions logged with user ID, timestamp, and before/after state |
| Data retention | Raw source records retained for 90 days; signal snapshots retained indefinitely |
