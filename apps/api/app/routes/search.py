"""
מנוע נתונים חיים — COGNET LDI Engine.
שואב נתונים מ-10+ מקורות חינמיים, תומך ב-50+ מדינות, ומנתח כל נושא בזמן אמת.
"""
from __future__ import annotations

import asyncio
import logging
import math
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/search", tags=["search"])

# ---------------------------------------------------------------------------
# מדינות נתמכות — 50+ מדינות עם קודי גיאו ושפות
# ---------------------------------------------------------------------------
COUNTRIES: dict[str, dict[str, Any]] = {
    # מזרח תיכון
    "IL": {"name": "Israel", "google_geo": "IL", "google_trends_pn": "israel", "languages": ["he", "en"]},
    "AE": {"name": "UAE", "google_geo": "AE", "google_trends_pn": "united_arab_emirates", "languages": ["ar", "en"]},
    "SA": {"name": "Saudi Arabia", "google_geo": "SA", "google_trends_pn": "saudi_arabia", "languages": ["ar"]},
    "EG": {"name": "Egypt", "google_geo": "EG", "google_trends_pn": "egypt", "languages": ["ar"]},
    # צפון אמריקה
    "US": {"name": "United States", "google_geo": "US", "google_trends_pn": "united_states", "languages": ["en"]},
    "CA": {"name": "Canada", "google_geo": "CA", "google_trends_pn": "canada", "languages": ["en", "fr"]},
    "MX": {"name": "Mexico", "google_geo": "MX", "google_trends_pn": "mexico", "languages": ["es"]},
    # אירופה
    "GB": {"name": "United Kingdom", "google_geo": "GB", "google_trends_pn": "united_kingdom", "languages": ["en"]},
    "DE": {"name": "Germany", "google_geo": "DE", "google_trends_pn": "germany", "languages": ["de"]},
    "FR": {"name": "France", "google_geo": "FR", "google_trends_pn": "france", "languages": ["fr"]},
    "NL": {"name": "Netherlands", "google_geo": "NL", "google_trends_pn": "netherlands", "languages": ["nl", "en"]},
    "ES": {"name": "Spain", "google_geo": "ES", "google_trends_pn": "spain", "languages": ["es"]},
    "IT": {"name": "Italy", "google_geo": "IT", "google_trends_pn": "italy", "languages": ["it"]},
    "SE": {"name": "Sweden", "google_geo": "SE", "google_trends_pn": "sweden", "languages": ["sv", "en"]},
    "NO": {"name": "Norway", "google_geo": "NO", "google_trends_pn": "norway", "languages": ["no", "en"]},
    "DK": {"name": "Denmark", "google_geo": "DK", "google_trends_pn": "denmark", "languages": ["da", "en"]},
    "FI": {"name": "Finland", "google_geo": "FI", "google_trends_pn": "finland", "languages": ["fi", "en"]},
    "PL": {"name": "Poland", "google_geo": "PL", "google_trends_pn": "poland", "languages": ["pl"]},
    "CH": {"name": "Switzerland", "google_geo": "CH", "google_trends_pn": "switzerland", "languages": ["de", "fr", "en"]},
    "AT": {"name": "Austria", "google_geo": "AT", "google_trends_pn": "austria", "languages": ["de"]},
    "BE": {"name": "Belgium", "google_geo": "BE", "google_trends_pn": "belgium", "languages": ["nl", "fr", "en"]},
    "PT": {"name": "Portugal", "google_geo": "PT", "google_trends_pn": "portugal", "languages": ["pt"]},
    "IE": {"name": "Ireland", "google_geo": "IE", "google_trends_pn": "ireland", "languages": ["en"]},
    "CZ": {"name": "Czech Republic", "google_geo": "CZ", "google_trends_pn": "czech_republic", "languages": ["cs"]},
    "RO": {"name": "Romania", "google_geo": "RO", "google_trends_pn": "romania", "languages": ["ro"]},
    "GR": {"name": "Greece", "google_geo": "GR", "google_trends_pn": "greece", "languages": ["el"]},
    "HU": {"name": "Hungary", "google_geo": "HU", "google_trends_pn": "hungary", "languages": ["hu"]},
    "UA": {"name": "Ukraine", "google_geo": "UA", "google_trends_pn": "ukraine", "languages": ["uk"]},
    # אסיה-פסיפיק
    "IN": {"name": "India", "google_geo": "IN", "google_trends_pn": "india", "languages": ["en", "hi"]},
    "JP": {"name": "Japan", "google_geo": "JP", "google_trends_pn": "japan", "languages": ["ja"]},
    "KR": {"name": "South Korea", "google_geo": "KR", "google_trends_pn": "south_korea", "languages": ["ko"]},
    "CN": {"name": "China", "google_geo": "CN", "google_trends_pn": "china", "languages": ["zh"]},
    "SG": {"name": "Singapore", "google_geo": "SG", "google_trends_pn": "singapore", "languages": ["en", "zh"]},
    "AU": {"name": "Australia", "google_geo": "AU", "google_trends_pn": "australia", "languages": ["en"]},
    "NZ": {"name": "New Zealand", "google_geo": "NZ", "google_trends_pn": "new_zealand", "languages": ["en"]},
    "TW": {"name": "Taiwan", "google_geo": "TW", "google_trends_pn": "taiwan", "languages": ["zh"]},
    "TH": {"name": "Thailand", "google_geo": "TH", "google_trends_pn": "thailand", "languages": ["th"]},
    "VN": {"name": "Vietnam", "google_geo": "VN", "google_trends_pn": "vietnam", "languages": ["vi"]},
    "PH": {"name": "Philippines", "google_geo": "PH", "google_trends_pn": "philippines", "languages": ["en", "tl"]},
    "ID": {"name": "Indonesia", "google_geo": "ID", "google_trends_pn": "indonesia", "languages": ["id"]},
    "MY": {"name": "Malaysia", "google_geo": "MY", "google_trends_pn": "malaysia", "languages": ["ms", "en"]},
    # דרום אמריקה
    "BR": {"name": "Brazil", "google_geo": "BR", "google_trends_pn": "brazil", "languages": ["pt"]},
    "AR": {"name": "Argentina", "google_geo": "AR", "google_trends_pn": "argentina", "languages": ["es"]},
    "CL": {"name": "Chile", "google_geo": "CL", "google_trends_pn": "chile", "languages": ["es"]},
    "CO": {"name": "Colombia", "google_geo": "CO", "google_trends_pn": "colombia", "languages": ["es"]},
    # אפריקה
    "ZA": {"name": "South Africa", "google_geo": "ZA", "google_trends_pn": "south_africa", "languages": ["en"]},
    "NG": {"name": "Nigeria", "google_geo": "NG", "google_trends_pn": "nigeria", "languages": ["en"]},
    "KE": {"name": "Kenya", "google_geo": "KE", "google_trends_pn": "kenya", "languages": ["en", "sw"]},
}

