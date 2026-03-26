"""נתיבי בדיקת בריאות ומוכנות של השירות."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.dependencies.database import get_db
from app.schemas.common import HealthResponse, ReadinessResponse

logger = get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="בדיקת חיות")
async def health() -> HealthResponse:
    """
    בדיקת חיות בסיסית — לא בודקת חיבורים חיצוניים.
    מוחזר תמיד 200 כל עוד התהליך רץ.
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(tz=timezone.utc),
    )


@router.get("/ready", response_model=ReadinessResponse, summary="בדיקת מוכנות")
async def readiness(db: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    """
    בדיקת מוכנות — בודקת חיבור למסד נתונים ול-Redis.
    מחזיר 200 גם במצב degraded, לא 500, כדי לא לגרום ל-restart מיותר.
    """
    db_status = "unavailable"
    redis_status = "unavailable"

    # בדיקת מסד נתונים
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
        logger.debug("בדיקת מסד נתונים עברה בהצלחה")
    except Exception as exc:
        logger.warning("חיבור למסד נתונים נכשל", error=str(exc))

    # בדיקת Redis
    try:
        import redis.asyncio as aioredis

        from app.core.settings import get_settings

        settings = get_settings()
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        redis_status = "ok"
        logger.debug("בדיקת Redis עברה בהצלחה")
    except Exception as exc:
        logger.warning("חיבור ל-Redis נכשל", error=str(exc))

    # קביעת מצב כולל
    if db_status == "ok" and redis_status == "ok":
        overall_status = "ok"
    elif db_status == "ok" or redis_status == "ok":
        overall_status = "degraded"
    else:
        overall_status = "unavailable"

    return ReadinessResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        last_pipeline_run=None,  # ימולא לאחר שיהיה מסד נתונים
        timestamp=datetime.now(tz=timezone.utc),
    )
