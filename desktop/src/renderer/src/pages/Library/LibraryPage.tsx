import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, BookOpen, RotateCw } from 'lucide-react'
import { apiFetch } from '@/lib/api'
import { type LibrarySummary } from '@/lib/parsedDocuments'
import LibraryRow from './LibraryRow'

interface LibraryPageProps {
  apiBase: string
  apiToken: string
}

export default function LibraryPage({
  apiBase,
  apiToken,
}: LibraryPageProps): JSX.Element {
  const [rows, setRows] = useState<LibrarySummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const loadRows = useCallback(async (): Promise<void> => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        '/api/parsed-documents',
      )
      if (!response.ok) {
        throw new Error(`Failed to load library (${response.status})`)
      }
      const data = await response.json()
      setRows(data.parsed_documents || [])
    } catch (err) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Could not reach the backend.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [apiBase, apiToken])

  useEffect(() => {
    loadRows()
  }, [loadRows])

  const handleRowDeleted = useCallback((deletedId: string): void => {
    setRows((prev) => prev.filter((row) => row.id !== deletedId))
  }, [])

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 pb-12 pt-6">
        <header className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
              Library
            </h1>
            <p className="font-serif text-sm text-ink-tertiary italic mt-1">
              Parsed documents, ready to review or reuse.
            </p>
          </div>
          <button
            type="button"
            onClick={loadRows}
            disabled={isLoading}
            className="btn-ghost px-3 py-2 text-sm shrink-0"
            title="Reload"
          >
            <RotateCw
              size={13}
              className={isLoading ? 'animate-spin' : undefined}
            />
            Refresh
          </button>
        </header>

        {isLoading && rows.length === 0 && (
          <div className="card flex items-center justify-center gap-2 px-4 py-10 text-sm text-ink-tertiary">
            <Loader2 size={14} className="animate-spin" />
            Loading library…
          </div>
        )}

        {errorMessage && (
          <div className="card mb-4 bg-danger/5 border-danger/30 px-4 py-3">
            <div className="text-xs font-semibold text-danger uppercase tracking-wider mb-1">
              Library unavailable
            </div>
            <div className="text-sm text-ink-secondary">{errorMessage}</div>
          </div>
        )}

        {!isLoading && !errorMessage && rows.length === 0 && <EmptyState />}

        {rows.length > 0 && (
          <div className="space-y-3">
            {rows.map((row) => (
              <LibraryRow
                key={row.id}
                row={row}
                apiBase={apiBase}
                apiToken={apiToken}
                onDeleted={handleRowDeleted}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function EmptyState(): JSX.Element {
  return (
    <div className="card flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      <div className="w-10 h-10 rounded-xl bg-paper-200 flex items-center justify-center">
        <BookOpen size={18} className="text-ink-tertiary" strokeWidth={1.5} />
      </div>
      <div className="font-serif text-base text-ink">
        No parsed documents yet
      </div>
      <div className="text-sm text-ink-tertiary max-w-sm">
        Parse a paper on the{' '}
        <Link
          to="/parse"
          className="text-accent hover:text-accent-hover underline underline-offset-2"
        >
          Parse page
        </Link>{' '}
        and it will appear here — ready to review again without reparsing.
      </div>
    </div>
  )
}
