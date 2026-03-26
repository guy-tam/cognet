"""
Normalizer — ממיר RawSourceRecord ל-NormalizedRecord.
אחריות: ניקוי טקסט, קודים קנוניים, מפתח dedup, שמירת מוצא מקור.
"""

import re
from datetime import datetime, timezone

from shared.contracts.normalized_record import NormalizedRecord
from shared.contracts.raw_record import RawSourceRecord
from shared.enums.pipeline import NormalizationStatus, SourceType
from shared.utils.hashing import compute_dedup_key


# מיפוי קודי שפה לצורה קנונית
CANONICAL_LANGUAGE_MAP: dict[str, str] = {
    "english": "en",
    "hebrew": "he",
    "arabic": "ar",
    "russian": "ru",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "portuguese": "pt",
    "chinese": "zh",
    "japanese": "ja",
    # קודים שכבר קנוניים — העברה ישירה
    "en": "en",
    "he": "he",
    "ar": "ar",
    "ru": "ru",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "pt": "pt",
    "zh": "zh",
    "ja": "ja",
}

# מיפוי SourceType לסוג רשומה מנורמל
_SOURCE_TYPE_TO_RECORD_TYPE: dict[str, str] = {
    SourceType.job_postings.value: "job_posting",
    SourceType.trend_signals.value: "trend_signal",
    SourceType.internal_supply.value: "learning_asset",
}

# regex לניקוי תגי HTML
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
# regex לצמצום רווחים מרובים
_WHITESPACE_PATTERN = re.compile(r"\s+")


class Normalizer:
    """מנרמל RawSourceRecord לפורמט אחיד וקנוני."""

    def normalize(self, raw: RawSourceRecord) -> NormalizedRecord:
        """
        ממיר רשומה גולמית לרשומה מנורמלת.

        שלבי העיבוד:
        1. חילוץ כותרת ממפתחות אפשריים (title, keyword, name)
        2. חילוץ טקסט ממפתחות אפשריים (description, summary, text)
        3. ניקוי טקסט: הסרת HTML, צמצום רווחים, trim
        4. קנוניזציה של שפה ומדינה
        5. קביעת record_type לפי source_type
        6. חישוב dedup_key

        Args:
            raw: RawSourceRecord לנרמול.

        Returns:
            NormalizedRecord מוכן להעשרה.
        """
        payload = raw.payload

        # חילוץ כותרת — ניסיון לפי סדר עדיפות
        raw_title = (
            payload.get("title")
            or payload.get("keyword")
            or payload.get("name")
            or ""
        )
        normalized_title = self._clean_text(str(raw_title)) or "untitled"

        # חילוץ טקסט — ניסיון לפי סדר עדיפות
        raw_text = (
            payload.get("description")
            or payload.get("summary")
            or payload.get("text")
        )
        normalized_text = self._clean_text(raw_text) if raw_text else None

        # קנוניזציה של שפה
        lang_raw = raw.language_code or payload.get("language_code") or payload.get("language")
        canonical_language = self._canonicalize_language(lang_raw)

        # קנוניזציה של מדינה — uppercase + strip
        country_raw = raw.country_code or payload.get("country_code")
        canonical_country = self._canonicalize_country(country_raw)

        # קביעת סוג הרשומה
        record_type = self._determine_record_type(raw.source_type.value)

        # חישוב מפתח dedup דטרמיניסטי
        dedup_key = compute_dedup_key(
            source_type=raw.source_type.value,
            external_id=raw.external_id,
            normalized_title=normalized_title,
            country_code=canonical_country,
        )

        return NormalizedRecord(
            raw_record_id=raw.id or _generate_placeholder_id(),
            source_name=raw.source_name,
            source_type=raw.source_type,
            normalized_title=normalized_title,
            normalized_text=normalized_text,
            canonical_language=canonical_language,
            canonical_country=canonical_country,
            canonical_region=raw.region_code,
            record_type=record_type,
            dedup_key=dedup_key,
            normalization_status=NormalizationStatus.normalized,
            created_at=datetime.now(tz=timezone.utc),
            source_run_id=raw.source_run_id,
        )

    def _clean_text(self, text: str | None) -> str | None:
        """
        מנקה טקסט: מסיר תגי HTML, מצמצם רווחים ומבצע trim.

        Args:
            text: טקסט לניקוי, או None.

        Returns:
            טקסט נקי, או None אם הקלט היה None.
        """
        if text is None:
            return None

        # הסרת תגי HTML
        cleaned = _HTML_TAG_PATTERN.sub(" ", text)

        # צמצום רווחים מרובים (כולל newlines, tabs)
        cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned)

        # trim
        cleaned = cleaned.strip()

        return cleaned if cleaned else None

    def _determine_record_type(self, source_type: str) -> str:
        """
        קובע את סוג הרשומה המנורמלת לפי סוג המקור.

        job_postings    → "job_posting"
        trend_signals   → "trend_signal"
        internal_supply → "learning_asset"

        Args:
            source_type: מחרוזת סוג המקור.

        Returns:
            מחרוזת סוג הרשומה.
        """
        return _SOURCE_TYPE_TO_RECORD_TYPE.get(source_type, "unknown")

    def _canonicalize_language(self, lang: str | None) -> str | None:
        """
        ממיר קוד שפה גולמי לצורה קנונית.

        Args:
            lang: קוד שפה גולמי (יכול להיות שם מלא כמו "English" או קוד כמו "en").

        Returns:
            קוד שפה קנוני כ-lowercase, או None אם לא זוהה.
        """
        if not lang:
            return None
        normalized = lang.lower().strip()
        return CANONICAL_LANGUAGE_MAP.get(normalized, normalized[:2] if len(normalized) >= 2 else None)

    def _canonicalize_country(self, country: str | None) -> str | None:
        """
        ממיר קוד מדינה גולמי לצורה קנונית — uppercase alpha-2.

        Args:
            country: קוד מדינה גולמי.

        Returns:
            קוד מדינה קנוני כ-uppercase, או None אם ריק.
        """
        if not country:
            return None
        return country.upper().strip()[:2]


def _generate_placeholder_id():
    """מייצר UUID זמני כ-placeholder עבור raw_record_id חסר."""
    import uuid
    return uuid.uuid4()
