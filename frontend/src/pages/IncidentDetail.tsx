import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertTriangle, ArrowLeft, CircleAlert } from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/api'
import {
  severityConfig,
  statusConfig,
  typography,
  spacing,
  layout,
} from '@/lib/styles'
import { formatDateTime } from '@/lib/incident'
import TimelineFeed from '@/components/incident/TimelineFeed'
import IncidentPanel from '@/components/incident/IncidentPanel'
import { useIncidentWebSocket } from '@/hooks/useIncidentWebSocket'
import type { Incident, HumanDecision, TimelineEvent } from '@/types'

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generatingRetro, setGeneratingRetro] = useState(false)

  const fetchIncident = useCallback(() => {
    if (!id) return
    api
      .getIncident(id)
      .then((res) => setIncident(res.incident))
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
  }, [id])

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)
    api
      .getIncident(id)
      .then((res) => setIncident(res.incident))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  useIncidentWebSocket(id, fetchIncident)

  const isApproved = useMemo(
    () => incident?.timeline.some((e) => e.type === 'human_action') ?? false,
    [incident?.timeline],
  )

  const handleApprove = useCallback(
    async (optionId: string, notes: string) => {
      if (!id) return
      const res = await api.submitAction(id, {
        approved_option_id: optionId,
        approved_by: 'On-call Engineer',
        notes: notes || undefined,
      })
      if (res.success) {
        setIncident((prev) => {
          if (!prev) return prev
          const newEvent: TimelineEvent = {
            id: `evt-${crypto.randomUUID()}`,
            incident_id: prev.id,
            timestamp: new Date().toISOString(),
            stage: 'resolving',
            type: 'human_action',
            title: 'Remediation approved',
            payload: {
              approved_option_id: optionId,
              approved_by: 'On-call Engineer',
              notes: notes || null,
            } as HumanDecision,
          }
          return {
            ...prev,
            status: res.incident_status,
            timeline: [...prev.timeline, newEvent],
          }
        })
      }
    },
    [id],
  )

  const handleMergeFix = useCallback(
    async (notes: string) => {
      if (!id) return
      const res = await api.mergeFix(id, {
        approved_by: 'On-call Engineer',
        notes: notes || undefined,
      })
      if (res.success) {
        setIncident((prev) => {
          if (!prev) return prev
          const newEvent: TimelineEvent = {
            id: `evt-${crypto.randomUUID()}`,
            incident_id: prev.id,
            timestamp: new Date().toISOString(),
            stage: 'resolving',
            type: 'human_action',
            title: 'PR merged — fix deployed',
            payload: {
              approved_option_id: 'pr-fix',
              approved_by: 'On-call Engineer',
              notes: notes || null,
            } as HumanDecision,
          }
          return {
            ...prev,
            status: res.incident_status,
            timeline: [...prev.timeline, newEvent],
          }
        })
      }
    },
    [id],
  )

  const handleResolveManually = useCallback(
    async (explanation: string) => {
      if (!id) return
      const res = await api.resolveManually(id, {
        explanation,
        approved_by: 'On-call Engineer',
      })
      if (res.success) {
        setIncident((prev) => {
          if (!prev) return prev
          const newEvent: TimelineEvent = {
            id: `evt-${crypto.randomUUID()}`,
            incident_id: prev.id,
            timestamp: new Date().toISOString(),
            stage: 'resolving',
            type: 'human_action',
            title: 'Resolved manually',
            payload: {
              approved_option_id: 'resolve-manual',
              approved_by: 'On-call Engineer',
              notes: explanation,
            } as HumanDecision,
          }
          return {
            ...prev,
            status: res.incident_status,
            timeline: [...prev.timeline, newEvent],
          }
        })
      }
    },
    [id],
  )

  const handleGenerateRetro = useCallback(async () => {
    if (!id) return
    setGeneratingRetro(true)
    try {
      await api.generateRetro(id)
      navigate(`/incident/${id}/retro`)
    } catch {
      setError('Failed to generate post-mortem. Please try again.')
    } finally {
      setGeneratingRetro(false)
    }
  }, [id, navigate])

  if (!id) {
    return (
      <div className="py-12 text-center">
        <p className="text-sm text-destructive">No incident ID provided</p>
      </div>
    )
  }

  if (loading) return <DetailSkeleton />

  if (error || !incident) {
    return (
      <div className="space-y-4 py-12 text-center">
        <p className="text-sm text-destructive">
          {error ?? 'Incident not found'}
        </p>
        <Button variant="outline" size="sm" asChild>
          <Link to="/dashboard">Back to Dashboard</Link>
        </Button>
      </div>
    )
  }

  const sevCfg = severityConfig[incident.severity]
  const statCfg = statusConfig[incident.status]

  return (
    <div className={spacing.section}>
      {/* Back navigation */}
      <Button variant="ghost" size="sm" className="-ml-2 gap-1.5" asChild>
        <Link to="/dashboard">
          <ArrowLeft className="size-4" />
          Dashboard
        </Link>
      </Button>

      {/* Incident header card — severity-colored left accent */}
      <Card className={cn('border-l-4 py-0', sevCfg.border)}>
        <CardContent className="py-5">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2.5 flex-wrap">
                <Badge className={cn('font-semibold', sevCfg.badge)}>
                  {incident.severity} &mdash; {sevCfg.label}
                </Badge>
                <h1 className={typography.h2}>
                  Incident #{incident.id}
                </h1>
              </div>
              <p className={cn(typography.bodyLarge, 'mt-2 max-w-3xl')}>
                {incident.summary}
              </p>
            </div>
            <Badge
              variant="secondary"
              className={cn('mt-1 shrink-0 gap-1.5', statCfg.badge)}
            >
              <span
                className={cn(
                  'inline-block size-2 rounded-full',
                  statCfg.dot,
                  statCfg.animate && 'animate-pulse',
                )}
              />
              {statCfg.label}
            </Badge>
          </div>

          {/* Metadata strip */}
          <div className="mt-3 flex items-center gap-2 text-sm text-muted-foreground">
            <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
              {incident.service}
            </span>
            <span>&middot;</span>
            <span>{incident.environment}</span>
            <span>&middot;</span>
            <time className="tabular-nums">
              {formatDateTime(incident.created_at)}
            </time>
          </div>
        </CardContent>
      </Card>

      {/* Error / needs-input banner */}
      {incident.status === 'error' && (
        <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950/30">
          <CircleAlert className="size-5 shrink-0 text-red-600 dark:text-red-400" />
          <div>
            <p className="text-sm font-semibold text-red-800 dark:text-red-300">
              Pipeline stopped due to an agent error
            </p>
            <p className="text-xs text-muted-foreground">
              Review the timeline below for details. You may need to retry or
              resolve this incident manually.
            </p>
          </div>
        </div>
      )}
      {incident.status === 'needs_input' && (
        <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/30">
          <AlertTriangle className="size-5 shrink-0 text-amber-600 dark:text-amber-400" />
          <div>
            <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
              Agent needs human input to continue
            </p>
            <p className="text-xs text-muted-foreground">
              The agent could not complete a stage automatically. Review the
              timeline and provide the required input.
            </p>
          </div>
        </div>
      )}

      {/* Two-column layout */}
      <div className={layout.splitPanel}>
        {/* Left: Timeline */}
        <section>
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Timeline
          </h2>
          <TimelineFeed
            events={incident.timeline}
            incidentId={incident.id}
            currentStatus={incident.status}
            approved={isApproved}
            onApprove={handleApprove}
            onMergeFix={handleMergeFix}
            onResolveManually={handleResolveManually}
          />
        </section>

        {/* Right: Incident panel — sticky so it stays visible while scrolling timeline */}
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <IncidentPanel
            incident={incident}
            onGenerateRetro={handleGenerateRetro}
            generatingRetro={generatingRetro}
          />
        </aside>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function DetailSkeleton() {
  return (
    <div className={spacing.section}>
      <Skeleton className="h-8 w-28" />
      <Skeleton className="h-36 rounded-xl" />
      <div className={layout.splitPanel}>
        <div className="space-y-4">
          <Skeleton className="h-5 w-20" />
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-44 rounded-lg" />
          ))}
        </div>
        <div className="space-y-4">
          <Skeleton className="h-44 rounded-lg" />
          <Skeleton className="h-56 rounded-lg" />
        </div>
      </div>
    </div>
  )
}
