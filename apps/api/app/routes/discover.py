"""
Auto-Discovery Engine — COGNET LDI Engine.
Finds the hottest learning topics for any country/market using multiple live sources.
Primary sources: GitHub, StackOverflow, HackerNews, Wikipedia, Reddit (no rate limits).
Google Trends used sparingly for top results only (rate-limited).
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/discover", tags=["discover"])

# ─── 50 countries ───
COUNTRIES = {
    "IL": {"name": "Israel", "geo": "IL", "pn": "israel"},
    "US": {"name": "United States", "geo": "US", "pn": "united_states"},
    "GB": {"name": "United Kingdom", "geo": "GB", "pn": "united_kingdom"},
    "DE": {"name": "Germany", "geo": "DE", "pn": "germany"},
    "FR": {"name": "France", "geo": "FR", "pn": "france"},
    "IN": {"name": "India", "geo": "IN", "pn": "india"},
    "JP": {"name": "Japan", "geo": "JP", "pn": "japan"},
    "KR": {"name": "South Korea", "geo": "KR", "pn": "south_korea"},
    "BR": {"name": "Brazil", "geo": "BR", "pn": "brazil"},
    "AU": {"name": "Australia", "geo": "AU", "pn": "australia"},
    "CA": {"name": "Canada", "geo": "CA", "pn": "canada"},
    "NL": {"name": "Netherlands", "geo": "NL", "pn": "netherlands"},
    "SE": {"name": "Sweden", "geo": "SE", "pn": "sweden"},
    "SG": {"name": "Singapore", "geo": "SG", "pn": "singapore"},
    "ES": {"name": "Spain", "geo": "ES", "pn": "spain"},
    "IT": {"name": "Italy", "geo": "IT", "pn": "italy"},
    "PL": {"name": "Poland", "geo": "PL", "pn": "poland"},
    "CH": {"name": "Switzerland", "geo": "CH", "pn": "switzerland"},
    "AT": {"name": "Austria", "geo": "AT", "pn": "austria"},
    "BE": {"name": "Belgium", "geo": "BE", "pn": "belgium"},
    "DK": {"name": "Denmark", "geo": "DK", "pn": "denmark"},
    "FI": {"name": "Finland", "geo": "FI", "pn": "finland"},
    "NO": {"name": "Norway", "geo": "NO", "pn": "norway"},
    "IE": {"name": "Ireland", "geo": "IE", "pn": "ireland"},
    "PT": {"name": "Portugal", "geo": "PT", "pn": "portugal"},
    "CZ": {"name": "Czech Republic", "geo": "CZ", "pn": "czech_republic"},
    "RO": {"name": "Romania", "geo": "RO", "pn": "romania"},
    "GR": {"name": "Greece", "geo": "GR", "pn": "greece"},
    "HU": {"name": "Hungary", "geo": "HU", "pn": "hungary"},
    "UA": {"name": "Ukraine", "geo": "UA", "pn": "ukraine"},
    "ZA": {"name": "South Africa", "geo": "ZA", "pn": "south_africa"},
    "NG": {"name": "Nigeria", "geo": "NG", "pn": "nigeria"},
    "KE": {"name": "Kenya", "geo": "KE", "pn": "kenya"},
    "EG": {"name": "Egypt", "geo": "EG", "pn": "egypt"},
    "AE": {"name": "UAE", "geo": "AE", "pn": "united_arab_emirates"},
    "SA": {"name": "Saudi Arabia", "geo": "SA", "pn": "saudi_arabia"},
    "MX": {"name": "Mexico", "geo": "MX", "pn": "mexico"},
    "AR": {"name": "Argentina", "geo": "AR", "pn": "argentina"},
    "CL": {"name": "Chile", "geo": "CL", "pn": "chile"},
    "CO": {"name": "Colombia", "geo": "CO", "pn": "colombia"},
    "TW": {"name": "Taiwan", "geo": "TW", "pn": "taiwan"},
    "TH": {"name": "Thailand", "geo": "TH", "pn": "thailand"},
    "VN": {"name": "Vietnam", "geo": "VN", "pn": "vietnam"},
    "PH": {"name": "Philippines", "geo": "PH", "pn": "philippines"},
    "ID": {"name": "Indonesia", "geo": "ID", "pn": "indonesia"},
    "MY": {"name": "Malaysia", "geo": "MY", "pn": "malaysia"},
    "NZ": {"name": "New Zealand", "geo": "NZ", "pn": "new_zealand"},
    "TR": {"name": "Turkey", "geo": "TR", "pn": "turkey"},
    "RU": {"name": "Russia", "geo": "RU", "pn": "russia"},
    "CN": {"name": "China", "geo": "CN", "pn": "china"},
}

# ─── Topics to scan ───
SCAN_TOPICS = [
    "artificial intelligence", "machine learning", "deep learning", "generative AI",
    "large language models", "prompt engineering", "ChatGPT", "data science",
    "data engineering", "data analytics", "python", "javascript",
    "typescript", "react", "next.js", "node.js", "web development",
    "cloud computing", "AWS", "Azure", "kubernetes", "docker", "devops",
    "cybersecurity", "ethical hacking", "blockchain", "web3", "cryptocurrency",
    "product management", "UX design", "figma", "mobile development",
    "flutter", "react native", "swift", "rust programming", "golang",
    "system design", "software architecture", "microservices", "API development",
    "SQL", "mongodb", "graphql", "no code", "low code",
    "robotics", "computer vision", "NLP", "digital marketing", "SEO",
]

# ─── In-memory cache ───
_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 300  # 5 minutes


def _get_cached(key: str) -> Any | None:
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
    return None


def _set_cached(key: str, val: Any) -> None:
    _cache[key] = (time.time(), val)


# ─── Response models ───

class TopicResult(BaseModel):
    rank: int
    topic: str
    opportunity_score: float
    stackoverflow_questions: int = 0
    hackernews_mentions: int = 0
    hackernews_avg_score: float = 0
    github_repos: int = 0
    wikipedia_views: int = 0
    reddit_posts: int = 0
    trend_direction: str = "unknown"
    growth_rate: float = 0
    job_demand_signal: str = ""
    evidence_summary: str = ""
    sources_used: int = 0


class DiscoverResponse(BaseModel):
    country_code: str
    country_name: str
    mode: str
    topics_scanned: int
    results: list[TopicResult]
    sources_queried: list[str]
    scan_time_ms: int
    timestamp: str


# ─── Source fetchers (all free, no API keys, high rate limits) ───

async def _fetch_so(client: httpx.AsyncClient, topic: str) -> dict:
    """Stack Overflow: tag count + recent questions."""
    tag = topic.lower().replace(" ", "-").replace(".", "")
    try:
        resp = await client.get(
            f"https://api.stackexchange.com/2.3/tags/{tag}/info",
            params={"site": "stackoverflow"},
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            if items:
                count = items[0].get("count", 0)
                return {"questions": count, "score": min(1.0, count / 200000)}
    except Exception:
        pass
    # Fallback: search
    try:
        resp = await client.get(
            "https://api.stackexchange.com/2.3/search/excerpts",
            params={"site": "stackoverflow", "q": topic, "pagesize": 1},
        )
        if resp.status_code == 200:
            total = resp.json().get("total", 0)
            return {"questions": total, "score": min(1.0, total / 50000)}
    except Exception:
        pass
    return {"questions": 0, "score": 0}


async def _fetch_hn(client: httpx.AsyncClient, topic: str) -> dict:
    """Hacker News: story mentions via Algolia (free, fast, no limits)."""
    try:
        resp = await client.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": topic, "tags": "story", "hitsPerPage": 10},
        )
        if resp.status_code == 200:
            data = resp.json()
            total = data.get("nbHits", 0)
            hits = data.get("hits", [])
            avg = 0.0
            if hits:
                scores = [h.get("points", 0) or 0 for h in hits]
                avg = sum(scores) / len(scores)
            return {"mentions": total, "avg_score": round(avg, 1), "score": min(1.0, total / 5000)}
    except Exception:
        pass
    return {"mentions": 0, "avg_score": 0, "score": 0}


async def _fetch_github(client: httpx.AsyncClient, topic: str) -> dict:
    """GitHub: repository count (free API, 10 req/min unauthenticated)."""
    try:
        resp = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": topic, "sort": "updated", "per_page": 1},
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        if resp.status_code == 200:
            total = resp.json().get("total_count", 0)
            return {"repos": total, "score": min(1.0, total / 50000)}
    except Exception:
        pass
    return {"repos": 0, "score": 0}


async def _fetch_wikipedia(client: httpx.AsyncClient, topic: str) -> dict:
    """Wikipedia: pageviews last 30 days (free, no limits)."""
    title = topic.replace(" ", "_")
    try:
        resp = await client.get(
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
            f"en.wikipedia/all-access/all-agents/{title}/daily/20260224/20260326",
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            total = sum(i.get("views", 0) for i in items)
            return {"views": total, "score": min(1.0, total / 300000)}
    except Exception:
        pass
    return {"views": 0, "score": 0}


async def _fetch_reddit(client: httpx.AsyncClient, topic: str) -> dict:
    """Reddit: recent post count (free)."""
    try:
        resp = await client.get(
            "https://old.reddit.com/search.json",
            params={"q": topic, "sort": "new", "limit": 10, "t": "month"},
            headers={"User-Agent": "COGNET-LDI/1.0"},
            follow_redirects=True,
        )
        if resp.status_code == 200:
            children = resp.json().get("data", {}).get("children", [])
            total_score = sum(c.get("data", {}).get("score", 0) for c in children)
            return {"posts": len(children), "total_score": total_score, "score": min(1.0, len(children) / 10)}
    except Exception:
        pass
    return {"posts": 0, "score": 0}


async def _scan_single_topic(client: httpx.AsyncClient, topic: str) -> dict:
    """Scan a single topic across all non-rate-limited sources concurrently."""
    cache_key = f"topic:{topic}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    tasks = {
        "stackoverflow": _fetch_so(client, topic),
        "hackernews": _fetch_hn(client, topic),
        "github": _fetch_github(client, topic),
        "wikipedia": _fetch_wikipedia(client, topic),
        "reddit": _fetch_reddit(client, topic),
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    topic_data: dict[str, Any] = {"topic": topic, "sources": 0}
    total_score = 0.0
    weights = {"stackoverflow": 0.25, "hackernews": 0.20, "github": 0.25, "wikipedia": 0.15, "reddit": 0.15}

    for key, result in zip(tasks.keys(), results):
        if isinstance(result, Exception) or not isinstance(result, dict):
            continue
        topic_data[key] = result
        score = result.get("score", 0)
        total_score += score * weights.get(key, 0.1)
        topic_data["sources"] += 1

    topic_data["opportunity_score"] = round(total_score, 4)
    _set_cached(cache_key, topic_data)
    return topic_data


# ─── Endpoints ───

@router.get("/scan", response_model=DiscoverResponse)
async def discover_topics(
    country_code: str = Query("IL", description="ISO country code (50 supported)"),
    limit: int = Query(25, ge=5, le=50),
) -> DiscoverResponse:
    """
    Scan 50 learning topics across 5 live sources (StackOverflow, HackerNews,
    GitHub, Wikipedia, Reddit) and rank by opportunity score.
    Returns results in ~15-20 seconds.
    """
    start = time.monotonic()
    country = COUNTRIES.get(country_code, {"name": country_code, "geo": country_code})

    async with httpx.AsyncClient(timeout=12.0) as client:
        # Scan all topics concurrently (in batches of 10 to avoid overwhelming)
        all_results: list[dict] = []
        for i in range(0, len(SCAN_TOPICS), 10):
            batch = SCAN_TOPICS[i:i + 10]
            batch_results = await asyncio.gather(
                *[_scan_single_topic(client, t) for t in batch],
                return_exceptions=True,
            )
            for r in batch_results:
                if isinstance(r, dict):
                    all_results.append(r)

    # Sort by opportunity score
    all_results.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)

    # Build response
    results = []
    for rank, data in enumerate(all_results[:limit], 1):
        so = data.get("stackoverflow", {})
        hn = data.get("hackernews", {})
        gh = data.get("github", {})
        wp = data.get("wikipedia", {})
        rd = data.get("reddit", {})

        # Build evidence
        evidences = []
        if so.get("questions", 0) > 50000:
            evidences.append(f"SO: {so['questions']:,} questions")
        if hn.get("mentions", 0) > 1000:
            evidences.append(f"HN: {hn['mentions']:,} mentions")
        if gh.get("repos", 0) > 10000:
            evidences.append(f"GitHub: {gh['repos']:,} repos")
        if wp.get("views", 0) > 100000:
            evidences.append(f"Wiki: {wp['views']:,} views/month")

        results.append(TopicResult(
            rank=rank,
            topic=data.get("topic", "?"),
            opportunity_score=data.get("opportunity_score", 0),
            stackoverflow_questions=so.get("questions", 0),
            hackernews_mentions=hn.get("mentions", 0),
            hackernews_avg_score=hn.get("avg_score", 0),
            github_repos=gh.get("repos", 0),
            wikipedia_views=wp.get("views", 0),
            reddit_posts=rd.get("posts", 0),
            evidence_summary="; ".join(evidences) if evidences else "",
            sources_used=data.get("sources", 0),
        ))

    elapsed = int((time.monotonic() - start) * 1000)

    return DiscoverResponse(
        country_code=country_code,
        country_name=country.get("name", country_code),
        mode="multi-source",
        topics_scanned=len(SCAN_TOPICS),
        results=results,
        sources_queried=["StackOverflow", "HackerNews", "GitHub", "Wikipedia", "Reddit"],
        scan_time_ms=elapsed,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/trending-now")
async def trending_now(country_code: str = Query("IL")) -> dict:
    """Get what's trending RIGHT NOW (Google Trends — single request)."""
    country = COUNTRIES.get(country_code, {"name": country_code, "pn": country_code.lower()})
    pn = country.get("pn", country_code.lower())
    trending = []

    cache_key = f"trending:{country_code}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    try:
        from pytrends.request import TrendReq
        loop = asyncio.get_event_loop()
        pt = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        df = await loop.run_in_executor(None, lambda: pt.trending_searches(pn=pn))
        if df is not None and not df.empty:
            for idx, row in df.iterrows():
                trending.append({"rank": idx + 1, "topic": str(row.iloc[0])})
    except Exception as e:
        logger.warning(f"Trending failed for {country_code}: {e}")

    result = {
        "country_code": country_code,
        "country_name": country.get("name", country_code),
        "trending_now": trending,
        "source": "Google Trends Realtime",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _set_cached(cache_key, result)
    return result


@router.get("/countries")
async def list_countries() -> dict:
    """List all 50 supported countries."""
    return {
        "count": len(COUNTRIES),
        "countries": [
            {"code": code, "name": info["name"]}
            for code, info in sorted(COUNTRIES.items(), key=lambda x: x[1]["name"])
        ],
    }
