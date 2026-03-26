"""נתיבי API לסטטוס ולהפעלת צינור — מנוע COGNET LDI."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel, Field
from app.schemas.pipeline import PipelineStatusResponse
from app.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/v1/pipeline", tags=["pipeline"])

_service = OpportunityService()


@router.get("/status", response_model=PipelineStatusResponse)
async def pipeline_status() -> dict:
    """קבלת סטטוס הצינור הנוכחי."""
    return await _service.get_pipeline_status()


class PipelineTriggerRequest(BaseModel):
    country_code: str = Field(default="IL", description="קוד מדינת שוק היעד")
    language_code: str = Field(default="he", description="קוד שפת שוק היעד")


class PipelineTriggerResponse(BaseModel):
    message: str
    country_code: str
    language_code: str


@router.post("/trigger", response_model=PipelineTriggerResponse)
async def trigger_pipeline(
    request: PipelineTriggerRequest,
    background_tasks: BackgroundTasks,
) -> PipelineTriggerResponse:
    """
    הפעלת הרצת צינור. רצה באופן אסינכרוני ברקע.

    ל-MVP: משתמש ב-FastAPI BackgroundTasks (ללא תלות ב-Celery).
    לאחר MVP: מעבר להפעלת משימת Celery למעקב נכון אחר משימות.
    """
    import asyncio
    from services.orchestration.pipeline import PipelineOrchestrator

    async def _run_pipeline():
        orchestrator = PipelineOrchestrator(
            country_code=request.country_code,
            language_code=request.language_code,
        )
        result = await orchestrator.run()
        # עדכון מטמון השירות עם התוצאות
        cache_key = f"{request.country_code}:{request.language_code}"
        if _service._cache is None:
            _service._cache = {}
        _service._cache[cache_key] = result.get("opportunities", [])

    background_tasks.add_task(asyncio.run, _run_pipeline())

    return PipelineTriggerResponse(
        message="הרצת צינור הופעלה",
        country_code=request.country_code,
        language_code=request.language_code,
    )