# ---------------------------------------------------------------------------
# משקלות מקורות לחישוב ציון הזדמנות
# ---------------------------------------------------------------------------
SOURCE_WEIGHTS: dict[str, float] = {
    "google_trends": 0.15,
    "google_trends_jobs": 0.15,
    "stackoverflow": 0.12,
    "hackernews": 0.10,
    "github": 0.12,
    "reddit": 0.08,
    "wikipedia": 0.08,
    "devto": 0.06,
    "youtube_trends": 0.08,
    "npm_pypi": 0.06,
}

# ---------------------------------------------------------------------------
# נושאים לסריקת שוק
# ---------------------------------------------------------------------------
SCAN_TOPICS: list[str] = [
    "artificial intelligence", "machine learning", "data science", "python programming",
    "web development", "cloud computing", "cybersecurity", "devops", "blockchain",
    "product management", "ui ux design", "data engineering", "mobile development",
    "game development", "robotics", "quantum computing", "internet of things",
    "augmented reality", "3d printing", "drone technology", "prompt engineering",
    "generative AI", "large language models", "computer vision", "natural language processing",
    "kubernetes", "microservices", "system design", "software architecture",
    "agile methodology", "digital marketing", "seo", "content marketing",
    "project management", "leadership skills", "public speaking",
    "financial modeling", "cryptocurrency", "defi", "no code development",
    "low code platforms", "api development", "graphql", "rust programming",
    "golang", "typescript", "react", "angular", "vue.js",
]

# ---------------------------------------------------------------------------
# טיימאאוט ברירת מחדל לבקשות HTTP
# ---------------------------------------------------------------------------
_HTTP_TIMEOUT = 10.0


# ===========================================================================
# מודלים — Pydantic
# ===========================================================================

class SourceResult(BaseModel):
    """תוצאה ממקור בודד."""
    source: str
    score: float = 0.0
    success: bool = False
    data: dict = Field(default_factory=dict)
    error: str | None = None


class SearchResult(BaseModel):
    """תוצאת ניתוח מלאה עבור נושא אחד."""
    topic: str
    opportunity_score: float = 0.0
    confidence: float = 0.0
    demand_signal: str = "low"
    growth_signal: str = "stable"
    evidence_sources: list[str] = Field(default_factory=list)
    why_now: str = ""
    recommended_action: str = ""
    source_breakdown: list[SourceResult] = Field(default_factory=list)
    raw_data: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """תגובה לשאילתת ניתוח."""
    query: str
    country_code: str
    results: list[SearchResult]
    total_sources_queried: int = 0
    sources_succeeded: int = 0
    analysis_time_ms: int = 0
    timestamp: str = ""


class DeepAnalyzeResponse(BaseModel):
    """תגובה לניתוח מעמיק — כולל ציון ביקוש ללמידה."""
    query: str
    country_code: str
    opportunity_score: float = 0.0
    learning_demand_score: float = 0.0
    confidence: float = 0.0
    source_breakdown: list[SourceResult] = Field(default_factory=list)
    learning_signals: dict = Field(default_factory=dict)
    demand_signal: str = "low"
    growth_signal: str = "stable"
    why_now: str = ""
    recommended_action: str = ""
    raw_data: dict = Field(default_factory=dict)
    analysis_time_ms: int = 0
    timestamp: str = ""


class TrendingResponse(BaseModel):
    """תגובה לנושאים טרנדיים."""
    country_code: str
    trending_topics: list[dict]
    source: str
    timestamp: str


class MarketScanItem(BaseModel):
    """פריט בסריקת שוק."""
    topic: str
    opportunity_score: float = 0.0
    trend_score: float = 0.0
    rank: int = 0


class MarketScanResponse(BaseModel):
    """תגובה לסריקת שוק."""
    country_code: str
    country_name: str
    topics_scanned: int = 0
    results: list[MarketScanItem] = Field(default_factory=list)
    scan_time_ms: int = 0
    timestamp: str = ""


# ===========================================================================
# פונקציות עזר — שליפת נתונים ממקורות
# ===========================================================================

def _get_geo(country_code: str) -> str:
    """מחזיר קוד גיאו עבור Google Trends."""
    country = COUNTRIES.get(country_code, {})
    return country.get("google_geo", "")


def _get_pn(country_code: str) -> str:
    """מחזיר שם מדינה עבור Google Trends trending."""
    country = COUNTRIES.get(country_code, {})
    return country.get("google_trends_pn", "united_states")


async def _fetch_google_trends(query: str, geo: str) -> SourceResult:
    """שליפת נתוני Google Trends — עניין לאורך זמן ושאילתות קשורות."""
    try:
        # pytrends הוא סינכרוני, מריצים בתוך executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _sync_google_trends, query, geo)
        return result
    except Exception as e:
        logger.warning("Google Trends failed for '%s': %s", query, e)
        return SourceResult(source="google_trends", error=str(e))


