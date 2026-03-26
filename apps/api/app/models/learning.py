"""מודל SQLAlchemy לנכסי למידה פנימיים של הארגון."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from app.db.types import PortableUUID, PortableJSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InternalLearningAsset(Base):
    """נכס למידה פנימי — קורס, מודול, או תוכן חינוכי הנמצא במאגר הארגוני."""

    __tablename__ = "internal_learning_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID, primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # רשימת מיומנויות מכוסות — מזהים או שמות
    skills: Mapped[list] = mapped_column(PortableJSON, nullable=False, default=list)
    # רשימת נושאים מכוסים
    topics: Mapped[list] = mapped_column(PortableJSON, nullable=False, default=list)
    # קוד שפה ISO 639-1, למשל: he, en
    language: Mapped[str] = mapped_column(String, nullable=False)
    # פורמט: video / article / course / webinar / quiz / ...
    format: Mapped[str] = mapped_column(String, nullable=False)
    # סטטוס: active / archived / draft
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    # רמת כיסוי: beginner / intermediate / advanced
    coverage_level: Mapped[str | None] = mapped_column(String, nullable=True)
    # מטא-דאטה נוסף — שם העמודה "metadata"
    metadata_: Mapped[dict] = mapped_column(
        "metadata", PortableJSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # עדכון אוטומטי בכל שמירה
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<InternalLearningAsset id={self.id} title={self.title!r} "
            f"format={self.format!r} status={self.status!r}>"
        )
