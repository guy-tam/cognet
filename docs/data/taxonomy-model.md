# Taxonomy Model — COGNET LDI Engine

## 1. עיקרון הטקסונומיה

הטקסונומיה של COGNET LDI היא שכבת normalization מרכזית שמאפשרת השוואה בין מקורות שונים. ללא טקסונומיה משותפת, "Python" במשרה אחת ו-"python programming" בקורס אחר הם שני ישויות נפרדות — עם טקסונומיה הן אותה יחידה.

**עקרונות עיצוב:**
- **MVP-practical:** טבלאות פשוטות + alias lookups — לא ontology מורכבת
- **Source-agnostic normalization:** כל מקור ממפה ל-canonical IDs בלבד
- **Deliberate governance:** שינויים בטקסונומיה עוברים תהליך, לא נעשים ad-hoc
- **Extensible, not over-engineered:** קל להוסיף entities חדשות בלי לשבור את הקיים
- **Seed-first:** הטקסונומיה מתחילה עם seed data קטן ומדויק, לא עם ניסיון לכסות הכל

---

## 2. משפחות ישויות קנוניות (Canonical Entity Families)

| Family | תיאור | טבלת DB |
|--------|--------|---------|
| `skill` | מיומנות טכנית או soft skill | `taxonomy_skills` |
| `topic` | נושא למידה רחב יותר ממיומנות | `taxonomy_topics` |
| `role` | תפקיד מקצועי בשוק עבודה | `taxonomy_roles` |
| `industry` | ענף תעשייתי | `taxonomy_industries` |
| `country` | מדינה (ISO codes) | `taxonomy_countries` |
| `region` | אזור גיאוגרפי (פנימי) | `taxonomy_regions` |
| `language` | שפה (ISO + מטה-דאטה RTL) | `taxonomy_languages` |
| `audience_segment` | פלח קהל לומדים | `taxonomy_audience_segments` |
| `learning_format` | פורמט מוצר למידה | `taxonomy_learning_formats` |

---

## 3. מבנה טקסונומיית מיומנויות (Skill Taxonomy)

### סכמה

```sql
CREATE TABLE taxonomy_skills (
    id              VARCHAR(64) PRIMARY KEY,   -- "skill_python", "skill_react"
    name            VARCHAR(255) NOT NULL,      -- שם קנוני: "Python"
    aliases         TEXT[],                     -- ["python3", "Python 3", "py"]
    category        VARCHAR(64),               -- "programming_language" | "framework" | "soft_skill" | ...
    parent_skill_id VARCHAR(64) REFERENCES taxonomy_skills(id),  -- nullable, לתת-מיומנויות
    source_labels   JSONB,                     -- {"linkedin": "Python (Programming Language)", "indeed": "python"}
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### דוגמאות ל-seed data

| id | name | aliases | category | parent_skill_id |
|----|------|---------|---------|----------------|
| `skill_python` | Python | python3, py, python programming | programming_language | null |
| `skill_django` | Django | django framework, django rest | framework | `skill_python` |
| `skill_react` | React | reactjs, react.js, react framework | framework | `skill_javascript` |
| `skill_sql` | SQL | structured query language, sql queries | data_querying | null |
| `skill_machine_learning` | Machine Learning | ml, machine-learning, ML engineering | ml_ai | null |
| `skill_data_analysis` | Data Analysis | data analytics, data analyst skills | data | null |
| `skill_communication` | Communication | communication skills, verbal communication | soft_skill | null |

### קטגוריות מיומנות

```
programming_language    — שפות תכנות (Python, Java, Go)
framework               — frameworks ו-libraries (React, Django, TensorFlow)
platform_tool           — כלים ופלטפורמות (AWS, Docker, Git)
data_querying           — שפות ופורמטים של נתונים (SQL, GraphQL)
ml_ai                   — מיומנויות AI/ML
soft_skill              — מיומנויות רכות (leadership, communication)
domain_knowledge        — ידע תחומי (finance, healthcare)
methodology             — מתודולוגיות (Agile, Scrum, DevOps)
data                    — עיבוד וניתוח נתונים כללי
security                — אבטחת מידע
design                  — UX/UI, product design
```

---

## 4. מבנה טקסונומיית נושאים (Topic Taxonomy)

נושאים רחבים יותר ממיומנויות ספציפיות — מייצגים תחומי למידה שלמים.

```sql
CREATE TABLE taxonomy_topics (
    id               VARCHAR(64) PRIMARY KEY,   -- "topic_web_dev", "topic_data_science"
    name             VARCHAR(255) NOT NULL,
    aliases          TEXT[],
    related_skills   VARCHAR(64)[],             -- FK לרשימת skill IDs
    related_roles    VARCHAR(64)[],             -- FK לרשימת role IDs
    audience_hints   VARCHAR(64)[],             -- audience_segments שרלוונטיים
    description      TEXT,
    is_active        BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);
