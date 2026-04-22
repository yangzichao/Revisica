import { apiFetch } from '@/lib/api'
import type { ParseResultData } from '@/pages/Parse/ParseResult'

function parsedDocumentPath(id: string): string {
  return `/api/parsed-documents/${encodeURIComponent(id)}`
}

export async function fetchParsedDocument(
  apiBase: string,
  apiToken: string,
  id: string,
): Promise<ParseResultData> {
  const response = await apiFetch(apiBase, apiToken, parsedDocumentPath(id))
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail || `Failed to load (${response.status})`)
  }
  return response.json() as Promise<ParseResultData>
}

export async function deleteParsedDocument(
  apiBase: string,
  apiToken: string,
  id: string,
): Promise<void> {
  const response = await apiFetch(apiBase, apiToken, parsedDocumentPath(id), {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error(`Delete failed (${response.status})`)
  }
}
