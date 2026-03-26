"""FastAPI dependency להחזרת הגדרות האפליקציה."""

from app.core.settings import Settings, get_settings


def get_settings_dep() -> Settings:
    """
    FastAPI dependency שמחזיר את הגדרות האפליקציה.

    שימוש בנתיב:
        async def my_route(settings: Settings = Depends(get_settings_dep)):
            ...
    """
    return get_settings()
