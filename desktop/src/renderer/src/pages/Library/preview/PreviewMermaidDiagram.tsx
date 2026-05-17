import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'

// Mermaid keeps a module-level config + counter, so initialization must
// happen exactly once per renderer process. Doing it inline at module
// load also means the first <PreviewMermaidDiagram> render doesn't
// race a still-uninitialized engine.
let mermaidInitialized = false
function ensureMermaidInitialized(): void {
  if (mermaidInitialized) return
  mermaid.initialize({
    startOnLoad: false,
    // ``neutral`` is the closest of mermaid's built-in palettes to the
    // warm-paper reader theme — black/grey strokes on a white-ish
    // background. ``default`` is heavy blue and clashes hard with the
    // surrounding text.
    theme: 'neutral',
    // ``strict`` disables any user-supplied HTML inside diagram nodes
    // and bans click handlers. Our diagram sources come from MinerU's
    // OCR of arbitrary PDFs, so we treat them as untrusted.
    securityLevel: 'strict',
    fontFamily: 'inherit',
    flowchart: { htmlLabels: false, curve: 'basis' },
  })
  mermaidInitialized = true
}

// mermaid.render needs a unique DOM id per call; it temporarily mounts
// an off-screen SVG with that id while serializing. A module-level
// counter keeps ids stable across renders of the same component (so
// re-renders for unchanged source don't churn ids unnecessarily).
let renderCounter = 0

interface PreviewMermaidDiagramProps {
  source: string
}

export default function PreviewMermaidDiagram({
  source,
}: PreviewMermaidDiagramProps): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null)
  const [renderError, setRenderError] = useState<string | null>(null)

  useEffect(() => {
    ensureMermaidInitialized()
    let cancelled = false
    setRenderError(null)
    const renderId = `revisica-mermaid-${++renderCounter}`
    mermaid
      .render(renderId, source)
      .then(({ svg }) => {
        if (cancelled) return
        if (containerRef.current) {
          containerRef.current.innerHTML = svg
        }
      })
      .catch((err) => {
        if (cancelled) return
        const message = err instanceof Error ? err.message : String(err)
        setRenderError(message)
      })
    return () => {
      cancelled = true
    }
  }, [source])

  if (renderError) {
    // Mermaid sometimes leaves an orphan error div on document.body
    // when render() throws; React's tree is unaffected and the next
    // render will clean it up via its own bookkeeping. We surface the
    // raw source so users can still read the diagram description.
    return (
      <div className="my-4">
        <div className="text-xs text-ink-tertiary mb-1 italic">
          mermaid render failed — showing source
        </div>
        <pre className="overflow-x-auto rounded-md border border-paper-300 bg-paper-50 p-3 text-xs">
          <code>{source}</code>
        </pre>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="my-4 flex justify-center [&_svg]:max-w-full [&_svg]:h-auto"
    />
  )
}
