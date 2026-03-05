import { Progress } from '@/components/ui/progress'
import { AlertTriangle, Lightbulb } from 'lucide-react'
import type { RootCauseResult } from '@/types'

export default function RootCauseCard({
  payload,
}: {
  payload: RootCauseResult
}) {
  const pct = Math.round(payload.confidence_score * 100)

  return (
    <div className="rounded-lg border border-l-[3px] border-l-indigo-500 bg-card p-4 space-y-4 dark:border-l-indigo-400">
      {/* Probable cause callout */}
      <div className="flex gap-3 rounded-md border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-950/50">
        <Lightbulb className="h-5 w-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
        <p className="text-sm leading-relaxed text-blue-900 dark:text-blue-200">
          {payload.probable_cause}
        </p>
      </div>

      {/* Confidence bar */}
      <div>
        <div className="flex items-center justify-between text-sm mb-1.5">
          <span className="text-muted-foreground text-xs font-medium">
            Confidence
          </span>
          <span className="font-semibold tabular-nums">{pct}%</span>
        </div>
        <Progress value={pct} />
      </div>

      {/* Evidence (numbered list) */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
          Evidence
        </h4>
        <ol className="list-decimal list-inside space-y-1.5">
          {payload.evidence.map((item, i) => (
            <li key={i} className="text-sm leading-relaxed text-foreground/80">
              {item}
            </li>
          ))}
        </ol>
      </div>

      {/* Contributing factors (warning list) */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400 mb-2">
          Contributing Factors
        </h4>
        <ul className="space-y-2">
          {payload.contributing_factors.map((item, i) => (
            <li
              key={i}
              className="flex items-start gap-2 text-sm leading-relaxed text-amber-800 dark:text-amber-300"
            >
              <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
