'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { WorkflowStep, TaskStatus } from '@/types'
import { CheckCircle2, Circle, Loader2, XCircle, Brain, Database, LineChart } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AgentMonitorProps {
  taskStatus?: TaskStatus
  workflowSteps?: WorkflowStep[]
}

const AGENT_ICONS = {
  parse: Brain,
  plan: Brain,
  extract: Database,
  analyze: LineChart,
  result: CheckCircle2,
}

export function AgentMonitor({ taskStatus, workflowSteps }: AgentMonitorProps) {
  const steps = workflowSteps || []
  const progress = taskStatus?.progress || 0

  return (
    <Card className="animate-fade-in">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-blue-600" />
          Agent Activity Monitor
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        {taskStatus && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-gray-700">
                {taskStatus.status}
              </span>
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
        <div className="space-y-3">
          {steps.length === 0 && !taskStatus && (
            <div className="text-center py-8 text-gray-400">
              <Brain className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>Submit a query to see agent activity</p>
            </div>
          )}

          {steps.map((step, index) => {
            const Icon = AGENT_ICONS[step.step as keyof typeof AGENT_ICONS] || Circle
            const isCompleted = step.status === 'completed'
            const isInProgress = step.status === 'in_progress'
            const isFailed = step.status === 'failed'

            return (
              <div
                key={index}
                className={cn(
                  "flex items-start gap-3 p-3 rounded-lg transition-all duration-300",
                  isCompleted && "bg-green-50 border border-green-200",
                  isInProgress && "bg-blue-50 border border-blue-200 animate-pulse",
                  isFailed && "bg-red-50 border border-red-200",
                  !isCompleted && !isInProgress && !isFailed && "bg-gray-50 border border-gray-200"
                )}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {isCompleted && <CheckCircle2 className="h-5 w-5 text-green-600" />}
                  {isInProgress && <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />}
                  {isFailed && <XCircle className="h-5 w-5 text-red-600" />}
                  {!isCompleted && !isInProgress && !isFailed && (
                    <Circle className="h-5 w-5 text-gray-400" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Icon className={cn(
                      "h-4 w-4",
                      isCompleted && "text-green-600",
                      isInProgress && "text-blue-600",
                      isFailed && "text-red-600",
                      !isCompleted && !isInProgress && !isFailed && "text-gray-400"
                    )} />
                    <h4 className={cn(
                      "font-medium capitalize",
                      isCompleted && "text-green-900",
                      isInProgress && "text-blue-900",
                      isFailed && "text-red-900",
                      !isCompleted && !isInProgress && !isFailed && "text-gray-600"
                    )}>
                      {step.step ? step.step.replace(/_/g, ' ') : 'Processing...'}
                    </h4>
                  </div>
                  
                  {step.details && (
                    <p className="text-sm text-gray-600 mt-1">{step.details}</p>
                  )}
                  
                  {step.timestamp && (
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Current State */}
        {taskStatus && (
          <div className={cn(
            "p-3 rounded-lg border text-sm",
            taskStatus.state === 'SUCCESS' && "bg-green-50 border-green-200 text-green-900",
            taskStatus.state === 'PROCESSING' && "bg-blue-50 border-blue-200 text-blue-900",
            taskStatus.state === 'FAILURE' && "bg-red-50 border-red-200 text-red-900",
            taskStatus.state === 'PENDING' && "bg-gray-50 border-gray-200 text-gray-900"
          )}>
            <div className="flex items-center gap-2">
              <div className={cn(
                "h-2 w-2 rounded-full",
                taskStatus.state === 'SUCCESS' && "bg-green-600",
                taskStatus.state === 'PROCESSING' && "bg-blue-600 animate-pulse",
                taskStatus.state === 'FAILURE' && "bg-red-600",
                taskStatus.state === 'PENDING' && "bg-gray-600"
              )} />
              <span className="font-medium">
                {taskStatus.state === 'SUCCESS' && 'Analysis Complete'}
                {taskStatus.state === 'PROCESSING' && 'Processing...'}
                {taskStatus.state === 'FAILURE' && 'Analysis Failed'}
                {taskStatus.state === 'PENDING' && 'Waiting to Start'}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
