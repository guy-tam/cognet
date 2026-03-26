"""
מודל Pydantic עבור רשומה מנורמלת — לאחר עיבוד הרשומה הגולמית.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from shared.enums.pipeline import NormalizationStatus, SourceType


class NormalizedRecord(BaseModel):
    """רשומה לאחר תהליך הנרמול — מוכנה להעשרה."""

    # מזהה ייחודי — נקבע בעת שמירה לבסיס הנתונים
    id: UUID | None = None

    # מזהה הרשומה הגולמית שממנה נגזרה רשומה זו
    raw_record_id: UUID

    # שם המקור המקורי
    source_name: str

    # סוג המקור
    source_type: SourceType

    # כותרת מנורמלת — אחידה ללא שפה ספציפית
    normalized_title: str

    # תוכן טקסטואלי מנורמל (אופציונלי)
    normalized_text: str | None = None

    # שפה קנונית לפי ISO 639-1
    canonical_language: str | None = None

    # מדינה קנונית לפי ISO 3166-1 alpha-2
    canonical_country: str | None = None

    # אזור קנוני
    canonical_region: str | None = None

    # סוג הרשומה: job_posting | trend_signal | learning_asset
    record_type: str

    # מפתח ייחודי לצורך כפילויות (hash דטרמיניסטי)
    dedup_key: str

    # סטטוס תהליך הנרמול
    normalization_status: NormalizationStatus

    # זמן יצירת הרשומה המנורמלת
    created_at: datetime

    # מזהה ריצת המקור המשויכת
    source_run_id: UUID
