# Agent System — COGNET LDI Engine

## 1. מודל הסוכנים (Agent Model)

ה-agents ב-COGNET LDI הם **רכיבים מומחים תחומים (bounded specialist components)** — לא swarms אוטונומיים, לא multi-agent chat systems, ולא AI שמקבל החלטות עצמאיות.

**הגדרה:** כל agent הוא פונקציה ניתנת לבדיקה עם inputs מוגדרים, outputs מוגדרים, ו-schema contract מוצהר. ה-agent אחראי על שלב ספציפי בפייפליין ה-intelligence.

**עקרונות ליבה:**
- **Bounded:** כל agent עושה דבר אחד ועושה אותו טוב
- **Testable:** כל agent ניתן לריצה בנפרד עם inputs מוק
- **Validated:** כל output עובר JSON schema validation לפני שימוש downstream
- **Fallback-safe:** כל agent מגדיר מה קורה כשהוא נכשל
- **Non-LLM by default:** LLM הוא כלי אופציונלי ותחום, לא הברירת מחדל

---

## 2. גבול Deterministic / LLM (Boundary Rule)

### כלל זהב

> **כל logic שניתן לכתוב כקוד דטרמיניסטי — יכתב כקוד דטרמיניסטי.**
> LLM משמש רק כאשר: (א) הבעיה דורשת language understanding, (ב) output מוגדר ב-schema, (ג) יש fallback אם LLM נכשל.

### שימושים מותרים ב-LLM
| שימוש | Agent | סיבה |
|--------|-------|-------|
| חילוץ skills מטקסט job description | JobDemandAgent | NLP extraction |
| זיהוי שפת תוכן | normalization layer | language detection |
| סיכום opportunity לתצוגה | LearningOpportunityAgent | text summarization |
| הצעת aliases לטקסונומיה | (כלי עזר פנימי) | label matching |

### שימושים אסורים ב-LLM
| שימוש אסור | סיבה |
|------------|-------|
| חישוב ranking score | חייב להיות reproducible + auditable |
| validations של schema | לוגיקה דטרמיניסטית |
| pipeline orchestration decisions | לא ל-LLM לקבוע flow |
| database writes ישירות | בטיחות + predictability |

---

## 3. חוזה ממשק Agent (Agent Interface Contract)

כל agent חייב לתעד את שדות הממשק הבאים:

```python
@dataclass
class AgentSpec:
    purpose: str              # תיאור חד-משפטי של מה ה-agent עושה
    ownership: str            # מי אחראי על ה-agent (squad/engineer)
    inputs: list[InputSpec]   # רשימת inputs: שם, סוג, חובה/אופציונלי
    outputs: list[OutputSpec] # רשימת outputs עם JSON schema reference
    dependencies: list[str]   # services/tables/agents שה-agent תלוי בהם
    schema_contracts: dict    # הפניות לסכמות input/output
    fallback_rules: str       # מה קורה בכשל: SKIP | PARTIAL | HALT
    retry_rules: RetryPolicy  # מספר ניסיונות, delay, conditions
    non_goals: list[str]      # מה ה-agent לא עושה (חשוב לתיחום)
```

### מדיניות Fallback

| מדיניות | משמעות |
|---------|---------|
| `SKIP` | ה-agent מדלג על הריצה, הפייפליין ממשיך |
| `PARTIAL` | ה-agent מחזיר תוצאה חלקית עם `is_partial: true` flag |
| `HALT` | ה-agent עוצר את הפייפליין ומדווח critical error |

---

## 4. שמונה מחלקות ה-Agents

---

### 4.1 MarketResearchAgent

**סטטוס MVP: SCAFFOLD ONLY**

**Purpose:** לאסוף ולמרכז insights גבוהי-רמה על שוק עבודה לפי אזור — macro trends, industry growth signals, hiring demand context.

**Inputs:**
- `region_id: str` — אזור גיאוגרפי לניתוח
- `industry_ids: list[str]` — (אופציונלי) מיקוד בענפים ספציפיים
- `time_window_days: int` — חלון זמן לניתוח (default: 90)

**Outputs:**
```json
{
  "agent": "MarketResearchAgent",
  "region_id": "region_il",
  "status": "scaffold",
  "data": null,
  "scaffold_note": "לא מומש ב-MVP"
}
```

