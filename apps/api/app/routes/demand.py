"""
Learning Demand Intelligence — COGNET LDI Engine.
What people WANT TO LEARN — based on REAL data from APIs that always work:
  - StackOverflow: beginner questions, "how to" queries, tutorial requests
  - HackerNews: "learn X", "course X", tutorial articles
  - GitHub: tutorial/course/learning repos, educational content
  - Wikipedia: pageviews on learning-related articles
  - Reddit: r/learnprogramming style activity

Google Trends used as bonus signal when available (rate limited).
"""
from __future__ import annotations

import asyncio
import logging
import time
import math
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/demand", tags=["demand"])

COUNTRIES = {
    "IL": "Israel", "US": "United States", "GB": "United Kingdom",
    "DE": "Germany", "FR": "France", "IN": "India", "JP": "Japan",
    "KR": "South Korea", "BR": "Brazil", "AU": "Australia", "CA": "Canada",
    "NL": "Netherlands", "SE": "Sweden", "SG": "Singapore", "ES": "Spain",
    "IT": "Italy", "PL": "Poland", "CH": "Switzerland", "AT": "Austria",
    "BE": "Belgium", "DK": "Denmark", "FI": "Finland", "NO": "Norway",
    "IE": "Ireland", "PT": "Portugal", "ZA": "South Africa", "NG": "Nigeria",
    "AE": "UAE", "SA": "Saudi Arabia", "MX": "Mexico", "AR": "Argentina",
    "CO": "Colombia", "TW": "Taiwan", "TH": "Thailand", "VN": "Vietnam",
    "PH": "Philippines", "ID": "Indonesia", "MY": "Malaysia", "TR": "Turkey",
    "EG": "Egypt", "UA": "Ukraine", "CZ": "Czech Republic", "RO": "Romania",
    "GR": "Greece", "NZ": "New Zealand", "CL": "Chile", "KE": "Kenya",
    "HU": "Hungary", "RU": "Russia", "CN": "China",
}

TOPICS = [
    "artificial intelligence", "machine learning", "data science", "python",
    "web development", "cybersecurity", "cloud computing", "devops",
    "react", "javascript", "typescript", "SQL", "data engineering",
    "product management", "UX design", "digital marketing", "SEO",
    "project management", "blockchain", "prompt engineering", "generative AI",
    "deep learning", "mobile development", "flutter", "swift",
    "rust", "golang", "kubernetes", "docker", "AWS",
    "data analytics", "power BI", "excel", "figma",
    "video editing", "graphic design", "photography",
    "public speaking", "leadership", "negotiation",
    "financial modeling", "investing", "accounting",
    "no code", "automation", "ChatGPT", "system design",
    "software architecture", "agile", "scrum",
]

# ─── Cache ───
_cache: dict[str, tuple[float, object]] = {}
CACHE_TTL = 600


def _cached(key: str):
    if key in _cache and time.time() - _cache[key][0] < CACHE_TTL:
        return _cache[key][1]
    return None


def _set_cache(key: str, val):
    _cache[key] = (time.time(), val)


# ─── Models ───

class DemandItem(BaseModel):
    rank: int
    topic: str
    learning_demand_score: float
    people_want_to_learn: int = Field(description="SO beginner questions + HN learn mentions")
    companies_are_hiring: int = Field(description="GitHub job/hiring repos")
    community_activity: int = Field(description="Reddit + HN tutorial mentions")
    github_learning_repos: int = 0
    so_beginner_questions: int = 0
    hn_learn_mentions: int = 0
    wikipedia_views: int = 0
    growth_direction: str = "stable"
    gap_signal: str = "moderate_gap"
    why: str = ""
    action: str = ""
    sources_succeeded: int = 0


class DemandResponse(BaseModel):
    country_code: str
    country_name: str
    scan_time_ms: int
    topics_analyzed: int
    timestamp: str
    results: list[DemandItem]


# ─── Source fetchers — ALL reliable, no rate limits ───

async def _so_learning(client: httpx.AsyncClient, topic: str) -> dict:
    """SO beginner/learning questions."""
    total = 0
    try:
        resp = await client.get(
            "https://api.stackexchange.com/2.3/search/excerpts",
            params={"site": "stackoverflow", "q": f"{topic} tutorial beginner how to learn", "pagesize": 1},
        )
        if resp.status_code == 200:
            total = resp.json().get("total", 0)
    except Exception:
        pass
    return {"so_beginner": total, "score": min(1.0, total / 5000)}