def _sync_google_trends(query: str, geo: str) -> SourceResult:
    """חלק סינכרוני של שליפת Google Trends."""
    from pytrends.request import TrendReq

    pt = TrendReq(hl="en-US", tz=360, timeout=(8, 20))
    pt.build_payload([query], timeframe="today 3-m", geo=geo)
    interest = pt.interest_over_time()

    if interest is None or interest.empty or query not in interest.columns:
        return SourceResult(source="google_trends", score=0.0, success=True, data={"note": "no data"})

    series = interest[query]
    current = float(series.iloc[-1])
    avg = float(series.mean())
    peak = float(series.max())
    recent_avg = float(series[-4:].mean()) if len(series) >= 4 else avg
    older_avg = float(series[:4].mean()) if len(series) >= 4 else avg

    # נרמול ציון: current / 100
    score = round(current / 100.0, 4)

    # כיוון
    if older_avg > 0:
        ratio = recent_avg / older_avg
    else:
        ratio = 1.0

    if ratio > 1.3:
        direction = "surging"
    elif ratio > 1.1:
        direction = "rising"
    elif ratio < 0.7:
        direction = "declining"
    else:
        direction = "stable"

    # שאילתות קשורות
    related = {}
    try:
        rq = pt.related_queries()
        if query in rq:
            top = rq[query].get("top")
            rising = rq[query].get("rising")
            if top is not None and not top.empty:
                related["top_queries"] = top["query"].head(5).tolist()
            if rising is not None and not rising.empty:
                related["rising_queries"] = rising["query"].head(5).tolist()
    except Exception:
        pass

    data = {
        "current": current,
        "average": round(avg, 1),
        "peak": peak,
        "recent_avg": round(recent_avg, 1),
        "older_avg": round(older_avg, 1),
        "direction": direction,
        "data_points": len(series),
        **related,
    }

    return SourceResult(source="google_trends", score=score, success=True, data=data)


