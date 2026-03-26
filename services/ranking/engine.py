"""
מנוע דירוג דטרמיניסטי — COGNET LDI Engine

מחשב ציון הזדמנות כולל מוקטור אותות באמצעות משקלים ניתנים להגדרה.
זהו הליבה של לוגיקת הציון. חייב להישאר:
- דטרמיניסטי: אותם קלטים → אותם פלטים תמיד
- מוסבר: פירוט הציון תמיד נשמר
- ניתן לבדיקה: ללא תלות ב-DB או רשת
- מנוהל: שינויי משקלים חייבים לעבור scoring-governance.md
"""

from shared.contracts.signal_vector import ScoreBreakdown, SignalVector
from shared.enums.opportunity import OpportunityClassification
from services.ranking.weights import DEFAULT_WEIGHTS, ScoringWeights


class RankingEngine:
    """מנוע דירוג דטרמיניסטי — מחשב ציונים ומדרג הזדמנויות."""

    def __init__(self, weights: ScoringWeights = DEFAULT_WEIGHTS) -> None:
        """
        מאתחל את מנוע הדירוג עם משקלים ניתנים להגדרה.

        Args:
            weights: אובייקט ScoringWeights עם משקלי הממדים השונים.
        """
        self.weights = weights

    def compute_score(
        self, signal: SignalVector
    ) -> tuple[float, ScoreBreakdown]:
        """
        מחשב ציון הזדמנות כולל מוקטור אותות.

        הנוסחה: total = sum(weight_i * score_i) עבור כל הממדים.
        הציון מוחזר מעוגל ל-4 ספרות אחרי הנקודה ומוגבל לטווח 0–1.

        Args:
            signal: SignalVector עם ציוני ממדים מאוכלסים.

        Returns:
            tuple של (total_score: float, breakdown: ScoreBreakdown).
        """
        w = self.weights
        s = signal.scores

        # חישוב משוקלל של כל הממדים
        total = (
            w.demand_weight * s.demand_score
            + w.growth_weight * s.growth_score
            + w.job_market_weight * s.job_market_score
            + w.trend_weight * s.trend_score
            + w.content_gap_weight * s.content_gap_score
            + w.localization_fit_weight * s.localization_fit_score
            + w.teachability_weight * s.teachability_score
            + w.strategic_fit_weight * s.strategic_fit_score
        )

        # עיגול ל-4 ספרות + הגבלה לטווח 0–1
        total_score = round(max(0.0, min(1.0, total)), 4)

        # שמירת פירוט הציון כמו שהוא (ציוני הממדים כבר בטווח 0–1)
        breakdown = ScoreBreakdown(
            demand_score=s.demand_score,
            growth_score=s.growth_score,
            job_market_score=s.job_market_score,
            trend_score=s.trend_score,
            content_gap_score=s.content_gap_score,
            localization_fit_score=s.localization_fit_score,
            teachability_score=s.teachability_score,
            strategic_fit_score=s.strategic_fit_score,
        )

        return total_score, breakdown

    def compute_confidence(self, signal: SignalVector) -> float:
        """
        מחשב ציון ביטחון מותאם על בסיס הביטחון הבסיסי של הוקטור.

        מנגנוני הורדת ביטחון:
        - פחות מ-2 משפחות מקור: כפל ב-0.85
        - פחות מ-3 ראיות: כפל ב-0.90
        - בדיוק משפחת מקור אחת: כפל נוסף ב-0.80

        Args:
            signal: SignalVector עם שדות ביטחון, evidence_count ו-source_families.

        Returns:
            float בטווח [0.10, 1.0].
        """
        confidence = signal.confidence_score
        num_families = len(signal.source_families)

        # עונש על פחות מ-2 משפחות מקור
        if num_families < 2:
            confidence *= 0.85

        # עונש על מספר ראיות נמוך
        if signal.evidence_count < 3:
            confidence *= 0.90

        # עונש נוסף על מקור יחיד בלבד
        if num_families == 1:
            confidence *= 0.80

        # רצפה של 0.10 — לעולם לא נחזיר ביטחון אפסי לחלוטין
        return round(max(0.10, min(1.0, confidence)), 4)

    def classify(self, total_score: float) -> OpportunityClassification:
        """
        מסווג הזדמנות לפי ציון כולל.

        סף         | סיווג
        ---------- | ---------------
        >= 0.80    | immediate
        >= 0.65    | near_term
        >= 0.50    | watchlist
        >= 0.35    | low_priority
        < 0.35     | rejected

        Args:
            total_score: ציון כולל בטווח [0, 1].

        Returns:
            OpportunityClassification המתאים.
        """
        if total_score >= 0.80:
            return OpportunityClassification.immediate
        elif total_score >= 0.65:
            return OpportunityClassification.near_term
        elif total_score >= 0.50:
            return OpportunityClassification.watchlist
        elif total_score >= 0.35:
            return OpportunityClassification.low_priority
        else:
            return OpportunityClassification.rejected

    def rank_signals(
        self, signals: list[SignalVector]
    ) -> list[tuple[SignalVector, float, ScoreBreakdown]]:
        """
        מחשב ציון לכל וקטור ומחזיר רשימה ממוינת בסדר יורד.

        Args:
            signals: רשימת SignalVector לדירוג.

        Returns:
            רשימת tuple של (signal, total_score, breakdown) ממוינת
            בסדר יורד לפי total_score.
        """
        scored = []
        for signal in signals:
            total_score, breakdown = self.compute_score(signal)
            scored.append((signal, total_score, breakdown))

        # מיון יורד לפי ציון — דטרמיניסטי: stable sort לפי entity_name בעת שוויון
        scored.sort(key=lambda t: (t[1], t[0].entity_name), reverse=True)

        return scored
