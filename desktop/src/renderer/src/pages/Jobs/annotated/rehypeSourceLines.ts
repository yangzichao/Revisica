// Rehype plugin that stamps each rendered element with the 1-based line
// of the markdown source it came from (``data-line``). Finding anchors
// carry line numbers into the same markdown text, so this attribute is
// the bridge between a finding and the DOM block it should highlight.

interface HastNodeLike {
  type: string
  tagName?: string
  properties?: Record<string, unknown>
  position?: { start?: { line?: number | null } | null } | null
  children?: HastNodeLike[]
}

export default function rehypeSourceLines() {
  return (tree: HastNodeLike): void => {
    stampSourceLines(tree)
  }
}

function stampSourceLines(node: HastNodeLike): void {
  if (node.type === 'element') {
    const line = node.position?.start?.line
    if (typeof line === 'number' && line > 0) {
      node.properties = { ...node.properties, dataLine: String(line) }
    }
  }
  for (const child of node.children ?? []) {
    stampSourceLines(child)
  }
}
