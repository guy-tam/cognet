"""
TrendAnalysisAgent — OPERATIONAL (MVP)
מטרה: ניתוח אותות מגמה/חיפוש עבור שוק נתון לזיהוי נושאים עולים.
קלטים: רשומות מגמה מנורמלות, country_code, language_code, time_window_days
פלטים: רשימה של {topic_name, trend_score, growth_score, evidence_count}
לא בתחום: אינו מחשב ציון הזדמנות סופי, אינו מנהל taxonomy
"""
import logging
import time
import uuid

from services.agents.base_agent import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class TrendAnalysisAgent(BaseAgent):
    """
    מנתח אותות מגמה וחיפוש לפי שוק — מחזיר נושאים עולים עם ציוני מגמה וצמיחה.
    """

    @property
    def agent_name(self) -> str:
        return "TrendAnalysisAgent"

    @property
    def purpose(self) -> str:
        return (
            "Analyze trend and search signals for a given market to identify "
            "rising topics, quantify trend momentum, and surface evidence counts "
            "for downstream signal computation."
        )

    @property
    def non_goals(self) -> list[str]:
        return [
            "Does not compute final opportunity scores — that is the RankingEngine's responsibility.",
            "Does not manage or update the topic taxonomy — uses provided keyword/topic labels as-is.",
            "Does not fetch raw data — operates on pre-normalized trend records only.",
        ]

    async def run(
        self,
        run_id: uuid.UUID,
        trend_records: list[dict],
        country_code: str,
        language_code: str,
        **kwargs,
    ) -> AgentResult:
        """
        מנתח רשומות מגמה מנורמלות ומחשב ציוני מגמה וצמיחה לכל נושא.

        Args:
            run_id: מזהה ריצת ה-pipeline.
            trend_records: רשומות מגמה מנורמלות — כל אחת עם keyword, search_volume_index, trend_direction.
            country_code: קוד המדינה של השוק המנותח.
            language_code: קוד השפה של השוק המנותח.

        Returns:
            AgentResult עם output: {topic_signals: [{topic_name, trend_score, growth_score, evidence_count}]}
        """
        start = time.monotonic()

        logger.info(
            "TrendAnalysisAgent.run started",
            extra={
                "agent_name": self.agent_name,
                "run_id": str(run_id),
                "input_summary": {
                    "record_count": len(trend_records),
                    "country_code": country_code,
                    "language_code": language_code,
                },
            },
        )

        try:
            # קיבוץ רשומות לפי keyword/topic
            topic_groups: dict[str, list[dict]] = {}
            for record in trend_records:
                # תמיכה גם ברשומות גולמיות וגם ב-NormalizedRecord כ-dict
                topic_name = (
                    record.get("keyword")
                    or record.get("normalized_title")
                    or record.get("name")
                    or "unknown"
                )
                topic_name = topic_name.lower().strip()
                if topic_name not in topic_groups:
                    topic_groups[topic_name] = []
                topic_groups[topic_name].append(record)

            # חישוב מדדים לכל נושא
            topic_raw: list[dict] = []
            for topic_name, records in topic_groups.items():
                mention_count = len(records)
                # ממוצע search_volume_index (אם קיים)
                volumes = [
                    r.get("search_volume_index", 0)
                    for r in records
                    if r.get("search_volume_index") is not None
                ]
                avg_search_volume = sum(volumes) / len(volumes) if volumes else 0.0

                # trend_direction: אם רוב הרשומות "rising" → rising, אחרת לפי רוב
                directions = [r.get("trend_direction", "stable") for r in records]
                direction_counts: dict[str, int] = {}
                for d in directions:
                    direction_counts[d] = direction_counts.get(d, 0) + 1
                trend_direction = max(direction_counts, key=direction_counts.get)

                topic_raw.append(
                    {
                        "topic_name": topic_name,
                        "mention_count": mention_count,
                        "avg_search_volume": avg_search_volume,
                        "trend_direction": trend_direction,
                    }
                )

            # נרמול trend_score: mention_count / max_mention_count בקבוצה
            max_mentions = max((t["mention_count"] for t in topic_raw), default=1)

            topic_signals: list[dict] = []
            for t in topic_raw:
                # trend_score = mention_count מנורמל ל-0-1 לפי המקסימום בקבוצה
                trend_score = round(t["mention_count"] / max(max_mentions, 1), 4)

                # growth_score לפי כיוון המגמה
                direction = t["trend_direction"]
                if direction == "rising":
                    growth_score = 0.8
                elif direction == "stable":
                    growth_score = 0.5
                else:
                    # "declining" או כל ערך אחר
                    growth_score = 0.2

                topic_signals.append(
                    {
                        "topic_name": t["topic_name"],
                        "trend_score": trend_score,
                        "growth_score": growth_score,
                        "evidence_count": t["mention_count"],
                        "avg_search_volume": round(t["avg_search_volume"], 2),
                        "trend_direction": t["trend_direction"],
                    }
                )

            # מיון יורד לפי trend_score
            topic_signals.sort(key=lambda x: x["trend_score"], reverse=True)

            duration_ms = int((time.monotonic() - start) * 1000)

            logger.info(
                "TrendAnalysisAgent.run completed",
                extra={
                    "agent_name": self.agent_name,
                    "run_id": str(run_id),
                    "output_summary": {
                        "topics_found": len(topic_signals),
                        "top_topic": topic_signals[0]["topic_name"] if topic_signals else None,
                    },
                    "duration_ms": duration_ms,
                },
            )

            return self._make_result(
                run_id=run_id,
                success=True,
                output={"topic_signals": topic_signals},
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "TrendAnalysisAgent.run failed",
                extra={"agent_name": self.agent_name, "run_id": str(run_id), "error": str(exc)},
                exc_info=True,
            )
            return self._make_result(
                run_id=run_id,
                success=False,
                output={"topic_signals": []},
                error=str(exc),
                duration_ms=duration_ms,
            )
