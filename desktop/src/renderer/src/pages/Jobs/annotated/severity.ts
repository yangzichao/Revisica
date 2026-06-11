import type { FindingSeverity } from './types'

// One visual identity per severity, drawn from the vintage-paper palette:
// danger red for critical, burnt-orange accent for major, muted gold for
// minor, ink grey for informational notes.
export interface SeverityStyle {
  label: string
  badgeClass: string
  blockMarkClass: string
  highlightName: string
}

export const SEVERITY_STYLES: Record<FindingSeverity, SeverityStyle> = {
  critical: {
    label: 'Critical',
    badgeClass: 'bg-danger/10 text-danger',
    blockMarkClass: 'annotated-block-critical',
    highlightName: 'revisica-finding-critical',
  },
  major: {
    label: 'Major',
    badgeClass: 'bg-accent/10 text-accent',
    blockMarkClass: 'annotated-block-major',
    highlightName: 'revisica-finding-major',
  },
  minor: {
    label: 'Minor',
    badgeClass: 'bg-[#B8923A]/15 text-[#8A6D2B]',
    blockMarkClass: 'annotated-block-minor',
    highlightName: 'revisica-finding-minor',
  },
  info: {
    label: 'Info',
    badgeClass: 'bg-paper-300/60 text-ink-tertiary',
    blockMarkClass: 'annotated-block-info',
    highlightName: 'revisica-finding-info',
  },
}

export function severityStyle(severity: string): SeverityStyle {
  return SEVERITY_STYLES[severity as FindingSeverity] ?? SEVERITY_STYLES.major
}
