"""
Stack Overflow Connector — fetches real tag and question data from the public Stack Overflow API.
No API key needed for basic usage (300 requests/day without key).
"""
import uuid
import logging
from datetime import datetime, timezone

import httpx

from services.ingestion.base_connector import BaseConnector
from shared.contracts.raw_record import RawSourceRecord
from shared.enums.pipeline import SourceType

logger = logging.getLogger(__name__)

# Tags to track (matching our taxonomy)
TRACKED_TAGS = [
    "python", "machine-learning", "react", "typescript", "kubernetes",
    "docker", "aws", "azure", "sql", "data-science", "deep-learning",
    "devops", "cybersecurity", "generative-ai", "prompt-engineering",
    "mlops", "data-engineering", "nextjs", "fastapi", "terraform",
    "rust", "golang", "flutter", "blockchain", "web3",
]

SO_API_BASE = "https://api.stackexchange.com/2.3"


class StackOverflowConnector(BaseConnector):
    """Fetches real Stack Overflow tag popularity and recent question data."""

    source_name = "stackoverflow"
    source_type = SourceType.trend_signals
    trust_tier = "tier_1_high"

    async def fetch(self, run_id: uuid.UUID, **kwargs) -> list[dict]:
        """Fetch tag info and recent questions from Stack Overflow."""
        logger.info(f"StackOverflowConnector: fetching data for {len(TRACKED_TAGS)} tags")
        results = []

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Fetch tag info in batches
            for i in range(0, len(TRACKED_TAGS), 20):
                batch = TRACKED_TAGS[i:i+20]
                tags_str = ";".join(batch)
                try:
                    resp = await client.get(
                        f"{SO_API_BASE}/tags/{tags_str}/info",
                        params={"site": "stackoverflow", "filter": "default"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for item in data.get("items", []):
                            results.append({
                                "keyword": item.get("name", ""),
                                "tag_count": item.get("count", 0),
                                "has_synonyms": item.get("has_synonyms", False),
                                "is_required": item.get("is_required", False),
                                "source_note": "tag_info",
                                "trend_direction": "stable",  # Will be computed from question activity
                                "search_volume_index": min(100, int(item.get("count", 0) / 10000)),
                                "captured_at": datetime.now(timezone.utc).isoformat(),
                            })
                except Exception as e:
                    logger.warning(f"StackOverflow tag info failed: {e}")

            # Fetch recent questions for top tags to gauge activity
            for tag in TRACKED_TAGS[:10]:
                try:
                    resp = await client.get(
                        f"{SO_API_BASE}/questions",
                        params={
                            "site": "stackoverflow",
                            "tagged": tag,
                            "sort": "creation",
                            "order": "desc",
                            "pagesize": 5,
                            "filter": "default",
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        questions = data.get("items", [])
                        for q in questions:
                            results.append({
                                "keyword": tag,
                                "title": q.get("title", ""),
                                "score": q.get("score", 0),
                                "view_count": q.get("view_count", 0),
                                "answer_count": q.get("answer_count", 0),
                                "tags": q.get("tags", []),
                                "creation_date": q.get("creation_date", 0),
                                "source_note": "recent_question",
                                "trend_direction": "rising" if q.get("score", 0) > 5 else "stable",
                                "search_volume_index": min(100, q.get("view_count", 0) // 100),
                                "captured_at": datetime.now(timezone.utc).isoformat(),
                            })
                except Exception as e:
                    logger.warning(f"StackOverflow questions for {tag} failed: {e}")

        logger.info(f"StackOverflowConnector: fetched {len(results)} records")
        return results

    def parse(self, raw_item: dict, run_id: uuid.UUID) -> RawSourceRecord:
        return RawSourceRecord(
            source_name=self.source_name,
            source_type=self.source_type,
            external_id=f"so_{raw_item.get('keyword', '')}_{raw_item.get('source_note', '')}",
            collected_at=datetime.now(timezone.utc),
            language_code="en",
            country_code=None,
            payload=raw_item,
            checksum=RawSourceRecord.compute_checksum(raw_item),
            source_run_id=run_id,
            trust_tier=self.trust_tier,
        )
