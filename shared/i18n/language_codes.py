"""
קודי שפות נתמכות, זיהוי שפות RTL ומיפוי קנוני לקודי ISO 639-1.
"""

# שפות הנתמכות כרגע על ידי המערכת
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "he": "Hebrew",
}

# שפות הנכתבות מימין לשמאל (RTL)
RTL_LANGUAGES: set[str] = {"he", "ar", "fa", "ur"}

# מיפוי גרסאות נפוצות של שמות שפות לקודי ISO 639-1
CANONICAL_LANGUAGE_MAP: dict[str, str] = {
    # אנגלית
    "english": "en",
    "eng": "en",
    # עברית
    "hebrew": "he",
    "heb": "he",
    "עברית": "he",
    # ערבית
    "arabic": "ar",
    "ara": "ar",
    "عربي": "ar",
    "عربية": "ar",
    # פרסית
    "persian": "fa",
    "farsi": "fa",
    "fas": "fa",
    "فارسی": "fa",
    # אורדו
    "urdu": "ur",
    "urd": "ur",
    "اردو": "ur",
    # ספרדית
    "spanish": "es",
    "español": "es",
    "spa": "es",
    # צרפתית
    "french": "fr",
    "français": "fr",
    "fra": "fr",
    # גרמנית
    "german": "de",
    "deutsch": "de",
    "deu": "de",
    # פורטוגזית
    "portuguese": "pt",
    "português": "pt",
    "por": "pt",
}


def is_rtl(language_code: str) -> bool:
    """
    בודק אם שפה נכתבת מימין לשמאל.

    Args:
        language_code: קוד שפה לפי ISO 639-1 (לדוגמה: "he", "ar").

    Returns:
        True אם השפה היא RTL, אחרת False.
    """
    return language_code.lower() in RTL_LANGUAGES


def is_supported(language_code: str) -> bool:
    """
    בודק אם קוד השפה נתמך על ידי המערכת.

    Args:
        language_code: קוד שפה לפי ISO 639-1.

    Returns:
        True אם השפה נתמכת, אחרת False.
    """
    return language_code.lower() in SUPPORTED_LANGUAGES
