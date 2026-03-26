'use client'

import { useState, useEffect } from 'react'
import ScoreBar from '@/components/ScoreBar'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api'

interface DemandItem {
  rank: number
  topic: string
  learning_demand_score: number
  people_want_to_learn: number
  companies_are_hiring: number
  community_activity: number
  growth_direction: string
  growth_percent: number
  gap_signal: string
  why: string
  action: string
}

const GAP_COLORS: Record<string, string> = {
  high_gap: 'bg-green-100 text-green-800',
  moderate_gap: 'bg-blue-100 text-blue-800',
  low_gap: 'bg-yellow-100 text-yellow-800',
  saturated: 'bg-gray-100 text-gray-600',
}
const GAP_LABELS: Record<string, string> = {
  high_gap: '🔥 High Opportunity', moderate_gap: '📈 Moderate', low_gap: '➡️ Low', saturated: '⬇️ Saturated',
}
const DIR_ICON: Record<string, string> = {
  surging: '🚀', rising: '📈', stable: '➡️', declining: '📉',
}

interface Country { code: string; name: string }

export default function DemandPage() {
  const [country, setCountry] = useState('IL')
  const [countries, setCountries] = useState<Country[]>([])
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<DemandItem[]>([])
  const [info, setInfo] = useState<{ time: number; count: number; name: string } | null>(null)
  const [selected, setSelected] = useState<DemandItem | null>(null)

  useEffect(() => {
    fetch(`${API}/v1/discover/countries`).then(r => r.json()).then(d => setCountries(d.countries || [])).catch(() => {})
  }, [])

  async function scan() {
    setLoading(true); setResults([]); setInfo(null); setSelected(null)
    try {
      const res = await fetch(`${API}/v1/demand/scan?country_code=${country}&limit=30`)
      const d = await res.json()
      setResults(d.results || [])
      setInfo({ time: d.scan_time_ms, count: d.topics_analyzed, name: d.country_name })
    } catch { /* empty */ }
    finally { setLoading(false) }
  }

  const sel = selected

  return (
    <div className="space-y-5 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold">📚 Learning Demand Intelligence</h1>
        <p className="text-gray-500 text-sm mt-1">
          What people actually want to learn right now — based on search patterns, hiring trends, and community activity
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4 flex flex-wrap gap-4 items-center">
        <select value={country} onChange={e => setCountry(e.target.value)}
          className="px-3 py-2.5 border rounded-lg bg-white text-sm min-w-[200px]">
          {countries.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
          {!countries.length && <option value={country}>{country}</option>}
        </select>
        <button onClick={scan} disabled={loading}
          className="px-6 py-2.5 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50">
          {loading ? '⏳ Analyzing learning demand...' : '📚 Scan Learning Demand'}
        </button>
        {info && (
          <span className="text-sm text-gray-500">
            {info.count} topics · {info.name} · {(info.time / 1000).toFixed(1)}s
          </span>
        )}
      </div>

      {loading && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="animate-spin h-8 w-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto" />
          <p className="mt-4 text-gray-500">Analyzing what people want to learn...</p>
          <p className="text-xs text-gray-400 mt-1">Checking &quot;learn X&quot;, &quot;X course&quot;, &quot;X jobs&quot; search patterns + community signals</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Table */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-3 py-2.5 text-left text-gray-600 font-medium">#</th>
                  <th className="px-3 py-2.5 text-left text-gray-600 font-medium">What People Want to Learn</th>
                  <th className="px-3 py-2.5 text-left text-gray-600 font-medium">Demand</th>
                  <th className="px-3 py-2.5 text-center text-gray-600 font-medium">People</th>
                  <th className="px-3 py-2.5 text-center text-gray-600 font-medium">Jobs</th>
                  <th className="px-3 py-2.5 text-left text-gray-600 font-medium">Opportunity</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {results.map(item => (
                  <tr key={item.rank}
                    className={`hover:bg-purple-50 cursor-pointer transition ${sel?.topic === item.topic ? 'bg-purple-50' : ''}`}
                    onClick={() => setSelected(item)}>
                    <td className="px-3 py-2.5 text-gray-400">{item.rank}</td>
                    <td className="px-3 py-2.5 font-medium capitalize">{item.topic}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1.5">
                        <div className="w-14"><ScoreBar score={item.learning_demand_score} label="" /></div>
                        <span className="text-xs">{(item.learning_demand_score * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <span className="text-xs">{item.people_want_to_learn.toFixed(0)}</span>
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <span className="text-xs">{item.companies_are_hiring.toFixed(0)}</span>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${GAP_COLORS[item.gap_signal] || ''}`}>
                        {GAP_LABELS[item.gap_signal] || item.gap_signal}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Detail panel */}
          <div>
            {sel ? (
              <div className="bg-white rounded-lg shadow p-5 sticky top-6 space-y-4">
                <h3 className="text-lg font-bold capitalize">{sel.topic}</h3>
                <div className="text-center">
                  <div className="text-4xl font-bold text-purple-700">{(sel.learning_demand_score * 100).toFixed(0)}%</div>
                  <div className="text-xs text-gray-500">Learning Demand Score</div>
                </div>

                <div className="space-y-2">
                  <ScoreBar score={sel.people_want_to_learn / 100} label="People Searching to Learn" />
                  <ScoreBar score={sel.companies_are_hiring / 100} label="Companies Hiring" />
                  <ScoreBar score={sel.community_activity} label="Community Activity" />
                </div>

                <div className="space-y-1.5 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Growth</span>
                    <span className={sel.growth_percent > 0 ? 'text-green-600' : 'text-red-500'}>
                      {DIR_ICON[sel.growth_direction]} {sel.growth_percent > 0 ? '+' : ''}{sel.growth_percent.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Opportunity</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${GAP_COLORS[sel.gap_signal] || ''}`}>
                      {GAP_LABELS[sel.gap_signal]}
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-purple-50 rounded text-sm text-purple-800">{sel.why}</div>
                <div className="p-3 bg-blue-50 rounded text-sm text-blue-800 font-medium">📋 {sel.action}</div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-5 text-center text-gray-400 text-sm">
                Click a topic for details
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
