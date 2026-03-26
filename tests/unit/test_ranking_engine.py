"""
בדיקות יחידה למנוע הדירוג הדטרמיניסטי של COGNET LDI Engine.
בדיקות אלו רצות ללא תלות ב-DB או רשת.
"""
import uuid
from datetime import datetime, timezone

import pytest

from services.ranking.engine import RankingEngine
from services.ranking.weights import DEFAULT_WEIGHTS, ScoringWeights
from shared.contracts.signal_vector import ScoreBreakdown, SignalVector
from shared.enums.opportunity import OpportunityClassification
from shared.enums.signals import SignalEntityType


# ──────────────────────────────────────────────
# עזר: בניית SignalVector עם ברירות מחדל סבירות
# ──────────────────────────────────────────────

def make_signal(**overrides) -> SignalVector:
    """
    יוצר SignalVector עם ערכי ברירת מחדל — קל לעקיפה לפי הצורך.
    ברירת מחדל: כל ציוני הממדים הם 0.5, ביטחון 1.0, 3 ראיות, 2 משפחות מקור.
    """
    scores_defaults = {
        "demand_score": 0.5,
        "growth_score": 0.5,
        "job_market_score": 0.5,
        "trend_score": 0.5,
        "content_gap_score": 0.5,
        "localization_fit_score": 0.5,
        "teachability_score": 0.5,
        "strategic_fit_score": 0.5,
    }
    # מאפשר עקיפת ציונים בודדים ברמת השטוחה
    for key in list(scores_defaults):
        if key in overrides:
            scores_defaults[key] = overrides.pop(key)

    defaults = dict(
        entity_type=SignalEntityType.skill,
        entity_id=None,
        entity_name="Python",
        country_code="IL",
        language_code="he",
        scores=ScoreBreakdown(**scores_defaults),
        confidence_score=1.0,
        evidence_count=3,
        source_families=["job_postings", "trend_signals"],
        run_id=uuid.uuid4(),
        computed_at=datetime.now(tz=timezone.utc),
    )
    defaults.update(overrides)
    return SignalVector(**defaults)


# ──────────────────────────────────────────────
# בדיקות משקלים
# ──────────────────────────────────────────────

def test_weights_sum_to_one():
    """DEFAULT_WEIGHTS — סכום כל הרכיבים חייב להיות 1.0."""
    w = DEFAULT_WEIGHTS
    total = (
        w.demand_weight
        + w.growth_weight
        + w.job_market_weight
        + w.trend_weight
        + w.content_gap_weight
        + w.localization_fit_weight
        + w.teachability_weight
        + w.strategic_fit_weight
    )
    assert abs(total - 1.0) < 1e-9


def test_invalid_weights_raise_error():
    """ScoringWeights שסכומם אינו 1.0 — חייבים להעלות ValueError."""
    with pytest.raises(ValueError, match="1.0"):
        ScoringWeights(
            demand_weight=0.99,
            growth_weight=0.01,
            job_market_weight=0.01,  # סכום > 1.0 בכוונה
            trend_weight=0.00,
            content_gap_weight=0.00,
            localization_fit_weight=0.00,
            teachability_weight=0.00,
            strategic_fit_weight=0.00,
        )


# ──────────────────────────────────────────────
# בדיקות compute_score
# ──────────────────────────────────────────────

def test_compute_score_all_zeros_returns_zero():
    """אות עם כל ציוני ממדים 0.0 — ציון כולל חייב להיות 0.0."""
    engine = RankingEngine()
    signal = make_signal(
        demand_score=0.0,
        growth_score=0.0,
        job_market_score=0.0,
        trend_score=0.0,
        content_gap_score=0.0,
        localization_fit_score=0.0,
        teachability_score=0.0,
        strategic_fit_score=0.0,
    )
    total_score, _ = engine.compute_score(signal)
    assert total_score == 0.0


def test_compute_score_all_ones_returns_one():
    """אות עם כל ציוני ממדים 1.0 — ציון כולל חייב להיות 1.0."""
    engine = RankingEngine()
    signal = make_signal(
        demand_score=1.0,
        growth_score=1.0,
        job_market_score=1.0,
        trend_score=1.0,
        content_gap_score=1.0,
        localization_fit_score=1.0,
        teachability_score=1.0,
        strategic_fit_score=1.0,
    )
    total_score, _ = engine.compute_score(signal)
    assert total_score == 1.0


def test_compute_score_deterministic():
    """אותו קלט — תמיד אותו פלט. בדיקת דטרמיניזם."""
    engine = RankingEngine()
    signal = make_signal(demand_score=0.7, growth_score=0.6, job_market_score=0.8)
    score_a, _ = engine.compute_score(signal)
    score_b, _ = engine.compute_score(signal)
    assert score_a == score_b


def test_compute_score_breakdown_preserved():
    """
    הפירוט (breakdown) שמוחזר מ-compute_score חייב להכיל את כל 8 הרכיבים
    ולשקף את ציוני הקלט.
    """
    engine = RankingEngine()
    signal = make_signal(
        demand_score=0.3,
        growth_score=0.4,
        job_market_score=0.5,
        trend_score=0.6,
        content_gap_score=0.7,
        localization_fit_score=0.8,
        teachability_score=0.9,
        strategic_fit_score=1.0,
    )
    _, breakdown = engine.compute_score(signal)
    assert breakdown.demand_score == 0.3
    assert breakdown.growth_score == 0.4
    assert breakdown.job_market_score == 0.5
    assert breakdown.trend_score == 0.6
    assert breakdown.content_gap_score == 0.7
    assert breakdown.localization_fit_score == 0.8
    assert breakdown.teachability_score == 0.9
    assert breakdown.strategic_fit_score == 1.0


