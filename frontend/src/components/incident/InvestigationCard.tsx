import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { AlertTriangle, DollarSign } from 'lucide-react'
import { serviceStatusConfig } from '@/lib/styles'
import type { InvestigationResult, ImpactLevel } from '@/types'

const impactStyle: Record<ImpactLevel, string> = {
  primary: 'border-red-300 text-red-700 dark:border-red-700 dark:text-red-400',
  downstream: 'border-amber-300 text-amber-700 dark:border-amber-700 dark:text-amber-400',
  none: '',
}

export default function InvestigationCard({
  payload,
}: {
  payload: InvestigationResult
}) {
  const { log_findings, affected_services, estimated_users_affected, revenue_impact_per_minute } = payload

  return (
    <div className="rounded-lg border border-l-[3px] border-l-blue-500 bg-card p-4 space-y-4 dark:border-l-blue-400">
      {/* Affected services table */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
          Affected Services
        </h4>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Service</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Impact</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {affected_services.map((svc) => (
              <TableRow key={svc.service}>
                <TableCell className="font-mono text-xs">{svc.service}</TableCell>
                <TableCell>
                  <Badge className={serviceStatusConfig[svc.status].badge}>
                    {serviceStatusConfig[svc.status].label}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={impactStyle[svc.impact]}>
                    {svc.impact}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Log findings code block */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
          Log Findings
        </h4>
        <pre className="rounded-md bg-muted p-3 text-xs font-mono leading-relaxed overflow-x-auto whitespace-pre-wrap">
{`Error:    ${log_findings.error_pattern}
Freq:     ${log_findings.frequency}
First:    ${log_findings.first_occurrence}
Versions: ${log_findings.affected_versions.join(', ')}
Healthy:  ${log_findings.last_healthy_version}${
  log_findings.correlated_event
    ? `\nCorrel:   ${log_findings.correlated_event}`
    : ''
}${
  log_findings.sample_stack_trace
    ? `\n\nStack trace:\n${log_findings.sample_stack_trace}`
    : ''
}`}
        </pre>
      </div>

      {/* Revenue impact callout */}
      {revenue_impact_per_minute && (
        <div className="flex items-center gap-3 rounded-md border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-950/50">
          <DollarSign className="h-5 w-5 text-red-600 dark:text-red-400 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-red-800 dark:text-red-200">
              {revenue_impact_per_minute}/min revenue impact
            </p>
            <p className="text-xs text-red-600 dark:text-red-400">
              {estimated_users_affected} affected
            </p>
          </div>
          <AlertTriangle className="h-4 w-4 text-red-500 shrink-0" />
        </div>
      )}
    </div>
  )
}
