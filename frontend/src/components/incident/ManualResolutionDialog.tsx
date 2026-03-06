import { useState } from 'react'
import { Button } from '@/components/ui/button'
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

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  onResolve: (explanation: string) => Promise<void>
}

export default function ManualResolutionDialog({
  open,
  onOpenChange,
  onResolve,
}: Props) {
  const [explanation, setExplanation] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit() {
    if (!explanation.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      await onResolve(explanation.trim())
      setExplanation('')
      onOpenChange(false)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to resolve. Please retry.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Resolve Manually</DialogTitle>
          <DialogDescription>
            Explain how this incident was resolved without merging the proposed
            fix. The PR will be closed automatically.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="manual-explanation">What did you do?</Label>
          <Textarea
            id="manual-explanation"
            value={explanation}
            onChange={(e) => setExplanation(e.target.value)}
            placeholder="e.g. Rolled back deployment manually, applied a different config fix..."
            rows={4}
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={submitting || !explanation.trim()}
          >
            {submitting ? 'Resolving...' : 'Resolve Incident'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
