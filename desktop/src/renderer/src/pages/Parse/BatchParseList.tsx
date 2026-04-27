import { Link } from 'react-router-dom'
import {
  Loader2,
  CheckCircle2,
  XCircle,
  Circle,
  Clock,
  Trash2,
  ArrowRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FileType } from '@/pages/NewJob/types'

export type BatchItemStatus =
  | 'pending'
  | 'submitting'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'

export interface BatchParseItem {
  id: string
  filePath: string
  fileType: FileType
  runId: string | null
  status: BatchItemStatus
  error: string | null
  resultId: string | null
}

interface BatchParseListProps {
  items: BatchParseItem[]
  isSubmitting: boolean
  onClear: () => void
  onRemoveItem: (id: string) => void
}

function basename(path: string): string {
  const slash = path.lastIndexOf('/')
  return slash >= 0 ? path.slice(slash + 1) : path
}

function StatusGlyph({ status }: { status: BatchItemStatus }): JSX.Element {
  switch (status) {
    case 'submitting':
      return <Loader2 size={14} className="animate-spin text-ink-tertiary" />
    case 'queued':
      return <Clock size={14} className="text-ink-tertiary" strokeWidth={1.7} />
    case 'running':
      return <Loader2 size={14} className="animate-spin text-accent" />
    case 'completed':
      return <CheckCircle2 size={14} className="text-success" />
    case 'failed':
      return <XCircle size={14} className="text-danger" />
    default:
      return <Circle size={14} className="text-ink-faint" strokeWidth={1.5} />
  }
}

function statusLabel(status: BatchItemStatus): string {
  switch (status) {
    case 'pending':
      return 'Pending'
    case 'submitting':
      return 'Submitting…'
    case 'queued':
      return 'Queued'
    case 'running':
      return 'Parsing'
    case 'completed':
      return 'Done'
    case 'failed':
      return 'Failed'
  }
}

export default function BatchParseList({
  items,
  isSubmitting,
  onClear,
  onRemoveItem,
}: BatchParseListProps): JSX.Element {
  const total = items.length
  const completed = items.filter((i) => i.status === 'completed').length
  const failed = items.filter((i) => i.status === 'failed').length
  const inFlight = items.filter(
    (i) => i.status === 'queued' || i.status === 'running',
  ).length
  const allDone = total > 0 && completed + failed === total

  return (
    <div className="card mt-6 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-paper-300/60 bg-paper-100/60">
        <div className="min-w-0">
          <div className="text-xs font-semibold text-ink-secondary tracking-wider uppercase">
            Batch · {total} file{total === 1 ? '' : 's'}
          </div>
          <div className="text-[11px] text-ink-tertiary mt-0.5">
            {allDone ? (
              <>
                {completed} done
                {failed > 0 && (
                  <span className="text-danger"> · {failed} failed</span>
                )}
              </>
            ) : isSubmitting ? (
              <>Submitting to queue…</>
            ) : inFlight > 0 ? (
              <>
                {completed}/{total} done · {inFlight} in flight
              </>
            ) : (
              <>Ready to submit</>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onClear}
          disabled={isSubmitting}
          className="btn-ghost px-2.5 py-1.5 text-xs"
          title="Clear batch"
        >
          <Trash2 size={12} strokeWidth={1.8} />
          Clear
        </button>
      </div>

      <ul className="divide-y divide-paper-300/40">
        {items.map((item) => (
          <BatchRow
            key={item.id}
            item={item}
            onRemove={() => onRemoveItem(item.id)}
            canRemove={!isSubmitting && item.status === 'pending'}
          />
        ))}
      </ul>
    </div>
  )
}

function BatchRow({
  item,
  onRemove,
  canRemove,
}: {
  item: BatchParseItem
  onRemove: () => void
  canRemove: boolean
}): JSX.Element {
  const name = basename(item.filePath)
  const isTerminal = item.status === 'completed' || item.status === 'failed'
  return (
    <li className="flex items-center gap-3 px-4 py-2.5">
      <StatusGlyph status={item.status} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className="font-mono text-xs text-ink truncate"
            title={item.filePath}
          >
            {name}
          </span>
          {item.fileType && (
            <span className="text-[10px] uppercase tracking-wider text-ink-faint shrink-0">
              {item.fileType}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-0.5">
          <span
            className={cn(
              'text-[11px]',
              item.status === 'failed'
                ? 'text-danger'
                : item.status === 'completed'
                  ? 'text-success'
                  : 'text-ink-tertiary',
            )}
          >
            {statusLabel(item.status)}
          </span>
          {item.runId && (
            <code className="font-mono text-[10px] text-ink-faint">
              {item.runId.slice(0, 8)}
            </code>
          )}
          {item.status === 'failed' && item.error && (
            <span
              className="text-[11px] text-danger/80 truncate"
              title={item.error}
            >
              · {item.error}
            </span>
          )}
        </div>
      </div>

      {item.status === 'completed' && item.resultId && (
        <Link
          to={`/?parsed=${encodeURIComponent(item.resultId)}`}
          className="text-[11px] text-accent hover:text-accent-hover font-medium inline-flex items-center gap-0.5 shrink-0"
        >
          Review
          <ArrowRight size={11} strokeWidth={1.8} />
        </Link>
      )}
      {isTerminal && item.runId && (
        <Link
          to={`/jobs/${item.runId}`}
          className="text-[11px] text-ink-tertiary hover:text-ink-secondary shrink-0"
        >
          Job
        </Link>
      )}
      {!isTerminal && item.runId && (
        <Link
          to={`/jobs/${item.runId}`}
          className="text-[11px] text-ink-tertiary hover:text-ink-secondary shrink-0"
        >
          View
        </Link>
      )}
      {canRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove ${name} from batch`}
          title="Remove from batch"
          className="p-1 -m-1 text-ink-faint hover:text-danger shrink-0"
        >
          <Trash2 size={12} strokeWidth={1.8} />
        </button>
      )}
    </li>
  )
}
