import { useMemo } from 'react'
import { cn } from '@/lib/utils'
import { statusConfig, type StatusStyle } from '@/lib/styles'
import { formatTime } from '@/lib/incident'
import { Badge } from '@/components/ui/badge'
import TriageCard from './TriageCard'
import InvestigationCard from './InvestigationCard'
import RootCauseCard from './RootCauseCard'
import RemediationCard from './RemediationCard'
import HumanDecisionCard from './HumanDecisionCard'
import ResolvedCard from './ResolvedCard'
import type {
  TimelineEvent,
  TriageResult,
  InvestigationResult,
  RootCauseResult,
  RemediationResult,
  HumanDecision,
  PostMortem,
} from '@/types'

interface Props {
  events: TimelineEvent[]
  incidentId: string
  approved: boolean
  onApprove: (optionId: string, notes: string) => Promise<void>
  onMergeFix?: (notes: string) => Promise<void>
  onResolveManually?: (explanation: string) => Promise<void>
}

export default function TimelineFeed({
  events,
  incidentId,
  approved,
  onApprove,
  onMergeFix,
  onResolveManually,
}: Props) {
  const optionTitleMap = useMemo(() => {
    const remEvent = events.find((e) => e.stage === 'awaiting_approval')
    if (!remEvent) return new Map<string, string>()
    const options = (remEvent.payload as RemediationResult).options
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

        return (
          <div key={event.id} className="relative flex gap-4 pb-8 last:pb-0">
            {/* Vertical connecting line */}
            {index < events.length - 1 && (
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
    </div>
  )
}
