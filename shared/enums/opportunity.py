"""
אנומים עבור הזדמנויות תוכן — סיווג, מחזור חיים, פורמטים וקהלי יעד.
"""

from enum import Enum


class OpportunityClassification(str, Enum):
    """סיווג הזדמנות לפי עדיפות ורלוונטיות."""

    immediate = "immediate"
    near_term = "near_term"
    watchlist = "watchlist"
    low_priority = "low_priority"
    rejected = "rejected"
    archived = "archived"


class OpportunityLifecycleState(str, Enum):
    """מצב מחזור החיים של הזדמנות במערכת."""

    draft = "draft"
    surfaced = "surfaced"
    analyst_review = "analyst_review"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"


class RecommendedFormat(str, Enum):
    """פורמט תוכן מומלץ עבור ההזדמנות."""

    short_course = "short_course"
    learning_track = "learning_track"
    workshop = "workshop"
    certification_prep = "certification_prep"
    project_based = "project_based"


class AudienceSegment(str, Enum):
    """פילוח קהל היעד של ההזדמנות."""

    student = "student"
    early_career = "early_career"
    mid_career = "mid_career"
    senior = "senior"
    career_changer = "career_changer"
    enterprise_learner = "enterprise_learner"
