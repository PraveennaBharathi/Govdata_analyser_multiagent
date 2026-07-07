'use client'

import { useState } from 'react'
import { QueryInput } from '@/components/QueryInput'
import { AgentMonitor } from '@/components/AgentMonitor'
import { ResultsView } from '@/components/ResultsView'
import { LiveCityView } from '@/components/LiveCityView'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api'
import { downloadBlob } from '@/lib/utils'
import { TaskStatus, QueryResult } from '@/types'
import {
  Sparkles, Home as HomeIcon, Briefcase, Train, Building2, Users,
  Wind, GraduationCap, Network, ChevronRight, Clock, Loader2, Cpu
} from 'lucide-react'
import { cn } from '@/lib/utils'

// ── Model config ──────────────────────────────────────────────────────────────

const MODELS = [
  { id: 'auto',          label: 'Auto',          sub: '3-tier routing' },
  { id: 'ollama',        label: 'Ollama',         sub: 'Local · qwen2.5' },
  { id: 'mistral-small', label: 'Mistral Small',  sub: 'Fast · routing' },
  { id: 'mistral-large', label: 'Mistral Large',  sub: 'Quality · narrative' },
  { id: 'magistral',     label: 'Magistral',      sub: 'Reasoning · CoT' },
  { id: 'gemini',        label: 'Gemini',         sub: 'Google · fallback' },
] as const

type ModelId = typeof MODELS[number]['id']

// ── Domain config ─────────────────────────────────────────────────────────────

type DomainId =
  | 'housing' | 'labour' | 'transport' | 'business'
  | 'demographics' | 'live_city' | 'education' | 'cross_domain'

interface Domain {
  id: DomainId
  label: string
  icon: React.ElementType
  live: boolean
  description: string
  examples: string[]
  placeholder: string
  comingSoon?: string[]
}

const DOMAINS: Domain[] = [
  {
    id: 'housing',
    label: 'Housing',
    icon: HomeIcon,
    live: true,
    description: 'HDB resale prices, trends, and town comparisons from 234k+ live transactions.',
    placeholder: 'Ask about HDB resale prices, town comparisons, flat types…',
    examples: [
      'Show HDB resale price trends from 2020 to 2024',
      'Compare 4-room flat prices across Singapore towns',
      'Which HDB towns have seen the fastest price growth?',
      'What is the average HDB resale price in Tampines?',
    ],
    comingSoon: ['URA private property', 'Rental index', 'Public vs private gap'],
  },
  {
    id: 'labour',
    label: 'Labour',
    icon: Briefcase,
    live: true,
    description: 'Composite labour health score across unemployment, retrenchments, recruitment, and long-term unemployment.',
    placeholder: 'Ask about unemployment, retrenchments, labour health…',
    examples: [
      "What is Singapore's current labour market health?",
      'How have retrenchments trended since 2020?',
      'Compare recruitment vs unemployment rates over time',
      'What is the long-term unemployment trend in Singapore?',
    ],
    comingSoon: ['Sector breakdown (60+ industries)', 'Resident vs PR split'],
  },
  {
    id: 'transport',
    label: 'Transport',
    icon: Train,
    live: false,
    description: 'MRT ridership, bus utilisation, and traffic flow patterns from LTA.',
    placeholder: 'Ask about MRT ridership, commuter trends…',
    examples: [
      'Which MRT lines have the highest ridership?',
      'How has bus ridership changed since COVID?',
      'Show commuter trends on the North-South Line',
    ],
    comingSoon: ['MRT ridership by station', 'Bus utilisation rates', 'Traffic flow data'],
  },
  {
    id: 'business',
    label: 'Business',
    icon: Building2,
    live: false,
    description: 'Company formations, dissolutions, and sector activity from ACRA.',
    placeholder: 'Ask about business formations, industry trends…',
    examples: [
      'How many new companies were formed in Singapore last year?',
      'Which sectors saw the most business formations?',
      'Show business formation trends since 2018',
    ],
    comingSoon: ['ACRA company registrations', 'Sector formation rates', 'Business dissolutions'],
  },
  {
    id: 'demographics',
    label: 'Demographics',
    icon: Users,
    live: false,
    description: 'Population age distribution, ethnic composition, and resident statistics from SingStat.',
    placeholder: 'Ask about population, age groups, ethnic breakdown…',
    examples: [
      'How is Singapore\'s population aging?',
      'Show resident population trends by age group',
      'What is the dependency ratio trend?',
    ],
    comingSoon: ['SingStat population data', 'Age pyramid', 'Ethnic composition'],
  },
  {
    id: 'live_city',
    label: 'Live City',
    icon: Wind,
    live: true,
    description: 'Real-time air quality (PSI), dengue clusters, and weather from NEA (no API key required).',
    placeholder: 'Ask about air quality, dengue, weather…',
    examples: [
      'What is Singapore\'s current air quality?',
      'Show active dengue clusters today',
      'Is the PSI in the healthy range?',
    ],
    comingSoon: ['Live PSI index', 'Dengue cluster map', '2-hour weather forecast'],
  },
  {
    id: 'education',
    label: 'Education',
    icon: GraduationCap,
    live: false,
    description: 'School enrollment, PSLE results, and post-secondary pathways.',
    placeholder: 'Ask about school enrollment, education outcomes…',
    examples: [
      'Show primary school enrollment trends',
      'What percentage of students go to polytechnics?',
    ],
    comingSoon: ['School enrollment data', 'PSLE cohort pathways', 'University intake'],
  },
  {
    id: 'cross_domain',
    label: 'Cross-Domain',
    icon: Network,
    live: true,
    description: 'Ask questions that span multiple datasets. Powered by magistral chain-of-thought reasoning.',
    placeholder: 'Ask a cross-domain question…',
    examples: [
      'Do retrenchments predict HDB price drops 6 months later?',
      'How does population aging correlate with HDB demand?',
      'Is there a link between MRT ridership and employment?',
    ],
    comingSoon: ['Magistral chain-of-thought reasoning', 'Multi-dataset correlation', 'Causal analysis'],
  },
]

