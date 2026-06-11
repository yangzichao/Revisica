import { useState, useEffect, useMemo, useCallback } from 'react'
import { useParams, useNavigate, NavLink } from 'react-router-dom'
import {
  Loader2, CheckCircle2, XCircle, Circle, FileText, Inbox,
  FileScan, ArrowRight, Archive, RotateCcw, Trash2,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'
import { formatElapsed } from '@/lib/formatters'
import { useDeleteConfirm } from '@/pages/Library/useDeleteConfirm'
import AnnotatedReviewView from './annotated/AnnotatedReviewView'
import { fetchRunFindings } from './annotated/findingsApi'
import type { FindingsPayload } from './annotated/types'

// ── Types ──────────────────────────────────────────────────────────

interface TaskStatus {
  name: string
  // ``cached`` is reported by the MinerU parser when a chunk is reused from
  // the on-disk cache instead of being recomputed — surface it visually so
  // users can see resumed jobs skipping completed work.
  //
  // ``fallback`` means the primary backend (typically vlm) crashed on this
  // chunk and the parser is now retrying it with the fallback backend
  // (typically pipeline). The row is still "in progress" — we keep
  // spinning — but the icon shade is darker to signal "retry, expect
  // longer runtime".
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cached' | 'fallback'
  detail?: string
}

type JobKind = 'review' | 'parse'

interface RunStatus {
  run_id: string
  // `kind` is optional so that pre-existing run records (from before parse
  // became a tracked job) still deserialize cleanly; default to 'review'.
  kind?: JobKind
  // Parse jobs sit in 'queued' until the single parse worker picks them up.
  state: 'queued' | 'running' | 'completed' | 'failed'
  started_at?: string
  tasks: TaskStatus[]
  error?: string
  // The submitted request, echoed back by the server — used to derive a
  // human-readable source label for the job list.
  config?: Record<string, unknown>
  // Set when this run was created via the retry endpoint.
  retry_of?: string
}

interface ReviewResults {
  run_id: string
  kind: 'review'
  summary: string
  writing_report?: string
  math_report?: string
  polish_report?: string
  run_dir: string
}

interface ParseResults {
  run_id: string
  kind: 'parse'
  id: string
  parser_used: string
  source_path: string
  title: string
  authors: string[]
  abstract: string
  section_count: number
  parsed_at: string
  elapsed_ms: number
}

type JobResults = ReviewResults | ParseResults

type ReportTab = 'summary' | 'annotated' | 'writing' | 'math' | 'polish'

const TAB_LABELS: Record<ReportTab, string> = {
  summary: 'Summary',
  annotated: 'Annotated',
  writing: 'Writing',
  math: 'Math',
  polish: 'Polish',
}

function computeAvailableTabs(
  results: ReviewResults,
  findings: FindingsPayload | null,
): ReportTab[] {
  const tabs: ReportTab[] = []
  if (results.summary && results.summary.trim()) tabs.push('summary')
  // The annotated view is the richest representation — list it right
  // after Summary; the default-tab logic below also lands on it first.
  if (findings && findings.findings.length > 0) tabs.push('annotated')
  if (results.polish_report && results.polish_report.trim()) tabs.push('polish')
  if (results.writing_report && results.writing_report.trim()) tabs.push('writing')
  if (results.math_report && results.math_report.trim()) tabs.push('math')
  return tabs
}

function jobKind(status: RunStatus | null | undefined): JobKind {
  return status?.kind ?? 'review'
}

function jobSourceLabel(job: RunStatus): string | null {
  const config = job.config
  if (!config) return null
  const filePath = typeof config.file_path === 'string' ? config.file_path : ''
  if (filePath) {
    const segments = filePath.split('/')
    return segments[segments.length - 1] || filePath
  }
  const parsedDocumentId =
    typeof config.parsed_document_id === 'string'
      ? config.parsed_document_id
      : ''
  return parsedDocumentId || null
}

// ── Selected-job detail state ──────────────────────────────────────

interface SelectedJobDetail {
  status: RunStatus | null
  results: JobResults | null
  findings: FindingsPayload | null
  activeTab: ReportTab
  errorMessage: string | null
}

const INITIAL_SELECTED_JOB_DETAIL: SelectedJobDetail = {
  status: null,
  results: null,
  findings: null,
  activeTab: 'summary',
  errorMessage: null,
}

// ── Main Component ─────────────────────────────────────────────────

export default function Jobs({
  apiBase,
  apiToken,
}: {
  apiBase: string
  apiToken: string
}): JSX.Element {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  const [jobs, setJobs] = useState<RunStatus[]>([])
  const [selectedJobDetail, setSelectedJobDetail] = useState<SelectedJobDetail>(
    INITIAL_SELECTED_JOB_DETAIL,
  )

  // Poll the server-side run list. The backend persists runs to disk, so
  // this also shows history (and any interrupted runs) from before the
  // last app restart — no client-side run-id bookkeeping needed.
  useEffect(() => {
    const fetchAllJobs = async (): Promise<void> => {
      try {
        const response = await apiFetch(apiBase, apiToken, '/api/runs')
        if (!response.ok) return
        const payload = await response.json()
        if (Array.isArray(payload.runs)) {
          setJobs(payload.runs)
        }
      } catch {
        // Backend unreachable — keep showing the last known list.
      }
    }

    fetchAllJobs()
    const interval = setInterval(fetchAllJobs, 2000)
    return () => clearInterval(interval)
  }, [apiBase, apiToken])

  // Fetch detail for the selected job
  useEffect(() => {
    if (!runId) {
      setSelectedJobDetail(INITIAL_SELECTED_JOB_DETAIL)
      return
    }

    // Atomic reset when runId changes
    setSelectedJobDetail(INITIAL_SELECTED_JOB_DETAIL)

    const poll = setInterval(async () => {
      try {
        const response = await apiFetch(apiBase, apiToken, `/api/status/${runId}`)
        if (!response.ok) {
          setSelectedJobDetail((prev) => ({ ...prev, errorMessage: 'Failed to fetch job status' }))
          return
        }

        const jobStatus: RunStatus = await response.json()
        setSelectedJobDetail((prev) => ({ ...prev, status: jobStatus }))

        if (jobStatus.state === 'completed') {
          clearInterval(poll)
          const resultsResponse = await apiFetch(
            apiBase,
            apiToken,
            `/api/results/${runId}`,
          )
          if (resultsResponse.ok) {
            const payload: JobResults = await resultsResponse.json()
            // Parse jobs have nothing to tab through; review jobs default
            // to the first non-summary report (where the actionable content
            // lives — summary is just the header). When anchored findings
            // exist, that first tab is the Annotated view.
            let activeTab: ReportTab = 'summary'
            let findings: FindingsPayload | null = null
            if (payload.kind === 'review') {
              findings = await fetchRunFindings(apiBase, apiToken, runId).catch(
                () => null,
              )
              const tabs = computeAvailableTabs(payload, findings)
              const firstReportTab = tabs.find((tab) => tab !== 'summary')
              activeTab = firstReportTab ?? tabs[0] ?? 'summary'
            }
            setSelectedJobDetail((prev) => ({
              ...prev,
              results: payload,
              findings,
              activeTab,
            }))
          }
        } else if (jobStatus.state === 'failed') {
          clearInterval(poll)
        }
      } catch {
        setSelectedJobDetail((prev) => ({ ...prev, errorMessage: 'Lost connection to backend' }))
      }
    }, 1000)

    return () => clearInterval(poll)
  }, [runId, apiBase, apiToken])

  // Auto-select the first in-flight job (running or queued) if none is selected
  useEffect(() => {
    if (!runId && jobs.length > 0) {
      const inflightJob = jobs.find(
        (job) => job.state === 'running' || job.state === 'queued',
      )
      if (inflightJob) {
        navigate(`/jobs/${inflightJob.run_id}`, { replace: true })
      }
    }
  }, [runId, jobs, navigate])

  // Retry a failed job: the server relaunches it with the original config
  // (parses resume from cached chunks), then we jump to the new run.
  const [retryState, setRetryState] = useState<{
    inFlight: boolean
    error: string | null
  }>({ inFlight: false, error: null })

  useEffect(() => {
    setRetryState({ inFlight: false, error: null })
  }, [runId])

  const handleRetry = useCallback(async (): Promise<void> => {
    if (!runId) return
    setRetryState({ inFlight: true, error: null })
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        `/api/runs/${runId}/retry`,
        { method: 'POST' },
      )
      const data = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(data.detail || `Retry failed (${response.status})`)
      }
      setRetryState({ inFlight: false, error: null })
      navigate(`/jobs/${data.run_id}`)
    } catch (err) {
      setRetryState({
        inFlight: false,
        error: err instanceof Error ? err.message : 'Retry failed',
      })
    }
  }, [runId, apiBase, apiToken, navigate])

  const handleDelete = useCallback(
    async (jobRunId: string): Promise<void> => {
      const response = await apiFetch(apiBase, apiToken, `/api/runs/${jobRunId}`, {
        method: 'DELETE',
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || `Delete failed (${response.status})`)
      }
      setJobs((previous) => previous.filter((job) => job.run_id !== jobRunId))
      if (jobRunId === runId) {
        navigate('/jobs', { replace: true })
      }
    },
    [apiBase, apiToken, runId, navigate],
  )

  const { status: selectedStatus, results, findings, activeTab, errorMessage } =
    selectedJobDetail

  // Reviews launched from the Library carry the parsed document id; the
  // annotated view needs it to resolve asset image URLs.
  const parsedDocumentId =
    typeof selectedStatus?.config?.parsed_document_id === 'string'
      ? selectedStatus.config.parsed_document_id
      : undefined

  const reportContent = useMemo((): string => {
    if (!results || results.kind !== 'review') return ''
    switch (activeTab) {
      case 'writing':
        return results.writing_report ?? '*No writing report available*'
      case 'math':
        return results.math_report ?? '*No math report available*'
      case 'polish':
        return results.polish_report ?? '*No polish report available*'
      default:
        return results.summary
    }
  }, [activeTab, results])

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Job list panel */}
      <aside className="w-56 shrink-0 overflow-y-auto bg-paper-200/50 border-r border-paper-300">
        <div className="px-4 pt-5 pb-3">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-faint">
            Jobs
          </span>
        </div>

        {jobs.length === 0 ? (
          <EmptyJobList />
        ) : (
          <div className="px-2 space-y-0.5 pb-4">
            {jobs.map((job) => (
              <JobListItem
                key={job.run_id}
                job={job}
                isActive={job.run_id === runId}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </aside>

      {/* Detail panel */}
      <div className="flex-1 overflow-y-auto">
        {!runId && <EmptyDetail />}

        {runId && errorMessage && (
          <div className="p-8">
            <div className="rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
              {errorMessage}
            </div>
          </div>
        )}

        {runId && selectedStatus && !results && (
          <JobProgressView
            runId={runId}
            status={selectedStatus}
            onRetry={handleRetry}
            retryInFlight={retryState.inFlight}
            retryError={retryState.error}
          />
        )}

        {runId && results && results.kind === 'parse' && (
          <ParseResultsView
            runId={runId}
            results={results}
            onStartReview={() =>
              navigate(`/?parsed=${encodeURIComponent(results.id)}`)
            }
          />
        )}

        {runId && results && results.kind === 'review' && (
          <JobResultsView
            runId={runId}
            results={results}
            findings={findings}
            activeTab={activeTab}
            onTabChange={(tab) =>
              setSelectedJobDetail((prev) => ({ ...prev, activeTab: tab }))
            }
            content={reportContent}
            apiBase={apiBase}
            apiToken={apiToken}
            parsedDocumentId={parsedDocumentId}
          />
        )}
      </div>
    </div>
  )
}

// ── Sub-components ─────────────────────────────────────────────────

function TaskStatusIcon({ status }: { status: string }): JSX.Element {
  switch (status) {
    case 'running':
      return <Loader2 size={16} className="animate-spin text-accent" />
    case 'queued':
    case 'pending':
      return <Circle size={16} className="text-ink-tertiary" strokeWidth={1.5} />
    case 'completed':
      return <CheckCircle2 size={16} className="text-success" />
    case 'cached':
      // Distinct from "completed" — same green semantics, but the archive
      // glyph signals "reused from cache, no work done this run". Important
      // for resumed parses where most chunks land instantly.
      return <Archive size={16} className="text-success" />
    case 'fallback':
      // Same spinner shape as "running" so the row clearly stays
      // in-progress, but rendered in the darker accent shade. Surfaces
      // "this chunk's primary backend crashed and we're retrying with
      // the backup engine (typically vlm → pipeline)" without needing a
      // separate icon family.
      return <Loader2 size={16} className="animate-spin text-accent-hover" />
    case 'failed':
      return <XCircle size={16} className="text-danger" />
    default:
      return <Circle size={16} className="text-ink-faint" />
  }
}

function StateBadge({ state }: { state: string }): JSX.Element {
  const colorClass = {
    queued: 'bg-paper-300/60 text-ink-tertiary',
    running: 'bg-accent/10 text-accent',
    completed: 'bg-success/10 text-success',
    failed: 'bg-danger/10 text-danger',
  }[state] ?? 'bg-paper-200 text-ink-tertiary'

  return (
    <span
      className={cn(
        'text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full',
        colorClass,
      )}
    >
      {state}
    </span>
  )
}

function EmptyJobList(): JSX.Element {
  return (
    <div className="flex flex-col items-center pt-20 px-4 text-center">
      <Inbox size={28} className="text-ink-faint mb-3" strokeWidth={1.2} />
      <p className="text-sm text-ink-tertiary font-medium">No jobs yet</p>
      <p className="text-xs text-ink-faint mt-1">Start a review from New</p>
    </div>
  )
}

function EmptyDetail(): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center h-full text-ink-tertiary">
      <FileText size={36} className="mb-3 text-ink-faint" strokeWidth={1.1} />
      <p className="text-sm">Select a job to view details</p>
    </div>
  )
}

function JobListItem({
  job,
  isActive,
  onDelete,
}: {
  job: RunStatus
  isActive: boolean
  onDelete: (runId: string) => Promise<void>
}): JSX.Element {
  const kind = jobKind(job)
  const KindIcon = kind === 'parse' ? FileScan : FileText
  const sourceLabel = jobSourceLabel(job)
  const isFinished = job.state === 'completed' || job.state === 'failed'

  const { isConfirming, isDeleting, request, cancel } = useDeleteConfirm({
    perform: () => onDelete(job.run_id),
  })

  return (
    <NavLink
      to={`/jobs/${job.run_id}`}
      className={cn(
        'group flex items-center gap-2.5 px-3 py-2.5 rounded-lg',
        'transition-colors duration-150',
        isActive
          ? 'bg-paper-50 shadow-subtle'
          : 'hover:bg-paper-300/30',
      )}
      onMouseLeave={() => {
        if (isConfirming) cancel()
      }}
    >
      <TaskStatusIcon status={job.state} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <KindIcon
            size={11}
            strokeWidth={1.5}
            className="text-ink-faint shrink-0"
          />
          <div className="font-mono text-xs font-medium text-ink truncate">
            {job.run_id.slice(0, 8)}
          </div>
        </div>
        <div className="text-[10px] text-ink-faint mt-0.5 truncate">
          {kind === 'parse' ? 'Parse · ' : ''}
          {sourceLabel ? `${sourceLabel} · ` : ''}
          {job.started_at
            ? new Date(job.started_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
              })
            : ''}
        </div>
      </div>
      {isFinished && (
        <button
          type="button"
          title={isConfirming ? 'Click again to remove' : 'Remove from history'}
          aria-label={
            isConfirming
              ? `Confirm removing job ${job.run_id.slice(0, 8)}`
              : `Remove job ${job.run_id.slice(0, 8)}`
          }
          disabled={isDeleting}
          onClick={(event) => {
            // The row itself is a NavLink — keep the click from navigating.
            event.preventDefault()
            event.stopPropagation()
            void request()
          }}
          className={cn(
            'shrink-0 p-1 rounded-md border-none bg-transparent cursor-pointer',
            'transition-opacity duration-150',
            isConfirming
              ? 'opacity-100 text-danger'
              : 'opacity-0 group-hover:opacity-100 text-ink-faint hover:text-danger',
          )}
        >
          {isDeleting ? (
            <Loader2 size={13} className="animate-spin" />
          ) : (
            <Trash2 size={13} strokeWidth={1.6} />
          )}
        </button>
      )}
    </NavLink>
  )
}