**Non-goals:**
- לא מבצע job demand analysis ספציפי (זה JobDemandAgent)
- לא מחשב skill gaps

**Fallback:** `SKIP` — הפייפליין ממשיך ללא macro context

---

### 4.2 TrendAnalysisAgent

**סטטוס MVP: OPERATIONAL**

**Purpose:** ניתוח אותות trend/search לזיהוי נושאים ומיומנויות שבעלייה, לפי אזור ושפה.

**Inputs:**
```python
@dataclass
class TrendAnalysisInput:
    market_id: str              # "region_il", "region_us"
    language_code: str          # "he", "en"
    time_window_days: int       # 30, 60, 90
    topic_ids: list[str]        # נושאים לניתוח — None = כל הנושאים הפעילים
    min_data_points: int = 3    # מינימום נקודות נתון לתוצאה תקפה
```

**Outputs:**
```python
@dataclass
class TrendAnalysisOutput:
    agent: str = "TrendAnalysisAgent"
    run_id: str                     # UUID של ריצה זו
    market_id: str
    language_code: str
    computed_at: datetime
    trend_signals: list[TrendSignal]
    is_partial: bool = False
    coverage_note: str | None = None  # הסבר אם חסרים מקורות
```

```python
@dataclass
class TrendSignal:
    topic_id: str            # canonical topic ID
    skill_ids: list[str]     # canonical skill IDs קשורים
    trend_direction: str     # "rising" | "stable" | "declining"
    trend_score: float       # 0.0–1.0, normalized
    source_count: int        # כמה מקורות תרמו לאות זה
    confidence: float        # 0.0–1.0
    data_window_start: date
    data_window_end: date
    contributing_sources: list[str]  # source_names שתרמו
```

**Dependencies:**
- `normalized_trend_records` (DB table) — רשומות טרנד לאחר normalization
- `taxonomy_topics`, `taxonomy_skills` — לקשירת labels לcanonical IDs

**Schema Contract:** `schemas/agents/trend_analysis_output.json`

**Fallback:** `PARTIAL` — אם חסרים מקורות מסוימים, מחזיר תוצאה עם `is_partial: true` ו-`coverage_note`

**Retry Policy:** 2 ניסיונות, delay 5 שניות, רק עבור DB timeout errors

**Non-goals:**
- לא מנתח job postings
- לא מחשב skill gap
- לא מדרג הזדמנויות למידה

**LLM Usage:** אין — כל החישובים דטרמיניסטיים (aggregation, normalization, trend direction calc)

---

### 4.3 JobDemandAgent

**סטטוס MVP: OPERATIONAL**

**Purpose:** ניתוח ביקוש שוק עבודה ספציפי — אילו מיומנויות ותפקידים נדרשים בשוק לפי אזור, כמה, ובאיזה עוצמה.

**Inputs:**
```python
@dataclass
class JobDemandInput:
    market_id: str
    language_code: str
    time_window_days: int = 90
    skill_ids: list[str] | None = None   # None = כל המיומנויות
    role_ids: list[str] | None = None    # None = כל התפקידים
    min_job_count: int = 10              # מינימום משרות לחישוב demand signal
```

**Outputs:**
```python
@dataclass
class JobDemandOutput:
    agent: str = "JobDemandAgent"
    run_id: str
    market_id: str
    language_code: str
    computed_at: datetime
    skill_demand: list[SkillDemandSignal]
    role_demand: list[RoleDemandSignal]
    total_jobs_analyzed: int
    time_window_start: date
    time_window_end: date
    is_partial: bool = False
```

```python
@dataclass
class SkillDemandSignal:
    skill_id: str
    mention_count: int              # כמה משרות ציינו מיומנות זו
    job_coverage_pct: float        # אחוז המשרות שציינו מיומנות זו
    demand_score: float            # 0.0–1.0, normalized
    trend_direction: str           # "rising" | "stable" | "declining" (לעומת period קודם)
    seniority_distribution: dict   # {"entry": 0.3, "mid": 0.5, "senior": 0.2}
    top_industries: list[str]      # industry IDs שהמשרות שייכות אליהם
    confidence: float
```

**LLM Usage (מוגדר ואופציונלי):**
- חילוץ skills מ-job description כאשר `skills_mentioned_raw` ריק
- חייב להחזיר JSON עם `{"skills": [{"label": str, "confidence": float}]}`
- אם LLM נכשל → fallback ל-keyword matching בלבד

