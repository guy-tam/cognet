"""נקודת הכניסה הראשית של ה-API — יצירת אפליקציית FastAPI."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import get_logger, setup_logging
from app.core.settings import get_settings
from app.routes.health import router as health_router
from app.routes.opportunities import router as opportunities_router
from app.routes.pipeline import router as pipeline_router
from app.telemetry.middleware import RequestTelemetryMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """ניהול מחזור חיי האפליקציה — startup ו-shutdown."""
    settings = get_settings()
    logger = get_logger(__name__)

    logger.info(
        "COGNET LDI Engine מתחיל לפעול",
        env=settings.app_env,
        host=settings.api_host,
        port=settings.api_port,
        is_production=settings.is_production,
    )

    yield  # האפליקציה רצה כאן

    logger.info("COGNET LDI Engine מסיים פעולה")


def create_app() -> FastAPI:
    """
    Factory ליצירת אפליקציית FastAPI מוגדרת ומוכנה להרצה.

    קוראת:
    1. setup_logging() — אתחול structlog
    2. יצירת FastAPI עם lifespan
    3. הוספת CORS middleware
    4. רישום כל הנתיבים
    """
    settings = get_settings()

    # אתחול לוגינג לפני כל דבר אחר
    setup_logging(log_level=settings.log_level)

    app = FastAPI(
        title="COGNET LDI Engine API",
        description="Learning Demand Intelligence Engine — מנוע זיהוי ביקוש ללמידה",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # הגדרת CORS
    # בסביבת production יש להחליף את ["*"] ברשימת domains מורשים
    if settings.is_production:
        allowed_origins = [
            "https://cognet.app",
            "https://www.cognet.app",
        ]
    else:
        # בפיתוח — מאפשר כל מקור
        allowed_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # טלמטריית בקשות — רישום משך, סטטוס ונתיב לכל קריאת API
    app.add_middleware(RequestTelemetryMiddleware)

    # רישום נתיבים
    # health — ללא prefix, נגיש ב-/health ו-/ready
    app.include_router(health_router)

    # נתיבי עסקים — תחת /api
    app.include_router(opportunities_router, prefix="/api")
    app.include_router(pipeline_router, prefix="/api")

    return app


# יצירת מופע האפליקציה — uvicorn ישתמש בו ישירות
app = create_app()
