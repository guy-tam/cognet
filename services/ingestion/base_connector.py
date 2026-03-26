"""
Base Source Connector — ממשק מופשט שכל מחבר מקור חייב לממש.
כל מחבר חייב להגדיר: source_name, source_type, fetch, parse, on_failure, metadata.
"""
import uuid
from abc import ABC, abstractmethod

from shared.contracts.raw_record import RawSourceRecord
from shared.enums.pipeline import SourceType, PipelineStatus


class BaseConnector(ABC):
    """מחלקת בסיס מופשטת לכל מחבר מקור נתונים."""

    # שם המחבר — חייב להיות מוגדר בתת-מחלקות
    source_name: str
    # סוג המקור לפי SourceType enum
    source_type: SourceType
    # רמת אמינות ברירת מחדל
    trust_tier: str = "tier_2_medium"

    @abstractmethod
    async def fetch(self, run_id: uuid.UUID, **kwargs) -> list[dict]:
        """שולף נתונים גולמיים מהמקור. מחזיר רשימת מילוני payload גולמי."""
        ...

    @abstractmethod
    def parse(self, raw_item: dict, run_id: uuid.UUID) -> RawSourceRecord | None:
        """מנתח פריט גולמי בודד ל-RawSourceRecord. מחזיר None אם לא ניתן לנתח."""
        ...

    def on_failure(self, error: Exception, context: dict) -> None:
        """מטפל בשגיאת fetch או parse. ניתן לדרוס לטיפול ספציפי למקור."""
        pass

    def get_metadata(self) -> dict:
        """מחזיר מטא-נתוני מקור לרשומת הריצה."""
        return {
            "source_name": self.source_name,
            "source_type": (
                self.source_type.value
                if hasattr(self.source_type, "value")
                else self.source_type
            ),
            "trust_tier": self.trust_tier,
        }

    async def run(
        self, run_id: uuid.UUID, **kwargs
    ) -> tuple[list[RawSourceRecord], list[Exception]]:
        """
        מריץ את מחזור fetch → parse המלא. מחזיר (records, errors).
        שגיאות נאספות ולא מועלות — הצלחה חלקית תקינה.

        Args:
            run_id: מזהה ריצת ה-pipeline.

        Returns:
            tuple של (רשימת RawSourceRecord, רשימת שגיאות).
        """
        records: list[RawSourceRecord] = []
        errors: list[Exception] = []

        try:
            raw_items = await self.fetch(run_id, **kwargs)
        except Exception as e:
            self.on_failure(e, {"stage": "fetch", "run_id": str(run_id)})
            return [], [e]

        for item in raw_items:
            try:
                record = self.parse(item, run_id)
                if record is not None:
                    records.append(record)
            except Exception as e:
                errors.append(e)
                self.on_failure(
                    e,
                    {
                        "stage": "parse",
                        "run_id": str(run_id),
                        "item": str(item)[:200],
                    },
                )

        return records, errors
