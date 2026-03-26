"""
Hacker News Connector — fetches top stories and job postings from the HN API.
Completely free, no API key, no rate limits.
"""
import uuid
import logging
from datetime import datetime, timezone

import httpx

from services.ingestion.base_connector import BaseConnector
from shared.contracts.raw_record import RawSourceRecord
from shared.enums.pipeline import SourceType

logger = logging.getLogger(__name__)

HN_API = "https://hacker-news.firebaseio.com/v0"


class HackerNewsConnector(BaseConnector):
    """Fetches real HN top stories and job posts to gauge tech topic demand."""

    source_name = "hackernews"
    source_type = SourceType.job_postings  # HN has both tech discussion and job posts
    trust_tier = "tier_2_medium"

    async def fetch(self, run_id: uuid.UUID, max_stories: int = 50, **kwargs) -> list[dict]:
        """Fetch top stories and job stories from Hacker News."""
        logger.info("HackerNewsConnector: fetching top stories and jobs")
        results = []

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Top stories
            try:
                resp = await client.get(f"{HN_API}/topstories.json")
                story_ids = resp.json()[:max_stories]

                for sid in story_ids:
                    try:
                        r = await client.get(f"{HN_API}/item/{sid}.json")
                        story = r.json()
                        if story and story.get("title"):
                            results.append({
                                "title": story.get("title", ""),
                                "url": story.get("url", ""),
                                "score": story.get("score", 0),
                                "comments": story.get("descendants", 0),
                                "by": story.get("by", ""),
                                "time": story.get("time", 0),
                                "type": story.get("type", "story"),
                                "source_note": "top_story",
                                "captured_at": datetime.now(timezone.utc).isoformat(),
                            })
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"HN top stories failed: {e}")

            # Job stories
            try:
                resp = await client.get(f"{HN_API}/jobstories.json")
                job_ids = resp.json()[:30]

                for jid in job_ids:
                    try:
                        r = await client.get(f"{HN_API}/item/{jid}.json")
                        job = r.json()
                        if job and job.get("title"):
                            results.append({
                                "title": job.get("title", ""),
                                "url": job.get("url", ""),
                                "text": (job.get("text", "") or "")[:500],
                                "by": job.get("by", ""),
                                "time": job.get("time", 0),
                                "type": "job",
                                "source_note": "job_posting",
                                "captured_at": datetime.now(timezone.utc).isoformat(),
                            })
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"HN job stories failed: {e}")

        logger.info(f"HackerNewsConnector: fetched {len(results)} records")
        return results

    def parse(self, raw_item: dict, run_id: uuid.UUID) -> RawSourceRecord:
        return RawSourceRecord(
            source_name=self.source_name,
            source_type=self.source_type,
            external_id=f"hn_{raw_item.get('title', 'unknown')[:50]}",
            collected_at=datetime.now(timezone.utc),
            language_code="en",
            country_code=None,
            payload=raw_item,
            checksum=RawSourceRecord.compute_checksum(raw_item),
            source_run_id=run_id,
            trust_tier=self.trust_tier,
        )
