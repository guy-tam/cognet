"""סכמות תגובה למצב Pipeline."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PipelineStatusResponse(BaseModel):
    """מצב הרצת ה-Pipeline הנוכחית או האחרונה."""

    # מזהה הרצה
    pipeline_run_id: UUID | None = Field(default=None, description="מזהה ייחודי של הרצת ה-Pipeline")

    # מצב
    status: str = Field(
        description="מצב הרצה: pending / running / completed / failed / cancelled"
    )

    # זמנים
    started_at: datetime | None = Field(default=None, description="זמן תחילת הרצה")
    ended_at: datetime | None = Field(default=None, description="זמן סיום הרצה")

    # פרטי שלבים
    step_summaries: list[dict] = Field(
        default_factory=list,
        description="סיכום כל שלב בהרצה — שם, מצב, מספר רשומות שעובדו",
    )

    # סטטיסטיקות
    error_count: int = Field(default=0, description="מספר שגיאות שהתרחשו במהלך הרצה")

    # הרצה אחרונה מוצלחת
    last_successful_run: datetime | None = Field(
        default=None,
        description="זמן הרצה אחרונה שהסתיימה בהצלחה",
    )
