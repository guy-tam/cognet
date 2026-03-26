"""
LearningOpportunityAgent — SCAFFOLD (לא פעיל ב-MVP)
מטרה: הרחבת הזדמנויות למידה מזוהות בהצעות תוכן ספציפיות ופורמטים מומלצים.
סטטוס: Scaffold — לא מחובר ל-pipeline ב-MVP.
"""
import uuid

from services.agents.base_agent import AgentResult, BaseAgent


class LearningOpportunityAgent(BaseAgent):
    """
    SCAFFOLD בלבד — אינו פעיל ב-MVP.
    מיועד להרחבת הזדמנויות למידה לפרטי תוכן ופורמטים ספציפיים.
    """

    @property
    def agent_name(self) -> str:
        return "LearningOpportunityAgent"

    @property
    def purpose(self) -> str:
        return (
            "Expand identified learning opportunities into specific content proposals, "
            "suggested learning formats, and preliminary scope definitions."
        )

    @property
    def non_goals(self) -> list[str]:
        return [
            "Does not generate final OpportunityBrief objects — that is the OpportunityGenerator's responsibility.",
            "Does not perform market signal analysis or gap computation.",
            "Not operational in MVP — scaffold only.",
        ]

    async def run(self, run_id: uuid.UUID, **inputs) -> AgentResult:
        # SCAFFOLD: לא פעיל ב-MVP
        return self._make_result(
            run_id=run_id,
            success=False,
            output={},
            error="LearningOpportunityAgent is not operational in MVP",
        )
