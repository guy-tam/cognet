"""
Opportunity API response schemas — COGNET LDI Engine.
Aligned with shared/contracts/signal_vector.ScoreBreakdown and shared/contracts/opportunity.OpportunityBrief.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ScoreBreakdownResponse(BaseModel):
    """פירוט ציוני ההזדמנות — 8 ממדים, כל אחד בין 0 ל-1."""

    demand_score: float = Field(default=0.0, ge=0.0, le=1.0)
    growth_score: float = Field(default=0.0, ge=0.0, le=1.0)
    job_market_score: float = Field(default=0.0, ge=0.0, le=1.0)
    trend_score: float = Field(default=0.0, ge=0.0, le=1.0)
    content_gap_score: float = Field(default=0.0, ge=0.0, le=1.0)
    localization_fit_score: float = Field(default=0.0, ge=0.0, le=1.0)
    teachability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    strategic_fit_score: float = Field(default=0.0, ge=0.0, le=1.0)


class EvidenceItemResponse(BaseModel):
    """פריט ראיה בודד התומך בהזדמנות."""

    source_type: str
    source_reference: str
    evidence_summary: str
    evidence_weight: float = Field(default=0.5, ge=0.0, le=1.0)


class OpportunityResponse(BaseModel):
    """תגובת הזדמנות למידה מלאה — aligned with OpportunityBrief contract."""

    id: UUID | None = None
    topic_id: UUID | None = None
    canonical_topic_name: str
    country_code: str
    region_code: str | None = None
    language_code: str
    audience_segment: str = "early_career"
    recommended_format: str = "short_course"
    opportunity_score: float = Field(ge=0.0, le=1.0)
    score_breakdown: ScoreBreakdownResponse = Field(default_factory=ScoreBreakdownResponse)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    why_now_summary: str = ""
    evidence: list[EvidenceItemResponse] = Field(default_factory=list)
    classification: str = "watchlist"
    lifecycle_state: str = "surfaced"
    run_id: str | None = None
    created_at: datetime | None = None


class OpportunityListResponse(BaseModel):
    """תגובת רשימת הזדמנויות עם מטא-דאטה על הפילטרים שהופעלו."""

    opportunities: list[OpportunityResponse] = Field(default_factory=list)
    total: int = 0
    filters_applied: dict = Field(default_factory=dict)
