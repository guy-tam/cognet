"""
JobDemandAgent — OPERATIONAL (MVP)
מטרה: ניתוח נתוני מודעות משרה לכימות ביקוש מעסיקים לכישורים/נושאים לפי שוק.
קלטים: רשומות מודעות משרה מנורמלות, country_code, language_code
פלטים: {skill_demand: [{skill_name, demand_score, job_count, top_companies_count}], topic_demand: [...]}
לא בתחום: אינו מדרג הזדמנויות, אינו מעשיר כישורים (משתמש בתוויות כישורים כפי שמסופקות)
"""
import logging
import time
import uuid

from services.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class JobDemandAgent(BaseAgent):
    """
    מנתח נתוני מודעות משרה — מחשב ציוני ביקוש לכישורים ונושאים לפי שוק.
    """

    @property
    def agent_name(self) -> str:
        return "JobDemandAgent"

    @property
    def purpose(self) -> str:
        return (
            "Analyze job posting data to quantify employer skill and topic demand "
            "per market, producing normalized demand scores and job counts for use "
            "in downstream signal computation."
        )

    @property
    def non_goals(self) -> list[str]:
        return [
            "Does not rank or prioritize opportunities — produces raw demand signals only.",
            "Does not enrich or normalize skill labels — uses skill names as provided in job postings.",
            "Does not fetch job posting data — operates on pre-normalized records only.",
        ]

    async def run(
        self,
        run_id: uuid.UUID,
        job_records: list[dict],
        country_code: str,
        language_code: str,
        **kwargs,
    ) -> AgentResult:
        """
        מנתח רשומות מודעות משרה מנורמלות ומחשב ציוני ביקוש לכישורים ונושאים.

        Args:
            run_id: מזהה ריצת ה-pipeline.
            job_records: רשומות מודעות משרה — כל אחת עם skills ו/או topics ב-payload.
            country_code: קוד המדינה של השוק המנותח.
            language_code: קוד השפה של השוק המנותח.

        Returns:
            AgentResult עם output: {skill_demand: [...], topic_demand: [...]}
        """
        start = time.monotonic()

        logger.info(
            "JobDemandAgent.run started",
            extra={
                "agent_name": self.agent_name,
                "run_id": str(run_id),
                "input_summary": {
                    "record_count": len(job_records),
                    "country_code": country_code,
                    "language_code": language_code,
                },
            },
        )

        try:
            total_postings = len(job_records)

            # ספירת אזכורי כישורים
            skill_counts: dict[str, int] = {}
            # ספירת חברות לפי כישור (לחישוב top_companies_count)
            skill_companies: dict[str, set] = {}
            # ספירת אזכורי נושאים (מכותרות מנורמלות)
            topic_counts: dict[str, int] = {}
            topic_companies: dict[str, set] = {}

            for record in job_records:
                # חילוץ payload — תמיכה ב-dict גולמי וב-NormalizedRecord כ-dict
                payload = record.get("payload", record)
                company = payload.get("company", "unknown")

                # כישורים
                skills = payload.get("skills", [])
                if isinstance(skills, list):
                    for skill in skills:
                        skill_lower = str(skill).lower().strip()
                        if skill_lower:
                            skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1
                            if skill_lower not in skill_companies:
                                skill_companies[skill_lower] = set()
                            skill_companies[skill_lower].add(company)

                # נושאים מכותרת המשרה כ-proxy פשוט
                title = (
                    payload.get("title")
                    or record.get("normalized_title")
                    or ""
                )
                if title:
                    topic_key = title.lower().strip()
                    topic_counts[topic_key] = topic_counts.get(topic_key, 0) + 1
                    if topic_key not in topic_companies:
                        topic_companies[topic_key] = set()
                    topic_companies[topic_key].add(company)

            # חישוב skill_demand
            skill_demand: list[dict] = []
            for skill_name, count in skill_counts.items():
                demand_score = count / max(total_postings, 1)
                # job_market_score: הגברת אות ברור — min(1.0, demand_score * 2.0)
                job_market_score = round(min(1.0, demand_score * 2.0), 4)
                skill_demand.append(
                    {
                        "skill_name": skill_name,
                        "demand_score": round(demand_score, 4),
                        "job_market_score": job_market_score,
                        "job_count": count,
                        "top_companies_count": len(skill_companies.get(skill_name, set())),
                    }
                )

            # מיון יורד לפי demand_score
            skill_demand.sort(key=lambda x: x["demand_score"], reverse=True)

            # חישוב topic_demand
            topic_demand: list[dict] = []
            for topic_name, count in topic_counts.items():
                demand_score = count / max(total_postings, 1)
                job_market_score = round(min(1.0, demand_score * 2.0), 4)
                topic_demand.append(
                    {
                        "topic_name": topic_name,
                        "demand_score": round(demand_score, 4),
                        "job_market_score": job_market_score,
                        "job_count": count,
                        "top_companies_count": len(topic_companies.get(topic_name, set())),
                    }
                )

            topic_demand.sort(key=lambda x: x["demand_score"], reverse=True)

            duration_ms = int((time.monotonic() - start) * 1000)

            logger.info(
                "JobDemandAgent.run completed",
                extra={
                    "agent_name": self.agent_name,
                    "run_id": str(run_id),
                    "output_summary": {
                        "skills_found": len(skill_demand),
                        "topics_found": len(topic_demand),
                        "total_postings": total_postings,
                    },
                    "duration_ms": duration_ms,
                },
            )

            return self._make_result(
                run_id=run_id,
                success=True,
                output={
                    "skill_demand": skill_demand,
                    "topic_demand": topic_demand,
                    "total_postings_analyzed": total_postings,
                },
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "JobDemandAgent.run failed",
                extra={"agent_name": self.agent_name, "run_id": str(run_id), "error": str(exc)},
                exc_info=True,
            )
            return self._make_result(
                run_id=run_id,
                success=False,
                output={"skill_demand": [], "topic_demand": [], "total_postings_analyzed": 0},
                error=str(exc),
                duration_ms=duration_ms,
            )