async def _fetch_google_trends_jobs(query: str, geo: str) -> SourceResult:
    """שליפת Google Trends עבור "[query] jobs" — למדידת ביקוש בשוק העבודה."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _sync_google_trends_jobs, query, geo)
        return result
    except Exception as e:
        logger.warning("Google Trends Jobs failed for '%s': %s", query, e)
        return SourceResult(source="google_trends_jobs", error=str(e))


def _sync_google_trends_jobs(query: str, geo: str) -> SourceResult:
    """חלק סינכרוני — Google Trends עבור "[query] jobs"."""
    from pytrends.request import TrendReq

    jobs_query = f"{query} jobs"
    pt = TrendReq(hl="en-US", tz=360, timeout=(8, 20))
    pt.build_payload([jobs_query], timeframe="today 3-m", geo=geo)
    interest = pt.interest_over_time()

    if interest is None or interest.empty or jobs_query not in interest.columns:
        return SourceResult(source="google_trends_jobs", score=0.0, success=True, data={"note": "no data"})

    series = interest[jobs_query]
    current = float(series.iloc[-1])
    avg = float(series.mean())
    score = round(current / 100.0, 4)

    return SourceResult(
        source="google_trends_jobs",
        score=score,
        success=True,
        data={"query": jobs_query, "current": current, "average": round(avg, 1)},
    )


async def _fetch_stackoverflow(query: str) -> SourceResult:
    """שליפת נתוני Stack Overflow — תגיות, שאלות אחרונות, אחוז תשובות."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            tag = query.lower().replace(" ", "-")
            total_questions = 0
            recent_count = 0
            answer_rate = 0.0

            # מידע על תגית
            resp = await client.get(
                f"https://api.stackexchange.com/2.3/tags/{tag}/info",
                params={"site": "stackoverflow"},
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    total_questions = items[0].get("count", 0)

            # שאלות אחרונות
            resp2 = await client.get(
                "https://api.stackexchange.com/2.3/search/excerpts",
                params={
                    "site": "stackoverflow", "q": query,
                    "sort": "creation", "order": "desc", "pagesize": 10,
                },
            )
            if resp2.status_code == 200:
                items2 = resp2.json().get("items", [])
                recent_count = len(items2)
                # חישוב אחוז תשובות
                answered = sum(1 for i in items2 if i.get("has_accepted_answer", False))
                answer_rate = round(answered / max(recent_count, 1), 2)

            # נרמול ציון: log scale מ-0 עד 1
            if total_questions > 0:
                score = min(1.0, math.log10(max(total_questions, 1)) / 6.0)  # 1M questions = 1.0
            else:
                score = min(1.0, recent_count / 10.0) * 0.3  # ציון נמוך יותר אם אין תגית ישירה

            return SourceResult(
                source="stackoverflow",
                score=round(score, 4),
                success=True,
                data={
                    "tag": tag,
                    "total_questions": total_questions,
                    "recent_questions": recent_count,
                    "answer_rate": answer_rate,
                },
            )
    except Exception as e:
        logger.warning("StackOverflow failed for '%s': %s", query, e)
        return SourceResult(source="stackoverflow", error=str(e))


async def _fetch_hackernews(query: str) -> SourceResult:
    """שליפת Hacker News דרך Algolia API — אזכורים, ציונים, פעילות אחרונה."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": query, "tags": "story", "hitsPerPage": 30},
            )
            if resp.status_code != 200:
                return SourceResult(source="hackernews", error=f"HTTP {resp.status_code}")

            data = resp.json()
            hits = data.get("hits", [])
            total_hits = data.get("nbHits", 0)
            mentions = len(hits)

            scores = [h.get("points", 0) or 0 for h in hits]
            avg_score = round(sum(scores) / max(len(scores), 1), 1)
            max_score = max(scores) if scores else 0
            comments = [h.get("num_comments", 0) or 0 for h in hits]
            avg_comments = round(sum(comments) / max(len(comments), 1), 1)

            # נרמול: total_hits log scale
            if total_hits > 0:
                score = min(1.0, math.log10(max(total_hits, 1)) / 5.0)  # 100K hits = 1.0
            else:
                score = 0.0

            return SourceResult(
                source="hackernews",
                score=round(score, 4),
                success=True,
                data={
                    "total_hits": total_hits,
                    "recent_mentions": mentions,
                    "avg_score": avg_score,
                    "max_score": max_score,
                    "avg_comments": avg_comments,
                    "top_titles": [h.get("title", "")[:100] for h in hits[:5]],
                },
            )
    except Exception as e:
        logger.warning("HackerNews failed for '%s': %s", query, e)
        return SourceResult(source="hackernews", error=str(e))


async def _fetch_wikipedia(query: str) -> SourceResult:
    """שליפת צפיות בויקיפדיה — 30 ימים אחרונים — מודד עניין ציבורי."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            # קודם מחפשים את שם הערך המדויק
            article_title = query.replace(" ", "_")
            # Pageviews API: 30 ימים אחרונים
            today = datetime.now(timezone.utc)
            end = today.strftime("%Y%m%d")
            start_dt = today.replace(day=max(today.day - 30, 1)) if today.day > 30 else today
            # פשוט לוקחים 30 ימים אחורה
            import calendar
            month = today.month
            year = today.year
            if today.day >= 30:
                start_str = f"{year}{month:02d}01"
            else:
                # חודש קודם
                prev_month = month - 1 if month > 1 else 12
                prev_year = year if month > 1 else year - 1
                days_in_prev = calendar.monthrange(prev_year, prev_month)[1]
                start_day = max(today.day, 1)
                start_str = f"{prev_year}{prev_month:02d}{start_day:02d}"

            url = (
                f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
                f"/en.wikipedia/all-access/all-agents/{article_title}/daily/{start_str}/{end}"
            )
            resp = await client.get(url, headers={"User-Agent": "COGNET-LDI/1.0"})

            if resp.status_code != 200:
                return SourceResult(source="wikipedia", score=0.0, success=True, data={"note": "article not found"})

            items = resp.json().get("items", [])
            views = [i.get("views", 0) for i in items]
            total_views = sum(views)
            avg_daily = round(total_views / max(len(views), 1), 1)

            # נרמול: log scale, 100K views/month = 1.0
            if total_views > 0:
                score = min(1.0, math.log10(max(total_views, 1)) / 5.0)
            else:
                score = 0.0

            return SourceResult(
                source="wikipedia",
                score=round(score, 4),
                success=True,
                data={
                    "article": article_title,
                    "total_views_30d": total_views,
                    "avg_daily_views": avg_daily,
                    "days_tracked": len(views),
                },
            )
    except Exception as e:
        logger.warning("Wikipedia failed for '%s': %s", query, e)
        return SourceResult(source="wikipedia", error=str(e))


async def _fetch_github(query: str) -> SourceResult:
    """שליפת GitHub — מספר ריפוזיטוריז, כוכבים, ריפוזיטוריז חדשים."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "stars", "order": "desc", "per_page": 10},
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if resp.status_code != 200:
                return SourceResult(source="github", error=f"HTTP {resp.status_code}")

            data = resp.json()
            total_count = data.get("total_count", 0)
            items = data.get("items", [])

            total_stars = sum(i.get("stargazers_count", 0) for i in items)
            total_forks = sum(i.get("forks_count", 0) for i in items)

            # ריפוזיטוריז שנוצרו לאחרונה (בשנה האחרונה)
            recent_repos = 0
            for item in items:
                created = item.get("created_at", "")
                if created and created[:4] >= str(datetime.now().year - 1):
                    recent_repos += 1

            # נרמול: log scale
            if total_count > 0:
                score = min(1.0, math.log10(max(total_count, 1)) / 5.5)  # ~300K repos = 1.0
            else:
                score = 0.0

            return SourceResult(
                source="github",
                score=round(score, 4),
                success=True,
                data={
                    "total_repos": total_count,
                    "top_10_stars": total_stars,
                    "top_10_forks": total_forks,
                    "recent_repos_in_top10": recent_repos,
                    "top_repos": [
                        {"name": i.get("full_name", ""), "stars": i.get("stargazers_count", 0)}
                        for i in items[:5]
                    ],
                },
            )
    except Exception as e:
        logger.warning("GitHub failed for '%s': %s", query, e)
        return SourceResult(source="github", error=str(e))


async def _fetch_reddit(query: str) -> SourceResult:
    """שליפת Reddit — חיפוש פוסטים וסאברדיטים."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(
                "https://old.reddit.com/search.json",
                params={"q": query, "sort": "relevance", "limit": 25, "t": "month"},
                headers={"User-Agent": "COGNET-LDI/1.0"},
            )
            if resp.status_code != 200:
                return SourceResult(source="reddit", error=f"HTTP {resp.status_code}")

            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            post_count = len(posts)

            scores_list = [p.get("data", {}).get("score", 0) for p in posts]
            avg_score = round(sum(scores_list) / max(len(scores_list), 1), 1)
            total_comments = sum(p.get("data", {}).get("num_comments", 0) for p in posts)

            subreddits = list(set(p.get("data", {}).get("subreddit", "") for p in posts))

            # נרמול
            if post_count > 0:
                score = min(1.0, post_count / 25.0) * 0.5 + min(1.0, avg_score / 500.0) * 0.5
            else:
                score = 0.0

            return SourceResult(
                source="reddit",
                score=round(min(1.0, score), 4),
                success=True,
                data={
                    "posts_found": post_count,
                    "avg_score": avg_score,
                    "total_comments": total_comments,
                    "subreddits": subreddits[:10],
                },
            )
    except Exception as e:
        logger.warning("Reddit failed for '%s': %s", query, e)
        return SourceResult(source="reddit", error=str(e))


