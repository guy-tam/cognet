# MVP Scope — COGNET LDI Engine

## 1. הגדרת הצלחת MVP

> **MVP מוצלח = זרימה קוהרנטית אחת מ-end לend: ממקורות נתונים ← דרך normalization ← דרך agents ← לAPI ← לממשק admin — בצורה שניתן להדגים ולהריץ שוב.**

MVP הוא לא proof of concept ולא prototype. הוא גרסה ראשונה עובדת של המנוע שמאפשרת לבדוק את ה-intelligence logic על נתונים אמיתיים ולהציג תוצאות לבעלי עניין.

**מה שאנחנו צריכים בסוף MVP:**
- פייפליין מלא שרץ מ-trigger ידני ועד output מוצג ב-UI
- לפחות שוק אחד (ישראל / `region_il`) עם נתונים אמיתיים
- ranked topics עם composite scores מבוססי signals אמיתיים
- API שמגיש את התוצאות
- admin UI שמראה pipeline status ורשימת הזדמנויות
- תיעוד מספיק לחבר מפתח חדש

---

## 2. מה בתוך ה-MVP (In Scope)

### מקורות נתונים
- [x] Job Postings connector (לפחות אחד מ: LinkedIn API, Indeed, job board scraping)
- [x] Trend Signals connector (Google Trends + Stack Overflow)
- [x] Internal Supply connector (CSV import + manual trigger)

### שכבת עיבוד נתונים
- [x] Raw Record ingestion ו-persistence (DB)
- [x] Normalization pipeline: skill/topic/role label → canonical ID
- [x] Deduplication בסיסי (external_id + source_name)
- [x] Language detection לרשומות קיימות
- [x] Taxonomy seed data (skills, topics, roles, aliases)

### Agents (4 Operational)
- [x] TrendAnalysisAgent — מנתח trend signals לפי market
- [x] JobDemandAgent — מנתח job posting demand לפי skill/role
- [x] SkillGapAgent — מחשב gap בין demand ל-supply
- [x] TopicPrioritizationAgent — מדרג topics לפי composite score

### API
- [x] `GET /health` — בדיקת זמינות
- [x] `GET /readiness` — בדיקת מוכנות (DB, config)
- [x] `GET /api/v1/opportunities` — רשימת הזדמנויות מדורגות
- [x] `GET /api/v1/opportunities/:id` — פרטי הזדמנות ספציפית
- [x] `GET /api/v1/pipeline/status` — סטטוס ריצות pipeline אחרונות
- [x] `POST /api/v1/pipeline/trigger` — trigger ידני לריצת pipeline (admin)

### Admin UI
- [x] Dashboard — KPI cards (נושאים מדורגים, coverage, run status)
- [x] Opportunities list — רשימה מדורגת עם filters בסיסיים
- [x] Opportunity detail — פרטי הזדמנות עם score breakdown
- [x] Pipeline status page — ריצות אחרונות + logs
- [x] Locale switch — עברית / אנגלית (RTL support)

### Infrastructure
- [x] PostgreSQL (DB ראשי)
- [x] FastAPI (backend)
- [x] Next.js (admin UI)
- [x] Docker Compose לסביבת פיתוח
- [x] Environment config (`.env` based)
- [x] Structured logging (JSON logs)
- [x] Basic error handling (לא crash on partial failure)

### Testing
- [x] Unit tests: ranking math, schema validation, normalization logic
- [x] Integration tests: health endpoint, opportunities endpoint
- [x] Placeholder e2e structure (לא מלא ב-MVP)

---

## 3. מה מחוץ ל-MVP (Out of Scope)

| פיצ'ר | סיבה |
|--------|-------|
| MarketResearchAgent | מורכב מדי, scaffold בלבד |
| RegionCultureFitAgent | נחוץ לאחר validation של הצרכים |
| ConsistencyValidationAgent | ל-V2 |
| LearningOpportunityAgent | scaffold, לאחר TopicPrioritization stable |
| Celery / async task queue | over-engineering ל-MVP |
| Multi-tenant support | לאחר MVP |
| User authentication (API) | לאחר MVP, API פנימי לעת עתה |
| Salary data integration | לאחר MVP |
| Enterprise training demand | לאחר MVP |
| Automatic taxonomy expansion (LLM) | לאחר MVP |
| Event-driven triggers (webhooks) | לאחר MVP |
| Kubernetes deployment | לאחר MVP |
| OpenTelemetry full tracing | OpenTelemetry readiness hooks only ב-MVP |
| MOOC/competitor platform data | לאחר MVP |
| Mobile UI | לאחר MVP |
| Email/Slack notifications | לאחר MVP |

---

## 4. הגדרת ה-First Flow

זרימה ראשונה מלאה = ה-critical path של המערכת:

