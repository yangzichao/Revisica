import { useEffect, useState } from 'react'
import { CheckCircle2, AlertTriangle, Loader2, Copy, Check } from 'lucide-react'
import type { BenchmarkRunState } from './types'

interface ProgressPanelProps {
  state: BenchmarkRunState
  onCopyOutputDir: (path: string) => void
  outputDirCopied: boolean
}

export default function ProgressPanel({
  state,
  onCopyOutputDir,
  outputDirCopied,
}: ProgressPanelProps): JSX.Element {
  const isRunning = state.status === 'running'
  const elapsed = useElapsedSeconds(
    state.started_at,
    state.finished_at,
    isRunning,
  )
  const cellElapsed = useElapsedSeconds(
    state.current_cell_started_at,
    null,
    isRunning && state.current_cell_started_at !== null,
  )

  const percent =
    state.total_cells > 0
      ? Math.round((state.completed_cells / state.total_cells) * 100)
      : 0

  const headerIcon = headerIconFor(state.status)
  const headerLabel = headerLabelFor(state.status)
  const borderColor = borderColorFor(state.status)

  return (
    <section className={`rounded-lg border ${borderColor} bg-paper-50 px-6 py-5`}>
      <header className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {headerIcon}
          <h2 className="font-serif text-lg font-semibold text-ink tracking-tight">
            {headerLabel}
          </h2>
        </div>
        <div className="text-xs font-mono text-ink-tertiary">
          {formatSeconds(elapsed)}
        </div>
      </header>

      <div className="mt-4">
        <div className="flex items-baseline justify-between text-xs text-ink-tertiary">
          <span>
            {state.completed_cells} of {state.total_cells || '—'} cells
          </span>
          <span className="font-mono">{percent}%</span>
        </div>
        <div className="mt-1.5 h-2 rounded-full bg-paper-200 overflow-hidden">
          <div
            className="h-full bg-accent transition-all duration-500 ease-out"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      {isRunning && state.current_paper_id && (
        <div className="mt-4 flex items-center gap-2 text-sm text-ink-secondary">
          <Loader2 size={14} className="animate-spin text-accent shrink-0" />
          <div className="min-w-0">
            <div className="truncate">
              Parsing{' '}
              <span className="font-mono text-ink">{state.current_paper_id}</span>{' '}
              with{' '}
              <span className="font-mono text-ink">
                {state.current_parser_key}
              </span>
            </div>
            {cellElapsed !== null && (
              <div className="text-[11px] text-ink-faint mt-0.5">
                Cell elapsed: {formatSeconds(cellElapsed)}
              </div>
            )}
          </div>
        </div>
      )}

      {state.status === 'failed' && state.error && (
        <div className="mt-4 rounded-md bg-danger/5 border border-danger/30 p-3 text-sm text-danger">
          <div className="flex items-start gap-2">
            <AlertTriangle size={14} className="mt-0.5 shrink-0" />
            <div className="break-words">{state.error}</div>
          </div>
        </div>
      )}

      <div className="mt-4 flex items-center justify-between text-[11px] text-ink-faint">
        <div className="flex gap-3">
          <span>Run ID: {state.run_id}</span>
          <span>·</span>
          <span>Started {formatClock(state.started_at)}</span>
          {state.finished_at && (
            <>
              <span>·</span>
              <span>Finished {formatClock(state.finished_at)}</span>
            </>
          )}
        </div>
        <button
          type="button"
          onClick={() => onCopyOutputDir(state.output_dir)}
          className="btn-ghost px-2 py-1 inline-flex items-center gap-1 text-[11px]"
          title={state.output_dir}
        >
          {outputDirCopied ? <Check size={11} /> : <Copy size={11} />}
          {outputDirCopied ? 'Path copied' : 'Copy path'}
        </button>
      </div>
    </section>
  )
}

/**
 * Return the elapsed seconds between `startedAt` and either `endedAt`
 * (if given) or the live clock. When `active` is true, re-renders every
 * second so the displayed value keeps climbing; when false, the value
 * freezes at its last update.
 */
function useElapsedSeconds(
  startedAt: string | null,
  endedAt: string | null,
  active: boolean,
): number | null {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!active) return
    const interval = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(interval)
  }, [active])
  if (!startedAt) return null
  const started = new Date(startedAt).getTime()
  if (Number.isNaN(started)) return null
  const reference = endedAt ? new Date(endedAt).getTime() : now
  if (Number.isNaN(reference)) return null
  return Math.max(0, Math.floor((reference - started) / 1000))
}

function headerIconFor(status: BenchmarkRunState['status']): JSX.Element {
  if (status === 'running') {
    return <Loader2 size={16} className="animate-spin text-accent" />
  }
  if (status === 'succeeded') {
    return <CheckCircle2 size={16} className="text-success" />
  }
  return <AlertTriangle size={16} className="text-danger" />
}

function headerLabelFor(status: BenchmarkRunState['status']): string {
  if (status === 'running') return 'In progress'
  if (status === 'succeeded') return 'Run complete'
  return 'Run failed'
}

function borderColorFor(status: BenchmarkRunState['status']): string {
  if (status === 'running') return 'border-accent/40'
  if (status === 'succeeded') return 'border-success/40'
  return 'border-danger/40'
}

function formatSeconds(value: number | null): string {
  if (value === null) return '—'
  if (value < 60) return `${value}s`
  const minutes = Math.floor(value / 60)
  const seconds = value % 60
  return `${minutes}m ${seconds.toString().padStart(2, '0')}s`
}

function formatClock(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
