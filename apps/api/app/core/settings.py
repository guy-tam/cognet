"""הגדרות אפליקציה — נטענות מקובץ .env באמצעות pydantic-settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """הגדרות מרכזיות של המערכת."""

    # סביבת הרצה
    app_env: str = Field(default="development", description="סביבת הרצה: development/staging/production")
    app_secret_key: str = Field(description="מפתח סודי לחתימת טוקנים ועוגיות")
    log_level: str = Field(default="INFO", description="רמת לוגינג")

    # שרת API
    api_host: str = Field(default="0.0.0.0", description="כתובת האזנה של שרת ה-API")
    api_port: int = Field(default=8000, description="פורט שרת ה-API")

    # מסד נתונים
    database_url: str = Field(description="URL לחיבור PostgreSQL אסינכרוני")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="URL לחיבור Redis")

    # LLM — אופציונלי
    anthropic_api_key: str | None = Field(default=None, description="מפתח API של Anthropic (לא חובה)")

    # הגדרות Pipeline
    default_pipeline_country: str = Field(default="IL", description="קוד מדינה ברירת מחדל לפייפליין")
    default_pipeline_language: str = Field(default="he", description="קוד שפה ברירת מחדל לפייפליין")
    max_opportunities_per_run: int = Field(default=100, description="מקסימום הזדמנויות להחזיר בהרצה אחת")
    minimum_opportunity_score: float = Field(default=0.35, description="ציון מינימלי לקבלת הזדמנות")
    minimum_confidence_score: float = Field(default=0.20, description="ציון ביטחון מינימלי")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        """בודק האם הסביבה הנוכחית היא production."""
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """מחזיר את אובייקט ההגדרות (מטומן בזיכרון לאחר הקריאה הראשונה)."""
    return Settings()