function JobProgressView({
  runId,
  status,
  onRetry,
  retryInFlight,
  retryError,
}: {
  runId: string
  status: RunStatus
  onRetry: () => void
  retryInFlight: boolean
  retryError: string | null
}): JSX.Element {
  return (
    <div className="max-w-2xl mx-auto px-8 py-10">
      <div className="flex items-center gap-3 mb-8">
        <h2 className="font-serif text-xl font-semibold text-ink">
          {runId.slice(0, 8)}
        </h2>
        <StateBadge state={status.state} />
        {status.retry_of && (
          <span className="text-[11px] text-ink-faint">
            retry of{' '}
            <NavLink
              to={`/jobs/${status.retry_of}`}
              className="font-mono underline decoration-dotted hover:text-ink-secondary"
            >
              {status.retry_of.slice(0, 8)}
            </NavLink>
          </span>
        )}
      </div>

      <div className="card divide-y divide-paper-300/60">
        {status.tasks.map((task) => (
          <div key={task.name} className="flex items-center gap-3 px-5 py-3.5">
            <TaskStatusIcon status={task.status} />
            <span className="text-sm text-ink flex-1">{task.name}</span>
            {task.detail && (
              <span className="text-xs text-ink-faint">{task.detail}</span>
            )}
          </div>
        ))}
      </div>

      {status.state === 'failed' && (
        <>
          {status.error && (
            <div className="mt-6 rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
              {status.error}
            </div>
          )}
          <button
            type="button"
            onClick={onRetry}
            disabled={retryInFlight}
            className="btn-primary mt-5 px-5 py-2 text-sm"
          >
            {retryInFlight ? (
              <Loader2 size={13} className="animate-spin" />
            ) : (
              <RotateCcw size={13} strokeWidth={1.8} />
            )}
            Retry job
          </button>
          {retryError && (
            <p className="mt-3 text-xs text-danger">{retryError}</p>
          )}
        </>
      )}
    </div>
  )
}

