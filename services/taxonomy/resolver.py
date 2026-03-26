"""
Taxonomy Resolver — resolves raw labels to canonical taxonomy entities.
Uses in-memory alias maps for MVP. Designed to be backed by DB in production.
"""
from dataclasses import dataclass
import re


@dataclass
class ResolvedSkill:
    canonical_name: str
    confidence: float
    matched_alias: str | None = None


@dataclass
class ResolvedTopic:
    canonical_name: str
    confidence: float
    matched_alias: str | None = None


# Canonical skills with known aliases
CANONICAL_SKILLS: dict[str, set[str]] = {
    "Python": {"python programming", "python3", "python development", "python dev"},
    "Machine Learning": {"ml", "machine-learning", "ai/ml"},
    "Data Engineering": {"data pipelines", "etl", "data infrastructure"},
    "React": {"reactjs", "react.js", "react development"},
    "TypeScript": {"ts", "typescript development"},
    "SQL": {"mysql", "postgresql", "postgres", "database querying"},
    "Cloud Computing": {"aws", "azure", "gcp", "cloud infrastructure", "cloud platforms"},
    "DevOps": {"ci/cd", "devops engineering", "platform engineering"},
    "Cybersecurity": {"information security", "infosec", "network security"},
    "Product Management": {"product manager", "pm"},
    "Prompt Engineering": {"llm prompting", "prompt design", "ai prompting"},
    "Generative AI": {"genai", "gen ai", "generative artificial intelligence", "ai generation"},
    "MLOps": {"ml operations", "ml infrastructure", "model deployment"},
    "Data Analysis": {"data analytics", "data analyst skills"},
    "Project Management": {"pm skills", "scrum", "agile"},
}

# Canonical topics with known aliases
CANONICAL_TOPICS: dict[str, set[str]] = {
    "Artificial Intelligence": {"ai", "artificial intelligence basics"},
    "Data Science": {"data science fundamentals"},
    "Web Development": {"web dev", "frontend development", "backend development"},
    "Cybersecurity Fundamentals": {"cyber basics", "information security fundamentals"},
    "Cloud Architecture": {"cloud design patterns", "cloud solutions"},
    "Product Design": {"ux design", "ui/ux", "user experience design"},
    "Leadership & Management": {"management skills", "leadership development"},
    "Agile & Scrum": {"agile methodology", "scrum framework", "agile practices"},
    "Data Engineering Fundamentals": {"data pipeline basics", "etl fundamentals"},
    "Prompt Engineering": {"llm usage", "ai prompting techniques"},
}

COUNTRY_ALIASES: dict[str, str] = {
    "israel": "IL", "il": "IL",
    "united states": "US", "usa": "US", "us": "US", "america": "US",
    "united kingdom": "GB", "uk": "GB", "england": "GB",
    "germany": "DE", "deutschland": "DE", "de": "DE",
    "india": "IN", "in": "IN",
}

LANGUAGE_ALIASES: dict[str, str] = {
    "hebrew": "he", "he": "he",
    "english": "en", "en": "en",
    "arabic": "ar", "ar": "ar",
    "german": "de", "de": "de",
}


class TaxonomyResolver:
    """Resolves raw labels to canonical taxonomy entities using in-memory alias maps."""

    def __init__(self) -> None:
        # Build reverse lookup: alias -> canonical name
        self._skill_alias_map: dict[str, str] = {}
        for canonical, aliases in CANONICAL_SKILLS.items():
            self._skill_alias_map[canonical.lower()] = canonical
            for alias in aliases:
                self._skill_alias_map[alias.lower()] = canonical

        self._topic_alias_map: dict[str, str] = {}
        for canonical, aliases in CANONICAL_TOPICS.items():
            self._topic_alias_map[canonical.lower()] = canonical
            for alias in aliases:
                self._topic_alias_map[alias.lower()] = canonical

    def resolve_skill(self, raw_label: str) -> ResolvedSkill | None:
        """Resolve a raw skill label to a canonical skill."""
        normalized = self._normalize(raw_label)
        if not normalized:
            return None

        # Direct match
        if normalized in self._skill_alias_map:
            return ResolvedSkill(
                canonical_name=self._skill_alias_map[normalized],
                confidence=1.0 if normalized == self._skill_alias_map[normalized].lower() else 0.85,
                matched_alias=raw_label if normalized != self._skill_alias_map[normalized].lower() else None,
            )

        # Substring match: check if any canonical name is in the label or vice versa
        for canonical_lower, canonical_name in self._skill_alias_map.items():
            if canonical_lower in normalized or normalized in canonical_lower:
                if len(normalized) >= 3:  # Avoid very short spurious matches
                    return ResolvedSkill(
                        canonical_name=canonical_name,
                        confidence=0.60,
                        matched_alias=raw_label,
                    )

        return None

    def resolve_topic(self, raw_label: str) -> ResolvedTopic | None:
        """Resolve a raw topic label to a canonical topic."""
        normalized = self._normalize(raw_label)
        if not normalized:
            return None

        # Direct match
        if normalized in self._topic_alias_map:
            return ResolvedTopic(
                canonical_name=self._topic_alias_map[normalized],
                confidence=1.0 if normalized == self._topic_alias_map[normalized].lower() else 0.85,
                matched_alias=raw_label if normalized != self._topic_alias_map[normalized].lower() else None,
            )

        # Substring match
        for canonical_lower, canonical_name in self._topic_alias_map.items():
            if canonical_lower in normalized or normalized in canonical_lower:
                if len(normalized) >= 3:
                    return ResolvedTopic(
                        canonical_name=canonical_name,
                        confidence=0.60,
                        matched_alias=raw_label,
                    )

        return None

    def resolve_country_code(self, raw: str) -> str | None:
        """Resolve a raw country label to ISO 3166-1 alpha-2 code."""
        normalized = raw.strip().lower()
        return COUNTRY_ALIASES.get(normalized)

    def resolve_language_code(self, raw: str) -> str | None:
        """Resolve a raw language label to ISO 639-1 code."""
        normalized = raw.strip().lower()
        return LANGUAGE_ALIASES.get(normalized)

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for matching: lowercase, strip, collapse whitespace."""
        text = text.strip().lower()
        text = re.sub(r"\s+", " ", text)
        return text