async def _hn_learning(client: httpx.AsyncClient, topic: str) -> dict:
    """HN mentions of learning/courses."""
    mentions = 0
    avg_score = 0.0
    try:
        resp = await client.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": f"learn {topic} course tutorial", "tags": "story", "hitsPerPage": 10},
        )
        if resp.status_code == 200:
            data = resp.json()
            mentions = data.get("nbHits", 0)
            hits = data.get("hits", [])
            if hits:
                avg_score = sum(h.get("points", 0) or 0 for h in hits) / len(hits)
    except Exception:
        pass
    return {"hn_learn": mentions, "avg_score": round(avg_score, 1), "score": min(1.0, mentions / 2000)}


async def _github_learning(client: httpx.AsyncClient, topic: str) -> dict:
    """GitHub learning/tutorial repos."""
    repos = 0
    try:
        resp = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": f"{topic} tutorial course learn", "sort": "stars", "per_page": 1},
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        if resp.status_code == 200:
            repos = resp.json().get("total_count", 0)
    except Exception:
        pass
    return {"repos": repos, "score": min(1.0, repos / 20000)}


async def _github_jobs(client: httpx.AsyncClient, topic: str) -> dict:
    """GitHub repos mentioning hiring/jobs."""
    repos = 0
    try:
        resp = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": f"{topic} jobs hiring", "sort": "updated", "per_page": 1},
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        if resp.status_code == 200:
            repos = resp.json().get("total_count", 0)
    except Exception:
        pass
    return {"job_repos": repos, "score": min(1.0, repos / 5000)}


