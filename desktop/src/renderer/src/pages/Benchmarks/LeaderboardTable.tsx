import { useMemo } from 'react'
import type { BenchmarkCell, BenchmarkRunState } from './types'

interface LeaderboardTableProps {
  state: BenchmarkRunState
}

interface ParserAggregate {
  parserKey: string
  totalCells: number
  successCells: number
  averageDurationSeconds: number | null
  titleMatchRate: number | null       // null if no ground truth available
  averageAuthorsF1: number | null
  averageAbstractOverlap: number | null
  hasMathRate: number | null
  cleanTitlesRate: number | null
  averageLeftoverCount: number | null
  averageMarkdownLength: number | null
}

export default function LeaderboardTable({
  state,
}: LeaderboardTableProps): JSX.Element {
  const aggregates = useMemo(
    () => aggregateByParser(state),
    [state],
  )

  if (aggregates.length === 0) {
    return (
      <section className="rounded-lg border border-paper-300 bg-paper-50 px-6 py-8 text-center">
        <p className="text-sm text-ink-tertiary">
          Leaderboard will populate as cells complete.
        </p>
      </section>
    )
  }

  return (
    <section className="rounded-lg border border-paper-300 bg-paper-50 overflow-hidden">
      <header className="px-6 py-4 border-b border-paper-200">
        <h2 className="font-serif text-lg font-semibold text-ink tracking-tight">
          Leaderboard
        </h2>
        <p className="text-xs text-ink-tertiary mt-1">
          Aggregated across {state.paper_ids.length || '—'}{' '}
          {state.paper_ids.length === 1 ? 'paper' : 'papers'}. Updates live.
        </p>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-paper-100 text-ink-tertiary text-xs uppercase tracking-wide">
            <tr>
              <th className="text-left px-6 py-2.5 font-medium">Parser</th>
              <th className="text-right px-3 py-2.5 font-medium">Success</th>
              <th className="text-right px-3 py-2.5 font-medium">Avg time</th>
              <th className="text-right px-3 py-2.5 font-medium">Title</th>
              <th className="text-right px-3 py-2.5 font-medium">Authors F1</th>
              <th className="text-right px-3 py-2.5 font-medium">Abstract</th>
              <th className="text-right px-3 py-2.5 font-medium">Math</th>
              <th className="text-right px-3 py-2.5 font-medium">Clean titles</th>
              <th className="text-right px-3 py-2.5 font-medium">Leftover</th>
              <th className="text-right px-6 py-2.5 font-medium">Avg md len</th>
            </tr>
          </thead>
          <tbody>
            {aggregates.map((row) => (
              <tr
                key={row.parserKey}
                className="border-t border-paper-200 hover:bg-paper-100/50"
              >
                <td className="px-6 py-2.5 font-mono text-ink">
                  {row.parserKey}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {row.successCells}/{row.totalCells}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatSeconds(row.averageDurationSeconds)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatPercent(row.titleMatchRate)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatDecimal(row.averageAuthorsF1)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatDecimal(row.averageAbstractOverlap)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatPercent(row.hasMathRate)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatPercent(row.cleanTitlesRate)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {formatNumberOr(row.averageLeftoverCount, 1)}
                </td>
                <td className="px-6 py-2.5 text-right tabular-nums text-ink-tertiary">
                  {formatNumberOr(row.averageMarkdownLength, 0)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function aggregateByParser(state: BenchmarkRunState): ParserAggregate[] {
  const orderedKeys =
    state.adapter_keys.length > 0
      ? state.adapter_keys
      : Array.from(new Set(state.cells.map((cell) => cell.parser_key)))

  return orderedKeys.map((parserKey) => {
    const cellsForParser = state.cells.filter(
      (cell) => cell.parser_key === parserKey,
    )
    const successCells = cellsForParser.filter((cell) => cell.success)
    const totalCells = cellsForParser.length
    const successCount = successCells.length

    const averageDurationSeconds = averageOrNull(
      successCells.map((cell) => cell.duration_seconds),
    )
    const averageAuthorsF1 = averageOrNull(
      metricValues(successCells, (cell) => cell.metrics?.authors_f1 ?? null),
    )
    const averageAbstractOverlap = averageOrNull(
      metricValues(successCells, (cell) => cell.metrics?.abstract_overlap_ratio ?? null),
    )
    const titleMatchRate = rateOverScoredCells(
      successCells,
      (cell) => cell.metrics?.title_match_ok ?? null,
    )
    const hasMathRate = rateOver(
      successCells,
      (cell) => cell.metrics?.has_math ?? false,
    )
    const cleanTitlesRate = rateOver(
      successCells,
      (cell) => cell.metrics?.clean_heading_titles ?? false,
    )
    const averageLeftoverCount = averageOrNull(
      successCells.map(
        (cell) => cell.metrics?.leftover_latex_commands.length ?? 0,
      ),
    )
    const averageMarkdownLength = averageOrNull(
      successCells.map((cell) => cell.metrics?.markdown_length ?? 0),
    )

    return {
      parserKey,
      totalCells,
      successCells: successCount,
      averageDurationSeconds,
      titleMatchRate,
      averageAuthorsF1,
      averageAbstractOverlap,
      hasMathRate,
      cleanTitlesRate,
      averageLeftoverCount,
      averageMarkdownLength,
    }
  })
}

function metricValues(
  cells: BenchmarkCell[],
  extractor: (cell: BenchmarkCell) => number | null,
): number[] {
  return cells
    .map(extractor)
    .filter((value): value is number => value !== null && value !== undefined)
}

function averageOrNull(values: number[]): number | null {
  if (values.length === 0) return null
  const sum = values.reduce((total, value) => total + value, 0)
  return sum / values.length
}

function rateOver(
  cells: BenchmarkCell[],
  predicate: (cell: BenchmarkCell) => boolean,
): number | null {
  if (cells.length === 0) return null
  const matched = cells.filter(predicate).length
  return matched / cells.length
}

function rateOverScoredCells(
  cells: BenchmarkCell[],
  predicate: (cell: BenchmarkCell) => boolean | null,
): number | null {
  const scored = cells.filter((cell) => predicate(cell) !== null)
  if (scored.length === 0) return null
  const matched = scored.filter((cell) => predicate(cell) === true).length
  return matched / scored.length
}

function formatSeconds(value: number | null): string {
  if (value === null) return '—'
  if (value < 60) return `${value.toFixed(1)}s`
  return `${(value / 60).toFixed(1)}m`
}

function formatPercent(value: number | null): string {
  if (value === null) return '—'
  return `${Math.round(value * 100)}%`
}

function formatDecimal(value: number | null): string {
  if (value === null) return '—'
  return value.toFixed(2)
}

function formatNumberOr(value: number | null, fractionDigits: number): string {
  if (value === null) return '—'
  return value.toFixed(fractionDigits)
}
