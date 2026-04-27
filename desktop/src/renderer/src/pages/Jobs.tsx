import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate, NavLink } from 'react-router-dom'
import {
  Loader2, CheckCircle2, XCircle, Circle, FileText, Inbox,
  FileScan, ArrowRight,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'
import { formatElapsed } from '@/lib/formatters'

// ── Types ──────────────────────────────────────────────────────────

interface TaskStatus {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
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

type ReportTab = 'summary' | 'writing' | 'math' | 'polish'

const TAB_LABELS: Record<ReportTab, string> = {
  summary: 'Summary',
  writing: 'Writing',
  math: 'Math',
  polish: 'Polish',
}

function computeAvailableTabs(results: ReviewResults): ReportTab[] {
  const tabs: ReportTab[] = []
  if (results.summary && results.summary.trim()) tabs.push('summary')
  if (results.polish_report && results.polish_report.trim()) tabs.push('polish')
  if (results.writing_report && results.writing_report.trim()) tabs.push('writing')
  if (results.math_report && results.math_report.trim()) tabs.push('math')
  return tabs
}

function jobKind(status: RunStatus | null | undefined): JobKind {
  return status?.kind ?? 'review'
}

function readRunIds(): string[] {
  try {
    const stored = localStorage.getItem('revisica_run_ids')
    if (!stored) return []
    const parsed = JSON.parse(stored)
    return Array.isArray(parsed)
      ? parsed.filter((id): id is string => typeof id === 'string')
      : []
  } catch {
    // Corrupted storage — reset so we don't keep crashing the page.
    localStorage.removeItem('revisica_run_ids')
    return []
  }
}

// ── Selected-job detail state ──────────────────────────────────────

interface SelectedJobDetail {
  status: RunStatus | null
  results: JobResults | null
  activeTab: ReportTab
  errorMessage: string | null
}

const INITIAL_SELECTED_JOB_DETAIL: SelectedJobDetail = {
  status: null,
  results: null,
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

  // Poll all known jobs
  useEffect(() => {
    const runIds = readRunIds()
    if (runIds.length === 0) return

    const fetchAllJobs = async (): Promise<void> => {
      const statuses: RunStatus[] = []
      for (const id of runIds) {
        try {
          const response = await apiFetch(apiBase, apiToken, `/api/status/${id}`)
          if (response.ok) statuses.push(await response.json())
        } catch {
          // Skip unreachable jobs
        }
      }
      statuses.sort((a, b) =>
        (b.started_at ?? '').localeCompare(a.started_at ?? ''),
      )
      setJobs(statuses)
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
            // lives — summary is just the header).
            let activeTab: ReportTab = 'summary'
            if (payload.kind === 'review') {
              const tabs = computeAvailableTabs(payload)
              const firstReportTab = tabs.find((tab) => tab !== 'summary')
              activeTab = firstReportTab ?? tabs[0] ?? 'summary'
            }
            setSelectedJobDetail((prev) => ({
              ...prev,
              results: payload,
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

  const { status: selectedStatus, results, activeTab, errorMessage } = selectedJobDetail

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
          <JobProgressView runId={runId} status={selectedStatus} />
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
            activeTab={activeTab}
            onTabChange={(tab) =>
              setSelectedJobDetail((prev) => ({ ...prev, activeTab: tab }))
            }
            content={reportContent}
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
}: {
  job: RunStatus
  isActive: boolean
}): JSX.Element {
  const kind = jobKind(job)
  const KindIcon = kind === 'parse' ? FileScan : FileText
  return (
    <NavLink
      to={`/jobs/${job.run_id}`}
      className={cn(
        'flex items-center gap-2.5 px-3 py-2.5 rounded-lg',
        'transition-colors duration-150',
        isActive
          ? 'bg-paper-50 shadow-subtle'
          : 'hover:bg-paper-300/30',
      )}
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
        <div className="text-[10px] text-ink-faint mt-0.5">
          {kind === 'parse' ? 'Parse · ' : ''}
          {job.started_at
            ? new Date(job.started_at).toLocaleTimeString()
            : ''}
        </div>
      </div>
    </NavLink>
  )
}

function JobProgressView({
  runId,
  status,
}: {
  runId: string
  status: RunStatus
}): JSX.Element {
  return (
    <div className="max-w-2xl mx-auto px-8 py-10">
      <div className="flex items-center gap-3 mb-8">
        <h2 className="font-serif text-xl font-semibold text-ink">
          {runId.slice(0, 8)}
        </h2>
        <StateBadge state={status.state} />
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

      {status.state === 'failed' && status.error && (
        <div className="mt-6 rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
          {status.error}
        </div>
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
  activeTab,
  onTabChange,
  content,
}: {
  runId: string
  results: ReviewResults
  activeTab: ReportTab
  onTabChange: (tab: ReportTab) => void
  content: string
}): JSX.Element {
  const availableTabs = computeAvailableTabs(results)

  return (
    <div className="max-w-3xl mx-auto px-8 py-10">
      {/* Header */}
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

      {/* Report content */}
      <div className="card px-6 py-6">
        <div className="prose-paper">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
