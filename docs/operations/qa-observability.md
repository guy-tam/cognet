# QA & Observability — COGNET LDI Engine

## 1. עיקרון QA

> **QA מתחיל בארכיטקטורה, לא בסוף.**

ב-COGNET LDI, איכות אינה שלב נפרד — היא מוטמעת בכל החלטת עיצוב:
- חוזי schema מוגדרים לפני כתיבת קוד
- fallback behavior מוגדר לפני שחושבים על happy path
- logs כתובים כך שניתן לדבג בלי to reproduce מחדש
- agents בנויים ל-testability ראשית

**שלושה עמודי observability ב-MVP:**
1. **Structured logs** — כל מידע נחוץ לדיבוג קיים ב-log
2. **Health endpoints** — מערכת יכולה לדווח על עצמה
3. **Pipeline stage tracking** — כל שלב בפייפליין מתועד עם status

---

## 2. Structured Logging

### עיקרון

כל log entry הוא JSON object. לא strings חופשיים. לא f-strings עם concatenation. כל שדה הוא שדה מובנה.

### Library

**Python backend:** `structlog` עם JSON renderer ב-production, ConsoleRenderer ב-development.

```python
import structlog

log = structlog.get_logger()

# שימוש נכון
log.info(
    "pipeline_stage_complete",
    run_id=run_id,
    stage="job_demand_agent",
    market_id=market_id,
    duration_ms=elapsed_ms,
    records_processed=count,
)

# שימוש שגוי — לא לעשות
log.info(f"pipeline stage {stage} done for {market_id}")
```

### שדות חובה בכל Log Entry

| שדה | סוג | תיאור |
|-----|-----|--------|
| `event` | string | שם האירוע (snake_case) |
| `level` | string | debug / info / warning / error / critical |
| `timestamp` | string | ISO 8601 UTC |
| `module` | string | שם המודול (e.g., "agents.job_demand") |
| `run_id` | string | UUID של ריצת pipeline (אם רלוונטי) |
| `stage` | string | שם השלב בפייפליין |
| `market_id` | string | market (אם רלוונטי) |

### שדות אופציונליים נפוצים

| שדה | תיאור |
|-----|--------|
| `source_name` | שם הקונקטור (e.g., "linkedin_jobs_il") |
| `source_run_id` | UUID ספציפי לריצת connector |
| `record_count` | מספר רשומות שעובדו |
| `duration_ms` | זמן ביצוע במילישניות |
| `error_type` | סוג השגיאה (class name) |
| `error_detail` | תיאור קצר של השגיאה |
| `topic_id` | אם log קשור לנושא ספציפי |
| `skill_id` | אם log קשור למיומנות ספציפית |
| `agent_name` | שם ה-agent הרץ |

### Log Configuration

```python
# config/logging.py
import structlog
import logging

def configure_logging(env: str = "production"):
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if env == "development":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

---

## 3. Health Endpoint

**Route:** `GET /health`

**מטרה:** בדיקה בסיסית שהשרת עולה ומגיב — בלי dependency checks.

**Response (200 OK תמיד, כל עוד התהליך חי):**
```json
{
  "status": "ok",
  "service": "cognet-ldi-api",
  "version": "0.1.0",
  "timestamp": "2026-03-26T12:00:00Z"
}
```

**כללים:**
- לא מתחבר ל-DB
- לא בודק config
- חייב להגיב תוך 1 שנייה
- משמש load balancer / container health check

---

## 4. Readiness Endpoint

**Route:** `GET /readiness`

**מטרה:** בדיקה שהשרת מוכן לקבל traffic אמיתי — כולל connectivity checks.

**Response (200 OK כאשר ready):**
```json
{
  "status": "ready",
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 4
    },
    "taxonomy_loaded": {
      "status": "ok",
      "skill_count": 52,
      "topic_count": 21
    },
    "config": {
      "status": "ok"
    }
  },
  "timestamp": "2026-03-26T12:00:00Z"
}
```

**Response (503 Service Unavailable כאשר not ready):**
```json
{
  "status": "not_ready",
  "checks": {
    "database": {
      "status": "error",
      "error": "connection timeout"
    },
    "taxonomy_loaded": {
      "status": "ok",
      "skill_count": 52,
      "topic_count": 21
    },
    "config": {
      "status": "ok"
    }
  },
  "timestamp": "2026-03-26T12:00:00Z"
}
```

**Readiness checks:**
1. `database` — SELECT 1 על ה-DB
2. `taxonomy_loaded` — בדיקה שיש לפחות N skills ו-M topics ב-taxonomy tables
3. `config` — בדיקה שכל required env vars קיימים (לא ריקים)

---

## 5. Pipeline Stage Logs

כל שלב בפייפליין נרשם ב-DB וב-logs.

### DB Schema

```sql
CREATE TABLE pipeline_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    triggered_by    VARCHAR(64),       -- "manual" | "scheduled" | "api"
    market_id       VARCHAR(64),
    started_at      TIMESTAMP NOT NULL,
    completed_at    TIMESTAMP,
    status          VARCHAR(32),       -- "running" | "completed" | "failed" | "partial"
    error_count     INT DEFAULT 0,
    stages_total    INT,
    stages_completed INT DEFAULT 0,
    metadata        JSONB
);

