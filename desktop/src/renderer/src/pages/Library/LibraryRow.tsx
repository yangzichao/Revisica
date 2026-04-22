import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronDown,
  ChevronRight,
  Trash2,
  ArrowRight,
  Loader2,
  BookOpen,
} from 'lucide-react'
import { Chip } from '@/components/Chip'
import { formatRelativeTime } from '@/lib/formatters'
import {
  deriveDocumentLabels,
  resumeReviewPath,
  type LibrarySummary,
} from '@/lib/parsedDocuments'
import ParseResult, { type ParseResultData } from '@/pages/Parse/ParseResult'
import {
  deleteParsedDocument,
  fetchParsedDocument,
} from './parsedDocumentApi'
import { useDeleteConfirm } from './useDeleteConfirm'

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

  const { fileName, heading } = deriveDocumentLabels(
    row.source_path,
    row.title,
  )

  const deleteConfirm = useDeleteConfirm({
    perform: () => deleteParsedDocument(apiBase, apiToken, row.id),
    onDeleted: () => onDeleted(row.id),
  })

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
      const data = await fetchParsedDocument(apiBase, apiToken, row.id)
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

  const handleOpenPreview = useCallback((): void => {
    navigate(`/library/${encodeURIComponent(row.id)}`)
  }, [navigate, row.id])

  const authorLine = summarizeAuthors(row.authors)
  const timeLine = formatRelativeTime(row.parsed_at)
  const combinedError = detailError || deleteConfirm.error

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
            <Chip tone="accent">{row.parser_used}</Chip>
            <Chip>
              {row.section_count} section{row.section_count === 1 ? '' : 's'}
            </Chip>
            <Chip>{timeLine}</Chip>
            <Chip tone="muted">{fileName}</Chip>
          </div>
        </button>

        <div className="flex items-center gap-1.5 shrink-0">
          {deleteConfirm.isConfirming ? (
            <>
              <button
                type="button"
                onClick={deleteConfirm.request}
                disabled={deleteConfirm.isDeleting}
                className="btn-ghost px-2.5 py-1.5 text-xs text-danger hover:bg-danger/10"
              >
                {deleteConfirm.isDeleting ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  <Trash2 size={12} />
                )}
                Confirm delete
              </button>
              <button
                type="button"
                onClick={deleteConfirm.cancel}
                disabled={deleteConfirm.isDeleting}
                className="btn-ghost px-2.5 py-1.5 text-xs"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={handleOpenPreview}
                className="btn-ghost px-2.5 py-1.5 text-xs text-ink-secondary hover:text-ink"
                title="Open rendered preview"
              >
                <BookOpen size={12} />
                Open
              </button>
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
                onClick={deleteConfirm.request}
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
          {combinedError && !isLoadingDetail && (
            <div className="text-sm text-danger">{combinedError}</div>
          )}
          {detail && !isLoadingDetail && <ParseResult result={detail} />}
        </div>
      )}
    </div>
  )
}

function summarizeAuthors(authors: string[]): string {
  if (!authors || authors.length === 0) return ''
  if (authors.length <= 3) return authors.join(', ')
  return `${authors.slice(0, 3).join(', ')} +${authors.length - 3} more`
}