function ParseResultsView({
  runId,
  results,
  onStartReview,
}: {
  runId: string
  results: ParseResults
  onStartReview: () => void
}): JSX.Element {
  return (
    <div className="max-w-2xl mx-auto px-8 py-10">
      <div className="flex items-center gap-3 mb-1">
        <h2 className="font-serif text-xl font-semibold text-ink">
          {runId.slice(0, 8)}
        </h2>
        <StateBadge state="completed" />
        <span className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full bg-paper-200 text-ink-tertiary">
          Parse
        </span>
      </div>
      <p className="text-xs text-ink-faint font-mono mb-8 truncate">
        {results.source_path}
      </p>

      <div className="card px-5 py-5 mb-6">
        <div className="text-xs font-semibold uppercase tracking-wider text-ink-faint mb-3">
          Parsed document
        </div>
        <div className="space-y-2 text-sm">
          {results.title && (
            <div>
              <span className="text-ink-tertiary">Title: </span>
              <span className="text-ink font-medium">{results.title}</span>
            </div>
          )}
          {results.authors.length > 0 && (
            <div>
              <span className="text-ink-tertiary">Authors: </span>
              <span className="text-ink">{results.authors.join(', ')}</span>
            </div>
          )}
          <div>
            <span className="text-ink-tertiary">Parser: </span>
            <span className="text-ink font-mono">{results.parser_used}</span>
          </div>
          <div>
            <span className="text-ink-tertiary">Sections: </span>
            <span className="text-ink">{results.section_count}</span>
          </div>
          <div>
            <span className="text-ink-tertiary">Elapsed: </span>
            <span className="text-ink">{formatElapsed(results.elapsed_ms)}</span>
          </div>
          <div>
            <span className="text-ink-tertiary">ID: </span>
            <code className="font-mono text-[11px] text-ink-tertiary">
              {results.id}
            </code>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={onStartReview}
        className="btn-primary px-5 py-2 text-sm"
      >
        Start review
        <ArrowRight size={13} strokeWidth={1.8} />
      </button>
    </div>
  )
}

