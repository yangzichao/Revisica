import { useState, useCallback } from 'react'
import { FileUp, FileCheck, Play, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'

// ── Types ──────────────────────────────────────────────────────────

interface IngestResult {
  parser_used: string
  markdown: string
  title: string
  authors: string[]
  abstract: string
  section_count: number
}

const PARSERS = [
  { value: 'auto', label: 'Auto', description: 'Detect best parser' },
  { value: 'mineru', label: 'MinerU', description: 'Local PDF (GPU)' },
  { value: 'marker', label: 'Marker', description: 'Local PDF' },
  { value: 'mathpix', label: 'Mathpix', description: 'Cloud API' },
  { value: 'pandoc', label: 'Pandoc', description: 'LaTeX → MD' },
  { value: 'tex-basic', label: 'TeX Basic', description: 'Built-in LaTeX' },
  { value: 'markdown', label: 'Markdown', description: 'Passthrough' },
]

// ── Component ──────────────────────────────────────────────────────

export default function Parse({ apiBase }: { apiBase: string }): JSX.Element {
  const [filePath, setFilePath] = useState('')
  const [parser, setParser] = useState('auto')
  const [isParsing, setIsParsing] = useState(false)
  const [result, setResult] = useState<IngestResult | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    setIsDragOver(false)
    const file = event.dataTransfer.files[0]
    if (file) {
      const electronFile = file as File & { path?: string }
      setFilePath(electronFile.path || file.name)
    }
  }, [])

  const handleParse = async (): Promise<void> => {
    if (!filePath.trim()) return
    setIsParsing(true)
    setErrorMessage(null)
    setResult(null)

    try {
      const response = await fetch(`${apiBase}/api/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath, parser }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to parse')
      }

      setResult(await response.json())
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Parse failed')
    } finally {
      setIsParsing(false)
    }
  }

  const canParse = filePath.trim().length > 0 && !isParsing

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-12">
        <header className="mb-10">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            Parse
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Test document ingestion and view parsed output
          </p>
        </header>

        {/* File input */}
        <div className="max-w-lg">
          <div
            className={cn(
              'rounded-xl border-2 border-dashed px-6 py-8 text-center',
              'transition-colors duration-200 cursor-pointer mb-3',
              isDragOver
                ? 'border-accent bg-accent/5'
                : filePath
                  ? 'border-success/40 bg-success/[0.03]'
                  : 'border-paper-300 hover:border-paper-400',
            )}
            onDrop={handleDrop}
            onDragOver={(event) => {
              event.preventDefault()
              setIsDragOver(true)
            }}
            onDragLeave={() => setIsDragOver(false)}
          >
            {filePath ? (
              <div className="flex items-center justify-center gap-3">
                <FileCheck size={20} className="text-success" strokeWidth={1.7} />
                <span className="font-mono text-sm text-ink truncate max-w-xs">
                  {filePath.split('/').pop()}
                </span>
                <button
                  onClick={(event) => {
                    event.stopPropagation()
                    setFilePath('')
                    setResult(null)
                  }}
                  className="text-xs text-ink-tertiary hover:text-accent underline underline-offset-2 bg-transparent border-none cursor-pointer"
                >
                  change
                </button>
              </div>
            ) : (
              <>
                <FileUp size={28} className="mx-auto mb-2 text-ink-faint" strokeWidth={1.3} />
                <p className="text-sm text-ink-secondary font-medium">
                  Drop a file here
                </p>
                <p className="text-xs text-ink-faint mt-1">.pdf, .tex, .md</p>
              </>
            )}
          </div>

          <input
            type="text"
            value={filePath}
            onChange={(event) => setFilePath(event.target.value)}
            placeholder="Or type a file path..."
            className="input font-mono mb-4"
          />

          {/* Parser selector + parse button */}
          <div className="flex gap-3 mb-8">
            <div className="flex-1">
              <label className="block text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-2">
                Parser
              </label>
              <select
                value={parser}
                onChange={(event) => setParser(event.target.value)}
                className="input"
              >
                {PARSERS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label} — {option.description}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={handleParse}
                disabled={!canParse}
                className="btn-primary px-5 py-2.5 shrink-0"
              >
                {isParsing ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Parsing...
                  </>
                ) : (
                  <>
                    <Play size={16} strokeWidth={2} />
                    Parse
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error */}
        {errorMessage && (
          <div className="rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger mb-6">
            {errorMessage}
          </div>
        )}

        {/* Result */}
        {result && (
          <section>
            {/* Metadata bar */}
            <div className="card flex flex-wrap items-center gap-x-6 gap-y-2 px-5 py-3.5 mb-4 text-sm">
              <MetadataItem label="Parser" value={result.parser_used} />
              {result.title && (
                <MetadataItem label="Title" value={result.title} />
              )}
              {result.authors.length > 0 && (
                <MetadataItem
                  label="Authors"
                  value={result.authors.join(', ')}
                />
              )}
              <MetadataItem
                label="Sections"
                value={String(result.section_count)}
              />
            </div>

            {/* Rendered markdown */}
            <div className="card px-6 py-6">
              <div className="prose-paper">
                <ReactMarkdown>{result.markdown}</ReactMarkdown>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

function MetadataItem({
  label,
  value,
}: {
  label: string
  value: string
}): JSX.Element {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-ink-faint">{label}:</span>
      <span className="font-medium text-ink truncate max-w-xs">{value}</span>
    </div>
  )
}
