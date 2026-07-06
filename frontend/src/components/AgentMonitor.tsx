'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { WorkflowStep, TaskStatus } from '@/types'
import { CheckCircle2, Circle, Loader2, XCircle, Brain, Database, BarChart3, FileText, List } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AgentMonitorProps {
  taskStatus?: TaskStatus
  workflowSteps?: WorkflowStep[]
}

const ICON_MAP: Record<string, React.ElementType> = {
  brain: Brain,
  list: List,
  database: Database,
  chart: BarChart3,
  file: FileText,
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function AgentMonitor({ taskStatus, workflowSteps }: AgentMonitorProps) {
  const allSteps = workflowSteps || []
  // Hide steps that completed with 0ms — internal overhead not meaningful to show
  const steps = allSteps.filter(s => s.status !== 'completed' || (s.duration_ms ?? 0) > 0)
  const progress = taskStatus?.progress || 0

  const totalMs = allSteps.reduce((sum, s) => sum + (s.duration_ms ?? 0), 0)
  const showTiming = allSteps.length > 0 && totalMs > 0

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-600" />
            Agent Pipeline
          </span>
          {showTiming && (
            <span className="text-sm font-normal text-gray-500">
              Total: {formatDuration(totalMs)}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar — shown while processing */}
        {taskStatus && taskStatus.state !== 'SUCCESS' && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-gray-700">{taskStatus.status}</span>
              <span className="text-gray-500">{progress}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full transition-all duration-500 ease-out",
                  progress < 30 && "bg-red-500",
                  progress >= 30 && progress < 70 && "bg-yellow-500",
                  progress >= 70 && "bg-green-500"
                )}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Workflow Steps */}
        <div className="space-y-2">
          {steps.length === 0 && !taskStatus && (
            <div className="text-center py-8 text-gray-400">
              <Brain className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Submit a query to see agent activity</p>
            </div>
          )}

          {steps.length === 0 && taskStatus?.state === 'PROCESSING' && (
            <div className="space-y-2">
              {['Parse Query', 'Create Analysis Plan', 'Extract Data', 'Analyze Data', 'Generate Report'].map((label, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 border border-gray-200">
                  <Circle className="h-5 w-5 text-gray-300 flex-shrink-0" />
                  <span className="text-sm text-gray-400">{label}</span>
                </div>
              ))}
            </div>
          )}

          {steps.map((step, index) => {
            const Icon = ICON_MAP[step.icon ?? ''] ?? Circle
            const isCompleted = step.status === 'completed'
            const isInProgress = step.status === 'in_progress'
            const isFailed = step.status === 'failed'
            const label = step.label ?? step.step.replace(/_/g, ' ')

            return (
              <div
                key={index}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg border transition-all duration-300",
                  isCompleted && "bg-green-50 border-green-200",
                  isInProgress && "bg-blue-50 border-blue-200 animate-pulse",
                  isFailed && "bg-red-50 border-red-200",
                  !isCompleted && !isInProgress && !isFailed && "bg-gray-50 border-gray-200"
                )}
              >
                <div className="flex-shrink-0">
                  {isCompleted && <CheckCircle2 className="h-5 w-5 text-green-600" />}
                  {isInProgress && <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />}
                  {isFailed && <XCircle className="h-5 w-5 text-red-600" />}
                  {!isCompleted && !isInProgress && !isFailed && (
                    <Circle className="h-5 w-5 text-gray-300" />
                  )}
                </div>

                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <Icon className={cn(
                    "h-4 w-4 flex-shrink-0",
                    isCompleted && "text-green-600",
                    isInProgress && "text-blue-600",
                    isFailed && "text-red-600",
                    !isCompleted && !isInProgress && !isFailed && "text-gray-300"
                  )} />
                  <span className={cn(
                    "text-sm font-medium capitalize truncate",
                    isCompleted && "text-green-900",
                    isInProgress && "text-blue-900",
                    isFailed && "text-red-900",
                    !isCompleted && !isInProgress && !isFailed && "text-gray-400"
                  )}>
                    {label}
                  </span>
                </div>

                {/* Timing badge */}
                {isCompleted && step.duration_ms !== undefined && step.duration_ms > 0 && (
                  <span className="flex-shrink-0 text-xs font-mono bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                    {formatDuration(step.duration_ms)}
                  </span>
                )}
              </div>
            )
          })}
        </div>

        {/* Status pill */}
        {taskStatus && (
          <div className={cn(
            "p-3 rounded-lg border text-sm flex items-center gap-2",
            taskStatus.state === 'SUCCESS' && "bg-green-50 border-green-200 text-green-900",
            taskStatus.state === 'PROCESSING' && "bg-blue-50 border-blue-200 text-blue-900",
            taskStatus.state === 'FAILURE' && "bg-red-50 border-red-200 text-red-900",
            taskStatus.state === 'PENDING' && "bg-gray-50 border-gray-200 text-gray-900"
          )}>
            <div className={cn(
              "h-2 w-2 rounded-full flex-shrink-0",
              taskStatus.state === 'SUCCESS' && "bg-green-600",
              taskStatus.state === 'PROCESSING' && "bg-blue-600 animate-pulse",
              taskStatus.state === 'FAILURE' && "bg-red-600",
              taskStatus.state === 'PENDING' && "bg-gray-600"
            )} />
            <span className="font-medium">
              {taskStatus.state === 'SUCCESS' && 'Analysis Complete'}
              {taskStatus.state === 'PROCESSING' && 'Running pipeline...'}
              {taskStatus.state === 'FAILURE' && 'Pipeline Failed'}
              {taskStatus.state === 'PENDING' && 'Waiting to Start'}
            </span>
          </div>
        )}

        {/* LLM disclaimer */}
        <p className="text-xs text-gray-400 leading-relaxed pt-1 border-t border-gray-100">
          Powered by Ollama qwen2.5:14b (local) · Mistral API (primary) · Google Gemini (fallback)
        </p>
      </CardContent>
    </Card>
  )
}
