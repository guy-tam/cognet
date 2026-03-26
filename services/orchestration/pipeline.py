"""
Pipeline Orchestrator — מתאם את pipeline המודיעין המלא של COGNET LDI Engine.
MVP: ביצוע סדרתי פשוט, לא event-driven.
שלבים: ingest → normalize → compute signals → rank → generate opportunities
"""
import logging
import time
import uuid

from services.agents.job_demand_agent import JobDemandAgent
from services.agents.skill_gap_agent import SkillGapAgent
from services.agents.topic_prioritization_agent import TopicPrioritizationAgent
from services.agents.trend_analysis_agent import TrendAnalysisAgent
from services.ingestion.connectors.internal_supply import InternalSupplyConnector
from services.ingestion.connectors.job_postings import JobPostingsConnector
from services.ingestion.connectors.trend_signals import TrendSignalsConnector
from services.normalization.normalizer import Normalizer
from services.opportunities.generator import OpportunityGenerator
from services.ranking.engine import RankingEngine
from services.signals.computer import SignalComputer

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    מתאם את ריצת ה-pipeline המלאה מ-ingest ועד הזדמנויות.

    MVP: ביצוע סדרתי — כל שלב ממתין לסיום הקודם.
    כל שלב נרשם עם: שם, ספירת רשומות, ספירת שגיאות ומשך ריצה.
    """

    def __init__(
        self,
        country_code: str = "IL",
        language_code: str = "he",
        run_id: uuid.UUID | None = None,
    ) -> None:
        """
        מאתחל את ה-PipelineOrchestrator.

        Args:
            country_code: קוד מדינה לסינון וחישוב אותות (ברירת מחדל: "IL").
            language_code: קוד שפה לסינון (ברירת מחדל: "he").
            run_id: מזהה ריצה ייחודי. אם לא מסופק, נוצר UUID חדש.
        """
        self.country_code = country_code
        self.language_code = language_code
        self.run_id = run_id or uuid.uuid4()

        # רכיבי תשתית
        self._normalizer = Normalizer()
        self._signal_computer = SignalComputer(
            country_code=country_code, language_code=language_code
        )
        self._ranking_engine = RankingEngine()
        self._opportunity_generator = OpportunityGenerator(
            ranking_engine=self._ranking_engine
        )

        # מחברי קלט
        self._job_connector = JobPostingsConnector()
        self._trend_connector = TrendSignalsConnector()
        self._supply_connector = InternalSupplyConnector()

        # סוכנים
        self._trend_agent = TrendAnalysisAgent()
        self._job_agent = JobDemandAgent()
        self._gap_agent = SkillGapAgent()
        self._prioritization_agent = TopicPrioritizationAgent()

    async def run(self) -> dict:
        """
        מריץ את ה-pipeline המלא בסדר סדרתי.

        שלבים:
        1. Ingest — שליפת נתונים גולמיים מכל 3 מחברי stub
        2. Normalize — המרת RawSourceRecord ל-NormalizedRecord
        3. Agent signals — הפעלת סוכני ניתוח (trend, job demand, skill gap, prioritization)
        4. Compute signals — בניית SignalVector עבור נושאים מדורגים
        5. Rank — דירוג SignalVector עם RankingEngine
        6. Generate — יצירת OpportunityBrief מהוקטורים המדורגים

        Returns:
            מילון עם: run_id, steps, opportunities_count, opportunities, errors
        """
        pipeline_start = time.monotonic()
        steps: list[dict] = []
        all_errors: list[str] = []

        logger.info(
            "PipelineOrchestrator.run started",
            extra={
                "run_id": str(self.run_id),
                "country_code": self.country_code,
                "language_code": self.language_code,
            },
        )

        # ---- שלב 1: Ingest ----
        raw_job_records, raw_trend_records, raw_supply_records = await self._step_ingest(
            steps, all_errors
        )

        # ---- שלב 2: Normalize ----
        norm_job_records, norm_trend_records, norm_supply_records = self._step_normalize(
            raw_job_records, raw_trend_records, raw_supply_records, steps, all_errors
        )

        # ---- שלב 3: Agent signals (pass raw records for payload access) ----
        trend_signals, job_demand_signals, skill_gaps, ranked_topics = (
            await self._step_agent_signals(
                norm_trend_records, norm_job_records, norm_supply_records, steps, all_errors,
                raw_job=raw_job_records, raw_trend=raw_trend_records, raw_supply=raw_supply_records,
            )
        )

        # ---- שלב 4: Compute SignalVectors ----
        signal_vectors = self._step_compute_signals(
            ranked_topics,
            norm_job_records,
            norm_trend_records,
            steps,
            all_errors,
        )

        # ---- שלב 5: Rank ----
        ranked = self._step_rank(signal_vectors, steps, all_errors)

        # ---- שלב 6: Generate opportunities ----
        opportunities = self._step_generate(ranked, steps, all_errors)

        total_ms = int((time.monotonic() - pipeline_start) * 1000)

        logger.info(
            "PipelineOrchestrator.run completed",
            extra={
                "run_id": str(self.run_id),
                "opportunities_count": len(opportunities),
                "total_ms": total_ms,
                "error_count": len(all_errors),
            },
        )

        return {
            "run_id": str(self.run_id),
            "country_code": self.country_code,
            "language_code": self.language_code,
            "steps": steps,
            "opportunities_count": len(opportunities),
            "opportunities": [self._brief_to_dict(o) for o in opportunities],
            "errors": all_errors,
            "total_duration_ms": total_ms,
        }

    # ---- שלבי pipeline פרטיים ----

    async def _step_ingest(
        self, steps: list, all_errors: list
    ) -> tuple[list, list, list]:
        """שלב 1: שליפת נתונים גולמיים מכל 3 מחברים."""
        step_start = time.monotonic()
        logger.info("Pipeline step: ingest", extra={"run_id": str(self.run_id)})

        raw_job, job_errors = await self._job_connector.run(
            self.run_id, country_code=self.country_code
        )
        raw_trend, trend_errors = await self._trend_connector.run(
            self.run_id, country_code=self.country_code
        )
        raw_supply, supply_errors = await self._supply_connector.run(self.run_id)

        errors = job_errors + trend_errors + supply_errors
        all_errors.extend([str(e) for e in errors])

        steps.append(
            {
                "step_name": "ingest",
                "record_count": len(raw_job) + len(raw_trend) + len(raw_supply),
                "error_count": len(errors),
                "duration_ms": int((time.monotonic() - step_start) * 1000),
                "detail": {
                    "job_records": len(raw_job),
                    "trend_records": len(raw_trend),
                    "supply_records": len(raw_supply),
                },
            }
        )
        return raw_job, raw_trend, raw_supply

    def _step_normalize(
        self,
        raw_job: list,
        raw_trend: list,
        raw_supply: list,
        steps: list,
        all_errors: list,
    ) -> tuple[list, list, list]:
        """שלב 2: נרמול כל הרשומות הגולמיות."""
        step_start = time.monotonic()
        logger.info("Pipeline step: normalize", extra={"run_id": str(self.run_id)})

        norm_job, job_errs = self._normalize_batch(raw_job)
        norm_trend, trend_errs = self._normalize_batch(raw_trend)
        norm_supply, supply_errs = self._normalize_batch(raw_supply)

        all_errors.extend(job_errs + trend_errs + supply_errs)

        steps.append(
            {
                "step_name": "normalize",
                "record_count": len(norm_job) + len(norm_trend) + len(norm_supply),
                "error_count": len(job_errs) + len(trend_errs) + len(supply_errs),
                "duration_ms": int((time.monotonic() - step_start) * 1000),
                "detail": {
                    "job_normalized": len(norm_job),
                    "trend_normalized": len(norm_trend),
                    "supply_normalized": len(norm_supply),
                },
            }
        )
        return norm_job, norm_trend, norm_supply

    async def _step_agent_signals(
        self,
        norm_trend: list,
        norm_job: list,
        norm_supply: list,
        steps: list,
        all_errors: list,
        raw_job: list | None = None,
        raw_trend: list | None = None,
        raw_supply: list | None = None,
    ) -> tuple[list, list, list, list]:
        """שלב 3: הפעלת סוכני ניתוח — trend, job demand, skill gap, prioritization."""
        step_start = time.monotonic()
        logger.info("Pipeline step: agent_signals", extra={"run_id": str(self.run_id)})

        # Agents work on raw payloads (with structured fields like skills, keyword, etc.)
        trend_payloads = [
            r.payload if hasattr(r, "payload") else (r.model_dump() if hasattr(r, "model_dump") else r)
            for r in (raw_trend or norm_trend)
        ]
        trend_result = await self._trend_agent.run(
            run_id=self.run_id,
            trend_records=trend_payloads,
            country_code=self.country_code,
            language_code=self.language_code,
        )
        trend_signals = trend_result.output.get("topic_signals", []) if trend_result.success else []
        if not trend_result.success and trend_result.error:
            all_errors.append(f"TrendAnalysisAgent: {trend_result.error}")

        # JobDemandAgent — works on raw payloads with skill/company fields
        job_payloads = [
            r.payload if hasattr(r, "payload") else (r.model_dump() if hasattr(r, "model_dump") else r)
            for r in (raw_job or norm_job)
        ]
        job_result = await self._job_agent.run(
            run_id=self.run_id,
            job_records=job_payloads,
            country_code=self.country_code,
            language_code=self.language_code,
        )
        job_demand_signals = (
            job_result.output.get("skill_demand", []) if job_result.success else []
        )
        if not job_result.success and job_result.error:
            all_errors.append(f"JobDemandAgent: {job_result.error}")

        # SkillGapAgent — נושאי ההיצע הפנימי כרשימת מחרוזות
        supply_topics = self._extract_supply_topics(norm_supply)
        gap_result = await self._gap_agent.run(
            run_id=self.run_id,
            demanded_skills=job_demand_signals,
            internal_supply_topics=supply_topics,
        )
        skill_gaps = gap_result.output.get("gaps", []) if gap_result.success else []
        if not gap_result.success and gap_result.error:
            all_errors.append(f"SkillGapAgent: {gap_result.error}")

        # TopicPrioritizationAgent — שילוב כל האותות
        prio_result = await self._prioritization_agent.run(
            run_id=self.run_id,
            trend_signals=trend_signals,
            job_demand_signals=job_demand_signals,
            skill_gaps=skill_gaps,
        )
        ranked_topics = (
            prio_result.output.get("ranked_topics", []) if prio_result.success else []
        )
        if not prio_result.success and prio_result.error:
            all_errors.append(f"TopicPrioritizationAgent: {prio_result.error}")

        steps.append(
            {
                "step_name": "agent_signals",
                "record_count": len(ranked_topics),
                "error_count": sum(
                    1
                    for r in [trend_result, job_result, gap_result, prio_result]
                    if not r.success
                ),
                "duration_ms": int((time.monotonic() - step_start) * 1000),
                "detail": {
                    "trend_topics": len(trend_signals),
                    "job_skills": len(job_demand_signals),
                    "skill_gaps": len(skill_gaps),
                    "ranked_topics": len(ranked_topics),
                },
            }
        )
        return trend_signals, job_demand_signals, skill_gaps, ranked_topics

    def _step_compute_signals(
        self,
        ranked_topics: list[dict],
        norm_job: list,
        norm_trend: list,
        steps: list,
        all_errors: list,
    ) -> list:
        """שלב 4: בניית SignalVector לכל נושא מדורג."""
        step_start = time.monotonic()
        logger.info("Pipeline step: compute_signals", extra={"run_id": str(self.run_id)})

        total_job_records = len(norm_job)
        total_trend_records = len(norm_trend)
        signal_vectors = []
        errors: list[str] = []

        for topic in ranked_topics:
            try:
                topic_name = topic.get("topic_name", "unknown")
                composite_score = float(topic.get("composite_score", 0.0))
                trend_score = float(topic.get("trend_score", 0.0))
                job_market_score = float(topic.get("job_market_score", 0.0))
                gap_score = float(topic.get("gap_score", 0.3))
                evidence_count = int(topic.get("evidence_count", 1))
                signal_sources = topic.get("signal_sources", [])

                # ציון ביקוש: שקלול פשוט מ-job_market_score ו-trend_score
                demand_score = self._signal_computer.compute_demand_score(
                    job_posting_count=max(1, int(job_market_score * total_job_records)),
                    trend_mention_count=max(0, int(trend_score * total_trend_records)),
                    total_records=max(total_job_records + total_trend_records, 1),
                )

                # ציון צמיחה: נגזר מ-trend_score
                growth_score = self._signal_computer.compute_growth_score(
                    recent_count=max(1, int(trend_score * 10)),
                    older_count=max(1, int(trend_score * 7)),
                )

                # ציון פער תוכן: נגזר מ-gap_score ישירות
                content_gap_score = self._signal_computer.compute_content_gap_score(
                    demand_level=job_market_score,
                    supply_coverage=max(0.0, job_market_score - gap_score),
                )

                scores = {
                    "demand_score": demand_score,
                    "growth_score": growth_score,
                    "job_market_score": job_market_score,
                    "trend_score": trend_score,
                    "content_gap_score": content_gap_score,
                    "localization_fit_score": 0.7,  # stub — לא מחושב ב-MVP
                    "teachability_score": 0.7,       # stub — לא מחושב ב-MVP
                    "strategic_fit_score": composite_score,
                }

                # מספר משפחות מקור → ביטחון
                num_families = len(signal_sources)
                confidence = min(1.0, 0.5 + num_families * 0.15)

                sv = self._signal_computer.build_signal_vector(
                    entity_name=topic_name,
                    entity_type="skill",
                    scores=scores,
                    evidence_count=evidence_count,
                    source_families=signal_sources,
                    run_id=self.run_id,
                    confidence_score=confidence,
                )
                signal_vectors.append(sv)

            except Exception as exc:
                errors.append(f"compute_signals/{topic.get('topic_name', '?')}: {exc}")

        all_errors.extend(errors)
        steps.append(
            {
                "step_name": "compute_signals",
                "record_count": len(signal_vectors),
                "error_count": len(errors),
                "duration_ms": int((time.monotonic() - step_start) * 1000),
            }
        )
        return signal_vectors

    def _step_rank(
        self,
        signal_vectors: list,
        steps: list,
        all_errors: list,
    ) -> list:
        """שלב 5: דירוג SignalVector עם RankingEngine."""
        step_start = time.monotonic()
        logger.info("Pipeline step: rank", extra={"run_id": str(self.run_id)})

        try:
            ranked = self._ranking_engine.rank_signals(signal_vectors)
        except Exception as exc:
            all_errors.append(f"rank: {exc}")
            ranked = []

        steps.append(
            {
                "step_name": "rank",
                "record_count": len(ranked),
                "error_count": 0 if ranked else 1,
                "duration_ms": int((time.monotonic() - step_start) * 1000),
            }
        )
        return ranked

    def _step_generate(
        self,
        ranked: list,
        steps: list,
        all_errors: list,
    ) -> list:
        """שלב 6: יצירת OpportunityBrief מהוקטורים המדורגים."""
        step_start = time.monotonic()
        logger.info("Pipeline step: generate_opportunities", extra={"run_id": str(self.run_id)})

        # rank_signals מחזיר list[tuple[SignalVector, float, ScoreBreakdown]]
        signal_vectors_only = [sv for sv, _score, _breakdown in ranked]

        try:
            opportunities = self._opportunity_generator.generate(
                signals=signal_vectors_only, run_id=self.run_id
            )
        except Exception as exc:
            all_errors.append(f"generate_opportunities: {exc}")
            opportunities = []

        steps.append(
            {
                "step_name": "generate_opportunities",
                "record_count": len(opportunities),
                "error_count": 0,
                "duration_ms": int((time.monotonic() - step_start) * 1000),
            }
        )
        return opportunities

    # ---- עזר ----

    def _normalize_batch(self, raw_records: list) -> tuple[list, list[str]]:
        """מנרמל אצווה של RawSourceRecord. מחזיר (normalized_list, error_strings)."""
        normalized = []
        errors: list[str] = []
        for raw in raw_records:
            try:
                normalized.append(self._normalizer.normalize(raw))
            except Exception as exc:
                errors.append(str(exc))
        return normalized, errors

    def _extract_supply_topics(self, norm_supply: list) -> list[str]:
        """
        מחלץ שמות נושאים מרשומות היצע מנורמלות.
        משתמש ב-normalized_title אם זמין, אחרת ב-payload.topics.
        """
        topics: list[str] = []
        for record in norm_supply:
            # שם מנורמל
            title = getattr(record, "normalized_title", None)
            if title and title != "untitled":
                topics.append(title)
            # נושאים מה-payload
            payload = getattr(record, "payload", {}) or {}
            for t in payload.get("topics", []):
                if t:
                    topics.append(str(t))
            for s in payload.get("skills", []):
                if s:
                    topics.append(str(s))
        return list(set(topics))  # dedup

    def _brief_to_dict(self, brief) -> dict:
        """ממיר OpportunityBrief למילון סדרי (JSON-friendly)."""
        return {
            "canonical_topic_name": brief.canonical_topic_name,
            "country_code": brief.country_code,
            "region_code": getattr(brief, "region_code", None),
            "language_code": brief.language_code,
            "audience_segment": (
                brief.audience_segment.value
                if hasattr(brief.audience_segment, "value")
                else str(brief.audience_segment)
            ),
            "recommended_format": (
                brief.recommended_format.value
                if hasattr(brief.recommended_format, "value")
                else str(brief.recommended_format)
            ),
            "opportunity_score": brief.opportunity_score,
            "score_breakdown": {
                "demand_score": brief.score_breakdown.demand_score,
                "growth_score": brief.score_breakdown.growth_score,
                "job_market_score": brief.score_breakdown.job_market_score,
                "trend_score": brief.score_breakdown.trend_score,
                "content_gap_score": brief.score_breakdown.content_gap_score,
                "localization_fit_score": brief.score_breakdown.localization_fit_score,
                "teachability_score": brief.score_breakdown.teachability_score,
                "strategic_fit_score": brief.score_breakdown.strategic_fit_score,
            },
            "confidence_score": brief.confidence_score,
            "why_now_summary": brief.why_now_summary,
            "evidence": [
                {
                    "source_type": e.source_type,
                    "source_reference": e.source_reference,
                    "evidence_summary": e.evidence_summary,
                    "evidence_weight": e.evidence_weight,
                }
                for e in (brief.evidence or [])
            ],
            "classification": brief.classification.value if hasattr(brief.classification, "value") else str(brief.classification),
            "lifecycle_state": (
                brief.lifecycle_state.value
                if hasattr(brief.lifecycle_state, "value")
                else str(brief.lifecycle_state)
            ),
            "run_id": str(brief.run_id),
        }
