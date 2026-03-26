"""
בדיקות אינטגרציה לנתיבי Health של COGNET LDI Engine API.
מריצים את אפליקציית FastAPI בתוך הפרוצס — אין צורך ב-DB אמיתי עבור /health.
"""
import os
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# הוספת נתיבי המודולים ל-PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../apps/api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# הגדרת משתני סביבה מינימליים לפני ייבוא האפליקציה
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-for-integration-tests")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_cognet")
os.environ.setdefault("APP_ENV", "test")

from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

# ייבוא האפליקציה לאחר הגדרת env vars
from main import create_app  # type: ignore[import]
from app.dependencies.database import get_db  # type: ignore[import]
from app.core.settings import get_settings  # type: ignore[import]


def _build_app_with_mock_db():
    """יוצר אפליקציה עם override ל-DB dependency — ללא חיבור אמיתי."""
    # ניקוי cache של settings לפני יצירת אפליקציה חדשה
    get_settings.cache_clear()

    app = create_app()

    # mock ל-DB session — /health אינו משתמש ב-DB, אבל /ready כן
    async def override_get_db():
        mock_session = AsyncMock(spec=AsyncSession)
        # מדמה כישלון חיבור — graceful degradation
        mock_session.execute.side_effect = Exception("DB not available in test environment")
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    return app


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """AsyncClient מחובר לאפליקציה — ללא שרת אמיתי."""
    app = _build_app_with_mock_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ──────────────────────────────────────────────
# בדיקות /health
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    """GET /health — חייב להחזיר 200 OK."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_has_status_ok(client: AsyncClient):
    """GET /health — גוף התגובה חייב לכלול {"status": "ok"}."""
    response = await client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_response_has_timestamp(client: AsyncClient):
    """GET /health — גוף התגובה חייב לכלול שדה 'timestamp'."""
    response = await client.get("/health")
    data = response.json()
    assert "timestamp" in data
    assert data["timestamp"] is not None


# ──────────────────────────────────────────────
# בדיקות /ready
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ready_endpoint_returns_200(client: AsyncClient):
    """
    GET /ready — חייב להחזיר 200 OK גם כאשר ה-DB אינו מחובר.
    מנגנון ה-graceful degradation אמור להגן על הנקודה.
    """
    response = await client.get("/ready")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ready_response_has_required_fields(client: AsyncClient):
    """
    GET /ready — גוף התגובה חייב לכלול את השדות: status, database, redis, timestamp.
    """
    response = await client.get("/ready")
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "timestamp" in data
