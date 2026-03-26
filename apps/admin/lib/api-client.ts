import type {
  HealthResponse,
  OpportunityListResponse,
  OpportunityResponse,
  PipelineStatusResponse,
} from '@/types/api'

// כתובת בסיס של ה-API — ניתן לשינוי דרך משתנה סביבה
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api'

// פונקציית fetch מרכזית עם טיפוסים ומניעת שגיאות גנריות
async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!res.ok) {
    const err = await res
      .json()
      .catch(() => ({ error: { code: 'UNKNOWN', message: res.statusText } }))
    throw new Error(err?.error?.message ?? 'API request failed')
  }

  return res.json() as Promise<T>
}

// פרמטרים לסינון הזדמנויות
export interface GetOpportunitiesParams {
  country_code?: string
  language_code?: string
  classification?: string
  min_score?: number
  limit?: number
  offset?: number
}

// שליפת רשימת הזדמנויות עם פרמטרי סינון
export async function getOpportunities(
  params: GetOpportunitiesParams = {}
): Promise<OpportunityListResponse> {
  const query = new URLSearchParams()
  if (params.country_code) query.set('country_code', params.country_code)
  if (params.language_code) query.set('language_code', params.language_code)
  if (params.classification) query.set('classification', params.classification)
  if (params.min_score !== undefined)
    query.set('min_score', String(params.min_score))
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.offset !== undefined) query.set('offset', String(params.offset))

  const qs = query.toString()
  return apiFetch<OpportunityListResponse>(
    `/v1/opportunities${qs ? `?${qs}` : ''}`
  )
}

// שליפת ההזדמנויות המובילות
export async function getTopOpportunities(params: {
  country_code?: string
  language_code?: string
  limit?: number
} = {}): Promise<OpportunityResponse[]> {
  const query = new URLSearchParams()
  if (params.country_code) query.set('country_code', params.country_code)
  if (params.language_code) query.set('language_code', params.language_code)
  if (params.limit !== undefined) query.set('limit', String(params.limit))

  const qs = query.toString()
  return apiFetch<OpportunityResponse[]>(
    `/v1/opportunities/top${qs ? `?${qs}` : ''}`
  )
}

// שליפת הזדמנויות לפי שוק ספציפי
export async function getOpportunitiesByMarket(
  country_code: string,
  language_code: string,
  classification?: string
): Promise<OpportunityListResponse> {
  const query = new URLSearchParams({ country_code, language_code })
  if (classification) query.set('classification', classification)

  return apiFetch<OpportunityListResponse>(
    `/v1/opportunities/by-market?${query.toString()}`
  )
}

// שליפת סטטוס ה-pipeline
export async function getPipelineStatus(): Promise<PipelineStatusResponse> {
  return apiFetch<PipelineStatusResponse>('/v1/pipeline/status')
}

// בדיקת תקינות ה-API
export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health')
}
