"""
פונקציות עזר לניהול זמן — UTC ופורמט ISO 8601.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """
    מחזיר את הזמן הנוכחי ב-UTC עם tzinfo מוגדר.

    Returns:
        datetime עם tzinfo=UTC.
    """
    return datetime.now(tz=timezone.utc)


def to_iso_string(dt: datetime) -> str:
    """
    ממיר datetime למחרוזת ISO 8601.

    Args:
        dt: אובייקט datetime (מומלץ עם tzinfo).

    Returns:
        מחרוזת בפורמט ISO 8601 (לדוגמה: "2026-03-26T10:30:00+00:00").
    """
    return dt.isoformat()
