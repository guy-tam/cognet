"""
Google Trends Connector — fetches REAL trending search data via pytrends.
No API key needed. Uses the unofficial Google Trends API.
"""
import uuid
import logging
from datetime import datetime, timezone

from pytrends.request import TrendReq

from services.ingestion.base_connector import BaseConnector
from shared.contracts.raw_record import RawSourceRecord
from shared.enums.pipeline import SourceType

logger = logging.getLogger(__name__)

# Topics to track — these are the learning/tech topics we care about
TRACKED_TOPICS = [
    "Python programming",
    "machine learning",
    "data engineering",
    "React javascript",
    "cloud computing",
    "cybersecurity",
    "generative AI",
    "prompt engineering",
    "DevOps",
    "Kubernetes",
    "data science",
    "product management",
    "SQL database",
    "TypeScript",
    "MLOps",
]

# Can also do dynamic trending searches
TRENDING_CATEGORIES = {
    "technology": 5,   # Google Trends category ID for Computers & Electronics
    "education": 958,  # Online Education
    "jobs": 60,        # Jobs & Education
}


class GoogleTrendsConnector(BaseConnector):
    """Fetches real Google Trends data for tracked learning topics."""

    source_name = "google_trends"
    source_type = SourceType.trend_signals
    trust_tier = "tier_2_medium"

    def __init__(self, timeframe: str = "today 3-m"):
        self.timeframe = timeframe
        self._pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))

    async def fetch(self, run_id: uuid.UUID, country_code: str = "IL", **kwargs) -> list[dict]:
        """Fetch real Google Trends data for tracked topics."""
        logger.info(f"GoogleTrendsConnector: fetching trends for {len(TRACKED_TOPICS)} topics")
        results = []

        # Map country codes to Google Trends geo codes
        geo_map = {
            "IL": "IL", "US": "US", "GB": "GB", "DE": "DE", "IN": "IN",
            "FR": "FR", "CA": "CA", "AU": "AU", "BR": "BR", "JP": "JP",
        }
        geo = geo_map.get(country_code, "")

        # Fetch interest over time in batches of 5 (Google Trends limit)
        for i in range(0, len(TRACKED_TOPICS), 5):
            batch = TRACKED_TOPICS[i:i+5]
            try:
                self._pytrends.build_payload(batch, timeframe=self.timeframe, geo=geo)

                # Interest over time
                interest_df = self._pytrends.interest_over_time()
                if interest_df is not None and not interest_df.empty:
                    for keyword in batch:
                        if keyword in interest_df.columns:
                            series = interest_df[keyword]
                            recent_avg = float(series[-4:].mean()) if len(series) >= 4 else float(series.mean())
                            older_avg = float(series[:4].mean()) if len(series) >= 4 else float(series.mean())

                            # Determine trend direction
                            if recent_avg > older_avg * 1.2:
                                direction = "rising"
                            elif recent_avg < older_avg * 0.8:
                                direction = "declining"
                            else:
                                direction = "stable"

                            current_value = int(series.iloc[-1]) if len(series) > 0 else 0
                            peak_value = int(series.max())

                            results.append({
                                "keyword": keyword,
                                "search_volume_index": current_value,
                                "peak_volume_index": peak_value,
                                "average_volume": round(float(series.mean()), 1),
                                "recent_average": round(recent_avg, 1),
                                "older_average": round(older_avg, 1),
                                "trend_direction": direction,
                                "country_code": country_code,
                                "language_code": kwargs.get("language_code", "en"),
                                "timeframe": self.timeframe,
                                "data_points": len(series),
                                "captured_at": datetime.now(timezone.utc).isoformat(),
                            })

                # Also get related queries for each topic
                try:
                    related = self._pytrends.related_queries()
                    for keyword in batch:
                        if keyword in related and related[keyword].get("rising") is not None:
                            rising_df = related[keyword]["rising"]
                            if rising_df is not None and not rising_df.empty:
                                for _, row in rising_df.head(3).iterrows():
                                    results.append({
                                        "keyword": str(row.get("query", "")),
                                        "search_volume_index": 0,
                                        "trend_direction": "rising",
                                        "related_to": keyword,
                                        "rise_percentage": str(row.get("value", "")),
                                        "country_code": country_code,
                                        "language_code": kwargs.get("language_code", "en"),
                                        "timeframe": self.timeframe,
                                        "source_note": "related_rising_query",
                                        "captured_at": datetime.now(timezone.utc).isoformat(),
                                    })
                except Exception:
                    pass  # Related queries sometimes fail — non-critical

            except Exception as e:
                logger.warning(f"GoogleTrendsConnector: batch {batch} failed: {e}")
                continue

        # Also fetch trending searches for the region
        try:
            trending = self._pytrends.trending_searches(pn="israel" if country_code == "IL" else "united_states")
            if trending is not None and not trending.empty:
                for _, row in trending.head(10).iterrows():
                    topic = str(row.iloc[0]) if len(row) > 0 else ""
                    if topic:
                        results.append({
                            "keyword": topic,
                            "search_volume_index": 0,
                            "trend_direction": "rising",
                            "country_code": country_code,
                            "language_code": kwargs.get("language_code", "en"),
                            "source_note": "daily_trending",
                            "captured_at": datetime.now(timezone.utc).isoformat(),
                        })
        except Exception:
            pass  # Trending searches sometimes fail

        logger.info(f"GoogleTrendsConnector: fetched {len(results)} trend records")
        return results

    def parse(self, raw_item: dict, run_id: uuid.UUID) -> RawSourceRecord:
        """Parse a Google Trends result into a RawSourceRecord."""
        return RawSourceRecord(
            source_name=self.source_name,
            source_type=self.source_type,
            external_id=f"gtrends_{raw_item.get('keyword', 'unknown')}_{raw_item.get('country_code', '')}",
            collected_at=datetime.now(timezone.utc),
            language_code=raw_item.get("language_code"),
            country_code=raw_item.get("country_code"),
            payload=raw_item,
            checksum=RawSourceRecord.compute_checksum(raw_item),
            source_run_id=run_id,
            trust_tier=self.trust_tier,
        )