async def _fetch_devto(query: str) -> SourceResult:
    """שליפת Dev.to — מאמרים, תגובות, תגיות פופולריות."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.get(
                "https://dev.to/api/articles",
                params={"tag": query.lower().replace(" ", ""), "per_page": 20, "top": 30},
            )
            # ננסה גם חיפוש רגיל אם תגית לא עובדת
            if resp.status_code != 200 or not resp.json():
                resp = await client.get(
                    "https://dev.to/api/articles",
                    params={"tag": query.lower().replace(" ", "-"), "per_page": 20, "top": 30},
                )

            if resp.status_code != 200:
                return SourceResult(source="devto", error=f"HTTP {resp.status_code}")

            articles = resp.json()
            if not isinstance(articles, list):
                articles = []

            article_count = len(articles)
            reactions = [a.get("positive_reactions_count", 0) for a in articles]
            avg_reactions = round(sum(reactions) / max(len(reactions), 1), 1)
            total_reactions = sum(reactions)
            comments_count = sum(a.get("comments_count", 0) for a in articles)

            # נרמול
            if article_count > 0:
                score = min(1.0, article_count / 20.0) * 0.4 + min(1.0, avg_reactions / 100.0) * 0.6
            else:
                score = 0.0

            return SourceResult(
                source="devto",
                score=round(min(1.0, score), 4),
                success=True,
                data={
                    "articles_found": article_count,
                    "avg_reactions": avg_reactions,
                    "total_reactions": total_reactions,
                    "total_comments": comments_count,
                },
            )
    except Exception as e:
        logger.warning("Dev.to failed for '%s': %s", query, e)
        return SourceResult(source="devto", error=str(e))


async def _fetch_youtube_trends(query: str, geo: str) -> SourceResult:
    """שליפת Google Trends בקטגוריית YouTube — מודד עניין בתוכן וידאו."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _sync_youtube_trends, query, geo)
        return result
    except Exception as e:
        logger.warning("YouTube Trends failed for '%s': %s", query, e)
        return SourceResult(source="youtube_trends", error=str(e))


def _sync_youtube_trends(query: str, geo: str) -> SourceResult:
    """חלק סינכרוני — Google Trends קטגוריית YouTube."""
    from pytrends.request import TrendReq

    pt = TrendReq(hl="en-US", tz=360, timeout=(8, 20))
    # gprop='youtube' מסנן לחיפושי YouTube
    pt.build_payload([query], timeframe="today 3-m", geo=geo, gprop="youtube")
    interest = pt.interest_over_time()

    if interest is None or interest.empty or query not in interest.columns:
        return SourceResult(source="youtube_trends", score=0.0, success=True, data={"note": "no data"})

    series = interest[query]
    current = float(series.iloc[-1])
    avg = float(series.mean())
    score = round(current / 100.0, 4)

    return SourceResult(
        source="youtube_trends",
        score=score,
        success=True,
        data={"current": current, "average": round(avg, 1)},
    )


async def _fetch_npm_pypi(query: str) -> SourceResult:
    """בדיקת קיום חבילת npm או PyPI והבאת סטטיסטיקות בסיסיות."""
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            pkg_name = query.lower().replace(" ", "-")
            npm_found = False
            pypi_found = False
            npm_data: dict[str, Any] = {}
            pypi_data: dict[str, Any] = {}

            # npm
            try:
                resp = await client.get(f"https://registry.npmjs.org/{pkg_name}")
                if resp.status_code == 200:
                    info = resp.json()
                    npm_found = True
                    npm_data = {
                        "name": info.get("name", ""),
                        "description": (info.get("description") or "")[:200],
                        "latest_version": info.get("dist-tags", {}).get("latest", ""),
                    }
            except Exception:
                pass

            # PyPI
            try:
                resp = await client.get(f"https://pypi.org/pypi/{pkg_name}/json")
                if resp.status_code == 200:
                    info = resp.json()
                    pypi_found = True
                    pypi_info = info.get("info", {})
                    pypi_data = {
                        "name": pypi_info.get("name", ""),
                        "summary": (pypi_info.get("summary") or "")[:200],
                        "version": pypi_info.get("version", ""),
                        "downloads": info.get("info", {}).get("downloads", {}).get("last_month", 0),
                    }
            except Exception:
                pass

            # נניח גם חיפוש ללא מקף
            if not npm_found and not pypi_found:
                pkg_no_dash = query.lower().replace(" ", "").replace("-", "")
                try:
                    resp = await client.get(f"https://registry.npmjs.org/{pkg_no_dash}")
                    if resp.status_code == 200:
                        npm_found = True
                        info = resp.json()
                        npm_data = {"name": info.get("name", ""), "description": (info.get("description") or "")[:200]}
                except Exception:
                    pass
                try:
                    resp = await client.get(f"https://pypi.org/pypi/{pkg_no_dash}/json")
                    if resp.status_code == 200:
                        pypi_found = True
                        info = resp.json()
                        pypi_data = {"name": info.get("info", {}).get("name", "")}
                except Exception:
                    pass

            found_count = int(npm_found) + int(pypi_found)
            score = min(1.0, found_count * 0.5)  # 0, 0.5, or 1.0

            return SourceResult(
                source="npm_pypi",
                score=round(score, 4),
                success=True,
                data={
                    "npm_found": npm_found,
                    "pypi_found": pypi_found,
                    "npm": npm_data,
                    "pypi": pypi_data,
                },
            )
    except Exception as e:
        logger.warning("npm/PyPI failed for '%s': %s", query, e)
        return SourceResult(source="npm_pypi", error=str(e))


# ===========================================================================
# חישוב ציון משוקלל
# ===========================================================================

