"""מודלי SQLAlchemy למעקב אחר הרצות הפייפליין ורשומות המקור."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from app.db.types import PortableUUID, PortableJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    # ייבוא לצרכי type hints בלבד — מניע ייבוא מעגלי בזמן ריצה
    from app.models.opportunities import OpportunityBrief


class SourceRun(Base):
    """הרצת מקור — תיעוד פעולת איסוף נתונים ממקור אחד."""

    __tablename__ = "source_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    source_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # סטטוס: pending / running / completed / failed
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)

    # קשרים
    raw_records: Mapped[list["RawSourceRecord"]] = relationship(
        "RawSourceRecord", back_populates="source_run", cascade="all, delete-orphan"
    )
    normalized_records: Mapped[list["NormalizedRecord"]] = relationship(
        "NormalizedRecord", back_populates="source_run"
    )

    def __repr__(self) -> str:
        return f"<SourceRun id={self.id} source={self.source_name!r} status={self.status!r}>"


class RawSourceRecord(Base):
    """רשומת מקור גולמית — נתון כפי שהתקבל לפני כל עיבוד."""

    __tablename__ = "raw_source_records"

    __table_args__ = (
        # מניעת כפילויות: אותו מקור עם אותו checksum
        UniqueConstraint("source_name", "checksum", name="uq_raw_source_checksum"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    source_run_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, ForeignKey("source_runs.id"), nullable=False, index=True
    )
    source_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    language_code: Mapped[str | None] = mapped_column(String, nullable=True)
    country_code: Mapped[str | None] = mapped_column(String, nullable=True)
    region_code: Mapped[str | None] = mapped_column(String, nullable=True)
    # תוכן הרשומה המלא — JSON גמיש
    payload: Mapped[dict] = mapped_column(PortableJSON, nullable=False)
    # טביעת אצבע לזיהוי כפילויות
    checksum: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # רמת אמינות המקור: tier_1_high / tier_2_medium / tier_3_low
    trust_tier: Mapped[str] = mapped_column(String, nullable=False, default="tier_2_medium")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # קשרים
    source_run: Mapped["SourceRun"] = relationship("SourceRun", back_populates="raw_records")
    normalized_record: Mapped["NormalizedRecord | None"] = relationship(
        "NormalizedRecord", back_populates="raw_record", uselist=False
    )

    def __repr__(self) -> str:
        return f"<RawSourceRecord id={self.id} source={self.source_name!r} checksum={self.checksum!r}>"


class NormalizedRecord(Base):
    """רשומה מנורמלת — לאחר ניקוי, תרגום ועיבוד סמנטי."""

    __tablename__ = "normalized_records"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    # קשר יחיד לרשומה הגולמית
    raw_record_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("raw_source_records.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    normalized_title: Mapped[str] = mapped_column(String, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_language: Mapped[str | None] = mapped_column(String, nullable=True)
    canonical_country: Mapped[str | None] = mapped_column(String, nullable=True)
    canonical_region: Mapped[str | None] = mapped_column(String, nullable=True)
    # סוג הרשומה: job_posting / course / article / survey / ...
    record_type: Mapped[str] = mapped_column(String, nullable=False)
    # מפתח לזיהוי כפילויות סמנטיות
    dedup_key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # סטטוס: normalized / pending_review / rejected
    normalization_status: Mapped[str] = mapped_column(
        String, nullable=False, default="normalized"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    source_run_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, ForeignKey("source_runs.id"), nullable=False, index=True
    )

    # קשרים
    raw_record: Mapped["RawSourceRecord"] = relationship(
        "RawSourceRecord", back_populates="normalized_record"
    )
    source_run: Mapped["SourceRun"] = relationship(
        "SourceRun", back_populates="normalized_records"
    )

    def __repr__(self) -> str:
        return (
            f"<NormalizedRecord id={self.id} title={self.normalized_title!r} "
            f"status={self.normalization_status!r}>"
        )


class PipelineRun(Base):
    """הרצת פייפליין — תיעוד מחזור עיבוד מלא מקצה לקצה."""

    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # סטטוס: running / completed / failed / partial
    status: Mapped[str] = mapped_column(String, nullable=False)
    # סיכום כל שלב בפייפליין — רשימת אובייקטים
    step_summaries: Mapped[list] = mapped_column(PortableJSON, nullable=False, default=list)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # מטא-דאטה כללי — שם העמודה "metadata" (מילת מפתח שמורה ב-Python)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", PortableJSON, nullable=False, default=dict
    )

    # קשרים
    opportunity_briefs: Mapped[list["OpportunityBrief"]] = relationship(  # type: ignore[name-defined]
        "OpportunityBrief", back_populates="pipeline_run"
    )

    def __repr__(self) -> str:
        return f"<PipelineRun id={self.id} status={self.status!r}>"


