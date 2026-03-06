import { AlertTriangle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SystemEventPayload {
  error?: string
  stage?: string
  detail?: string
}

interface Props {
  payload: SystemEventPayload
  title: string
}

export default function SystemEventCard({ payload, title }: Props) {
  const isError = !!payload.error

  return (
    <div
      className={cn(
        'rounded-lg border p-4 space-y-2',
        isError
          ? 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/30'
          : 'border-border bg-muted/30',
      )}
    >
      <div className="flex items-center gap-2">
        {isError ? (
          <AlertTriangle className="size-4 text-red-600 dark:text-red-400" />
        ) : (
          <Info className="size-4 text-muted-foreground" />
        )}
        <h4 className="text-sm font-semibold">{title}</h4>
      </div>
      {payload.detail && (
        <p className="text-xs text-muted-foreground">{payload.detail}</p>
      )}
      {payload.stage && (
        <p className="text-xs text-muted-foreground font-mono">
          Stage: {payload.stage}
        </p>
      )}
    </div>
  )
}
