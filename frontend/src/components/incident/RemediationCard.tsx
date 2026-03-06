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
import { AlertTriangle, Clock, ExternalLink, GitPullRequest, Shield, Star, Wrench } from 'lucide-react'
import { cn } from '@/lib/utils'
import { riskConfig } from '@/lib/styles'
import ManualResolutionDialog from './ManualResolutionDialog'
import type { RemediationResult, RemediationOption } from '@/types'

interface Props {
  payload: RemediationResult
  approved: boolean
  onApprove: (optionId: string, notes: string) => Promise<void>
  onMergeFix?: (notes: string) => Promise<void>
  onResolveManually?: (explanation: string) => Promise<void>
}

function DiffView({ diff }: { diff: string }) {
  const lines = diff.split('\n')
  return (
    <div className="rounded-md border bg-muted/30 overflow-x-auto text-xs">
      <pre className="p-3 leading-relaxed">
        {lines.map((line, i) => {
          let cls = 'text-muted-foreground'
          if (line.startsWith('+') && !line.startsWith('+++')) {
            cls = 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-950/40'
          } else if (line.startsWith('-') && !line.startsWith('---')) {
            cls = 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950/40'
          } else if (line.startsWith('@@')) {
            cls = 'text-blue-600 dark:text-blue-400'
          } else if (line.startsWith('diff') || line.startsWith('---') || line.startsWith('+++')) {
            cls = 'text-muted-foreground font-semibold'
          }
          return (
            <div key={i} className={cn('px-1 -mx-1', cls)}>
              {line || ' '}
            </div>
          )
        })}
      </pre>
    </div>
  )
}

export default function RemediationCard({
  payload,
  approved,
  onApprove,
  onMergeFix,
  onResolveManually,
}: Props) {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedOption, setSelectedOption] = useState<RemediationOption | null>(
    null,
  )
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [approveError, setApproveError] = useState<string | null>(null)
  const [manualDialogOpen, setManualDialogOpen] = useState(false)

  const hasPR = !!payload.pr
  const maxConfidence = payload.options.length > 0
    ? Math.max(...payload.options.map((o) => o.confidence))
    : 0

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

  async function handleMergeFix() {
    if (!onMergeFix) return
    setSubmitting(true)
    setApproveError(null)
    try {
      await onMergeFix('')
    } catch (err) {
      setApproveError(
        err instanceof Error ? err.message : 'Merge failed. Please retry.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (!payload.options.length && !hasPR) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/30">
        <div className="flex items-center gap-2">
          <AlertTriangle className="size-4 text-amber-600 dark:text-amber-400" />
          <h4 className="text-sm font-semibold text-amber-800 dark:text-amber-300">
            No remediation options available
          </h4>
        </div>
        <p className="mt-1.5 text-xs text-muted-foreground">
          The agent could not determine remediation options for this incident.
          Manual intervention is required.
        </p>
        {onResolveManually && !approved && (
          <Button
            size="sm"
            variant="outline"
            className="mt-3"
            onClick={() => setManualDialogOpen(true)}
          >
            <Wrench className="h-3.5 w-3.5 mr-1" />
            Resolve Manually
          </Button>
        )}
        {onResolveManually && (
          <ManualResolutionDialog
            open={manualDialogOpen}
            onOpenChange={setManualDialogOpen}
            onResolve={onResolveManually}
          />
        )}
      </div>
    )
  }

  return (
    <>
      <div className="space-y-3">
        {/* PR Fix Section */}
        {hasPR && (
          <div className="rounded-lg border bg-card p-4 space-y-3 ring-2 ring-green-500/30 border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2 flex-wrap">
              <GitPullRequest className="h-4 w-4 text-green-600" />
              <h4 className="text-sm font-semibold">
                Pull Request #{payload.pr!.pr_number}
              </h4>
              <Badge className="bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300 gap-1">
                <Star className="h-3 w-3" />
                Code Fix
              </Badge>
              <a
                href={payload.pr!.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-auto inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                View on GitHub
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>

            <p className="text-xs text-muted-foreground font-mono">
              {payload.pr!.file_path}
            </p>

            {payload.pr!.diff && <DiffView diff={payload.pr!.diff} />}

            {/* Action buttons */}
            {!approved && (
              <div className="flex items-center gap-2 pt-1">
                <Button size="sm" onClick={handleMergeFix} disabled={submitting}>
                  {submitting ? 'Merging...' : 'Approve & Merge'}
                </Button>
                {onResolveManually && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setManualDialogOpen(true)}
                  >
                    <Wrench className="h-3.5 w-3.5 mr-1" />
                    Resolve Manually
                  </Button>
                )}
              </div>
            )}

            {approveError && (
              <p className="text-sm text-destructive">{approveError}</p>
            )}
          </div>
        )}

        {/* Standard remediation options */}
        {payload.options.map((option) => {
          const isRecommended = option.confidence === maxConfidence && !hasPR
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

              {/* Approve button — only show for non-PR options */}
              {!approved && !hasPR && (
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

      {/* Standard approval dialog (non-PR flow) */}
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

      {/* Manual resolution dialog */}
      {onResolveManually && (
        <ManualResolutionDialog
          open={manualDialogOpen}
          onOpenChange={setManualDialogOpen}
          onResolve={onResolveManually}
        />
      )}
    </>
  )
}
