'use client'

import { useState } from 'react'
import { QueryInput } from '@/components/QueryInput'
import { AgentMonitor } from '@/components/AgentMonitor'
import { ResultsView } from '@/components/ResultsView'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api'
import { downloadBlob } from '@/lib/utils'
import { TaskStatus, QueryResult } from '@/types'
import { Sparkles, History, Github, ExternalLink } from 'lucide-react'
import Link from 'next/link'

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [taskStatus, setTaskStatus] = useState<TaskStatus>()
  const [result, setResult] = useState<QueryResult>()
  const [queryId, setQueryId] = useState<number>()

  const handleSubmitQuery = async (query: string) => {
    setIsLoading(true)
    setTaskStatus(undefined)
    setResult(undefined)
    setQueryId(undefined)

    try {
      // Submit async query
      const response = await apiClient.submitQueryAsync(query)
      setQueryId(response.query_id)

      // Poll for status
      await apiClient.pollTaskStatus(
        response.task_id,
        (status) => {
          setTaskStatus(status)
          
          // Update result if available
          if (status.state === 'SUCCESS' && status.result) {
            setResult(status.result)
          }
        },
        2000,
        60
      )
    } catch (error) {
      console.error('Query error:', error)
      alert('Failed to process query. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleExport = async (format: 'json' | 'csv') => {
    if (!queryId) return

    try {
      const blob = await apiClient.exportQuery(queryId, format)
      downloadBlob(blob, `analysis-${queryId}.${format}`)
    } catch (error) {
      console.error('Export error:', error)
      alert('Failed to export results.')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  GovData Analytics
                </h1>
                <p className="text-sm text-gray-600">AI-Powered Policy Analysis</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Link href="/history">
                <Button variant="outline" size="sm">
                  <History className="h-4 w-4 mr-2" />
                  History
                </Button>
              </Link>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="ghost" size="icon">
                  <Github className="h-5 w-5" />
                </Button>
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Welcome Card */}
          {!result && !isLoading && (
            <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-purple-50 animate-fade-in">
              <CardHeader>
                <CardTitle className="text-center text-2xl">
                  Welcome to GovData Analytics
                </CardTitle>
              </CardHeader>
              <CardContent className="text-center space-y-4">
                <p className="text-gray-700 text-lg">
                  Ask questions about government data in natural language and get AI-powered insights
                </p>
                <div className="flex flex-wrap justify-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-green-500 rounded-full" />
                    <span>Real-time AI agents</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-blue-500 rounded-full" />
                    <span>Interactive visualizations</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 bg-purple-500 rounded-full" />
                    <span>Policy recommendations</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Query Input */}
          <QueryInput onSubmit={handleSubmitQuery} isLoading={isLoading} />

          {/* Two Column Layout */}
          {(isLoading || result) && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Agent Monitor - Left Column */}
              <div className="lg:col-span-1">
                <AgentMonitor
                  taskStatus={taskStatus}
                  workflowSteps={result?.workflow_steps}
                />
              </div>

              {/* Results - Right Column */}
              <div className="lg:col-span-2">
                <ResultsView
                  result={result}
                  queryId={queryId}
                  onExport={handleExport}
                />
              </div>
            </div>
          )}

          {/* Features Section */}
          {!result && !isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
              <Card className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Sparkles className="h-5 w-5 text-blue-600" />
                    Natural Language
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Ask questions in plain English. No need to learn complex query languages.
                  </p>
                </CardContent>
              </Card>

              <Card className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <ExternalLink className="h-5 w-5 text-green-600" />
                    Real-Time Monitoring
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Watch AI agents work in real-time with live progress updates and reasoning steps.
                  </p>
                </CardContent>
              </Card>

              <Card className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <History className="h-5 w-5 text-purple-600" />
                    Analysis History
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">
                    Browse previous analyses and export results in JSON or CSV format.
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm mt-16">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-sm text-gray-600">
            <p>Built with Next.js, TypeScript, and Tailwind CSS</p>
            <p className="mt-1">Powered by AI agents with multi-cloud LLM integration</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
