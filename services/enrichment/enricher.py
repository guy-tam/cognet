"""
Enricher — extracts and maps skills, topics, roles from normalized records.
MVP: Rule-based extraction using taxonomy resolver. No LLM dependency.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from services.taxonomy.resolver import TaxonomyResolver
from shared.contracts.normalized_record import NormalizedRecord
from shared.contracts.enrichment import (
    EnrichmentOutput,
    EnrichedSkillRef,
    EnrichedTopicRef,
    EnrichedRoleRef,
)


class Enricher:
    """Rule-based enrichment using taxonomy resolver for skill/topic extraction."""

    def __init__(self, taxonomy_resolver: TaxonomyResolver | None = None) -> None:
        self.resolver = taxonomy_resolver or TaxonomyResolver()

    def enrich(self, record: NormalizedRecord) -> EnrichmentOutput:
        """Enrich a normalized record with skills, topics, and metadata."""
        text = self._combine_text(record)
        skills = self._extract_skills(text)
        topics = self._extract_topics(text)

        # Compute enrichment confidence based on extraction results
        if skills and topics:
            confidence = 1.0
        elif skills or topics:
            confidence = 0.7
        else:
            confidence = 0.5

        return EnrichmentOutput(
            normalized_record_id=record.id or uuid.uuid4(),
            skills=skills,
            topics=topics,
            roles=[],  # Role extraction not implemented in MVP
            industries=[],  # Industry extraction not implemented in MVP
            geographic_relevance=[record.canonical_country] if record.canonical_country else [],
            language_context=record.canonical_language,
            teachability_hint=None,
            enrichment_confidence=confidence,
            enriched_at=datetime.now(timezone.utc),
        )

    def _combine_text(self, record: NormalizedRecord) -> str:
        """Combine title and text fields for extraction."""
        parts = []
        if record.normalized_title:
            parts.append(record.normalized_title)
        if record.normalized_text:
            parts.append(record.normalized_text)
        return " ".join(parts)

    def _extract_skills(self, text: str) -> list[EnrichedSkillRef]:
        """Extract skills from text using taxonomy resolver."""
        seen: set[str] = set()
        results: list[EnrichedSkillRef] = []

        # Try resolving individual words and common multi-word patterns
        tokens = self._tokenize(text)
        for token in tokens:
            resolved = self.resolver.resolve_skill(token)
            if resolved and resolved.canonical_name not in seen:
                seen.add(resolved.canonical_name)
                results.append(EnrichedSkillRef(
                    skill_id=None,
                    skill_name=resolved.canonical_name,
                    confidence=resolved.confidence,
                    source_label=resolved.matched_alias or token,
                ))

        return results

    def _extract_topics(self, text: str) -> list[EnrichedTopicRef]:
        """Extract topics from text using taxonomy resolver."""
        seen: set[str] = set()
        results: list[EnrichedTopicRef] = []

        tokens = self._tokenize(text)
        for token in tokens:
            resolved = self.resolver.resolve_topic(token)
            if resolved and resolved.canonical_name not in seen:
                seen.add(resolved.canonical_name)
                results.append(EnrichedTopicRef(
                    topic_id=None,
                    topic_name=resolved.canonical_name,
                    confidence=resolved.confidence,
                ))

        return results

    def _tokenize(self, text: str) -> list[str]:
        """
        Extract tokens and multi-word phrases from text for matching.
        Returns individual words plus bigrams and trigrams.
        """
        text = text.lower().strip()
        # Remove special chars except hyphens and slashes (useful for terms like "ci/cd")
        text = re.sub(r"[^\w\s/\-]", " ", text)
        words = text.split()

        tokens = list(words)
        # Bigrams
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]} {words[i+1]}")
        # Trigrams
        for i in range(len(words) - 2):
            tokens.append(f"{words[i]} {words[i+1]} {words[i+2]}")

        return tokens
