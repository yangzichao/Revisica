import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronDown,
  ChevronRight,
  Trash2,
  ArrowRight,
  Loader2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'
import { formatRelativeTime } from '@/lib/time'
import {
  deriveDocumentLabels,
  resumeReviewPath,
  type LibrarySummary,
} from '@/lib/parsedDocuments'
import ParserChip from '@/components/ParserChip'
import ParseResult, { type ParseResultData } from '@/pages/Parse/ParseResult'

interface LibraryRowProps {
  row: LibrarySummary
  apiBase: string
  apiToken: string
  onDeleted: (id: string) => void
}

export default function LibraryRow({
  row,
  apiBase,
  apiToken,
  onDeleted,
}: LibraryRowProps): JSX.Element {
  const navigate = useNavigate()
  const [isExpanded, setIsExpanded] = useState(false)
  const [detail, setDetail] = useState<ParseResultData | null>(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  const { fileName, heading } = deriveDocumentLabels(
    row.source_path,
    row.title,
  )

  const handleToggleExpand = useCallback(async (): Promise<void> => {
    if (isExpanded) {
      setIsExpanded(false)
      return
    }
    setIsExpanded(true)
    if (detail || isLoadingDetail) return
    setIsLoadingDetail(true)
    setDetailError(null)
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        `/api/parsed-documents/${encodeURIComponent(row.id)}`,
      )
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || `Failed to load (${response.status})`)
      }
      const data: ParseResultData = await response.json()
      setDetail(data)
    } catch (err) {
      setDetailError(
        err instanceof Error ? err.message : 'Could not load detail',
      )
    } finally {
      setIsLoadingDetail(false)
    }
  }, [isExpanded, detail, isLoadingDetail, apiBase, apiToken, row.id])

  const handleStartReview = useCallback((): void => {
    navigate(resumeReviewPath(row.id))
  }, [navigate, row.id])

  const handleDelete = useCallback(async (): Promise<void> => {
    if (!confirmingDelete) {
      setConfirmingDelete(true)
      return
    }
    setIsDeleting(true)
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        `/api/parsed-documents/${encodeURIComponent(row.id)}`,
        { method: 'DELETE' },
      )
      if (!response.ok) {
        throw new Error(`Delete failed (${response.status})`)
      }
      onDeleted(row.id)
    } catch (err) {
      setIsDeleting(false)
      setConfirmingDelete(false)
      setDetailError(
        err instanceof Error ? err.message : 'Delete failed',
      )
    }
  }, [confirmingDelete, apiBase, apiToken, row.id, onDeleted])

  const handleCancelDelete = useCallback((): void => {
    setConfirmingDelete(false)
  }, [])

  const authorLine = summarizeAuthors(row.authors)
  const timeLine = formatRelativeTime(row.parsed_at)

  return (
    <div className="card overflow-hidden">
      <div className="flex items-start gap-3 px-4 py-3.5">
        <button
          type="button"
          onClick={handleToggleExpand}
          className="shrink-0 mt-1 text-ink-tertiary hover:text-ink-secondary transition-colors cursor-pointer bg-transparent border-none p-0"
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
        >
          {isExpanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        </button>

        <button
          type="button"
          onClick={handleToggleExpand}
          className="flex-1 min-w-0 text-left bg-transparent border-none cursor-pointer p-0"
        >
          <div className="font-serif text-base font-semibold text-ink truncate leading-snug">
            {heading}
          </div>
          {authorLine && (
            <div className="text-xs text-ink-tertiary mt-0.5 truncate">
              {authorLine}
            </div>
          )}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <ParserChip parser={row.parser_used} />
            <MetaChip>
              {row.section_count} section{row.section_count === 1 ? '' : 's'}
            </MetaChip>
            <MetaChip>{timeLine}</MetaChip>
            <MetaChip muted>{fileName}</MetaChip>
          </div>
        </button>

        <div className="flex items-center gap-1.5 shrink-0">
          {confirmingDelete ? (
            <>
              <button
                type="button"
                onClick={handleDelete}
                disabled={isDeleting}
                className="btn-ghost px-2.5 py-1.5 text-xs text-danger hover:bg-danger/10"
              >
                {isDeleting ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  <Trash2 size={12} />
                )}
                Confirm delete
              </button>
              <button
                type="button"
                onClick={handleCancelDelete}
                disabled={isDeleting}
                className="btn-ghost px-2.5 py-1.5 text-xs"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={handleStartReview}
                className="btn-ghost px-2.5 py-1.5 text-xs text-accent hover:bg-accent/10"
                title="Start review using this parse"
              >
                Review
                <ArrowRight size={12} />
              </button>
              <button
                type="button"
                onClick={handleDelete}
                className="btn-ghost px-2 py-1.5 text-xs text-ink-tertiary hover:text-danger"
                title="Delete"
              >
                <Trash2 size={12} />
              </button>
            </>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-paper-300 bg-paper-100/60 px-5 py-4">
          {isLoadingDetail && (
            <div className="flex items-center gap-2 text-xs text-ink-tertiary">
              <Loader2 size={12} className="animate-spin" />
              Loading details…
            </div>
          )}
          {detailError && !isLoadingDetail && (
            <div className="text-sm text-danger">{detailError}</div>
          )}
          {detail && !isLoadingDetail && <ParseResult result={detail} />}
        </div>
      )}
    </div>
  )
}

function MetaChip({
  children,
  muted,
}: {
  children: React.ReactNode
  muted?: boolean
}): JSX.Element {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-full border text-[11px] font-medium',
        muted
          ? 'border-paper-300 bg-transparent text-ink-faint font-mono'
          : 'border-paper-300 bg-paper-50 text-ink-tertiary',
      )}
    >
      {children}
    </span>
  )
}

function summarizeAuthors(authors: string[]): string {
  if (!authors || authors.length === 0) return ''
  if (authors.length <= 3) return authors.join(', ')
  return `${authors.slice(0, 3).join(', ')} +${authors.length - 3} more`
}
