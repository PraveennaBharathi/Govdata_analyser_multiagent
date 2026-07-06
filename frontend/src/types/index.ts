export interface WorkflowStep {
  step: string
  label?: string
  icon?: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  duration_ms?: number
  timestamp?: string
  details?: string
}

// ── HDB ──────────────────────────────────────────────────────────────────────

export interface HDBSummaryStats {
  total_transactions: number
  years_covered: string
  overall_median_price: number
  price_change_pct: number
  most_expensive_town: string
  most_affordable_town: string
  most_affordable_price: number
  top_flat_type: string
  high_floor_premium_pct: number
}

export interface StoreyRow {
  band: string
  median_price: number
  transactions: number
}

export interface PSMRow {
  flat_type: string
  median_psm: number
}

export interface MomentumRow {
  town: string
  price_2020_22: number
  price_2023_25: number
  momentum_pct: number
}

export interface TownRow {
  town: string
  median_price: number
}

export interface FlatTypeRow {
  flat_type: string
  median_price: number
}

export interface HDBAnalysis {
  status: string
  domain: 'housing'
  conversational_response: string
  chart: string
  town_summary: TownRow[]
  town_summary_bottom: TownRow[]
  flat_type_summary: FlatTypeRow[]
  storey_summary: StoreyRow[]
  psm_summary: PSMRow[]
  town_momentum: MomentumRow[]
  insights: string[]
  summary_statistics: HDBSummaryStats
}

// ── Labour ───────────────────────────────────────────────────────────────────

export interface LabourSummaryStats {
  labour_health_score: number
  health_status: 'Healthy' | 'Caution' | 'Stressed'
  latest_year: number
  datasets_analysed: string[]
  metric_scores: Record<string, number>
}

export interface LabourAnalysis {
  status: string
  domain: 'labour'
  conversational_response: string
  chart: string
  insights: string[]
  yearly_metrics: Record<string, Array<{ year: number; value: number }>>
  composite_score: {
    composite: Record<number, number>
    per_metric: Record<string, Record<number, number>>
  }
  summary_statistics: LabourSummaryStats
}

// ── Cross-Domain ──────────────────────────────────────────────────────────────

export interface CrossDomainSummaryStats {
  years_analyzed: number
  year_range: string
  hdb_price_change_pct: number
  labour_score_change: number
  pearson_r_hdb_labour: number
  correlation_strength: string
  key_finding: string
}

export interface CrossDomainRow {
  year: number
  hdb_median: number
  labour_score: number
  unemployment_rate?: number
  retrenchments?: number
}

export interface CrossDomainAnalysis {
  status: string
  domain: 'cross_domain'
  conversational_response: string
  chart: string
  insights: string[]
  correlation_data: CrossDomainRow[]
  correlations: Record<string, number>
  summary_statistics: CrossDomainSummaryStats
}

// ── Union ─────────────────────────────────────────────────────────────────────

export type DomainAnalysis = HDBAnalysis | LabourAnalysis | CrossDomainAnalysis

export interface ResultPayload {
  query: string
  conversational_response: string
  parsed_query: Record<string, unknown>
  analysis_plan: string[]
  extraction_summary: {
    status: string
    records_count: number
    sources: string[]
  }
  analysis: DomainAnalysis
  structured_report: null
  status: string
}

// ── API response wrappers ─────────────────────────────────────────────────────

export interface QueryResult {
  status: string
  parsed_query?: Record<string, unknown>
  analysis_plan?: string[]
  result?: ResultPayload
  workflow_steps?: WorkflowStep[]
}

export interface TaskStatus {
  task_id: string
  state: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE'
  status: string
  progress?: number
  query_id?: number
  result?: QueryResult
  error?: string
}

export interface HealthStatus {
  status: string
  timestamp: string
  services: Record<string, string>
}

// Legacy compat — api.ts references these
export interface Query {
  id: number
  user_query: string
  status: string
  created_at: string
  completed_at?: string
  parsed_query?: Record<string, unknown>
  result?: QueryResult
}
