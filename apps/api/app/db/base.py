"""בסיס דקלרטיבי של SQLAlchemy עם מוסכמות שמות אחידות לאינדקסים ואילוצים."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# מוסכמות שמות לאינדקסים, אילוצים ומפתחות זרים
# מאפשר ל-Alembic לייצר שמות צפויים ועקביים
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """מחלקת בסיס לכל מודלי ה-ORM של המערכת."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