// ── Sidebar ───────────────────────────────────────────────────────────────────

function Sidebar({
  active,
  onChange,
}: {
  active: DomainId
  onChange: (id: DomainId) => void
}) {
  return (
    <aside className="w-60 flex-shrink-0 bg-slate-900 min-h-screen flex flex-col border-r border-slate-800">
      {/* Brand */}
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 bg-gradient-to-br from-blue-500 to-violet-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/40">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="text-sm font-bold text-white tracking-tight">GovData</div>
            <div className="text-xs text-slate-400">Analytics Platform</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5">
        {DOMAINS.map((d) => {
          const Icon = d.icon
          const isActive = active === d.id
          return (
            <button
              key={d.id}
              onClick={() => onChange(d.id)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-150 text-sm',
                isActive
                  ? 'bg-blue-600 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
              )}
            >
              <Icon className={cn('h-4 w-4 flex-shrink-0', isActive ? 'text-white' : 'text-slate-500')} />
              <span className="flex-1">{d.label}</span>
              {d.live ? (
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 flex-shrink-0 shadow-sm shadow-emerald-400/50" title="Live" />
              ) : (
                <Clock className="h-3 w-3 text-slate-600 flex-shrink-0" />
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800 space-y-1">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Live data
          </span>
          <span className="flex items-center gap-1.5">
            <Clock className="h-3 w-3" /> Coming soon
          </span>
        </div>
        <p className="text-xs text-slate-600">data.gov.sg · MOM · NEA</p>
      </div>
    </aside>
  )
}

// ── Coming soon panel ─────────────────────────────────────────────────────────

function ComingSoon({ domain }: { domain: Domain }) {
  const Icon = domain.icon
  return (
    <div className="max-w-lg mx-auto mt-16 space-y-5 animate-fade-in">
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 px-8 py-10 text-center">
          <div className="h-16 w-16 rounded-2xl bg-white/10 flex items-center justify-center mx-auto mb-4">
            <Icon className="h-8 w-8 text-white/70" />
          </div>
          <h2 className="text-2xl font-bold text-white">{domain.label}</h2>
          <p className="text-slate-400 text-sm mt-2">{domain.description}</p>
        </div>
        <div className="px-8 py-6">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">What's coming</p>
          <div className="space-y-2">
            {(domain.comingSoon ?? []).map((item) => (
              <div key={item} className="flex items-center gap-2.5 text-sm text-slate-600">
                <ChevronRight className="h-4 w-4 text-blue-400 flex-shrink-0" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>
      <p className="text-center text-xs text-slate-400">
        Housing · Labour · Live City · Cross-Domain tabs are fully live now.
      </p>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Home() {
  const [activeDomain, setActiveDomain] = useState<DomainId>('housing')
  const [selectedModel, setSelectedModel] = useState<ModelId>('ollama')
  const [isLoading, setIsLoading] = useState(false)
  const [queryError, setQueryError] = useState<string>()
  const [taskStatus, setTaskStatus] = useState<TaskStatus>()
  const [result, setResult] = useState<QueryResult>()
  const [queryId, setQueryId] = useState<number>()

  const domain = DOMAINS.find((d) => d.id === activeDomain)!

  const handleTabChange = (id: DomainId) => {
    setActiveDomain(id)
    setResult(undefined)
    setTaskStatus(undefined)
    setQueryId(undefined)
  }

  const handleSubmitQuery = async (query: string) => {
    setIsLoading(true)
    setTaskStatus(undefined)
    setResult(undefined)
    setQueryError(undefined)

    try {
      const response = await apiClient.submitQueryAsync(query, selectedModel)
      setQueryId(response.query_id)

      await apiClient.pollTaskStatus(
        response.task_id,
        (status) => {
          setTaskStatus(status)
          if (status.state === 'SUCCESS' && status.result) {
            setResult(status.result)
          }
          if (status.state === 'FAILURE') {
            setQueryError(status.error ?? 'Analysis failed — check backend logs')
          }
        },
        2000,
        60
      )
    } catch (error) {
      console.error('Query error:', error)
      setQueryError(error instanceof Error ? error.message : 'Unexpected error — please try again')
    } finally {
      setIsLoading(false)
    }
  }

  const handleExport = async (format: 'json' | 'csv') => {
    if (!queryId) return
    try {
      const blob = await apiClient.exportQuery(queryId, format)
      downloadBlob(blob, `analysis-${queryId}.${format}`)
    } catch {}
  }

  return (
    <div className="min-h-screen flex bg-gray-50">
      <Sidebar active={activeDomain} onChange={handleTabChange} />

      <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
        {/* Top bar */}
        <header className="h-14 border-b bg-white shadow-sm flex items-center px-6 gap-3 flex-shrink-0 sticky top-0 z-10">
          <div className="h-7 w-7 rounded-lg bg-blue-50 flex items-center justify-center">
            <domain.icon className="h-4 w-4 text-blue-600" />
          </div>
          <h1 className="font-semibold text-gray-900">{domain.label} Intelligence</h1>
          {domain.live ? (
            <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-50 text-emerald-700 font-medium border border-emerald-200">
              ● Live
            </span>
          ) : (
            <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-400 border border-gray-200">
              Coming Soon
            </span>
          )}
          <div className="flex-1" />
          {/* Model selector */}
          <div className="flex items-center gap-2">
            <Cpu className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value as ModelId)}
              disabled={isLoading}
              className={cn(
                "text-xs border border-slate-200 rounded-lg bg-white px-2.5 py-1",
                "text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400",
                "cursor-pointer transition-colors hover:border-slate-300",
                isLoading && "opacity-50 cursor-not-allowed"
              )}
            >
              {MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label} — {m.sub}
                </option>
              ))}
            </select>
          </div>
        </header>

        <main className="flex-1 p-6">
          {!domain.live ? (
            <ComingSoon domain={domain} />
          ) : activeDomain === 'live_city' ? (
            <div className="max-w-4xl mx-auto">
              <LiveCityView />
            </div>
          ) : (
            <div className="max-w-6xl mx-auto space-y-6">
              {/* Query input */}
              <QueryInput
                onSubmit={handleSubmitQuery}
                isLoading={isLoading}
                examples={domain.examples}
                placeholder={domain.placeholder}
              />

              {/* Error banner */}
              {queryError && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-start gap-2">
                  <span className="font-semibold flex-shrink-0">Error:</span>
                  <span>{queryError}</span>
                </div>
              )}

              {/* Results area */}
              {(isLoading || result) && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-1">
                    <AgentMonitor
                      taskStatus={taskStatus}
                      workflowSteps={result?.workflow_steps}
                      modelPreference={result?.model_preference ?? selectedModel}
                    />
                  </div>
                  <div className="lg:col-span-2">
                    {isLoading && !result ? (
                      <div className="flex items-center justify-center py-24 text-gray-400">
                        <Loader2 className="h-8 w-8 animate-spin mr-3" />
                        <span>Running analysis pipeline…</span>
                      </div>
                    ) : (
                      <ResultsView
                        result={result}
                        queryId={queryId}
                        onExport={handleExport}
                      />
                    )}
                  </div>
                </div>
              )}

              {/* Welcome state */}
              {!isLoading && !result && (
                <div className="animate-fade-in">
                  <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                    <div className="bg-gradient-to-br from-slate-900 to-slate-800 px-8 py-10 flex items-center gap-6">
                      <div className="h-14 w-14 rounded-2xl bg-white/10 flex items-center justify-center flex-shrink-0">
                        <domain.icon className="h-7 w-7 text-white" />
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-white">{domain.label} Intelligence</h2>
                        <p className="text-slate-400 text-sm mt-1 max-w-lg">{domain.description}</p>
                      </div>
                    </div>
                    <div className="px-8 py-6">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Try asking</p>
                      <div className="flex flex-wrap gap-2">
                        {domain.examples.map((ex) => (
                          <button
                            key={ex}
                            onClick={() => handleSubmitQuery(ex)}
                            className="px-4 py-2 text-sm rounded-xl border border-slate-200 bg-slate-50 text-slate-700 hover:border-blue-400 hover:bg-blue-50 hover:text-blue-700 transition-all duration-150"
                          >
                            {ex}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
