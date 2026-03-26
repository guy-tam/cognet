"""
Initialize the database — create all tables and seed taxonomy data.
Run this once to set up a local SQLite database for development.

Usage: cd apps/api && python init_db.py
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone

# Ensure imports work
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


async def init_database():
    from app.db.session import engine
    from app.db.base import Base
    # Import all models so they register with Base.metadata
    import app.models  # noqa: F401

    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ All tables created")

    # Seed taxonomy data
    from app.db.session import AsyncSessionLocal
    from app.models.taxonomy import Skill, Topic, Country, Language, Industry, Role
    from services.taxonomy.seed import SEED_SKILLS, SEED_TOPICS, SEED_COUNTRIES, SEED_LANGUAGES

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy import select, func
        count = await session.execute(select(func.count()).select_from(Skill))
        if count.scalar_one() > 0:
            print("→ Database already seeded, skipping")
            return

        print("Seeding taxonomy data...")

        # Skills
        for s in SEED_SKILLS:
            session.add(Skill(id=uuid.uuid4(), name=s["name"], category=s.get("category")))
        print(f"  → {len(SEED_SKILLS)} skills")

        # Topics
        for t in SEED_TOPICS:
            session.add(Topic(id=uuid.uuid4(), name=t["name"]))
        print(f"  → {len(SEED_TOPICS)} topics")

        # Countries
        for c in SEED_COUNTRIES:
            session.add(Country(id=uuid.uuid4(), code=c["code"], name=c["name"]))
        print(f"  → {len(SEED_COUNTRIES)} countries")

        # Languages
        for lang in SEED_LANGUAGES:
            session.add(Language(
                id=uuid.uuid4(), code=lang["code"],
                name=lang["name"], is_rtl=lang.get("is_rtl", False),
            ))
        print(f"  → {len(SEED_LANGUAGES)} languages")

        # Seed some industries
        industries = ["Technology", "Healthcare", "Finance", "Education", "Manufacturing"]
        for name in industries:
            session.add(Industry(id=uuid.uuid4(), name=name))
        print(f"  → {len(industries)} industries")

        # Seed some roles
        roles = [
            ("Software Engineer", "Technology"),
            ("Data Scientist", "Technology"),
            ("Product Manager", "Technology"),
            ("DevOps Engineer", "Technology"),
            ("Cybersecurity Analyst", "Technology"),
        ]
        for name, hint in roles:
            session.add(Role(id=uuid.uuid4(), name=name, industry_hint=hint))
        print(f"  → {len(roles)} roles")

        await session.commit()
        print("✓ Taxonomy data seeded")

    # Run the pipeline to populate opportunities
    print("\nRunning initial pipeline...")
    from services.orchestration.pipeline import PipelineOrchestrator
    orch = PipelineOrchestrator(country_code="IL", language_code="he")
    result = await orch.run()
    print(f"  → {result['opportunities_count']} opportunities generated")

    # Persist opportunities to DB
    if result['opportunities']:
        from app.models.opportunities import OpportunityBrief as OppModel
        from app.models.opportunities import OpportunityEvidenceItem
        from app.models.pipeline import PipelineRun

        async with AsyncSessionLocal() as session:
            # Create pipeline run record
            pipeline_run = PipelineRun(
                id=uuid.UUID(result['run_id']),
                started_at=datetime.now(timezone.utc),
                ended_at=datetime.now(timezone.utc),
                status="completed",
                step_summaries=result.get('steps', []),
                error_count=len(result.get('errors', [])),
            )
            session.add(pipeline_run)

            # Persist each opportunity
            for opp_data in result['opportunities']:
                opp = OppModel(
                    id=uuid.uuid4(),
                    canonical_topic_name=opp_data['canonical_topic_name'],
                    country_code=opp_data['country_code'],
                    region_code=opp_data.get('region_code'),
                    language_code=opp_data['language_code'],
                    audience_segment=opp_data.get('audience_segment', 'early_career'),
                    recommended_format=opp_data.get('recommended_format', 'short_course'),
                    opportunity_score=opp_data['opportunity_score'],
                    demand_score=opp_data['score_breakdown']['demand_score'],
                    growth_score=opp_data['score_breakdown']['growth_score'],
                    job_market_score=opp_data['score_breakdown']['job_market_score'],
                    trend_score=opp_data['score_breakdown']['trend_score'],
                    content_gap_score=opp_data['score_breakdown']['content_gap_score'],
                    localization_fit_score=opp_data['score_breakdown']['localization_fit_score'],
                    teachability_score=opp_data['score_breakdown']['teachability_score'],
                    strategic_fit_score=opp_data['score_breakdown']['strategic_fit_score'],
                    why_now_summary=opp_data.get('why_now_summary', ''),
                    confidence_score=opp_data['confidence_score'],
                    classification=opp_data['classification'],
                    lifecycle_state=opp_data.get('lifecycle_state', 'surfaced'),
                    run_id=uuid.UUID(result['run_id']),
                )
                session.add(opp)

                # Persist evidence items
                for ev in opp_data.get('evidence', []):
                    session.add(OpportunityEvidenceItem(
                        id=uuid.uuid4(),
                        opportunity_id=opp.id,
                        source_type=ev['source_type'],
                        source_reference=ev['source_reference'],
                        evidence_summary=ev['evidence_summary'],
                        evidence_weight=ev.get('evidence_weight', 0.5),
                    ))

            await session.commit()
            print(f"  → {len(result['opportunities'])} opportunities persisted to DB")

    print("\n✓ Database initialization complete!")
    print(f"  Database file: cognet_ldi.db")
    print(f"  Start API with: cd apps/api && uvicorn main:app --reload")


if __name__ == "__main__":
    asyncio.run(init_database())
