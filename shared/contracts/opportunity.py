"""
מודלי Pydantic עבור הזדמנויות תוכן — ראיות, תקצירי הזדמנות ומטא-נתוני ציון.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from shared.enums.opportunity import (
    AudienceSegment,
    OpportunityClassification,
    OpportunityLifecycleState,
    RecommendedFormat,
)
from shared.contracts.signal_vector import ScoreBreakdown


class EvidenceItem(BaseModel):
    """פריט ראיה בודד התומך בהמלצת ההזדמנות."""

    # סוג המקור (לדוגמה: "job_posting", "trend_signal")
    source_type: str

    # הפניה ספציפית למקור (URL, מזהה רשומה וכדומה)
    source_reference: str

    # תקציר הראיה בלשון טבעית
    evidence_summary: str

    # משקל הראיה בחישוב הציון (0 עד 1, ברירת מחדל: 0.5)
    evidence_weight: float = Field(default=0.5, ge=0.0, le=1.0)


class OpportunityBrief(BaseModel):
    """תקציר הזדמנות תוכן — מודל מרכזי המייצג הזדמנות שזוהתה."""

    # מזהה ייחודי — נקבע בעת שמירה לבסיס הנתונים
    id: UUID | None = None

    # מזהה הנושא הקנוני במאגר (אם מקושר)
    topic_id: UUID | None = None

    # שם הנושא הקנוני
    canonical_topic_name: str

    # קוד מדינה לפי ISO 3166-1 alpha-2
    country_code: str

    # קוד אזור (אופציונלי)
    region_code: str | None = None

    # קוד שפה לפי ISO 639-1
    language_code: str

    # פילוח קהל היעד
    audience_segment: AudienceSegment

    # פורמט תוכן מומלץ
    recommended_format: RecommendedFormat

    # ציון הזדמנות מצטבר (0 עד 1)
    opportunity_score: float = Field(ge=0.0, le=1.0)

    # פירוט הציונים לפי ממד
    score_breakdown: ScoreBreakdown

    # הסבר קצר מדוע ההזדמנות רלוונטית כעת
    why_now_summary: str

    # רשימת ראיות התומכות בהמלצה
    evidence: list[EvidenceItem] = []

    # ציון ביטחון כולל (0 עד 1)
    confidence_score: float = Field(ge=0.0, le=1.0)

    # סיווג ההזדמנות לפי עדיפות
    classification: OpportunityClassification

    # מצב מחזור החיים — ברירת מחדל: surfaced (עלה לפני כן)
    lifecycle_state: OpportunityLifecycleState = OpportunityLifecycleState.surfaced

    # מזהה ריצת ה-pipeline שיצרה את ההזדמנות
    run_id: UUID

    # זמן יצירת ההזדמנות
    created_at: datetime
