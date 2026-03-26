"""ייצוא מחדש של dependency מסד הנתונים לשימוש בנתיבים."""

from app.db.session import get_db

__all__ = ["get_db"]
