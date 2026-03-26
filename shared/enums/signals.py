"""
אנומים עבור אותות (signals) — סוגי ישויות ורמות אמינות מקור.
"""

from enum import Enum


class SignalEntityType(str, Enum):
    """סוג הישות שהאות מתייחס אליה."""

    skill = "skill"
    topic = "topic"
    role = "role"
    industry = "industry"


class SourceTrustTier(str, Enum):
    """רמת האמינות של מקור הנתונים."""

    # מקורות אמינים ומוסמכים (לדוגמה: LinkedIn, Indeed)
    tier_1_high = "tier_1_high"
    # מקורות בינוניים (לדוגמה: אתרי גיוס אזוריים)
    tier_2_medium = "tier_2_medium"
    # מקורות ניסיוניים — דורשים אימות נוסף
    tier_3_experimental = "tier_3_experimental"
