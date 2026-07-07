'use client'
import ReactMarkdown from 'react-markdown'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  BarChart3, Download, FileText, TrendingUp, Lightbulb,
  Building2, Briefcase, MapPin, Home, Network, Layers, Ruler, Zap
} from 'lucide-react'
import { QueryResult, HDBAnalysis, LabourAnalysis, CrossDomainAnalysis, DomainAnalysis } from '@/types'
import { cn } from '@/lib/utils'

interface ResultsViewProps {
  result?: QueryResult
  queryId?: number
  onExport?: (format: 'json' | 'csv') => void
}

// ── helpers ───────────────────────────────────────────────────────────────────

function fmt(n: number, decimals = 0) {
  return n.toLocaleString('en-SG', { maximumFractionDigits: decimals })
}

function fmtSGD(n: number) {
  return `SGD ${n >= 1_000_000 ? (n / 1_000_000).toFixed(2) + 'M' : fmt(n)}`
}

function healthColor(status: string) {
  if (status === 'Healthy') return 'text-green-600'
  if (status === 'Caution') return 'text-yellow-600'
  return 'text-red-600'
}

function healthBg(status: string) {
  if (status === 'Healthy') return 'bg-green-50 border-green-200'
  if (status === 'Caution') return 'bg-yellow-50 border-yellow-200'
  return 'bg-red-50 border-red-200'
}

const METRIC_LABELS: Record<string, string> = {
  unemployment: 'Unemployment Rate',
  retrenchment: 'Retrenchments',
  recruitment: 'Recruitment Rate',
  long_term_unemployment: 'Long-term Unemployment',
}

// ── sub-components ────────────────────────────────────────────────────────────

