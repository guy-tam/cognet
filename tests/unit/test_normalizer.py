"""
בדיקות יחידה ל-Normalizer של COGNET LDI Engine.
בדיקות אלו רצות ללא תלות ב-DB או רשת.
"""
import uuid
from datetime import datetime, timezone

import pytest

from services.normalization.normalizer import Normalizer
from shared.contracts.raw_record import RawSourceRecord
from shared.enums.pipeline import SourceType


# ──────────────────────────────────────────────
# עזר: בניית RawSourceRecord עם ברירות מחדל
# ──────────────────────────────────────────────

def make_raw_record(**overrides) -> RawSourceRecord:
    """
    יוצר RawSourceRecord עם ערכי ברירת מחדל — ניתן לעקיפה לפי הצורך.
    """
    payload = overrides.pop("payload", {"title": "Python Developer"})
    defaults = dict(
        source_name="test_source",
        source_type=SourceType.job_postings,
        external_id="ext-001",
        collected_at=datetime.now(tz=timezone.utc),
        language_code="en",
        country_code="IL",
        payload=payload,
        checksum=RawSourceRecord.compute_checksum(payload),
        source_run_id=uuid.uuid4(),
    )
    defaults.update(overrides)
    return RawSourceRecord(**defaults)


# ──────────────────────────────────────────────
# בדיקות
# ──────────────────────────────────────────────

def test_normalize_job_posting_extracts_title():
    """
    payload עם מפתח 'title' — normalized_title חייב להיות מוגדר נכון.
    """
    normalizer = Normalizer()
    raw = make_raw_record(payload={"title": "Senior Python Developer"})
    result = normalizer.normalize(raw)
    assert result.normalized_title == "Senior Python Developer"


def test_normalize_strips_html_tags():
    """
    תיאור עם תגי HTML — הטקסט המנורמל חייב להיות ללא תגים.
    """
    normalizer = Normalizer()
    raw = make_raw_record(
        payload={
            "title": "Dev Role",
            "description": "<b>Python</b> developer with <em>experience</em>",
        }
    )
    result = normalizer.normalize(raw)
    assert "<b>" not in result.normalized_text
    assert "<em>" not in result.normalized_text
    assert "Python" in result.normalized_text
    assert "developer" in result.normalized_text
    assert "experience" in result.normalized_text


def test_normalize_collapses_whitespace():
    """
    תיאור עם רווחים ושורות עודפים — הטקסט המנורמל חייב להיות נקי.
    """
    normalizer = Normalizer()
    raw = make_raw_record(
        payload={
            "title": "Backend Engineer",
            "description": "We   need\n\n  a developer   with  Python  skills.",
        }
    )
    result = normalizer.normalize(raw)
    # אין ריצוף רווחים, אין שבירות שורה
    assert "  " not in result.normalized_text
    assert "\n" not in result.normalized_text
    assert result.normalized_text == "We need a developer with Python skills."


def test_normalize_record_type_job_posting():
    """
    source_type=job_postings — record_type חייב להיות 'job_posting'.
    """
    normalizer = Normalizer()
    raw = make_raw_record(source_type=SourceType.job_postings)
    result = normalizer.normalize(raw)
    assert result.record_type == "job_posting"


def test_normalize_record_type_trend_signal():
    """
    source_type=trend_signals — record_type חייב להיות 'trend_signal'.
    """
    normalizer = Normalizer()
    payload = {"keyword": "machine learning"}
    raw = make_raw_record(
        source_type=SourceType.trend_signals,
        payload=payload,
        checksum=RawSourceRecord.compute_checksum(payload),
    )
    result = normalizer.normalize(raw)
    assert result.record_type == "trend_signal"


def test_normalize_dedup_key_deterministic():
    """
    אותם קלטים — תמיד אותו dedup_key (דטרמיניזם מלא).
    """
    normalizer = Normalizer()
    payload = {"title": "Data Engineer"}
    checksum = RawSourceRecord.compute_checksum(payload)

    run_id = uuid.uuid4()
    raw_a = make_raw_record(
        external_id="ext-42",
        country_code="US",
        payload=payload,
        checksum=checksum,
        source_run_id=run_id,
    )
    raw_b = make_raw_record(
        external_id="ext-42",
        country_code="US",
        payload=payload,
        checksum=checksum,
        source_run_id=run_id,
    )

    result_a = normalizer.normalize(raw_a)
    result_b = normalizer.normalize(raw_b)
    assert result_a.dedup_key == result_b.dedup_key


def test_normalize_preserves_source_lineage():
    """
    source_name ו-source_run_id חייבים להישמר ברשומה המנורמלת.
    """
    normalizer = Normalizer()
    run_id = uuid.uuid4()
    raw = make_raw_record(
        source_name="linkedin_jobs",
        source_run_id=run_id,
    )
    result = normalizer.normalize(raw)
    assert result.source_name == "linkedin_jobs"
    assert result.source_run_id == run_id
