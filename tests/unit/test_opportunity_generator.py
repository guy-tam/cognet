"""
בדיקות יחידה ל-OpportunityGenerator של COGNET LDI Engine.
בדיקות אלו רצות ללא תלות ב-DB או רשת.
"""
import uuid
from datetime import datetime, timezone

import pytest

from services.opportunities.generator import OpportunityGenerator
from services.ranking.engine import RankingEngine
from shared.contracts.signal_vector import ScoreBreakdown, SignalVector
from shared.enums.opportunity import OpportunityClassification, OpportunityLifecycleState
from shared.enums.signals import SignalEntityType


# ──────────────────────────────────────────────
# עזרים
# ──────────────────────────────────────────────

def make_signal(
    entity_name: str = "Python",
    country_code: str = "IL",
    language_code: str = "he",
    score_value: float = 0.5,
    source_families: list[str] | None = None,
    evidence_count: int = 5,
    confidence_score: float = 1.0,
    **score_overrides,
) -> SignalVector:
    """
    יוצר SignalVector.
    score_value מאכלס את כל 8 הממדים אלא אם score_overrides מגדיר אחרת.
    """
    if source_families is None:
        source_families = ["job_postings", "trend_signals"]

    scores_dict = {
        "demand_score": score_value,
        "growth_score": score_value,
        "job_market_score": score_value,
        "trend_score": score_value,
        "content_gap_score": score_value,
        "localization_fit_score": score_value,
        "teachability_score": score_value,
        "strategic_fit_score": score_value,
    }
    scores_dict.update(score_overrides)

    return SignalVector(
        entity_type=SignalEntityType.skill,
        entity_id=None,
        entity_name=entity_name,
        country_code=country_code,
        language_code=language_code,
        scores=ScoreBreakdown(**scores_dict),
        confidence_score=confidence_score,
        evidence_count=evidence_count,
        source_families=source_families,
        run_id=uuid.uuid4(),
        computed_at=datetime.now(tz=timezone.utc),
    )


def make_generator(min_score: float = 0.35, min_confidence: float = 0.20) -> OpportunityGenerator:
    """יוצר OpportunityGenerator עם RankingEngine ברירת מחדל."""
    return OpportunityGenerator(
        ranking_engine=RankingEngine(),
        min_score=min_score,
        min_confidence=min_confidence,
    )


# ──────────────────────────────────────────────
# בדיקות
# ──────────────────────────────────────────────

def test_generate_returns_opportunity_for_high_score_signal():
    """
    אות עם כל הציונים 0.9 (ציון כולל > 0.8) — חייבת להיווצר הזדמנות.
    """
    generator = make_generator()
    run_id = uuid.uuid4()
    signal = make_signal(score_value=0.9)
    results = generator.generate([signal], run_id)
    assert len(results) == 1


def test_generate_filters_below_min_score():
    """
    אות עם כל ציוני הממדים 0.0 (ציון כולל = 0.0) — לא אמורה לצאת הזדמנות.
    """
    generator = make_generator()
    run_id = uuid.uuid4()
    signal = make_signal(score_value=0.0)
    results = generator.generate([signal], run_id)
    assert len(results) == 0


def test_generate_opportunity_has_required_fields():
    """
    הזדמנות שנוצרה חייבת להכיל את כל השדות הנדרשים.
    """
    generator = make_generator()
    run_id = uuid.uuid4()
    signal = make_signal(score_value=0.9, entity_name="Machine Learning")
    results = generator.generate([signal], run_id)
    assert len(results) == 1

    opp = results[0]
    assert opp.canonical_topic_name == "Machine Learning"
    assert opp.country_code == "IL"
    assert opp.language_code == "he"
    assert 0.0 <= opp.opportunity_score <= 1.0
    assert opp.score_breakdown is not None
    assert isinstance(opp.why_now_summary, str) and len(opp.why_now_summary) > 0
    assert isinstance(opp.evidence, list)
    assert 0.0 <= opp.confidence_score <= 1.0
    assert isinstance(opp.classification, OpportunityClassification)
    assert isinstance(opp.lifecycle_state, OpportunityLifecycleState)
    assert opp.run_id == run_id


def test_generate_lifecycle_state_is_surfaced():
    """
    כל ההזדמנויות שנוצרות חייבות לקבל lifecycle_state = surfaced.
    """
    generator = make_generator()
    run_id = uuid.uuid4()
    signals = [
        make_signal(entity_name="Python", score_value=0.9),
        make_signal(entity_name="Kubernetes", score_value=0.85),
    ]
    results = generator.generate(signals, run_id)
    assert len(results) == 2
    for opp in results:
        assert opp.lifecycle_state == OpportunityLifecycleState.surfaced


def test_generate_deduplicates_same_topic_same_market():
    """
    שני אותות לאותו נושא+מדינה+שפה — רק אחד יוצא (בעל הציון הגבוה ביותר).
    """
    generator = make_generator()
    run_id = uuid.uuid4()

    low_signal = make_signal(entity_name="Docker", country_code="IL", language_code="he", score_value=0.5)
    high_signal = make_signal(entity_name="Docker", country_code="IL", language_code="he", score_value=0.9)

    results = generator.generate([low_signal, high_signal], run_id)
    assert len(results) == 1
    # חייב לשמור את הציון הגבוה ביותר
    assert results[0].opportunity_score > 0.8


def test_generate_sorted_by_score_descending():
    """
    3 אותות עם ציונים שונים — הפלט ממוין יורד לפי opportunity_score.
    """
    generator = make_generator()
    run_id = uuid.uuid4()

    signals = [
        make_signal(entity_name="SQL", score_value=0.5),
        make_signal(entity_name="Kubernetes", score_value=0.9),
        make_signal(entity_name="Docker", score_value=0.7),
    ]
    results = generator.generate(signals, run_id)
    assert len(results) == 3

    scores = [r.opportunity_score for r in results]
    # ממוין יורד
    assert scores[0] >= scores[1] >= scores[2]
    # הגבוה ביותר — Kubernetes
    assert results[0].canonical_topic_name == "Kubernetes"
