'use client'

import { useTranslations } from 'next-intl'
import { useState, useEffect } from 'react'
import ScoreBar from '@/components/ScoreBar'
import { Link } from '@/lib/navigation'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api'

interface Opp {
  canonical_topic_name: string
  opportunity_score: number
  confidence_score: number
  classification: string
  country_code: string
  why_now_summary: string
}

export default function DashboardPage() {
  const t = useTranslations()
  const [opps, setOpps] = useState<Opp[]>([])
  const [pipeStatus, setPipeStatus] = useState<string>('...')
  const [apiStatus, setApiStatus] = useState<string>('...')
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState('')

  async function refresh() {
    setLoading(true)
    try {
      const [h, o, p] = await Promise.allSettled([
        fetch(`${API}/../health`).then(r => r.json()),
        fetch(`${API}/v1/opportunities/top?limit=10`).then(r => r.json()),
        fetch(`${API}/v1/pipeline/status`).then(r => r.json()),
      ])
      setApiStatus(h.status === 'fulfilled' ? h.value?.status || '?' : 'offline')
      if (o.status === 'fulfilled') setOpps(Array.isArray(o.value) ? o.value : o.value?.opportunities || [])
      if (p.status === 'fulfilled') setPipeStatus(p.value?.status || '?')
      setLastRefresh(new Date().toLocaleTimeString())
    } catch { setApiStatus('error') }
    finally { setLoading(false) }
  }

  useEffect(() => { refresh() }, [])
  useEffect(() => { const i = setInterval(refresh, 60000); return () => clearInterval(i) }, [])

  const cc: Record<string, string> = {
    immediate: 'bg-green-100 text-green-800', near_term: 'bg-blue-100 text-blue-800',
    watchlist: 'bg-yellow-100 text-yellow-800', low_priority: 'bg-gray-100 text-gray-600',
  }
  const sc: Record<string, string> = { ok: 'bg-green-500', completed: 'bg-green-500', degraded: 'bg-yellow-500', offline: 'bg-red-500' }

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('dashboard.title')}</h1>
          <p className="text-gray-500 text-sm">{t('dashboard.subtitle')}</p>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && <span className="text-xs text-gray-400">{lastRefresh}</span>}
          <button onClick={refresh} disabled={loading} className="px-3 py-1.5 bg-gray-100 rounded text-sm hover:bg-gray-200">
            {loading ? '...' : '↻'}
          </button>
        </div>
      </div>

      {/* Status */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 mb-1">
            <div className={`w-2.5 h-2.5 rounded-full ${sc[apiStatus] || 'bg-gray-400'}`} />
            <span className="text-sm text-gray-500">API</span>
          </div>
          <div className="text-lg font-bold capitalize">{apiStatus}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 mb-1">
            <div className={`w-2.5 h-2.5 rounded-full ${sc[pipeStatus] || 'bg-gray-400'}`} />
            <span className="text-sm text-gray-500">Pipeline</span>
          </div>
          <div className="text-lg font-bold capitalize">{pipeStatus}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <span className="text-sm text-gray-500">{t('dashboard.total_opportunities')}</span>
          <div className="text-2xl font-bold">{opps.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <span className="text-sm text-gray-500">Top Score</span>
          <div className="text-2xl font-bold">{opps[0] ? `${(opps[0].opportunity_score * 100).toFixed(0)}%` : '—'}</div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link href="/discover" className="bg-white rounded-lg shadow p-4 hover:bg-blue-50 transition border-l-4 border-blue-500 block">
          <div className="font-medium">🌍 {t('nav.discover')}</div>
          <p className="text-sm text-gray-500 mt-1">Scan 50 topics × 5 sources × 50 countries — real-time</p>
        </Link>
        <Link href="/demand" className="bg-white rounded-lg shadow p-4 hover:bg-purple-50 transition border-l-4 border-purple-500 block">
          <div className="font-medium">📚 Learning Demand</div>
          <p className="text-sm text-gray-500 mt-1">What people want to learn — search patterns + hiring signals</p>
        </Link>
        <Link href="/opportunities" className="bg-white rounded-lg shadow p-4 hover:bg-green-50 transition border-l-4 border-green-500 block">
          <div className="font-medium">📊 {t('nav.opportunities')}</div>
          <p className="text-sm text-gray-500 mt-1">{opps.length} ranked opportunities from pipeline</p>
        </Link>
      </div>

      {/* Top opportunities live table */}
      {opps.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-5 py-3 border-b flex items-center justify-between">
            <h2 className="font-semibold">{t('dashboard.top_opportunities')}</h2>
            <Link href="/opportunities" className="text-sm text-blue-600 hover:underline">View all →</Link>
          </div>
          <div className="divide-y">
            {opps.slice(0, 8).map((o, i) => (
              <div key={i} className="px-5 py-3 flex items-center gap-4 hover:bg-gray-50">
                <span className="text-gray-400 text-sm w-6">{i + 1}</span>
                <div className="flex-1">
                  <span className="font-medium capitalize">{o.canonical_topic_name}</span>
                  <span className="text-xs text-gray-400 ml-2">{o.country_code}</span>
                </div>
                <div className="w-20"><ScoreBar score={o.opportunity_score} label="" /></div>
                <span className="text-sm w-12">{(o.opportunity_score * 100).toFixed(0)}%</span>
                <span className={`px-2 py-0.5 rounded-full text-xs ${cc[o.classification] || 'bg-gray-100'}`}>
                  {o.classification?.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
