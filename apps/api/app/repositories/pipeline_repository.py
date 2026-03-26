"""
Pipeline Repository — שכבת גישה ל-DB עבור הרצות פייפליין.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.pipeline import PipelineRun


class PipelineRepository:
    """Repository לגישה לטבלת pipeline_runs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest(self) -> PipelineRun | None:
        """מחזיר את הרצת הפייפליין האחרונה (לפי started_at)."""
        stmt = (
            select(PipelineRun)
            .order_by(desc(PipelineRun.started_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_last_successful(self) -> PipelineRun | None:
        """מחזיר את הרצת הפייפליין האחרונה שהסתיימה בהצלחה."""
        stmt = (
            select(PipelineRun)
            .where(PipelineRun.status == "completed")
            .order_by(desc(PipelineRun.started_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
