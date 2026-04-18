import { useCallback, useEffect, useRef, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { apiFetch } from '@/lib/api'
import ConfigPanel from './ConfigPanel'
import ProgressPanel from './ProgressPanel'
import LeaderboardTable from './LeaderboardTable'
import type {
  BenchmarkConfigDraft,
  BenchmarkRunState,
  ParserAvailability,
} from './types'

const STATUS_POLL_INTERVAL_MS = 1500

const DEFAULT_DRAFT: BenchmarkConfigDraft = {
  parserKeys: ['pandoc', 'tex-basic', 'mineru:pipeline', 'mineru:vlm', 'mineru:hybrid'],
  limit: 3,
  skipGroundTruth: false,
  noPdfDownload: false,
}

export default function IngestionBenchmarkPage({
  apiBase,
  apiToken,
}: {
  apiBase: string
  apiToken: string
}): JSX.Element {
  const [availableParsers, setAvailableParsers] =
    useState<ParserAvailability[] | null>(null)
  const [runState, setRunState] = useState<BenchmarkRunState | null>(null)
  const [draft, setDraft] = useState<BenchmarkConfigDraft>(DEFAULT_DRAFT)
  const [isStarting, setIsStarting] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const [outputDirCopied, setOutputDirCopied] = useState(false)

  const pollTimerRef = useRef<number | null>(null)
  const copyFeedbackTimerRef = useRef<number | null>(null)

  const fetchParsers = useCallback(async () => {
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        '/api/benchmark/ingestion/parsers',
      )
      if (!response.ok) return
      const payload = await response.json()
      setAvailableParsers(payload.parsers ?? [])
    } catch {
      setAvailableParsers([])
    }
  }, [apiBase, apiToken])

  const fetchStatus = useCallback(async () => {
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        '/api/benchmark/ingestion/status',
      )
      if (!response.ok) return
      const payload = await response.json()
      setRunState(payload.state ?? null)
    } catch {
      // Transient — keep polling.
    }
  }, [apiBase, apiToken])

  useEffect(() => {
    void fetchParsers()
    void fetchStatus()
  }, [fetchParsers, fetchStatus])

  // Start / stop a polling loop based on run status.
  useEffect(() => {
    const isRunning = runState?.status === 'running'
    if (!isRunning) {
      if (pollTimerRef.current !== null) {
        window.clearInterval(pollTimerRef.current)
        pollTimerRef.current = null
      }
      return
    }
    if (pollTimerRef.current !== null) return
    pollTimerRef.current = window.setInterval(() => {
      void fetchStatus()
    }, STATUS_POLL_INTERVAL_MS)
    return () => {
      if (pollTimerRef.current !== null) {
        window.clearInterval(pollTimerRef.current)
        pollTimerRef.current = null
      }
    }
  }, [runState?.status, fetchStatus])

  const handleStart = useCallback(async () => {
    setStartError(null)
    setIsStarting(true)
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        '/api/benchmark/ingestion/start',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            parsers: draft.parserKeys,
            limit: draft.limit,
            skip_ground_truth: draft.skipGroundTruth,
            no_pdf_download: draft.noPdfDownload,
          }),
        },
      )
      if (!response.ok) {
        const message = await safeErrorDetail(response)
        setStartError(message)
        return
      }
      const payload = await response.json()
      setRunState(payload.state ?? null)
    } catch (error) {
      setStartError(
        error instanceof Error ? error.message : 'Failed to start benchmark.',
      )
    } finally {
      setIsStarting(false)
    }
  }, [apiBase, apiToken, draft])

  const handleCopyOutputDir = useCallback((path: string) => {
    if (!navigator.clipboard?.writeText) return
    void navigator.clipboard.writeText(path).then(
      () => {
        setOutputDirCopied(true)
        if (copyFeedbackTimerRef.current !== null) {
          window.clearTimeout(copyFeedbackTimerRef.current)
        }
        copyFeedbackTimerRef.current = window.setTimeout(() => {
          setOutputDirCopied(false)
          copyFeedbackTimerRef.current = null
        }, 2000)
      },
      () => undefined,
    )
  }, [])

  useEffect(() => {
    return () => {
      if (copyFeedbackTimerRef.current !== null) {
        window.clearTimeout(copyFeedbackTimerRef.current)
        copyFeedbackTimerRef.current = null
      }
    }
  }, [])

  const isRunning = runState?.status === 'running'

  if (availableParsers === null) {
    return (
      <div className="flex-1 flex items-center justify-center text-sm text-ink-tertiary">
        <Loader2 size={14} className="animate-spin mr-2" />
        Loading benchmark configuration…
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-10 space-y-6">
        <header>
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            Ingestion benchmark
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Run every parser on the same arXiv papers and compare them against
            ground truth.
          </p>
        </header>

        <ConfigPanel
          availableParsers={availableParsers}
          draft={draft}
          onDraftChange={setDraft}
          onStart={handleStart}
          isStarting={isStarting}
          isRunning={!!isRunning}
        />

        {startError && (
          <div className="rounded-md bg-danger/5 border border-danger/30 px-4 py-3 text-sm text-danger">
            {startError}
          </div>
        )}

        {runState && (
          <ProgressPanel
            state={runState}
            onCopyOutputDir={handleCopyOutputDir}
            outputDirCopied={outputDirCopied}
          />
        )}

        {runState && runState.cells.length > 0 && (
          <LeaderboardTable state={runState} />
        )}
      </div>
    </div>
  )
}

async function safeErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') return body.detail
    return JSON.stringify(body)
  } catch {
    return `HTTP ${response.status}`
  }
}
