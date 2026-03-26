"""
Signal Computer — מחשב SignalVector מנתוני מקור מועשרים.
צבירה דטרמיניסטית של אותות ביקוש, צמיחה, שוק עבודה ומגמות.
"""

import uuid
from datetime import datetime

from shared.contracts.signal_vector import ScoreBreakdown, SignalVector
from shared.enums.signals import SignalEntityType
from shared.utils.time import utcnow


class SignalComputer:
    """מחשב SignalVector מנתונים מועשרים באמצעות לוגיקת צבירה דטרמיניסטית."""

    def __init__(self, country_code: str, language_code: str) -> None:
        """
        מאתחל את ה-SignalComputer עבור שוק גיאוגרפי/שפתי ספציפי.

        Args:
            country_code: קוד מדינה לפי ISO 3166-1 alpha-2 (לדוגמה: "IL").
            language_code: קוד שפה לפי ISO 639-1 (לדוגמה: "he").
        """
        self.country_code = country_code
        self.language_code = language_code

    def compute_demand_score(
        self,
        job_posting_count: int,
        trend_mention_count: int,
        total_records: int,
    ) -> float:
        """
        מחשב ציון ביקוש מנורמל על בסיס מודעות משרה ואזכורי מגמה.

        נוסחה: (job_posting_count + trend_mention_count * 0.5) / max(total_records, 1)
        הציון מוגבל לטווח [0, 1].

        Args:
            job_posting_count: מספר מודעות משרה רלוונטיות.
            trend_mention_count: מספר אזכורי מגמה.
            total_records: סך הרשומות לנרמול.

        Returns:
            float בטווח [0.0, 1.0].
        """
        raw = (job_posting_count + trend_mention_count * 0.5) / max(total_records, 1)
        return max(0.0, min(1.0, raw))

    def compute_growth_score(self, recent_count: int, older_count: int) -> float:
        """
        מחשב ציון צמיחה על בסיס השוואת תקופות.

        אם older_count == 0 מוחזר 0.5 (ניטרלי — אין נתוני בסיס להשוואה).
        אחרת ratio = recent_count / older_count, ממופה לפי:
            ratio > 2.0  → 1.0
            ratio = 1.5  → 0.8
            ratio = 1.0  → 0.5
            ratio = 0.5  → 0.2
            ratio < 0.25 → 0.0
        אינטרפולציה לינארית בין הסף.

        Args:
            recent_count: ספירת פריטים בתקופה האחרונה.
            older_count: ספירת פריטים בתקופה הישנה יותר.

        Returns:
            float בטווח [0.0, 1.0].
        """
        if older_count == 0:
            # אין נתוני בסיס — ציון ניטרלי
            return 0.5

        ratio = recent_count / older_count

        # מיפוי לפי נקודות עוגן עם אינטרפולציה לינארית
        if ratio >= 2.0:
            return 1.0
        elif ratio >= 1.5:
            # אינטרפולציה בין 1.5→0.8 ו-2.0→1.0
            t = (ratio - 1.5) / (2.0 - 1.5)
            return 0.8 + t * (1.0 - 0.8)
        elif ratio >= 1.0:
            # אינטרפולציה בין 1.0→0.5 ו-1.5→0.8
            t = (ratio - 1.0) / (1.5 - 1.0)
            return 0.5 + t * (0.8 - 0.5)
        elif ratio >= 0.5:
            # אינטרפולציה בין 0.5→0.2 ו-1.0→0.5
            t = (ratio - 0.5) / (1.0 - 0.5)
            return 0.2 + t * (0.5 - 0.2)
        elif ratio >= 0.25:
            # אינטרפולציה בין 0.25→0.0 ו-0.5→0.2
            t = (ratio - 0.25) / (0.5 - 0.25)
            return 0.0 + t * (0.2 - 0.0)
        else:
            return 0.0

    def compute_content_gap_score(
        self, demand_level: float, supply_coverage: float
    ) -> float:
        """
        מחשב ציון פער תוכן — עד כמה קיים חסר בין ביקוש להיצע.

        gap = demand_level - supply_coverage
        ציון = clamp(0, 1, 0.5 + gap)

        ביקוש גבוה + היצע נמוך → ציון גבוה (פער גדול)
        ביקוש נמוך + היצע גבוה → ציון נמוך (היצע עולה על ביקוש)

        Args:
            demand_level: ציון ביקוש בטווח [0, 1].
            supply_coverage: כיסוי ההיצע הקיים בטווח [0, 1].

        Returns:
            float בטווח [0.0, 1.0].
        """
        gap = demand_level - supply_coverage
        return max(0.0, min(1.0, 0.5 + gap))

    def build_signal_vector(
        self,
        entity_name: str,
        entity_type: str,
        scores: dict,
        evidence_count: int,
        source_families: list[str],
        run_id: uuid.UUID,
        confidence_score: float = 1.0,
        entity_id: uuid.UUID | None = None,
    ) -> SignalVector:
        """
        בונה SignalVector מציוני ממדים מחושבים.

        Args:
            entity_name: שם הישות (כישור, נושא, תפקיד וכו').
            entity_type: סוג הישות כמחרוזת (מומר ל-SignalEntityType).
            scores: מילון עם ציוני הממדים השונים.
            evidence_count: מספר הראיות שתרמו לחישוב.
            source_families: רשימת משפחות מקורות שתרמו.
            run_id: מזהה ריצת ה-pipeline.
            confidence_score: ציון ביטחון בסיסי (ברירת מחדל: 1.0).
            entity_id: מזהה פנימי של הישות (אופציונלי).

        Returns:
            SignalVector מוכן לדירוג.
        """
        # המרת מחרוזת entity_type ל-enum
        entity_type_enum = SignalEntityType(entity_type)

        # בניית ScoreBreakdown מהמילון — ערכים חסרים ישתמשו ב-0.0
        breakdown = ScoreBreakdown(
            demand_score=float(scores.get("demand_score", 0.0)),
            growth_score=float(scores.get("growth_score", 0.0)),
            job_market_score=float(scores.get("job_market_score", 0.0)),
            trend_score=float(scores.get("trend_score", 0.0)),
            content_gap_score=float(scores.get("content_gap_score", 0.0)),
            localization_fit_score=float(scores.get("localization_fit_score", 0.0)),
            teachability_score=float(scores.get("teachability_score", 0.0)),
            strategic_fit_score=float(scores.get("strategic_fit_score", 0.0)),
        )

        return SignalVector(
            entity_type=entity_type_enum,
            entity_id=entity_id,
            entity_name=entity_name,
            country_code=self.country_code,
            language_code=self.language_code,
            scores=breakdown,
            confidence_score=max(0.0, min(1.0, confidence_score)),
            evidence_count=evidence_count,
            source_families=list(source_families),
            run_id=run_id,
            computed_at=utcnow(),
        )
