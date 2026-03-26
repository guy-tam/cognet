"""
משקלי ציון ברירת מחדל עבור מנוע הדירוג של COGNET LDI Engine.
GOVERNANCE: שינויים במשקלים אלו חייבים לעבור את תהליך ניהול הציונים
המתועד ב: /docs/governance/scoring-governance.md
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringWeights:
    """משקלי ציון ניתנים להגדרה עבור כל ממד ציון."""

    # משקל ביקוש — כמה גבוה הביקוש הכולל לתוכן
    demand_weight: float = 0.20
    # משקל צמיחה — מגמת עלייה לאורך זמן
    growth_weight: float = 0.15
    # משקל שוק עבודה — נוכחות במודעות משרה
    job_market_weight: float = 0.20
    # משקל מגמות — רלוונטיות לטרנדים עדכניים
    trend_weight: float = 0.10
    # משקל פער תוכן — היצע נמוך מול ביקוש גבוה
    content_gap_weight: float = 0.15
    # משקל התאמה לוקאלית — שוק/שפה ספציפיים
    localization_fit_weight: float = 0.05
    # משקל למדותיות — ניתן לבנות תוכן לימודי
    teachability_weight: float = 0.05
    # משקל התאמה אסטרטגית — יישור עם יעדי הארגון
    strategic_fit_weight: float = 0.10

    def __post_init__(self) -> None:
        """מוודא שסכום המשקלים שווה ל-1.0."""
        total = (
            self.demand_weight
            + self.growth_weight
            + self.job_market_weight
            + self.trend_weight
            + self.content_gap_weight
            + self.localization_fit_weight
            + self.teachability_weight
            + self.strategic_fit_weight
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"סכום משקלי הציון חייב להיות 1.0, קיבלנו {total:.4f}")


# משקלי ברירת מחדל — בשימוש אם לא הוגדרו משקלים מותאמים
DEFAULT_WEIGHTS = ScoringWeights()
