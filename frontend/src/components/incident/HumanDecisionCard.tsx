import { CheckCircle2 } from 'lucide-react'
import type { HumanDecision } from '@/types'

interface Props {
  payload: HumanDecision
  optionTitle?: string
}

export default function HumanDecisionCard({ payload, optionTitle }: Props) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-950/50">
      <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 shrink-0" />
      <div className="space-y-1 min-w-0">
        <p className="text-sm font-medium text-green-900 dark:text-green-200">
          Remediation approved by {payload.approved_by}
        </p>
        <p className="text-xs text-green-700 dark:text-green-400">
          Option: {optionTitle ?? payload.approved_option_id}
        </p>
        {payload.notes && (
          <p className="text-xs text-green-700 dark:text-green-400 italic">
            &ldquo;{payload.notes}&rdquo;
          </p>
        )}
      </div>
    </div>
  )
}
