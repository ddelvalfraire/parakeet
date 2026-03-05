import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Clock, Shield, Star } from 'lucide-react'
import { cn } from '@/lib/utils'
import { riskConfig } from '@/lib/styles'
import type { RemediationResult, RemediationOption } from '@/types'

interface Props {
  payload: RemediationResult
  approved: boolean
  onApprove: (optionId: string, notes: string) => Promise<void>
}

export default function RemediationCard({
  payload,
  approved,
  onApprove,
}: Props) {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedOption, setSelectedOption] = useState<RemediationOption | null>(
    null,
  )
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [approveError, setApproveError] = useState<string | null>(null)

  const maxConfidence = Math.max(...payload.options.map((o) => o.confidence))

  function handleApproveClick(option: RemediationOption) {
    setSelectedOption(option)
    setNotes('')
    setApproveError(null)
    setDialogOpen(true)
  }

  async function handleConfirm() {
    if (!selectedOption) return
    setSubmitting(true)
    setApproveError(null)
    try {
      await onApprove(selectedOption.id, notes)
      setDialogOpen(false)
    } catch (err) {
      setApproveError(
        err instanceof Error ? err.message : 'Approval failed. Please retry.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <div className="space-y-3">
        {payload.options.map((option) => {
          const isRecommended = option.confidence === maxConfidence
          const pct = Math.round(option.confidence * 100)

          return (
            <div
              key={option.id}
              className={cn(
                'rounded-lg border bg-card p-4 space-y-3',
                isRecommended && 'ring-2 ring-green-500/30 border-green-200 dark:border-green-800',
              )}
            >
              {/* Header */}
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="text-sm font-semibold">{option.title}</h4>
                {isRecommended && (
                  <Badge className="bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300 gap-1">
                    <Star className="h-3 w-3" />
                    Recommended
                  </Badge>
                )}
                <Badge className={riskConfig[option.risk_level].badge}>
                  <Shield className="h-3 w-3" />
                  {riskConfig[option.risk_level].label} risk
                </Badge>
              </div>

              <p className="text-sm text-muted-foreground">
                {option.description}
              </p>

              {/* Confidence bar */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-muted-foreground">Confidence</span>
                  <span className="font-semibold tabular-nums">{pct}%</span>
                </div>
                <Progress value={pct} className="h-1.5" />
              </div>

              {/* Recovery time */}
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                <span>Recovery: {option.estimated_recovery_time}</span>
              </div>

              {/* Steps */}
              <ol className="list-decimal list-inside space-y-1">
                {option.steps.map((step, i) => (
                  <li
                    key={i}
                    className="text-xs text-muted-foreground font-mono leading-relaxed"
                  >
                    {step}
                  </li>
                ))}
              </ol>

              {/* Approve button */}
              {!approved && (
                <Button
                  size="sm"
                  variant={isRecommended ? 'default' : 'outline'}
                  onClick={() => handleApproveClick(option)}
                >
                  Approve
                </Button>
              )}
            </div>
          )
        })}
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Remediation</DialogTitle>
            <DialogDescription>
              You are about to approve:{' '}
              <strong>{selectedOption?.title}</strong>. This will begin the
              remediation process immediately.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="approval-notes">Notes (optional)</Label>
            <Textarea
              id="approval-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Any additional context for the team..."
              rows={3}
            />
          </div>
          {approveError && (
            <p className="text-sm text-destructive">{approveError}</p>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button onClick={handleConfirm} disabled={submitting}>
              {submitting ? 'Approving...' : 'Confirm Approval'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
