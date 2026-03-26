"""מודלי SQLAlchemy לישויות הטקסונומיה של מנוע COGNET LDI."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from app.db.types import PortableUUID, PortableJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    # ייבוא לצרכי type hints בלבד — מניע ייבוא מעגלי בזמן ריצה
    from app.models.opportunities import OpportunityBrief


class Skill(Base):
    """מיומנות — יכולת או ידע שניתן ללמד ולמדוד."""

    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    # קשר עצמי — מיומנות-אב (היררכיה)
    parent_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID, ForeignKey("skills.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # קשרים
    parent_skill: Mapped["Skill | None"] = relationship(
        "Skill", remote_side="Skill.id", back_populates="child_skills"
    )
    child_skills: Mapped[list["Skill"]] = relationship(
        "Skill", back_populates="parent_skill"
    )
    aliases: Mapped[list["SkillAlias"]] = relationship(
        "SkillAlias", back_populates="skill", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Skill id={self.id} name={self.name!r}>"


class SkillAlias(Base):
    """כינוי חלופי למיומנות — למיפוי שמות ממקורות שונים."""

    __tablename__ = "skill_aliases"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, ForeignKey("skills.id"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_label: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # קשרים
    skill: Mapped["Skill"] = relationship("Skill", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<SkillAlias id={self.id} alias={self.alias!r} skill_id={self.skill_id}>"


class Topic(Base):
    """נושא — תחום תוכן רחב שניתן ללמד (למשל: ניהול פרויקטים, Python)."""

    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # קשרים
    aliases: Mapped[list["TopicAlias"]] = relationship(
        "TopicAlias", back_populates="topic", cascade="all, delete-orphan"
    )
    opportunity_briefs: Mapped[list["OpportunityBrief"]] = relationship(  # type: ignore[name-defined]
        "OpportunityBrief", back_populates="topic"
    )

    def __repr__(self) -> str:
        return f"<Topic id={self.id} name={self.name!r}>"


class TopicAlias(Base):
    """כינוי חלופי לנושא."""

    __tablename__ = "topic_aliases"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, ForeignKey("topics.id"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # קשרים
    topic: Mapped["Topic"] = relationship("Topic", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<TopicAlias id={self.id} alias={self.alias!r} topic_id={self.topic_id}>"


class Role(Base):
    """תפקיד תעסוקתי — למשל: מהנדס תוכנה, מנהל מוצר."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    # רמז לתעשייה (לא קשר FK — עשוי להיות טקסט חופשי)
    industry_hint: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"


class Industry(Base):
    """תעשייה — ענף כלכלי (למשל: היי-טק, חינוך, בריאות)."""

    __tablename__ = "industries"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Industry id={self.id} name={self.name!r}>"


class Country(Base):
    """מדינה — לפי קוד ISO 3166-1 alpha-2."""

    __tablename__ = "countries"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    # קוד ISO דו-תווי, למשל: IL, US, DE
    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # קשרים
    regions: Mapped[list["Region"]] = relationship(
        "Region", back_populates="country", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Country id={self.id} code={self.code!r} name={self.name!r}>"


class Region(Base):
    """אזור — תת-חלוקה גיאוגרפית בתוך מדינה."""

    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    country_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, ForeignKey("countries.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    # קשרים
    country: Mapped["Country"] = relationship("Country", back_populates="regions")

    def __repr__(self) -> str:
        return f"<Region id={self.id} code={self.code!r} name={self.name!r}>"


class Language(Base):
    """שפה — לפי קוד ISO 639-1."""

    __tablename__ = "languages"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    # קוד שפה דו-תווי, למשל: he, en, ar
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # האם השפה נכתבת מימין לשמאל
    is_rtl: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Language id={self.id} code={self.code!r} name={self.name!r}>"


