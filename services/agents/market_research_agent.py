"""
MarketResearchAgent — SCAFFOLD (לא פעיל ב-MVP)
מטרה: מחקר הקשר שוק רחב למדינה/אזור/סקטור נתון.
סטטוס: Scaffold — לא מחובר ל-pipeline ב-MVP.
"""
import uuid

from services.agents.base_agent import AgentResult, BaseAgent


class MarketResearchAgent(BaseAgent):
    """
    SCAFFOLD בלבד — אינו פעיל ב-MVP.
    מיועד למחקר הקשר שוק רחב הכולל אינדיקטורים כלכליים ודוחות ענף.
    """

    @property
    def agent_name(self) -> str:
        return "MarketResearchAgent"

    @property
    def purpose(self) -> str:
        return (
            "Research broader market context including economic indicators, "
            "industry reports, and regional learning culture signals."
        )

    @property
    def non_goals(self) -> list[str]:
        return [
            "Does not compute opportunity scores.",
            "Does not replace trend or job signal analysis.",
            "Not operational in MVP — scaffold only.",
        ]

    async def run(self, run_id: uuid.UUID, **inputs) -> AgentResult:
        # SCAFFOLD: לא פעיל ב-MVP
        return self._make_result(
            run_id=run_id,
            success=False,
            output={},
            error="MarketResearchAgent is not operational in MVP",
        )
