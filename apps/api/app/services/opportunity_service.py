"""
Opportunity Service — bridges API layer with DB and pipeline services.
Reads from persisted DB records when available, falls back to in-memory pipeline.
"""
from __future__ import annotations

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.opportunities import OpportunityBrief as OppModel, OpportunityEvidenceItem
from app.models.pipeline import PipelineRun


class OpportunityService:
    """Service for retrieving opportunities from DB or generating in-memory."""

    async def get_opportunities(
        self,
        country_code: str | None = None,
        language_code: str | None = None,
        classification: str | None = None,
        min_score: float = 0.35,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Get opportunities from DB with optional filters."""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(OppModel).where(OppModel.opportunity_score >= min_score)
                count_stmt = select(func.count()).select_from(OppModel).where(
                    OppModel.opportunity_score >= min_score
                )

                if country_code:
                    stmt = stmt.where(OppModel.country_code == country_code)
                    count_stmt = count_stmt.where(OppModel.country_code == country_code)
                if language_code:
                    stmt = stmt.where(OppModel.language_code == language_code)
                    count_stmt = count_stmt.where(OppModel.language_code == language_code)
                if classification:
                    stmt = stmt.where(OppModel.classification == classification)
                    count_stmt = count_stmt.where(OppModel.classification == classification)

                stmt = stmt.order_by(desc(OppModel.opportunity_score)).limit(limit).offset(offset)

                result = await session.execute(stmt)
                rows = result.scalars().all()

                count_result = await session.execute(count_stmt)
                total = count_result.scalar_one()

                # Load evidence for each opportunity
                opportunities = []
                for row in rows:
                    ev_stmt = select(OpportunityEvidenceItem).where(
                        OpportunityEvidenceItem.opportunity_id == row.id
                    )
                    ev_result = await session.execute(ev_stmt)
                    evidence_rows = ev_result.scalars().all()
                    opportunities.append(self._model_to_dict(row, evidence_rows))

                return opportunities, total

        except Exception:
            return await self._fallback_generate(country_code, language_code, classification, min_score, limit, offset)

    async def get_top_opportunities(
        self,
        country_code: str | None = None,
        language_code: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Get top N opportunities sorted by score."""
        opps, _ = await self.get_opportunities(
            country_code=country_code,
            language_code=language_code,
            min_score=0.0,
            limit=limit,
        )
        return opps

    async def get_pipeline_status(self) -> dict:
        """Get latest pipeline run status from DB."""
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(1)
                result = await session.execute(stmt)
                run = result.scalar_one_or_none()

                if run:
                    return {
                        "pipeline_run_id": str(run.id),
                        "status": run.status or "unknown",
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
                        "step_summaries": run.step_summaries or [],
                        "error_count": run.error_count or 0,
                        "last_successful_run": run.started_at.isoformat() if run.status == "completed" else None,
                    }
        except Exception:
            pass

        return {
            "pipeline_run_id": None,
            "status": "not_run",
            "started_at": None,
            "ended_at": None,
            "step_summaries": [],
            "error_count": 0,
            "last_successful_run": None,
        }

    def _model_to_dict(self, row: OppModel, evidence_rows: list) -> dict:
        """Convert DB model to API response dict."""
        return {
            "id": str(row.id) if row.id else None,
            "topic_id": str(row.topic_id) if row.topic_id else None,
            "canonical_topic_name": row.canonical_topic_name,
            "country_code": row.country_code,
            "region_code": row.region_code,
            "language_code": row.language_code,
            "audience_segment": row.audience_segment or "early_career",
            "recommended_format": row.recommended_format or "short_course",
            "opportunity_score": row.opportunity_score,
            "score_breakdown": {
                "demand_score": row.demand_score or 0.0,
                "growth_score": row.growth_score or 0.0,
                "job_market_score": row.job_market_score or 0.0,
                "trend_score": row.trend_score or 0.0,
                "content_gap_score": row.content_gap_score or 0.0,
                "localization_fit_score": row.localization_fit_score or 0.0,
                "teachability_score": row.teachability_score or 0.0,
                "strategic_fit_score": row.strategic_fit_score or 0.0,
            },
            "confidence_score": row.confidence_score or 0.0,
            "why_now_summary": row.why_now_summary or "",
            "evidence": [
                {
                    "source_type": ev.source_type,
                    "source_reference": ev.source_reference,
                    "evidence_summary": ev.evidence_summary,
                    "evidence_weight": ev.evidence_weight or 0.5,
                }
                for ev in evidence_rows
            ],
            "classification": row.classification or "watchlist",
            "lifecycle_state": row.lifecycle_state or "surfaced",
            "run_id": str(row.run_id) if row.run_id else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    async def _fallback_generate(self, country_code, language_code, classification, min_score, limit, offset):
        """Fallback: generate opportunities in-memory if DB unavailable."""
        from services.orchestration.pipeline import PipelineOrchestrator
        orch = PipelineOrchestrator(
            country_code=country_code or "IL",
            language_code=language_code or "he",
        )
        result = await orch.run()
        opps = result.get("opportunities", [])

        if classification:
            opps = [o for o in opps if o.get("classification") == classification]
        opps = [o for o in opps if o.get("opportunity_score", 0) >= min_score]

        total = len(opps)
        return opps[offset:offset + limit], total
