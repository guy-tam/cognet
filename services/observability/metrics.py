"""
מטריקות ניטור — מנוע COGNET LDI.
MVP: הוקים ללוגינג מובנה. לאחר MVP: אינטגרציית OpenTelemetry.
"""
import logging
import time
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)


@contextmanager
def track_step(step_name: str, run_id: str, **extra) -> Generator[dict, None, None]:
    """
    מנהל הקשר למעקב אחר ביצוע שלב בצינור.

    שימוש:
        with track_step("normalize", run_id="abc") as ctx:
            # ביצוע עבודה
            ctx["record_count"] = 15
    """
    ctx: dict = {"step_name": step_name, "run_id": run_id, "record_count": 0, "error_count": 0}
    start = time.monotonic()

    logger.info(f"Step started: {step_name}", extra={"run_id": run_id, **extra})

    try:
        yield ctx
    except Exception as exc:
        ctx["error_count"] += 1
        ctx["error"] = str(exc)
        logger.error(
            f"Step failed: {step_name}",
            extra={"run_id": run_id, "error": str(exc), **extra},
            exc_info=True,
        )
        raise
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        ctx["duration_ms"] = duration_ms
        logger.info(
            f"Step completed: {step_name}",
            extra={
                "run_id": run_id,
                "record_count": ctx["record_count"],
                "error_count": ctx["error_count"],
                "duration_ms": duration_ms,
                **extra,
            },
        )


def log_pipeline_start(run_id: str, country_code: str, language_code: str) -> None:
    """רישום התחלת הרצת צינור."""
    logger.info(
        "Pipeline run started",
        extra={"run_id": run_id, "country_code": country_code, "language_code": language_code},
    )


def log_pipeline_end(run_id: str, opportunities_count: int, error_count: int, duration_ms: int) -> None:
    """רישום סיום הרצת צינור."""
    logger.info(
        "Pipeline run completed",
        extra={
            "run_id": run_id,
            "opportunities_count": opportunities_count,
            "error_count": error_count,
            "duration_ms": duration_ms,
        },
    )
