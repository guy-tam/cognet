"""
Opportunity Generator — ממיר וקטורי אותות מדורגים לאובייקטי OpportunityBrief.
"""

import uuid

from shared.contracts.opportunity import EvidenceItem, OpportunityBrief
from shared.contracts.signal_vector import SignalVector
from shared.enums.opportunity import (
    AudienceSegment,
    OpportunityClassification,
    OpportunityLifecycleState,
    RecommendedFormat,
)
from shared.utils.time import utcnow
from services.ranking.engine import RankingEngine


class OpportunityGenerator:
    """מייצר OpportunityBrief ממדורגי SignalVector עם סינון, dedup ומיון."""

    def __init__(
        self,
        ranking_engine: RankingEngine,
        min_score: float = 0.35,
        min_confidence: float = 0.20,
    ) -> None:
        """
        מאתחל את מחולל ההזדמנויות.

        Args:
            ranking_engine: מנוע הדירוג לחישוב ציונים.
            min_score: ציון מינימלי לסינון (ברירת מחדל: 0.35).
            min_confidence: ביטחון מינימלי לסינון (ברירת מחדל: 0.20).
        """
        self.ranking_engine = ranking_engine
        self.min_score = min_score
        self.min_confidence = min_confidence

    def generate(
        self, signals: list[SignalVector], run_id: uuid.UUID
    ) -> list[OpportunityBrief]:
        """
        מייצר רשימת הזדמנויות ממדורגות מוקטורי אותות.

        תהליך:
        1. חישוב ציון וביטחון לכל וקטור
        2. סינון לפי min_score ו-min_confidence
        3. בניית OpportunityBrief לכל וקטור שעבר
        4. דה-דופ לפי (canonical_topic_name, country_code, language_code) — שומר ציון גבוה ביותר
        5. מיון יורד לפי opportunity_score

        Args:
            signals: רשימת SignalVector לעיבוד.
            run_id: מזהה ריצת ה-pipeline.

        Returns:
            רשימת OpportunityBrief ממוינת בסדר יורד.
        """
        # מילון dedup: מפתח → OpportunityBrief עם הציון הגבוה ביותר
        dedup: dict[tuple[str, str, str], OpportunityBrief] = {}

        for signal in signals:
            total_score, breakdown = self.ranking_engine.compute_score(signal)
            confidence = self.ranking_engine.compute_confidence(signal)

            # סינון לפי סף ציון וביטחון
            if total_score < self.min_score or confidence < self.min_confidence:
                continue

            classification = self.ranking_engine.classify(total_score)

            brief = OpportunityBrief(
                canonical_topic_name=signal.entity_name,
                country_code=signal.country_code,
                language_code=signal.language_code,
                audience_segment=AudienceSegment.early_career,
                recommended_format=self._recommend_format(total_score, signal),
                opportunity_score=total_score,
                score_breakdown=breakdown,
                why_now_summary=self._generate_why_now(signal, total_score),
                evidence=self._build_evidence(signal),
                confidence_score=confidence,
                classification=classification,
                lifecycle_state=OpportunityLifecycleState.surfaced,
                run_id=run_id,
                created_at=utcnow(),
            )

            # dedup — שמירת הציון הגבוה ביותר לכל מפתח ייחודי
            dedup_key = (
                signal.entity_name,
                signal.country_code,
                signal.language_code,
            )
            existing = dedup.get(dedup_key)
            if existing is None or total_score > existing.opportunity_score:
                dedup[dedup_key] = brief

        # מיון יורד לפי ציון — דטרמיניסטי: שימוש ב-canonical_topic_name כקריטריון משני
        results = sorted(
            dedup.values(),
            key=lambda b: (b.opportunity_score, b.canonical_topic_name),
            reverse=True,
        )

        return results

    def _generate_why_now(self, signal: SignalVector, score: float) -> str:
        """
        מייצר תקציר טקסטואלי דטרמיניסטי (ללא LLM) מדוע ההזדמנות רלוונטית כעת.

        הפרזה משתנה בהתאם לסיווג ההזדמנות.

        Args:
            signal: SignalVector עם נתוני הישות.
            score: ציון הזדמנות כולל.

        Returns:
            מחרוזת תקציר בשפה אנגלית.
        """
        classification = self.ranking_engine.classify(score)
        num_families = len(signal.source_families)
        families_str = ", ".join(signal.source_families) if signal.source_families else "unknown"

        if classification == OpportunityClassification.immediate:
            return (
                f"{signal.entity_name} shows urgent, high-confidence demand in the "
                f"{signal.country_code} market (score: {score:.2f}). "
                f"Strong signal from {num_families} source {'family' if num_families == 1 else 'families'} "
                f"({families_str}) with {signal.evidence_count} evidence points. "
                f"Confidence: {signal.confidence_score:.2f}. Recommend immediate action."
            )
        elif classification == OpportunityClassification.near_term:
            return (
                f"{signal.entity_name} shows strong near-term demand in the "
                f"{signal.country_code} market (score: {score:.2f}). "
                f"Evidence from {num_families} source {'family' if num_families == 1 else 'families'} "
                f"({families_str}) with confidence {signal.confidence_score:.2f}. "
                f"Recommend planning content development within next quarter."
            )
        elif classification == OpportunityClassification.watchlist:
            return (
                f"{signal.entity_name} shows moderate demand signal in the "
                f"{signal.country_code} market (score: {score:.2f}). "
                f"Observed across {num_families} source {'family' if num_families == 1 else 'families'} "
                f"with {signal.evidence_count} evidence points. "
                f"Confidence: {signal.confidence_score:.2f}. Monitor for strengthening signals."
            )
        else:
            # low_priority
            return (
                f"{signal.entity_name} shows early-stage demand in the "
                f"{signal.country_code} market (score: {score:.2f}). "
                f"Evidence from {num_families} source {'family' if num_families == 1 else 'families'} "
                f"with confidence {signal.confidence_score:.2f}. Low priority at this time."
            )

    def _build_evidence(self, signal: SignalVector) -> list[EvidenceItem]:
        """
        בונה רשימת ראיות — פריט אחד לכל משפחת מקור.

        Args:
            signal: SignalVector עם source_families ו-run_id.

        Returns:
            רשימת EvidenceItem.
        """
        items = []
        for family in signal.source_families:
            items.append(
                EvidenceItem(
                    source_type=family,
                    source_reference=f"signal_run/{signal.run_id}",
                    evidence_summary=f"Demand signal from {family} source data",
                    evidence_weight=0.7,
                )
            )
        return items

    def _recommend_format(
        self, score: float, signal: SignalVector
    ) -> RecommendedFormat:
        """
        ממליץ על פורמט תוכן על בסיס ציון ופרמטרי הוקטור.

        ציון >= 0.80 → short_course (ביקוש גבוה — מהיר לשוק)
        ציון >= 0.65 → short_course אם content_gap_score >= 0.5, אחרת learning_track
        ציון >= 0.50 → workshop
        אחרת        → short_course (ברירת מחדל)

        Args:
            score: ציון הזדמנות כולל.
            signal: SignalVector לגישה ל-content_gap_score.

        Returns:
            RecommendedFormat המתאים.
        """
        if score >= 0.80:
            return RecommendedFormat.short_course
        elif score >= 0.65:
            # בחירה לפי פער תוכן: פער גבוה → קורס קצר, פער נמוך → מסלול למידה
            if signal.scores.content_gap_score >= 0.5:
                return RecommendedFormat.short_course
            else:
                return RecommendedFormat.learning_track
        elif score >= 0.50:
            return RecommendedFormat.workshop
        else:
            return RecommendedFormat.short_course
