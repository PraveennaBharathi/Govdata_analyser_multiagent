'use client'

import { useEffect, useState, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Wind, Cloud, RefreshCw, MapPin, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PSIRegion {
  psi: number
  pm25: number
  pm10: number
  category: string
}

interface LiveCityData {
  status: string
  psi?: {
    timestamp: string
    overall: number
    category: string
    color: string
    by_region: Record<string, PSIRegion>
  }
  weather?: {
    timestamp: string
    valid_start: string
    valid_end: string
    summary: string
    breakdown: Array<{ forecast: string; count: number }>
    forecasts: Array<{ area: string; forecast: string }>
  }
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const PSI_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  Good:           { bg: 'bg-green-50',  text: 'text-green-700',  border: 'border-green-200' },
  Moderate:       { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  Unhealthy:      { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  'Very Unhealthy': { bg: 'bg-red-50', text: 'text-red-700',   border: 'border-red-200' },
  Hazardous:      { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
}

const REGION_LABELS: Record<string, string> = {
  north: 'North', south: 'South', east: 'East', west: 'West', central: 'Central'
}

function psiBarColor(val: number) {
  if (val <= 50)  return '#16a34a'
  if (val <= 100) return '#ca8a04'
  if (val <= 200) return '#ea580c'
  if (val <= 300) return '#dc2626'
  return '#7c3aed'
}

function fmt(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })
  } catch { return ts }
}

export function LiveCityView() {
  const [data, setData] = useState<LiveCityData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/live-city`)
      if (!res.ok) throw new Error(`API error ${res.status}`)
      const json: LiveCityData = await res.json()
      setData(json)
      setLastRefresh(new Date())
    } catch (e) {
      console.error('Live city fetch failed', e)
      setError(e instanceof Error ? e.message : 'Failed to load live city data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const id = setInterval(fetchData, 10 * 60 * 1000) // refresh every 10 min
    return () => clearInterval(id)
  }, [fetchData])

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center py-24 text-gray-400">
        <Loader2 className="h-8 w-8 animate-spin mr-3" />
        <span>Fetching live city data…</span>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-red-400 gap-3">
        <p className="font-medium">Failed to load live city data</p>
        <p className="text-sm text-gray-400">{error}</p>
        <button onClick={fetchData} className="text-sm text-blue-500 underline">Retry</button>
      </div>
    )
  }

  const psi = data?.psi
  const wx  = data?.weather
  const psiColors = psi ? (PSI_COLORS[psi.category] ?? PSI_COLORS['Moderate']) : null

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Live City Dashboard</h2>
          <p className="text-sm text-gray-500">
            Real-time data from NEA · Last updated {lastRefresh.toLocaleTimeString('en-SG', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50"
        >
          <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* PSI Panel */}
      {psi && psiColors && (
        <Card className={cn('border-2', psiColors.border, psiColors.bg)}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wind className={cn('h-5 w-5', psiColors.text)} />
              Air Quality (PSI) · {fmt(psi.timestamp)}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Overall score */}
            <div className="flex items-center gap-6">
              <div className="text-center">
                <div
                  className="text-6xl font-black tabular-nums"
                  style={{ color: psiBarColor(psi.overall) }}
                >
                  {psi.overall}
                </div>
                <div className="text-xs text-gray-500 mt-1">Overall PSI</div>
              </div>
              <div>
                <div className={cn('text-2xl font-bold', psiColors.text)}>{psi.category}</div>
                <div className="text-sm text-gray-600 mt-1">24-hour PSI (max across regions)</div>
                <div className="mt-2 h-2.5 w-48 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(psi.overall / 300 * 100, 100)}%`,
                      backgroundColor: psiBarColor(psi.overall),
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1 w-48">
                  <span>0</span><span>Good</span><span>Moderate</span><span>300</span>
                </div>
              </div>
            </div>

            {/* Region breakdown */}
            <div className="grid grid-cols-5 gap-2">
              {Object.entries(psi.by_region).map(([region, r]) => (
                <div key={region} className="p-3 bg-white rounded-lg border text-center">
                  <div className="text-xs text-gray-500 font-medium">{REGION_LABELS[region]}</div>
                  <div
                    className="text-2xl font-bold mt-1 tabular-nums"
                    style={{ color: psiBarColor(r.psi) }}
                  >
                    {r.psi}
                  </div>
                  <div className="text-xs text-gray-400">PM2.5: {r.pm25}</div>
                </div>
              ))}
            </div>

            <p className="text-xs text-gray-400">
              PSI 0–50: Good · 51–100: Moderate · 101–200: Unhealthy · 201–300: Very Unhealthy · 300+: Hazardous
            </p>
          </CardContent>
        </Card>
      )}

      {/* Weather Panel */}
      {wx && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cloud className="h-5 w-5 text-blue-500" />
              2-Hour Weather Forecast · Valid {fmt(wx.valid_start)} – {fmt(wx.valid_end)}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Summary pills */}
            <div className="flex flex-wrap gap-2">
              {wx.breakdown.map(({ forecast, count }) => (
                <span
                  key={forecast}
                  className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-200"
                >
                  {forecast} <span className="text-blue-400 ml-1">({count} areas)</span>
                </span>
              ))}
            </div>

            {/* Area grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 max-h-72 overflow-y-auto">
              {wx.forecasts.map(({ area, forecast }) => (
                <div key={area} className="flex items-center gap-1.5 p-1.5 rounded hover:bg-gray-50">
                  <MapPin className="h-3 w-3 text-gray-300 flex-shrink-0" />
                  <span className="text-xs text-gray-700 font-medium truncate">{area}</span>
                  <span className="text-xs text-gray-400 truncate flex-1">{forecast.split('(')[0].trim()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
