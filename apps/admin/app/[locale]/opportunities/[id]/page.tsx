'use client'

import { useTranslations } from 'next-intl'
import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { OpportunityResponse } from '@/types/api'
import { getTopOpportunities } from '@/lib/api-client'
import ScoreBreakdown from '@/components/ScoreBreakdown'

// דף פרטי הזדמנות — מציג מידע מלא על הזדמנות בודדת
export default function OpportunityDetailPage() {
  const t = useTranslations()
  const params = useParams()
  const router = useRouter()
  const [opportunity, setOpportunity] = useState<OpportunityResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadOpportunity() {
      try {
        // גישת MVP: מציאת ההזדמנות מהרשימה לפי אינדקס
        // לאחר MVP: שליפה לפי ID מ-GET /v1/opportunities/:id
        const opportunities = await getTopOpportunities({ limit: 50 })
        const idx = parseInt(params.id as string, 10)
        if (opportunities[idx]) {
          setOpportunity(opportunities[idx])
        } else {
          setError('Opportunity not found')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load opportunity')
      } finally {
        setLoading(false)
      }
    }
    loadOpportunity()
  }, [params.id])

  // מצב טעינה — שלד אנימציה
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse" />
        <div className="h-64 bg-gray-200 rounded animate-pulse" />
      </div>
    )
  }

  // מצב שגיאה
  if (error || !opportunity) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 text-lg">{error || t('common.error')}</p>
        <button
          onClick={() => router.back()}
          className="mt-4 premium-btn"
        >
          {t('common.back')}
        </button>
      </div>
    )
  }

  // מיפוי צבעים לפי סיווג
  const classificationColor: Record<string, string> = {
    immediate: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
    near_term: 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200',
    watchlist: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
    low_priority: 'bg-slate-50 text-slate-600 ring-1 ring-slate-200',
    rejected: 'bg-red-50 text-red-700 ring-1 ring-red-200',
    archived: 'bg-purple-50 text-purple-700 ring-1 ring-purple-200',
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* כותרת */}
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => router.back()}
            className="text-sm text-indigo-600 hover:underline mb-2 inline-block"
          >
            &larr; {t('common.back')}
          </button>
          <h1 className="text-2xl font-bold">{opportunity.canonical_topic_name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${classificationColor[opportunity.classification] || 'bg-gray-100'}`}>
              {t(`opportunities.classification_labels.${opportunity.classification}`)}
            </span>
            <span className="text-gray-500">
              {opportunity.country_code} &middot; {opportunity.language_code}
            </span>
            <span className="text-gray-500">
              {t('opportunities.format')}: {opportunity.recommended_format.replace('_', ' ')}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold">{(opportunity.opportunity_score * 100).toFixed(0)}%</div>
          <div className="text-sm text-gray-500">{t('scores.total')}</div>
        </div>
      </div>

      {/* רשת תוכן ראשית */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* פירוט ציונים */}
        <div className="premium-card p-6">
          <h2 className="text-lg font-semibold mb-4">{t('opportunities.score_breakdown')}</h2>
          <ScoreBreakdown breakdown={opportunity.score_breakdown} />
        </div>

        {/* למה עכשיו */}
        <div className="premium-card p-6">
          <h2 className="text-lg font-semibold mb-4">{t('opportunities.why_now')}</h2>
          <p className="text-gray-700 leading-relaxed">{opportunity.why_now_summary}</p>
          <div className="mt-4 flex items-center gap-4 text-sm text-gray-500">
            <span>{t('scores.confidence')}: {(opportunity.confidence_score * 100).toFixed(0)}%</span>
            <span>{t('opportunities.lifecycle_state')}: {opportunity.lifecycle_state}</span>
          </div>
        </div>

        {/* ראיות */}
        <div className="premium-card p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">
            {t('opportunities.evidence')} ({opportunity.evidence.length})
          </h2>
          {opportunity.evidence.length === 0 ? (
            <p className="text-gray-400 italic">{t('common.na')}</p>
          ) : (
            <div className="space-y-3">
              {opportunity.evidence.map((ev, idx) => (
                <div key={idx} className="border rounded p-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm text-indigo-700">{ev.source_type}</span>
                    <span className="text-xs text-gray-400">
                      weight: {(ev.evidence_weight * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-gray-700 text-sm">{ev.evidence_summary}</p>
                  <p className="text-xs text-gray-400 mt-1">{ev.source_reference}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* כותרת תחתונה — מטא-דאטה */}
      <div className="text-xs text-gray-400 border-t pt-4">
        Run ID: {opportunity.run_id} &middot; Created: {opportunity.created_at || 'N/A'}
      </div>
    </div>
  )
}
