'use client'

import { useTranslations } from 'next-intl'
import { useEffect, useState } from 'react'
import { getTopOpportunities, getPipelineStatus } from '@/lib/api-client'
import type { OpportunityResponse, PipelineStatusResponse } from '@/types/api'

// רכיב skeleton לטעינה
function StatCardSkeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-1/2 mb-3" />
      <div className="h-8 bg-gray-200 rounded w-1/3" />
    </div>
  )
}

// כרטיס סטטיסטיקה
function StatCard({
  label,
  value,
  color = 'blue',
}: {
  label: string
  value: string | number
  color?: 'blue' | 'green' | 'yellow' | 'red'
}) {
  const colorMap = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className={`text-3xl font-bold mt-1 ${colorMap[color]}`}>{value}</p>
    </div>
  )
}

// בדג סטטוס pipeline
function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    completed: 'bg-green-100 text-green-800',
    running: 'bg-blue-100 text-blue-800',
    failed: 'bg-red-100 text-red-800',
    partial: 'bg-yellow-100 text-yellow-800',
    pending: 'bg-gray-100 text-gray-800',
  }
  const cls = colorMap[status] ?? 'bg-gray-100 text-gray-800'

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {status}
    </span>
  )
}

export default function DashboardPage() {
  const t = useTranslations('dashboard')
  const tCommon = useTranslations('common')

  const [topOps, setTopOps] = useState<OpportunityResponse[]>([])
  const [pipeline, setPipeline] = useState<PipelineStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [ops, pip] = await Promise.all([
        getTopOpportunities({ limit: 5 }),
        getPipelineStatus(),
      ])
      setTopOps(ops)
      setPipeline(pip)
    } catch (err) {
      setError(err instanceof Error ? err.message : tCommon('error'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* כותרת */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-500 mt-1">{t('subtitle')}</p>
      </div>

      {/* שגיאה */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center justify-between">
          <p className="text-red-700 text-sm">{error}</p>
          <button
            onClick={loadData}
            className="text-sm font-medium text-red-700 underline hover:no-underline"
          >
            {tCommon('retry')}
          </button>
        </div>
      )}

      {/* כרטיסי סטטיסטיקה */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {loading ? (
          <>
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </>
        ) : (
          <>
            <StatCard
              label={t('total_opportunities')}
              value={topOps.length > 0 ? `${topOps.length}+` : '0'}
              color="blue"
            />
            <StatCard
              label={t('pipeline_status')}
              value={pipeline?.status ?? tCommon('unknown')}
              color={
                pipeline?.status === 'completed'
                  ? 'green'
                  : pipeline?.status === 'failed'
                  ? 'red'
                  : 'yellow'
              }
            />
            <StatCard
              label={t('last_run')}
              value={
                pipeline?.started_at
                  ? new Date(pipeline.started_at).toLocaleDateString()
                  : tCommon('na')
              }
              color="blue"
            />
          </>
        )}
      </div>

      {/* טבלת הזדמנויות מובילות */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">{t('top_opportunities')}</h2>
        </div>

        {loading ? (
          <div className="p-6 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        ) : topOps.length === 0 ? (
          <div className="p-6 text-center text-gray-400 text-sm">
            {tCommon('na')}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-start px-6 py-3 font-medium text-gray-500">נושא</th>
                <th className="text-start px-6 py-3 font-medium text-gray-500">שוק</th>
                <th className="text-start px-6 py-3 font-medium text-gray-500">ציון</th>
                <th className="text-start px-6 py-3 font-medium text-gray-500">סיווג</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {topOps.map((op, idx) => (
                <tr key={op.id ?? idx} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-3 font-medium text-gray-900 truncate max-w-xs">
                    {op.canonical_topic_name}
                  </td>
                  <td className="px-6 py-3 text-gray-600">
                    {op.country_code}/{op.language_code}
                  </td>
                  <td className="px-6 py-3">
                    <span className="font-semibold text-blue-700">
                      {(op.opportunity_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-6 py-3">
                    <StatusBadge status={op.classification} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* פרטי pipeline */}
      {pipeline && !loading && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('pipeline_status')}</h2>
          <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Run ID</dt>
              <dd className="font-mono text-xs text-gray-700 truncate">{pipeline.pipeline_run_id ?? tCommon('na')}</dd>
            </div>
            <div>
              <dt className="text-gray-500">סטטוס</dt>
              <dd><StatusBadge status={pipeline.status} /></dd>
            </div>
            <div>
              <dt className="text-gray-500">שגיאות</dt>
              <dd className={pipeline.error_count > 0 ? 'text-red-600 font-semibold' : 'text-gray-700'}>
                {pipeline.error_count}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">שלבים</dt>
              <dd className="text-gray-700">{pipeline.step_summaries.length}</dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  )
}
