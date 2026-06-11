import { forwardRef, memo, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Components } from 'react-markdown'
import { ImageOff } from 'lucide-react'
import PreviewAssetImage from '@/pages/Library/preview/PreviewAssetImage'
import {
  ExternalSafeLink,
  MermaidAwarePre,
  REHYPE_PLUGINS,
  REMARK_PLUGINS,
  StyledTable,
  SubstantiveDetails,
} from '@/pages/Library/preview/markdownComponents'
import rehypeSourceLines from './rehypeSourceLines'

// The annotated copy of the reviewed paper: the same renderer the Library
// preview uses, plus ``data-line`` stamps on every element so finding
// anchors can be mapped onto rendered blocks (see useFindingHighlights).

const ANNOTATED_REHYPE_PLUGINS = [...REHYPE_PLUGINS, rehypeSourceLines]

interface AnnotatedDocumentProps {
  markdown: string
  apiBase: string
  apiToken: string
  // Reviews started from the Library carry the parsed document id, which
  // is what asset image URLs are namespaced under. Reviews of raw files
  // have no asset store — images degrade to a labelled placeholder.
  parsedDocumentId?: string
  onClick?: (event: React.MouseEvent<HTMLDivElement>) => void
}

const AnnotatedDocument = forwardRef<HTMLDivElement, AnnotatedDocumentProps>(
  function AnnotatedDocument(
    { markdown, apiBase, apiToken, parsedDocumentId, onClick },
    ref,
  ): JSX.Element {
    const markdownComponents = useMemo<Components>(
      () => ({
        img: (props) =>
          parsedDocumentId ? (
            <PreviewAssetImage
              apiBase={apiBase}
              apiToken={apiToken}
              parsedDocumentId={parsedDocumentId}
              src={props.src}
              alt={props.alt}
            />
          ) : (
            <MissingAssetPlaceholder alt={props.alt} />
          ),
        table: StyledTable,
        a: ExternalSafeLink,
        pre: MermaidAwarePre,
        details: SubstantiveDetails,
      }),
      [apiBase, apiToken, parsedDocumentId],
    )

    return (
      <div ref={ref} onClick={onClick}>
        <article className="prose-paper prose-paper-preview max-w-[72ch]">
          <ReactMarkdown
            remarkPlugins={REMARK_PLUGINS}
            rehypePlugins={ANNOTATED_REHYPE_PLUGINS}
            components={markdownComponents}
          >
            {markdown}
          </ReactMarkdown>
        </article>
      </div>
    )
  },
)

export default memo(AnnotatedDocument)

function MissingAssetPlaceholder({ alt }: { alt?: string }): JSX.Element {
  return (
    <span className="my-4 flex items-center gap-2 rounded-md border border-paper-300 bg-paper-100 px-3 py-2 text-xs text-ink-faint">
      <ImageOff size={14} strokeWidth={1.5} />
      {alt || 'figure'}
    </span>
  )
}
