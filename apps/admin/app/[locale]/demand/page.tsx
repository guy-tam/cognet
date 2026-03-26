'use client'

import { useState, useEffect } from 'react'
import ScoreBar from '@/components/ScoreBar'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api'

interface TimelinePoint { date: string; value: number }

interface DemandItem {
  rank: number; topic: string; learning_demand_score: number
  hn_learn_mentions: number; hn_avg_score: number
  github_learning_repos: number; github_job_repos: number
  wikipedia_views_30d: number; reddit_learn_posts: number; so_tag_count: number
  gap_signal: string; why: string; action: string; sources_ok: number
  timeline: TimelinePoint[]
}

interface Country { code: string; name: string }

const GAP_BADGE: Record<string, { bg: string; label: string }> = {
  high_gap: { bg: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200', label: '🔥 High Opportunity' },
  moderate_gap: { bg: 'bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200', label: '📈 Moderate' },
  low_gap: { bg: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200', label: '➡️ Low' },
  emerging: { bg: 'bg-purple-50 text-purple-700 ring-1 ring-purple-200', label: '🌱 Emerging' },
  saturated: { bg: 'bg-slate-50 text-slate-600 ring-1 ring-slate-200', label: '⬇️ Saturated' },
}

function MiniTimeline({ data, height = 40 }: { data: TimelinePoint[]; height?: number }) {
  if (!data || data.length < 2) return null
  const values = data.map(d => d.value)
  const max = Math.max(...values, 1)
  const w = 100 / values.length

  return (
    <div className="relative" style={{ height }}>
      <svg viewBox={`0 0 100 ${height}`} className="w-full h-full" preserveAspectRatio="none">
        <defs>
          <linearGradient id="tl" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366F1" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#6366F1" stopOpacity="0.05" />
          </linearGradient>
        </defs>
        {/* Area fill */}
        <path
          d={`M 0 ${height} ` + values.map((v, i) => `L ${i * w} ${height - (v / max) * (height - 4)}`).join(' ') + ` L 100 ${height} Z`}
          fill="url(#tl)"
        />
        {/* Line */}
        <polyline
          points={values.map((v, i) => `${i * w},${height - (v / max) * (height - 4)}`).join(' ')}
          fill="none" stroke="#6366F1" strokeWidth="1.5"
        />
      </svg>
    </div>
  )
}

export default function DemandPage() {
  const [country, setCountry] = useState('US')
  const [countries, setCountries] = useState<Country[]>([])
  const [timeRange, setTimeRange] = useState('30d')
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
      const res = await fetch(`${API}/v1/demand/scan?country_code=${country}&limit=30&time_range=${timeRange}`)
      const d = await res.json()
      setResults(d.results || [])
      setInfo({ time: d.scan_time_ms, count: d.topics_analyzed, name: d.country_name })
    } catch { /* empty */ }
    finally { setLoading(false) }
  }

  const sel = selected

  return (
    <div className="space-y-5 max-w-6xl animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold"><span className="gradient-text">📚 What People Want to Learn</span></h1>
        <p className="text-gray-500 text-sm mt-1">
          Real-time learning demand — HackerNews, GitHub, Wikipedia, Reddit, StackOverflow
        </p>
      </div>

      {/* Controls */}
      <div className="glass-card p-4 flex flex-wrap gap-3 items-center">
        <select value={country} onChange={e => setCountry(e.target.value)}
          className="px-3 py-2 border rounded-lg bg-white text-sm min-w-[180px]">
          {countries.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
          {!countries.length && <option value={country}>{country}</option>}
        </select>

        {/* Time range selector */}
        <div className="flex bg-gray-100 rounded-lg p-0.5">
          {['7d', '30d', '90d'].map(r => (
            <button key={r} onClick={() => setTimeRange(r)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${timeRange === r ? 'bg-white shadow text-purple-700' : 'text-gray-500'}`}>
              {r === '7d' ? 'Week' : r === '30d' ? 'Month' : '3 Months'}
            </button>
          ))}
        </div>

        <button onClick={scan} disabled={loading}
          className="premium-btn disabled:opacity-50">
          {loading ? '⏳ Scanning 50 topics × 6 sources...' : '📚 Scan Learning Demand'}
        </button>

        {info && (
          <span className="text-xs text-gray-400">
            {info.count} topics · {info.name} · {(info.time / 1000).toFixed(1)}s
          </span>
        )}
      </div>

      {loading && (
        <div className="premium-card p-8 text-center">
          <div className="animate-shimmer h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full mx-auto animate-spin" />
          <p className="mt-4 text-gray-600">Scanning what people want to learn...</p>
          <p className="text-xs text-gray-400 mt-1">Querying HackerNews · GitHub · Wikipedia · Reddit · StackOverflow</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Results */}
          <div className="lg:col-span-2 premium-card overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-3 py-2.5 text-left text-gray-600 font-medium w-8">#</th>
                  <th className="px-3 py-2.5 text-left text-gray-600 font-medium">Topic</th>
                  <th className="px-3 py-2.5 text-left text-gray-600 font-medium w-24">Demand</th>
                  <th className="px-3 py-2.5 text-right text-gray-600 font-medium">HN</th>
                  <th className="px-3 py-2.5 text-right text-gray-600 font-medium">GitHub</th>
                  <th className="px-3 py-2.5 text-right text-gray-600 font-medium">Wiki/mo</th>
                  <th className="px-3 py-2.5 text-left text-gray-600 font-medium w-20">Trend</th>
                  <th className="px-3 py-2.5 text-left text-gray-600 font-medium">Signal</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {results.map(item => (
                  <tr key={item.rank}
                    className={`hover:bg-purple-50 cursor-pointer transition ${sel?.topic === item.topic ? 'bg-purple-50' : ''}`}
                    onClick={() => setSelected(item)}>
                    <td className="px-3 py-2.5 text-gray-400">{item.rank}</td>
                    <td className="px-3 py-2.5 font-medium capitalize text-gray-800">{item.topic}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1">
                        <div className="w-12"><ScoreBar score={item.learning_demand_score} label="" /></div>
                        <span className="text-xs text-gray-500">{(item.learning_demand_score * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-right text-xs text-gray-500">
                      {item.hn_learn_mentions > 0 ? item.hn_learn_mentions.toLocaleString() : '—'}
                    </td>
                    <td className="px-3 py-2.5 text-right text-xs text-gray-500">
                      {item.github_learning_repos > 0 ? item.github_learning_repos.toLocaleString() : '—'}
                    </td>
                    <td className="px-3 py-2.5 text-right text-xs text-gray-500">
                      {item.wikipedia_views_30d > 0 ? `${(item.wikipedia_views_30d / 1000).toFixed(0)}K` : '—'}
                    </td>
                    <td className="px-3 py-2.5">
                      {item.timeline.length > 2 && (
                        <MiniTimeline data={item.timeline} height={24} />
                      )}
                    </td>
                    <td className="px-3 py-2.5">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${GAP_BADGE[item.gap_signal]?.bg || 'bg-gray-100'}`}>
                        {GAP_BADGE[item.gap_signal]?.label || item.gap_signal}
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
              <div className="premium-card p-5 sticky top-6 space-y-4 border-l-4 border-l-purple-500">
                <h3 className="text-lg font-bold capitalize">{sel.topic}</h3>
                <div className="text-center">
                  <div className="text-4xl font-bold text-purple-700">{(sel.learning_demand_score * 100).toFixed(0)}%</div>
                  <div className="text-xs text-gray-500">Learning Demand Score</div>
                </div>

                {/* Timeline chart */}
                {sel.timeline.length > 2 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Wikipedia daily views (30 days)</p>
                    <MiniTimeline data={sel.timeline} height={60} />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>{sel.timeline[0]?.date}</span>
                      <span>{sel.timeline[sel.timeline.length - 1]?.date}</span>
                    </div>
                  </div>
                )}

                {/* Source breakdown */}
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-gray-500">🔶 HackerNews</span><span>{sel.hn_learn_mentions.toLocaleString()} mentions</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">🐙 GitHub Learn</span><span>{sel.github_learning_repos.toLocaleString()} repos</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">💼 GitHub Jobs</span><span>{sel.github_job_repos.toLocaleString()} repos</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">📖 Wikipedia</span><span>{sel.wikipedia_views_30d.toLocaleString()} views/mo</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">💬 Reddit</span><span>{sel.reddit_learn_posts} posts</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">📚 StackOverflow</span><span>{sel.so_tag_count.toLocaleString()} questions</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Sources OK</span><span>{sel.sources_ok}/6</span></div>
                </div>

                <div className={`px-3 py-2 rounded-lg text-xs font-medium ${GAP_BADGE[sel.gap_signal]?.bg || 'bg-gray-100'}`}>
                  {GAP_BADGE[sel.gap_signal]?.label || sel.gap_signal}
                </div>

                {sel.why && sel.why !== 'Low signals — emerging or niche topic' && (
                  <p className="text-xs text-gray-600 bg-gray-50 p-3 rounded">{sel.why}</p>
                )}

                <div className="p-3 bg-purple-50 rounded text-sm text-purple-800 font-medium">{sel.action}</div>
              </div>
            ) : (
              <div className="premium-card p-5 text-center text-gray-400 text-sm">
                ← Click a topic for details + timeline
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