```python
def extract_skills_from_description(description: str) -> list[ExtractedSkill]:
    """
    מנסה LLM extraction. אם נכשל — keyword matching fallback.
    """
    try:
        return llm_extract_skills(description, schema=SKILL_EXTRACTION_SCHEMA)
    except LLMError:
        logger.warning("LLM extraction failed, falling back to keyword matching")
        return keyword_match_skills(description)
```

**Dependencies:**
- `normalized_job_records` (DB table)
- `taxonomy_skills`, `taxonomy_roles`, `taxonomy_industries`

**Fallback:** `PARTIAL` — מחזיר demand signals עבור מה שחושב, אפילו אם חלק נכשל

**Non-goals:**
- לא מנתח trend signals
- לא יודע מה קיים ב-supply הפנימי
- לא מחשב ranking של הזדמנויות

---

### 4.4 SkillGapAgent

**סטטוס MVP: OPERATIONAL**

**Purpose:** חישוב הפער בין ביקוש מיומנויות בשוק (מ-JobDemandAgent) לבין ה-supply הקיים בפלטפורמה הפנימית. מזהה היכן יש gap שדורש תוכן חדש או חיזוק.

**Inputs:**
```python
@dataclass
class SkillGapInput:
    market_id: str
    job_demand_output: JobDemandOutput   # output מ-JobDemandAgent
    internal_supply: list[CourseRecord]  # מ-normalized internal supply
    gap_threshold_pct: float = 0.3       # מתחת לכיסוי 30% = gap משמעותי
```

**Outputs:**
```python
@dataclass
class SkillGapOutput:
    agent: str = "SkillGapAgent"
    run_id: str
    market_id: str
    computed_at: datetime
    skill_gaps: list[SkillGap]
    coverage_summary: CoverageSummary
```

```python
@dataclass
class SkillGap:
    skill_id: str
    demand_score: float         # מ-JobDemandAgent
    supply_coverage: float      # 0.0–1.0 (כמה טוב הפלטפורמה מכסה את המיומנות)
    gap_score: float            # demand_score * (1 - supply_coverage)
    gap_severity: str           # "critical" | "moderate" | "low"
    courses_covering: list[str] # course IDs שמכסים את המיומנות (יכול להיות ריק)
    recommendation: str         # "create_new" | "enhance_existing" | "sufficient"

@dataclass
class CoverageSummary:
    total_skills_in_demand: int
    skills_well_covered: int       # supply_coverage >= 0.7
    skills_partially_covered: int  # 0.3 <= supply_coverage < 0.7
    skills_not_covered: int        # supply_coverage < 0.3
    overall_coverage_pct: float
```

**Gap Score Algorithm:**
```python
def compute_gap_score(demand_score: float, supply_coverage: float) -> float:
    """
    gap_score = demand_score * (1.0 - supply_coverage)
    ערכים: 0.0 (אין gap) עד 1.0 (ביקוש מקסימלי, אפס supply)
    """
    return round(demand_score * (1.0 - supply_coverage), 4)

def compute_supply_coverage(skill_id: str, courses: list[CourseRecord]) -> float:
    """
    מחשב כמה טוב מכוסה מיומנות לפי:
    - מספר קורסים שמתייגים את המיומנות (נרמול לפי מקסימום נצפה)
    - ציון קורסים (rating_avg)
    - enrollment count (proxy לאיכות)
    """
    covering = [c for c in courses if skill_id in c.skills_covered_canonical]
    if not covering:
        return 0.0
    coverage_raw = len(covering) / MAX_COURSES_PER_SKILL_SATURATION  # const = 5
    quality_boost = sum(c.rating_avg or 3.0 for c in covering) / (len(covering) * 5.0)
    return min(1.0, coverage_raw * 0.7 + quality_boost * 0.3)
```

**Fallback:** `PARTIAL` — מחזיר gaps עבור מיומנויות שחושבו

**Non-goals:**
- לא יודע מה ה-trend (זה TrendAnalysisAgent)
- לא מדרג הזדמנויות ספציפיות (זה TopicPrioritizationAgent)
- לא ממליץ על מחיר קורסים

---

### 4.5 RegionCultureFitAgent

**סטטוס MVP: SCAFFOLD ONLY**

