"""
בדיקות אינטגרציה לנתיבי Opportunities ו-Pipeline של COGNET LDI Engine API.
מריצים את אפליקציית FastAPI בתוך הפרוצס — stub data, אין צורך ב-DB אמיתי.
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

from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from main import create_app  # type: ignore[import]
from app.dependencies.database import get_db  # type: ignore[import]
from app.core.settings import get_settings  # type: ignore[import]


def _build_app_with_mock_db():
    """יוצר אפליקציה עם override ל-DB dependency — ללא חיבור אמיתי."""
    get_settings.cache_clear()
    app = create_app()

    async def override_get_db():
        mock_session = AsyncMock(spec=AsyncSession)
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
# בדיקות /api/v1/opportunities
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_opportunities_list_returns_200(client: AsyncClient):
    """GET /api/v1/opportunities/ — חייב להחזיר 200 OK."""
    response = await client.get("/api/v1/opportunities/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_opportunities_list_has_schema(client: AsyncClient):
    """
    GET /api/v1/opportunities/ — גוף התגובה חייב לכלול 'opportunities' (list) ו-'total' (int).
    """
    response = await client.get("/api/v1/opportunities/")
    data = response.json()
    assert "opportunities" in data
    assert isinstance(data["opportunities"], list)
    assert "total" in data
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_opportunities_top_returns_200(client: AsyncClient):
    """GET /api/v1/opportunities/top — חייב להחזיר 200 OK."""
    response = await client.get("/api/v1/opportunities/top")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_opportunities_top_is_list(client: AsyncClient):
    """GET /api/v1/opportunities/top — גוף התגובה חייב להיות רשימה."""
    response = await client.get("/api/v1/opportunities/top")
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_opportunities_by_market_returns_200(client: AsyncClient):
    """GET /api/v1/opportunities/by-market?country_code=IL&language_code=he — חייב להחזיר 200 OK."""
    response = await client.get(
        "/api/v1/opportunities/by-market",
        params={"country_code": "IL", "language_code": "he"},
    )
    assert response.status_code == 200


# ──────────────────────────────────────────────
# בדיקות /api/v1/pipeline/status
# ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_status_returns_200(client: AsyncClient):
    """GET /api/v1/pipeline/status — חייב להחזיר 200 OK."""
    response = await client.get("/api/v1/pipeline/status")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_pipeline_status_has_status_field(client: AsyncClient):
    """GET /api/v1/pipeline/status — גוף התגובה חייב לכלול שדה 'status'."""
    response = await client.get("/api/v1/pipeline/status")
    data = response.json()
    assert "status" in data
    assert isinstance(data["status"], str)
