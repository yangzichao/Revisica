import { useMemo } from 'react'
import { Chip } from '@/components/Chip'
import { formatElapsed } from '@/lib/formatters'

export interface ParseResultSection {
  id: string
  title: string
  level: number
  content: string
}

export interface ParseResultData {
  id: string
  parsed_at: string
  elapsed_ms: number
  parser_used: string
  source_path: string
  markdown: string
  title: string
  authors: string[]
  abstract: string
  section_count: number
  sections: ParseResultSection[]
}

interface ParseResultProps {
  result: ParseResultData
}

const MARKDOWN_PREVIEW_LIMIT = 2000

export default function ParseResult({ result }: ParseResultProps): JSX.Element {
  const elapsedLabel = formatElapsed(result.elapsed_ms)
  const authors = result.authors || []
  const sections = result.sections || []

  const previewMarkdown = useMemo(
    () => result.markdown.slice(0, MARKDOWN_PREVIEW_LIMIT),
    [result.markdown],
  )
  const markdownTruncated = result.markdown.length > MARKDOWN_PREVIEW_LIMIT

  return (
    <div className="mt-6 space-y-4">
      <SummaryChips
        parserUsed={result.parser_used}
        elapsedLabel={elapsedLabel}
        sectionCount={result.section_count}
        authorCount={authors.length}
      />

      <MetadataCard
        title={result.title}
        authors={authors}
        abstract={result.abstract}
      />

      <SectionListCard sections={sections} />

      <details className="card group px-4 py-3 cursor-pointer">
        <summary className="text-xs font-semibold text-ink-secondary tracking-wider uppercase select-none list-none flex items-center justify-between">
          <span>Raw markdown preview</span>
          <span className="text-ink-tertiary font-normal normal-case tracking-normal">
            first {Math.min(MARKDOWN_PREVIEW_LIMIT, result.markdown.length).toLocaleString()} chars
          </span>
        </summary>
        <pre className="mt-3 font-mono text-[11px] leading-relaxed text-ink-secondary bg-paper-100 p-3 rounded-md overflow-auto max-h-96 whitespace-pre-wrap break-words">
          {previewMarkdown}
          {markdownTruncated && (
            <span className="text-ink-tertiary italic">
              {'\n\n'}…truncated ({(result.markdown.length - MARKDOWN_PREVIEW_LIMIT).toLocaleString()} more chars)
            </span>
          )}
        </pre>
      </details>
    </div>
  )
}

function SummaryChips({
  parserUsed,
  elapsedLabel,
  sectionCount,
  authorCount,
}: {
  parserUsed: string
  elapsedLabel: string
  sectionCount: number
  authorCount: number
}): JSX.Element {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <Chip tone="accent">parsed via {parserUsed}</Chip>
      <Chip>{elapsedLabel}</Chip>
      <Chip>
        {sectionCount} section{sectionCount === 1 ? '' : 's'}
      </Chip>
      <Chip>
        {authorCount} author{authorCount === 1 ? '' : 's'}
      </Chip>
    </div>
  )
}

function MetadataCard({
  title,
  authors,
  abstract,
}: {
  title: string
  authors: string[]
  abstract: string
}): JSX.Element {
  return (
    <div className="card px-5 py-4 space-y-3">
      <div>
        {title ? (
          <h2 className="font-serif text-lg font-semibold text-ink leading-snug">
            {title}
          </h2>
        ) : (
          <h2 className="font-serif text-lg italic text-ink-tertiary">
            no title detected
          </h2>
        )}
      </div>

      <div>
        <div className="text-[11px] font-semibold text-ink-tertiary uppercase tracking-wider mb-1">
          Authors
        </div>
        {authors.length > 0 ? (
          <div className="text-sm text-ink-secondary">
            {authors.join(', ')}
          </div>
        ) : (
          <div className="text-sm italic text-ink-tertiary">
            no authors detected
          </div>
        )}
      </div>

      <div>
        <div className="text-[11px] font-semibold text-ink-tertiary uppercase tracking-wider mb-1">
          Abstract
        </div>
        {abstract ? (
          <AbstractBlock text={abstract} />
        ) : (
          <div className="text-sm italic text-ink-tertiary">
            no abstract detected
          </div>
        )}
      </div>
    </div>
  )
}

function AbstractBlock({ text }: { text: string }): JSX.Element {
  const TRUNCATE_AT = 400
  const truncated = text.length > TRUNCATE_AT
  if (!truncated) {
    return (
      <p className="font-serif text-sm text-ink-secondary leading-relaxed">
        {text}
      </p>
    )
  }
  return (
    <details className="group">
      <summary className="font-serif text-sm text-ink-secondary leading-relaxed cursor-pointer list-none">
        <span>{text.slice(0, TRUNCATE_AT)}…</span>
        <span className="ml-1 text-[11px] text-accent font-sans font-medium not-italic group-open:hidden">
          show more
        </span>
      </summary>
      <p className="font-serif text-sm text-ink-secondary leading-relaxed mt-1">
        {text}
      </p>
    </details>
  )
}

function SectionListCard({
  sections,
}: {
  sections: ParseResultSection[]
}): JSX.Element {
  return (
    <div className="card px-5 py-4">
      <div className="text-[11px] font-semibold text-ink-tertiary uppercase tracking-wider mb-3">
        Sections
      </div>
      {sections.length === 0 ? (
        <div className="text-sm italic text-ink-tertiary">
          no sections detected
        </div>
      ) : (
        <ul className="space-y-1.5">
          {sections.map((section) => (
            <SectionRow key={section.id} section={section} />
          ))}
        </ul>
      )}
    </div>
  )
}

function SectionRow({ section }: { section: ParseResultSection }): JSX.Element {
  const indent = Math.max(0, (section.level - 1) * 14)
  const charCount = section.content.length
  return (
    <li
      className="flex items-baseline gap-3 text-sm"
      style={{ paddingLeft: indent }}
    >
      <span className="font-mono text-[10px] text-ink-faint shrink-0 w-8 tabular-nums">
        #{section.level}
      </span>
      <span className="text-ink truncate flex-1 min-w-0">{section.title}</span>
      <span className="font-mono text-[11px] text-ink-tertiary tabular-nums shrink-0">
        {charCount.toLocaleString()} chars
      </span>
    </li>
  )
}

