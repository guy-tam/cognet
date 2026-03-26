"""
Internal Supply Connector — מחבר stub להיצע למידה פנימי.
בסביבת ייצור מתחבר ל-LMS API או מאגר תוכן פנימי.
ל-MVP מחזיר נתוני fixture סטטיים.

Trust Tier: Tier 2 (Medium Trust)
Source Type: internal_supply
"""

import uuid
from datetime import datetime, timezone

from shared.contracts.raw_record import RawSourceRecord
from shared.enums.pipeline import SourceType
from shared.enums.signals import SourceTrustTier
from services.ingestion.base_connector import BaseConnector


# נתוני stub — נכסי למידה פנימיים מציאותיים לבדיקה
_STUB_INTERNAL_SUPPLY = [
    {
        "title": "Introduction to Python Programming",
        "topics": ["Python", "programming basics", "data structures"],
        "skills": ["Python", "scripting", "problem solving"],
        "format": "short_course",
        "language": "en",
        "status": "published",
        "coverage_level": 0.9,
        "external_id": "supply_001",
        "duration_hours": 8,
    },
    {
        "title": "SQL for Data Analysis",
        "topics": ["SQL", "databases", "data analysis", "querying"],
        "skills": ["SQL", "PostgreSQL", "data manipulation"],
        "format": "short_course",
        "language": "en",
        "status": "published",
        "coverage_level": 0.85,
        "external_id": "supply_002",
        "duration_hours": 6,
    },
    {
        "title": "Agile Product Management Fundamentals",
        "topics": ["agile", "scrum", "product management", "roadmap"],
        "skills": ["Agile", "Scrum", "backlog management", "stakeholder communication"],
        "format": "workshop",
        "language": "he",
        "status": "published",
        "coverage_level": 0.7,
        "external_id": "supply_003",
        "duration_hours": 4,
    },
    {
        "title": "Cloud Fundamentals: AWS",
        "topics": ["cloud computing", "AWS", "infrastructure"],
        "skills": ["AWS", "EC2", "S3", "cloud architecture"],
        "format": "learning_track",
        "language": "en",
        "status": "draft",
        "coverage_level": 0.4,
        "external_id": "supply_004",
        "duration_hours": 20,
    },
    {
        "title": "Cybersecurity Awareness",
        "topics": ["cybersecurity", "information security", "phishing"],
        "skills": ["security awareness", "threat recognition"],
        "format": "short_course",
        "language": "en",
        "status": "published",
        "coverage_level": 0.5,
        "external_id": "supply_005",
        "duration_hours": 2,
    },
]


class InternalSupplyConnector(BaseConnector):
    """מחבר stub להיצע למידה פנימי — מחזיר נתוני נכסי למידה לדוגמה."""

    source_name = "internal_supply_stub"
    source_type = SourceType.internal_supply
    trust_tier = "tier_2_medium"

    async def fetch(self, run_id: uuid.UUID, **kwargs) -> list[dict]:
        """
        מחזיר נתוני stub של נכסי למידה פנימיים.

        Args:
            run_id: מזהה ריצת ה-pipeline.

        Returns:
            רשימת מילוני נכסי למידה גולמיים.
        """
        # מחזיר את כל נכסי הלמידה — אין סינון לפי מדינה (תוכן פנימי גלובלי)
        return list(_STUB_INTERNAL_SUPPLY)

    def parse(self, raw_item: dict, run_id: uuid.UUID) -> RawSourceRecord | None:
        """
        ממיר מילון נכס למידה גולמי ל-RawSourceRecord.

        Args:
            raw_item: מילון הנתונים הגולמי.
            run_id: מזהה ריצת ה-pipeline.

        Returns:
            RawSourceRecord, או None אם הפריט אינו תקין.
        """
        # בדיקת שדות חובה
        if not raw_item.get("title") or not raw_item.get("format"):
            return None

        checksum = RawSourceRecord.compute_checksum(raw_item)

        # נכסים פנימיים — שפה מתוך שדה "language", אין קוד מדינה ספציפי
        return RawSourceRecord(
            source_name=self.source_name,
            source_type=self.source_type,
            external_id=raw_item.get("external_id"),
            collected_at=datetime.now(tz=timezone.utc),
            language_code=raw_item.get("language"),
            country_code=None,
            payload=raw_item,
            checksum=checksum,
            source_run_id=run_id,
            trust_tier=SourceTrustTier.tier_2_medium,
        )
