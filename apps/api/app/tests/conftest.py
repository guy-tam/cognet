"""הגדרות pytest משותפות לכל בדיקות ה-API."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.settings import Settings, get_settings
from main import create_app


def get_test_settings() -> Settings:
    """הגדרות לסביבת בדיקות — מחליף את get_settings() הרגיל."""
    return Settings(
        app_env="test",
        app_secret_key="test-secret-key-not-for-production",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test_cognet",
        redis_url="redis://localhost:6379/1",
        log_level="DEBUG",
    )


@pytest.fixture
def test_app():
    """
    יוצר אפליקציית FastAPI לצורכי בדיקה.
    מחליף את ה-settings עם הגדרות בדיקה.
    """
    app = create_app()
    # עקיפת dependency של settings לסביבת בדיקה
    app.dependency_overrides[get_settings] = get_test_settings
    return app


@pytest.fixture
async def async_client(test_app):
    """
    מחזיר AsyncClient מוגדר לבדיקות אסינכרוניות.
    משתמש ב-ASGITransport במקום HTTP אמיתי.
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client
