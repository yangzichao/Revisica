import { Play, Loader2, AlertTriangle } from 'lucide-react'
import type { ParserAvailability, BenchmarkConfigDraft } from './types'

interface ConfigPanelProps {
  availableParsers: ParserAvailability[]
  draft: BenchmarkConfigDraft
  onDraftChange: (draft: BenchmarkConfigDraft) => void
  onStart: () => void
  isStarting: boolean
  isRunning: boolean
}

export default function ConfigPanel({
  availableParsers,
  draft,
  onDraftChange,
  onStart,
  isStarting,
  isRunning,
}: ConfigPanelProps): JSX.Element {
  const toggleParser = (parserKey: string): void => {
    const isSelected = draft.parserKeys.includes(parserKey)
    const nextKeys = isSelected
      ? draft.parserKeys.filter((key) => key !== parserKey)
      : [...draft.parserKeys, parserKey]
    onDraftChange({ ...draft, parserKeys: nextKeys })
  }

  const selectedInstalledCount = draft.parserKeys.filter((key) =>
    availableParsers.find((p) => p.key === key)?.available,
  ).length

  const canStart =
    !isStarting && !isRunning && selectedInstalledCount > 0 && draft.limit > 0

  return (
    <section className="rounded-lg border border-paper-300 bg-paper-50 px-6 py-5 space-y-5">
      <header>
        <h2 className="font-serif text-lg font-semibold text-ink tracking-tight">
          Run configuration
        </h2>
        <p className="text-xs text-ink-tertiary mt-1">
          Each selected parser runs on every paper. MinerU backends run sequentially
          and can take several minutes per paper on Apple Silicon.
        </p>
      </header>

      <div>
        <div className="mb-2 flex items-baseline justify-between">
          <label className="text-sm font-medium text-ink-secondary">Parsers</label>
          <span className="text-[11px] text-ink-faint">
            {selectedInstalledCount} of {draft.parserKeys.length} selected installed
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {availableParsers.map((parser) => (
            <ParserChip
              key={parser.key}
              parser={parser}
              isSelected={draft.parserKeys.includes(parser.key)}
              onToggle={() => toggleParser(parser.key)}
              isDisabled={isRunning || isStarting}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-5">
        <div>
          <label
            htmlFor="benchmark-limit"
            className="block mb-2 text-sm font-medium text-ink-secondary"
          >
            Papers
          </label>
          <input
            id="benchmark-limit"
            type="number"
            min={1}
            max={24}
            value={draft.limit}
            onChange={(event) =>
              onDraftChange({
                ...draft,
                limit: Math.max(1, Math.min(24, Number(event.target.value) || 1)),
              })
            }
            disabled={isRunning || isStarting}
            className="w-full rounded-md border border-paper-300 bg-paper-50 px-3 py-2 text-sm text-ink disabled:opacity-60"
          />
          <p className="mt-1 text-[11px] text-ink-faint">
            Number from the 24-paper arXiv corpus (default 3 is a ~15 min full run)
          </p>
        </div>

        <div className="space-y-2 text-sm">
          <label className="flex items-start gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={draft.skipGroundTruth}
              onChange={(event) =>
                onDraftChange({ ...draft, skipGroundTruth: event.target.checked })
              }
              disabled={isRunning || isStarting}
              className="mt-0.5"
            />
            <span className="text-ink-secondary">
              Skip ground truth
              <span className="block text-[11px] text-ink-faint">
                No arXiv API lookup; only structural metrics
              </span>
            </span>
          </label>
          <label className="flex items-start gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={draft.noPdfDownload}
              onChange={(event) =>
                onDraftChange({ ...draft, noPdfDownload: event.target.checked })
              }
              disabled={isRunning || isStarting}
              className="mt-0.5"
            />
            <span className="text-ink-secondary">
              Offline mode
              <span className="block text-[11px] text-ink-faint">
                Don't download missing PDFs from arXiv
              </span>
            </span>
          </label>
        </div>
      </div>

      <div className="pt-1">
        <button
          type="button"
          onClick={onStart}
          disabled={!canStart}
          className="btn-primary inline-flex items-center gap-2 px-4 py-2 text-sm disabled:opacity-50"
        >
          {isStarting || isRunning ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Play size={14} />
          )}
          {isRunning ? 'Running…' : 'Run benchmark'}
        </button>
        {selectedInstalledCount === 0 && draft.parserKeys.length > 0 && (
          <span className="ml-3 inline-flex items-center gap-1 text-xs text-danger">
            <AlertTriangle size={12} />
            None of the selected parsers are installed
          </span>
        )}
      </div>
    </section>
  )
}

function ParserChip({
  parser,
  isSelected,
  onToggle,
  isDisabled,
}: {
  parser: ParserAvailability
  isSelected: boolean
  onToggle: () => void
  isDisabled: boolean
}): JSX.Element {
  const baseClasses =
    'rounded-full border px-3 py-1 text-xs font-medium transition-colors'
  let stateClasses = ''
  if (isSelected && parser.available) {
    stateClasses = 'border-accent bg-accent/10 text-accent'
  } else if (isSelected && !parser.available) {
    stateClasses = 'border-danger bg-danger/10 text-danger'
  } else if (parser.available) {
    stateClasses =
      'border-paper-300 bg-paper-50 text-ink-secondary hover:border-paper-400'
  } else {
    stateClasses = 'border-paper-300 bg-paper-100 text-ink-faint'
  }
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={isDisabled}
      className={`${baseClasses} ${stateClasses} disabled:cursor-not-allowed disabled:opacity-60`}
      title={
        parser.available
          ? `${parser.key} (${parser.requires_format})`
          : parser.skip_reason ?? 'unavailable'
      }
    >
      {parser.key}
      {!parser.available && (
        <span className="ml-1.5 text-[10px] uppercase tracking-wide">missing</span>
      )}
    </button>
  )
}