CREATE TABLE pipeline_stages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID REFERENCES pipeline_runs(id),
    stage_name      VARCHAR(64) NOT NULL,  -- "ingest_jobs", "normalize", "trend_agent", ...
    started_at      TIMESTAMP NOT NULL,
    completed_at    TIMESTAMP,
    status          VARCHAR(32),  -- "running" | "completed" | "failed" | "skipped"
    records_in      INT,
    records_out     INT,
    error_message   TEXT,
    metadata        JSONB
);
```

### Log Events לפי שלב

```python
# תחילת ריצה
log.info("pipeline_run_start",
    run_id=run_id, market_id=market_id, triggered_by="manual", stage="pipeline")

# תחילת שלב
log.info("pipeline_stage_start",
    run_id=run_id, stage="ingest_job_postings", source_name="linkedin_jobs_il")

# סיום שלב
log.info("pipeline_stage_complete",
    run_id=run_id, stage="ingest_job_postings",
    records_in=0, records_out=1243, duration_ms=4521)

# כשל שלב
log.error("pipeline_stage_failed",
    run_id=run_id, stage="ingest_job_postings",
    error_type="ConnectorRateLimitError",
    error_detail="429 received from LinkedIn API",
    fallback_applied="SKIP_AND_LOG")

# סיום ריצה
log.info("pipeline_run_complete",
    run_id=run_id, market_id=market_id,
    status="partial", stages_completed=6, stages_total=7,
    total_duration_ms=87432, error_count=1)
```

---

## 6. Job Execution Logs

לוגים ספציפיים לפעולות פנים-agent.

```python
# JobDemandAgent — תחילת ניתוח
log.info("agent_run_start",
    agent_name="JobDemandAgent", run_id=run_id, market_id=market_id,
    jobs_to_analyze=1243, skill_ids_count=52)

# LLM extraction attempt
log.debug("llm_skill_extraction_attempt",
    agent_name="JobDemandAgent", run_id=run_id,
    record_external_id="job_12345", description_chars=842)

# LLM extraction fallback
log.warning("llm_skill_extraction_fallback",
    agent_name="JobDemandAgent", run_id=run_id,
    record_external_id="job_12345",
    reason="LLMTimeout", fallback="keyword_matching",
    skills_found_by_fallback=3)

# Normalization miss
log.warning("normalization_miss",
    stage="normalize", run_id=run_id,
    entity_type="skill", raw_label="java spring boot microservices",
    source_name="linkedin_jobs_il",
    action="stored_as_unknown")

# SkillGapAgent — gap computation
log.debug("skill_gap_computed",
    agent_name="SkillGapAgent", run_id=run_id,
    skill_id="skill_kubernetes", demand_score=0.72,
    supply_coverage=0.15, gap_score=0.612,
    gap_severity="critical")

# TopicPrioritizationAgent — ranking complete
log.info("topic_ranking_complete",
    agent_name="TopicPrioritizationAgent", run_id=run_id,
    topics_ranked=21, top_topic_id="topic_devops",
    top_score=0.847, weights_used={"job_demand": 0.5, "trend": 0.25, "gap": 0.25})
