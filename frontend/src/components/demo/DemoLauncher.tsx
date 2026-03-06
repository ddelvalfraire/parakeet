import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { api } from '@/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { FlaskConical, Play, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { DemoScenario } from '@/types'

const LANG_COLORS: Record<string, string> = {
  go: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-950 dark:text-cyan-300',
  javascript: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300',
  python: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
}

const SEV_COLORS: Record<string, string> = {
  P1: 'bg-red-600 text-white',
  P2: 'bg-orange-600 text-white',
  P3: 'bg-yellow-600 text-white',
}

export default function DemoLauncher() {
  const navigate = useNavigate()
  const [scenarios, setScenarios] = useState<DemoScenario[]>([])
  const [loading, setLoading] = useState(true)
  const [launching, setLaunching] = useState<string | null>(null)
  const [resetting, setResetting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchScenarios = useCallback(async () => {
    try {
      const res = await api.listScenarios()
      setScenarios(res.scenarios)
    } catch {
      // Silently fail — demo features are optional
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchScenarios()
  }, [fetchScenarios])

  async function handleLaunch(scenarioId: string) {
    setLaunching(scenarioId)
    setError(null)
    try {
      const res = await api.startDemo({ scenario_id: scenarioId })
      navigate(`/incident/${res.incident.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to launch demo')
      setLaunching(null)
    }
  }

  async function handleReset() {
    setResetting(true)
    try {
      await api.resetDemo()
    } catch {
      // ignore
    } finally {
      setResetting(false)
    }
  }

  if (loading) {
    return (
      <Card className="p-4 gap-0">
        <div className="flex items-center gap-2 mb-3">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 w-32" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[1, 2, 3].map(i => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
      </Card>
    )
  }

  if (scenarios.length === 0) return null

  return (
    <Card className="p-4 gap-0">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FlaskConical className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          <span className="text-sm font-semibold">Live Demo</span>
          <span className="text-xs text-muted-foreground">
            Launch a scenario to see AI-powered remediation in action
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReset}
          disabled={resetting}
          className="text-xs"
        >
          <RotateCcw className={cn('h-3 w-3', resetting && 'animate-spin')} />
          Reset
        </Button>
      </div>

      {error && (
        <p className="text-xs text-destructive mb-2">{error}</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {scenarios.map(scenario => (
          <div
            key={scenario.id}
            className="rounded-lg border bg-card p-3 space-y-2 hover:border-foreground/20 transition-colors"
          >
            <div className="flex items-center gap-1.5 flex-wrap">
              <Badge className={cn('text-[10px] px-1.5 py-0', SEV_COLORS[scenario.severity])}>
                {scenario.severity}
              </Badge>
              <Badge variant="secondary" className={cn('text-[10px] px-1.5 py-0', LANG_COLORS[scenario.language])}>
                {scenario.language}
              </Badge>
            </div>
            <h4 className="text-xs font-semibold leading-tight">
              {scenario.title}
            </h4>
            <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
              {scenario.service} — {scenario.description}
            </p>
            <Button
              size="sm"
              variant="outline"
              className="w-full h-7 text-xs"
              disabled={launching !== null}
              onClick={() => handleLaunch(scenario.id)}
            >
              {launching === scenario.id ? (
                'Launching...'
              ) : (
                <>
                  <Play className="h-3 w-3 mr-1" />
                  Launch
                </>
              )}
            </Button>
          </div>
        ))}
      </div>
    </Card>
  )
}