function JobResultsView({
  runId,
  results,
  findings,
  activeTab,
  onTabChange,
  content,
  apiBase,
  apiToken,
  parsedDocumentId,
}: {
  runId: string
  results: ReviewResults
  findings: FindingsPayload | null
  activeTab: ReportTab
  onTabChange: (tab: ReportTab) => void
  content: string
  apiBase: string
  apiToken: string
  parsedDocumentId?: string
}): JSX.Element {
  const availableTabs = computeAvailableTabs(results, findings)
  // The annotated view scrolls its two panes internally, so its layout
  // pins to the panel height; the markdown tabs scroll in the parent.
  const isAnnotated = activeTab === 'annotated' && findings !== null

  const header = (
    <div className={cn('mx-auto w-full px-8 pt-10', isAnnotated ? 'max-w-6xl' : 'max-w-3xl')}>
      <div className="flex items-center gap-3 mb-1">
        <h2 className="font-serif text-xl font-semibold text-ink">
          {runId.slice(0, 8)}
        </h2>
        <StateBadge state="completed" />
      </div>
      <p className="text-xs text-ink-faint font-mono mb-8 truncate">
        {results.run_dir}
      </p>

      {/* Report tabs — only show tabs with content */}
      {availableTabs.length > 1 && (
        <div className="flex gap-1 mb-6 p-1 rounded-lg bg-paper-200/60">
          {availableTabs.map((tab) => (
            <button
              key={tab}
              onClick={() => onTabChange(tab)}
              className={cn(
                'flex-1 px-4 py-2 text-sm font-medium rounded-md',
                'transition-colors duration-150 border-none cursor-pointer',
                tab === activeTab
                  ? 'bg-paper-50 text-ink shadow-subtle'
                  : 'bg-transparent text-ink-tertiary hover:text-ink-secondary',
              )}
            >
              {TAB_LABELS[tab]}
            </button>
          ))}
        </div>
      )}
    </div>
  )

  if (isAnnotated) {
    return (
      <div className="h-full flex flex-col overflow-hidden">
        {header}
        <div className="flex-1 min-h-0 mx-auto w-full max-w-6xl border-t border-paper-300">
          <AnnotatedReviewView
            payload={findings}
            apiBase={apiBase}
            apiToken={apiToken}
            parsedDocumentId={parsedDocumentId}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="pb-10">
      {header}
      <div className="max-w-3xl mx-auto w-full px-8">
        {/* Report content */}
        <div className="card px-6 py-6">
          <div className="prose-paper">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  )
}