```

---

## 7. Error Handling ו-Logging

### עקרונות

1. **Log ואז handle — לא handle בשקט:** כל exception נרשם, גם אם הפייפליין ממשיך
2. **Structured errors:** error_type + error_detail תמיד ב-log
3. **No silent failures:** `except Exception: pass` אסור בהחלט
4. **Fallback is explicit:** כל fallback נרשם כ-warning עם fallback applied

### Exception Hierarchy

```python
class CognetLDIError(Exception):
    """Base exception"""
    pass

class ConnectorError(CognetLDIError):
    """שגיאות בשכבת קונקטורים"""
    pass

class ConnectorRateLimitError(ConnectorError):
    pass

class ConnectorAuthError(ConnectorError):
    pass

class NormalizationError(CognetLDIError):
    pass

class AgentError(CognetLDIError):
    pass

class AgentOutputValidationError(AgentError):
    """output של agent לא עומד ב-schema"""
    pass

class AgentTimeoutError(AgentError):
    pass

class PipelineError(CognetLDIError):
    pass
```

### Error Logging Pattern

```python
try:
    result = run_agent(agent, inputs)
except AgentTimeoutError as e:
    log.error("agent_timeout",
        agent_name=agent.name, run_id=run_id,
        error_type="AgentTimeoutError",
        error_detail=str(e),
        fallback_applied="PARTIAL_OUTPUT")
    result = agent.get_partial_output()
except AgentOutputValidationError as e:
    log.error("agent_output_invalid",
        agent_name=agent.name, run_id=run_id,
        error_type="AgentOutputValidationError",
        field=e.field, error_detail=e.message)
    raise PipelineError(f"Invalid output from {agent.name}") from e
```

---

## 8. קטגוריות QA

### 8.1 Startup Stability
- Docker Compose עולה בלי errors על machine נקייה
- כל services healthy לאחר `docker compose up`
- `/health` מחזיר 200 תוך 30 שניות מ-startup

### 8.2 DB Connectivity
- `/readiness` מחזיר DB check = "ok"
- Alembic migrations רצות ללא errors על DB ריק
- בדיקה שכל taxonomy tables קיימות וm-seeded

### 8.3 Route Wiring
- כל registered routes מגיבות (לא 404)
- Routes עם path params (`/opportunities/:id`) — בדיקה עם valid ו-invalid ID

### 8.4 Schema Validity
- כל agent output עובר `jsonschema.validate` לפני שנשמר
- בדיקה שschema files קיימים ל-4 agents operational

### 8.5 Ranking Math Sanity

```python
def test_composite_score_bounds():
    """composite score חייב להיות בין 0.0 ל-1.0"""
    for _ in range(1000):
        job = random.uniform(0, 1)
        trend = random.uniform(0, 1)
        gap = random.uniform(0, 1)
        score = compute_composite_score(job, trend, gap, DEFAULT_WEIGHTS)
        assert 0.0 <= score <= 1.0

def test_composite_score_ordering():
    """topic עם demand גבוה יותר חייב לדרג גבוה יותר (ceteris paribus)"""
    score_high = compute_composite_score(0.9, 0.5, 0.5, DEFAULT_WEIGHTS)
    score_low  = compute_composite_score(0.3, 0.5, 0.5, DEFAULT_WEIGHTS)
    assert score_high > score_low

def test_weights_sum_to_one():
    """weights חייבים לסכום ל-1.0"""
    w = PrioritizationWeights()
    total = w.job_demand_weight + w.trend_weight + w.gap_weight
    assert abs(total - 1.0) < 1e-9

def test_gap_score_formula():
    """gap_score = demand * (1 - supply_coverage)"""
    assert compute_gap_score(1.0, 0.0) == 1.0
    assert compute_gap_score(1.0, 1.0) == 0.0
    assert compute_gap_score(0.0, 0.0) == 0.0
    assert abs(compute_gap_score(0.8, 0.5) - 0.4) < 1e-9
