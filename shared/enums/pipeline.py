"""
אנומים עבור תהליכי pipeline — סטטוסים, סוגי מקורות ומצבי נרמול.
"""

from enum import Enum


class PipelineStatus(str, Enum):
    """מצב ריצת ה-pipeline."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    partial = "partial"


class SourceType(str, Enum):
    """סוג מקור נתונים בתהליך האיסוף."""

    job_postings = "job_postings"
    trend_signals = "trend_signals"
    internal_supply = "internal_supply"


class NormalizationStatus(str, Enum):
    """מצב תהליך הנרמול של רשומה."""

    pending = "pending"
    normalized = "normalized"
    failed = "failed"
    skipped = "skipped"


class RecordStatus(str, Enum):
    """מצב רשומה לאורך מחזור חייה בפייפליין."""

    raw = "raw"
    normalized = "normalized"
    enriched = "enriched"
    processed = "processed"
    error = "error"