```
[1] Ingest
    ↓ Job Postings connector רץ, מביא רשומות גולמיות
    ↓ Trend Signals connector רץ, מביא trend records
    ↓ Internal Supply connector רץ (CSV upload), מביא course records
    ↓ כל רשומות נשמרות ב-raw_records DB table

[2] Normalize
    ↓ כל raw records עוברים normalization
    ↓ skill/topic/role labels ממופים ל-canonical IDs
    ↓ dedup מוחק כפילויות
    ↓ normalized records נשמרים

[3] Enrich
    ↓ language detection על רשומות בלי language_code
    ↓ country/region enrichment על רשומות עם location_raw
    ↓ skill extraction מ-job descriptions (LLM fallback → keyword)

[4] Signal
    ↓ TrendAnalysisAgent רץ → TrendAnalysisOutput נשמר
    ↓ JobDemandAgent רץ → JobDemandOutput נשמר

[5] Gap
    ↓ SkillGapAgent רץ עם job demand + internal supply → SkillGapOutput

[6] Rank
    ↓ TopicPrioritizationAgent רץ עם כל ה-signals → RankedTopics נשמרים ב-DB

[7] API
    ↓ GET /api/v1/opportunities מגיש RankedTopics מה-DB

[8] Admin UI
    ↓ Opportunities list page מציגה את התוצאות
    ↓ Pipeline status page מציגה את הריצה האחרונה
```

**זרימה זו חייבת לעבוד end-to-end לפני שמגיעים ל-MVP release gate.**

---

## 5. משפחות מקורות ל-MVP

| משפחה | קונקטורים ב-MVP | Tier | סטטוס |
|--------|----------------|------|--------|
| Job Postings | 1 connector (LinkedIn או Indeed) | 1 | operational |
| Trend Signals | Google Trends + Stack Overflow | 2 | operational |
| Internal Supply | CSV connector | 1 | operational |

**הערה:** Twitter/X connector יהיה בקוד אך לא יחובר ל-pipeline ב-MVP (Tier 3 — לא משפיע על ranking).

---

## 6. Agent MVP Set

| Agent | סטטוס MVP | חלק מ-pipeline |
|-------|-----------|---------------|
| MarketResearchAgent | scaffold | לא |
| **TrendAnalysisAgent** | **operational** | **כן** |
| **JobDemandAgent** | **operational** | **כן** |
| **SkillGapAgent** | **operational** | **כן** |
| RegionCultureFitAgent | scaffold | לא (SKIP fallback) |
| **TopicPrioritizationAgent** | **operational** | **כן** |
| LearningOpportunityAgent | scaffold | לא |
| ConsistencyValidationAgent | scaffold | לא |

---

## 7. UI MVP Scope

### Dashboard
- KPI cards: מספר ranked topics, coverage % של supply, timestamp של last run, market active
- Quick nav לרשימת הזדמנויות ולpipeline status

### Opportunities List
- טבלה/רשימה מדורגת של ranked topics
- עמודות: rank, topic name, composite score, top skill gaps, last updated
- Filter: market, minimum score
- Sort: לפי rank (default), score, date

### Opportunity Detail
- שם הנושא, composite score
- Score breakdown: job demand score, trend score, gap score, weights used
- רשימת מיומנויות עם הגבוה gap
- קורסים קיימים שמכסים (מה-supply)
- recommendation: create_new / enhance_existing / sufficient

### Pipeline Status Page
- טבלה של ריצות אחרונות (run_id, started_at, completed_at, status, errors_count)
- כפתור trigger ריצה ידנית
- לחיצה על ריצה → פרטי stages

### Locale Switch
- כפתור עברית/אנגלית בheader
- RTL layout מלא לעברית
- כל strings דרך i18n keys (אין hardcoded text)

---

## 8. Infrastructure MVP Scope

### מה חובה ב-MVP
```yaml
# docker-compose.yml — MVP services
services:
  db:
    image: postgres:15
    volumes: [postgres_data:/var/lib/postgresql/data]

  api:
    build: ./api
    depends_on: [db]
    env_file: .env
    ports: ["8000:8000"]

  ui:
    build: ./ui
    depends_on: [api]
    ports: ["3000:3000"]
```

### Database (PostgreSQL)
- טבלאות: raw_records, normalized_records, taxonomy_*, pipeline_runs, pipeline_stages, ranked_topics, skill_gaps
- Alembic migrations מ-day 1
- Read replica — לא נדרש ב-MVP

### Logging
- JSON structured logs (Python: structlog)
- כל log entry: module, run_id, stage, level, message, timestamp UTC
- לא CloudWatch/Datadog ב-MVP — stdout בלבד

### Configuration
- `.env` file עם כל secrets
- `.env.example` ב-repo (ללא values)
- `config.py` מרכזי שטוען את כל ה-env vars

---

## 9. Testing MVP Scope

### Unit Tests (חובה)
- ranking math: `compute_composite_score`, `compute_gap_score`, `compute_supply_coverage`
- schema validation: כל agent output schema
- normalization: alias lookup, fuzzy match fallback