```

### 8.6 Normalization Sanity

```python
def test_known_alias_resolves():
    """alias ידוע חייב לחזור ל-canonical ID"""
    result = normalize_label("python3", "skill", "linkedin_jobs_il")
    assert result == "skill_python"

def test_unknown_alias_returns_none():
    """label שאין לו alias → None (לא crash)"""
    result = normalize_label("xyz_totally_unknown_skill_9999", "skill", "any_source")
    assert result is None

def test_case_insensitive():
    """normalization חייב להיות case-insensitive"""
    assert normalize_label("Python", "skill", "any") == normalize_label("python", "skill", "any")
```

### 8.7 Pipeline Status Visibility
- לאחר ריצה: `GET /api/v1/pipeline/status` מחזיר את הריצה האחרונה עם שדות נכונים
- status = "completed" | "partial" | "failed" — לא null

### 8.8 Admin Data Rendering
- Opportunities list: לפחות 1 result מוצג לאחר pipeline run
- Opportunity detail: כל fields מוצגים (rank, scores, skill gaps)
- Pipeline status: כל stages מוצגים עם status

### 8.9 Localization Key Presence

```python
def test_all_i18n_keys_present():
    """כל i18n keys בעברית חייבים להיות גם באנגלית"""
    he_keys = set(load_translation("he").keys())
    en_keys = set(load_translation("en").keys())
    missing_in_en = he_keys - en_keys
    missing_in_he = en_keys - he_keys
    assert not missing_in_en, f"Keys missing in EN: {missing_in_en}"
    assert not missing_in_he, f"Keys missing in HE: {missing_in_he}"
```

### 8.10 Hebrew RTL Shell Behavior
- בעת בחירת locale עברית: `dir="rtl"` ב-`<html>` tag
- padding/margin values מוחלפים (tailwind: `pl-` ↔ `pr-` עם RTL plugin)
- כפתורים, טבלאות, navigation — כל alignments נכונים

### 8.11 Empty / Error State Handling
- Opportunities list ריקה → UI מציג "אין הזדמנויות זמינות" (לא blank page)
- Pipeline run נכשל → UI מציג status = "failed" עם error indicator
- API error 500 → response מכיל `{"error": "internal_error", "run_id": "..."}` (לא raw traceback)

---

## 9. Testing Layers

### Layer 1 — Unit Tests

**מיקום:** `tests/unit/`

```
tests/unit/
  test_ranking_math.py          # compute_composite_score, compute_gap_score
  test_schema_validation.py     # כל 4 agent output schemas
  test_normalization.py         # alias lookup, fuzzy match, case insensitivity
  test_connector_parse.py       # parse() של כל connector עם fixtures
  test_supply_coverage.py       # compute_supply_coverage algorithm
```

**כלל:** unit tests לא מתחברים ל-DB. כל DB dependency → mock.

### Layer 2 — Integration Tests

**מיקום:** `tests/integration/`

```
tests/integration/
  test_health.py            # GET /health
  test_readiness.py         # GET /readiness (requires live DB)
  test_opportunities_api.py # GET /api/v1/opportunities (requires seeded DB)
  test_pipeline_status.py   # GET /api/v1/pipeline/status
  test_taxonomy_seed.py     # שה-seed data נטען נכון
```

**כלל:** integration tests רצים על test DB (Docker). לא על production data.

### Layer 3 — E2E (Placeholder)

**מיקום:** `tests/e2e/`

```python
# tests/e2e/test_full_pipeline.py
import pytest

@pytest.mark.skip(reason="e2e requires full environment with live connectors")
def test_full_pipeline_il_market():
    """
    TODO: רץ pipeline מלא על ישראל עם fixture data.
    1. מעלה fixture records לraw_records
    2. מריץ normalization
    3. מריץ כל 4 agents
    4. בודק שranked_topics נשמרו ב-DB
    5. בודק ש-/api/v1/opportunities מחזיר תוצאות
    """
    pass

@pytest.mark.skip(reason="e2e requires full environment with live connectors")
def test_pipeline_partial_failure_recovery():
    """
    TODO: בודק שהפייפליין ממשיך גם כאשר TrendAnalysisAgent נכשל.
    """
    pass
