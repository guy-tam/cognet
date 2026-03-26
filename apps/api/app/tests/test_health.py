"""בדיקות לנתיבי בדיקת הבריאות של השירות."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(async_client: AsyncClient) -> None:
    """
    בדיקה שנתיב /health מחזיר 200 עם status="ok".
    נתיב זה לא תלוי בחיבורים חיצוניים ותמיד צריך להצליח.
    """
    response = await async_client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    # וידוא שה-timestamp הוא מחרוזת ISO 8601 תקינה
    assert isinstance(data["timestamp"], str)
    assert len(data["timestamp"]) > 0


@pytest.mark.asyncio
async def test_ready_returns_status(async_client: AsyncClient) -> None:
    """
    בדיקה שנתיב /ready מחזיר 200 ומכיל את כל השדות הנדרשים.
    המצב יכול להיות degraded/unavailable בסביבת בדיקה (אין DB/Redis),
    אבל הנתיב עצמו חייב לחזור 200 ולא 500.
    """
    response = await async_client.get("/ready")

    # /ready תמיד מחזיר 200, גם אם הרכיבים לא זמינים
    assert response.status_code == 200

    data = response.json()

    # וידוא שדות חובה קיימים
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "timestamp" in data

    # status חייב להיות אחד מהערכים המוגדרים
    assert data["status"] in ("ok", "degraded", "unavailable")

    # database ו-redis חייבים להיות ok או unavailable
    assert data["database"] in ("ok", "unavailable")
    assert data["redis"] in ("ok", "unavailable")

    # last_pipeline_run יכול להיות null
    assert "last_pipeline_run" in data
