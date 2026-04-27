import { useReducer, useState, useCallback, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Play, Loader2, Bookmark, ArrowRight, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'
import Step1ImportFile, { detectFileType } from '@/pages/NewJob/Step1ImportFile'
import {
  DEFAULT_MINERU_BACKEND,
  DEFAULT_VENUE_PROFILE,
  type FileType,
  type WizardAction,
  type WizardState,
} from '@/pages/NewJob/types'
import ParseResult, { type ParseResultData } from './ParseResult'
import BatchParseList, {
  type BatchItemStatus,
  type BatchParseItem,
} from './BatchParseList'

const RUN_IDS_STORAGE_KEY = 'revisica_run_ids'

function appendRunIdToHistory(runId: string): void {
  try {
    const stored = localStorage.getItem(RUN_IDS_STORAGE_KEY)
    const parsed = stored ? JSON.parse(stored) : []
    const existing = Array.isArray(parsed)
      ? parsed.filter((id): id is string => typeof id === 'string')
      : []
    existing.unshift(runId)
    localStorage.setItem(
      RUN_IDS_STORAGE_KEY,
      JSON.stringify(existing.slice(0, 50)),
    )
  } catch {
    // Private mode / quota — not fatal
  }
}

// Initial state mirrors the wizard's shape so we can hand it to
// Step1ImportFile unchanged. The unused review-lane fields are harmless stubs.
const INITIAL_STATE: WizardState = {
  filePath: '',
  fileType: null,
  currentStep: 1,
  parserChoice: null,
  mineruBackend: DEFAULT_MINERU_BACKEND,
  primaryEngine: 'claude',
  secondaryEnabled: true,
  secondaryEngine: 'gpt',
  mode: 'review',
  venueProfile: DEFAULT_VENUE_PROFILE,
  llmProofReview: false,
}

// A trimmed reducer: Step1ImportFile only dispatches these three actions.
// Anything else the wider wizard dispatches would hit the default branch,
// which keeps the state intact.
function reducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case 'SET_FILE': {
      const keepParser = state.fileType === action.fileType
      const nextParser = keepParser
        ? state.parserChoice
        : action.fileType === 'pdf'
          ? null
          : 'auto'
      return {
        ...state,
        filePath: action.filePath,
        fileType: action.fileType,
        parserChoice: nextParser,
      }
    }
    case 'CLEAR_FILE':
      return { ...state, filePath: '', fileType: null, parserChoice: null }
    case 'SET_PARSER':
      return { ...state, parserChoice: action.parser }
    case 'SET_MINERU_BACKEND':
      return { ...state, mineruBackend: action.backend }
    default:
      return state
  }
}

function canRunParse(state: WizardState): boolean {
  if (!state.filePath || !state.fileType) return false
  if (state.fileType === 'pdf') {
    return state.parserChoice === 'mineru' || state.parserChoice === 'mathpix'
  }
  return true
}

function canRunBatch(state: WizardState, items: BatchParseItem[]): boolean {
  if (items.length === 0) return false
  if (items.some((i) => !i.fileType)) return false
  const hasPdf = items.some((i) => i.fileType === 'pdf')
  if (hasPdf) {
    return (
      state.parserChoice === 'mineru' || state.parserChoice === 'mathpix'
    )
  }
  return true
}

function makeBatchItem(filePath: string): BatchParseItem {
  return {
    id:
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    filePath,
    fileType: detectFileType(filePath),
    runId: null,
    status: 'pending',
    error: null,
    resultId: null,
  }
}

function parserForFileType(state: WizardState, fileType: FileType): string {
  if (fileType === 'pdf') return state.parserChoice ?? 'auto'
  return 'auto'
}

interface ParsePageProps {
  apiBase: string
  apiToken: string
}