```

---

## 10. Anomaly Detection Hooks

### מה לבדוק (MVP — logging בלבד, לא alerts)

| Anomaly | Detection Logic | Action |
|---------|----------------|--------|
| Job postings count drop >50% ביחס לריצה הקודמת | compare records_out בין runs | log.warning + flag ב-pipeline_run metadata |
| Normalization miss rate >20% | miss_count / total_records > 0.2 | log.warning |
| All trend signals returning 0 | trend_score == 0 לכל topics | log.warning |
| Agent timeout | duration > threshold | log.error + PARTIAL fallback |
| Composite score distribution collapse | כל scores < 0.1 או > 0.9 | log.warning |
| Zero opportunities after full pipeline | ranked_topics count == 0 | log.error |

### Implementation Pattern

```python
def check_pipeline_anomalies(result: PipelineResult, previous_run: PipelineRun | None) -> None:
    """
    רץ לאחר כל pipeline completion.
    לא זורק exceptions — רק logs.
    """
    log = structlog.get_logger().bind(stage="anomaly_check", run_id=result.run_id)

    # בדיקת job count drop
    if previous_run and result.jobs_ingested < previous_run.jobs_ingested * 0.5:
        log.warning("anomaly_job_count_drop",
            current=result.jobs_ingested,
            previous=previous_run.jobs_ingested,
            drop_pct=round(1 - result.jobs_ingested / previous_run.jobs_ingested, 2))

    # בדיקת normalization miss rate
    miss_rate = result.normalization_misses / max(result.records_normalized, 1)
    if miss_rate > 0.20:
        log.warning("anomaly_high_normalization_miss_rate",
            miss_rate=round(miss_rate, 3),
            threshold=0.20)

    # בדיקת zero opportunities
    if result.ranked_topics_count == 0:
        log.error("anomaly_zero_opportunities",
            market_id=result.market_id)
```

---

## 11. מסלול התרחבות עתידית — OpenTelemetry

ב-MVP: **logging בלבד.** OpenTelemetry hooks קיימים כ-stub.

```python
# observability/tracing.py
"""
Stub module לOpenTelemetry integration עתידית.
ב-MVP: כל פונקציות הtracing הן no-ops.
"""

def get_tracer(name: str):
    """Returns a no-op tracer in MVP."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return NoOpTracer()

class NoOpTracer:
    def start_as_current_span(self, name: str, **kwargs):
        from contextlib import contextmanager
        @contextmanager
        def noop():
            yield None
        return noop()
```

**מה יתווסף ב-V2:**
- Distributed tracing (Jaeger / Honeycomb)
- Metrics export (Prometheus)
- Alert rules בmessaging (Slack / PagerDuty)
- Dashboard ב-Grafana

---

## 12. Cost Awareness

### עקרונות עלות

**LLM calls:**
- אין לקרוא ל-LLM על כל job description — רק כאשר `skills_mentioned_raw` ריק ו-keyword matching נכשל
- batch extraction מועדף על single-record calls
- log כל LLM call עם `llm_tokens_used` לtracking עלויות

**Polling:**
- אין לpolll מקורות חיצוניים בקצב גבוה יותר מהנדרש
- Google Trends: לא יותר מפעם בשבוע לquery נתון
- Internal supply: לא יותר מפעם ב-24 שעות

**DB queries:**
- אין full table scans ב-normalization loop — שימוש ב-indexed alias lookups
- Agent outputs נשמרים ב-DB ומוגשים מ-DB — לא מחושבים מחדש בכל API request

**Pipeline frequency:**
- MVP: pipeline ידני בלבד (trigger על דרישה)
- אין scheduling אוטומטי ב-MVP (מונע ריצות מיותרות)

```python
# כלל: log כל LLM call עם token count
def call_llm_with_tracking(prompt: str, model: str, run_id: str) -> str:
    response = llm_client.complete(prompt, model=model)
    log.info("llm_call",
        run_id=run_id, model=model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        total_tokens=response.usage.total_tokens,
        estimated_cost_usd=estimate_cost(response.usage, model))
    return response.text
```