function InsightsPanel({ insights }: { insights: string[] }) {
  if (!insights?.length) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-amber-500" />
          Key Insights
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="space-y-3">
          {insights.map((ins, i) => (
            <li key={i} className="flex gap-3">
              <span className="flex-shrink-0 h-6 w-6 rounded-full bg-blue-100 text-blue-700 text-sm font-bold flex items-center justify-center">
                {i + 1}
              </span>
              <p className="text-gray-700 leading-relaxed">{ins}</p>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}

function ChartPanel({ chart, title }: { chart: string; title: string }) {
  if (!chart) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-blue-600" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <img
          src={`data:image/png;base64,${chart}`}
          alt={title}
          className="w-full rounded-lg border"
        />
      </CardContent>
    </Card>
  )
}

// ── HDB specific ──────────────────────────────────────────────────────────────

function HDBResults({ a }: { a: HDBAnalysis }) {
  const s = a.summary_statistics
  return (
    <>
      {/* Stats row */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            Market Overview — {s.years_covered}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <StatCard label="Median Price" value={fmtSGD(s.overall_median_price)} />
            <StatCard
              label="Price Change"
              value={`${s.price_change_pct >= 0 ? '+' : ''}${s.price_change_pct.toFixed(1)}%`}
              valueClass={s.price_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}
            />
            <StatCard label="Transactions" value={fmt(s.total_transactions)} />
            <StatCard
              label="Most Expensive"
              value={s.most_expensive_town}
              icon={<MapPin className="h-3 w-3" />}
            />
            <StatCard
              label="Most Affordable"
              value={`${s.most_affordable_town}${s.most_affordable_price ? ` · ${fmtSGD(s.most_affordable_price)}` : ''}`}
              icon={<MapPin className="h-3 w-3" />}
            />
            <StatCard label="Top Flat Type" value={s.top_flat_type} />
          </div>
        </CardContent>
      </Card>

      {/* Town ranking */}
      {a.town_summary?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-blue-600" />
              Town Price Ranking
              <span className="ml-auto text-xs font-normal text-gray-400">Latest year · median resale</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 font-semibold text-gray-600">#</th>
                    <th className="text-left py-2 font-semibold text-gray-600">Town</th>
                    <th className="text-right py-2 font-semibold text-gray-600">Median Price</th>
                  </tr>
                </thead>
                <tbody>
                  {a.town_summary.map((row, i) => (
                    <tr key={row.town} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="py-2 text-gray-400">{i + 1}</td>
                      <td className="py-2 font-medium text-gray-900">{row.town}</td>
                      <td className="py-2 text-right font-mono text-gray-700">{fmtSGD(row.median_price)}</td>
                    </tr>
                  ))}
                  {a.town_summary_bottom?.length > 0 && (
                    <>
                      <tr>
                        <td colSpan={3} className="py-1.5 text-center text-xs text-gray-400 border-b border-dashed tracking-wide">
                          · · · most affordable · · ·
                        </td>
                      </tr>
                      {a.town_summary_bottom.map((row, i) => (
                        <tr key={row.town} className="border-b last:border-0 hover:bg-green-50">
                          <td className="py-2 text-green-600 text-xs">↓</td>
                          <td className="py-2 font-medium text-gray-900">{row.town}</td>
                          <td className="py-2 text-right font-mono text-green-700">{fmtSGD(row.median_price)}</td>
                        </tr>
                      ))}
                    </>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Flat type breakdown */}
      {a.flat_type_summary?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Home className="h-5 w-5 text-purple-600" />
              Prices by Flat Type
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {a.flat_type_summary.map((row) => (
                <div key={row.flat_type} className="p-3 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                  <p className="text-xs text-gray-400 uppercase tracking-wider font-medium">{row.flat_type}</p>
                  <p className="text-xl font-bold text-gray-900 mt-1">{fmtSGD(row.median_price)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Storey premium */}
      {a.storey_summary?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-600" />
              Storey Premium
              {s.high_floor_premium_pct > 0 && (
                <span className="ml-auto text-sm font-normal text-indigo-600">
                  High floors cost +{s.high_floor_premium_pct}% vs low floors
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2 mb-3">
              ⚠ Cross-market average — premium includes estate location effects (high-floor units cluster in premium towns). Pure floor-level premium within comparable blocks is typically 10–20%.
            </p>
            <div className="grid grid-cols-3 gap-3">
              {a.storey_summary.map((row) => (
                <div key={row.band} className="p-4 bg-white rounded-xl border border-gray-100 shadow-sm text-center hover:shadow-md transition-shadow">
                  <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{row.band}</p>
                  <p className="text-xl font-bold text-gray-900 mt-1">{fmtSGD(row.median_price)}</p>
                  <p className="text-xs text-gray-400 mt-1">{fmt(row.transactions)} txns</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Price per sqm */}
      {a.psm_summary?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Ruler className="h-5 w-5 text-teal-600" />
              Price per sqm (Size-Adjusted)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {a.psm_summary.map((row) => (
                <div key={row.flat_type} className="p-3 bg-gray-50 rounded-lg border">
                  <p className="text-xs text-gray-500 uppercase tracking-wide">{row.flat_type}</p>
                  <p className="text-lg font-bold text-teal-700 mt-1">
                    SGD {fmt(row.median_psm)}<span className="text-xs text-gray-400 font-normal">/sqm</span>
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Town momentum */}
      {a.town_momentum?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-500" />
              Fastest-Moving Towns (2023–25 vs 2020–22)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {a.town_momentum.slice(0, 6).map((row, i) => (
                <div key={row.town} className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-4">{i + 1}</span>
                  <span className="text-sm font-medium text-gray-900 flex-1">{row.town}</span>
                  <span className="text-sm text-gray-500">
                    {fmtSGD(row.price_2020_22)} → {fmtSGD(row.price_2023_25)}
                  </span>
                  <span className={cn(
                    'text-sm font-bold min-w-[60px] text-right',
                    row.momentum_pct >= 0 ? 'text-green-600' : 'text-red-600'
                  )}>
                    {row.momentum_pct >= 0 ? '+' : ''}{row.momentum_pct}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <ChartPanel chart={a.chart} title="HDB Resale Price Trends" />
      <InsightsPanel insights={a.insights} />
    </>
  )
}

// ── Labour specific ───────────────────────────────────────────────────────────

function LabourResults({ a }: { a: LabourAnalysis }) {
  const s = a.summary_statistics
  const scoreColor = s.health_status === 'Healthy'
    ? '#16a34a' : s.health_status === 'Caution' ? '#ca8a04' : '#dc2626'

  return (
    <>
      {/* Health Score */}
      <Card className={cn('border-2', healthBg(s.health_status))}>
        <CardContent className="py-6">
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div
                className="text-6xl font-black tabular-nums"
                style={{ color: scoreColor }}
              >
                {s.labour_health_score.toFixed(0)}
              </div>
              <div className="text-sm text-gray-500 mt-1">out of 100</div>
            </div>
            <div>
              <div className={cn('text-2xl font-bold', healthColor(s.health_status))}>
                {s.health_status}
              </div>
              <div className="text-gray-600 text-sm mt-1">
                Labour Market Health Score — {s.latest_year}
              </div>
              <div className="text-xs text-gray-400 mt-2">
                Composite of {s.datasets_analysed.length} live MOM datasets
              </div>
            </div>
          </div>

          {/* Score bar */}
          <div className="mt-4">
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${s.labour_health_score}%`,
                  backgroundColor: scoreColor,
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Stressed</span>
              <span>Caution</span>
              <span>Healthy</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Per-metric scores */}
      {s.metric_scores && Object.keys(s.metric_scores).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-blue-600" />
              Metric Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(s.metric_scores).map(([key, score]) => {
                const c = score >= 70 ? '#16a34a' : score >= 50 ? '#ca8a04' : '#dc2626'
                return (
                  <div key={key} className="p-4 bg-gray-50 rounded-lg border">
                    <p className="text-xs text-gray-500 uppercase tracking-wide">
                      {METRIC_LABELS[key] ?? key.replace(/_/g, ' ')}
                    </p>
                    <div className="flex items-end gap-2 mt-2">
                      <span className="text-2xl font-bold" style={{ color: c }}>
                        {score.toFixed(0)}
                      </span>
                      <span className="text-sm text-gray-400 mb-0.5">/100</span>
                    </div>
                    <div className="mt-2 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${score}%`, backgroundColor: c }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      <ChartPanel chart={a.chart} title="Labour Market Dashboard" />
      <InsightsPanel insights={a.insights} />
    </>
  )
}

// ── Cross-Domain specific ─────────────────────────────────────────────────────

function corrColor(r: number) {
  const abs = Math.abs(r)
  if (abs >= 0.7) return r >= 0 ? 'text-green-600' : 'text-red-600'
  if (abs >= 0.4) return r >= 0 ? 'text-yellow-600' : 'text-orange-600'
  return 'text-gray-500'
}

function CrossDomainResults({ a }: { a: CrossDomainAnalysis }) {
  const s = a.summary_statistics
  const r = s.pearson_r_hdb_labour

  return (
    <>
      {/* Correlation hero card */}
      <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-purple-50">
        <CardContent className="py-6">
          <div className="flex items-start gap-6">
            <div className="text-center flex-shrink-0">
              <div className={cn('text-6xl font-black tabular-nums', corrColor(r))}>
                {r >= 0 ? '+' : ''}{r.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500 mt-1">Pearson r</div>
            </div>
            <div className="flex-1">
              <div className={cn('text-xl font-bold', corrColor(r))}>
                {s.correlation_strength}
              </div>
              <div className="text-gray-600 text-sm mt-1">
                Housing × Labour Market Correlation · {s.year_range}
              </div>
              <p className="text-gray-700 text-sm mt-3 leading-relaxed">{s.key_finding}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats grid */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            Cross-Domain Metrics · {s.year_range}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Years Analyzed" value={s.years_analyzed.toString()} />
            <StatCard
              label="HDB Price Change"
              value={`${s.hdb_price_change_pct >= 0 ? '+' : ''}${s.hdb_price_change_pct.toFixed(1)}%`}
              valueClass={s.hdb_price_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}
            />
            <StatCard
              label="Labour Score Δ"
              value={`${s.labour_score_change >= 0 ? '+' : ''}${s.labour_score_change.toFixed(1)} pts`}
              valueClass={s.labour_score_change >= 0 ? 'text-green-600' : 'text-red-600'}
            />
            <StatCard label="Correlation" value={r >= 0 ? `+${r.toFixed(2)}` : r.toFixed(2)} valueClass={corrColor(r)} />
          </div>
        </CardContent>
      </Card>

      {/* Year-by-year table */}
      {a.correlation_data?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5 text-purple-600" />
              Year-by-Year Alignment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 font-semibold text-gray-600">Year</th>
                    <th className="text-right py-2 font-semibold text-gray-600">HDB Median</th>
                    <th className="text-right py-2 font-semibold text-gray-600">Labour Score</th>
                    {a.correlation_data.every(r => r.unemployment_rate != null) && (
                      <th className="text-right py-2 font-semibold text-gray-600">Unemployment %</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {a.correlation_data.map((row) => (
                    <tr key={row.year} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="py-2 font-medium text-gray-900">{row.year}</td>
                      <td className="py-2 text-right text-gray-700">
                        SGD {(row.hdb_median / 1000).toFixed(0)}k
                      </td>
                      <td className="py-2 text-right">
                        <span className={cn(
                          'font-semibold',
                          row.labour_score >= 70 ? 'text-green-600' :
                          row.labour_score >= 50 ? 'text-yellow-600' : 'text-red-600'
                        )}>
                          {row.labour_score.toFixed(1)}
                        </span>
                      </td>
                      {a.correlation_data.every(r => r.unemployment_rate != null) && (
                        <td className="py-2 text-right text-gray-600">{row.unemployment_rate!.toFixed(1)}%</td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      <ChartPanel chart={a.chart} title="Housing vs Labour Market (Dual-Axis)" />
      <InsightsPanel insights={a.insights} />
    </>
  )
}

// ── Shared stat card ──────────────────────────────────────────────────────────

function StatCard({
  label, value, valueClass = 'text-gray-900', icon
}: {
  label: string
  value: string
  valueClass?: string
  icon?: React.ReactNode
}) {
  return (
    <div className="p-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow duration-200">
      <p className="text-xs text-gray-400 uppercase tracking-wider font-medium">{label}</p>
      <p className={cn('text-2xl font-bold mt-1.5 flex items-center gap-1.5', valueClass)}>
        {icon}{value}
      </p>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export function ResultsView({ result, queryId, onExport }: ResultsViewProps) {
  if (!result?.result) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-gray-400">
          <BarChart3 className="h-16 w-16 mx-auto mb-4 opacity-50" />
          <p>No results yet. Submit a query to see analysis.</p>
        </CardContent>
      </Card>
    )
  }

  const { conversational_response, analysis, query } = result.result

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Query banner */}
      {query && (
        <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-blue-50 border border-blue-100">
          <span className="mt-0.5 flex-shrink-0 h-5 w-5 rounded-full bg-blue-600 flex items-center justify-center text-white text-[10px] font-bold">Q</span>
          <p className="text-sm text-blue-900 font-medium leading-snug">{query}</p>
        </div>
      )}

      {/* Narrative */}
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-blue-100 flex items-center justify-center">
              <FileText className="h-4 w-4 text-blue-600" />
            </div>
            <span className="font-semibold text-slate-800 text-sm">Analysis Summary</span>
          </div>
          {onExport && (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => onExport('json')}>
                <Download className="h-3.5 w-3.5 mr-1.5" />JSON
              </Button>
              <Button variant="outline" size="sm" onClick={() => onExport('csv')}>
                <Download className="h-3.5 w-3.5 mr-1.5" />CSV
              </Button>
            </div>
          )}
        </div>
        <div className="px-6 py-5 prose prose-sm prose-gray max-w-none text-[15px]">
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="text-gray-700 leading-relaxed mb-3 last:mb-0">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
              em: ({ children }) => <em className="text-gray-700">{children}</em>,
              ul: ({ children }) => <ul className="list-disc pl-5 space-y-1 text-gray-700">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1 text-gray-700">{children}</ol>,
              li: ({ children }) => <li className="text-gray-700">{children}</li>,
            }}
          >
            {conversational_response}
          </ReactMarkdown>
        </div>
      </div>

      {/* Domain-specific panels */}
      {analysis?.domain === 'housing' && (
        <HDBResults a={analysis as HDBAnalysis} />
      )}
      {analysis?.domain === 'labour' && (
        <LabourResults a={analysis as LabourAnalysis} />
      )}
      {analysis?.domain === 'cross_domain' && (
        <CrossDomainResults a={analysis as CrossDomainAnalysis} />
      )}
    </div>
  )
}
