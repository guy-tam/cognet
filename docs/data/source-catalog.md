# Source Catalog — COGNET LDI Engine

## 1. עקרון מקורות הנתונים (Source Connector Principle)

כל מקורות הנתונים ב-COGNET LDI Engine מתחברים דרך אבסטרקציה תחומה (bounded abstraction). אין קוד שמדבר ישירות עם API חיצוני מחוץ לשכבת הקונקטור. כל קונקטור מממש ממשק אחיד, מדווח על שגיאות בצורה אחידה, ומפיק רשומות גולמיות לפי חוזה שדות קבוע.

**עקרונות ליבה:**
- כל קונקטור הוא יחידה עצמאית הניתנת לבדיקה בנפרד
- שינוי מקור חיצוני לא דורש שינויים בשכבות downstream
- כל קריאה לAPI חיצוני מתועדת עם run_id ייחודי
- כשל חלקי במקור לא מפיל את הפייפליין כולו
- תדירות עדכון ומגבלות rate limit מוגדרות per-source ולא globally

---

## 2. משפחות מקורות ראשוניות (Initial Source Families)

### 2.1 Job Postings — מודעות עבודה

**תיאור:** מקור ביקוש שוק העבודה — מייצג דרישות מיומנויות אמיתיות מהשוק. מהווה את האות החזק ביותר לצורכי למידה קיימים.

**מקורות ספציפיים:**
- LinkedIn Jobs API (כאשר גישה זמינה)
- Indeed Job Postings (scrape מוגדר לפי ToS)
- לוחות עבודה ספציפיים לאזור (e.g., AllJobs.co.il לישראל)

**שדות רשומה גולמית:**

| שדה | סוג | תיאור | חובה |
|-----|-----|--------|------|
| `external_id` | string | מזהה ייחודי במקור | כן |
| `title` | string | כותרת המשרה המקורית | כן |
| `description_raw` | text | תיאור מלא לא מנורמל | כן |
| `company_name` | string | שם המעסיק | לא |
| `company_size_bucket` | string | טווח גודל חברה (e.g., "50-200") | לא |
| `skills_mentioned_raw` | string[] | מיומנויות שהוזכרו בטקסט (pre-parse) | לא |
| `location_raw` | string | מיקום לא מנורמל כפי שהוזן | כן |
| `country_code` | string | ISO 3166-1 alpha-2 | כן |
| `region_code` | string | קוד אזור פנימי | לא |
| `employment_type` | string | full_time / part_time / contract | לא |
| `seniority_level` | string | entry / mid / senior / lead | לא |
| `salary_raw` | string | מידע שכר לא מנורמל | לא |
| `posted_at` | timestamp | תאריך פרסום המקורי | כן |
| `collected_at` | timestamp | זמן איסוף על ידי הקונקטור | כן |
| `language_code` | string | ISO 639-1 של תוכן הרשומה | כן |
| `industry_raw` | string | ענף כפי שדווח במקור | לא |
| `source_url` | string | URL המקורי (לאימות) | לא |

**Tier:** Tier 1

**נפח צפוי:** 5,000–50,000 משרות לאזור לחודש (תלוי בגישת API)

**מגבלות Rate Limit:**
- LinkedIn API: 100 קריאות ל-15 דקות (application-level)
- Scraping: אין לעלות על 1 בקשה לשניה, עם randomized delay של 2–5 שניות
- Indeed: לפי תנאי API הרשמי בלבד

**אסטרטגיית Backoff:** Exponential backoff, 3 ניסיונות מקסימום לפני רישום כשל ומעבר לרשומה הבאה

---

### 2.2 Trend / Search Signals — אותות טרנד וחיפוש

**תיאור:** מייצג ביקוש מבוסס עניין — מה אנשים מחפשים, מה עולה בפופולריות, אלו נושאים בעלייה ב-tech communities. אות משלים (לא ראשי) לביקוש שוק עבודה.

**מקורות ספציפיים:**
- Google Trends API (unofficial / SerpAPI wrapper)
- Stack Overflow Trends (דף ציבורי + חיפוש tag statistics)
- Twitter/X tech topics (trending hashtags בקטגוריית tech)

**שדות רשומה גולמית:**