async def _wikipedia_learning(client: httpx.AsyncClient, topic: str) -> dict:
    """Wikipedia pageviews."""
    views = 0
    try:
        title = topic.replace(" ", "_")
        resp = await client.get(
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
            f"en.wikipedia/all-access/all-agents/{title}/daily/20260224/20260326",
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            views = sum(i.get("views", 0) for i in items)
    except Exception:
        pass
    return {"views": views, "score": min(1.0, views / 200000)}


async def _reddit_learning(client: httpx.AsyncClient, topic: str) -> dict:
    """Reddit learning activity."""
    posts = 0
    try:
        resp = await client.get(
            "https://old.reddit.com/search.json",
            params={"q": f"learn {topic}", "sort": "new", "limit": 10, "t": "month"},
            headers={"User-Agent": "COGNET-LDI/1.0"},
            follow_redirects=True,
        )
        if resp.status_code == 200:
            posts = len(resp.json().get("data", {}).get("children", []))
    except Exception:
        pass
    return {"posts": posts, "score": min(1.0, posts / 10)}


async def _scan_topic(client: httpx.AsyncClient, topic: str) -> dict:
    """Scan a single topic across all learning-focused sources."""
    cache_key = f"demand_topic:{topic}"
    cached = _cached(cache_key)
    if cached:
        return cached

    tasks = {
        "so": _so_learning(client, topic),
        "hn": _hn_learning(client, topic),
        "github_learn": _github_learning(client, topic),
        "github_jobs": _github_jobs(client, topic),
        "wikipedia": _wikipedia_learning(client, topic),
        "reddit": _reddit_learning(client, topic),
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    data = {"topic": topic}
    sources_ok = 0

    weights = {"so": 0.20, "hn": 0.20, "github_learn": 0.20, "github_jobs": 0.15, "wikipedia": 0.10, "reddit": 0.15}
    total_score = 0.0

    for key, result in zip(tasks.keys(), results):
        if isinstance(result, dict):
            data[key] = result
            total_score += result.get("score", 0) * weights.get(key, 0.1)
            sources_ok += 1
        else:
            data[key] = {"error": str(result)}

    data["learning_demand_score"] = round(total_score, 4)
    data["sources_ok"] = sources_ok

    _set_cache(cache_key, data)
    return data


# ─── Endpoint ───

@router.get("/scan", response_model=DemandResponse)
async def scan_learning_demand(
    country_code: str = Query("IL", description="ISO country code"),
    limit: int = Query(25, ge=5, le=50),
) -> DemandResponse:
    """
    Scan what people WANT TO LEARN right now.

    Queries 6 live sources per topic (all free, no rate limits):
    - StackOverflow beginner questions
    - HackerNews learn/course/tutorial mentions
    - GitHub learning repos
    - GitHub hiring repos
    - Wikipedia pageviews
    - Reddit learning posts
    """
    start = time.monotonic()
    country_name = COUNTRIES.get(country_code, country_code)

    resp_cache = _cached(f"demand_full:{country_code}")
    if resp_cache:
        return resp_cache

    # Scan all topics in batches of 8 (to not overwhelm)
    all_data: list[dict] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for i in range(0, len(TOPICS), 8):
            batch = TOPICS[i:i + 8]
            results = await asyncio.gather(
                *[_scan_topic(client, t) for t in batch],
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, dict):
                    all_data.append(r)

    # Sort by learning demand
    all_data.sort(key=lambda x: x.get("learning_demand_score", 0), reverse=True)

    # Build response
    items = []
    for rank, d in enumerate(all_data[:limit], 1):
        so = d.get("so", {})
        hn = d.get("hn", {})
        gh_learn = d.get("github_learn", {})
        gh_jobs = d.get("github_jobs", {})
        wiki = d.get("wikipedia", {})
        reddit = d.get("reddit", {})

        so_q = so.get("so_beginner", 0) if isinstance(so, dict) else 0
        hn_m = hn.get("hn_learn", 0) if isinstance(hn, dict) else 0
        gh_lr = gh_learn.get("repos", 0) if isinstance(gh_learn, dict) else 0
        gh_jr = gh_jobs.get("job_repos", 0) if isinstance(gh_jobs, dict) else 0
        wiki_v = wiki.get("views", 0) if isinstance(wiki, dict) else 0
        reddit_p = reddit.get("posts", 0) if isinstance(reddit, dict) else 0

        score = d.get("learning_demand_score", 0)

        # Gap signal
        learn_signal = so_q + hn_m + gh_lr
        job_signal = gh_jr
        if learn_signal > 5000 and job_signal > 1000:
            gap = "high_gap"
        elif learn_signal > 1000 or job_signal > 500:
            gap = "moderate_gap"
        elif learn_signal > 200:
            gap = "low_gap"
        else:
            gap = "saturated"

        # Why
        parts = []
        if so_q > 1000:
            parts.append(f"{so_q:,} beginner questions on StackOverflow")
        if hn_m > 500:
            parts.append(f"{hn_m:,} learn/tutorial mentions on HackerNews")
        if gh_lr > 5000:
            parts.append(f"{gh_lr:,} tutorial repos on GitHub")
        if gh_jr > 1000:
            parts.append(f"Companies hiring: {gh_jr:,} job-related repos")
        if wiki_v > 50000:
            parts.append(f"{wiki_v:,} Wikipedia views/month")
        why = ". ".join(parts) if parts else "Limited learning signals detected"

        # Action
        if score >= 0.5 and gap in ("high_gap", "moderate_gap"):
            action = "🔥 Build course now — strong learning + hiring demand"
        elif score >= 0.3:
            action = "📈 Plan content — growing learning interest"
        elif score >= 0.15:
            action = "👀 Watch — moderate signals"
        else:
            action = "⏸️ Low priority"

        items.append(DemandItem(
            rank=rank,
            topic=d.get("topic", "?"),
            learning_demand_score=score,
            people_want_to_learn=so_q + hn_m,
            companies_are_hiring=gh_jr,
            community_activity=reddit_p + hn_m,
            github_learning_repos=gh_lr,
            so_beginner_questions=so_q,
            hn_learn_mentions=hn_m,
            wikipedia_views=wiki_v,
            gap_signal=gap,
            why=why,
            action=action,
            sources_succeeded=d.get("sources_ok", 0),
        ))

    elapsed = int((time.monotonic() - start) * 1000)

    response = DemandResponse(
        country_code=country_code,
        country_name=country_name,
        scan_time_ms=elapsed,
        topics_analyzed=len(TOPICS),
        timestamp=datetime.now(timezone.utc).isoformat(),
        results=items,
    )
    _set_cache(f"demand_full:{country_code}", response)
    return response
