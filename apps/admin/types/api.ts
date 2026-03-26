// טיפוסי TypeScript המשקפים את ה-Pydantic schemas של ה-backend

export interface ScoreBreakdown {
  demand_score: number
  growth_score: number
  job_market_score: number
  trend_score: number
  content_gap_score: number
  localization_fit_score: number
  teachability_score: number
  strategic_fit_score: number
}

export interface EvidenceItem {
  source_type: string
  source_reference: string
  evidence_summary: string
  evidence_weight: number
}

export type OpportunityClassification =
  | 'immediate'
  | 'near_term'
  | 'watchlist'
  | 'low_priority'
  | 'rejected'
  | 'archived'

export type LifecycleState =
  | 'draft'
  | 'surfaced'
  | 'analyst_review'
  | 'approved'
  | 'rejected'
  | 'archived'

export type RecommendedFormat =
  | 'short_course'
  | 'learning_track'
  | 'workshop'
  | 'certification_prep'
  | 'project_based'

export interface OpportunityResponse {
  id: string | null
  topic_id: string | null
  canonical_topic_name: string
  country_code: string
  region_code: string | null
  language_code: string
  audience_segment: string
  recommended_format: RecommendedFormat
  opportunity_score: number
  score_breakdown: ScoreBreakdown
  why_now_summary: string
  evidence: EvidenceItem[]
  confidence_score: number
  classification: OpportunityClassification
  lifecycle_state: LifecycleState
  run_id: string
  created_at: string
}

export interface OpportunityListResponse {
  opportunities: OpportunityResponse[]
  total: number
  filters_applied: Record<string, string>
}

export interface PipelineStatusResponse {
  pipeline_run_id: string | null
  status: string
  started_at: string | null
  ended_at: string | null
  step_summaries: Record<string, unknown>[]
  error_count: number
  last_successful_run: string | null
}

export interface HealthResponse {
  status: string
  timestamp: string
}

export interface ApiError {
  error: {
    code: string
    message: string
    request_id: string | null
  }
}
