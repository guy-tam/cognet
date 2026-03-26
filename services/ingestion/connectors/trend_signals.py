"""
Trend Signals Connector — מחבר stub לאותות מגמה.
בסביבת ייצור מתחבר ל-Google Trends API או מקור נתוני מגמה חיצוני.
ל-MVP מחזיר נתוני fixture סטטיים.

Trust Tier: Tier 2 (Medium Trust)
Source Type: trend_signals
"""

import uuid
from datetime import datetime, timezone

from shared.contracts.raw_record import RawSourceRecord
from shared.enums.pipeline import SourceType
from shared.enums.signals import SourceTrustTier
from services.ingestion.base_connector import BaseConnector


# נתוני stub — אותות מגמה מציאותיים לבדיקה
_STUB_TREND_SIGNALS = [
    {
        "keyword": "generative AI",
        "search_volume_index": 95,
        "trend_direction": "rising",
        "region": "Israel",
        "language_code": "en",
        "country_code": "IL",
        "captured_at": "2026-03-25T00:00:00Z",
        "external_id": "trend_001",
        "related_topics": ["LLM", "ChatGPT", "prompt engineering"],
    },
    {
        "keyword": "data engineering",
        "search_volume_index": 82,
        "trend_direction": "rising",
        "region": "Israel",
        "language_code": "en",
        "country_code": "IL",
        "captured_at": "2026-03-25T00:00:00Z",
        "external_id": "trend_002",
        "related_topics": ["dbt", "Apache Spark", "data pipelines"],
    },
    {
        "keyword": "cloud security",
        "search_volume_index": 74,
        "trend_direction": "stable",
        "region": "Israel",
        "language_code": "en",
        "country_code": "IL",
        "captured_at": "2026-03-25T00:00:00Z",
        "external_id": "trend_003",
        "related_topics": ["Zero Trust", "SASE", "CSPM"],
    },
    {
        "keyword": "machine learning operations",
        "search_volume_index": 68,
        "trend_direction": "rising",
        "region": "Israel",
        "language_code": "en",
        "country_code": "IL",
        "captured_at": "2026-03-25T00:00:00Z",
        "external_id": "trend_004",
        "related_topics": ["MLflow", "Kubeflow", "model monitoring"],
    },
    {
        "keyword": "product management",
        "search_volume_index": 61,
        "trend_direction": "stable",
        "region": "Israel",
        "language_code": "he",
        "country_code": "IL",
        "captured_at": "2026-03-25T00:00:00Z",
        "external_id": "trend_005",
        "related_topics": ["agile", "roadmap", "OKR"],
    },
]


class TrendSignalsConnector(BaseConnector):
    """מחבר stub לאותות מגמה — מחזיר נתוני דוגמה ריאליסטיים."""

    source_name = "trend_signals_stub"
    source_type = SourceType.trend_signals
    trust_tier = "tier_2_medium"

    async def fetch(
        self, run_id: uuid.UUID, country_code: str = "IL", **kwargs
    ) -> list[dict]:
        """
        מחזיר נתוני stub של אותות מגמה.

        Args:
            run_id: מזהה ריצת ה-pipeline.
            country_code: קוד מדינה לסינון (ברירת מחדל: "IL").

        Returns:
            רשימת מילוני אותות מגמה גולמיים.
        """
        return [
            signal
            for signal in _STUB_TREND_SIGNALS
            if signal.get("country_code") == country_code
        ]

    def parse(self, raw_item: dict, run_id: uuid.UUID) -> RawSourceRecord | None:
        """
        ממיר מילון אות מגמה גולמי ל-RawSourceRecord.

        Args:
            raw_item: מילון הנתונים הגולמי.
            run_id: מזהה ריצת ה-pipeline.

        Returns:
            RawSourceRecord, או None אם הפריט אינו תקין.
        """
        # בדיקת שדות חובה
        if not raw_item.get("keyword"):
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
