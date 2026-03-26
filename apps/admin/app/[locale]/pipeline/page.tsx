'use client'

import { useTranslations } from 'next-intl'
import { useEffect, useState } from 'react'
import { getPipelineStatus } from '@/lib/api-client'
import type { PipelineStatusResponse } from '@/types/api'

// בדג סטטוס pipeline
function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    completed: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
    running: 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200',
    failed: 'bg-red-50 text-red-700 ring-1 ring-red-200',
    partial: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
    pending: 'bg-slate-50 text-slate-600 ring-1 ring-slate-200',
  }
  const t = useTranslations('pipeline')
  const label = status in colorMap
    ? t(`status_labels.${status as 'completed' | 'running' | 'failed' | 'partial' | 'pending'}`)
    : status

  return (
    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold ${colorMap[status] ?? 'bg-gray-100 text-gray-700'}`}>
      {label}
    </span>
  )
}

// שורת skeleton
function SkeletonRow() {
  return (
    <div className="animate-pulse h-6 bg-gray-100 rounded my-2" />
  )
}

// פורמט תאריך בצורה נוחה
function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

export default function PipelinePage() {
  const t = useTranslations('pipeline')
  const tCommon = useTranslations('common')

  const [data, setData] = useState<PipelineStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const result = await getPipelineStatus()
      setData(result)
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
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* כותרת */}
      <h1 className="text-3xl font-bold"><span className="gradient-text">{t('title')}</span></h1>

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

      {/* כרטיס פרטי הרצה */}
      <div className="premium-card p-6 space-y-5">
        <h2 className="text-base font-semibold text-gray-700">פרטי הרצה אחרונה</h2>

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)}
          </div>
        ) : !data ? (
          <p className="text-gray-400 text-sm text-center py-6">{t('no_runs')}</p>
        ) : (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-5 text-sm">
            {/* Run ID */}
            <div className="space-y-1">
              <dt className="text-gray-500 font-medium">{t('run_id')}</dt>
              <dd className="font-mono text-xs text-gray-700 break-all">
                {data.pipeline_run_id ?? tCommon('na')}
              </dd>
            </div>

            {/* סטטוס */}
            <div className="space-y-1">
              <dt className="text-gray-500 font-medium">{t('status')}</dt>
              <dd>
                <StatusBadge status={data.status} />
              </dd>
            </div>

            {/* זמן התחלה */}
            <div className="space-y-1">
              <dt className="text-gray-500 font-medium">{t('started')}</dt>
              <dd className="text-gray-700">{formatDate(data.started_at)}</dd>
            </div>

            {/* זמן סיום */}
            <div className="space-y-1">
              <dt className="text-gray-500 font-medium">{t('ended')}</dt>
              <dd className="text-gray-700">{formatDate(data.ended_at)}</dd>
            </div>

            {/* שגיאות */}
            <div className="space-y-1">
              <dt className="text-gray-500 font-medium">{t('errors')}</dt>
              <dd className={data.error_count > 0 ? 'text-red-600 font-bold' : 'text-gray-700'}>
                {data.error_count}
              </dd>
            </div>

            {/* הרצה מוצלחת אחרונה */}
            <div className="space-y-1">
              <dt className="text-gray-500 font-medium">הרצה מוצלחת אחרונה</dt>
              <dd className="text-gray-700">{formatDate(data.last_successful_run)}</dd>
            </div>
          </dl>
        )}
      </div>

      {/* טבלת שלבים */}
      {!loading && data && data.step_summaries.length > 0 && (
        <div className="premium-card overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-700">{t('steps')}</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-start px-4 py-3 font-medium text-gray-500">#</th>
                  <th className="text-start px-4 py-3 font-medium text-gray-500">שלב</th>
                  <th className="text-start px-4 py-3 font-medium text-gray-500">פרטים</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.step_summaries.map((step, idx) => (
                  <tr key={idx} className="hover:bg-indigo-50/50 transition-colors">
                    <td className="px-4 py-3 text-gray-400">{idx + 1}</td>
                    <td className="px-4 py-3 font-medium text-gray-700">
                      {typeof step['name'] === 'string' ? step['name'] : `שלב ${idx + 1}`}
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-mono text-xs max-w-md truncate">
                      {JSON.stringify(step)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* מצב ריק לשלבים */}
      {!loading && data && data.step_summaries.length === 0 && (
        <div className="premium-card p-6 text-center">
          <p className="text-gray-400 text-sm">אין שלבים להצגה</p>
        </div>
      )}
    </div>
  )
}
