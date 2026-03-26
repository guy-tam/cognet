'use client'

import { useTranslations } from 'next-intl'
import { useState, useEffect } from 'react'
import ScoreBar from '@/components/ScoreBar'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api'

interface TopicResult {
  rank: number
  topic: string
  opportunity_score: number
  stackoverflow_questions: number
  hackernews_mentions: number
  hackernews_avg_score: number
  github_repos: number
  wikipedia_views: number
  reddit_posts: number
  trend_direction: string
  growth_rate: number
  evidence_summary: string
  sources_used: number
}

interface SearchResult {
  topic: string
  opportunity_score: number
  demand_signal: string
  growth_signal: string
  confidence: number
  evidence_sources: string[]
  why_now: string
  recommended_action: string
  google_trends_score: number
  google_trends_direction: string
  stackoverflow_activity: number
  hackernews_mentions: number
  hackernews_avg_score: number
  raw_data: Record<string, unknown>
}

interface Country { code: string; name: string }

const DIR_ICON: Record<string, string> = {
  surging: '🚀', rising: '📈', growing: '↗️', stable: '➡️', declining: '📉', unknown: '❓',
}
const DIR_COLOR: Record<string, string> = {
  surging: 'text-green-600', rising: 'text-green-500', growing: 'text-green-400',
  stable: 'text-gray-500', declining: 'text-red-500', unknown: 'text-gray-400',
}
const DEMAND_COLOR: Record<string, string> = {
  very_high: 'bg-green-100 text-green-800', high: 'bg-blue-100 text-blue-800',
  moderate: 'bg-yellow-100 text-yellow-800', low: 'bg-gray-100 text-gray-600',
}