def _compute_scores(
    source_results: list[SourceResult],
) -> tuple[float, float, str, str, str, str]:
    """
    מחשב ציון הזדמנות משוקלל, ביטחון, אותות ביקוש וצמיחה, הסבר ופעולה מומלצת.
    מחזיר: (opportunity_score, confidence, demand_signal, growth_signal, why_now, action)
    """
    # ציון משוקלל
    weighted_sum = 0.0
    total_weight = 0.0
    succeeded = 0
    evidence: list[str] = []
    why_parts: list[str] = []

    for sr in source_results:
        weight = SOURCE_WEIGHTS.get(sr.source, 0.05)
        if sr.success:
            weighted_sum += sr.score * weight
            total_weight += weight
            succeeded += 1
            if sr.score > 0.1:
                evidence.append(sr.source)

    # נרמול — חלוקה במשקל הכולל של המקורות שהצליחו
    if total_weight > 0:
        opportunity_score = round(weighted_sum / total_weight, 4)
    else:
        opportunity_score = 0.0

    # ביטחון — אחוז המקורות שהצליחו
    total_sources = len(SOURCE_WEIGHTS)
    confidence = round(succeeded / total_sources, 2)

    # אות ביקוש
    if opportunity_score >= 0.7:
        demand_signal = "very_high"
    elif opportunity_score >= 0.5:
        demand_signal = "high"
    elif opportunity_score >= 0.3:
        demand_signal = "moderate"
    else:
        demand_signal = "low"

    # אות צמיחה — מבוסס על Google Trends אם זמין
    growth_signal = "stable"
    for sr in source_results:
        if sr.source == "google_trends" and sr.success:
            direction = sr.data.get("direction", "stable")
            growth_signal = direction
            break

    # הסבר "למה עכשיו"
    for sr in source_results:
        if not sr.success or sr.score < 0.15:
            continue
        if sr.source == "google_trends":
            direction = sr.data.get("direction", "stable")
            current = sr.data.get("current", 0)
            if direction in ("rising", "surging"):
                why_parts.append(f"Google Trends shows {direction} interest (current: {current}/100)")
        elif sr.source == "google_trends_jobs":
            current = sr.data.get("current", 0)
            if current > 20:
                why_parts.append(f"Job market demand detected ({current}/100 on Google Trends)")
        elif sr.source == "stackoverflow":
            total_q = sr.data.get("total_questions", 0)
            if total_q > 10000:
                why_parts.append(f"Strong developer community ({total_q:,} Stack Overflow questions)")
        elif sr.source == "hackernews":
            total_hits = sr.data.get("total_hits", 0)
            if total_hits > 100:
                why_parts.append(f"Active tech discussion ({total_hits:,} Hacker News mentions)")
        elif sr.source == "github":
            repos = sr.data.get("total_repos", 0)
            if repos > 1000:
                why_parts.append(f"Rich open-source ecosystem ({repos:,} GitHub repos)")
        elif sr.source == "reddit":
            posts = sr.data.get("posts_found", 0)
            if posts > 5:
                why_parts.append(f"Active community discussion on Reddit ({posts} recent posts)")
        elif sr.source == "wikipedia":
            views = sr.data.get("total_views_30d", 0)
            if views > 10000:
                why_parts.append(f"High public interest ({views:,} Wikipedia views in 30 days)")

    why_now = ". ".join(why_parts) if why_parts else "Limited signal data — more analysis needed."

    # פעולה מומלצת
    if opportunity_score >= 0.7:
        action = "Strong opportunity — consider building content immediately"
    elif opportunity_score >= 0.5:
        action = "Promising opportunity — monitor closely and plan content"
    elif opportunity_score >= 0.3:
        action = "Moderate interest — add to watchlist"
    else:
        action = "Low current demand — defer unless strategic"

    return opportunity_score, confidence, demand_signal, growth_signal, why_now, action


# ===========================================================================
# ניתוח נושא מלא — פונקציית ליבה
# ===========================================================================

async def _full_analysis(query: str, country_code: str) -> tuple[list[SourceResult], float]:
    """מריץ את כל 10 המקורות במקביל ומחזיר תוצאות + זמן."""
    start = time.monotonic()
    geo = _get_geo(country_code)

    # שליפה מקבילית מכל המקורות
    results = await asyncio.gather(
        _fetch_google_trends(query, geo),
        _fetch_google_trends_jobs(query, geo),
        _fetch_stackoverflow(query),
        _fetch_hackernews(query),
        _fetch_wikipedia(query),
        _fetch_github(query),
        _fetch_reddit(query),
        _fetch_devto(query),
        _fetch_youtube_trends(query, geo),
        _fetch_npm_pypi(query),
        return_exceptions=True,
    )

    # המרת חריגות לתוצאות כושלות
    source_results: list[SourceResult] = []
    source_names = list(SOURCE_WEIGHTS.keys())
    for i, r in enumerate(results):
        if isinstance(r, SourceResult):
            source_results.append(r)
        elif isinstance(r, Exception):
            name = source_names[i] if i < len(source_names) else f"source_{i}"
            logger.warning("Source %s raised exception: %s", name, r)
            source_results.append(SourceResult(source=name, error=str(r)))
        else:
            source_results.append(SourceResult(source=f"source_{i}", error="unexpected result type"))

    elapsed = time.monotonic() - start
    return source_results, elapsed


# ===========================================================================
# נקודות קצה — Endpoints
# ===========================================================================

