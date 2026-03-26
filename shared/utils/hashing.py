"""
פונקציות עזר לחישוב checksums, מפתחות dedup ויצירת מזהי ריצה.
"""

import hashlib
import json
import uuid
from typing import Any


def compute_payload_checksum(payload: dict[str, Any]) -> str:
    """
    מחשב SHA-256 hex digest של payload — ממוין לפי מפתח לצורך עקביות.

    Args:
        payload: מילון הנתונים הגולמי מהמקור.

    Returns:
        מחרוזת hex של ה-SHA-256 (64 תווים).
    """
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_dedup_key(
    source_type: str,
    external_id: str | None,
    normalized_title: str,
    country_code: str | None,
) -> str:
    """
    מחשב מפתח dedup דטרמיניסטי מהשדות המזהים של הרשומה.

    הפונקציה מאחדת את השדות למחרוזת קנונית ומחשבת SHA-256.
    ערכי None מוחלפים ב-"" לצורך עקביות.

    Args:
        source_type: סוג המקור (לדוגמה: "job_postings").
        external_id: מזהה חיצוני מהמקור (אופציונלי).
        normalized_title: כותרת מנורמלת של הרשומה.
        country_code: קוד מדינה לפי ISO 3166-1 alpha-2 (אופציונלי).

    Returns:
        מחרוזת hex של ה-SHA-256.
    """
    parts = [
        source_type or "",
        external_id or "",
        normalized_title,
        country_code or "",
    ]
    # מחבר בסיפ שלא ניתן לזיוף בשדות ריקים
    canonical = "|".join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_run_id() -> uuid.UUID:
    """
    יוצר מזהה ריצה ייחודי (UUID4).

    Returns:
        uuid.UUID חדש ואקראי.
    """
    return uuid.uuid4()
