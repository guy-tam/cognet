"""סכמות תגובה משותפות לכל ה-API."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# טיפוס גנרי לתגובות מדורגות
T = TypeVar("T")


class HealthResponse(BaseModel):
    """תגובת בדיקת חיות (liveness) של השירות."""

    status: str = Field(description="מצב השירות — תמיד 'ok' אם הוא עונה")
    timestamp: datetime = Field(description="חותמת זמן UTC של התגובה")


class ReadinessResponse(BaseModel):
    """תגובת בדיקת מוכנות (readiness) — כולל מצב רכיבי תשתית."""

    status: str = Field(description="מצב כללי: ok / degraded / unavailable")
    database: str = Field(description="מצב חיבור מסד הנתונים: ok / unavailable")
    redis: str = Field(description="מצב חיבור Redis: ok / unavailable")
    last_pipeline_run: str | None = Field(
        default=None,
        description="זמן הרצת Pipeline אחרונה (ISO 8601) או null אם לא רצה עדיין",
    )
    timestamp: datetime = Field(description="חותמת זמן UTC של התגובה")


class ErrorDetail(BaseModel):
    """פרטי שגיאה ספציפית."""

    code: str = Field(description="קוד שגיאה מובנה, למשל: VALIDATION_ERROR")
    message: str = Field(description="תיאור קריא לאנוש של השגיאה")
    request_id: str | None = Field(default=None, description="מזהה הבקשה לצורך מעקב בלוגים")


class ErrorResponse(BaseModel):
    """מבנה אחיד לכל תגובות השגיאה ב-API."""

    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """תגובה מדורגת גנרית המבוססת על cursor pagination."""

    items: list[T] = Field(description="רשימת הפריטים בדף הנוכחי")
    total: int = Field(description="סך כל הפריטים התואמים לפילטר")
    next_cursor: str | None = Field(default=None, description="cursor למעבר לדף הבא")
    prev_cursor: str | None = Field(default=None, description="cursor למעבר לדף הקודם")