```

### דוגמאות ל-seed data

| id | name | related_skills (sample) | audience_hints |
|----|------|------------------------|---------------|
| `topic_web_dev` | Web Development | skill_html, skill_css, skill_javascript, skill_react | student, early_career |
| `topic_data_science` | Data Science | skill_python, skill_sql, skill_machine_learning | mid_career, career_changer |
| `topic_devops` | DevOps & Cloud | skill_docker, skill_kubernetes, skill_aws | mid_career, senior |
| `topic_cybersecurity` | Cybersecurity | skill_network_security, skill_python, skill_linux | early_career, mid_career |
| `topic_product_management` | Product Management | skill_communication, skill_analytics | mid_career, career_changer |
| `topic_mobile_dev` | Mobile Development | skill_react_native, skill_swift, skill_kotlin | early_career, mid_career |

---

## 5. מבנה טקסונומיית תפקידים (Role Taxonomy)

```sql
CREATE TABLE taxonomy_roles (
    id              VARCHAR(64) PRIMARY KEY,   -- "role_backend_engineer"
    name            VARCHAR(255) NOT NULL,
    aliases         TEXT[],                     -- ["backend developer", "server-side engineer"]
    seniority_levels TEXT[],                   -- ["entry", "mid", "senior", "lead"]
    related_skills   VARCHAR(64)[],            -- מיומנויות נפוצות לתפקיד
    related_topics   VARCHAR(64)[],
    industry_context VARCHAR(64)[],            -- industry IDs שבהם תפקיד זה נפוץ
    is_active        BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);