| שדה | סוג | תיאור | חובה |
|-----|-----|--------|------|
| `external_id` | string | מזהה ייחודי (hash של query + window) | כן |
| `query_term` | string | מונח החיפוש המקורי | כן |
| `signal_type` | string | search_volume / trend_index / tag_popularity | כן |
| `value` | float | ערך האות (normalized 0–100 או count) | כן |
| `value_unit` | string | index / count / percent_change | כן |
| `time_window_start` | date | תחילת חלון הזמן | כן |
| `time_window_end` | date | סוף חלון הזמן | כן |
| `geo_scope` | string | global / country_code / region | כן |
| `country_code` | string | ISO 3166-1 alpha-2 (אם רלוונטי) | לא |
| `source_platform` | string | google_trends / stackoverflow / twitter_x | כן |
| `related_queries_raw` | string[] | שאילתות קשורות שהמקור החזיר | לא |
| `language_code` | string | שפת השאילתה | לא |
| `collected_at` | timestamp | זמן איסוף | כן |

**Tier:** Tier 2

**תדירות עדכון:**
- Google Trends: שבועית (נתונים יומיים זמינים אך בעלי noise גבוה)
- Stack Overflow: חודשית (tag statistics יציבים יחסית)
- Twitter/X: שבועית (volatile — להשתמש כאות משני בלבד)

**סוג האות:** relative_interest (לא volume מוחלט) — יש לנרמל לפני שימוש

**מגבלות Rate Limit:**
- Google Trends (SerpAPI): לפי plan, בדרך כלל 100 בקשות/חודש בחינמי
- Stack Overflow API: 10,000 בקשות ליום עם key

---

### 2.3 Internal Learning Supply / Course Inventory — מלאי קורסים פנימי

**תיאור:** ייצוג של ה-supply הפנימי של פלטפורמת Cognet. משמש ל-SkillGapAgent להשוות בין ביקוש שוק לבין מה שהפלטפורמה כבר מציעה.

**מקורות ספציפיים:**
- CSV export ממערכת ניהול הקורסים הפנימית
- Database export ישיר (read-only replica אם זמין)
- Manual seed file לסביבת פיתוח

**שדות רשומה גולמית:**

| שדה | סוג | תיאור | חובה |
|-----|-----|--------|------|
| `external_id` | string | מזהה קורס פנימי | כן |
| `title` | string | שם הקורס | כן |
| `description` | text | תיאור הקורס | לא |
| `skills_covered_raw` | string[] | מיומנויות שהקורס מכסה (כפי שתויגו ידנית) | לא |
| `topics_raw` | string[] | נושאים שתויגו לקורס | לא |
| `learning_format` | string | short_course / track / workshop / cert_prep | כן |
| `duration_hours` | float | משך הקורס בשעות | לא |
| `audience_segment` | string | קהל יעד מוצהר | לא |
| `language_code` | string | שפת הקורס | כן |
| `country_availability` | string[] | רשימת מדינות שהקורס זמין בהן | לא |
| `is_active` | boolean | האם הקורס פעיל כרגע | כן |
| `created_at` | date | תאריך יצירת הקורס | לא |
| `updated_at` | date | עדכון אחרון | לא |
| `price_tier` | string | free / paid / subscription | לא |
| `rating_avg` | float | דירוג ממוצע (0–5) | לא |
| `enrollment_count` | integer | מספר נרשמים | לא |

**Tier:** Tier 1 (מקור פנימי — אמינות גבוהה)

**אסטרטגיית רענון:**
- CSV/export: ידני, לפי דרישה של אדמין (trigger ידני ב-admin UI)
- DB replica: poll אחת ל-24 שעות בשעות לא-שיא
- אין לרוץ full-refresh תוך כדי pipeline פעיל אחר

---

## 3. חוזה ממשק קונקטור (Source Connector Interface Contract)

כל קונקטור חייב לממש את הממשק הבא. ב-Python:

