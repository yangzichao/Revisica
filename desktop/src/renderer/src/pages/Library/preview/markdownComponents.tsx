import { Children, isValidElement } from 'react'
import type { ReactNode } from 'react'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import rehypeRaw from 'rehype-raw'
import rehypeSlug from 'rehype-slug'
import PreviewMermaidDiagram from './PreviewMermaidDiagram'

// Shared ReactMarkdown configuration for rendering a parsed paper —
// used by the Library preview and the Jobs annotated review view.
//
// remark-gfm enables GFM tables / strikethrough / autolinks. MinerU
// emits markdown tables inside its ``<details>`` description blocks
// (and occasionally in the main body), and without gfm those tables
// degrade silently into pipe-character paragraphs.
export const REMARK_PLUGINS = [remarkGfm, remarkMath]
export const REHYPE_PLUGINS = [rehypeRaw, rehypeSlug, rehypeKatex]

export function StyledTable({
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

export function ExternalSafeLink({
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
export function MermaidAwarePre(props: { children?: ReactNode }): JSX.Element {
  const mermaidSource = extractMermaidSource(props.children)
  if (mermaidSource !== null) {
    return <PreviewMermaidDiagram source={mermaidSource} />
  }
  return <pre>{props.children}</pre>
}

// MinerU attaches a ``<details>`` block to every figure with a class
// label as the ``<summary>`` and either (a) a mermaid diagram, (b) a
// markdown table of the figure's tabular data, or (c) a plain-text OCR
// description as the body. Cases (a) and (b) carry information the
// image itself doesn't expose; case (c) is redundant alt-text that
// duplicates the figure caption directly below, and showing it produces
// a confusing "▼ FLOWCHART → paragraph of prose" disclosure. We hide
// case (c) at the renderer level so the markdown on disk stays
// faithful to what MinerU produced.
export function SubstantiveDetails({
  children,
}: {
  children?: ReactNode
}): JSX.Element | null {
  if (!detailsHasNonProseBody(children)) {
    return null
  }
  return <details>{children}</details>
}

function detailsHasNonProseBody(children: ReactNode): boolean {
  // Walk the immediate children. Anything that isn't <summary>, plain
  // text, or a paragraph counts as "substantive" — a <pre> (mermaid),
  // <table>, embedded <img>, or any of our custom React components
  // (PreviewMermaidDiagram, StyledTable, PreviewAssetImage) all qualify
  // and keep the details block visible.
  const nodes = Children.toArray(children)
  for (const node of nodes) {
    // Plain strings / numbers / null land here — pure text content, prose.
    if (!isValidElement(node)) continue
    // Function/forwardRef/etc. components are always our overrides
    // (mermaid, table, image), so we treat them as substantive.
    if (typeof node.type !== 'string') return true
    // HTML tags: <summary> is the label, <p> is OCR description prose.
    // Everything else (<pre>, <table>, <img>, <div>, ...) is content.
    if (node.type === 'summary' || node.type === 'p') continue
    return true
  }
  return false
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
