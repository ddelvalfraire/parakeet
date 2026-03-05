import { useEffect, useState, useMemo, useCallback } from 'react'
import { Link } from 'react-router'
import { api } from '@/api'
import { cn } from '@/lib/utils'
import {
  severityConfig,
  statusConfig,
  typography,
  spacing,
  layout,
} from '@/lib/styles'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import type { IncidentSummary, IncidentStatus, Severity } from '@/types'
import type { LucideIcon } from 'lucide-react'
import {
  AlertTriangle,
  ChevronRight,
  CircleCheck,
  Clock,
  Inbox,
  RefreshCw,
  Search,
  Server,
  ShieldAlert,
  Zap,
} from 'lucide-react'

type Filter = 'all' | 'active' | 'resolved'

const SEVERITY_ORDER: Record<Severity, number> = {
  P1: 0,
  P2: 1,
  P3: 2,
  P4: 3,
}

const SEVERITY_BG: Record<Severity, string> = {
  P1: 'bg-red-600 dark:bg-red-500',
  P2: 'bg-orange-600 dark:bg-orange-500',
  P3: 'bg-yellow-600 dark:bg-yellow-500',
  P4: 'bg-blue-600 dark:bg-blue-500',
}

const PIPELINE_STAGES: IncidentStatus[] = [
  'triaging',
  'investigating',
  'root_cause',
  'awaiting_approval',
  'resolving',
  'resolved',
]

function relativeTime(iso: string): string {
  const sec = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (sec < 60) return 'just now'
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  return `${Math.floor(hr / 24)}d ago`
}

// ---------------------------------------------------------------------------
// Metric card
// ---------------------------------------------------------------------------

type MetricVariant = 'danger' | 'warning' | 'success' | 'info' | 'neutral'

const metricIconColor: Record<MetricVariant, string> = {
  danger: 'text-red-600 dark:text-red-400',
  warning: 'text-amber-600 dark:text-amber-400',
  success: 'text-emerald-600 dark:text-emerald-400',
  info: 'text-blue-600 dark:text-blue-400',
  neutral: 'text-muted-foreground',
}

