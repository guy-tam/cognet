"""
SkillGapAgent — OPERATIONAL (MVP)
מטרה: השוואת כישורים/נושאים מבוקשים מול היצע למידה פנימי לזיהוי פערים.
קלטים: demanded_skills (רשימה), internal_supply_topics (רשימה), coverage_threshold (ברירת מחדל 0.3)
פלטים: {gaps: [{topic_name, demand_score, supply_coverage, gap_score, priority}]}
לא בתחום: אינו קולט נתוני היצע חדשים, אינו יוצר קורסים
"""
import logging
import time
import uuid

from services.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class SkillGapAgent(BaseAgent):
    """
    מחשב פערים בין כישורים מבוקשים להיצע למידה פנימי קיים.
    """

    @property
    def agent_name(self) -> str:
        return "SkillGapAgent"

    @property
    def purpose(self) -> str:
        return (
            "Compare demanded skills and topics against internal learning supply "
            "to identify content gaps, quantify gap severity, and prioritize "
            "which gaps are most critical to address."
        )

    @property
    def non_goals(self) -> list[str]:
        return [
            "Does not ingest or update internal supply data — operates on provided supply lists only.",
            "Does not create or recommend specific course content — identifies gaps only.",
            "Does not handle enrichment or taxonomy normalization of supply topics.",
        ]

    async def run(
        self,
        run_id: uuid.UUID,
        demanded_skills: list[dict],
        internal_supply_topics: list[str],
        coverage_threshold: float = 0.3,
        **kwargs,
    ) -> AgentResult:
        """
        מחשב פערי כיסוי בין כישורים מבוקשים להיצע פנימי.

        Args:
            run_id: מזהה ריצת ה-pipeline.
            demanded_skills: רשימת דיקטים עם {skill_name/topic_name, demand_score}.
            internal_supply_topics: רשימת שמות נושאים/כישורים קיימים בהיצע הפנימי.
            coverage_threshold: סף כיסוי מינימלי לסיווג "כיסוי נמוך" (ברירת מחדל: 0.3).

        Returns:
            AgentResult עם output: {gaps: [{topic_name, demand_score, supply_coverage, gap_score, priority}]}
        """
        start = time.monotonic()

        logger.info(
            "SkillGapAgent.run started",
            extra={
                "agent_name": self.agent_name,
                "run_id": str(run_id),
                "input_summary": {
                    "demanded_count": len(demanded_skills),
                    "supply_topics_count": len(internal_supply_topics),
                    "coverage_threshold": coverage_threshold,
                },
            },
        )

        try:
            # נרמול רשימת ההיצע לאותיות קטנות לצורך השוואה
            supply_lower = {t.lower().strip() for t in internal_supply_topics if t}

            gaps: list[dict] = []
            for item in demanded_skills:
                # תמיכה בשדה skill_name או topic_name
                topic_name = (
                    item.get("skill_name")
                    or item.get("topic_name")
                    or "unknown"
                )
                demand_score = float(item.get("demand_score", 0.0))

                # השוואה פשוטה לפי lowercase — fuzzy match בסיסי
                topic_lower = topic_name.lower().strip()

                # חישוב supply_coverage לפי רמת התאמה
                supply_coverage = self._compute_supply_coverage(
                    topic_lower, supply_lower, coverage_threshold
                )

                # gap_score = max(0, demand_score - supply_coverage)
                gap_score = round(max(0.0, demand_score - supply_coverage), 4)

                # עדיפות לפי gap_score
                if gap_score > 0.6:
                    priority = "high"
                elif gap_score > 0.3:
                    priority = "medium"
                else:
                    priority = "low"

                gaps.append(
                    {
                        "topic_name": topic_name,
                        "demand_score": round(demand_score, 4),
                        "supply_coverage": round(supply_coverage, 4),
                        "gap_score": gap_score,
                        "priority": priority,
                    }
                )

            # מיון יורד לפי gap_score
            gaps.sort(key=lambda x: x["gap_score"], reverse=True)

            duration_ms = int((time.monotonic() - start) * 1000)

            logger.info(
                "SkillGapAgent.run completed",
                extra={
                    "agent_name": self.agent_name,
                    "run_id": str(run_id),
                    "output_summary": {
                        "gaps_found": len(gaps),
                        "high_priority_count": sum(1 for g in gaps if g["priority"] == "high"),
                        "medium_priority_count": sum(1 for g in gaps if g["priority"] == "medium"),
                    },
                    "duration_ms": duration_ms,
                },
            )

            return self._make_result(
                run_id=run_id,
                success=True,
                output={"gaps": gaps},
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "SkillGapAgent.run failed",
                extra={"agent_name": self.agent_name, "run_id": str(run_id), "error": str(exc)},
                exc_info=True,
            )
            return self._make_result(
                run_id=run_id,
                success=False,
                output={"gaps": []},
                error=str(exc),
                duration_ms=duration_ms,
            )

    def _compute_supply_coverage(
        self,
        topic_lower: str,
        supply_lower: set[str],
        coverage_threshold: float,
    ) -> float:
        """
        מחשב כיסוי היצע עבור נושא נתון.

        לוגיקת התאמה:
        - התאמה מלאה: supply_coverage = 1.0
        - התאמה חלקית (substring): supply_coverage = 0.7 (כיסוי בינוני)
        - מילה משותפת: supply_coverage = 0.3 (כיסוי נמוך)
        - ללא התאמה: supply_coverage = 0.0

        Args:
            topic_lower: שם הנושא המבוקש, אותיות קטנות.
            supply_lower: קבוצת שמות ההיצע, אותיות קטנות.
            coverage_threshold: סף לכיסוי נמוך.

        Returns:
            float בטווח [0.0, 1.0].
        """
        # התאמה מדויקת
        if topic_lower in supply_lower:
            return 1.0

        # התאמה חלקית — הנושא מכיל מחרוזת מההיצע או להפך
        for supply_topic in supply_lower:
            if supply_topic in topic_lower or topic_lower in supply_topic:
                return 0.7

        # התאמת מילה — לפחות מילה משותפת אחת
        topic_words = set(topic_lower.split())
        for supply_topic in supply_lower:
            supply_words = set(supply_topic.split())
            if topic_words & supply_words:
                return coverage_threshold  # ברירת מחדל: 0.3

        # ללא כיסוי
        return 0.0