# ──────────────────────────────────────────────
# בדיקות classify
# ──────────────────────────────────────────────

def test_classify_immediate_threshold():
    """ציון 0.80 — סיווג חייב להיות immediate."""
    engine = RankingEngine()
    assert engine.classify(0.80) == OpportunityClassification.immediate


def test_classify_near_term_threshold():
    """ציון 0.70 — סיווג חייב להיות near_term."""
    engine = RankingEngine()
    assert engine.classify(0.70) == OpportunityClassification.near_term


def test_classify_watchlist_threshold():
    """ציון 0.55 — סיווג חייב להיות watchlist."""
    engine = RankingEngine()
    assert engine.classify(0.55) == OpportunityClassification.watchlist


def test_classify_rejected_threshold():
    """ציון 0.30 — סיווג חייב להיות rejected (מתחת ל-0.35)."""
    engine = RankingEngine()
    assert engine.classify(0.30) == OpportunityClassification.rejected


# ──────────────────────────────────────────────
# בדיקות compute_confidence
# ──────────────────────────────────────────────

def test_confidence_penalty_single_source_family():
    """
    אות עם משפחת מקור יחידה — ביטחון סופי חייב להיות נמוך מהביטחון הבסיסי.
    עונש: x0.85 (num_families<2) ועוד x0.80 (num_families==1).
    """
    engine = RankingEngine()
    signal = make_signal(
        confidence_score=1.0,
        source_families=["job_postings"],  # משפחה אחת בלבד
        evidence_count=5,  # מספיק ראיות כדי לבטל עונש אחר
    )
    confidence = engine.compute_confidence(signal)
    # 1.0 * 0.85 * 0.80 = 0.68
    assert confidence < 1.0
    assert abs(confidence - 0.68) < 1e-4


def test_confidence_penalty_low_evidence():
    """
    אות עם evidence_count=1 (פחות מ-3) — ביטחון מופחת ב-x0.90.
    עם 2 משפחות מקור (ללא עונש משפחה), רק עונש הראיות פעיל.
    """
    engine = RankingEngine()
    signal = make_signal(
        confidence_score=1.0,
        source_families=["job_postings", "trend_signals"],
        evidence_count=1,
    )
    confidence = engine.compute_confidence(signal)
    # 1.0 * 0.90 = 0.90
    assert abs(confidence - 0.90) < 1e-4


def test_confidence_floor_at_0_10():
    """
    גם עם כל העונשים ביטחון בסיסי נמוך מאוד — הרצפה חייבת להיות 0.10.
    """
    engine = RankingEngine()
    signal = make_signal(
        confidence_score=0.01,  # ביטחון בסיסי נמוך מאוד
        source_families=["job_postings"],  # מפעיל שני עונשי משפחה
        evidence_count=1,  # מפעיל עונש ראיות
    )
    confidence = engine.compute_confidence(signal)
    assert confidence >= 0.10


# ──────────────────────────────────────────────
# בדיקות rank_signals
# ──────────────────────────────────────────────

def test_rank_signals_sorted_descending():
    """
    3 אותות עם ציונים שונים — הפלט חייב להיות ממוין בסדר יורד לפי total_score.
    """
    engine = RankingEngine()
    # ציון צפוי: 0.20*0.1 + 0.15*0.1 + 0.20*0.1 + ... (נמוך מאוד)
    low = make_signal(
        entity_name="Low",
        demand_score=0.1,
        growth_score=0.1,
        job_market_score=0.1,
        trend_score=0.1,
        content_gap_score=0.1,
        localization_fit_score=0.1,
        teachability_score=0.1,
        strategic_fit_score=0.1,
    )
    mid = make_signal(
        entity_name="Mid",
        demand_score=0.5,
        growth_score=0.5,
        job_market_score=0.5,
        trend_score=0.5,
        content_gap_score=0.5,
        localization_fit_score=0.5,
        teachability_score=0.5,
        strategic_fit_score=0.5,
    )
    high = make_signal(
        entity_name="High",
        demand_score=0.9,
        growth_score=0.9,
        job_market_score=0.9,
        trend_score=0.9,
        content_gap_score=0.9,
        localization_fit_score=0.9,
        teachability_score=0.9,
        strategic_fit_score=0.9,
    )

    # שולחים בסדר שאינו ממוין
    ranked = engine.rank_signals([mid, low, high])

    assert len(ranked) == 3
    scores = [r[1] for r in ranked]
    # ממוין יורד
    assert scores[0] >= scores[1] >= scores[2]
    # הגבוה ביותר — High
    assert ranked[0][0].entity_name == "High"
    # הנמוך ביותר — Low
    assert ranked[2][0].entity_name == "Low"


def test_rank_signals_empty_list():
    """קלט ריק — פלט ריק."""
    engine = RankingEngine()
    result = engine.rank_signals([])
    assert result == []