const metricDotColor: Record<MetricVariant, string> = {
  danger: 'bg-red-600 dark:bg-red-400',
  warning: 'bg-amber-600 dark:bg-amber-400',
  success: 'bg-emerald-600 dark:bg-emerald-400',
  info: 'bg-blue-600 dark:bg-blue-400',
  neutral: 'bg-muted-foreground',
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
  variant = 'neutral',
  pulse = false,
}: {
  icon: LucideIcon
  label: string
  value: number | string
  detail: string
  variant?: MetricVariant
  pulse?: boolean
}) {
  return (
    <Card className="gap-0 py-0">
      <div className="flex items-center gap-3 p-4">
        <div className={cn('rounded-lg bg-muted/80 p-2.5', metricIconColor[variant])}>
          <Icon className="size-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className={cn(typography.caption, 'uppercase tracking-wider font-medium')}>
            {label}
          </p>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-2xl font-bold tabular-nums leading-none">
              {value}
            </span>
            <span className={typography.caption}>{detail}</span>
            {pulse && (
              <span className="relative flex size-2 ml-1">
                <span
                  className={cn(
                    'absolute inline-flex size-full animate-ping rounded-full opacity-75',
                    metricDotColor[variant],
                  )}
                />
                <span
                  className={cn(
                    'relative inline-flex size-2 rounded-full',
                    metricDotColor[variant],
                  )}
                />
              </span>
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Stage pipeline
// ---------------------------------------------------------------------------

function StagePipeline({
  counts,
  loading,
}: {
  counts: Record<IncidentStatus, number>
  loading: boolean
}) {
  if (loading) {
    return (
      <Card className="gap-0 py-0 overflow-hidden">
        <div className="flex items-stretch divide-x divide-border">
          {PIPELINE_STAGES.map(stage => (
            <div
              key={stage}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-3"
            >
              <Skeleton className="size-2 rounded-full" />
              <Skeleton className="h-3 w-16 hidden sm:block" />
            </div>
          ))}
        </div>
      </Card>
    )
  }

  return (
    <Card className="gap-0 py-0 overflow-hidden">
      <div className="flex items-stretch divide-x divide-border">
        {PIPELINE_STAGES.map(stage => {
          const config = statusConfig[stage]
          const count = counts[stage]
          const isActive = count > 0 && stage !== 'resolved'
          const isResolved = stage === 'resolved'

          return (
            <Tooltip key={stage}>
              <TooltipTrigger asChild>
                <div
                  className={cn(
                    'flex-1 flex items-center justify-center gap-2 px-3 py-3 transition-colors cursor-default',
                    count > 0 && !isResolved && 'bg-accent/50',
                  )}
                >
                  <span className="relative flex shrink-0">
                    {isResolved && count > 0 ? (
                      <CircleCheck className="size-3.5 text-emerald-500" />
                    ) : (
                      <>
                        <span
                          className={cn(
                            'size-2 rounded-full',
                            count > 0 ? config.dot : 'bg-muted-foreground/20',
                          )}
                        />
                        {isActive && (
                          <span
                            className={cn(
                              'absolute inset-0 size-2 rounded-full animate-ping opacity-40',
                              config.dot,
                            )}
                          />
                        )}
                      </>
                    )}
                  </span>
                  <span
                    className={cn(
                      'text-xs font-medium whitespace-nowrap hidden sm:inline',
                      count > 0 ? 'text-foreground' : 'text-muted-foreground/60',
                    )}
                  >
                    {config.label}
                  </span>
                  {count > 0 && (
                    <span className="text-xs font-bold tabular-nums text-foreground">
                      {count}
                    </span>
                  )}
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                {config.label}: {count} incident{count !== 1 ? 's' : ''}
              </TooltipContent>
            </Tooltip>
          )
        })}
      </div>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Incident card
// ---------------------------------------------------------------------------

function IncidentCard({ incident }: { incident: IncidentSummary }) {
  const status = statusConfig[incident.status]
  const isActive = incident.status !== 'resolved'
  const isP1Active = incident.severity === 'P1' && isActive

  return (
    <Link
      to={`/incident/${incident.id}`}
      className={cn(
        'flex rounded-lg border bg-card overflow-hidden transition-all group',
        'hover:-translate-y-px hover:shadow-md',
        'focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50',
        isP1Active && 'ring-1 ring-red-500/20 dark:ring-red-500/30',
      )}
    >
      <div
        className={cn(
          'relative flex items-center justify-center w-12 shrink-0 text-xs font-black text-white tracking-wide',
          SEVERITY_BG[incident.severity],
          !isActive && 'opacity-50',
        )}
      >
        {isP1Active && (
          <span
            className={cn(
              'absolute inset-0 animate-pulse opacity-60',
              SEVERITY_BG[incident.severity],
            )}
          />
        )}
        <span className="relative">{incident.severity}</span>
      </div>

      <div className="flex-1 px-4 py-3 min-w-0">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-baseline gap-2 min-w-0">
            <span className={cn(typography.mono, 'font-semibold truncate')}>
              {incident.service}
            </span>
            <span className={cn(typography.caption, 'hidden sm:inline')}>
              {incident.environment}
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="flex items-center gap-1.5">
              {status.animate && (
                <span
                  className={cn(
                    'size-1.5 rounded-full animate-pulse',
                    status.dot,
                  )}
                />
              )}
              <span className="text-xs font-medium">
                {status.label}
              </span>
            </span>
            <span className="text-muted-foreground/30 select-none">&middot;</span>
            <time
              dateTime={incident.created_at}
              title={new Date(incident.created_at).toLocaleString()}
              className={cn(typography.caption, 'tabular-nums whitespace-nowrap')}
            >
              {relativeTime(incident.created_at)}
            </time>
            <ChevronRight className="size-3.5 text-muted-foreground/30 group-hover:text-muted-foreground transition-colors" />
          </div>
        </div>
        <p className={cn(typography.body, 'mt-1 text-muted-foreground line-clamp-1')}>
          {incident.summary}
        </p>
      </div>
    </Link>
  )
}

// ---------------------------------------------------------------------------
// Main dashboard
// ---------------------------------------------------------------------------

export default function Dashboard() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [, setTick] = useState(0)

  const fetchIncidents = useCallback(async () => {
    const res = await api.listIncidents()
    setIncidents(res.incidents)
  }, [])

  useEffect(() => {
    fetchIncidents()
      .catch(err =>
        setError(err instanceof Error ? err.message : 'Failed to load'),
      )
      .finally(() => setLoading(false))
  }, [fetchIncidents])

  useEffect(() => {
    const id = setInterval(() => {
      fetchIncidents().catch(() => {})
    }, 30_000)
    return () => clearInterval(id)
  }, [fetchIncidents])

  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 60_000)
    return () => clearInterval(id)
  }, [])

  const metrics = useMemo(() => {
    const active = incidents.filter(i => i.status !== 'resolved')
    const p1Active = active.filter(i => i.severity === 'P1')
    const p2Active = active.filter(i => i.severity === 'P2')
    const awaitingApproval = incidents.filter(
      i => i.status === 'awaiting_approval',
    )
    const servicesAffected = new Set(active.map(i => i.service))

    return {
      activeCount: active.length,
      p1Count: p1Active.length,
      p2Count: p2Active.length,
      criticalCount: p1Active.length + p2Active.length,
      awaitingCount: awaitingApproval.length,
      servicesAffected: servicesAffected.size,
    }
  }, [incidents])

  const stageCounts = useMemo(() => {
    const counts: Record<IncidentStatus, number> = {
      triaging: 0,
      investigating: 0,
      root_cause: 0,
      awaiting_approval: 0,
      resolving: 0,
      resolved: 0,
    }
    incidents.forEach(i => counts[i.status]++)
    return counts
  }, [incidents])

  const filtered = useMemo(() => {
    let list = incidents
    if (filter === 'active')
      list = list.filter(i => i.status !== 'resolved')
    if (filter === 'resolved')
      list = list.filter(i => i.status === 'resolved')
    if (search) {
      const q = search.toLowerCase()
      list = list.filter(
        i =>
          i.service.toLowerCase().includes(q) ||
          i.summary.toLowerCase().includes(q),
      )
    }
    return [...list].sort((a, b) => {
      const sev = SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
      return sev !== 0
        ? sev
        : new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
  }, [incidents, filter, search])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await fetchIncidents()
    } catch {}
    setRefreshing(false)
  }

  const handleRetry = () => {
    setError(null)
    setLoading(true)
    fetchIncidents()
      .catch(err =>
        setError(err instanceof Error ? err.message : 'Failed to load'),
      )
      .finally(() => setLoading(false))
  }

  if (error && incidents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="rounded-full bg-destructive/10 p-3 mb-3">
          <AlertTriangle className="size-6 text-destructive" />
        </div>
        <p className={typography.label}>Failed to load incidents</p>
        <p className={cn(typography.caption, 'mt-1')}>{error}</p>
        <Button variant="link" onClick={handleRetry} className="mt-4">
          Try again
        </Button>
      </div>
    )
  }

  return (
    <div className={spacing.section}>
      {/* Page header */}
      <div className={layout.pageHeader}>
        <div className="flex items-center gap-3">
          <h1 className={typography.h2}>Incidents</h1>
          {!loading && (
            <Badge
              variant="secondary"
              className={cn(
                'gap-1.5',
                metrics.activeCount > 0
                  ? 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                  : 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
              )}
              aria-live="polite"
            >
              {metrics.activeCount > 0 && (
                <span className="relative flex size-2">
                  <span
                    className={cn(
                      'absolute inline-flex size-full animate-ping rounded-full opacity-75',
                      severityConfig.P1.dot,
                    )}
                  />
                  <span
                    className={cn(
                      'relative inline-flex size-2 rounded-full',
                      severityConfig.P1.dot,
                    )}
                  />
                </span>
              )}
              {metrics.activeCount} active
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            handleRefresh()
          }}
          disabled={refreshing}
          aria-label="Refresh incidents"
        >
          <RefreshCw
            className={cn('size-3.5', refreshing && 'animate-spin')}
          />
          Refresh
        </Button>
      </div>

      {/* Stats overview */}
      {loading ? (
        <div className={layout.cardGridWide}>
          {Array.from({ length: 4 }, (_, i) => (
            <Card key={i} className="gap-0 py-0">
              <div className="flex items-center gap-3 p-4">
                <Skeleton className="size-9 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-6 w-10" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className={layout.cardGridWide}>
          <MetricCard
            icon={Zap}
            label="Active"
            value={metrics.activeCount}
            detail={metrics.activeCount === 1 ? 'incident' : 'incidents'}
            variant={metrics.activeCount > 0 ? 'warning' : 'success'}
            pulse={metrics.activeCount > 0}
          />
          <MetricCard
            icon={ShieldAlert}
            label="Critical"
            value={metrics.criticalCount}
            detail={
              metrics.criticalCount === 0
                ? 'none active'
                : `${metrics.p1Count} P1 · ${metrics.p2Count} P2`
            }
            variant={
              metrics.p1Count > 0
                ? 'danger'
                : metrics.p2Count > 0
                  ? 'warning'
                  : 'neutral'
            }
            pulse={metrics.p1Count > 0}
          />
          <MetricCard
            icon={Clock}
            label="Awaiting"
            value={metrics.awaitingCount}
            detail="need approval"
            variant={metrics.awaitingCount > 0 ? 'warning' : 'neutral'}
          />
          <MetricCard
            icon={Server}
            label="Services"
            value={metrics.servicesAffected}
            detail="affected"
            variant={
              metrics.servicesAffected > 2
                ? 'warning'
                : metrics.servicesAffected > 0
                  ? 'info'
                  : 'neutral'
            }
          />
        </div>
      )}

      {/* Stage pipeline */}
      <StagePipeline counts={stageCounts} loading={loading} />

      {/* Filter toolbar */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <Tabs
          value={filter}
          onValueChange={v => setFilter(v as Filter)}
        >
          <TabsList>
            <TabsTrigger value="all">
              All
              <span className="ml-1 text-xs opacity-60">
                {incidents.length}
              </span>
            </TabsTrigger>
            <TabsTrigger value="active">
              Active
              <span className="ml-1 text-xs opacity-60">
                {metrics.activeCount}
              </span>
            </TabsTrigger>
            <TabsTrigger value="resolved">
              Resolved
              <span className="ml-1 text-xs opacity-60">
                {incidents.length - metrics.activeCount}
              </span>
            </TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground pointer-events-none" />
          <Input
            type="search"
            placeholder="Filter services..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="h-8 w-48 pl-8"
            aria-label="Filter incidents by service or summary"
          />
        </div>
      </div>

      {/* Incident list */}
      {loading ? (
        <div
          className={spacing.stackTight}
          aria-busy="true"
          aria-label="Loading incidents"
        >
          {Array.from({ length: 4 }, (_, i) => (
            <div
              key={i}
              className="flex rounded-lg border bg-card overflow-hidden"
            >
              <Skeleton className="w-12 shrink-0 rounded-none" />
              <div className="flex-1 px-4 py-3">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-4 w-36" />
                  <Skeleton className="h-3 w-16" />
                  <div className="ml-auto flex items-center gap-2">
                    <Skeleton className="h-3 w-20" />
                    <Skeleton className="h-3 w-10" />
                  </div>
                </div>
                <Skeleton className="mt-2 h-3.5 w-3/4" />
              </div>
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-3 mb-3">
            {filter === 'active' && !search ? (
              <CircleCheck className="size-6 text-emerald-500" />
            ) : (
              <Inbox className="size-6 text-muted-foreground" />
            )}
          </div>
          <p className={typography.label}>
            {search
              ? 'No matching incidents'
              : filter === 'active'
                ? 'All clear'
                : filter === 'resolved'
                  ? 'No resolved incidents'
                  : 'No incidents'}
          </p>
          <p className={cn(typography.caption, 'mt-1')}>
            {search
              ? `Nothing matches "${search}".`
              : filter === 'active'
                ? 'No active incidents right now.'
                : filter === 'resolved'
                  ? 'No incidents have been resolved yet.'
                  : 'No incidents to display.'}
          </p>
        </div>
      ) : (
        <div className={spacing.stackTight}>
          {filtered.map(incident => (
            <IncidentCard key={incident.id} incident={incident} />
          ))}
        </div>
      )}
    </div>
  )
}
