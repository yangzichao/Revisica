import { FileText } from 'lucide-react'
import { Chip } from '@/components/Chip'
import { basename, formatElapsed, formatRelativeTime } from '@/lib/formatters'
import type { ParseResultData } from '@/pages/Parse/ParseResult'

interface LibraryPreviewHeaderProps {
  data: ParseResultData
}

export default function LibraryPreviewHeader({
  data,
}: LibraryPreviewHeaderProps): JSX.Element {
  const fileName = basename(data.source_path || '') || 'document'
  const title = (data.title || '').trim() || fileName
  const authors = data.authors || []

  return (
    <header className="space-y-3">
      <h1 className="font-serif text-[28px] leading-tight font-semibold text-ink">
        {title}
      </h1>
      {authors.length > 0 && (
        <div className="font-serif text-sm text-ink-secondary">
          {authors.join(', ')}
        </div>
      )}
      <div className="flex items-center flex-wrap gap-1.5 pt-1">
        <Chip tone="accent">parsed via {data.parser_used}</Chip>
        <Chip>
          {data.section_count} section{data.section_count === 1 ? '' : 's'}
        </Chip>
        <Chip>{formatElapsed(data.elapsed_ms)}</Chip>
        <Chip>{formatRelativeTime(data.parsed_at)}</Chip>
        <Chip tone="muted">
          <FileText size={10} strokeWidth={1.7} />
          {fileName}
        </Chip>
      </div>
    </header>
  )
}