export default function ParsePage({ apiBase, apiToken }: ParsePageProps): JSX.Element {
  const navigate = useNavigate()
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE)
  const [isParsing, setIsParsing] = useState(false)
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  // Parses funnel through a single backend worker, so a freshly submitted
  // job may sit in 'queued' until earlier parses finish. Track that
  // separately from `isParsing` so we can tell the user it's waiting.
  const [parseState, setParseState] = useState<'queued' | 'running' | null>(
    null,
  )
  const [result, setResult] = useState<ParseResultData | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const pollRef = useRef<number | null>(null)

  // Batch mode: when the user drops 2+ files we switch to a list view that
  // submits each file to the backend's parse queue and tracks per-row state.
  const [batchItems, setBatchItems] = useState<BatchParseItem[]>([])
  const [isBatchSubmitting, setIsBatchSubmitting] = useState(false)
  const isBatchMode = batchItems.length > 0
  // Keep a ref so the polling effect can read the latest list without
  // re-creating the interval on every status update.
  const batchItemsRef = useRef(batchItems)
  batchItemsRef.current = batchItems

  // Stop polling when the component unmounts mid-parse so we don't hammer
  // the backend after the user navigates away.
  useEffect(() => {
    return () => {
      if (pollRef.current !== null) {
        window.clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [])

  const stopPolling = useCallback((): void => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const updateBatchItem = useCallback(
    (id: string, patch: Partial<BatchParseItem>): void => {
      setBatchItems((prev) =>
        prev.map((item) => (item.id === id ? { ...item, ...patch } : item)),
      )
    },
    [],
  )

  const handleRunParse = useCallback(async (): Promise<void> => {
    if (!canRunParse(state)) return
    setIsParsing(true)
    setParseState('queued')
    setErrorMessage(null)
    setResult(null)
    setActiveRunId(null)
    const parser = parserForFileType(state, state.fileType)
    const mineruBackend = parser === 'mineru' ? state.mineruBackend : null

    let runId: string
    try {
      const response = await apiFetch(apiBase, apiToken, '/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: state.filePath,
          parser,
          mineru_backend: mineruBackend,
        }),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || `Parse failed (${response.status})`)
      }
      const submitData = await response.json()
      runId = submitData.run_id
      if (!runId) {
        throw new Error('Server did not return a run_id')
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Parse failed')
      setIsParsing(false)
      setParseState(null)
      return
    }

    setActiveRunId(runId)
    appendRunIdToHistory(runId)

    // Poll status; on completion fetch the result and render inline.
    stopPolling()
    pollRef.current = window.setInterval(async () => {
      try {
        const statusResponse = await apiFetch(
          apiBase,
          apiToken,
          `/api/status/${runId}`,
        )
        if (!statusResponse.ok) return
        const status = await statusResponse.json()
        if (status.state === 'queued') {
          setParseState('queued')
        } else if (status.state === 'running') {
          setParseState('running')
        } else if (status.state === 'completed') {
          stopPolling()
          const resultsResponse = await apiFetch(
            apiBase,
            apiToken,
            `/api/results/${runId}`,
          )
          if (!resultsResponse.ok) {
            const data = await resultsResponse.json().catch(() => ({}))
            setErrorMessage(data.detail || 'Failed to fetch parse result')
            setIsParsing(false)
            setParseState(null)
            return
          }
          const data: ParseResultData = await resultsResponse.json()
          setResult(data)
          setIsParsing(false)
          setParseState(null)
        } else if (status.state === 'failed') {
          stopPolling()
          setErrorMessage(status.error || 'Parse failed')
          setIsParsing(false)
          setParseState(null)
        }
      } catch {
        // Transient network issue — keep polling
      }
    }, 1000)
  }, [state, apiBase, apiToken, stopPolling])

  const handleClearResult = useCallback((): void => {
    stopPolling()
    setResult(null)
    setActiveRunId(null)
    setErrorMessage(null)
    setParseState(null)
  }, [stopPolling])

  const handleViewInJobs = useCallback((): void => {
    if (activeRunId) navigate(`/jobs/${activeRunId}`)
  }, [activeRunId, navigate])

  const handleStartReview = useCallback((): void => {
    if (!result) return
    navigate(`/?parsed=${encodeURIComponent(result.id)}`)
  }, [result, navigate])

  // Multi-file drop entry point. The host (this page) takes over rendering;
  // the first file is set as the wizard's "current" file so the parser-config
  // panel below the dropzone reflects the right format.
  const handleMultiFileDrop = useCallback(
    (paths: string[]): void => {
      if (paths.length === 0) return
      // Drop any single-file polling/result so the two modes don't overlap.
      stopPolling()
      setIsParsing(false)
      setParseState(null)
      setResult(null)
      setErrorMessage(null)
      setActiveRunId(null)

      const items = paths.map(makeBatchItem).filter((i) => i.fileType !== null)
      if (items.length === 0) return
      // PDFs need an explicit parser choice (MinerU vs Mathpix); other
      // formats use a fixed parser. Surface PDFs first so Step1's config
      // panel renders the PDF parser picker — otherwise a TeX-led batch
      // with PDFs in it would have no way to pick MinerU/Mathpix.
      items.sort((a, b) => {
        const aIsPdf = a.fileType === 'pdf'
        const bIsPdf = b.fileType === 'pdf'
        if (aIsPdf === bIsPdf) return 0
        return aIsPdf ? -1 : 1
      })
      setBatchItems(items)

      const first = items[0]
      if (first.fileType) {
        dispatch({
          type: 'SET_FILE',
          filePath: first.filePath,
          fileType: first.fileType,
        })
      }
    },
    [stopPolling],
  )

  const handleClearBatch = useCallback((): void => {
    setBatchItems([])
    setIsBatchSubmitting(false)
    dispatch({ type: 'CLEAR_FILE' })
  }, [])

  const handleRemoveBatchItem = useCallback((id: string): void => {
    const current = batchItemsRef.current
    const idx = current.findIndex((item) => item.id === id)
    if (idx < 0) return
    const next = current.filter((_, i) => i !== idx)
    setBatchItems(next)
    // If the removed row was the one driving Step1's parser-config panel,
    // re-point Step1 at the new first row (or clear it if the batch is
    // empty). Otherwise the sync effect below would think the user picked
    // a different file and wipe the whole batch.
    if (idx === 0) {
      if (next.length === 0) {
        dispatch({ type: 'CLEAR_FILE' })
      } else if (next[0].fileType) {
        dispatch({
          type: 'SET_FILE',
          filePath: next[0].filePath,
          fileType: next[0].fileType,
        })
      }
    }
  }, [])

  const handleSubmitBatch = useCallback(async (): Promise<void> => {
    if (!canRunBatch(state, batchItems)) return
    setIsBatchSubmitting(true)
    // Snapshot the pending IDs at start so newly-added rows (none in current
    // UI, but defensive) aren't accidentally submitted by this run.
    const pendingIds = batchItems
      .filter((item) => item.status === 'pending')
      .map((item) => item.id)

    for (const id of pendingIds) {
      const item = batchItemsRef.current.find((i) => i.id === id)
      if (!item || item.status !== 'pending') continue
      updateBatchItem(id, { status: 'submitting', error: null })

      const parser = parserForFileType(state, item.fileType)
      const mineruBackend = parser === 'mineru' ? state.mineruBackend : null

      try {
        const response = await apiFetch(apiBase, apiToken, '/api/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            file_path: item.filePath,
            parser,
            mineru_backend: mineruBackend,
          }),
        })
        if (!response.ok) {
          const data = await response.json().catch(() => ({}))
          throw new Error(data.detail || `Submit failed (${response.status})`)
        }
        const submitData = await response.json()
        const runId: string | undefined = submitData.run_id
        if (!runId) throw new Error('Server did not return a run_id')
        appendRunIdToHistory(runId)
        updateBatchItem(id, { runId, status: 'queued' })
      } catch (err) {
        updateBatchItem(id, {
          status: 'failed',
          error: err instanceof Error ? err.message : 'Submit failed',
        })
      }
    }

    setIsBatchSubmitting(false)
  }, [apiBase, apiToken, batchItems, state, updateBatchItem])

  // Keep the wizard's "current file" in sync with the batch. If the user
  // clears the file (Step1's "change" link → CLEAR_FILE) or drops a single
  // new file via Step1 while a batch was active, exit batch mode so the two
  // panes don't show conflicting state.
  useEffect(() => {
    if (batchItems.length === 0) return
    if (state.filePath === '') {
      setBatchItems([])
      return
    }
    if (!batchItems.some((i) => i.filePath === state.filePath)) {
      setBatchItems([])
    }
  }, [state.filePath, batchItems])

  // Batch polling: while at least one item is queued/running, poll each
  // in-flight runId every second. The effect re-arms only when transitioning
  // between "has in-flight items" and "no in-flight items" so per-tick status
  // updates don't restart the interval.
  const hasInFlightBatch = batchItems.some(
    (item) =>
      item.runId !== null &&
      (item.status === 'queued' || item.status === 'running'),
  )

  useEffect(() => {
    if (!hasInFlightBatch) return
    const interval = window.setInterval(async () => {
      const items = batchItemsRef.current
      const inFlight = items.filter(
        (item) =>
          item.runId !== null &&
          (item.status === 'queued' || item.status === 'running'),
      )
      if (inFlight.length === 0) return

      for (const item of inFlight) {
        if (!item.runId) continue
        try {
          const statusResponse = await apiFetch(
            apiBase,
            apiToken,
            `/api/status/${item.runId}`,
          )
          if (!statusResponse.ok) continue
          const status = await statusResponse.json()
          const nextState: BatchItemStatus | null =
            status.state === 'queued'
              ? 'queued'
              : status.state === 'running'
                ? 'running'
                : status.state === 'completed'
                  ? 'completed'
                  : status.state === 'failed'
                    ? 'failed'
                    : null
          if (nextState === null) continue

          if (nextState === 'completed') {
            // Pull /api/results to get the parsed-document id used for the
            // "Review" link. If that fails we still mark completed but keep
            // resultId null (no link is shown).
            let resultId: string | null = null
            try {
              const resultsResponse = await apiFetch(
                apiBase,
                apiToken,
                `/api/results/${item.runId}`,
              )
              if (resultsResponse.ok) {
                const data = await resultsResponse.json()
                if (typeof data?.id === 'string') resultId = data.id
              }
            } catch {
              // Leave resultId null
            }
            updateBatchItem(item.id, { status: 'completed', resultId })
          } else if (nextState === 'failed') {
            updateBatchItem(item.id, {
              status: 'failed',
              error: status.error || 'Parse failed',
            })
          } else if (nextState !== item.status) {
            updateBatchItem(item.id, { status: nextState })
          }
        } catch {
          // Transient network issue — keep polling
        }
      }
    }, 1000)

    return () => window.clearInterval(interval)
  }, [hasInFlightBatch, apiBase, apiToken, updateBatchItem])

  const canRun = canRunParse(state)
  const canRunBatchNow = canRunBatch(state, batchItems)
  const batchHasPending = batchItems.some((i) => i.status === 'pending')

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-8 pb-12 pt-6">
        <header className="mb-6">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            Parse only
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Run the ingestion step in isolation. Drop one paper for an inline
            preview, or many to queue them up — only one parses at a time.
          </p>
        </header>

        <Step1ImportFile
          apiBase={apiBase}
          apiToken={apiToken}
          state={state}
          dispatch={dispatch}
          onMultiFileDrop={handleMultiFileDrop}
        />

        {!isBatchMode && (
          <SingleParseControls
            canRun={canRun}
            isParsing={isParsing}
            parseState={parseState}
            activeRunId={activeRunId}
            hasResultOrError={!!(result || errorMessage)}
            onRun={handleRunParse}
            onClearResult={handleClearResult}
            onViewInJobs={handleViewInJobs}
          />
        )}

        {isBatchMode && (
          <>
            <BatchParseList
              items={batchItems}
              isSubmitting={isBatchSubmitting}
              onClear={handleClearBatch}
              onRemoveItem={handleRemoveBatchItem}
            />
            <div className="flex items-center gap-3 mt-4">
              <button
                type="button"
                disabled={
                  !canRunBatchNow || isBatchSubmitting || !batchHasPending
                }
                onClick={handleSubmitBatch}
                className={cn(
                  'btn-primary px-5 py-2 text-sm',
                  (!canRunBatchNow || !batchHasPending) &&
                    'opacity-50 cursor-not-allowed',
                )}
              >
                {isBatchSubmitting ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Submitting…
                  </>
                ) : (
                  <>
                    <Play size={14} strokeWidth={1.8} />
                    Submit batch ({batchItems.filter((i) => i.status === 'pending').length})
                  </>
                )}
              </button>
              <p className="font-serif text-xs text-ink-tertiary italic">
                Files run one-by-one through the parse queue. Safe to navigate
                away.
              </p>
            </div>
          </>
        )}

        {!isBatchMode && errorMessage && !result && (
          <ParseErrorCard message={errorMessage} />
        )}

        {!isBatchMode && result && (
          <>
            <div className="card flex items-center gap-3 mt-6 px-4 py-3 bg-success/5 border-success/30">
              <Bookmark size={16} className="text-success shrink-0" strokeWidth={1.8} />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-ink-secondary">
                  Saved to library
                </div>
                <code className="font-mono text-[11px] text-ink-tertiary truncate block">
                  {result.id}
                </code>
              </div>
              <button
                type="button"
                onClick={handleStartReview}
                className="btn-primary px-4 py-2 text-sm shrink-0"
              >
                Start review
                <ArrowRight size={13} strokeWidth={1.8} />
              </button>
            </div>
            <ParseResult result={result} />
          </>
        )}
      </div>
    </div>
  )
}

