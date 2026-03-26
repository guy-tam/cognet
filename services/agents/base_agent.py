"""
Base Agent — ממשק מופשט לכל סוכני מנוע COGNET LDI.
סוכנים הם רכיבים מתמחים ומוגבלים, לא נחילים אוטונומיים.
לכל סוכן יש מטרה מוגדרת, קלטים ופלטים מוקלדים, ויעדים שאינם בתחומו.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import uuid
import logging


@dataclass
class AgentResult:
    agent_name: str
    run_id: uuid.UUID
    success: bool
    output: dict  # קשור לסכמה — כל סוכן מגדיר את מבנה הפלט שלו
    error: str | None = None
    duration_ms: int = 0


class BaseAgent(ABC):
    """
    כל הסוכנים חייבים:
    - להגדיר בבירור: מטרה, non_goals, קלטים, פלטים
    - להיות קשורים לסכמה בפלט
    - לטפל בכשלים עם התנהגות fallback מפורשת
    - לרשום לוג של כל הפעלה עם: agent_name, run_id, input_summary, output_summary, duration_ms
    """

    @property
    @abstractmethod
    def agent_name(self) -> str: ...

    @property
    @abstractmethod
    def purpose(self) -> str: ...

    @property
    @abstractmethod
    def non_goals(self) -> list[str]: ...

    @abstractmethod
    async def run(self, run_id: uuid.UUID, **inputs) -> AgentResult: ...

    def _make_result(
        self,
        run_id: uuid.UUID,
        success: bool,
        output: dict,
        error: str | None = None,
        duration_ms: int = 0,
    ) -> AgentResult:
        """בונה AgentResult תקני עם שם הסוכן מאוכלס אוטומטית."""
        return AgentResult(
            agent_name=self.agent_name,
            run_id=run_id,
            success=success,
            output=output,
            error=error,
            duration_ms=duration_ms,
        )