export default function IntelligencePage() {
  const t = useTranslations()
  const [tab, setTab] = useState<'scan' | 'search'>('scan')
  const [country, setCountry] = useState('IL')
  const [countries, setCountries] = useState<Country[]>([])

  // Scan state
  const [scanLoading, setScanLoading] = useState(false)
  const [scanResults, setScanResults] = useState<TopicResult[]>([])
  const [scanInfo, setScanInfo] = useState<{ time: number; scanned: number; name: string; sources: string[] } | null>(null)
  const [selectedTopic, setSelectedTopic] = useState<TopicResult | null>(null)

  // Search state
  const [query, setQuery] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null)
  const [searchTime, setSearchTime] = useState(0)
  const [searchError, setSearchError] = useState<string | null>(null)

  // Trending
  const [trending, setTrending] = useState<{ topic: string }[]>([])
  const [trendingLoading, setTrendingLoading] = useState(false)

  useEffect(() => {
    fetch(`${API}/v1/discover/countries`).then(r => r.json()).then(d => setCountries(d.countries || [])).catch(() => {})
  }, [])

  async function runScan() {
    setScanLoading(true); setScanResults([]); setScanInfo(null); setSelectedTopic(null)
    try {
      const res = await fetch(`${API}/v1/discover/scan?country_code=${country}&limit=30`)
      const d = await res.json()
      setScanResults(d.results || [])
      setScanInfo({ time: d.scan_time_ms, scanned: d.topics_scanned, name: d.country_name, sources: d.sources_queried || [] })
    } catch { setScanResults([]) }
    finally { setScanLoading(false) }
  }

  async function runSearch() {
    if (!query.trim()) return
    setSearchLoading(true); setSearchResult(null); setSearchError(null)
    try {
      const res = await fetch(`${API}/v1/search/analyze?q=${encodeURIComponent(query)}&country_code=${country}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const d = await res.json()
      setSearchResult(d.results?.[0] || null)
      setSearchTime(d.analysis_time_ms || 0)
    } catch (e) { setSearchError(e instanceof Error ? e.message : 'Failed') }
    finally { setSearchLoading(false) }
  }

  async function loadTrending() {
    setTrendingLoading(true)
    try {
      const res = await fetch(`${API}/v1/discover/trending-now?country_code=${country}`)
      const d = await res.json()
      setTrending(d.trending_now || [])
    } catch { setTrending([]) }
    finally { setTrendingLoading(false) }
  }

  function drillDown(topic: string) {
    setQuery(topic); setTab('search')
    // Auto-search
    setTimeout(() => {
      setSearchLoading(true); setSearchResult(null)
      fetch(`${API}/v1/search/analyze?q=${encodeURIComponent(topic)}&country_code=${country}`)
        .then(r => r.json())
        .then(d => { setSearchResult(d.results?.[0] || null); setSearchTime(d.analysis_time_ms || 0) })
        .catch(() => {})
        .finally(() => setSearchLoading(false))
    }, 100)
  }

  const sr = searchResult

  return (
    <div className="space-y-5 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">🧠 Learning Demand Intelligence</h1>
          <p className="text-gray-500 text-sm mt-1">Real-time data from StackOverflow, HackerNews, GitHub, Wikipedia, Reddit, Google Trends</p>
        </div>
      </div>

      {/* Country + Tab selector */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <select value={country} onChange={e => setCountry(e.target.value)}
            className="px-3 py-2 border rounded-lg bg-white text-sm min-w-[200px]">
            {countries.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
            {countries.length === 0 && <option value={country}>{country}</option>}
          </select>

          <div className="flex bg-gray-100 rounded-lg p-0.5">
            <button onClick={() => setTab('scan')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'scan' ? 'bg-white shadow text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}>
              🌍 Market Scan
            </button>
            <button onClick={() => setTab('search')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'search' ? 'bg-white shadow text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}>
              🔍 Deep Search
            </button>
          </div>

          {tab === 'scan' && (
            <button onClick={runScan} disabled={scanLoading}
              className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
              {scanLoading ? '⏳ Scanning 50 topics...' : '🔍 Scan Market'}
            </button>
          )}

          {tab === 'search' && (
            <div className="flex gap-2 flex-1 min-w-[300px]">
              <input type="text" value={query} onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && runSearch()}
                placeholder="Any topic... (e.g. machine learning, React, cybersecurity)"
                className="flex-1 px-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <button onClick={runSearch} disabled={searchLoading || !query.trim()}
                className="px-5 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
                {searchLoading ? '⏳...' : 'Analyze'}
              </button>
            </div>
          )}

          <button onClick={loadTrending} disabled={trendingLoading}
            className="px-3 py-2 bg-orange-50 text-orange-700 rounded-lg text-sm hover:bg-orange-100 disabled:opacity-50">
            {trendingLoading ? '...' : '🔥 Trending'}
          </button>
        </div>
      </div>

      {/* Trending strip */}
      {trending.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-sm font-medium text-orange-700 mr-1">🔥 Trending now:</span>
            {trending.slice(0, 12).map((t, i) => (
              <button key={i} onClick={() => drillDown(t.topic)}
                className="px-2 py-0.5 bg-white rounded text-xs border border-orange-200 hover:bg-orange-100 transition-colors cursor-pointer">
                {t.topic}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ═══ SCAN TAB ═══ */}
      {tab === 'scan' && (
        <>
          {scanLoading && (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-gray-500">Scanning 50 topics across 5 live sources...</p>
              <p className="text-sm text-gray-400 mt-1">StackOverflow · HackerNews · GitHub · Wikipedia · Reddit</p>
            </div>
          )}

          {scanInfo && (
            <p className="text-sm text-gray-500">
              Scanned <strong>{scanInfo.scanned}</strong> topics for <strong>{scanInfo.name}</strong> in {(scanInfo.time / 1000).toFixed(1)}s
              — Sources: {scanInfo.sources.join(', ')}
            </p>
          )}

          {scanResults.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              <div className="lg:col-span-2 bg-white rounded-lg shadow overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-3 py-2.5 text-left text-gray-600 font-medium">#</th>
                      <th className="px-3 py-2.5 text-left text-gray-600 font-medium">Topic</th>
                      <th className="px-3 py-2.5 text-left text-gray-600 font-medium">Score</th>
                      <th className="px-3 py-2.5 text-right text-gray-600 font-medium">SO</th>
                      <th className="px-3 py-2.5 text-right text-gray-600 font-medium">HN</th>
                      <th className="px-3 py-2.5 text-right text-gray-600 font-medium">GitHub</th>
                      <th className="px-3 py-2.5 text-center text-gray-600 font-medium"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {scanResults.map(topic => (
                      <tr key={topic.rank}
                        className={`hover:bg-blue-50 cursor-pointer transition ${selectedTopic?.topic === topic.topic ? 'bg-blue-50' : ''}`}
                        onClick={() => setSelectedTopic(topic)}>
                        <td className="px-3 py-2.5 text-gray-400">{topic.rank}</td>
                        <td className="px-3 py-2.5 font-medium capitalize">{topic.topic}</td>
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-1.5">
                            <div className="w-14"><ScoreBar score={topic.opportunity_score} label="" /></div>
                            <span className="text-xs text-gray-500">{(topic.opportunity_score * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="px-3 py-2.5 text-right text-xs text-gray-500">
                          {topic.stackoverflow_questions > 0 ? `${(topic.stackoverflow_questions / 1000).toFixed(0)}K` : '—'}
                        </td>
                        <td className="px-3 py-2.5 text-right text-xs text-gray-500">
                          {topic.hackernews_mentions > 0 ? `${(topic.hackernews_mentions / 1000).toFixed(1)}K` : '—'}
                        </td>
                        <td className="px-3 py-2.5 text-right text-xs text-gray-500">
                          {topic.github_repos > 0 ? `${(topic.github_repos / 1000).toFixed(0)}K` : '—'}
                        </td>
                        <td className="px-3 py-2.5 text-center">
                          <button onClick={e => { e.stopPropagation(); drillDown(topic.topic) }}
                            className="text-blue-500 hover:text-blue-700 text-xs">🔍</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Side panel */}
              <div>
                {selectedTopic ? (
                  <div className="bg-white rounded-lg shadow p-5 sticky top-6 space-y-4">
                    <h3 className="text-lg font-bold capitalize">{selectedTopic.topic}</h3>
                    <div className="text-center">
                      <div className="text-4xl font-bold">{(selectedTopic.opportunity_score * 100).toFixed(0)}%</div>
                      <div className="text-xs text-gray-500">Opportunity Score</div>
                    </div>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between"><span className="text-gray-500">StackOverflow</span><span>{selectedTopic.stackoverflow_questions.toLocaleString()} questions</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">HackerNews</span><span>{selectedTopic.hackernews_mentions.toLocaleString()} mentions</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">GitHub</span><span>{selectedTopic.github_repos.toLocaleString()} repos</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Wikipedia</span><span>{selectedTopic.wikipedia_views.toLocaleString()} views/mo</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Reddit</span><span>{selectedTopic.reddit_posts} posts</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Sources</span><span>{selectedTopic.sources_used}/5</span></div>
                    </div>
                    {selectedTopic.evidence_summary && (
                      <p className="text-xs text-blue-700 bg-blue-50 p-2 rounded">{selectedTopic.evidence_summary}</p>
                    )}
                    <button onClick={() => drillDown(selectedTopic.topic)}
                      className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                      🔍 Deep Analyze
                    </button>
                  </div>
                ) : (
                  <div className="bg-white rounded-lg shadow p-5 text-center text-gray-400 text-sm">
                    Click a topic for details
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* ═══ SEARCH TAB ═══ */}
      {tab === 'search' && (
        <>
          {searchLoading && (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-gray-500">Analyzing &quot;{query}&quot; across 10+ live sources...</p>
            </div>
          )}
          {searchError && <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">{searchError}</div>}

          {sr && (
            <div className="space-y-5">
              {/* Header */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-xl font-bold capitalize">{sr.topic}</h2>
                    <div className="flex items-center gap-3 mt-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${DEMAND_COLOR[sr.demand_signal] || 'bg-gray-100'}`}>
                        Demand: {sr.demand_signal.replace('_', ' ')}
                      </span>
                      <span className={`text-sm ${DIR_COLOR[sr.growth_signal] || ''}`}>
                        {DIR_ICON[sr.growth_signal] || ''} {sr.growth_signal}
                      </span>
                      <span className="text-xs text-gray-400">{sr.evidence_sources.length} sources · {searchTime}ms</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-4xl font-bold">{(sr.opportunity_score * 100).toFixed(0)}%</div>
                    <div className="text-xs text-gray-500">Opportunity</div>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <p className="font-medium text-blue-800 text-sm">📋 {sr.recommended_action}</p>
                </div>
              </div>

              {/* Source cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg shadow p-4">
                  <h4 className="font-medium text-gray-700 text-sm mb-2">📊 Google Trends</h4>
                  <ScoreBar score={sr.google_trends_score} label="Interest" />
                  <p className="mt-1 text-xs text-gray-500">Direction: <strong>{sr.google_trends_direction}</strong></p>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                  <h4 className="font-medium text-gray-700 text-sm mb-2">💬 StackOverflow</h4>
                  <div className="text-2xl font-bold">{sr.stackoverflow_activity.toLocaleString()}</div>
                  <p className="text-xs text-gray-500">tagged questions</p>
                </div>
                <div className="bg-white rounded-lg shadow p-4">
                  <h4 className="font-medium text-gray-700 text-sm mb-2">🔶 HackerNews</h4>
                  <div className="text-2xl font-bold">{sr.hackernews_mentions.toLocaleString()}</div>
                  <p className="text-xs text-gray-500">mentions · avg score {sr.hackernews_avg_score}</p>
                </div>
              </div>

              {/* Why Now */}
              <div className="bg-white rounded-lg shadow p-5">
                <h4 className="font-medium text-gray-700 mb-2">💡 Why Now</h4>
                <p className="text-gray-700 text-sm">{sr.why_now}</p>
                <div className="mt-3 flex gap-2 flex-wrap">
                  {sr.evidence_sources.map(s => (
                    <span key={s} className="px-2 py-0.5 bg-gray-100 rounded text-xs">{s}</span>
                  ))}
                  <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">Confidence: {(sr.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
