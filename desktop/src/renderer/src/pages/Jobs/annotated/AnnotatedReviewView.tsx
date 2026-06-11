import { useCallback, useMemo, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import AnnotatedDocument from './AnnotatedDocument'
import FindingsSidebar from './FindingsSidebar'
import { SEVERITY_STYLES, severityStyle } from './severity'
import type { Finding, FindingSeverity, FindingsPayload } from './types'
import { useFindingHighlights } from './useFindingHighlights'

// Side-by-side annotated reading view: the reviewed paper with severity
// highlights on the left, the finding cards on the right, scroll-synced
// in both directions.

const ALL_SEVERITIES = Object.keys(SEVERITY_STYLES) as FindingSeverity[]

interface AnnotatedReviewViewProps {
  payload: FindingsPayload
  apiBase: string
  apiToken: string
  parsedDocumentId?: string
}

export default function AnnotatedReviewView({
  payload,
  apiBase,
  apiToken,
  parsedDocumentId,
}: AnnotatedReviewViewProps): JSX.Element {
  const documentRef = useRef<HTMLDivElement>(null)
  const [activeFindingId, setActiveFindingId] = useState<string | null>(null)
  const [enabledSeverities, setEnabledSeverities] = useState<Set<FindingSeverity>>(
    () => new Set(ALL_SEVERITIES),
  )

  const visibleFindings = useMemo(
    () => payload.findings.filter((finding) => enabledSeverities.has(finding.severity)),
    [payload.findings, enabledSeverities],
  )

  const { scrollToFinding, findingIdsForBlock } = useFindingHighlights(
    documentRef,
    visibleFindings,
    activeFindingId,
  )

  const handleSidebarSelect = useCallback(
    (findingId: string): void => {
      setActiveFindingId(findingId)
      scrollToFinding(findingId)
    },
    [scrollToFinding],
  )

  const handleDocumentClick = useCallback(
    (event: React.MouseEvent<HTMLDivElement>): void => {
      const ids = findingIdsForBlock(event.target as HTMLElement)
      if (ids.length === 0) return
      // Repeated clicks on a block with several findings cycle through them.
      const currentIndex = activeFindingId ? ids.indexOf(activeFindingId) : -1
      setActiveFindingId(ids[(currentIndex + 1) % ids.length])
    },
    [findingIdsForBlock, activeFindingId],
  )

  const toggleSeverity = useCallback((severity: FindingSeverity): void => {
    setEnabledSeverities((previous) => {
      const next = new Set(previous)
      if (next.has(severity)) {
        next.delete(severity)
      } else {
        next.add(severity)
      }
      return next
    })
  }, [])

  return (
    <div className="flex h-full min-h-0">
      {/* Document pane */}
      <div className="flex-1 min-w-0 overflow-y-auto px-10 py-8 bg-paper-100/40">
        <AnnotatedDocument
          ref={documentRef}
          markdown={payload.document_markdown}
          apiBase={apiBase}
          apiToken={apiToken}
          parsedDocumentId={parsedDocumentId}
          onClick={handleDocumentClick}
        />
      </div>

      {/* Findings pane */}
      <aside className="w-96 shrink-0 overflow-y-auto border-l border-paper-300 bg-paper-200/30 px-4 pt-5">
        <SeverityFilterChips
          findings={payload.findings}
          enabledSeverities={enabledSeverities}
          onToggle={toggleSeverity}
        />
        <FindingsSidebar
          findings={visibleFindings}
          activeFindingId={activeFindingId}
          onSelect={handleSidebarSelect}
        />
      </aside>
    </div>
  )
}

function SeverityFilterChips({
  findings,
  enabledSeverities,
  onToggle,
}: {
  findings: Finding[]
  enabledSeverities: Set<FindingSeverity>
  onToggle: (severity: FindingSeverity) => void
}): JSX.Element {
  const counts = useMemo(() => {
    const result = new Map<FindingSeverity, number>()
    for (const finding of findings) {
      result.set(finding.severity, (result.get(finding.severity) ?? 0) + 1)
    }
    return result
  }, [findings])

  return (
    <div className="flex flex-wrap gap-1.5 pb-4">
      {ALL_SEVERITIES.filter((severity) => (counts.get(severity) ?? 0) > 0).map(
        (severity) => {
          const style = severityStyle(severity)
          const enabled = enabledSeverities.has(severity)
          return (
            <button
              key={severity}
              type="button"
              onClick={() => onToggle(severity)}
              title={enabled ? `Hide ${style.label} findings` : `Show ${style.label} findings`}
              className={cn(
                'text-[11px] font-semibold px-2.5 py-1 rounded-full border cursor-pointer',
                'transition-all duration-150',
                enabled
                  ? cn(style.badgeClass, 'border-transparent')
                  : 'bg-transparent text-ink-faint border-paper-300 line-through',
              )}
            >
              {style.label} · {counts.get(severity)}
            </button>
          )
        },
      )}
    </div>
  )
}
