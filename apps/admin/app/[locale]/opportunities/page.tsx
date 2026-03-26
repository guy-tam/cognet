'use client'

import { useTranslations } from 'next-intl'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { getOpportunities, type GetOpportunitiesParams } from '@/lib/api-client'
import type { OpportunityListResponse, OpportunityClassification } from '@/types/api'

// בדג סיווג עם צבע מתאים
function ClassificationBadge({ cls }: { cls: string }) {
  const colorMap: Record<string, string> = {
    immediate: 'bg-green-100 text-green-800',
    near_term: 'bg-blue-100 text-blue-800',
    watchlist: 'bg-yellow-100 text-yellow-800',
    low_priority: 'bg-gray-100 text-gray-600',
    rejected: 'bg-red-100 text-red-700',
    archived: 'bg-purple-100 text-purple-700',
  }
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${colorMap[cls] ?? 'bg-gray-100 text-gray-600'}`}>
      {cls}
    </span>
  )
}

// שורת skeleton לטעינה
function TableRowSkeleton() {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: 7 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-gray-100 rounded" />
        </td>
      ))}
    </tr>
  )
}

// קלאסיפיקציות אפשריות לסינון
const CLASSIFICATIONS: Array<{ value: OpportunityClassification | ''; label: string }> = [
  { value: '', label: '—' },
  { value: 'immediate', label: 'Immediate' },
  { value: 'near_term', label: 'Near Term' },
  { value: 'watchlist', label: 'Watchlist' },
  { value: 'low_priority', label: 'Low Priority' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'archived', label: 'Archived' },
]

const PAGE_SIZE = 20

export default function OpportunitiesPage() {
  const t = useTranslations('opportunities')
  const tCommon = useTranslations('common')
  const router = useRouter()

  // מצב סינון
  const [filters, setFilters] = useState<GetOpportunitiesParams>({})
  const [pendingFilters, setPendingFilters] = useState<GetOpportunitiesParams>({})

  // מצב תוצאות
  const [data, setData] = useState<OpportunityListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(0)

  async function loadData(params: GetOpportunitiesParams, pageNum: number) {
    setLoading(true)
    setError(null)
    try {
      const result = await getOpportunities({
        ...params,
        limit: PAGE_SIZE,
        offset: pageNum * PAGE_SIZE,
      })
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : tCommon('error'))
    } finally {
      setLoading(false)
    }
  }

  // טעינה ראשונית ובכל שינוי של סינון / עמוד
  useEffect(() => {
    loadData(filters, page)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, page])

  function applyFilters() {
    setPage(0)
    setFilters({ ...pendingFilters })
  }

  function resetFilters() {
    setPendingFilters({})
    setPage(0)
    setFilters({})
  }

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* כותרת */}
      <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>

      {/* פאנל סינון */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">{t('filters')}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {/* מדינה */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              {t('country')}
            </label>
            <input
              type="text"
              placeholder="e.g. US, IL"
              value={pendingFilters.country_code ?? ''}
              onChange={(e) =>
                setPendingFilters((f) => ({ ...f, country_code: e.target.value || undefined }))
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* שפה */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              {t('language')}
            </label>
            <input
              type="text"
              placeholder="e.g. en, he"
              value={pendingFilters.language_code ?? ''}
              onChange={(e) =>
                setPendingFilters((f) => ({ ...f, language_code: e.target.value || undefined }))
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* סיווג */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              {t('classification')}
            </label>
            <select
              value={pendingFilters.classification ?? ''}
              onChange={(e) =>
                setPendingFilters((f) => ({
                  ...f,
                  classification: e.target.value || undefined,
                }))
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              {CLASSIFICATIONS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.value ? t(`classification_labels.${c.value}`) : '—'}
                </option>
              ))}
            </select>
          </div>

          {/* ציון מינימלי */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              {t('min_score')}
            </label>
            <input
              type="number"
              min={0}
              max={1}
              step={0.05}
              placeholder="0.0 – 1.0"
              value={pendingFilters.min_score ?? ''}
              onChange={(e) =>
                setPendingFilters((f) => ({
                  ...f,
                  min_score: e.target.value ? Number(e.target.value) : undefined,
                }))
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* כפתורי סינון */}
        <div className="flex gap-3 mt-4">
          <button
            onClick={applyFilters}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            {t('apply_filters')}
          </button>
          <button
            onClick={resetFilters}
            className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors"
          >
            {t('reset')}
          </button>
        </div>
      </div>

      {/* שגיאה */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center justify-between">
          <p className="text-red-700 text-sm">{error}</p>
          <button
            onClick={() => loadData(filters, page)}
            className="text-sm font-medium text-red-700 underline hover:no-underline"
          >
            {tCommon('retry')}
          </button>
        </div>
      )}

      {/* טבלת הזדמנויות */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <span className="text-sm text-gray-500">
            {data ? `${data.total} תוצאות` : ''}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-start px-4 py-3 font-medium text-gray-500">{t('topic')}</th>
                <th className="text-start px-4 py-3 font-medium text-gray-500">{t('market')}</th>
                <th className="text-start px-4 py-3 font-medium text-gray-500">{t('score')}</th>
                <th className="text-start px-4 py-3 font-medium text-gray-500">{t('confidence')}</th>
                <th className="text-start px-4 py-3 font-medium text-gray-500">{t('classification')}</th>
                <th className="text-start px-4 py-3 font-medium text-gray-500">{t('format')}</th>
                <th className="text-start px-4 py-3 font-medium text-gray-500">{t('created')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                Array.from({ length: 6 }).map((_, i) => <TableRowSkeleton key={i} />)
              ) : !data || data.opportunities.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center">
                    <p className="text-gray-500 font-medium">{t('no_opportunities')}</p>
                    <p className="text-gray-400 text-xs mt-1">{t('no_opportunities_hint')}</p>
                  </td>
                </tr>
              ) : (
                data.opportunities.map((op, idx) => (
                  <tr
                    key={op.id ?? idx}
                    onClick={() => router.push(`opportunities/${page * PAGE_SIZE + idx}`)}
                    className="hover:bg-gray-50 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-3 font-medium text-gray-900 max-w-xs truncate">
                      {op.canonical_topic_name}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {op.country_code}/{op.language_code}
                    </td>
                    <td className="px-4 py-3 font-semibold text-blue-700">
                      {(op.opportunity_score * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {(op.confidence_score * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-3">
                      <ClassificationBadge cls={op.classification} />
                    </td>
                    <td className="px-4 py-3 text-gray-600 capitalize">
                      {op.recommended_format.replace(/_/g, ' ')}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(op.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
            >
              {tCommon('back')}
            </button>
            <span className="text-sm text-gray-500">
              עמוד {page + 1} מתוך {totalPages}
            </span>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
            >
              הבא
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
