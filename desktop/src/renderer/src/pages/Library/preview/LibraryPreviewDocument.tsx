import { memo } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Components } from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeRaw from 'rehype-raw'
import rehypeSlug from 'rehype-slug'
import { ImageOff } from 'lucide-react'

const REMARK_PLUGINS = [remarkMath]
const REHYPE_PLUGINS = [rehypeRaw, rehypeSlug, rehypeKatex]

const MARKDOWN_COMPONENTS: Components = {
  img: PlaceholderImage,
  table: StyledTable,
  a: ExternalSafeLink,
}

interface LibraryPreviewDocumentProps {
  markdown: string
}

function LibraryPreviewDocument({
  markdown,
}: LibraryPreviewDocumentProps): JSX.Element {
  return (
    <article className="prose-paper prose-paper-preview max-w-[72ch]">
      <ReactMarkdown
        remarkPlugins={REMARK_PLUGINS}
        rehypePlugins={REHYPE_PLUGINS}
        components={MARKDOWN_COMPONENTS}
      >
        {markdown}
      </ReactMarkdown>
    </article>
  )
}

export default memo(LibraryPreviewDocument)

function PlaceholderImage({
  alt,
  src,
}: {
  alt?: string
  src?: string
}): JSX.Element {
  const label = alt?.trim() || basenameFromSrc(src) || 'image'
  // inline-block (not inline-flex) so vertical margins actually apply —
  // CSS ignores margin-top/bottom on inline-level boxes.
  return (
    <span className="my-3 inline-block align-middle px-3 py-2 rounded-md border border-dashed border-paper-400 bg-paper-100 text-ink-tertiary text-xs font-sans not-italic">
      <ImageOff size={12} strokeWidth={1.7} className="inline-block mr-1.5 -mt-0.5" />
      <span className="inline truncate max-w-[40ch] align-middle">{label}</span>
    </span>
  )
}

function StyledTable({
  children,
}: {
  children?: React.ReactNode
}): JSX.Element {
  return (
    <div className="my-4 overflow-x-auto rounded-lg border border-paper-300 bg-paper-50">
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  )
}

function ExternalSafeLink({
  href,
  children,
}: {
  href?: string
  children?: React.ReactNode
}): JSX.Element {
  const isInternalAnchor = href?.startsWith('#')
  return (
    <a
      href={href}
      target={isInternalAnchor ? undefined : '_blank'}
      rel={isInternalAnchor ? undefined : 'noopener noreferrer'}
    >
      {children}
    </a>
  )
}

function basenameFromSrc(src?: string): string | null {
  if (!src) return null
  return src.split('/').pop() || null
}
