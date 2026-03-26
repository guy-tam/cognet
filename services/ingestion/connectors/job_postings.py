"""
Job Postings Connector — מחבר stub ל-MVP.
בסביבת ייצור מתחבר ל-API של לוח דרושים או מקור נתונים מסוכל.
ל-MVP קורא מנתוני fixture סטטיים.

Trust Tier: Tier 2 (Medium Trust)
Source Type: job_postings
"""

import uuid
from datetime import datetime, timezone

from shared.contracts.raw_record import RawSourceRecord
from shared.enums.pipeline import SourceType
from shared.enums.signals import SourceTrustTier
from services.ingestion.base_connector import BaseConnector


# נתוני stub — מודעות משרה מציאותיות לבדיקה
_STUB_JOB_POSTINGS = [
    {
        "title": "Senior Data Engineer",
        "company": "TechCorp Israel",
        "location": "Tel Aviv, Israel",
        "skills": ["Python", "Apache Spark", "dbt", "Airflow", "SQL"],
        "description": (
            "We are looking for a Senior Data Engineer to design and build scalable "
            "data pipelines. Experience with cloud platforms (AWS/GCP) required."
        ),
        "posted_at": "2026-03-20T09:00:00Z",
        "country_code": "IL",
        "language_code": "en",
        "external_id": "job_001",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Startup Tel Aviv",
        "location": "Tel Aviv, Israel",
        "skills": ["Python", "PyTorch", "MLflow", "Docker", "Kubernetes"],
        "description": (
            "Join our ML team building production-grade models. "
            "Strong background in deep learning and model deployment required."
        ),
        "posted_at": "2026-03-21T10:30:00Z",
        "country_code": "IL",
        "language_code": "en",
        "external_id": "job_002",
    },
    {
        "title": "Cloud Architect",
        "company": "Enterprise Solutions Ltd",
        "location": "Herzliya, Israel",
        "skills": ["AWS", "Terraform", "Kubernetes", "Microservices", "Security"],
        "description": (
            "Design and implement cloud infrastructure for enterprise clients. "
            "AWS Solutions Architect certification preferred."
        ),
        "posted_at": "2026-03-22T08:00:00Z",
        "country_code": "IL",
        "language_code": "en",
        "external_id": "job_003",
    },
    {
        "title": "Product Manager - EdTech",
        "company": "LearnCo",
        "location": "Remote, Israel",
        "skills": ["Product Strategy", "Agile", "Data Analysis", "User Research"],
        "description": (
            "Lead product development for our e-learning platform. "
            "Experience with EdTech products a strong advantage."
        ),
        "posted_at": "2026-03-23T11:00:00Z",
        "country_code": "IL",
        "language_code": "he",
        "external_id": "job_004",
    },
    {
        "title": "Cybersecurity Analyst",
        "company": "SecureIL",
        "location": "Beer Sheva, Israel",
        "skills": ["SIEM", "Threat Intelligence", "Penetration Testing", "Python"],
        "description": (
            "Monitor and protect organizational infrastructure from cyber threats. "
            "Experience with SOC operations required."
        ),
        "posted_at": "2026-03-24T07:30:00Z",
        "country_code": "IL",
        "language_code": "en",
        "external_id": "job_005",
    },
]


class JobPostingsConnector(BaseConnector):
    """מחבר stub למודעות משרה — מחזיר נתוני דוגמה ריאליסטיים."""

    source_name = "job_postings_stub"
    source_type = SourceType.job_postings
    trust_tier = "tier_2_medium"

    async def fetch(
        self, run_id: uuid.UUID, country_code: str = "IL", **kwargs
    ) -> list[dict]:
        """
        מחזיר נתוני stub של מודעות משרה.

        Args:
            run_id: מזהה ריצת ה-pipeline.
            country_code: קוד מדינה לסינון (ברירת מחדל: "IL").

        Returns:
            רשימת מילוני מודעות משרה גולמיים.
        """
        # סינון לפי country_code אם צוין
        return [
            posting
            for posting in _STUB_JOB_POSTINGS
            if posting.get("country_code") == country_code
        ]

    def parse(self, raw_item: dict, run_id: uuid.UUID) -> RawSourceRecord | None:
        """
        ממיר מילון מודעת משרה גולמית ל-RawSourceRecord.

        Args:
            raw_item: מילון הנתונים הגולמי.
            run_id: מזהה ריצת ה-pipeline.

        Returns:
            RawSourceRecord, או None אם הפריט אינו תקין.
        """
        # בדיקת שדות חובה
        if not raw_item.get("title") or not raw_item.get("company"):
            return None

        checksum = RawSourceRecord.compute_checksum(raw_item)

        return RawSourceRecord(
            source_name=self.source_name,
            source_type=self.source_type,
            external_id=raw_item.get("external_id"),
            collected_at=datetime.now(tz=timezone.utc),
            language_code=raw_item.get("language_code"),
            country_code=raw_item.get("country_code"),
            payload=raw_item,
            checksum=checksum,
            source_run_id=run_id,
            trust_tier=SourceTrustTier.tier_2_medium,
        )
