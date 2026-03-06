import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { History, ExternalLink, Loader2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { severityConfig } from '@/lib/styles'
import { api } from '@/api'
import type { SimilarIncident } from '@/types/agents'

interface Props {
  incidentId: string
}

export default function SimilarIncidentsCard({ incidentId }: Props) {
  const [items, setItems] = useState<SimilarIncident[]>([])
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    setLoading(true)
    setFailed(false)
    api
      .getSimilarIncidents(incidentId)
      .then((res) => setItems(res.similar))
      .catch(() => setFailed(true))
      .finally(() => setLoading(false))
  }, [incidentId])

  if (loading) {
    return (
      <div className="rounded-lg border bg-card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <History className="size-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Similar Past Incidents</h3>
        </div>
        <div className="flex items-center justify-center py-4 text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          <span className="ml-2 text-xs">Searching past incidents...</span>
        </div>
      </div>
    )
  }

  if (failed || items.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <History className="size-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Similar Past Incidents</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          {failed ? 'Could not load similar incidents.' : 'No similar past incidents found.'}
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border bg-card p-4 space-y-3">
      <div className="flex items-center gap-2">
        <History className="size-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold">Similar Past Incidents</h3>
        <span className="ml-auto text-xs tabular-nums text-muted-foreground">
          {items.length} match{items.length !== 1 && 'es'}
        </span>
      </div>
      <div className="space-y-2">
        {items.map((item) => {
          const sevCfg = severityConfig[item.severity as keyof typeof severityConfig] ?? severityConfig.P4
          const score = Math.round(item.similarity_score * 100)
          return (
            <Link
              key={item.incident_id}
              to={`/incident/${item.incident_id}`}
              className="group block rounded-md border p-3 transition-colors hover:bg-accent/50"
            >
              <div className="flex items-center gap-2">
                <Badge className={cn('text-[10px] px-1.5 py-0', sevCfg.badge)}>
                  {item.severity}
                </Badge>
                <span className="truncate text-xs font-medium">
                  #{item.incident_id}
                </span>
                <span className="ml-auto shrink-0 text-[10px] tabular-nums text-muted-foreground">
                  {score}% match
                </span>
                <ExternalLink className="size-3 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
              </div>
              <p className="mt-1.5 line-clamp-2 text-xs text-muted-foreground">
                {item.root_cause}
              </p>
              <p className="mt-1 line-clamp-1 text-xs text-emerald-600 dark:text-emerald-400">
                Fix: {item.remediation_taken}
              </p>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
