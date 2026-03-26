"""מודל SQLAlchemy לתצלומי אותות — ציוני ביקוש ומגמות לישויות."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, func
from app.db.types import PortableUUID, PortableJSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SignalSnapshot(Base):
    """
    תצלום אותות — מצב מחושב של ציוני ביקוש, צמיחה ומגמות
    עבור מיומנות או נושא בשפה ומדינה ספציפיות.
    """

    __tablename__ = "signal_snapshots"

    __table_args__ = (
        # אינדקס לשאילתות לפי שם ישות, מדינה ושפה
        Index("ix_signal_snapshots_entity_country_lang", "entity_name", "country_code", "language_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    # סוג הישות: skill / topic
    entity_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # מזהה הישות — UUID אם קיים בטקסונומיה, אחרת None
    entity_id: Mapped[uuid.UUID | None] = mapped_column(PortableUUID, nullable=True)
    # שם הישות לחיפוש מהיר ללא JOIN
    entity_name: Mapped[str] = mapped_column(String, nullable=False)
    country_code: Mapped[str] = mapped_column(String, nullable=False)
    language_code: Mapped[str] = mapped_column(String, nullable=False)

    # --- ציונות (0.0 עד 1.0) ---
    # ציון ביקוש כולל
    demand_score: Mapped[float] = mapped_column(Float, nullable=False)
    # ציון קצב צמיחה
    growth_score: Mapped[float] = mapped_column(Float, nullable=False)
    # ציון שוק עבודה
    job_market_score: Mapped[float] = mapped_column(Float, nullable=False)
    # ציון מגמה כללית
    trend_score: Mapped[float] = mapped_column(Float, nullable=False)
    # ציון פער תוכן — כמה צריך ואין
    content_gap_score: Mapped[float] = mapped_column(Float, nullable=False)
    # ציון התאמה לוקליזציה
    localization_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    # ציון ניתנות ללמד
    teachability_score: Mapped[float] = mapped_column(Float, nullable=False)
    # ציון התאמה אסטרטגית
    strategic_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    # ציון ביטחון בחישוב
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # מספר ראיות שתמכו בחישוב
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # משפחות המקורות שתרמו — רשימת strings
    source_families: Mapped[list] = mapped_column(PortableJSON, nullable=False, default=list)

    # מזהה הרצת הפייפליין שיצרה את הסנאפשוט
    run_id: Mapped[uuid.UUID] = mapped_column(PortableUUID, nullable=False, index=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<SignalSnapshot id={self.id} entity={self.entity_name!r} "
            f"country={self.country_code!r} lang={self.language_code!r} "
            f"demand={self.demand_score:.2f}>"
        )
