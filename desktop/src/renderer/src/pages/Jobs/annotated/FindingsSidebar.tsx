import { useEffect, useRef } from 'react'
import { Inbox, MapPinOff } from 'lucide-react'
import { cn } from '@/lib/utils'
import { severityStyle } from './severity'
import type { Finding } from './types'

interface FindingsSidebarProps {
  findings: Finding[]
  activeFindingId: string | null
  onSelect: (findingId: string) => void
}

export default function FindingsSidebar({
  findings,
  activeFindingId,
  onSelect,
}: FindingsSidebarProps): JSX.Element {
  if (findings.length === 0) {
    return (
      <div className="flex flex-col items-center pt-16 px-4 text-center">
        <Inbox size={24} className="text-ink-faint mb-2" strokeWidth={1.2} />
        <p className="text-xs text-ink-tertiary">No findings match the filter</p>
      </div>
    )
  }

  return (
    <div className="space-y-2 pb-6">
      {findings.map((finding) => (
        <FindingCard
          key={finding.id}
          finding={finding}
          isActive={finding.id === activeFindingId}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}

function FindingCard({
  finding,
  isActive,
  onSelect,
}: {
  finding: Finding
  isActive: boolean
  onSelect: (findingId: string) => void
}): JSX.Element {
  const style = severityStyle(finding.severity)
  const cardRef = useRef<HTMLButtonElement>(null)

  // Keep the active card visible when activation comes from a click
  // inside the document.
  useEffect(() => {
    if (isActive) {
      cardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [isActive])

  const anchored = finding.anchor.resolution !== 'unresolved'

  return (
    <button
      ref={cardRef}
      type="button"
      onClick={() => onSelect(finding.id)}
      className={cn(
        'w-full text-left rounded-lg border bg-paper-50 px-4 py-3 cursor-pointer',
        'transition-all duration-150',
        isActive
          ? 'border-accent/60 shadow-subtle ring-1 ring-accent/30'
          : 'border-paper-300 hover:border-paper-400 hover:shadow-subtle',
      )}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <span
          className={cn(
            'text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full',
            style.badgeClass,
          )}
        >
          {style.label}
        </span>
        <span className="text-[10px] uppercase tracking-wider text-ink-faint">
          {finding.lane === 'math' ? `math · ${finding.role}` : finding.role}
        </span>
        {!anchored && (
          <MapPinOff
            size={11}
            strokeWidth={1.6}
            className="text-ink-faint ml-auto shrink-0"
            aria-label="Not anchored in the document"
          />
        )}
      </div>

      <div className="text-sm font-medium text-ink leading-snug">{finding.title}</div>

      {finding.anchor.quote && (
        <div className="mt-1.5 text-xs italic text-ink-tertiary line-clamp-2 border-l-2 border-paper-400 pl-2">
          {finding.anchor.quote}
        </div>
      )}

      {finding.explanation && (
        <p className="mt-1.5 text-xs text-ink-secondary leading-relaxed line-clamp-4">
          {finding.explanation}
        </p>
      )}

      {finding.fix && (
        <p className="mt-1.5 text-xs leading-relaxed text-success">
          <span className="font-semibold">Fix: </span>
          {finding.fix}
        </p>
      )}

      {finding.evidence && (
        <p className="mt-1.5 text-[11px] font-mono leading-relaxed text-ink-tertiary bg-paper-100 rounded px-2 py-1.5 break-words">
          {finding.evidence}
        </p>
      )}

      <div className="mt-2 flex items-center gap-2 text-[10px] text-ink-faint">
        <span className="font-mono">{finding.id}</span>
        {finding.anchor.section_title && <span>§ {finding.anchor.section_title}</span>}
        {finding.anchor.line_number !== null && <span>L{finding.anchor.line_number}</span>}
      </div>
    </button>
  )
}