```

### דוגמאות ל-seed data

| id | name | aliases (sample) | seniority_levels |
|----|------|-----------------|-----------------|
| `role_backend_engineer` | Backend Engineer | backend developer, server-side dev | entry, mid, senior, lead |
| `role_frontend_engineer` | Frontend Engineer | frontend developer, UI engineer | entry, mid, senior |
| `role_data_scientist` | Data Scientist | data science engineer, ML scientist | mid, senior |
| `role_devops_engineer` | DevOps Engineer | platform engineer, SRE, infrastructure engineer | mid, senior, lead |
| `role_product_manager` | Product Manager | PM, product owner | mid, senior, lead |
| `role_data_analyst` | Data Analyst | business analyst, analytics engineer | entry, mid, senior |
| `role_ml_engineer` | ML Engineer | machine learning engineer, AI engineer | mid, senior |
| `role_security_engineer` | Security Engineer | cybersecurity engineer, InfoSec engineer | mid, senior |

---

## 6. מבנה טקסונומיית תעשיות (Industry Taxonomy)

```sql
CREATE TABLE taxonomy_industries (
    id          VARCHAR(64) PRIMARY KEY,   -- "industry_fintech"
    name        VARCHAR(255) NOT NULL,
    aliases     TEXT[],
    parent_id   VARCHAR(64) REFERENCES taxonomy_industries(id),  -- nullable
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

### ערכים ראשוניים

| id | name | parent_id |
|----|------|-----------|
| `industry_tech` | Technology | null |
| `industry_fintech` | FinTech | `industry_tech` |
| `industry_healthtech` | HealthTech | `industry_tech` |
| `industry_edtech` | EdTech | `industry_tech` |
| `industry_finance` | Finance & Banking | null |
| `industry_healthcare` | Healthcare | null |
| `industry_retail` | Retail & E-commerce | null |
| `industry_manufacturing` | Manufacturing | null |
| `industry_government` | Government & Public Sector | null |

---

## 7. טקסונומיה גיאוגרפית (Geographic Taxonomy)

### מדינות

```sql
CREATE TABLE taxonomy_countries (
    code        CHAR(2) PRIMARY KEY,   -- ISO 3166-1 alpha-2
    name_en     VARCHAR(255) NOT NULL,
    name_he     VARCHAR(255),          -- שם בעברית
    region_id   VARCHAR(64),           -- FK לטבלת אזורים
    is_active   BOOLEAN DEFAULT TRUE
);
```

### אזורים פנימיים

```sql
CREATE TABLE taxonomy_regions (
    id          VARCHAR(64) PRIMARY KEY,  -- "region_mena", "region_emea"
    name        VARCHAR(255) NOT NULL,
    country_codes CHAR(2)[],             -- מדינות באזור זה
    description TEXT
);
```

### אזורים ראשוניים ל-MVP

| id | name | country_codes (sample) |
|----|------|----------------------|
| `region_il` | Israel | IL |
| `region_mena` | Middle East & North Africa | IL, AE, SA, EG, JO, MA |
| `region_emea` | Europe, Middle East & Africa | IL + EU + MENA |
| `region_us` | United States | US |
| `region_global` | Global (cross-region) | — |

---

## 8. טקסונומיית שפות (Language Taxonomy)

```sql
CREATE TABLE taxonomy_languages (
    code            CHAR(2) PRIMARY KEY,   -- ISO 639-1
    name_en         VARCHAR(64) NOT NULL,
    name_native     VARCHAR(64),           -- שם בשפה עצמה
    is_rtl          BOOLEAN DEFAULT FALSE,
    script_family   VARCHAR(32),           -- "latin", "arabic", "hebrew", "cyrillic"
    is_active       BOOLEAN DEFAULT TRUE
);
```

### ערכים ראשוניים

| code | name_en | name_native | is_rtl | script_family |
|------|---------|-------------|--------|---------------|
| `he` | Hebrew | עברית | true | hebrew |
| `ar` | Arabic | العربية | true | arabic |
| `en` | English | English | false | latin |
| `fr` | French | Français | false | latin |
| `es` | Spanish | Español | false | latin |
| `de` | German | Deutsch | false | latin |
| `pt` | Portuguese | Português | false | latin |
| `ru` | Russian | Русский | false | cyrillic |
| `zh` | Chinese | 中文 | false | cjk |

---

## 9. פלחי קהל (Audience Segments)

```sql
CREATE TABLE taxonomy_audience_segments (
    id          VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(128) NOT NULL,
    description TEXT,
    age_range   VARCHAR(32),    -- אינדיקטיבי בלבד
    is_active   BOOLEAN DEFAULT TRUE
);
```

### הגדרות

| id | name | תיאור |
|----|------|-------|
| `student` | Student | סטודנט בלימודים פורמליים (תיכון–תואר ראשון) |
| `early_career` | Early Career | 0–3 שנות ניסיון בתחום |
| `mid_career` | Mid-Career Professional | 3–10 שנות ניסיון, מחפש להתעדכן / להתמחות |
| `senior` | Senior Professional | 10+ שנות ניסיון, מעוניין ב-upskilling ממוקד |
| `career_changer` | Career Changer | בא ממקצוע אחר, רוצה להסב לתחום חדש |
| `enterprise_learner` | Enterprise Learner | לומד בתוך מסגרת ארגונית (L&D) |

---

## 10. פורמטי למידה (Learning Formats)

```sql
CREATE TABLE taxonomy_learning_formats (
    id          VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(128) NOT NULL,
    description TEXT,
    typical_duration_hours_min INT,
    typical_duration_hours_max INT,
    is_active   BOOLEAN DEFAULT TRUE
);
```

### הגדרות

| id | name | טווח שעות אופייני | תיאור |
|----|------|-------------------|-------|
| `short_course` | Short Course | 2–15 שעות | קורס ממוקד על נושא אחד |
| `learning_track` | Learning Track | 20–80 שעות | סדרת קורסים בנושא רחב |
| `workshop` | Workshop | 2–8 שעות | ניסיון מעשי מרוכז |
| `certification_prep` | Certification Prep | 10–40 שעות | הכנה לבחינת הסמכה |
| `project_based` | Project-Based Learning | 10–30 שעות | למידה דרך פרויקט מעשי |

---

## 11. גישה לטיפול בשמות חלופיים (Synonym / Alias Mapping)

### הבעיה

מקורות שונים מתייגים את אותה מיומנות בצורות שונות:
- LinkedIn: "Python (Programming Language)"
- Job posting: "python3"
- Internal course: "Python Programming"
- Google Trends query: "learn python"

### הפתרון ב-MVP

**שלב 1 — Lookup table:**
```sql
CREATE TABLE taxonomy_alias_map (
    alias           VARCHAR(255) NOT NULL,
    canonical_type  VARCHAR(32) NOT NULL,   -- "skill" | "topic" | "role"
    canonical_id    VARCHAR(64) NOT NULL,
    source_name     VARCHAR(64),            -- null = universal alias
    confidence      FLOAT DEFAULT 1.0,      -- 0–1
    PRIMARY KEY (alias, canonical_type, source_name)
);
```

**שלב 2 — Normalization function:**
```python
def normalize_label(label: str, entity_type: str, source_name: str) -> str | None:
    """
    מחזיר canonical_id עבור label נתון.
    מנסה: source-specific lookup → universal lookup → fuzzy match (Tier 2+).
    מחזיר None אם לא נמצא match.
    """
    normalized = label.strip().lower()
    # 1. חיפוש מדויק source-specific
    result = db.query(
        "SELECT canonical_id FROM taxonomy_alias_map "
        "WHERE alias = %s AND canonical_type = %s AND source_name = %s",
        (normalized, entity_type, source_name)
    )
    if result: return result.canonical_id
    # 2. חיפוש מדויק universal
    result = db.query(
        "SELECT canonical_id FROM taxonomy_alias_map "
        "WHERE alias = %s AND canonical_type = %s AND source_name IS NULL",
        (normalized, entity_type)
    )
    if result: return result.canonical_id
    # 3. חיפוש fuzzy — רק אם confidence > 0.85
    return fuzzy_lookup(normalized, entity_type)
```

---

## 12. גישת MVP לטקסונומיה

MVP strategy: **לא ontology, לא knowledge graph — טבלאות מנורמלות עם alias lookups.**

**מה שנכנס ל-MVP:**
- seed data של ~50 מיומנויות נפוצות (top skills לפי ישראל + גלובל)
- seed data של ~20 נושאים
- seed data של ~15 תפקידים
- alias table עם ~200 aliases ידניים נפוצים
- כל ה-ISO tables (שפות, מדינות)
- audience_segments ו-learning_formats כולן

**מה שלא נכנס ל-MVP:**
- Skill hierarchy עמוקה (parent_skill_id קיים בסכמה אך לא מאוכלס)
- Automatic taxonomy expansion מ-LLM
- Industry taxonomy מעבר ל-8 ערכי seed
- Semantic similarity matching

---

## 13. ממשל טקסונומיה (Taxonomy Governance)

### כללי שינוי

1. **הוספת entity חדשה:** מותר דרך migration script + PR review
2. **שינוי שם canonical:** מחייב migration + עדכון alias table + עדכון normalizer
3. **מחיקת entity:** אסור — רק `is_active = false`. שמירת ה-ID לנצח
4. **הוספת alias:** מותר ב-migration ישירה

### תהליך לשינויים גדולים (taxonomy refactor)
- Proposal בכתב ב-PR description
- בדיקה שכל existing records עדיין ניתנים לנרמול
- migration script הפיך (reversible)
- smoke test על dataset קיים לפני merge

### Source labels (source_labels בטבלת skills)
- שדה JSONB המתעד איך כל מקור מכנה את המיומנות
- מאפשר reverse-lookup לדיבוג
- מתעדכן בכל parse חדש שמוסיף label לא מוכר

---

## 14. אסטרטגיית Seed Data (Bootstrap Strategy)

### שלב 1 — טבלאות ISO
```bash
# ייבוא מ-pycountry או iso-codes package
python scripts/seed_iso_countries.py    # ~250 מדינות
python scripts/seed_iso_languages.py    # ~50 שפות נפוצות
```

### שלב 2 — skills ו-topics ראשוניים
```bash
python scripts/seed_skills.py           # מ-seed/skills.json (~50 records)
python scripts/seed_topics.py           # מ-seed/topics.json (~20 records)
python scripts/seed_roles.py            # מ-seed/roles.json (~15 records)
```

### שלב 3 — alias table
```bash
python scripts/seed_aliases.py          # מ-seed/aliases.csv (~200 aliases)
```

### מבנה קובץ seed/skills.json
```json
[
  {
    "id": "skill_python",
    "name": "Python",
    "aliases": ["python3", "py", "python programming", "python (programming language)"],
    "category": "programming_language",
    "parent_skill_id": null,
    "source_labels": {
      "linkedin": "Python (Programming Language)",
      "indeed": "python"
    }
  }
]
```

### כלל חשוב
- seed data הוא **starting point בלבד** — הוא לא מייצג coverage מלא
- כל entity שה-normalizer לא מוצא match עבורה → נרשמת ב-`normalization_misses` log
- כל 2 שבועות: review של ה-misses הנפוצים ביותר ← עדכון alias table