@router.get("/analyze", response_model=SearchResponse)
async def analyze_topic(
    q: str = Query(..., min_length=2, max_length=200, description="נושא לניתוח — כל טקסט חופשי"),
    country_code: str = Query("IL", description="קוד מדינה (ISO 2-letter)"),
) -> SearchResponse:
    """
    ניתוח נושא בזמן אמת באמצעות 10+ מקורות נתונים חיים.
    מקבל כל נושא — לא רק מרשימה קבועה.

    דוגמה: /v1/search/analyze?q=machine+learning&country_code=IL
    """
    start_time = time.monotonic()
    source_results, _ = await _full_analysis(q, country_code)

    opportunity_score, confidence, demand_signal, growth_signal, why_now, action = _compute_scores(source_results)
    succeeded = sum(1 for sr in source_results if sr.success)
    evidence = [sr.source for sr in source_results if sr.success and sr.score > 0.1]

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    result = SearchResult(
        topic=q,
        opportunity_score=opportunity_score,
        confidence=confidence,
        demand_signal=demand_signal,
        growth_signal=growth_signal,
        evidence_sources=evidence,
        why_now=why_now,
        recommended_action=action,
        source_breakdown=source_results,
        raw_data={sr.source: sr.data for sr in source_results if sr.success},
    )

    return SearchResponse(
        query=q,
        country_code=country_code,
        results=[result],
        total_sources_queried=len(source_results),
        sources_succeeded=succeeded,
        analysis_time_ms=elapsed_ms,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/deep-analyze", response_model=DeepAnalyzeResponse)
async def deep_analyze_topic(
    q: str = Query(..., min_length=2, max_length=200, description="נושא לניתוח מעמיק"),
    country_code: str = Query("IL", description="קוד מדינה"),
) -> DeepAnalyzeResponse:
    """
    ניתוח מעמיק — כולל ציון ביקוש ללמידה.
    שואב את כל הנתונים של analyze + מגמות למידה:
    "[topic] course", "[topic] tutorial", "[topic] certification"
    """
    start_time = time.monotonic()
    geo = _get_geo(country_code)

    # שליפה מקבילית: כל המקורות + אותות למידה
    all_tasks = [
        _full_analysis(q, country_code),
        _fetch_learning_trends(q, geo),
    ]
    results = await asyncio.gather(*all_tasks, return_exceptions=True)

    # תוצאות מקורות רגילים
    if isinstance(results[0], tuple):
        source_results, _ = results[0]
    else:
        source_results = []

    # תוצאות אותות למידה
    if isinstance(results[1], dict):
        learning_signals = results[1]
    else:
        learning_signals = {"course": 0.0, "tutorial": 0.0, "certification": 0.0, "error": str(results[1])}

    opportunity_score, confidence, demand_signal, growth_signal, why_now, action = _compute_scores(source_results)

    # חישוב ציון ביקוש ללמידה
    learning_scores = [
        learning_signals.get("course", 0.0),
        learning_signals.get("tutorial", 0.0),
        learning_signals.get("certification", 0.0),
    ]
    learning_demand_score = round(sum(learning_scores) / max(len(learning_scores), 1), 4)

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    return DeepAnalyzeResponse(
        query=q,
        country_code=country_code,
        opportunity_score=opportunity_score,
        learning_demand_score=learning_demand_score,
        confidence=confidence,
        source_breakdown=source_results,
        learning_signals=learning_signals,
        demand_signal=demand_signal,
        growth_signal=growth_signal,
        why_now=why_now,
        recommended_action=action,
        raw_data={sr.source: sr.data for sr in source_results if sr.success},
        analysis_time_ms=elapsed_ms,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


async def _fetch_learning_trends(query: str, geo: str) -> dict[str, Any]:
    """שליפת Google Trends עבור ביטויי למידה — course, tutorial, certification."""
    suffixes = ["course", "tutorial", "certification"]
    tasks = []
    for suffix in suffixes:
        tasks.append(_sync_learning_trend_async(query, suffix, geo))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    output: dict[str, Any] = {}
    for i, suffix in enumerate(suffixes):
        r = results[i]
        if isinstance(r, float):
            output[suffix] = r
        elif isinstance(r, Exception):
            output[suffix] = 0.0
            output[f"{suffix}_error"] = str(r)
        else:
            output[suffix] = 0.0

    return output


async def _sync_learning_trend_async(query: str, suffix: str, geo: str) -> float:
    """מריץ שליפת Google Trends ללמידה ב-executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_learning_trend, query, suffix, geo)


def _sync_learning_trend(query: str, suffix: str, geo: str) -> float:
    """חלק סינכרוני — Google Trends עבור "[query] [suffix]"."""
    from pytrends.request import TrendReq

    full_query = f"{query} {suffix}"
    pt = TrendReq(hl="en-US", tz=360, timeout=(8, 20))
    pt.build_payload([full_query], timeframe="today 3-m", geo=geo)
    interest = pt.interest_over_time()

    if interest is None or interest.empty or full_query not in interest.columns:
        return 0.0

    series = interest[full_query]
    current = float(series.iloc[-1])
    return round(current / 100.0, 4)


@router.get("/trending", response_model=TrendingResponse)
async def get_trending(
    country_code: str = Query("IL", description="קוד מדינה לנושאים טרנדיים"),
) -> TrendingResponse:
    """קבלת נושאים טרנדיים כרגע עבור כל מדינה נתמכת."""
    trending_topics: list[dict] = []
    pn = _get_pn(country_code)

    try:
        loop = asyncio.get_event_loop()
        trending_topics = await loop.run_in_executor(None, _sync_trending, pn)
    except Exception as e:
        logger.warning("Trending search failed for %s: %s", country_code, e)

    return TrendingResponse(
        country_code=country_code,
        trending_topics=trending_topics,
        source="Google Trends Daily",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _sync_trending(pn: str) -> list[dict]:
    """חלק סינכרוני — Google Trends trending searches."""
    from pytrends.request import TrendReq

    pt = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
    df = pt.trending_searches(pn=pn)
    results: list[dict] = []
    if df is not None and not df.empty:
        for idx, row in df.head(20).iterrows():
            results.append({
                "rank": idx + 1,
                "topic": str(row.iloc[0]),
                "source": "google_trends_daily",
            })
    return results


@router.get("/compare")
async def compare_topics(
    topics: str = Query(..., description="נושאים מופרדים בפסיקים (עד 5)"),
    country_code: str = Query("IL", description="קוד מדינה"),
) -> dict:
    """
    השוואת עד 5 נושאים זה לצד זה — כל המקורות.
    כל נושא מקבל ציון הזדמנות מלא מכל 10 המקורות.
    """
    topic_list = [t.strip() for t in topics.split(",") if t.strip()][:5]

    if len(topic_list) < 2:
        return {"error": "יש לספק לפחות 2 נושאים מופרדים בפסיקים"}

    start_time = time.monotonic()

    # ניתוח מקביל של כל הנושאים
    tasks = [_full_analysis(topic, country_code) for topic in topic_list]
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    comparison: list[dict] = []
    for i, topic in enumerate(topic_list):
        r = all_results[i]
        if isinstance(r, tuple):
            source_results, _ = r
            opp_score, confidence, demand, growth, why_now, action = _compute_scores(source_results)
            comparison.append({
                "topic": topic,
                "opportunity_score": opp_score,
                "confidence": confidence,
                "demand_signal": demand,
                "growth_signal": growth,
                "why_now": why_now,
                "recommended_action": action,
                "source_scores": {sr.source: sr.score for sr in source_results if sr.success},
                "relative_rank": 0,
            })
        else:
            comparison.append({
                "topic": topic,
                "opportunity_score": 0.0,
                "error": str(r),
                "relative_rank": 0,
            })

    # דירוג יחסי
    comparison.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
    for i, c in enumerate(comparison):
        c["relative_rank"] = i + 1

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    return {
        "topics": topic_list,
        "country_code": country_code,
        "comparison": comparison,
        "analysis_time_ms": elapsed_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/market-scan", response_model=MarketScanResponse)
async def market_scan(
    country_code: str = Query("IL", description="קוד מדינה לסריקה"),
    limit: int = Query(50, ge=5, le=50, description="מספר נושאים לסרוק"),
) -> MarketScanResponse:
    """
    סריקת שוק — בודק את כל הנושאים המוגדרים מראש עבור מדינה מסוימת.
    משתמש ב-Google Trends batch comparison (5 נושאים בכל פעם) למהירות.
    מחזיר את כל הנושאים מדורגים לפי ציון הזדמנות.
    """
    start_time = time.monotonic()
    country = COUNTRIES.get(country_code, {"name": country_code})
    geo = _get_geo(country_code)
    topics_to_scan = SCAN_TOPICS[:limit]

    # שליפת Google Trends באצוות של 5 (מגבלת API)
    batches: list[list[str]] = []
    for i in range(0, len(topics_to_scan), 5):
        batches.append(topics_to_scan[i:i + 5])

    loop = asyncio.get_event_loop()
    batch_tasks = [
        loop.run_in_executor(None, _sync_batch_trends, batch, geo)
        for batch in batches
    ]
    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

    # איחוד תוצאות מכל האצוות
    topic_scores: dict[str, float] = {}
    for i, br in enumerate(batch_results):
        if isinstance(br, dict):
            topic_scores.update(br)
        elif isinstance(br, Exception):
            logger.warning("Batch %d failed: %s", i, br)
            # מילוי אפסים לנושאים שנכשלו
            for t in batches[i]:
                topic_scores.setdefault(t, 0.0)

    # בניית תוצאות מדורגות
    items: list[MarketScanItem] = []
    for topic in topics_to_scan:
        score = topic_scores.get(topic, 0.0)
        items.append(MarketScanItem(topic=topic, opportunity_score=0.0, trend_score=score))

    # דירוג לפי ציון
    items.sort(key=lambda x: x.trend_score, reverse=True)
    for i, item in enumerate(items):
        item.rank = i + 1
        # ציון הזדמנות מוערך על בסיס ציון הטרנד (פרוקסי מהיר)
        item.opportunity_score = round(item.trend_score, 4)

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    return MarketScanResponse(
        country_code=country_code,
        country_name=country.get("name", country_code),
        topics_scanned=len(topics_to_scan),
        results=items,
        scan_time_ms=elapsed_ms,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _sync_batch_trends(topics: list[str], geo: str) -> dict[str, float]:
    """שליפת Google Trends עבור אצווה של עד 5 נושאים — מחזיר ציון נרמול לכל אחד."""
    from pytrends.request import TrendReq

    pt = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
    pt.build_payload(topics, timeframe="today 3-m", geo=geo)
    interest = pt.interest_over_time()

    scores: dict[str, float] = {}
    if interest is not None and not interest.empty:
        for topic in topics:
            if topic in interest.columns:
                series = interest[topic]
                current = float(series.iloc[-1])
                scores[topic] = round(current / 100.0, 4)
            else:
                scores[topic] = 0.0
    else:
        for topic in topics:
            scores[topic] = 0.0

    return scores


@router.get("/countries")
async def list_countries() -> dict:
    """רשימת כל המדינות הנתמכות עם פרטיהן."""
    return {
        "total": len(COUNTRIES),
        "countries": {
            code: {"name": info["name"], "languages": info["languages"]}
            for code, info in COUNTRIES.items()
        },
    }


@router.get("/sources")
async def list_sources() -> dict:
    """רשימת כל מקורות הנתונים ומשקלותיהם."""
    return {
        "total": len(SOURCE_WEIGHTS),
        "sources": SOURCE_WEIGHTS,
        "description": {
            "google_trends": "Google search interest over time",
            "google_trends_jobs": "Job market demand via Google Trends for '[topic] jobs'",
            "stackoverflow": "Developer Q&A activity and tag popularity",
            "hackernews": "Tech community discussion and story mentions",
            "github": "Open-source repository counts and star trends",
            "reddit": "Community discussion across subreddits",
            "wikipedia": "Public interest measured by article pageviews",
            "devto": "Developer blog articles and engagement",
            "youtube_trends": "Video content interest via YouTube search trends",
            "npm_pypi": "Package ecosystem presence (npm + PyPI)",
        },
    }