```python
class SourceConnector(ABC):
    source_name: str          # מזהה קצר ייחודי, e.g., "linkedin_jobs_il"
    source_type: str          # job_postings | trend_signals | internal_supply
    source_version: str       # גרסת הקונקטור, לצורך audit

    @abstractmethod
    def fetch(self, params: FetchParams) -> FetchResult:
        """
        מביא רשומות גולמיות מהמקור.
        חייב לטפל ב-rate limits פנימית.
        מחזיר FetchResult עם records, run_id, ו-fetch_metadata.
        """
        ...

    @abstractmethod
    def parse(self, raw: Any) -> list[RawRecord]:
        """
        ממיר תגובת המקור לרשומות גולמיות סטנדרטיות.
        לא מבצע normalization — רק parse + validation בסיסי.
        """
        ...

    @abstractmethod
    def health_check(self) -> ConnectorHealth:
        """
        בדיקת זמינות ואימות credentials.
        חייב לרוץ תוך 5 שניות.
        """
        ...

    def on_failure(self, error: Exception, context: FetchContext) -> FailurePolicy:
        """
        ברירת מחדל: SKIP_AND_LOG.
        ניתן לעקוף לפי קונקטור (e.g., RETRY_WITH_BACKOFF).
        """
        return FailurePolicy.SKIP_AND_LOG
```

**מאפייני קונקטור נדרשים:**

| מאפיין | תיאור |
|--------|--------|
| `source_name` | מזהה string ייחודי, snake_case |
| `source_type` | אחד מ: `job_postings`, `trend_signals`, `internal_supply` |
| `fetch()` | מביא נתונים, מחזיר `FetchResult` |
| `parse()` | ממיר ל-`RawRecord[]` — ללא normalization |
| `health_check()` | בדיקת זמינות (max 5 שניות) |
| `on_failure()` | מדיניות כשל: `SKIP_AND_LOG` / `RETRY` / `HALT` |
| `rate_limit_notes` | docstring מתועד עם מגבלות ידועות |
| `testability_notes` | docstring עם הנחיות mock/fixture לבדיקות |
| `metadata_strategy` | כיצד מסומן run_id, checksums, ו-dedup key |

---

## 4. חוזה רשומה גולמית (Raw Record Contract)

כל רשומה שנכנסת לפייפליין חייבת לציית לסכמה הבאה:

```python
@dataclass
class RawRecord:
    source_name: str          # "linkedin_jobs_il"
    source_type: str          # "job_postings"
    external_id: str          # מזהה ייחודי במקור המקורי
    collected_at: datetime    # UTC timestamp של איסוף
    language_code: str        # ISO 639-1, e.g., "he", "en", "ar"
    country_code: str         # ISO 3166-1 alpha-2, e.g., "IL", "US"
    region_code: str | None   # קוד אזור פנימי (אופציונלי)
    payload: dict             # כל שדות המקור הספציפיים — unstructured
    checksum: str             # SHA-256 של payload לצורך dedup
    source_run_id: str        # UUID של ריצת הפייפליין שיצרה רשומה זו
```

**כללי RawRecord:**
- `external_id` + `source_name` = מפתח dedup ראשי
- `checksum` = SHA-256 של `json.dumps(payload, sort_keys=True)`
- אין לסנן שדות מ-`payload` בשלב זה — normalization מגיע אחר כך
- `collected_at` חייב להיות UTC תמיד

---

## 5. מפת דרכים למקורות עתידיים (Future Sources Roadmap)

| מקור | סוג | עדיפות | סטטוס |
|------|-----|---------|--------|
| Salary data (Glassdoor, levels.fyi) | compensation_signals | גבוה | לא-MVP |
| Labor statistics (BLS, CBS Israel) | macro_labor | בינוני | לא-MVP |
| Developer forum demand (Reddit r/learnprogramming) | forum_demand | בינוני | לא-MVP |
| Enterprise training demand (HR platform exports) | enterprise_demand | גבוה | לא-MVP |
| GitHub language trends | developer_activity | נמוך | לא-MVP |
| MOOC enrollment data (Coursera, edX public stats) | platform_demand | בינוני | לא-MVP |
| News/media signal (tech news volume) | media_signal | נמוך | לא-MVP |
| Conference & meetup topics | community_signal | נמוך | לא-MVP |

---

## 6. מדיניות הוספת מקור חדש (Source Addition Policy)

כדי להוסיף מקור חדש לפייפליין, המפתח חייב לספק:

