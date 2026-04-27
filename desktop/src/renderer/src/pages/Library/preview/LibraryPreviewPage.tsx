import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import type { ParseResultData } from '@/pages/Parse/ParseResult'
import { deriveExportFilename } from '@/lib/parsedDocuments'
import {
  deleteParsedDocument,
  fetchParsedDocument,
} from '../parsedDocumentApi'
import { useDeleteConfirm } from '../useDeleteConfirm'
import LibraryPreviewContents from './LibraryPreviewContents'
import LibraryPreviewDocument from './LibraryPreviewDocument'
import LibraryPreviewHeader from './LibraryPreviewHeader'
import LibraryPreviewTopBar from './LibraryPreviewTopBar'
import { extractTableOfContents } from './extractToc'
import { useActiveHeading } from './useActiveHeading'

interface LibraryPreviewPageProps {
  apiBase: string
  apiToken: string
}

export default function LibraryPreviewPage({
  apiBase,
  apiToken,
}: LibraryPreviewPageProps): JSX.Element {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [data, setData] = useState<ParseResultData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const scrollRootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setLoadError(null)
    setData(null)
    fetchParsedDocument(apiBase, apiToken, id)
      .then((fetched) => {
        if (!cancelled) setData(fetched)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setLoadError(
            err instanceof Error ? err.message : 'Could not load document.',
          )
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [apiBase, apiToken, id])

  const deleteConfirm = useDeleteConfirm({
    perform: () => deleteParsedDocument(apiBase, apiToken, id),
    onDeleted: () => navigate('/library'),
  })

  const tocEntries = useMemo(
    () => (data ? extractTableOfContents(data.markdown || '') : []),
    [data],
  )
  const slugs = useMemo(() => tocEntries.map((entry) => entry.slug), [tocEntries])
  const activeSlug = useActiveHeading(slugs, scrollRootRef)

  const handleBack = useCallback(() => navigate('/library'), [navigate])
  const handleStartReview = useCallback(
    () => navigate(`/?parsed=${encodeURIComponent(id)}`),
    [navigate, id],
  )

  const handleExportMarkdown = useCallback(async (): Promise<void> => {
    if (!data || isExporting) return
    setIsExporting(true)
    setExportError(null)
    try {
      const result = await window.api.saveMarkdown({
        defaultName: deriveExportFilename(
          data.source_path || '',
          data.title || '',
          id,
        ),
        content: data.markdown ?? '',
      })
      if (!result.saved && result.error) {
        setExportError(result.error)
      }
    } catch (err) {
      setExportError(
        err instanceof Error ? err.message : 'Could not export markdown',
      )
    } finally {
      setIsExporting(false)
    }
  }, [data, id, isExporting])

  const errorMessage = loadError || deleteConfirm.error || exportError

  return (
    <div ref={scrollRootRef} className="flex-1 overflow-y-auto scroll-smooth">
      <div className="max-w-6xl mx-auto px-8 pt-6 pb-16">
        <LibraryPreviewTopBar
          onBack={handleBack}
          onReview={handleStartReview}
          onExport={handleExportMarkdown}
          onDelete={deleteConfirm.request}
          onCancelDelete={deleteConfirm.cancel}
          isExporting={isExporting}
          isConfirmingDelete={deleteConfirm.isConfirming}
          isDeleting={deleteConfirm.isDeleting}
          disabled={!data}
        />

        {isLoading && <LoadingState />}
        {errorMessage && !isLoading && <ErrorState message={errorMessage} />}

        {data && !isLoading && (
          <>
            <LibraryPreviewHeader data={data} />
            <div className="flex gap-8 mt-6">
              <LibraryPreviewContents
                entries={tocEntries}
                activeSlug={activeSlug}
                scrollRootRef={scrollRootRef}
              />
              <div className="flex-1 min-w-0">
                <LibraryPreviewDocument markdown={data.markdown || ''} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function LoadingState(): JSX.Element {
  return (
    <div className="card flex items-center justify-center gap-2 px-4 py-16 text-sm text-ink-tertiary">
      <Loader2 size={14} className="animate-spin" />
      Loading document…
    </div>
  )
}

function ErrorState({ message }: { message: string }): JSX.Element {
  return (
    <div className="card mb-4 bg-danger/5 border-danger/30 px-4 py-3">
      <div className="text-xs font-semibold text-danger uppercase tracking-wider mb-1">
        Preview unavailable
      </div>
      <div className="text-sm text-ink-secondary">{message}</div>
    </div>
  )
}
