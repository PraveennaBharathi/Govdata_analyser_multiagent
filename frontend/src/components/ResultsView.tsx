'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { QueryResult } from '@/types'
import { BarChart3, Download, FileText, TrendingUp, Target } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ResultsViewProps {
  result?: QueryResult
  queryId?: number
  onExport?: (format: 'json' | 'csv') => void
}

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

  const { conversational_response, analysis, structured_report } = result.result

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Conversational Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-600" />
              Analysis Summary
            </CardTitle>
            {onExport && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onExport('json')}
                >
                  <Download className="h-4 w-4 mr-2" />
                  JSON
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onExport('csv')}
                >
                  <Download className="h-4 w-4 mr-2" />
                  CSV
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
            {conversational_response}
          </p>
        </CardContent>
      </Card>

      {/* Statistics */}
      {analysis?.statistics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Key Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(analysis.statistics).map(([key, value]) => (
                <div key={key} className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 capitalize">
                    {key.replace(/_/g, ' ')}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {typeof value === 'number' ? value.toFixed(2) : value}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Patterns */}
      {analysis?.patterns && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-purple-600" />
              Detected Patterns
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(analysis.patterns).map(([key, value]) => (
                <div key={key} className="flex items-start gap-3">
                  <div className="h-2 w-2 bg-purple-500 rounded-full mt-2" />
                  <div>
                    <p className="font-medium text-gray-900 capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                    <p className="text-gray-600">
                      {typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Correlations */}
      {analysis?.correlations?.strong_correlations && 
       analysis.correlations.strong_correlations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Strong Correlations</CardTitle>
            <CardDescription>
              Significant relationships found in the data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analysis.correlations.strong_correlations.map((corr, idx) => (
                <div
                  key={idx}
                  className={cn(
                    "p-4 rounded-lg border-l-4",
                    corr.correlation > 0 
                      ? "bg-green-50 border-green-500"
                      : "bg-red-50 border-red-500"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">
                        {corr.metric1} ↔ {corr.metric2}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {corr.strength} correlation
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold">
                        {(corr.correlation * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Visualizations */}
      {(analysis?.chart || analysis?.correlation_heatmap) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              Visualizations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {analysis.chart && (
              <div>
                <h4 className="font-medium mb-3">Trend Analysis</h4>
                <img
                  src={`data:image/png;base64,${analysis.chart}`}
                  alt="Trend Chart"
                  className="w-full rounded-lg border"
                />
              </div>
            )}
            {analysis.correlation_heatmap && (
              <div>
                <h4 className="font-medium mb-3">Correlation Heatmap</h4>
                <img
                  src={`data:image/png;base64,${analysis.correlation_heatmap}`}
                  alt="Correlation Heatmap"
                  className="w-full rounded-lg border"
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Structured Report */}
      {structured_report && (
        <Card>
          <CardHeader>
            <CardTitle>Detailed Report</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Executive Summary */}
            <div>
              <h3 className="font-semibold text-lg mb-2">Executive Summary</h3>
              <p className="text-gray-700">{structured_report.executive_summary}</p>
            </div>

            {/* Key Findings */}
            {structured_report.key_findings && structured_report.key_findings.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-2">Key Findings</h3>
                <ul className="space-y-2">
                  {structured_report.key_findings.map((finding, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold">{idx + 1}.</span>
                      <span className="text-gray-700">{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommendations */}
            {structured_report.recommendations && structured_report.recommendations.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-2">Policy Recommendations</h3>
                <div className="space-y-3">
                  {structured_report.recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        "p-4 rounded-lg border-l-4",
                        rec.priority === 'high' && "bg-red-50 border-red-500",
                        rec.priority === 'medium' && "bg-yellow-50 border-yellow-500",
                        rec.priority === 'low' && "bg-blue-50 border-blue-500"
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <h4 className="font-medium text-gray-900">{rec.title}</h4>
                        <span className={cn(
                          "px-2 py-1 text-xs rounded-full font-medium",
                          rec.priority === 'high' && "bg-red-100 text-red-700",
                          rec.priority === 'medium' && "bg-yellow-100 text-yellow-700",
                          rec.priority === 'low' && "bg-blue-100 text-blue-700"
                        )}>
                          {rec.priority}
                        </span>
                      </div>
                      <p className="text-gray-600 mt-2">{rec.description}</p>
                      <p className="text-sm text-gray-500 mt-2">
                        <strong>Rationale:</strong> {rec.rationale}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Data Sources */}
            {structured_report.data_sources && structured_report.data_sources.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-2">Data Sources</h3>
                <div className="space-y-2">
                  {structured_report.data_sources.map((source, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-900">{source.name}</p>
                      <p className="text-sm text-gray-600 mt-1">{source.description}</p>
                      <p className="text-xs text-gray-500 mt-1 italic">{source.citation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