**תיעוד נדרש לפני merge:**
1. **Source fact sheet** — שם, סוג, tier, תיאור קצר, URL או אזכור
2. **Schema spec** — כל שדות ה-payload, עם סוג ומינוח
3. **Rate limit notes** — כולל backoff strategy
4. **Legal/compliance note** — אישור שאיסוף מותר לפי ToS של המקור
5. **Connector implementation** — עם `fetch`, `parse`, `health_check`
6. **Unit tests** — לפחות בדיקת parse עם fixture מקורי ובדיקת health_check ב-mock
7. **Fixture file** — 5–20 רשומות לדוגמה (anonymized אם צריך)
8. **Seed records** — לסביבת בדיקה בלבד, לא production data

**תהליך אישור:**
- Pull request עם כל הנ"ל
- Review על ידי lead engineer
- אין להפעיל קונקטור חדש בפרודקשן ללא approval של legal note

---

## 7. Tier אמינות מקור (Source Trust Tiers)

| Tier | שם | קריטריונים | דוגמאות |
|------|----|------------|---------|
| **Tier 1** | High-Volume Reliable | API רשמי / מקור פנימי, SLA ידוע, schema יציב, coverage גבוה | LinkedIn API, internal course DB |
| **Tier 2** | Moderate | גישה לא-רשמית או עקיפה, signal חלש יותר, volume מוגבל, עלול להשתנות | Google Trends, Stack Overflow scrape |
| **Tier 3** | Experimental | ניסיוני, coverage נמוך, לא וולידטד, אסור להשפיע על ranking ב-MVP | Twitter/X topics, forum demand |

**כללי שימוש לפי tier:**
- Tier 1: רשאי לתרום ל-ranking signal עם weight מלא
- Tier 2: weight מוגבל (≤ 40% של composite score), חייב flagging ב-output
- Tier 3: לוגינג ו-monitoring בלבד ב-MVP, אין שימוש ב-ranking

---

## 8. שיקולים משפטיים ורגולטוריים (Legal & Compliance Considerations)

### Job Postings
- **LinkedIn:** שימוש ב-API הרשמי בלבד. אסור לשמור data שנאספה דרך scraping ללא רשות מפורשת. Terms of Service אוסרים automated scraping ב-robots.txt.
- **Indeed:** יש לפעול לפי Indeed Publisher Program. לא לאחסן PII (שמות מגייסים, אימייל חברות).
- **גנרי:** לא לאחסן שמות מגייסים ספציפיים, emails, או phone numbers ממודעות. `company_name` מותר.

### Trend / Search Signals
- **Google Trends:** נתונים ציבוריים, לא מצריכים attribution מיוחד. שימוש commercial דורש בדיקת ToS של Google.
- **Stack Overflow:** נתוני tag statistics ציבוריים תחת CC-BY-SA. attribution נדרש.
- **Twitter/X:** API terms משתנים תכופות. לא לאחסן tweet content. אות aggregated בלבד.

### Internal Supply
- **Course inventory:** נתונים פנימיים — אין מגבלות משפטיות חיצוניות.
- **Enrollment data:** אסור לכלול PII של לומדים. Aggregate metrics בלבד.

### כללי GDPR / Privacy
- אין לאחסן שמות מועמדים מהמשרות
- Job posting data נאסף ב-aggregate לצורך intelligence בלבד
- כל raw records עם potential PII חייבים scrubbing לפני אחסון ארוך-טווח

---

## 9. סיכום מבנה הקובץ הנדרש (Source Catalog File Structure)

```
ingestion/
  connectors/
    base.py                    # SourceConnector ABC + RawRecord dataclass
    job_postings/
      linkedin_connector.py    # Tier 1
      indeed_connector.py      # Tier 1
      alljobs_il_connector.py  # Tier 2 (ישראל ספציפי)
    trend_signals/
      google_trends_connector.py   # Tier 2
      stackoverflow_connector.py   # Tier 2
      twitter_x_connector.py       # Tier 3
    internal_supply/
      csv_connector.py         # Tier 1
      db_replica_connector.py  # Tier 1
  fixtures/
    linkedin_sample.json       # 10 משרות לדוגמה
    google_trends_sample.json  # 5 trend records לדוגמה
    internal_courses_sample.csv
```
