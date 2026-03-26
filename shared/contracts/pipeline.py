"""
מודלי Pydantic עבור סיכומי ריצות pipeline — ברמת הריצה הכוללת וברמת מקור בודד.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from shared.enums.pipeline import PipelineStatus, SourceType


class PipelineRunSummary(BaseModel):
    """סיכום ריצת pipeline שלמה — כולל כל השלבים."""

    # מזהה ריצת ה-pipeline
    pipeline_run_id: UUID

    # זמן תחילת הריצה
    started_at: datetime

    # זמן סיום הריצה (None אם עדיין רץ)
    ended_at: datetime | None = None

    # סטטוס כולל של הריצה
    status: PipelineStatus

    # סיכומים לפי שלב בריצה
    step_summaries: list[dict[str, Any]] = []

    # מספר שגיאות שהתרחשו במהלך הריצה
    error_count: int = 0

    # מטא-נתונים נוספים (גמיש)
    metadata: dict[str, Any] = {}


class SourceRunSummary(BaseModel):
    """סיכום ריצת איסוף ממקור נתונים בודד."""

    # מזהה ריצת המקור
    run_id: UUID

    # שם המקור שממנו אספנו
    source_name: str

    # סוג המקור
    source_type: SourceType

    # זמן תחילת האיסוף
    started_at: datetime

    # זמן סיום האיסוף (None אם עדיין רץ)
    ended_at: datetime | None = None

    # סטטוס ריצת המקור
    status: PipelineStatus

    # מספר רשומות שנאספו
    record_count: int

    # מספר שגיאות שהתרחשו
    error_count: int
