"""
RegionCultureFitAgent — SCAFFOLD (לא פעיל ב-MVP)
מטרה: הערכת התאמת נושאי למידה לתרבות הלמידה האזורית ולהעדפות מקומיות.
סטטוס: Scaffold — לא מחובר ל-pipeline ב-MVP.
"""
import uuid

from services.agents.base_agent import AgentResult, BaseAgent


class RegionCultureFitAgent(BaseAgent):
    """
    SCAFFOLD בלבד — אינו פעיל ב-MVP.
    מיועד להערכת התאמה תרבותית-אזורית של תכנים ללמידה.
    """

    @property
    def agent_name(self) -> str:
        return "RegionCultureFitAgent"

    @property
    def purpose(self) -> str:
        return (
            "Evaluate how well a topic or learning format fits the regional learning culture, "
            "language preferences, and educational norms of a target market."
        )

    @property
    def non_goals(self) -> list[str]:
        return [
            "Does not compute opportunity scores or rankings.",
            "Does not perform translation or localization of content.",
            "Not operational in MVP — scaffold only.",
        ]

    async def run(self, run_id: uuid.UUID, **inputs) -> AgentResult:
        # SCAFFOLD: לא פעיל ב-MVP
        return self._make_result(
            run_id=run_id,
            success=False,
            output={},
            error="RegionCultureFitAgent is not operational in MVP",
        )
