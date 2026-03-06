import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Activity,
  AlertTriangle,
  Bell,
  CheckCircle2,
  Circle,
  CircleAlert,
  FileText,
  Radio,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { severityConfig, statusConfig } from '@/lib/styles'
import { formatTime } from '@/lib/incident'
import type { Incident, IncidentStatus } from '@/types'
import SimilarIncidentsCard from '@/components/incident/SimilarIncidentsCard'

const PIPELINE_ORDER: IncidentStatus[] = [
  'triaging',
  'investigating',
  'root_cause',
  'awaiting_approval',
  'resolving',
  'resolved',
]

const STAGE_INDEX: Record<IncidentStatus, number> = Object.fromEntries(
  PIPELINE_ORDER.map((key, i) => [key, i]),
) as Record<IncidentStatus, number>

interface Props {
  incident: Incident
  onGenerateRetro: () => void
  generatingRetro: boolean
}

export default function IncidentPanel({
  incident,
  onGenerateRetro,
  generatingRetro,
}: Props) {
  const isErrored = incident.status === 'error' || incident.status === 'needs_input'
  const currentIdx = isErrored
    ? PIPELINE_ORDER.length  // show all stages as incomplete
    : STAGE_INDEX[incident.status]
  const isResolved = incident.status === 'resolved'
  const sevCfg = severityConfig[incident.severity]
  const completedStages = isErrored
    ? new Set(incident.timeline.filter(e => e.type === 'agent_output').map(e => e.stage))
    : null

  return (
    <div className="space-y-4">
      {/* Alert origin — severity-colored top accent */}
      <div
        className={cn(
          'rounded-lg border border-t-[3px] bg-card p-4 space-y-3',
          sevCfg.border,
        )}
      >
        <div className="flex items-center gap-2">
          <Bell className="size-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Alert Origin</h3>
        </div>
        <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-xs">
          <span className="text-muted-foreground">Source</span>
          <span className="font-medium">{incident.alert.source}</span>
          <span className="text-muted-foreground">Metric</span>
          <span className="font-mono">{incident.alert.metric}</span>
          <span className="text-muted-foreground">Value</span>
          <span>
            <span className="font-semibold text-red-700 dark:text-red-400">
              {incident.alert.value}
            </span>
            <span className="text-muted-foreground">
              {' '}
              (threshold: {incident.alert.threshold})
            </span>
          </span>
          <span className="text-muted-foreground">Service</span>
          <span className="font-mono">{incident.alert.service}</span>
          <span className="text-muted-foreground">Environment</span>
          <Badge variant="secondary" className="w-fit text-[10px]">
            {incident.alert.environment}
          </Badge>
          <span className="text-muted-foreground">Fired at</span>
          <span className="tabular-nums">
            {formatTime(incident.alert.timestamp)}
          </span>
        </div>
      </div>

      {/* Pipeline stages */}
      <div className="rounded-lg border bg-card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Activity className="size-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Pipeline</h3>
          <span className={cn(
            'ml-auto text-xs tabular-nums',
            isErrored ? 'text-red-600 dark:text-red-400 font-medium' : 'text-muted-foreground',
          )}>
            {isErrored ? 'Stopped' : `${currentIdx + 1}/${PIPELINE_ORDER.length}`}
          </span>
        </div>
        <div className="space-y-0">
          {PIPELINE_ORDER.map((key, idx) => {
            const isComplete = isErrored
              ? completedStages?.has(key) ?? false
              : idx < currentIdx
            const isCurrent = !isErrored && idx === currentIdx
            const isFuture = isErrored ? !(completedStages?.has(key) ?? false) : idx > currentIdx
            // The first future stage in an errored pipeline is where it stopped
            const isFailedAt = isErrored && isFuture && (
              idx === 0 || (completedStages?.has(PIPELINE_ORDER[idx - 1]) ?? false)
            )

            return (
              <div key={key} className="flex items-center gap-3">
                {/* Connector line from previous stage */}
                <div className="flex w-5 flex-col items-center">
                  {idx > 0 && (
                    <div
                      className={cn(
                        'h-2 w-0.5',
                        isComplete || isCurrent ? 'bg-primary'
                          : isFailedAt ? 'bg-red-400 dark:bg-red-500'
                          : 'bg-border',
                      )}
                    />
                  )}
                  {/* Stage icon */}
                  <div className="relative flex items-center justify-center">
                    {isComplete && (
                      <CheckCircle2 className="size-5 text-primary" />
                    )}
                    {isCurrent && (
                      <div className="relative">
                        <Radio className="size-5 text-primary" />
                        <span className="absolute inset-0 animate-ping rounded-full bg-primary/20" />
                      </div>
                    )}
                    {isFailedAt && incident.status === 'error' && (
                      <CircleAlert className="size-5 text-red-600 dark:text-red-400" />
                    )}
                    {isFailedAt && incident.status === 'needs_input' && (
                      <AlertTriangle className="size-5 text-amber-600 dark:text-amber-400" />
                    )}
                    {isFuture && !isFailedAt && (
                      <Circle className="size-5 text-muted-foreground/30" />
                    )}
                  </div>
                  {idx < PIPELINE_ORDER.length - 1 && (
                    <div
                      className={cn(
                        'h-2 w-0.5',
                        isComplete ? 'bg-primary' : 'bg-border',
                      )}
                    />
                  )}
                </div>
                {/* Stage label */}
                <span
                  className={cn(
                    'py-1 text-sm',
                    isComplete && 'text-muted-foreground',
                    isCurrent && 'font-semibold text-foreground',
                    isFailedAt && 'font-semibold text-red-600 dark:text-red-400',
                    isFuture && !isFailedAt && 'text-muted-foreground/40',
                  )}
                >
                  {statusConfig[key].label}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Similar past incidents */}
      <SimilarIncidentsCard incidentId={incident.id} />

      {/* Generate Post-Mortem button */}
      {isResolved && (
        <Button
          className="w-full gap-2"
          onClick={onGenerateRetro}
          disabled={generatingRetro}
        >
          <FileText className="size-4" />
          {generatingRetro ? 'Generating...' : 'Generate Post-Mortem'}
        </Button>
      )}
    </div>
  )
}
