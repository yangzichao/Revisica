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
  const fileName = sourcePath
    ? sourcePath.split('/').pop() || sourcePath
    : fallback
  const heading = title.trim() || fileName
  return { fileName, heading }
}

export function resumeReviewPath(parsedId: string): string {
  return `/?parsed=${encodeURIComponent(parsedId)}`
}
