'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Send, Loader2, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface QueryInputProps {
  onSubmit: (query: string) => void
  isLoading?: boolean
  className?: string
}

const EXAMPLE_QUERIES = [
  "Analyze employment trends from 2020 to 2024",
  "Show me GDP growth patterns over the last 5 years",
  "Compare unemployment rates across different sectors",
  "What are the key economic indicators for policy making?",
]

export function QueryInput({ onSubmit, isLoading = false, className }: QueryInputProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && !isLoading) {
      onSubmit(query.trim())
    }
  }

  const handleExampleClick = (example: string) => {
    setQuery(example)
  }

  return (
    <div className={cn('w-full space-y-4', className)}>
      {/* Main Input */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          <div className="absolute left-4 flex items-center pointer-events-none">
            <Sparkles className="h-5 w-5 text-blue-500" />
          </div>
          
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask me anything about government data... (e.g., 'Analyze employment trends from 2020 to 2024')"
            className={cn(
              "w-full min-h-[120px] pl-12 pr-24 py-4 text-base",
              "border-2 border-gray-200 rounded-xl",
              "focus:border-blue-500 focus:ring-4 focus:ring-blue-100",
              "transition-all duration-200",
              "resize-none",
              "placeholder:text-gray-400",
              isLoading && "opacity-50 cursor-not-allowed"
            )}
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
          />
          
          <div className="absolute right-4 bottom-4 flex items-center gap-2">
            <span className="text-xs text-gray-400">
              {query.length}/500
            </span>
            <Button
              type="submit"
              disabled={!query.trim() || isLoading}
              size="icon"
              className="rounded-lg"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </form>

      {/* Example Queries */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-gray-600">Try these examples:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              disabled={isLoading}
              className={cn(
                "px-3 py-1.5 text-sm rounded-full",
                "border border-gray-200 bg-white",
                "hover:border-blue-500 hover:bg-blue-50 hover:text-blue-700",
                "transition-all duration-200",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
