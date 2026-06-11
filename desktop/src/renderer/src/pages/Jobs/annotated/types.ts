// Mirrors the payload of GET /api/results/{run_id}/findings — the anchored
// findings written by the Python side (src/revisica/findings/).

export type FindingSeverity = 'critical' | 'major' | 'minor' | 'info'

export type AnchorResolution = 'exact' | 'line' | 'unresolved'

export interface FindingAnchor {
  quote: string
  // 1-based line in document_markdown; offsets are char indices into it.
  line_number: number | null
  start_offset: number | null
  end_offset: number | null
  section_id: string | null
  section_title: string | null
  resolution: AnchorResolution
}

export interface Finding {
  id: string
  lane: 'writing' | 'math'
  role: string
  provider: string | null
  model: string | null
  category: string
  severity: FindingSeverity
  title: string
  explanation: string
  fix: string
  evidence: string
  status: string | null
  anchor: FindingAnchor
}

export interface FindingsPayload {
  run_id: string
  version: number
  count: number
  findings: Finding[]
  document_markdown: string
}
