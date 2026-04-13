import { useState, useEffect } from 'react'
import { useParams, useNavigate, NavLink } from 'react-router-dom'
import {
  Loader2, CheckCircle2, XCircle, Circle, FileText, Inbox,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'

// ── Types ──────────────────────────────────────────────────────────

interface TaskStatus {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  detail?: string
}

interface RunStatus {
  run_id: string
  state: 'running' | 'completed' | 'failed'
  started_at?: string
  tasks: TaskStatus[]
  error?: string
}

interface ReviewResults {
  run_id: string
  summary: string
  writing_report?: string
  math_report?: string
  run_dir: string
}

type ReportTab = 'summary' | 'writing' | 'math'

// ── Main Component ─────────────────────────────────────────────────

export default function Jobs({ apiBase }: { apiBase: string }): JSX.Element {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  const [jobs, setJobs] = useState<RunStatus[]>([])
  const [selectedJob, setSelectedJob] = useState<RunStatus | null>(null)
  const [results, setResults] = useState<ReviewResults | null>(null)
  const [activeTab, setActiveTab] = useState<ReportTab>('summary')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Poll all known jobs
  useEffect(() => {
    const storedIds = localStorage.getItem('revisica_run_ids')
    const runIds: string[] = storedIds ? JSON.parse(storedIds) : []
    if (runIds.length === 0) return

    const fetchAllJobs = async (): Promise<void> => {
      const statuses: RunStatus[] = []
      for (const id of runIds) {
        try {
          const response = await fetch(`${apiBase}/api/status/${id}`)
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
  }, [apiBase])

  // Fetch detail for the selected job
  useEffect(() => {
    if (!runId) {
      setSelectedJob(null)
      setResults(null)
      return
    }

    setResults(null)
    setErrorMessage(null)
    setActiveTab('summary')

    const poll = setInterval(async () => {
      try {
        const response = await fetch(`${apiBase}/api/status/${runId}`)
        if (!response.ok) {
          setErrorMessage('Failed to fetch job status')
          return
        }

        const status: RunStatus = await response.json()
        setSelectedJob(status)

        if (status.state === 'completed') {
          clearInterval(poll)
          const resultsResponse = await fetch(
            `${apiBase}/api/results/${runId}`,
          )
          if (resultsResponse.ok) setResults(await resultsResponse.json())
        } else if (status.state === 'failed') {
          clearInterval(poll)
        }
      } catch {
        setErrorMessage('Lost connection to backend')
      }
    }, 1000)

    return () => clearInterval(poll)
  }, [runId, apiBase])

  // Auto-select the first running job if none is selected
  useEffect(() => {
    if (!runId && jobs.length > 0) {
      const runningJob = jobs.find((job) => job.state === 'running')
      if (runningJob) {
        navigate(`/jobs/${runningJob.run_id}`, { replace: true })
      }
    }
  }, [runId, jobs, navigate])

  const getReportContent = (): string => {
    if (!results) return ''
    switch (activeTab) {
      case 'writing':
        return results.writing_report ?? '*No writing report available*'
      case 'math':
        return results.math_report ?? '*No math report available*'
      default:
        return results.summary
    }
  }

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

        {runId && selectedJob && !results && (
          <JobProgressView runId={runId} status={selectedJob} />
        )}

        {runId && results && (
          <JobResultsView
            runId={runId}
            results={results}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            content={getReportContent()}
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
        <div className="font-mono text-xs font-medium text-ink truncate">
          {job.run_id.slice(0, 8)}
        </div>
        <div className="text-[10px] text-ink-faint mt-0.5">
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
  const tabs: ReportTab[] = ['summary', 'writing', 'math']

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

      {/* Report tabs */}
      <div className="flex gap-1 mb-6 p-1 rounded-lg bg-paper-200/60">
        {tabs.map((tab) => (
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
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Report content */}
      <div className="card px-6 py-6">
        <div className="prose-paper">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
