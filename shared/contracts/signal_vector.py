"""
מודלי Pydantic עבור וקטור אותות — ציוני ביקוש, צמיחה ורלוונטיות לפי ישות.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from shared.enums.signals import SignalEntityType


class ScoreBreakdown(BaseModel):
    """פירוט הציונים המרכיבים את ההזדמנות לפי ממדים שונים."""

    # ציון ביקוש כללי לתוכן (0 עד 1)
    demand_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # ציון צמיחה — מגמת עלייה לאורך זמן (0 עד 1)
    growth_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # ציון שוק התעסוקה — כמות מודעות משרה רלוונטיות (0 עד 1)
    job_market_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # ציון מגמות — רלוונטיות לטרנדים עדכניים (0 עד 1)
    trend_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # ציון פער תוכן — עד כמה קיים חסר בהיצע הלמידה (0 עד 1)
    content_gap_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # ציון התאמה לוקאלית — רלוונטיות לשוק/שפה ספציפיים (0 עד 1)
    localization_fit_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # ציון למדותיות — עד כמה ניתן לבנות תוכן לימודי (0 עד 1)
    teachability_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # ציון התאמה אסטרטגית — עד כמה מתיישב עם יעדי הארגון (0 עד 1)
    strategic_fit_score: float = Field(default=0.0, ge=0.0, le=1.0)


class SignalVector(BaseModel):
    """וקטור אותות מצטבר עבור ישות מסוימת בהקשר גיאוגרפי/שפתי."""

    # סוג הישות (כישור, נושא, תפקיד, תעשייה)
    entity_type: SignalEntityType

    # מזהה הישות במאגר הפנימי (אופציונלי — ייתכן שטרם שויך)
    entity_id: UUID | None = None

    # שם הישות
    entity_name: str

    # קוד מדינה לפי ISO 3166-1 alpha-2
    country_code: str

    # קוד שפה לפי ISO 639-1
    language_code: str

    # פירוט הציונים לפי ממד
    scores: ScoreBreakdown

    # ציון ביטחון כולל בחישוב הוקטור (0 עד 1)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)

    # מספר ראיות שתרמו לחישוב
    evidence_count: int = 0

    # משפחות מקורות שתרמו לוקטור (לדוגמה: ["job_postings", "trend_signals"])
    source_families: list[str] = []

    # מזהה ריצת ה-pipeline שחישבה את הוקטור
    run_id: UUID

    # זמן חישוב הוקטור
    computed_at: datetime
