import { useReducer, useState, useCallback, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Play, Loader2, Bookmark, ArrowRight, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'
import Step1ImportFile from '@/pages/NewJob/Step1ImportFile'
import {
  DEFAULT_MINERU_BACKEND,
  DEFAULT_VENUE_PROFILE,
  type WizardAction,
  type WizardState,
} from '@/pages/NewJob/types'
import ParseResult, { type ParseResultData } from './ParseResult'

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

  const handleRunParse = useCallback(async (): Promise<void> => {
    if (!canRunParse(state)) return
    setIsParsing(true)
    setParseState('queued')
    setErrorMessage(null)
    setResult(null)
    setActiveRunId(null)
    const parser =
      state.fileType === 'pdf' ? state.parserChoice ?? 'auto' : 'auto'
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

  const canRun = canRunParse(state)

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-8 pb-12 pt-6">
        <header className="mb-6">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            Parse only
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Run the ingestion step in isolation. No review, no cost — just the parsed document.
          </p>
        </header>

        <Step1ImportFile
          apiBase={apiBase}
          apiToken={apiToken}
          state={state}
          dispatch={dispatch}
        />

        <div className="flex items-center gap-3 mt-6">
          <button
            type="button"
            disabled={!canRun || isParsing}
            onClick={handleRunParse}
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
          {(result || errorMessage) && !isParsing && (
            <button
              type="button"
              onClick={handleClearResult}
              className="btn-ghost px-3 py-2 text-sm"
            >
              <RotateCcw size={13} />
              Clear result
            </button>
          )}
          {isParsing && activeRunId && (
            <button
              type="button"
              onClick={handleViewInJobs}
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

        {errorMessage && !result && (
          <ParseErrorCard message={errorMessage} />
        )}

        {result && (
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
