import { apiFetch } from '@/lib/api'
import type { FindingsPayload } from './types'

// Returns null when the run has no findings artifact (older runs, parse
// jobs) — the caller hides the Annotated tab in that case.
export async function fetchRunFindings(
  apiBase: string,
  apiToken: string,
  runId: string,
): Promise<FindingsPayload | null> {
  const response = await apiFetch(apiBase, apiToken, `/api/results/${runId}/findings`)
  if (!response.ok) return null
  const payload: FindingsPayload = await response.json()
  if (!Array.isArray(payload.findings)) return null
  return payload
}