**Purpose:** ניתוח התאמה תרבותית ואזורית — מה work in one region שונה מה work in another, אילו פורמטי למידה מועדפים, language preferences.

**Inputs:**
```python
@dataclass
class RegionCultureFitInput:
    region_id: str
    topic_ids: list[str]
    language_code: str
```

**Outputs (scaffold):**
```json
{
  "agent": "RegionCultureFitAgent",
  "status": "scaffold",
  "data": null
}
```

**Non-goals:**
- לא מחליף טקסונומיה גיאוגרפית
- לא מבצע translation

**Fallback:** `SKIP` — הפייפליין ממשיך ללא regional fit scoring

---

### 4.6 TopicPrioritizationAgent

**סטטוס MVP: OPERATIONAL**

**Purpose:** שילוב כל ה-signals (trend + job demand + skill gap) לדירוג נושאים לפי עדיפות — מה כדאי לבנות/לשפר ראשון.

**Inputs:**
```python
@dataclass
class TopicPrioritizationInput:
    market_id: str
    trend_output: TrendAnalysisOutput | None
    job_demand_output: JobDemandOutput
    skill_gap_output: SkillGapOutput
    weights: PrioritizationWeights | None = None  # None = default weights
```

```python
@dataclass
class PrioritizationWeights:
    job_demand_weight: float = 0.50   # ביקוש שוק עבודה
    trend_weight: float = 0.25        # אות טרנד
    gap_weight: float = 0.25          # skill gap פנימי
    # חובה: sum = 1.0
```

**Outputs:**
```python
@dataclass
class TopicPrioritizationOutput:
    agent: str = "TopicPrioritizationAgent"
    run_id: str
    market_id: str
    computed_at: datetime
    ranked_topics: list[RankedTopic]
    weights_used: PrioritizationWeights
    signal_coverage: dict   # אילו signals היו זמינים
```

```python
@dataclass
class RankedTopic:
    topic_id: str
    rank: int                    # 1 = highest priority
    composite_score: float       # 0.0–1.0
    job_demand_score: float
    trend_score: float | None    # None אם TrendAnalysisAgent לא רץ
    gap_score: float
    top_skill_gaps: list[str]    # skill IDs עם הגבוה gap_score
    rationale_summary: str | None  # טקסט קצר (LLM generated, אופציונלי)
```

**Composite Score Algorithm:**
```python
def compute_composite_score(
    job_demand: float,
    trend: float | None,
    gap: float,
    weights: PrioritizationWeights
) -> float:
    """
    אם trend חסר — מחדש weights יחסית בין job_demand ו-gap.
    """
    if trend is None:
        adjusted_job_w = weights.job_demand_weight / (weights.job_demand_weight + weights.gap_weight)
        adjusted_gap_w = weights.gap_weight / (weights.job_demand_weight + weights.gap_weight)
        return round(job_demand * adjusted_job_w + gap * adjusted_gap_w, 4)
    return round(
        job_demand * weights.job_demand_weight +
        trend * weights.trend_weight +
        gap * weights.gap_weight,
        4
    )
```

**LLM Usage (אופציונלי):**
- יצירת `rationale_summary` — משפט אחד המסביר מדוע נושא זה דורג גבוה
- Schema: `{"summary": string, "max_chars": 120}`
- אם LLM נכשל → `rationale_summary = null`, לא error

**Fallback:** `PARTIAL` — אם TrendAnalysisAgent לא רץ, ממשיך עם job_demand + gap בלבד

**Non-goals:**
- לא מחליט על budget להכנת קורסים
- לא מנהל content pipeline
- לא מייצר את תוכן הקורס

---

### 4.7 LearningOpportunityAgent

**סטטוס MVP: SCAFFOLD**

**Purpose:** המרת ranked topics ל-actionable learning opportunities — ספציפיות, עם metadata, מוכנות ל-display ב-API ו-UI.

**Outputs (scaffold):**
```json
{
  "agent": "LearningOpportunityAgent",
  "status": "scaffold",
  "data": null
}
```

**Non-goals ל-MVP:**
- לא מייצר content briefs
- לא מנהל approval workflows

**Fallback:** `SKIP`

---

### 4.8 ConsistencyValidationAgent

**סטטוס MVP: SCAFFOLD**

**Purpose:** בדיקות consistency cross-agent — האם outputs מ-agents שונים מסכימים, האם יש anomalies בולטות בתוצאות.

