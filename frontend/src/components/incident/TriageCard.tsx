import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { severityConfig } from '@/lib/styles'
import type { TriageResult } from '@/types'

export default function TriageCard({ payload }: { payload: TriageResult }) {
  return (
    <div className="rounded-lg border border-l-[3px] border-l-purple-500 bg-card p-4 space-y-3 dark:border-l-purple-400">
      <div className="flex items-center gap-2 flex-wrap">
        <Badge className={cn("font-semibold", severityConfig[payload.severity].badge)}>
          {payload.severity}
        </Badge>
        <span className="text-xs text-muted-foreground capitalize">
          {payload.category.replaceAll('_', ' ')}
        </span>
        {payload.is_duplicate && (
          <Badge variant="outline" className="text-xs">
            Duplicate
          </Badge>
        )}
      </div>
      <p className="text-sm leading-relaxed">{payload.summary}</p>
      <div className="flex flex-wrap gap-1.5">
        {payload.tags.map((tag) => (
          <Badge key={tag} variant="secondary" className="text-xs font-normal">
            {tag}
          </Badge>
        ))}
      </div>
    </div>
  )
}
