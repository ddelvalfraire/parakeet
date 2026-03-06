import { Link } from 'react-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FileText, ArrowRight } from 'lucide-react'
import type { PostMortem } from '@/types'

interface Props {
  payload: PostMortem
  incidentId: string
}

export default function ResolvedCard({ payload, incidentId }: Props) {
  return (
    <div className="rounded-lg border border-l-[3px] border-l-green-500 bg-card p-4 space-y-3 dark:border-l-green-400">
      <div className="flex items-center gap-2">
        <FileText className="h-4 w-4 text-muted-foreground" />
        <h4 className="text-sm font-semibold">Post-Mortem Preview</h4>
        <Badge variant="secondary" className="ml-auto text-xs">
          {payload.severity}
        </Badge>
      </div>

      <p className="text-sm font-medium">{payload.title}</p>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div className="text-muted-foreground">Duration</div>
        <div>{payload.duration}</div>
        <div className="text-muted-foreground">Users affected</div>
        <div>{payload.impact.users_affected}</div>
        <div className="text-muted-foreground">Services degraded</div>
        <div>{payload.impact.services_degraded.join(', ')}</div>
      </div>

      <Button variant="outline" size="sm" className="gap-1.5" asChild>
        <Link to={`/incident/${incidentId}/retro`}>
          View Full Post-Mortem
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </Button>
    </div>
  )
}
