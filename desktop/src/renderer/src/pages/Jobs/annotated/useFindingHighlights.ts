import { useCallback, useEffect, useRef, useState } from 'react'
import type { Finding } from './types'
import { SEVERITY_STYLES, severityStyle } from './severity'

// Drives the in-document visuals for a set of anchored findings:
//
// 1. Block tint — every finding maps to the rendered element whose
//    ``data-line`` is closest at-or-before the finding's line number;
//    that block gets a severity-colored left border (CSS classes).
// 2. Exact-quote marks — findings whose anchor resolved ``exact`` also get
//    a character-precise mark via the CSS Custom Highlight API, which
//    paints DOM Ranges without mutating the rendered tree.
//
// Returns scrollToFinding for sidebar→document navigation and
// findingIdsForBlock so clicks in the document can select a finding.

const ACTIVE_HIGHLIGHT_NAME = 'revisica-finding-active'

export function useFindingHighlights(
  containerRef: React.RefObject<HTMLElement>,
  findings: Finding[],
  activeFindingId: string | null,
): {
  scrollToFinding: (findingId: string) => void
  findingIdsForBlock: (element: HTMLElement) => string[]
  documentReady: boolean
} {
  const blockByFindingId = useRef<Map<string, HTMLElement>>(new Map())
  const findingIdsByBlock = useRef<Map<HTMLElement, string[]>>(new Map())
  // The markdown tree renders asynchronously relative to the first effect
  // pass; re-run the mapping once blocks exist.
  const [documentReady, setDocumentReady] = useState(false)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const apply = (): void => {
      const blocks = collectLineBlocks(container)
      if (blocks.length === 0) return
      setDocumentReady(true)

      blockByFindingId.current = new Map()
      findingIdsByBlock.current = new Map()
      const highlightRanges = new Map<string, Range[]>()

      for (const finding of findings) {
        const block = blockForLine(blocks, finding.anchor.line_number)
        if (!block) continue
        blockByFindingId.current.set(finding.id, block)
        const ids = findingIdsByBlock.current.get(block) ?? []
        ids.push(finding.id)
        findingIdsByBlock.current.set(block, ids)

        const style = severityStyle(finding.severity)
        block.classList.add('annotated-block', style.blockMarkClass)
        if (finding.id === activeFindingId) {
          block.classList.add('annotated-block-active')
        }

        if (finding.anchor.resolution === 'exact' && finding.anchor.quote) {
          const range = findQuoteRange(container, block, finding.anchor.quote)
          if (range) {
            const name =
              finding.id === activeFindingId ? ACTIVE_HIGHLIGHT_NAME : style.highlightName
            const ranges = highlightRanges.get(name) ?? []
            ranges.push(range)
            highlightRanges.set(name, ranges)
          }
        }
      }

      registerHighlights(highlightRanges)
    }

    apply()
    // Re-apply after layout shifts (images loading, KaTeX settling).
    const observer = new MutationObserver(() => apply())
    observer.observe(container, { childList: true, subtree: true })

    return () => {
      observer.disconnect()
      clearHighlights()
      container
        .querySelectorAll('.annotated-block')
        .forEach((element) =>
          element.classList.remove(
            'annotated-block',
            'annotated-block-active',
            ...Object.values(SEVERITY_STYLES).map((s) => s.blockMarkClass),
          ),
        )
    }
  }, [containerRef, findings, activeFindingId])

  const scrollToFinding = useCallback((findingId: string): void => {
    const block = blockByFindingId.current.get(findingId)
    block?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [])

  const findingIdsForBlock = useCallback((element: HTMLElement): string[] => {
    let current: HTMLElement | null = element
    while (current) {
      const ids = findingIdsByBlock.current.get(current)
      if (ids && ids.length > 0) return ids
      current = current.parentElement
    }
    return []
  }, [])

  return { scrollToFinding, findingIdsForBlock, documentReady }
}

// ── block mapping ───────────────────────────────────────────────────

interface LineBlock {
  line: number
  element: HTMLElement
}

function collectLineBlocks(container: HTMLElement): LineBlock[] {
  const elements = Array.from(container.querySelectorAll<HTMLElement>('[data-line]'))
  return elements
    .map((element) => ({ line: Number(element.dataset.line), element }))
    .filter((block) => Number.isFinite(block.line))
    .sort((a, b) => a.line - b.line)
}

function blockForLine(blocks: LineBlock[], line: number | null): HTMLElement | null {
  if (line === null || blocks.length === 0) return null
  let best: LineBlock | null = null
  for (const block of blocks) {
    if (block.line > line) break
    // Prefer the latest-starting (deepest/nearest) block at or before the
    // anchor line; ties go to the later element in document order, which
    // is the more deeply nested one.
    best = block
  }
  return (best ?? blocks[0]).element
}

// ── quote → DOM Range ───────────────────────────────────────────────

interface TextIndex {
  normalized: string
  // For each char in ``normalized``: the text node and offset it came from.
  nodes: Text[]
  offsets: number[]
}

function buildTextIndex(root: HTMLElement): TextIndex {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) =>
      // KaTeX's hidden MathML mirror duplicates every formula's text —
      // matching inside it would paint invisible highlights.
      node.parentElement?.closest('.katex-mathml')
        ? NodeFilter.FILTER_REJECT
        : NodeFilter.FILTER_ACCEPT,
  })
  const chars: string[] = []
  const nodes: Text[] = []
  const offsets: number[] = []
  let inWhitespace = false
  let textNode = walker.nextNode() as Text | null
  while (textNode) {
    const text = textNode.data
    for (let index = 0; index < text.length; index += 1) {
      if (/\s/.test(text[index])) {
        if (inWhitespace) continue
        chars.push(' ')
        nodes.push(textNode)
        offsets.push(index)
        inWhitespace = true
      } else {
        chars.push(text[index])
        nodes.push(textNode)
        offsets.push(index)
        inWhitespace = false
      }
    }
    textNode = walker.nextNode() as Text | null
  }
  return { normalized: chars.join(''), nodes, offsets }
}

function findQuoteRange(
  container: HTMLElement,
  preferredBlock: HTMLElement,
  quote: string,
): Range | null {
  const needle = quote.split(/\s+/).filter(Boolean).join(' ')
  if (needle.length < 3) return null

  // Search the preferred block first; markdown/math syntax can shift text
  // across blocks, so fall back to the whole document.
  for (const root of [preferredBlock, container]) {
    const index = buildTextIndex(root)
    const position = index.normalized.indexOf(needle)
    if (position === -1) continue
    const range = document.createRange()
    range.setStart(index.nodes[position], index.offsets[position])
    const last = position + needle.length - 1
    range.setEnd(index.nodes[last], index.offsets[last] + 1)
    return range
  }
  return null
}

// ── CSS Custom Highlight registry ───────────────────────────────────

const OWNED_HIGHLIGHT_NAMES = [
  ...Object.values(SEVERITY_STYLES).map((style) => style.highlightName),
  ACTIVE_HIGHLIGHT_NAME,
]

function highlightsSupported(): boolean {
  return typeof Highlight !== 'undefined' && typeof CSS !== 'undefined' && 'highlights' in CSS
}

function registerHighlights(rangesByName: Map<string, Range[]>): void {
  if (!highlightsSupported()) return
  clearHighlights()
  for (const [name, ranges] of rangesByName) {
    CSS.highlights.set(name, new Highlight(...ranges))
  }
}

function clearHighlights(): void {
  if (!highlightsSupported()) return
  for (const name of OWNED_HIGHLIGHT_NAMES) {
    CSS.highlights.delete(name)
  }
}
