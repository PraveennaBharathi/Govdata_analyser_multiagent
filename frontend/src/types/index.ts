export interface Query {
  id: number
  user_query: string
  status: 'pending' | 'queued' | 'processing' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
  parsed_query?: ParsedQuery
  result?: QueryResult
}

export interface ParsedQuery {
  intent: string
  entities: string[]
  time_period?: {
    start: string
    end: string
  }
  metrics?: string[]
}

export interface QueryResult {
  status: string
  parsed_query?: ParsedQuery
  analysis_plan?: string[]
  result?: AnalysisResult
  workflow_steps?: WorkflowStep[]
}

export interface AnalysisResult {
  conversational_response: string
  analysis: Analysis
  structured_report?: StructuredReport
}

export interface Analysis {
  status: string
  summary: string
  statistics?: Statistics
  correlations?: Correlations
  patterns?: Patterns
  insights?: string[]
  chart?: string
  correlation_heatmap?: string
}

export interface Statistics {
  mean?: number
  median?: number
  std_dev?: number
  min?: number
  max?: number
  cagr?: number
  total_change?: number
}

export interface Correlations {
  correlation_matrix?: Record<string, Record<string, number>>
  strong_correlations?: Array<{
    metric1: string
    metric2: string
    correlation: number
    strength: string
  }>
}

export interface Patterns {
  overall_trend?: string
  growth_pattern?: string
  volatility?: string
  seasonal_patterns?: string[]
}

export interface StructuredReport {
  title: string
  executive_summary: string
  methodology: string
  key_findings: string[]
  data_sources: DataSource[]
  recommendations: Recommendation[]
  limitations: string[]
  conclusion: string
}

export interface DataSource {
  name: string
  description: string
  url: string
  citation: string
}

export interface Recommendation {
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  rationale: string
}

export interface WorkflowStep {
  step: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  timestamp?: string
  details?: string
}

export interface TaskStatus {
  task_id: string
  state: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE'
  status: string
  progress?: number
  total?: number
  query_id?: number
  result?: QueryResult
  error?: string
}

export interface HealthStatus {
  status: string
  timestamp: string
  services: {
    database: string
    llm_service: string
  }
}
