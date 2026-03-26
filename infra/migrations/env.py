"""
קובץ סביבת Alembic — מגדיר כיצד לגלות מודלים ולהתחבר למסד הנתונים.

תומך בשני מצבים:
  - offline: יוצר SQL סטטי ללא חיבור למסד נתונים
  - online:  מתחבר ומריץ migrations בזמן אמת (אסינכרוני)
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ייבוא Base — חייב לקרות לפני ייבוא המודלים
from app.db.base import Base  # noqa: F401

# ייבוא כל המודלים כדי ש-Alembic יגלה את הטבלאות
from app.models import *  # noqa: F401, F403

# ייבוא הגדרות האפליקציה לשליפת DATABASE_URL
from app.core.settings import Settings

# -------------------------------------------------------------------
# הגדרת לוגינג מ-alembic.ini
# -------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------------------
# מטא-דאטה — Alembic ישתמש בו לזיהוי שינויים אוטומטי
# -------------------------------------------------------------------
target_metadata = Base.metadata

# -------------------------------------------------------------------
# שליפת DATABASE_URL מהגדרות האפליקציה
# -------------------------------------------------------------------
_settings = Settings()  # type: ignore[call-arg]
# Alembic דורש URL סינכרוני גם לאנג'ין האסינכרוני —
# asyncpg → psycopg2 לצרכי autogenerate
_db_url = _settings.database_url


def _get_sync_url(url: str) -> str:
    """ממיר URL אסינכרוני לסינכרוני עבור מצב offline."""
    return url.replace("postgresql+asyncpg://", "postgresql://")


# -------------------------------------------------------------------
# מצב Offline — מייצר DDL סטטי ללא חיבור למסד נתונים
# -------------------------------------------------------------------
def run_migrations_offline() -> None:
    """
    הרצת migrations במצב offline.
    שימושי לייצוא SQL לסקריפטים ידניים.
    """
    context.configure(
        url=_get_sync_url(_db_url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # תמיכה ב-naming convention של Base
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# -------------------------------------------------------------------
# מצב Online — מריץ migrations בפועל מול מסד הנתונים
# -------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    """מריץ migrations בתוך חיבור פעיל."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """יוצר async engine ומריץ migrations באמצעות run_sync."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _db_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # run_sync מאפשר להריץ קוד סינכרוני בתוך async context
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """נקודת כניסה למצב online — מריץ את ה-coroutine האסינכרוני."""
    asyncio.run(run_async_migrations())


# -------------------------------------------------------------------
# בחירת מצב הרצה
# -------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
