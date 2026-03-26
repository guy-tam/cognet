"""
Portable column types — work with both PostgreSQL and SQLite.
SQLite: UUID stored as CHAR(36), JSONB stored as JSON (TEXT).
PostgreSQL: native UUID and JSONB.
"""
from sqlalchemy import JSON, String, TypeDecorator
import uuid


class PortableUUID(TypeDecorator):
    """UUID type that works on both PostgreSQL (native) and SQLite (CHAR(36))."""

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(str(value))
        return None


# JSONB-compatible type — uses native JSONB on PostgreSQL, JSON (TEXT) on SQLite
PortableJSON = JSON
