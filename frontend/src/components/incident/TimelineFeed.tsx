import { useMemo } from 'react'
import { cn } from '@/lib/utils'
import { statusConfig, type StatusStyle } from '@/lib/styles'
import { formatTime } from '@/lib/incident'
import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'
import TriageCard from './TriageCard'
import InvestigationCard from './InvestigationCard'
import RootCauseCard from './RootCauseCard'
import RemediationCard from './RemediationCard'
import HumanDecisionCard from './HumanDecisionCard'
import ResolvedCard from './ResolvedCard'
import SystemEventCard from './SystemEventCard'
import type {
  TimelineEvent,
  IncidentStatus,
  TriageResult,
  InvestigationResult,
  RootCauseResult,
  RemediationResult,
  HumanDecision,
  PostMortem,
} from '@/types'

const ACTIVE_STATUSES = new Set<IncidentStatus>([
  'triaging',
  'investigating',
  'root_cause',
  'remediating',
  'resolving',
])

const WORKING_LABELS: Partial<Record<IncidentStatus, string>> = {
  triaging: 'Classifying alert and assessing severity\u2026',
  investigating: 'Collecting evidence and analyzing logs\u2026',
  root_cause: 'Identifying root cause\u2026',
  remediating: 'Exploring code and planning remediation\u2026',
  resolving: 'Generating post-mortem\u2026',
}

interface Props {
  events: TimelineEvent[]
  incidentId: string
  currentStatus: IncidentStatus
  approved: boolean
  onApprove: (optionId: string, notes: string) => Promise<void>
  onMergeFix?: (notes: string) => Promise<void>
  onResolveManually?: (explanation: string) => Promise<void>
}

export default function TimelineFeed({
  events,
  incidentId,
  currentStatus,
  approved,
  onApprove,
  onMergeFix,
  onResolveManually,
}: Props) {
  const optionTitleMap = useMemo(() => {
    const remEvent = events.find((e) => e.stage === 'awaiting_approval')
    if (!remEvent) return new Map<string, string>()
    const options = (remEvent.payload as RemediationResult).options ?? []
    if (!options.length) return new Map<string, string>()
    return new Map(options.map((o) => [o.id, o.title]))
  }, [events])

  function renderCard(event: TimelineEvent) {
    if (event.type === 'human_action') {
      const decision = event.payload as HumanDecision
      return (
        <HumanDecisionCard
          payload={decision}
          optionTitle={optionTitleMap.get(decision.approved_option_id)}
        />
      )
    }

    if (event.type === 'system_event') {
      const payload = event.payload as { error?: string; stage?: string; detail?: string }
      return <SystemEventCard payload={payload} title={event.title} />
    }

    switch (event.stage) {
      case 'triaging':
        return <TriageCard payload={event.payload as TriageResult} />
      case 'investigating':
        return (
          <InvestigationCard
            payload={event.payload as InvestigationResult}
          />
        )
      case 'root_cause':
        return <RootCauseCard payload={event.payload as RootCauseResult} />
      case 'awaiting_approval':
        return (
          <RemediationCard
            payload={event.payload as RemediationResult}
            approved={approved}
            onApprove={onApprove}
            onMergeFix={onMergeFix}
            onResolveManually={onResolveManually}
          />
        )
      case 'resolved':
        return (
          <ResolvedCard
            payload={event.payload as PostMortem}
            incidentId={incidentId}
          />
        )
      default:
        return null
    }
  }

  const isWorking = ACTIVE_STATUSES.has(currentStatus)
  const workingLabel = WORKING_LABELS[currentStatus]
  const workingCfg = isWorking
    ? statusConfig[currentStatus as keyof typeof statusConfig]
    : null

  return (
    <div className="relative">
      {events.map((event, index) => {
        const cfg: StatusStyle = statusConfig[event.stage as keyof typeof statusConfig] ?? {
          label: event.stage,
          badge: 'bg-gray-100 text-gray-800 dark:bg-gray-900/40 dark:text-gray-300',
          icon: 'text-gray-600 dark:text-gray-400',
          dot: 'bg-gray-600 dark:bg-gray-400',
          animate: false,
        }

        const hasMore = index < events.length - 1 || isWorking

        return (
          <div key={event.id} className="relative flex gap-4 pb-8">
            {/* Vertical connecting line */}
            {hasMore && (
              <div className="absolute left-[11px] top-8 bottom-0 w-0.5 bg-border" />
            )}

            {/* Stage dot — larger ring with colored inner dot */}
            <div className="relative z-10 mt-1 flex size-6 shrink-0 items-center justify-center rounded-full bg-background ring-2 ring-border">
              <div
                className={cn('size-2.5 rounded-full', cfg.dot)}
              />
            </div>

            {/* Event content */}
            <div className="flex-1 min-w-0">
              {/* Header: timestamp + stage badge */}
              <div className="flex items-center gap-2 mb-1.5">
                <time className="font-mono text-xs tabular-nums text-muted-foreground">
                  {formatTime(event.timestamp)}
                </time>
                <Badge
                  variant="secondary"
                  className={cn('gap-1 px-1.5 py-0 text-[10px]', cfg.badge)}
                >
                  {cfg.animate && (
                    <span
                      className={cn(
                        'inline-block size-1 rounded-full animate-pulse',
                        cfg.dot,
                      )}
                    />
                  )}
                  {cfg.label}
                </Badge>
              </div>

              {/* Event title */}
              <p className="text-sm font-semibold mb-2">{event.title}</p>

              {/* Card content */}
              {renderCard(event)}
            </div>
          </div>
        )
      })}

      {/* Agent working indicator — shown at bottom when pipeline is actively processing */}
      {isWorking && workingCfg && (
        <div className="relative flex gap-4">
          {/* Pulsing dot */}
          <div className="relative z-10 mt-1 flex size-6 shrink-0 items-center justify-center rounded-full bg-background ring-2 ring-border">
            <div
              className={cn(
                'size-2.5 rounded-full animate-pulse',
                workingCfg.dot,
              )}
            />
          </div>

          {/* Working message */}
          <div className="flex items-center gap-2 min-w-0">
            <Loader2
              className={cn('size-3.5 animate-spin', workingCfg.icon)}
            />
            <p className="text-sm text-muted-foreground">
              {workingLabel}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
