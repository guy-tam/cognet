# COGNET Learning Demand Intelligence Engine

> Internal intelligence, search, signal, ranking, and opportunity platform for Cognet.

## What is this?

COGNET LDI Engine is **not** the course delivery platform. It is the intelligence layer that determines what people truly need and want to learn in a specific market context. It transforms fragmented signals (job postings, trend data, internal supply gaps) into structured, ranked, explainable learning opportunities.

## Repository Structure

```
/
├── .cursor/rules/          # Cursor IDE development rules (13 rule files)
├── docs/                   # Architecture, product, governance, and operations docs
│   ├── product/            # Vision, product objectives
│   ├── technical/          # Architecture, data flow, domain model, API contracts
│   ├── data/               # Source catalog, taxonomy model
│   ├── agents/             # Agent system documentation
│   ├── operations/         # MVP scope, QA, observability
│   ├── governance/         # Scoring governance, source trust policy
│   └── evaluation/         # Evaluation framework
├── apps/
│   ├── api/                # FastAPI backend (Python 3.11+)
│   └── admin/              # Next.js 14 internal admin UI (TypeScript)
├── services/               # Domain services (Python)
│   ├── ingestion/          # Source connectors, raw data collection
│   ├── normalization/      # Text cleanup, canonical mapping
│   ├── enrichment/         # Skill/topic/role extraction
│   ├── taxonomy/           # Canonical entity management
│   ├── signals/            # Deterministic signal computation
│   ├── agents/             # Bounded specialist agents
│   ├── ranking/            # Deterministic ranking engine
│   ├── opportunities/      # Opportunity generation
│   └── orchestration/      # Pipeline orchestration
├── shared/                 # Shared Python contracts, schemas, enums
│   ├── contracts/          # Pydantic models (RawRecord, NormalizedRecord, etc.)
│   ├── enums/              # Shared Python enums
│   └── utils/              # Hashing, time utilities
├── infra/
│   ├── docker/             # docker-compose.yml, Dockerfiles
│   ├── scripts/            # Startup and utility scripts
│   └── migrations/         # Alembic database migrations
└── tests/
    ├── unit/               # Pure logic tests (no DB/network)
    ├── integration/        # API and service integration tests
    └── e2e/                # End-to-end flow tests
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.111 + Python 3.11 |
| Database | PostgreSQL 16 + SQLAlchemy 2.x async |
| Migrations | Alembic |
| Cache/Queue | Redis 7 |
| Background Jobs | Celery |
| Admin UI | Next.js 14 + TypeScript + Tailwind CSS |
| Localization | next-intl (English + Hebrew, RTL) |
| Logging | structlog |
| LLM (optional) | Anthropic Claude API |

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- Poetry (Python package manager)

## Local Setup

### 1. Clone and configure environment

```bash
git clone <repo>
cd cognet

# API environment
cp apps/api/.env.example apps/api/.env
# Edit apps/api/.env with your settings

# Admin environment
cp apps/admin/.env.example apps/admin/.env.local
```

### 2. Start infrastructure (PostgreSQL + Redis)

```bash
cd infra/docker
docker-compose up -d postgres redis
```

### 3. Install Python dependencies

```bash
cd apps/api
poetry install
```

### 4. Run migrations

```bash
# From project root
export PYTHONPATH="$(pwd)/apps/api:$(pwd)/services:$(pwd)"
cd infra
alembic upgrade head
```

### 5. Start the API

```bash
cd apps/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API available at: http://localhost:8000
API docs: http://localhost:8000/docs

### 6. Start the Admin UI

```bash
cd apps/admin
npm install
npm run dev
```

Admin UI available at: http://localhost:3000

## Environment Variables

### API (`apps/api/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL async URL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Yes | Redis URL (`redis://localhost:6379/0`) |
| `APP_ENV` | No | `development` or `production` (default: `development`) |
| `APP_SECRET_KEY` | Yes in prod | Secret key for security |
| `ANTHROPIC_API_KEY` | No | Claude API key (optional — system works without it) |
| `DEFAULT_PIPELINE_COUNTRY` | No | Default country code (default: `IL`) |
| `DEFAULT_PIPELINE_LANGUAGE` | No | Default language (default: `he`) |
| `MINIMUM_OPPORTUNITY_SCORE` | No | Min score to surface opportunities (default: `0.35`) |

### Admin (`apps/admin/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | No | Backend API URL (default: `http://localhost:8000/api`) |

## Running Tests

```bash
# All tests
bash infra/scripts/run-tests.sh

# Unit tests only
export PYTHONPATH="$(pwd)/apps/api:$(pwd)/services:$(pwd)"
pytest tests/unit/ -v

# API tests
pytest apps/api/app/tests/ -v

# With coverage
pytest --cov=services --cov=apps/api/app tests/ -v
```

## Database Migrations

```bash
# Apply all pending migrations
cd infra && alembic upgrade head

# Create new migration after model changes
cd infra && alembic revision --autogenerate -m "add new field"

# Downgrade one step
cd infra && alembic downgrade -1
```

## Bilingual UI (EN + Hebrew)

The admin UI supports full English and Hebrew (RTL) rendering.

- Language files: `apps/admin/locales/en/common.json` and `apps/admin/locales/he/common.json`
- Switch language using the locale switcher in the admin navigation
- Hebrew mode activates RTL layout automatically

## Key Architecture Decisions

- **Modular monolith**: Not microservices. Strong domain boundaries with clear extraction paths.
- **Deterministic ranking**: Scoring is always deterministic — no LLM substitution for numerical scores.
- **Source connectors**: All data sources accessed through bounded connector abstractions.
- **LLM optional**: The system works without an LLM API key. LLM is used only for `why_now` summaries.
- **Audit trail**: Every surfaced opportunity traces back to source families, evidence items, scoring inputs, and pipeline run.

## Documentation

- [Product Vision](docs/product/vision.md)
- [Architecture](docs/technical/architecture.md)
- [Data Flow](docs/technical/data-flow.md)
- [Domain Model](docs/technical/domain-model.md)
- [API Contracts](docs/technical/api-contracts.md)
- [Scoring Governance](docs/governance/scoring-governance.md)
- [Agent System](docs/agents/agent-system.md)
- [MVP Scope](docs/operations/mvp-scope.md)

---

*COGNET Learning Demand Intelligence Engine — Internal Tool*
