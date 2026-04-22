import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowRight,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Loader2,
} from 'lucide-react'
import { apiFetch } from '@/lib/api'
import { formatRelativeTime } from '@/lib/formatters'
import {
  deriveDocumentLabels,
  resumeReviewPath,
  type LibrarySummary,
} from '@/lib/parsedDocuments'
import { Chip } from '@/components/Chip'

interface LibraryPickerInlineProps {
  apiBase: string
  apiToken: string
}

export default function LibraryPickerInline({
  apiBase,
  apiToken,
}: LibraryPickerInlineProps): JSX.Element | null {
  const navigate = useNavigate()
  const [rows, setRows] = useState<LibrarySummary[] | null>(null)
  const [isExpanded, setIsExpanded] = useState(false)
  const isLoading = rows === null

  useEffect(() => {
    let cancelled = false
    const load = async (): Promise<void> => {
      try {
        const response = await apiFetch(
          apiBase,
          apiToken,
          '/api/parsed-documents',
        )
        if (cancelled || !response.ok) {
          if (!cancelled) setRows([])
          return
        }
        const data = await response.json()
        if (!cancelled) setRows(data.parsed_documents || [])
      } catch {
        if (!cancelled) setRows([])
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [apiBase, apiToken])

  const handlePick = useCallback(
    (id: string): void => {
      navigate(resumeReviewPath(id))
    },
    [navigate],
  )

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-ink-tertiary py-2">
        <Loader2 size={12} className="animate-spin" />
        Checking library…
      </div>
    )
  }

  if (rows.length === 0) return null

  return (
    <div className="card overflow-hidden">
      <button
        type="button"
        onClick={() => setIsExpanded((value) => !value)}
        aria-expanded={isExpanded}
        className="w-full flex items-center gap-2 px-4 py-3 text-left bg-transparent border-none cursor-pointer hover:bg-paper-100/70 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown size={14} className="text-ink-tertiary shrink-0" />
        ) : (
          <ChevronRight size={14} className="text-ink-tertiary shrink-0" />
        )}
        <BookOpen
          size={14}
          className="text-ink-tertiary shrink-0"
          strokeWidth={1.7}
        />
        <span className="text-sm text-ink-secondary font-medium flex-1">
          Or pick from Library
        </span>
        <span className="text-xs text-ink-tertiary">{rows.length} parsed</span>
      </button>
      {isExpanded && (
        <div className="border-t border-paper-300 divide-y divide-paper-300 max-h-64 overflow-y-auto">
          {rows.map((row) => (
            <LibraryPickerRow key={row.id} row={row} onPick={handlePick} />
          ))}
        </div>
      )}
    </div>
  )
}

function LibraryPickerRow({
  row,
  onPick,
}: {
  row: LibrarySummary
  onPick: (id: string) => void
}): JSX.Element {
  const { heading } = deriveDocumentLabels(row.source_path, row.title)
  const timeLine = formatRelativeTime(row.parsed_at)
  return (
    <button
      type="button"
      onClick={() => onPick(row.id)}
      className="w-full flex items-center gap-3 px-4 py-3 text-left bg-transparent border-none cursor-pointer hover:bg-paper-100/70 transition-colors"
    >
      <div className="flex-1 min-w-0">
        <div className="font-serif text-sm font-semibold text-ink truncate leading-snug">
          {heading}
        </div>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          <Chip tone="accent">{row.parser_used}</Chip>
          <span className="text-[11px] text-ink-tertiary">
            {row.section_count} section{row.section_count === 1 ? '' : 's'}
          </span>
          {timeLine && (
            <span className="text-[11px] text-ink-tertiary">{timeLine}</span>
          )}
        </div>
      </div>
      <ArrowRight size={14} className="text-accent shrink-0" />
    </button>
  )
}