### Integration Tests (חובה)
- `GET /health` → 200 OK
- `GET /readiness` → 200 OK עם DB connected
- `GET /api/v1/opportunities` → 200 OK עם valid schema

### Placeholder E2E (לא מלא ב-MVP)
- קובץ `tests/e2e/test_full_pipeline.py` קיים
- מסומן `@pytest.mark.skip(reason="e2e - requires full environment")`
- מכיל את הstructure לריצה עתידית

### Coverage Target ל-MVP
- ranking logic: 100%
- normalization logic: 90%+
- API routes: 80%+

---

## 10. Release Gates — מה חייב להיות נכון ל-MVP Milestone

| Gate | תיאור | חובה / מומלץ |
|------|--------|-------------|
| G1 | פייפליין מלא רץ end-to-end ב-staging | חובה |
| G2 | לפחות שוק אחד עם נתונים אמיתיים | חובה |
| G3 | כל unit tests עוברים | חובה |
| G4 | כל integration tests עוברים | חובה |
| G5 | `/health` ו-`/readiness` מחזירים 200 | חובה |
| G6 | Admin UI מציג opportunities ו-pipeline status | חובה |
| G7 | Locale switch עובד (עברית + אנגלית) | חובה |
| G8 | RTL layout תקין לעברית | חובה |
| G9 | אין unhandled exceptions ב-critical path | חובה |
| G10 | כל agent outputs עוברים schema validation | חובה |
| G11 | Source addition policy מתועדת | מומלץ |
| G12 | OpenTelemetry hooks קיימים (stub) | מומלץ |
| G13 | E2E test structure קיים (גם אם skipped) | מומלץ |

---

## 11. Build Order — פאזות A עד H

### Phase A — Infrastructure Foundation
- Docker Compose עם PostgreSQL + FastAPI + Next.js
- Alembic migrations setup
- `.env` config loading
- `/health` endpoint
- Structured logging setup
- **Validation gate A:** `docker compose up` עולה בלי errors, `/health` מחזיר 200

### Phase B — Taxonomy & Raw Records
- DB schema: taxonomy tables + raw_records + normalized_records
- Seed data scripts (ISO tables + 50 skills + 20 topics + aliases)
- RawRecord dataclass + connector base class
- **Validation gate B:** seed scripts רצים, taxonomy tables מאוכלסות

### Phase C — Source Connectors
- Internal Supply CSV connector (מלא, operational)
- Trend Signals connector (Google Trends + Stack Overflow)
- Job Postings connector (1 connector מלא)
- Normalization pipeline + alias lookup
- **Validation gate C:** כל 3 connectors מביאים רשומות, normalization מייצר normalized_records

### Phase D — Agents (TrendAnalysis + JobDemand)
- TrendAnalysisAgent (operational)
- JobDemandAgent (operational, עם LLM skill extraction fallback)
- Schema validation לoutputs
- Unit tests לשני ה-agents
- **Validation gate D:** שני agents רצים על נתונים אמיתיים, schema validation עובר

### Phase E — SkillGap + TopicPrioritization
- SkillGapAgent (operational, עם coverage algorithm)
- TopicPrioritizationAgent (operational, עם composite score)
- Unit tests לרankign math ו-gap computation
- Pipeline orchestration (sequential)
- **Validation gate E:** פייפליין מלא רץ, ranked_topics נשמרים ב-DB

### Phase F — API Layer
- `GET /api/v1/opportunities`
- `GET /api/v1/opportunities/:id`
- `GET /api/v1/pipeline/status`
- `POST /api/v1/pipeline/trigger`
- `GET /readiness`
- Integration tests לכל routes
- **Validation gate F:** כל API endpoints מגיבים עם valid schema

### Phase G — Admin UI
- Dashboard עם KPI cards
- Opportunities list + detail
- Pipeline status page
- i18n setup (עברית + אנגלית)
- RTL layout
- **Validation gate G:** כל UI pages מציגות נתונים אמיתיים, locale switch עובד

### Phase H — QA & Release
- Review כל unit + integration tests
- Staging run עם נתונים אמיתיים
- Release gates checklist
- CLAUDE.md + docs review
- **Validation gate H:** כל release gates G1–G10 עוברים

---

## 12. מדיניות Partial Failure ב-Pipeline

**עיקרון:** פייפליין חלקי עדיף על פייפליין שנופל.

```
TrendAnalysisAgent נכשל
  → TopicPrioritizationAgent ממשיך עם job_demand + gap בלבד
  → ranked_topics נשמרים עם signal_coverage = {"trend": false}
  → API מחזיר results עם flag is_partial = true
  → UI מציג banner: "נתוני Trend לא זמינים לריצה זו"
```

**מה שלא מותר:**
- לשמור ranked_topics ב-DB ללא schema validation
- להציג scores שחושבו על בסיס נתונים פגומים ללא flagging
- לנסות לomit partial failure מה-logs
