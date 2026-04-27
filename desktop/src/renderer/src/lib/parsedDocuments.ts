import { basename } from './formatters'

export interface LibrarySummary {
  id: string
  parsed_at: string
  source_path: string
  parser_used: string
  elapsed_ms: number
  title: string
  authors: string[]
  section_count: number
}

export function deriveDocumentLabels(
  sourcePath: string,
  title: string,
  fallback = 'document',
): { fileName: string; heading: string } {
  const fileName = basename(sourcePath || '') || fallback
  const heading = (title || '').trim() || fileName
  return { fileName, heading }
}

export function resumeReviewPath(parsedId: string): string {
  return `/?parsed=${encodeURIComponent(parsedId)}`
}

// Suggested filename for the Save dialog when the user exports a parsed
// document's normalized markdown. Strips the extension off the source
// path, prefers the parsed title when present, and sanitizes characters
// that the filesystem (or Save dialog) won't accept.
export function deriveExportFilename(
  sourcePath: string,
  title: string,
  fallbackId: string,
): string {
  const fromPath =
    sourcePath?.split('/').pop()?.replace(/\.[^.]+$/, '') ?? ''
  const fromTitle = title?.trim() ?? ''
  const base = fromTitle || fromPath || fallbackId
  return base.replace(/[\\/:*?"<>|]/g, '-').slice(0, 120) || fallbackId
}