**Outputs (scaffold):**
```json
{
  "agent": "ConsistencyValidationAgent",
  "status": "scaffold",
  "data": null
}
```

**Fallback:** `SKIP`

---

## 5. Schema Validation חובה

כל agent output חייב לעבור JSON Schema validation לפני שנשמר ב-DB או מועבר ל-agent הבא.

```python
def validate_agent_output(output: dict, agent_name: str) -> None:
    """
    מעלה AgentOutputValidationError אם ה-schema לא תואם.
    לא ממשיך downstream אם validation נכשל.
    """
    schema_path = f"schemas/agents/{agent_name}_output.json"
    schema = load_json_schema(schema_path)
    try:
        jsonschema.validate(instance=output, schema=schema)
    except jsonschema.ValidationError as e:
        raise AgentOutputValidationError(
            agent=agent_name,
            field=e.json_path,
            message=str(e.message)
        )
```

**Schema files location:** `schemas/agents/`
- `trend_analysis_output.json`
- `job_demand_output.json`
- `skill_gap_output.json`
- `topic_prioritization_output.json`

---

## 6. Retry ו-Timeout Behavior

### מדיניות Retry (ברירת מחדל)

```python
@dataclass
class RetryPolicy:
    max_attempts: int = 2
    delay_seconds: float = 5.0
    backoff_factor: float = 2.0   # exponential
    retry_on: list[str] = field(default_factory=lambda: ["DBTimeout", "TransientError"])
    no_retry_on: list[str] = field(default_factory=lambda: ["ValidationError", "SchemaError"])
```

### Timeout Behavior

| Agent | Timeout | לאחר timeout |
|-------|---------|-------------|
| TrendAnalysisAgent | 60 שניות | PARTIAL output |
| JobDemandAgent | 120 שניות | PARTIAL output |
| SkillGapAgent | 30 שניות | PARTIAL output |
| TopicPrioritizationAgent | 30 שניות | HALT (critical agent) |

---

## 7. גישת Orchestration ל-MVP

**MVP orchestration: Sequential pipeline — אין event-driven, אין async message queue.**

```python
def run_intelligence_pipeline(params: PipelineParams) -> PipelineResult:
    """
    ריצה סדרתית פשוטה. כל agent מקבל את output של הקודם.
    """
    run_id = generate_run_id()
    logger.info("pipeline_start", run_id=run_id, market_id=params.market_id)

    # שלב 1: TrendAnalysisAgent
    trend_output = TrendAnalysisAgent().run(
        TrendAnalysisInput(market_id=params.market_id, ...)
    )

    # שלב 2: JobDemandAgent
    job_output = JobDemandAgent().run(
        JobDemandInput(market_id=params.market_id, ...)
    )

    # שלב 3: SkillGapAgent
    gap_output = SkillGapAgent().run(
        SkillGapInput(
            market_id=params.market_id,
            job_demand_output=job_output,
            internal_supply=load_supply(params.market_id)
        )
    )

    # שלב 4: TopicPrioritizationAgent
    priority_output = TopicPrioritizationAgent().run(
        TopicPrioritizationInput(
            market_id=params.market_id,
            trend_output=trend_output,
            job_demand_output=job_output,
            skill_gap_output=gap_output,
        )
    )

    return PipelineResult(run_id=run_id, prioritization=priority_output)
```

**מה שלא קיים ב-MVP:**
- Celery / task queue
- Event-driven triggers בין agents
- Parallel agent execution
- Agent memory / state persistence בין ריצות

---

## 8. Agent Registry

```python
AGENT_REGISTRY = {
    "MarketResearchAgent":        {"status": "scaffold", "class": MarketResearchAgent},
    "TrendAnalysisAgent":         {"status": "operational", "class": TrendAnalysisAgent},
    "JobDemandAgent":             {"status": "operational", "class": JobDemandAgent},
    "SkillGapAgent":              {"status": "operational", "class": SkillGapAgent},
    "RegionCultureFitAgent":      {"status": "scaffold", "class": RegionCultureFitAgent},
    "TopicPrioritizationAgent":   {"status": "operational", "class": TopicPrioritizationAgent},
    "LearningOpportunityAgent":   {"status": "scaffold", "class": LearningOpportunityAgent},
    "ConsistencyValidationAgent": {"status": "scaffold", "class": ConsistencyValidationAgent},
}
```
