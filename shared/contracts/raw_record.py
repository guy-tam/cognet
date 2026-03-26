"""
מודל Pydantic עבור רשומה גולמית ממקור נתונים — לפני כל עיבוד.
"""

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from shared.enums.pipeline import SourceType
from shared.enums.signals import SourceTrustTier


class RawSourceRecord(BaseModel):
    """רשומה גולמית כפי שהגיעה ממקור הנתונים, לפני נרמול."""

    # מזהה ייחודי — נקבע בעת שמירה לבסיס הנתונים
    id: UUID | None = None

    # שם המקור שממנו נאסף הנתון (לדוגמה: "linkedin_jobs", "coursera_trends")
    source_name: str

    # סוג המקור לפי טקסונומיה
    source_type: SourceType

    # מזהה חיצוני של הרשומה אצל המקור המקורי
    external_id: str | None = None

    # זמן האיסוף בפועל
    collected_at: datetime

    # קוד שפה לפי ISO 639-1 (לדוגמה: "en", "he")
    language_code: str | None = None

    # קוד מדינה לפי ISO 3166-1 alpha-2 (לדוגמה: "US", "IL")
    country_code: str | None = None

    # קוד אזור גיאוגרפי (לדוגמה: "tel_aviv", "new_york")
    region_code: str | None = None

    # הנתון הגולמי כפי שהגיע מהמקור
    payload: dict[str, Any]

    # טביעת אצבע SHA-256 של ה-payload — לזיהוי כפילויות
    checksum: str

    # מזהה ריצת המקור שבמסגרתה נאספה הרשומה
    source_run_id: UUID

    # רמת אמינות המקור — ברירת מחדל: בינונית
    trust_tier: SourceTrustTier = SourceTrustTier.tier_2_medium

    @classmethod
    def compute_checksum(cls, payload: dict[str, Any]) -> str:
        """מחשב SHA-256 hex digest של ה-payload לאחר סדרת המפתחות."""
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
