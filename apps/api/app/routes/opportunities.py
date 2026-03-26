"""
Opportunities API routes — COGNET LDI Engine.
Exposes ranked learning opportunities with filtering and pagination.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.responses import Response
from app.schemas.opportunities import OpportunityResponse, OpportunityListResponse
from app.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/v1/opportunities", tags=["opportunities"])

# Shared service instance (MVP: in-memory, post-MVP: inject via dependency)
_service = OpportunityService()


@router.get("/", response_model=OpportunityListResponse)
async def list_opportunities(
    country_code: str | None = Query(None, description="ISO 3166-1 alpha-2 country code"),
    language_code: str | None = Query(None, description="ISO 639-1 language code"),
    classification: str | None = Query(None, description="Classification filter"),
    min_score: float = Query(0.35, ge=0.0, le=1.0, description="Minimum opportunity score"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> OpportunityListResponse:
    """List opportunities with optional filters and pagination."""
    opportunities, total = await _service.get_opportunities(
        country_code=country_code,
        language_code=language_code,
        classification=classification,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )
    return OpportunityListResponse(
        opportunities=opportunities,
        total=total,
        filters_applied={
            k: v for k, v in {
                "country_code": country_code,
                "language_code": language_code,
                "classification": classification,
                "min_score": str(min_score),
            }.items() if v is not None
        },
    )


@router.get("/export")
async def export_opportunities(
    country_code: str | None = Query(None),
    language_code: str | None = Query(None),
    format: str = Query("json", description="Export format: json or csv"),
) -> Response:
    """ייצוא הזדמנויות כ-JSON או CSV לצריכה חיצונית."""
    import csv
    import io

    opportunities, total = await _service.get_opportunities(
        country_code=country_code,
        language_code=language_code,
        min_score=0.0,
        limit=1000,
    )

    if format == "csv":
        output = io.StringIO()
        if opportunities:
            writer = csv.DictWriter(output, fieldnames=[
                "canonical_topic_name", "country_code", "language_code",
                "opportunity_score", "confidence_score", "classification",
                "recommended_format", "audience_segment", "why_now_summary",
            ])
            writer.writeheader()
            for opp in opportunities:
                writer.writerow({
                    "canonical_topic_name": opp.get("canonical_topic_name", ""),
                    "country_code": opp.get("country_code", ""),
                    "language_code": opp.get("language_code", ""),
                    "opportunity_score": opp.get("opportunity_score", 0),
                    "confidence_score": opp.get("confidence_score", 0),
                    "classification": opp.get("classification", ""),
                    "recommended_format": opp.get("recommended_format", ""),
                    "audience_segment": opp.get("audience_segment", ""),
                    "why_now_summary": opp.get("why_now_summary", ""),
                })

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cognet_opportunities.csv"},
        )

    # ברירת מחדל: ייצוא JSON
    return JSONResponse(content={"opportunities": opportunities, "total": total})


@router.get("/top", response_model=list[OpportunityResponse])
async def top_opportunities(
    country_code: str | None = Query(None),
    language_code: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict]:
    """Get top-ranked opportunities."""
    return await _service.get_top_opportunities(
        country_code=country_code,
        language_code=language_code,
        limit=limit,
    )


@router.get("/by-market", response_model=OpportunityListResponse)
async def opportunities_by_market(
    country_code: str = Query(..., description="Required market country code"),
    language_code: str = Query(..., description="Required market language code"),
    classification: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> OpportunityListResponse:
    """Get opportunities for a specific market."""
    opportunities, total = await _service.get_opportunities(
        country_code=country_code,
        language_code=language_code,
        classification=classification,
        limit=limit,
    )
    return OpportunityListResponse(
        opportunities=opportunities,
        total=total,
        filters_applied={"country_code": country_code, "language_code": language_code},
    )


@router.get("/{index}")
async def get_opportunity_by_index(index: int) -> dict:
    """שליפת הזדמנות בודדת לפי אינדקס ברשימה המדורגת (MVP)."""
    opportunities, _ = await _service.get_opportunities(min_score=0.0, limit=1000)
    if 0 <= index < len(opportunities):
        return opportunities[index]
    raise HTTPException(status_code=404, detail="Opportunity not found")
