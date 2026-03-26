"""
ConsistencyValidationAgent — SCAFFOLD (לא פעיל ב-MVP)
מטרה: אימות עקביות בין פלטי הסוכנים השונים לפני הגעה לשלב הדירוג.
סטטוס: Scaffold — לא מחובר ל-pipeline ב-MVP.
"""
import uuid

from services.agents.base_agent import AgentResult, BaseAgent


class ConsistencyValidationAgent(BaseAgent):
    """
    SCAFFOLD בלבד — אינו פעיל ב-MVP.
    מיועד לאימות עקביות צולבת בין פלטי סוכנים מרובים.
    """

    @property
    def agent_name(self) -> str:
        return "ConsistencyValidationAgent"

    @property
    def purpose(self) -> str:
        return (
            "Validate consistency across outputs from multiple agents — detect contradictions, "
            "flag outlier scores, and surface data quality issues before signals reach the RankingEngine."
        )

    @property
    def non_goals(self) -> list[str]:
        return [
            "Does not modify or correct agent outputs — flags issues only.",
            "Does not replace schema validation on individual agent outputs.",
            "Not operational in MVP — scaffold only.",
        ]

    async def run(self, run_id: uuid.UUID, **inputs) -> AgentResult:
        # SCAFFOLD: לא פעיל ב-MVP
        return self._make_result(
            run_id=run_id,
            success=False,
            output={},
            error="ConsistencyValidationAgent is not operational in MVP",
        )
