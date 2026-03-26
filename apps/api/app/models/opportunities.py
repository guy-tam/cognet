"""מודלי SQLAlchemy להזדמנויות תוכן, ראיות ובחינות עריכה."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, func
from app.db.types import PortableUUID, PortableJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    # ייבוא לצרכי type hints בלבד — מניע ייבוא מעגלי בזמן ריצה
    from app.models.taxonomy import Topic
    from app.models.pipeline import PipelineRun


class OpportunityBrief(Base):
    """
    תקציר הזדמנות — נושא למידה שזוהה כבעל פוטנציאל גבוה
    בשוק ספציפי (מדינה + שפה + קהל יעד).
    """

    __tablename__ = "opportunity_briefs"

    __table_args__ = (
        # אינדקס לשאילתות ממויינות לפי ציון הזדמנות יורד
        Index(
            "ix_opportunity_briefs_country_lang_score",
            "country_code",
            "language_code",
            "opportunity_score",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    # קשר לנושא בטקסונומיה — אופציונלי אם הנושא חדש
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID, ForeignKey("topics.id"), nullable=True, index=True
    )
    # שם הנושא הקנוני לצרכי תצוגה ודוחות
    canonical_topic_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String, nullable=False)
    region_code: Mapped[str | None] = mapped_column(String, nullable=True)
    language_code: Mapped[str] = mapped_column(String, nullable=False)
    # פלח קהל יעד: professional / student / executive / ...
    audience_segment: Mapped[str] = mapped_column(String, nullable=False)
    # פורמט מומלץ: video / article / bootcamp / microlearning / ...
    recommended_format: Mapped[str] = mapped_column(String, nullable=False)

    # --- ציונות ---
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    demand_score: Mapped[float] = mapped_column(Float, nullable=False)
    growth_score: Mapped[float] = mapped_column(Float, nullable=False)
    job_market_score: Mapped[float] = mapped_column(Float, nullable=False)
    trend_score: Mapped[float] = mapped_column(Float, nullable=False)
    content_gap_score: Mapped[float] = mapped_column(Float, nullable=False)
    localization_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    teachability_score: Mapped[float] = mapped_column(Float, nullable=False)
    strategic_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # סיכום נרטיבי — למה עכשיו?
    why_now_summary: Mapped[str] = mapped_column(Text, nullable=False)
    # סיווג: quick_win / strategic / niche / emerging / ...
    classification: Mapped[str] = mapped_column(String, nullable=False)
    # מצב מחזור חיים: surfaced / under_review / approved / rejected / published
    lifecycle_state: Mapped[str] = mapped_column(
        String, nullable=False, default="surfaced"
    )

    # הרצת הפייפליין שיצרה את ההזדמנות
    run_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, ForeignKey("pipeline_runs.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # קשרים
    topic: Mapped["Topic | None"] = relationship(  # type: ignore[name-defined]
        "Topic", back_populates="opportunity_briefs"
    )
    pipeline_run: Mapped["PipelineRun"] = relationship(  # type: ignore[name-defined]
        "PipelineRun", back_populates="opportunity_briefs"
    )
    evidence_items: Mapped[list["OpportunityEvidenceItem"]] = relationship(
        "OpportunityEvidenceItem",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )
    review_decisions: Mapped[list["ReviewDecision"]] = relationship(
        "ReviewDecision",
        back_populates="opportunity",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<OpportunityBrief id={self.id} topic={self.canonical_topic_name!r} "
            f"country={self.country_code!r} score={self.opportunity_score:.2f} "
            f"state={self.lifecycle_state!r}>"
        )


class OpportunityEvidenceItem(Base):
    """פריט ראיה — מסמך תומך שמנמק את קיום ההזדמנות."""

    __tablename__ = "opportunity_evidence_items"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("opportunity_briefs.id"),
        nullable=False,
        index=True,
    )
    # סוג הראיה: job_posting / survey / industry_report / search_trend / ...
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    # הפניה למקור: URL, מזהה פנימי, וכו'
    source_reference: Mapped[str] = mapped_column(String, nullable=False)
    # תמצית הראיה בשפה טבעית
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    # משקל הראיה בחישוב הציון (0.0 עד 1.0)
    evidence_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # קשרים
    opportunity: Mapped["OpportunityBrief"] = relationship(
        "OpportunityBrief", back_populates="evidence_items"
    )

    def __repr__(self) -> str:
        return (
            f"<OpportunityEvidenceItem id={self.id} "
            f"opportunity_id={self.opportunity_id} source={self.source_type!r}>"
        )


class ReviewDecision(Base):
    """החלטת בחינה — תיעוד מעבר מצב של הזדמנות על ידי עורך אנושי."""

    __tablename__ = "review_decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("opportunity_briefs.id"),
        nullable=False,
        index=True,
    )
    # מצב לפני ואחרי ההחלטה
    from_state: Mapped[str] = mapped_column(String, nullable=False)
    to_state: Mapped[str] = mapped_column(String, nullable=False)
    # מי קיבל את ההחלטה — user_id, שם, או None לפעולות אוטומטיות
    decided_by: Mapped[str | None] = mapped_column(String, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # קשרים
    opportunity: Mapped["OpportunityBrief"] = relationship(
        "OpportunityBrief", back_populates="review_decisions"
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewDecision id={self.id} opportunity_id={self.opportunity_id} "
            f"{self.from_state!r} -> {self.to_state!r}>"
        )
