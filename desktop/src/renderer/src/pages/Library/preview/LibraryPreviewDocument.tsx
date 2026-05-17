import { Children, isValidElement, memo, useMemo } from 'react'
import type { ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import type { Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeRaw from 'rehype-raw'
import rehypeSlug from 'rehype-slug'
import PreviewAssetImage from './PreviewAssetImage'
import PreviewMermaidDiagram from './PreviewMermaidDiagram'

// remark-gfm enables GFM tables / strikethrough / autolinks. MinerU
// emits markdown tables inside its ``<details>`` description blocks
// (and occasionally in the main body), and without gfm those tables
// degrade silently into pipe-character paragraphs.
const REMARK_PLUGINS = [remarkGfm, remarkMath]
const REHYPE_PLUGINS = [rehypeRaw, rehypeSlug, rehypeKatex]

interface LibraryPreviewDocumentProps {
  markdown: string
  apiBase: string
  apiToken: string
  parsedDocumentId: string
}

function LibraryPreviewDocument({
  markdown,
  apiBase,
  apiToken,
  parsedDocumentId,
}: LibraryPreviewDocumentProps): JSX.Element {
  // ReactMarkdown re-instantiates components on every render unless we
  // memoize the map — without this, every img/table/a in the document
  // remounts on each parent re-render, which kicks off a fresh image
  // fetch and flickers the page.
  const markdownComponents = useMemo<Components>(
    () => ({
      img: (props) => (
        <PreviewAssetImage
          apiBase={apiBase}
          apiToken={apiToken}
          parsedDocumentId={parsedDocumentId}
          src={props.src}
          alt={props.alt}
        />
      ),
      table: StyledTable,
      a: ExternalSafeLink,
      pre: MermaidAwarePre,
    }),
    [apiBase, apiToken, parsedDocumentId],
  )

  return (
    <article className="prose-paper prose-paper-preview max-w-[72ch]">
      <ReactMarkdown
        remarkPlugins={REMARK_PLUGINS}
        rehypePlugins={REHYPE_PLUGINS}
        components={markdownComponents}
      >
        {markdown}
      </ReactMarkdown>
    </article>
  )
}

export default memo(LibraryPreviewDocument)

function StyledTable({
  children,
}: {
  children?: ReactNode
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
  children?: ReactNode
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

// We intercept at the ``<pre>`` level (rather than ``<code>``) so the
// mermaid diagram doesn't end up nested inside an irrelevant ``<pre>``
// wrapper with monospace styling. A fenced ``mermaid`` block always
// arrives as ``<pre><code class="language-mermaid">…</code></pre>``;
// when we recognize that shape we swap the whole ``<pre>`` for a
// ``<PreviewMermaidDiagram>``. Everything else (regular code blocks,
// inline ``<code>``) passes through untouched.
function MermaidAwarePre(props: { children?: ReactNode }): JSX.Element {
  const mermaidSource = extractMermaidSource(props.children)
  if (mermaidSource !== null) {
    return <PreviewMermaidDiagram source={mermaidSource} />
  }
  return <pre>{props.children}</pre>
}

function extractMermaidSource(children: ReactNode): string | null {
  const childArray = Children.toArray(children)
  if (childArray.length !== 1) return null
  const onlyChild = childArray[0]
  if (!isValidElement(onlyChild)) return null
  const childProps = onlyChild.props as {
    className?: string
    children?: ReactNode
  }
  const className = childProps.className || ''
  if (!/(^|\s)language-mermaid(\s|$)/.test(className)) return null
  const text = Children.toArray(childProps.children)
    .map((node) => (typeof node === 'string' ? node : ''))
    .join('')
  return text.replace(/\n$/, '')
}
