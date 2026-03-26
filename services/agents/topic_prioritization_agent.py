"""
TopicPrioritizationAgent — OPERATIONAL (MVP)
מטרה: שילוב אותות ניתוח מגמה, ביקוש משרות ופערי כישורים לדירוג נושאים.
קלטים: trend_signals (מ-TrendAnalysisAgent), job_demand_signals (מ-JobDemandAgent), skill_gaps (מ-SkillGapAgent)
פלטים: {ranked_topics: [{topic_name, composite_score, signal_sources, evidence_count, recommended_action}]}
לא בתחום: אינו מייצר OpportunityBriefs סופיים — זה תפקידם של RankingEngine + OpportunityGenerator
"""
import logging
import time
import uuid

from services.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)

# משקלי ציון מורכב
_TREND_WEIGHT = 0.35
_JOB_MARKET_WEIGHT = 0.45
_GAP_WEIGHT = 0.20

# סף נושאים מוחזרים
_MAX_TOPICS = 20


class TopicPrioritizationAgent(BaseAgent):
    """
    משלב אותות מרובים לדירוג נושאים מאוחד — מחזיר עד 20 נושאים מובילים.
    """

    @property
    def agent_name(self) -> str:
        return "TopicPrioritizationAgent"

    @property
    def purpose(self) -> str:
        return (
            "Combine trend analysis, job demand, and skill gap signals to produce "
            "a unified, prioritized topic ranking with composite scores and "
            "recommended actions for content development."
        )

    @property
    def non_goals(self) -> list[str]:
        return [
            "Does not generate final OpportunityBrief objects — that is the RankingEngine and OpportunityGenerator's responsibility.",
            "Does not fetch or normalize raw data — operates on pre-computed agent outputs only.",
            "Does not apply market-specific localization or regional adjustments.",
        ]

    async def run(
        self,
        run_id: uuid.UUID,
        trend_signals: list[dict] | None = None,
        job_demand_signals: list[dict] | None = None,
        skill_gaps: list[dict] | None = None,
        **kwargs,
    ) -> AgentResult:
        """
        משלב אותות ממספר סוכנים לדירוג נושאים מאוחד.

        Args:
            run_id: מזהה ריצת ה-pipeline.
            trend_signals: פלט מ-TrendAnalysisAgent — [{topic_name, trend_score, growth_score, evidence_count}].
            job_demand_signals: פלט מ-JobDemandAgent — [{skill_name/topic_name, demand_score, job_market_score}].
            skill_gaps: פלט מ-SkillGapAgent — [{topic_name, demand_score, gap_score, priority}].

        Returns:
            AgentResult עם output: {ranked_topics: [...]} ממוין יורד לפי composite_score, עד 20 נושאים.
        """
        start = time.monotonic()

        trend_signals = trend_signals or []
        job_demand_signals = job_demand_signals or []
        skill_gaps = skill_gaps or []

        logger.info(
            "TopicPrioritizationAgent.run started",
            extra={
                "agent_name": self.agent_name,
                "run_id": str(run_id),
                "input_summary": {
                    "trend_signals_count": len(trend_signals),
                    "job_demand_signals_count": len(job_demand_signals),
                    "skill_gaps_count": len(skill_gaps),
                },
            },
        )

        try:
            # אינדקסים לאחזור מהיר לפי שם נושא (lowercase)
            trend_index = self._build_trend_index(trend_signals)
            job_index = self._build_job_index(job_demand_signals)
            gap_index = self._build_gap_index(skill_gaps)

            # איחוד כל שמות הנושאים מכל המקורות
            all_topics: set[str] = set()
            all_topics.update(trend_index.keys())
            all_topics.update(job_index.keys())
            all_topics.update(gap_index.keys())

            ranked_topics: list[dict] = []
            for topic_lower in all_topics:
                trend_entry = trend_index.get(topic_lower)
                job_entry = job_index.get(topic_lower)
                gap_entry = gap_index.get(topic_lower)

                # ציונים עם ערכי ברירת מחדל
                trend_score = trend_entry.get("trend_score", 0.0) if trend_entry else 0.0
                job_market_score = job_entry.get("job_market_score", 0.0) if job_entry else 0.0
                # gap_score: 0.3 ניטרלי אם חסר — לא עונשים היעדר נתוני פער
                gap_score = gap_entry.get("gap_score", 0.3) if gap_entry else 0.3

                # ציון מורכב משוקלל
                composite_score = round(
                    (_TREND_WEIGHT * trend_score)
                    + (_JOB_MARKET_WEIGHT * job_market_score)
                    + (_GAP_WEIGHT * gap_score),
                    4,
                )

                # מקורות אות שתרמו
                signal_sources: list[str] = []
                if trend_entry:
                    signal_sources.append("trend_analysis")
                if job_entry:
                    signal_sources.append("job_demand")
                if gap_entry:
                    signal_sources.append("skill_gap")

                # ספירת ראיות כוללת
                evidence_count = (
                    (trend_entry.get("evidence_count", 1) if trend_entry else 0)
                    + (job_entry.get("job_count", 1) if job_entry else 0)
                )

                # שם הנושא המקורי (לפני lowercase)
                canonical_name = (
                    (trend_entry and trend_entry.get("topic_name"))
                    or (job_entry and (job_entry.get("topic_name") or job_entry.get("skill_name")))
                    or (gap_entry and gap_entry.get("topic_name"))
                    or topic_lower
                )

                # פעולה מומלצת לפי composite_score
                if composite_score > 0.7:
                    recommended_action = "build_now"
                elif composite_score > 0.5:
                    recommended_action = "build_soon"
                elif composite_score > 0.3:
                    recommended_action = "monitor"
                else:
                    recommended_action = "defer"

                ranked_topics.append(
                    {
                        "topic_name": canonical_name,
                        "composite_score": composite_score,
                        "trend_score": round(trend_score, 4),
                        "job_market_score": round(job_market_score, 4),
                        "gap_score": round(gap_score, 4),
                        "signal_sources": signal_sources,
                        "evidence_count": evidence_count,
                        "recommended_action": recommended_action,
                    }
                )

            # מיון יורד לפי composite_score, דטרמיניסטי: שם נושא כקריטריון משני
            ranked_topics.sort(
                key=lambda t: (t["composite_score"], t["topic_name"]),
                reverse=True,
            )

            # החזרת עד 20 נושאים מובילים
            top_topics = ranked_topics[:_MAX_TOPICS]

            duration_ms = int((time.monotonic() - start) * 1000)

            logger.info(
                "TopicPrioritizationAgent.run completed",
                extra={
                    "agent_name": self.agent_name,
                    "run_id": str(run_id),
                    "output_summary": {
                        "total_topics_scored": len(ranked_topics),
                        "returned_count": len(top_topics),
                        "top_topic": top_topics[0]["topic_name"] if top_topics else None,
                        "top_score": top_topics[0]["composite_score"] if top_topics else None,
                        "build_now_count": sum(
                            1 for t in top_topics if t["recommended_action"] == "build_now"
                        ),
                    },
                    "duration_ms": duration_ms,
                },
            )

            return self._make_result(
                run_id=run_id,
                success=True,
                output={"ranked_topics": top_topics},
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "TopicPrioritizationAgent.run failed",
                extra={"agent_name": self.agent_name, "run_id": str(run_id), "error": str(exc)},
                exc_info=True,
            )
            return self._make_result(
                run_id=run_id,
                success=False,
                output={"ranked_topics": []},
                error=str(exc),
                duration_ms=duration_ms,
            )

    # --- עזר: בניית אינדקסים ---

    def _build_trend_index(self, signals: list[dict]) -> dict[str, dict]:
        """בונה אינדקס trend_signals לפי topic_name בלוורקייס."""
        index: dict[str, dict] = {}
        for s in signals:
            name = s.get("topic_name", "")
            if name:
                index[name.lower().strip()] = s
        return index

    def _build_job_index(self, signals: list[dict]) -> dict[str, dict]:
        """בונה אינדקס job_demand_signals לפי skill_name או topic_name בלוורקייס."""
        index: dict[str, dict] = {}
        for s in signals:
            name = s.get("skill_name") or s.get("topic_name") or ""
            if name:
                index[name.lower().strip()] = s
        return index

    def _build_gap_index(self, gaps: list[dict]) -> dict[str, dict]:
        """בונה אינדקס skill_gaps לפי topic_name בלוורקייס."""
        index: dict[str, dict] = {}
        for g in gaps:
            name = g.get("topic_name", "")
            if name:
                index[name.lower().strip()] = g
        return index
