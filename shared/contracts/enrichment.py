"""
מודלי Pydantic עבור פלט העשרה — כישורים, נושאים, תפקידים ומטא-נתונים נוספים.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EnrichedSkillRef(BaseModel):
    """הפניה לכישור שזוהה בתהליך ההעשרה."""

    # מזהה הכישור במאגר הפנימי (אם קיים)
    skill_id: UUID | None = None

    # שם הכישור כפי שזוהה
    skill_name: str

    # רמת הביטחון בזיהוי (0 עד 1)
    confidence: float = Field(ge=0.0, le=1.0)

    # תווית המקור שממנו נגזר הכישור
    source_label: str | None = None


class EnrichedTopicRef(BaseModel):
    """הפניה לנושא שזוהה בתהליך ההעשרה."""

    # מזהה הנושא במאגר הפנימי (אם קיים)
    topic_id: UUID | None = None

    # שם הנושא
    topic_name: str

    # רמת הביטחון בזיהוי (0 עד 1)
    confidence: float = Field(ge=0.0, le=1.0)


class EnrichedRoleRef(BaseModel):
    """הפניה לתפקיד שזוהה בתהליך ההעשרה."""

    # מזהה התפקיד במאגר הפנימי (אם קיים)
    role_id: UUID | None = None

    # שם התפקיד
    role_name: str

    # רמת הביטחון בזיהוי (0 עד 1)
    confidence: float = Field(ge=0.0, le=1.0)


class EnrichmentOutput(BaseModel):
    """פלט מלא של תהליך ההעשרה עבור רשומה מנורמלת."""

    # מזהה הרשומה המנורמלת שעליה מתבססת ההעשרה
    normalized_record_id: UUID

    # רשימת כישורים שזוהו
    skills: list[EnrichedSkillRef] = []

    # רשימת נושאים שזוהו
    topics: list[EnrichedTopicRef] = []

    # רשימת תפקידים שזוהו
    roles: list[EnrichedRoleRef] = []

    # תעשיות רלוונטיות (שמות חופשיים)
    industries: list[str] = []

    # קודי מדינות רלוונטיות גיאוגרפית (ISO 3166-1 alpha-2)
    geographic_relevance: list[str] = []

    # הקשר שפתי (לדוגמה: "he-IL", "en-US")
    language_context: str | None = None

    # רמז ללמדותיות התוכן (0 עד 1) — עד כמה ניתן ללמד את הנושא
    teachability_hint: float | None = Field(default=None, ge=0.0, le=1.0)

    # ציון ביטחון כולל של תהליך ההעשרה (0 עד 1)
    enrichment_confidence: float = Field(ge=0.0, le=1.0)

    # זמן ביצוע ההעשרה
    enriched_at: datetime
