"""
בדיקות יחידה ל-SignalComputer של COGNET LDI Engine.
בדיקות אלו רצות ללא תלות ב-DB או רשת.
"""

import pytest

from services.signals.computer import SignalComputer


# ──────────────────────────────────────────────
# עזר: ברירת מחדל ל-SignalComputer
# ──────────────────────────────────────────────

def make_computer(country_code: str = "IL", language_code: str = "he") -> SignalComputer:
    """יוצר SignalComputer לשוק ישראלי/עברי כברירת מחדל."""
    return SignalComputer(country_code=country_code, language_code=language_code)


# ──────────────────────────────────────────────
# בדיקות compute_demand_score
# ──────────────────────────────────────────────

def test_demand_score_zero_when_no_records():
    """
    כאשר אין רשומות (job_posting_count=0, trend_mention_count=0, total_records=0)
    — ציון ביקוש חייב להיות 0.0.
    """
    computer = make_computer()
    score = computer.compute_demand_score(
        job_posting_count=0,
        trend_mention_count=0,
        total_records=0,
    )
    assert score == 0.0


def test_demand_score_clamped_to_one():
    """
    מספרים גבוהים מאוד — ציון ביקוש חייב להיות מוגבל ל-1.0.
    """
    computer = make_computer()
    score = computer.compute_demand_score(
        job_posting_count=1_000_000,
        trend_mention_count=500_000,
        total_records=1,  # total_records נמוך מאוד → raw score >> 1.0
    )
    assert score == 1.0


# ──────────────────────────────────────────────
# בדיקות compute_growth_score
# ──────────────────────────────────────────────

def test_growth_score_neutral_when_no_history():
    """
    older_count=0 — אין נתוני בסיס, ציון צמיחה חייב להיות 0.5 (ניטרלי).
    """
    computer = make_computer()
    score = computer.compute_growth_score(recent_count=100, older_count=0)
    assert score == 0.5


def test_growth_score_high_when_growing():
    """
    recent_count גבוה בהרבה מ-older_count (ratio > 2.0) — ציון צמיחה > 0.7.
    """
    computer = make_computer()
    score = computer.compute_growth_score(recent_count=300, older_count=100)
    # ratio = 3.0 > 2.0 → ציון = 1.0
    assert score > 0.7


# ──────────────────────────────────────────────
# בדיקות compute_content_gap_score
# ──────────────────────────────────────────────

def test_content_gap_high_when_high_demand_low_supply():
    """
    demand=1.0, supply=0.1 — פער תוכן גדול → ציון > 0.6.
    נוסחה: clamp(0,1, 0.5 + (1.0 - 0.1)) = clamp(0,1, 1.4) = 1.0
    """
    computer = make_computer()
    score = computer.compute_content_gap_score(demand_level=1.0, supply_coverage=0.1)
    assert score > 0.6


def test_content_gap_low_when_supply_covers_demand():
    """
    demand=0.3, supply=0.9 — היצע עולה על ביקוש → ציון < 0.3.
    נוסחה: clamp(0,1, 0.5 + (0.3 - 0.9)) = clamp(0,1, -0.1) = 0.0
    """
    computer = make_computer()
    score = computer.compute_content_gap_score(demand_level=0.3, supply_coverage=0.9)
    assert score < 0.3
