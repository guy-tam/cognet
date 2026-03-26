"""
Opportunities Repository — שכבת גישה ל-DB עבור תקציר הזדמנויות.
מפרידה בין עניינים של persistence מלוגיקת ה-service.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from app.models.opportunities import OpportunityBrief, OpportunityEvidenceItem
import uuid


class OpportunitiesRepository:
    """Repository לגישה לטבלת opportunity_briefs ולראיות הקשורות."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_many(
        self,
        country_code: str | None = None,
        language_code: str | None = None,
        classification: str | None = None,
        min_score: float = 0.35,
        limit: int = 20,
        offset: int = 0,
    ) -> list[OpportunityBrief]:
        """שולף רשימת הזדמנויות עם פילטרים אופציונליים וממיין לפי ציון יורד."""
        stmt = select(OpportunityBrief).where(
            OpportunityBrief.opportunity_score >= min_score
        )
        if country_code:
            stmt = stmt.where(OpportunityBrief.country_code == country_code)
        if language_code:
            stmt = stmt.where(OpportunityBrief.language_code == language_code)
        if classification:
            stmt = stmt.where(OpportunityBrief.classification == classification)
        stmt = (
            stmt.order_by(desc(OpportunityBrief.opportunity_score))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        country_code: str | None = None,
        language_code: str | None = None,
        classification: str | None = None,
        min_score: float = 0.35,
    ) -> int:
        """סופר הזדמנויות התואמות לפילטרים — לצרכי pagination."""
        stmt = select(func.count()).select_from(OpportunityBrief).where(
            OpportunityBrief.opportunity_score >= min_score
        )
        if country_code:
            stmt = stmt.where(OpportunityBrief.country_code == country_code)
        if language_code:
            stmt = stmt.where(OpportunityBrief.language_code == language_code)
        if classification:
            stmt = stmt.where(OpportunityBrief.classification == classification)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_evidence(
        self, opportunity_id: uuid.UUID
    ) -> list[OpportunityEvidenceItem]:
        """שולף את כל פריטי הראיה של הזדמנות ספציפית."""
        stmt = select(OpportunityEvidenceItem).where(
            OpportunityEvidenceItem.opportunity_id == opportunity_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
