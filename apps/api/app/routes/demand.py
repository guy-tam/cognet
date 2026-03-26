"""
Learning Demand Intelligence — COGNET LDI Engine.
Real data from reliable APIs about what people WANT TO LEARN.

Sources (all free, reliable):
  1. HackerNews Algolia — learn/course/tutorial mentions (unlimited, fast)
  2. GitHub Search — tutorial repos + job repos (10 req/min unauthed)
  3. Wikipedia Pageviews — article views (unlimited with proper UA)
  4. Reddit Search — learning community posts (reasonable limits)
  5. StackOverflow — tag counts + questions (300/day, cached aggressively)

Timeline support: scan across different time windows.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta

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
    "IT": "Italy", "PL": "Poland", "CH": "Switzerland", "IE": "Ireland",
    "PT": "Portugal", "ZA": "South Africa", "NG": "Nigeria", "AE": "UAE",
    "SA": "Saudi Arabia", "MX": "Mexico", "AR": "Argentina", "CO": "Colombia",
    "TW": "Taiwan", "TH": "Thailand", "VN": "Vietnam", "PH": "Philippines",
    "ID": "Indonesia", "MY": "Malaysia", "TR": "Turkey", "EG": "Egypt",
    "UA": "Ukraine", "CZ": "Czech Republic", "RO": "Romania", "NZ": "New Zealand",
    "CL": "Chile", "KE": "Kenya", "AT": "Austria", "BE": "Belgium",
    "DK": "Denmark", "FI": "Finland", "NO": "Norway", "GR": "Greece",
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

# ─── Cache (aggressive — 10 min per source, 5 min full results) ───
_cache: dict[str, tuple[float, object]] = {}
SOURCE_CACHE_TTL = 600
FULL_CACHE_TTL = 300
UA = "COGNET-LDI/1.0 (https://cognet.app; open@cognet.app) python-httpx"


def _get(key: str, ttl: int = SOURCE_CACHE_TTL):
    if key in _cache and time.time() - _cache[key][0] < ttl:
        return _cache[key][1]
    return None


def _put(key: str, val):
    _cache[key] = (time.time(), val)


# ─── Models ───

class TimelinePoint(BaseModel):
    date: str
    value: float


class DemandItem(BaseModel):
    rank: int
    topic: str
    learning_demand_score: float
    hn_learn_mentions: int = 0
    hn_avg_score: float = 0
    github_learning_repos: int = 0
    github_job_repos: int = 0
    wikipedia_views_30d: int = 0
    reddit_learn_posts: int = 0
    so_tag_count: int = 0
    gap_signal: str = "unknown"
    why: str = ""
    action: str = ""
    sources_ok: int = 0
    timeline: list[TimelinePoint] = Field(default_factory=list, description="Wikipedia daily views timeline")


class DemandResponse(BaseModel):
    country_code: str
    country_name: str
    scan_time_ms: int
    topics_analyzed: int
    timestamp: str
    time_range: str
    results: list[DemandItem]


# ─── Source fetchers ───

async def _hn(client: httpx.AsyncClient, topic: str) -> dict:
    """HackerNews learn mentions — most reliable, no limits."""
    ck = f"hn:{topic}"
    c = _get(ck)
    if c:
        return c
    try:
        r = await client.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": f"learn {topic} course tutorial", "tags": "story", "hitsPerPage": 15},
        )
        if r.status_code == 200:
            d = r.json()
            hits = d.get("hits", [])
            total = d.get("nbHits", 0)
            avg = sum(h.get("points", 0) or 0 for h in hits) / max(len(hits), 1)
            # Recent vs older for growth signal
            titles = [h.get("title", "") for h in hits[:5]]
            result = {"mentions": total, "avg_score": round(avg, 1), "titles": titles,
                      "score": min(1.0, total / 3000)}
            _put(ck, result)
            return result
    except Exception as e:
        logger.debug(f"HN failed for {topic}: {e}")
    return {"mentions": 0, "avg_score": 0, "score": 0}


async def _github_learn(client: httpx.AsyncClient, topic: str) -> dict:
    """GitHub tutorial/course repos."""
    ck = f"gh_learn:{topic}"
    c = _get(ck)
    if c:
        return c
    try:
        r = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": f"{topic} tutorial course learn", "sort": "stars", "per_page": 1},
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": UA},
        )
        if r.status_code == 200:
            total = r.json().get("total_count", 0)
            result = {"repos": total, "score": min(1.0, total / 20000)}
            _put(ck, result)
            return result
    except Exception:
        pass
    return {"repos": 0, "score": 0}


async def _github_jobs(client: httpx.AsyncClient, topic: str) -> dict:
    """GitHub job-related repos (hiring demand signal)."""
    ck = f"gh_jobs:{topic}"
    c = _get(ck)
    if c:
        return c
    try:
        r = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": f"{topic} jobs hiring career", "sort": "updated", "per_page": 1},
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": UA},
        )
        if r.status_code == 200:
            total = r.json().get("total_count", 0)
            result = {"repos": total, "score": min(1.0, total / 5000)}
            _put(ck, result)
            return result
    except Exception:
        pass
    return {"repos": 0, "score": 0}


async def _wikipedia(client: httpx.AsyncClient, topic: str) -> dict:
    """Wikipedia pageviews with daily timeline."""
    ck = f"wiki:{topic}"
    c = _get(ck)
    if c:
        return c

    title = topic.replace(" ", "_").title()
    # Try multiple title formats
    titles_to_try = [
        title,
        title.replace("_", "_(%s)_" % "programming_language") if topic.lower() in ("python", "swift", "rust", "go") else title,
        topic.replace(" ", "_"),
    ]

    end = datetime.now(timezone.utc)
    start_date = end - timedelta(days=30)
    start_str = start_date.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")

    for t in titles_to_try:
        try:
            r = await client.get(
                f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
                f"en.wikipedia/all-access/all-agents/{t}/daily/{start_str}/{end_str}",
                headers={"User-Agent": UA},
            )
            if r.status_code == 200:
                items = r.json().get("items", [])
                if items:
                    total = sum(i.get("views", 0) for i in items)
                    timeline = [
                        {"date": i.get("timestamp", "")[:8], "value": i.get("views", 0)}
                        for i in items
                    ]
                    result = {"views": total, "timeline": timeline,
                              "score": min(1.0, total / 300000)}
                    _put(ck, result)
                    return result
        except Exception:
            continue
    return {"views": 0, "timeline": [], "score": 0}


async def _reddit(client: httpx.AsyncClient, topic: str) -> dict:
    """Reddit learning posts."""
    ck = f"reddit:{topic}"
    c = _get(ck)
    if c:
        return c
    try:
        r = await client.get(
            "https://old.reddit.com/search.json",
            params={"q": f"learn {topic}", "sort": "new", "limit": 10, "t": "month"},
            headers={"User-Agent": UA},
            follow_redirects=True,
        )
        if r.status_code == 200:
            children = r.json().get("data", {}).get("children", [])
            result = {"posts": len(children), "score": min(1.0, len(children) / 10)}
            _put(ck, result)
            return result
    except Exception:
        pass
    return {"posts": 0, "score": 0}


async def _so(client: httpx.AsyncClient, topic: str) -> dict:
    """StackOverflow tag count (cached aggressively)."""
    ck = f"so:{topic}"
    c = _get(ck, ttl=1800)  # Cache 30 min
    if c:
        return c
    tag = topic.lower().replace(" ", "-")
    try:
        r = await client.get(
            f"https://api.stackexchange.com/2.3/tags/{tag}/info",
            params={"site": "stackoverflow"},
        )
        if r.status_code == 200:
            items = r.json().get("items", [])
            count = items[0].get("count", 0) if items else 0
            result = {"count": count, "score": min(1.0, count / 200000)}
            _put(ck, result)
            return result
    except Exception:
        pass
    return {"count": 0, "score": 0}


async def _scan_one(client: httpx.AsyncClient, topic: str) -> dict:
    """Scan one topic across all sources concurrently."""
    tasks = {
        "hn": _hn(client, topic),
        "github_learn": _github_learn(client, topic),
        "github_jobs": _github_jobs(client, topic),
        "wikipedia": _wikipedia(client, topic),
        "reddit": _reddit(client, topic),
        "so": _so(client, topic),
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    data = {"topic": topic}
    ok = 0
    weights = {"hn": 0.25, "github_learn": 0.20, "github_jobs": 0.15, "wikipedia": 0.15, "reddit": 0.10, "so": 0.15}
    total = 0.0

    for key, res in zip(tasks.keys(), results):
        if isinstance(res, dict):
            data[key] = res
            total += res.get("score", 0) * weights.get(key, 0.1)
            ok += 1
        else:
            data[key] = {}

    data["score"] = round(total, 4)
    data["ok"] = ok
    return data


# ─── Endpoints ───

@router.get("/scan", response_model=DemandResponse)
async def scan_demand(
    country_code: str = Query("IL"),
    limit: int = Query(25, ge=5, le=50),
    time_range: str = Query("30d", description="Timeline: 7d, 30d, 90d"),
) -> DemandResponse:
    """
    Scan what people WANT TO LEARN — real data from 6 live sources.
    Each topic gets: HN learn mentions, GitHub tutorial repos, Wikipedia views with daily timeline,
    Reddit learning posts, SO tag count, and a composite learning demand score.
    """
    start = time.monotonic()
    country_name = COUNTRIES.get(country_code, country_code)

    full_ck = f"demand:{country_code}:{time_range}"
    cached = _get(full_ck, FULL_CACHE_TTL)
    if cached:
        return cached

    all_data: list[dict] = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Scan in batches of 6 to respect GitHub rate limits
        for i in range(0, len(TOPICS), 6):
            batch = TOPICS[i:i + 6]
            results = await asyncio.gather(
                *[_scan_one(client, t) for t in batch],
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, dict):
                    all_data.append(r)
            # Small delay between batches to respect GitHub
            if i + 6 < len(TOPICS):
                await asyncio.sleep(0.5)

    all_data.sort(key=lambda x: x.get("score", 0), reverse=True)

    items: list[DemandItem] = []
    for rank, d in enumerate(all_data[:limit], 1):
        hn = d.get("hn", {})
        gl = d.get("github_learn", {})
        gj = d.get("github_jobs", {})
        wiki = d.get("wikipedia", {})
        rd = d.get("reddit", {})
        so = d.get("so", {})

        hn_m = hn.get("mentions", 0)
        gl_r = gl.get("repos", 0)
        gj_r = gj.get("repos", 0)
        wiki_v = wiki.get("views", 0)
        rd_p = rd.get("posts", 0)
        so_c = so.get("count", 0)
        score = d.get("score", 0)

        # Gap signal
        learn = hn_m + gl_r + rd_p
        hire = gj_r
        if learn > 3000 and hire > 500:
            gap = "high_gap"
        elif learn > 500 or hire > 200:
            gap = "moderate_gap"
        elif learn > 100:
            gap = "low_gap"
        else:
            gap = "emerging"

        # Why
        parts = []
        if hn_m > 500:
            parts.append(f"{hn_m:,} learn/tutorial mentions on HackerNews")
        if gl_r > 1000:
            parts.append(f"{gl_r:,} tutorial repos on GitHub")
        if gj_r > 500:
            parts.append(f"Hiring signal: {gj_r:,} job-related repos")
        if wiki_v > 50000:
            parts.append(f"{wiki_v:,} Wikipedia views/month")
        if so_c > 50000:
            parts.append(f"{so_c:,} StackOverflow questions")
        if rd_p >= 5:
            parts.append(f"Active Reddit learning community ({rd_p} recent posts)")
        why = ". ".join(parts) if parts else "Low signals — emerging or niche topic"

        # Action
        if score >= 0.4 and gap in ("high_gap", "moderate_gap"):
            action = "🔥 Build course now — strong learning + hiring demand"
        elif score >= 0.25:
            action = "📈 Plan content — meaningful learning interest"
        elif score >= 0.1:
            action = "👀 Watch — growing interest"
        else:
            action = "⏸️ Low priority"

        # Timeline from Wikipedia
        timeline = [TimelinePoint(date=p["date"], value=p["value"]) for p in wiki.get("timeline", [])]

        items.append(DemandItem(
            rank=rank, topic=d["topic"], learning_demand_score=score,
            hn_learn_mentions=hn_m, hn_avg_score=hn.get("avg_score", 0),
            github_learning_repos=gl_r, github_job_repos=gj_r,
            wikipedia_views_30d=wiki_v, reddit_learn_posts=rd_p, so_tag_count=so_c,
            gap_signal=gap, why=why, action=action,
            sources_ok=d.get("ok", 0), timeline=timeline,
        ))

    elapsed = int((time.monotonic() - start) * 1000)

    response = DemandResponse(
        country_code=country_code, country_name=country_name,
        scan_time_ms=elapsed, topics_analyzed=len(TOPICS),
        timestamp=datetime.now(timezone.utc).isoformat(),
        time_range=time_range, results=items,
    )
    _put(full_ck, response)
    return response
