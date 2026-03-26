"""
בדיקות יחידה לחוזים המשותפים (shared contracts) של COGNET LDI Engine.
בדיקות אלו רצות ללא תלות ב-DB או רשת.
"""
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from shared.contracts.raw_record import RawSourceRecord
from shared.contracts.signal_vector import ScoreBreakdown, SignalVector
from shared.contracts.opportunity import EvidenceItem, OpportunityBrief
from shared.enums.pipeline import SourceType
from shared.enums.signals import SignalEntityType
from shared.utils.hashing import compute_dedup_key, compute_payload_checksum
from shared.i18n.language_codes import CANONICAL_LANGUAGE_MAP, is_rtl, is_supported


# ──────────────────────────────────────────────
# עזרים
# ──────────────────────────────────────────────

def make_raw_record(payload: dict | None = None, **overrides) -> RawSourceRecord:
    """יוצר RawSourceRecord עם ערכי ברירת מחדל."""
    if payload is None:
        payload = {"title": "Python Developer"}
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
# בדיקות ScoreBreakdown
# ──────────────────────────────────────────────

def test_score_breakdown_defaults_to_zero():
    """
    ScoreBreakdown() ללא ארגומנטים — כל השדות חייבים להיות 0.0.
    """
    breakdown = ScoreBreakdown()
    assert breakdown.demand_score == 0.0
    assert breakdown.growth_score == 0.0
    assert breakdown.job_market_score == 0.0
    assert breakdown.trend_score == 0.0
    assert breakdown.content_gap_score == 0.0
    assert breakdown.localization_fit_score == 0.0
    assert breakdown.teachability_score == 0.0
    assert breakdown.strategic_fit_score == 0.0


def test_score_breakdown_rejects_out_of_range():
    """
    ScoreBreakdown עם demand_score=1.5 (מחוץ לטווח [0,1]) — חייב להעלות ValidationError.
    """
    with pytest.raises(ValidationError):
        ScoreBreakdown(demand_score=1.5)


# ──────────────────────────────────────────────
# בדיקות RawSourceRecord checksum
# ──────────────────────────────────────────────

def test_raw_record_checksum_deterministic():
    """
    אותו payload — תמיד אותה checksum (דטרמיניזם).
    """
    payload = {"title": "Data Scientist", "level": "senior"}
    checksum_a = RawSourceRecord.compute_checksum(payload)
    checksum_b = RawSourceRecord.compute_checksum(payload)
    assert checksum_a == checksum_b
    # SHA-256 hex — אורך 64 תווים
    assert len(checksum_a) == 64


# ──────────────────────────────────────────────
# בדיקות compute_dedup_key
# ──────────────────────────────────────────────

def test_compute_dedup_key_deterministic():
    """
    אותם ארגומנטים — תמיד אותו dedup_key.
    """
    key_a = compute_dedup_key(
        source_type="job_postings",
        external_id="ext-007",
        normalized_title="Python Developer",
        country_code="IL",
    )
    key_b = compute_dedup_key(
        source_type="job_postings",
        external_id="ext-007",
        normalized_title="Python Developer",
        country_code="IL",
    )
    assert key_a == key_b
    assert len(key_a) == 64


def test_compute_dedup_key_differs_on_different_inputs():
    """
    קלטים שונים — dedup_key שונה.
    """
    key_a = compute_dedup_key(
        source_type="job_postings",
        external_id="ext-001",
        normalized_title="Python Developer",
        country_code="IL",
    )
    key_b = compute_dedup_key(
        source_type="job_postings",
        external_id="ext-002",  # external_id שונה
        normalized_title="Python Developer",
        country_code="IL",
    )
    assert key_a != key_b


# ──────────────────────────────────────────────
# בדיקות is_rtl
# ──────────────────────────────────────────────

def test_hebrew_is_rtl():
    """עברית (he) — חייבת להיות RTL."""
    assert is_rtl("he") is True


def test_english_is_not_rtl():
    """אנגלית (en) — חייבת להיות LTR (לא RTL)."""
    assert is_rtl("en") is False


# ──────────────────────────────────────────────
# בדיקות CANONICAL_LANGUAGE_MAP
# ──────────────────────────────────────────────

def test_canonical_language_map_hebrew():
    """
    המפה הקנונית של שפות — 'עברית' חייב להיות ממופה ל-'he'.
    """
    assert CANONICAL_LANGUAGE_MAP["עברית"] == "he"


# ──────────────────────────────────────────────
# בדיקות is_supported
# ──────────────────────────────────────────────

def test_is_supported_en_and_he():
    """
    'en' ו-'he' — שתיהן חייבות להיות שפות נתמכות.
    """
    assert is_supported("en") is True
    assert is_supported("he") is True


def test_is_supported_unknown_returns_false():
    """
    'zz' — קוד שפה לא קיים — חייב להחזיר False.
    """
    assert is_supported("zz") is False
