import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router'
import { api } from '@/api'
import type { Incident } from '@/types/incident'
import type { PostMortem } from '@/types/agents'
import {
  severityConfig,
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
  Users,
  Network,
  ThumbsUp,
  ThumbsDown,
  Clover,
  FileText,
  Search,
} from 'lucide-react'

export default function Retrospective() {
  const { id } = useParams<{ id: string }>()
  const [retro, setRetro] = useState<PostMortem | null>(null)
  const [incident, setIncident] = useState<Incident | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    const controller = new AbortController()

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

      {/* Two-column layout: document + timeline */}
      <div className={layout.splitPanel}>
        {/* Left: Document content */}
        <div className={spacing.section}>
          {/* Executive Summary */}
          <section>
            <h2 className={cn(typography.h4, 'flex items-center gap-2 mb-3')}>
              <FileText className="size-5 text-muted-foreground" />
              Summary
            </h2>
            <p className={cn(typography.bodyLarge, 'leading-relaxed text-foreground')}>
              {retro.summary}
            </p>
          </section>

          <Separator />

          {/* Impact */}
          <section>
            <h2 className={cn(typography.h4, 'flex items-center gap-2 mb-3')}>
              <Users className="size-5 text-muted-foreground" />
              Impact
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Card className="transition-colors hover:bg-accent/50">
                <CardContent>
                  <span className={typography.label}>Users Affected</span>
                  <p className={cn(typography.h2, 'mt-2')}>
                    {retro.impact.users_affected}
                  </p>
                </CardContent>
              </Card>
              <Card className="transition-colors hover:bg-accent/50">
                <CardContent>
                  <span className={typography.label}>Services Degraded</span>
                  <p className={cn(typography.h2, 'mt-2')}>
                    {retro.impact.services_degraded.length}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {retro.impact.services_degraded.map((s) => (
                      <span
                        key={s}
                        className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-muted-foreground"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>

          <Separator />

          {/* Root Cause */}
          <section>
            <h2 className={cn(typography.h4, 'flex items-center gap-2 mb-3')}>
              <AlertTriangle className="size-5 text-amber-500" />
              Root Cause
            </h2>
            <p className={cn(typography.bodyLarge, 'leading-relaxed')}>
              {retro.root_cause}
            </p>
          </section>

          {/* Contributing Factors */}
          <section>
            <h2 className={cn(typography.h4, 'flex items-center gap-2 mb-3')}>
              <Search className="size-5 text-muted-foreground" />
              Contributing Factors
            </h2>
            <ul className="space-y-2">
              {retro.contributing_factors.map((factor, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="mt-2 inline-block size-1.5 shrink-0 rounded-full bg-amber-500" />
                  <p className={cn(typography.body, 'leading-relaxed')}>
                    {factor}
                  </p>
                </li>
              ))}
            </ul>
          </section>

          <Separator />

          {/* Remediation Taken */}
          <section>
            <h2 className={cn(typography.h4, 'flex items-center gap-2 mb-3')}>
              <Wrench className="size-5 text-muted-foreground" />
              Remediation
            </h2>
            <p className={cn(typography.body, 'leading-relaxed text-muted-foreground')}>
              {retro.remediation_taken}
            </p>
          </section>

          <Separator />

          {/* Lessons Learned */}
          <section>
            <h2 className={cn(typography.h4, 'mb-4')}>Lessons Learned</h2>
            <div className="space-y-4">
              <LessonsSection
                icon={<ThumbsUp className="size-4" />}
                iconColor="text-green-600 dark:text-green-400"
                title="What went well"
                items={retro.lessons_learned.went_well}
                dotColor="bg-green-600 dark:bg-green-400"
              />
              <LessonsSection
                icon={<ThumbsDown className="size-4" />}
                iconColor="text-red-600 dark:text-red-400"
                title="What went wrong"
                items={retro.lessons_learned.went_wrong}
                dotColor="bg-red-600 dark:bg-red-400"
              />
              <LessonsSection
                icon={<Clover className="size-4" />}
                iconColor="text-amber-600 dark:text-amber-400"
                title="Where we got lucky"
                items={retro.lessons_learned.got_lucky}
                dotColor="bg-amber-600 dark:bg-amber-400"
              />
            </div>
          </section>

          <Separator />

          {/* Action Items */}
          <section>
            <h2 className={cn(typography.h4, 'flex items-center gap-2 mb-3')}>
              <ShieldCheck className="size-5 text-muted-foreground" />
              Action Items
            </h2>
            <ul className={spacing.stack}>
              {retro.prevention.map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <Checkbox id={`action-${i}`} className="mt-0.5" />
                  <label
                    htmlFor={`action-${i}`}
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
          </section>
        </div>

        {/* Right: Timeline sidebar */}
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <Card>
            <CardHeader>
              <CardTitle className={cn(typography.h4, 'flex items-center gap-2')}>
                <Network className="size-5 text-muted-foreground" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
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

                  const displayTime = entry.time.includes('T')
                    ? formatTime(entry.time)
                    : entry.time

                  return (
                    <div key={i} className="relative flex gap-3">
                      <Icon
                        className={cn(
                          'absolute -left-8 top-0.5 size-[14px] shrink-0 -translate-x-1/2',
                          dotColor,
                        )}
                      />
                      <div className="min-w-0">
                        <span
                          className={cn(
                            'font-mono text-xs tabular-nums block',
                            isLast
                              ? 'font-semibold text-green-600 dark:text-green-400'
                              : 'text-muted-foreground',
                          )}
                        >
                          {displayTime}
                        </span>
                        <p
                          className={cn(
                            'text-sm leading-snug mt-0.5',
                            isLast &&
                              'font-semibold text-green-600 dark:text-green-400',
                          )}
                        >
                          {entry.event}
                        </p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Lessons Learned subsection
// ---------------------------------------------------------------------------

function LessonsSection({
  icon,
  iconColor,
  title,
  items,
  dotColor,
}: {
  icon: React.ReactNode
  iconColor: string
  title: string
  items: string[]
  dotColor: string
}) {
  if (items.length === 0) return null
  return (
    <Card>
      <CardContent>
        <div className="flex items-center gap-2 mb-2">
          <span className={iconColor}>{icon}</span>
          <span className={typography.label}>{title}</span>
        </div>
        <ul className="space-y-1.5">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-2.5">
              <span
                className={cn(
                  'mt-2 inline-block size-1.5 shrink-0 rounded-full',
                  dotColor,
                )}
              />
              <p className={cn(typography.body, 'leading-relaxed')}>{item}</p>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
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

      <div className={layout.splitPanel}>
        {/* Document skeleton */}
        <div className="space-y-6">
          <div className="space-y-2">
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
          <Skeleton className="h-px w-full" />
          <div className="grid gap-4 sm:grid-cols-2">
            <Skeleton className="h-28 rounded-lg" />
            <Skeleton className="h-28 rounded-lg" />
          </div>
          <Skeleton className="h-px w-full" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-28" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
          <Skeleton className="h-px w-full" />
          <div className="space-y-3">
            <Skeleton className="h-6 w-36" />
            <Skeleton className="h-24 rounded-lg" />
            <Skeleton className="h-24 rounded-lg" />
            <Skeleton className="h-20 rounded-lg" />
          </div>
        </div>
        {/* Timeline skeleton */}
        <Skeleton className="h-64 rounded-lg" />
      </div>
    </div>
  )
}
