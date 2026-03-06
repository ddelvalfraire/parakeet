import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router'
import { api } from '@/api'
import type { Incident } from '@/types/incident'
import type { PostMortem, PostMortemMetrics } from '@/types/agents'
import {
  severityConfig,
  serviceStatusConfig,
  typography,
  spacing,
  layout,
} from '@/lib/styles'
import { formatTime } from '@/lib/incident'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import {
  ArrowLeft,
  Clock,
  AlertTriangle,
  Wrench,
  ShieldCheck,
  CircleDot,
  CircleCheckBig,
  Circle,
  Flame,
  Activity,
  Timer,
  TrendingUp,
  Zap,
  Network,
} from 'lucide-react'

export default function Retrospective() {
  const { id } = useParams<{ id: string }>()
  const [retro, setRetro] = useState<PostMortem | null>(null)
  const [incident, setIncident] = useState<Incident | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    const controller = new AbortController()

    // Fetch both the retro and the incident context in parallel
    Promise.all([
      api.generateRetro(id),
      api.getIncident(id),
    ])
      .then(([retroRes, incidentRes]) => {
        if (!controller.signal.aborted) {
          setRetro(retroRes.post_mortem)
          setIncident(incidentRes.incident)
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : 'Failed to load post-mortem',
          )
        }
      })

    return () => controller.abort()
  }, [id])

  if (error) {
    return (
      <div className="flex items-center justify-center py-24">
        <Card className="max-w-md">
          <CardContent className="flex items-center gap-3 text-destructive">
            <AlertTriangle className="size-5 shrink-0" />
            <p className={typography.body}>{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!retro) {
    return <RetroSkeleton />
  }

  const sevConfig = severityConfig[retro.severity]
  const lastIndex = retro.timeline.length - 1
  const metrics = retro.impact.metrics

  return (
    <div className={spacing.section}>
      {/* Back navigation */}
      <Button variant="ghost" size="sm" className="-ml-2 gap-1.5" asChild>
        <Link to={id ? `/incident/${id}` : '/dashboard'}>
          <ArrowLeft className="size-4" />
          Back to Incident
        </Link>
      </Button>

      {/* Header Card */}
      <Card className={cn('overflow-hidden border-l-4', sevConfig.border)}>
        <CardContent className="py-5">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2.5 flex-wrap">
                <Badge className={cn('font-semibold', sevConfig.badge)}>
                  {retro.severity} &mdash; {sevConfig.label}
                </Badge>
                <h1 className={typography.h2}>{retro.title}</h1>
              </div>
              <p className="flex items-center gap-1.5 text-muted-foreground mt-2">
                <Clock className="size-4" />
                <span className={typography.body}>Duration: {retro.duration}</span>
              </p>
            </div>
          </div>

          {/* Incident context strip */}
          {incident && (
            <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
              <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                {incident.service}
              </span>
              <span>&middot;</span>
              <span>{incident.environment}</span>
              <span>&middot;</span>
              <span className="font-mono text-xs">#{incident.id}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Impact Dashboard */}
      {metrics ? (
        <ImpactDashboard metrics={metrics} />
      ) : (
        <ImpactFallback impact={retro.impact} />
      )}

      {/* Timeline */}
      <section>
        <h2 className={cn(typography.h4, 'mb-4')}>Timeline</h2>
        <div className={layout.timeline}>
          {retro.timeline.map((entry, i) => {
            const isFirst = i === 0
            const isLast = i === lastIndex
            const Icon = isLast
              ? CircleCheckBig
              : isFirst
                ? CircleDot
                : Circle
            const dotColor = isLast
              ? 'text-green-600 dark:text-green-400'
              : isFirst
                ? sevConfig.text
                : 'text-muted-foreground/40'

            // Format the timestamp if it looks like ISO
            const displayTime = entry.time.includes('T')
              ? formatTime(entry.time)
              : entry.time

            return (
              <div key={i} className="relative flex gap-4">
                <Icon
                  className={cn(
                    'absolute -left-8 top-0.5 size-[14px] shrink-0 -translate-x-1/2',
                    dotColor,
                  )}
                />
                <span
                  className={cn(
                    'font-mono text-xs w-20 shrink-0 pt-px tabular-nums',
                    isLast
                      ? 'font-semibold text-green-600 dark:text-green-400'
                      : 'text-muted-foreground',
                  )}
                >
                  {displayTime}
                </span>
                <p
                  className={cn(
                    typography.body,
                    isLast &&
                      'font-semibold text-green-600 dark:text-green-400',
                  )}
                >
                  {entry.event}
                </p>
              </div>
            )
          })}
        </div>
      </section>

      <Separator />

      {/* Root Cause */}
      <Card className="border-l-4 border-l-amber-500 dark:border-l-amber-600">
        <CardHeader className="pb-0">
          <CardTitle className={cn(typography.h4, 'flex items-center gap-2')}>
            <AlertTriangle className="size-5 text-amber-500" />
            Root Cause
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className={cn(typography.bodyLarge, 'leading-relaxed')}>
            {retro.root_cause}
          </p>
        </CardContent>
      </Card>

      {/* Remediation Taken */}
      <Card>
        <CardHeader className="pb-0">
          <CardTitle className={cn(typography.h4, 'flex items-center gap-2')}>
            <Wrench className="size-5 text-muted-foreground" />
            Remediation Taken
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className={cn(typography.body, 'text-muted-foreground')}>
            {retro.remediation_taken}
          </p>
        </CardContent>
      </Card>

      {/* Prevention */}
      <Card>
        <CardHeader className="pb-0">
          <CardTitle className={cn(typography.h4, 'flex items-center gap-2')}>
            <ShieldCheck className="size-5 text-muted-foreground" />
            Prevention
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className={spacing.stack}>
            {retro.prevention.map((item, i) => (
              <li key={i} className="flex items-start gap-3">
                <Checkbox id={`prevention-${i}`} className="mt-0.5" />
                <label
                  htmlFor={`prevention-${i}`}
                  className={cn(
                    typography.body,
                    'cursor-pointer select-none leading-relaxed',
                  )}
                >
                  {item}
                </label>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Impact Dashboard — 6 real operational metrics
// ---------------------------------------------------------------------------

function ImpactDashboard({ metrics }: { metrics: PostMortemMetrics }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <MetricCard
        icon={<Flame className="size-4" />}
        iconBg="bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400"
        label="Failed Requests"
        value={metrics.failed_requests.total}
        detail={`Peak ${metrics.failed_requests.peak_rate}`}
        accent="destructive"
      />
      <MetricCard
        icon={<Activity className="size-4" />}
        iconBg="bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400"
        label="Peak Error Rate"
        value={metrics.error_rate.peak}
        detail={`Baseline ${metrics.error_rate.baseline}`}
        accent="destructive"
      />
      <MetricCard
        icon={<TrendingUp className="size-4" />}
        iconBg="bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400"
        label="P99 Latency"
        value={metrics.latency_p99.peak}
        detail={`Baseline ${metrics.latency_p99.baseline}`}
        accent="warning"
      />
      <MetricCard
        icon={<Zap className="size-4" />}
        iconBg="bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-400"
        label="Est. Revenue Loss"
        value={metrics.revenue_loss.total}
        detail={metrics.revenue_loss.rate}
      />
      <MetricCard
        icon={<Timer className="size-4" />}
        iconBg="bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400"
        label="Time to Detect"
        value={metrics.time_to_detect}
        detail={`Resolved in ${metrics.time_to_resolve}`}
      />
      <ServiceHealthCard services={metrics.services_affected} />
    </div>
  )
}

function MetricCard({
  icon,
  iconBg,
  label,
  value,
  detail,
  accent,
}: {
  icon: React.ReactNode
  iconBg: string
  label: string
  value: string
  detail: string
  accent?: 'destructive' | 'warning'
}) {
  return (
    <Card
      className={cn(
        'relative overflow-hidden transition-colors hover:bg-accent/50',
        accent === 'destructive' &&
          'border-red-200 dark:border-red-900/50',
        accent === 'warning' &&
          'border-amber-200 dark:border-amber-900/50',
      )}
    >
      <CardContent>
        <div className="flex items-center gap-2.5">
          <span
            className={cn(
              'inline-flex size-7 items-center justify-center rounded-md',
              iconBg,
            )}
          >
            {icon}
          </span>
          <span className={typography.label}>{label}</span>
        </div>
        <p className={cn(typography.h2, 'mt-3 tabular-nums')}>{value}</p>
        <p className={cn(typography.caption, 'mt-1')}>{detail}</p>
      </CardContent>
    </Card>
  )
}

function ServiceHealthCard({
  services,
}: {
  services: PostMortemMetrics['services_affected']
}) {
  return (
    <Card className="transition-colors hover:bg-accent/50">
      <CardContent>
        <div className="flex items-center gap-2.5">
          <span className="inline-flex size-7 items-center justify-center rounded-md bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400">
            <Network className="size-4" />
          </span>
          <span className={typography.label}>Blast Radius</span>
        </div>
        <p className={cn(typography.h2, 'mt-3')}>
          {services.filter((s) => s.status !== 'healthy').length}
          <span className="ml-1.5 text-base font-normal text-muted-foreground">
            / {services.length} services
          </span>
        </p>
        <ul className="mt-2 space-y-1">
          {services.map((s) => {
            const cfg = serviceStatusConfig[s.status]
            return (
              <li
                key={s.name}
                className="flex items-center gap-2 text-xs"
              >
                <span
                  className={cn(
                    'inline-block size-1.5 rounded-full',
                    cfg.dot,
                    cfg.animate && 'animate-pulse',
                  )}
                />
                <span className="text-muted-foreground">{s.name}</span>
                <span className={cn('ml-auto font-medium', cfg.text)}>
                  {cfg.label}
                </span>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Fallback for older post-mortems without rich metrics
// ---------------------------------------------------------------------------

function ImpactFallback({
  impact,
}: {
  impact: PostMortem['impact']
}) {
  return (
    <div className={layout.cardGrid}>
      <Card className="transition-colors hover:bg-accent/50">
        <CardContent>
          <span className={typography.label}>Users Affected</span>
          <p className={cn(typography.h2, 'mt-2')}>{impact.users_affected}</p>
        </CardContent>
      </Card>
      <Card className="transition-colors hover:bg-accent/50">
        <CardContent>
          <span className={typography.label}>Revenue Loss</span>
          <p className={cn(typography.h2, 'mt-2')}>
            {impact.estimated_revenue_loss ?? 'N/A'}
          </p>
        </CardContent>
      </Card>
      <Card className="transition-colors hover:bg-accent/50">
        <CardContent>
          <span className={typography.label}>Services Degraded</span>
          <p className={cn(typography.h2, 'mt-2')}>
            {impact.services_degraded.length}
          </p>
          <p className={cn(typography.caption, 'mt-1')}>
            {impact.services_degraded.join(', ')}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function RetroSkeleton() {
  return (
    <div className={spacing.section}>
      <Skeleton className="h-8 w-36" />
      <Skeleton className="h-36 rounded-xl" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i}>
            <CardContent>
              <div className="flex items-center gap-2.5">
                <Skeleton className="size-7 rounded-md" />
                <Skeleton className="h-4 w-24" />
              </div>
              <Skeleton className="mt-3 h-8 w-28" />
              <Skeleton className="mt-2 h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="space-y-4">
        <Skeleton className="h-6 w-24" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-full max-w-md" />
          </div>
        ))}
      </div>
    </div>
  )
}