function SingleParseControls({
  canRun,
  isParsing,
  parseState,
  activeRunId,
  hasResultOrError,
  onRun,
  onClearResult,
  onViewInJobs,
}: {
  canRun: boolean
  isParsing: boolean
  parseState: 'queued' | 'running' | null
  activeRunId: string | null
  hasResultOrError: boolean
  onRun: () => void
  onClearResult: () => void
  onViewInJobs: () => void
}): JSX.Element {
  return (
    <>
      <div className="flex items-center gap-3 mt-6">
        <button
          type="button"
          disabled={!canRun || isParsing}
          onClick={onRun}
          className={cn(
            'btn-primary px-5 py-2 text-sm',
            !canRun && 'opacity-50 cursor-not-allowed',
          )}
        >
          {isParsing ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              {parseState === 'queued' ? 'Queued...' : 'Parsing...'}
            </>
          ) : (
            <>
              <Play size={14} strokeWidth={1.8} />
              Run parse
            </>
          )}
        </button>
        {hasResultOrError && !isParsing && (
          <button
            type="button"
            onClick={onClearResult}
            className="btn-ghost px-3 py-2 text-sm"
          >
            <RotateCcw size={13} />
            Clear result
          </button>
        )}
        {isParsing && activeRunId && (
          <button
            type="button"
            onClick={onViewInJobs}
            className="btn-ghost px-3 py-2 text-sm"
          >
            View in Jobs
            <ArrowRight size={13} strokeWidth={1.8} />
          </button>
        )}
      </div>

      {isParsing && activeRunId && (
        <p className="font-serif text-xs text-ink-tertiary italic mt-3">
          {parseState === 'queued' ? (
            <>
              Waiting for an earlier parse to finish — only one runs at a time.
              Tracked as job{' '}
              <code className="font-mono not-italic">{activeRunId}</code>; safe
              to navigate away.
            </>
          ) : (
            <>
              Tracked as job{' '}
              <code className="font-mono not-italic">{activeRunId}</code> —
              safe to navigate away; the parse keeps running in the
              background.
            </>
          )}
        </p>
      )}
    </>
  )
}

function ParseErrorCard({ message }: { message: string }): JSX.Element {
  const lowered = message.toLowerCase()
  const hint = lowered.includes('mineru')
    ? {
        text: 'Install MinerU from',
        linkLabel: 'Integrations',
        linkTo: '/integrations',
      }
    : lowered.includes('mathpix')
      ? {
          text: 'Configure Mathpix credentials on',
          linkLabel: 'Integrations',
          linkTo: '/integrations',
        }
      : null

  return (
    <div className="card mt-6 bg-danger/5 border-danger/30 px-4 py-4">
      <div className="text-xs font-semibold text-danger mb-1.5 tracking-wider uppercase">
        Parse failed
      </div>
      <div className="text-sm text-ink-secondary break-words">{message}</div>
      {hint && (
        <div className="text-xs text-ink-tertiary mt-2">
          {hint.text}{' '}
          <Link
            to={hint.linkTo}
            className="text-accent hover:text-accent-hover underline underline-offset-2"
          >
            {hint.linkLabel}
          </Link>
          .
        </div>
      )}
    </div>
  )
}
