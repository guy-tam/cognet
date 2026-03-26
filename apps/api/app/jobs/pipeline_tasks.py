"""
משימות רקע של הצינור — שאיבת נתונים, נרמול, חישוב אותות ויצירת הזדמנויות.

שימוש:
    # הפעלה ידנית
    from app.jobs.pipeline_tasks import run_full_pipeline
    run_full_pipeline.delay(country_code="IL", language_code="he")

    # או דרך לוח זמנים של Celery beat (מוגדר ב-celery_app)
"""
import logging
import asyncio
from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="cognet.pipeline.run_full",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
)
def run_full_pipeline(self, country_code: str = "IL", language_code: str = "he") -> dict:
    """
    הרצת צינור המודיעין המלא של COGNET.

    המשימה:
    1. שואבת מכל מחברי המקורות המוגדרים
    2. מנרמלת רשומות גולמיות
    3. מריצה ניתוח סוכנים (מגמות, ביקוש תעסוקתי, פערי מיומנויות, תעדוף)
    4. מחשבת וקטורי אותות
    5. מדרגת ומייצרת הזדמנויות

    Args:
        country_code: קוד מדינת שוק היעד (ISO 3166-1 alpha-2)
        language_code: קוד שפת שוק היעד (ISO 639-1)

    Returns:
        מילון תוצאות הרצת צינור עם run_id, שלבים, מספר הזדמנויות
    """
    logger.info(
        "run_full_pipeline task started",
        extra={"country_code": country_code, "language_code": language_code, "task_id": self.request.id},
    )

    try:
        # ייבוא כאן למניעת ייבוא מעגלי ברמת המודול
        from services.orchestration.pipeline import PipelineOrchestrator

        orchestrator = PipelineOrchestrator(
            country_code=country_code,
            language_code=language_code,
        )

        # הרצת הצינור האסינכרוני בתוך משימת Celery סינכרונית
        result = asyncio.run(orchestrator.run())

        logger.info(
            "run_full_pipeline task completed",
            extra={
                "run_id": result.get("run_id"),
                "opportunities_count": result.get("opportunities_count", 0),
                "error_count": len(result.get("errors", [])),
                "task_id": self.request.id,
            },
        )

        # החזרת סיכום סריאליזבילי (לא רשימת הזדמנויות מלאה כדי לשמור על תוצאת משימה קטנה)
        return {
            "run_id": result.get("run_id"),
            "country_code": country_code,
            "language_code": language_code,
            "opportunities_count": result.get("opportunities_count", 0),
            "steps": result.get("steps", []),
            "error_count": len(result.get("errors", [])),
            "status": "completed" if not result.get("errors") else "completed_with_errors",
        }

    except Exception as exc:
        logger.error(
            "run_full_pipeline task failed",
            extra={"error": str(exc), "task_id": self.request.id},
            exc_info=True,
        )
        # ניסיון חוזר בכשלים זמניים
        raise self.retry(exc=exc)


@celery_app.task(name="cognet.pipeline.run_ingestion_only")
def run_ingestion_only(country_code: str = "IL") -> dict:
    """הרצת שלב השאיבה בלבד (שימושי לבדיקת מחברים)."""
    import asyncio
    from services.ingestion.connectors.job_postings import JobPostingsConnector
    from services.ingestion.connectors.trend_signals import TrendSignalsConnector
    from services.ingestion.connectors.internal_supply import InternalSupplyConnector
    import uuid

    run_id = uuid.uuid4()

    async def _ingest():
        job_conn = JobPostingsConnector()
        trend_conn = TrendSignalsConnector()
        supply_conn = InternalSupplyConnector()

        job_records, job_errors = await job_conn.run(run_id, country_code=country_code)
        trend_records, trend_errors = await trend_conn.run(run_id, country_code=country_code)
        supply_records, supply_errors = await supply_conn.run(run_id)

        return {
            "run_id": str(run_id),
            "job_records": len(job_records),
            "trend_records": len(trend_records),
            "supply_records": len(supply_records),
            "total_errors": len(job_errors) + len(trend_errors) + len(supply_errors),
        }

    return asyncio.run(_ingest())


# לוח זמנים של Celery Beat להרצה תקופתית של הצינור
celery_app.conf.beat_schedule = {
    "run-pipeline-daily-IL-he": {
        "task": "cognet.pipeline.run_full",
        "schedule": 86400.0,  # כל 24 שעות
        "args": ("IL", "he"),
    },
}
