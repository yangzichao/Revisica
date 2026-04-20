import { useState, useCallback, useEffect, useMemo } from 'react'
import {
  FileUp,
  FileCheck,
  Cpu,
  Cloud,
  FileCode,
  FileText,
  FileType2,
  Clipboard,
  ClipboardCheck,
  Loader2,
  RefreshCw,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'
import ModeCard from '@/components/ModeCard'
import type {
  FileType,
  ParserChoice,
  ParserInfo,
  WizardState,
  WizardAction,
} from './types'

interface Step1Props {
  apiBase: string
  apiToken: string
  state: WizardState
  dispatch: React.Dispatch<WizardAction>
}

function detectFileType(path: string): FileType {
  const lowered = path.toLowerCase()
  if (lowered.endsWith('.pdf')) return 'pdf'
  if (lowered.endsWith('.tex')) return 'tex'
  if (lowered.endsWith('.md') || lowered.endsWith('.mmd') || lowered.endsWith('.markdown')) {
    return 'md'
  }
  return null
}

export default function Step1ImportFile({
  apiBase,
  apiToken,
  state,
  dispatch,
}: Step1Props): JSX.Element {
  const [isDragOver, setIsDragOver] = useState(false)
  const [unsupportedFlash, setUnsupportedFlash] = useState(false)
  const [dropErrorFlash, setDropErrorFlash] = useState<string | null>(null)
  const [parsers, setParsers] = useState<ParserInfo[]>([])
  const [isLoadingParsers, setIsLoadingParsers] = useState(true)

  const fetchParsers = useCallback(async (): Promise<void> => {
    try {
      const response = await apiFetch(apiBase, apiToken, '/api/config/parsers')
      if (response.ok) {
        const data = await response.json()
        setParsers(data.parsers || [])
      }
    } catch {
      // Will degrade gracefully — all parsers shown as unavailable
    } finally {
      setIsLoadingParsers(false)
    }
  }, [apiBase, apiToken])

  useEffect(() => {
    fetchParsers()
  }, [fetchParsers])

  const acceptPath = useCallback(
    (path: string): void => {
      const fileType = detectFileType(path)
      if (!fileType) {
        setUnsupportedFlash(true)
        setTimeout(() => setUnsupportedFlash(false), 1400)
        return
      }
      dispatch({ type: 'SET_FILE', filePath: path, fileType })
    },
    [dispatch],
  )

  const showDropError = useCallback((message: string): void => {
    setDropErrorFlash(message)
    setTimeout(() => setDropErrorFlash(null), 2400)
  }, [])

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      setIsDragOver(false)
      const file = event.dataTransfer.files[0]
      if (!file) return
      // Electron 32+ removed File.path; webUtils.getPathForFile is the
      // replacement. Returns '' for non-local sources (iCloud cloud-only
      // items, web drags, sandboxed attachments).
      const rawPath = window.api?.getPathForFile?.(file) ?? ''
      const path = rawPath.trim()
      // TODO: Windows — widen the absolute-path check if Windows is added.
      if (!path || !path.startsWith('/')) {
        showDropError(
          "Couldn't read a local path for this file. Drag it from Finder, or use the browse button.",
        )
        return
      }
      acceptPath(path)
    },
    [acceptPath, showDropError],
  )

  const handleBrowse = useCallback(async (): Promise<void> => {
    const picker = window.api?.openPaperPicker
    if (!picker) return
    const path = await picker()
    if (!path) return
    acceptPath(path)
  }, [acceptPath])

  const mineruInfo = useMemo(
    () => parsers.find((p) => p.name === 'mineru'),
    [parsers],
  )
  const mathpixInfo = useMemo(
    () => parsers.find((p) => p.name === 'mathpix'),
    [parsers],
  )
  const pandocInfo = useMemo(
    () => parsers.find((p) => p.name === 'pandoc'),
    [parsers],
  )
  const markdownInfo = useMemo(
    () => parsers.find((p) => p.name === 'markdown'),
    [parsers],
  )

  return (
    <div>
      <header className="mb-6">
        <h2 className="font-serif text-xl font-semibold text-ink tracking-tight">
          Import your paper
        </h2>
        <p className="font-serif text-sm text-ink-tertiary italic mt-1">
          Drop a file, or reuse the setup from a past job.
        </p>
      </header>

      <div
        className={cn(
          'flex items-center gap-2 mb-4 transition-colors duration-150',
          unsupportedFlash && 'text-danger',
        )}
      >
        <FormatChip icon={FileType2} label="PDF" flash={unsupportedFlash} />
        <FormatChip icon={FileCode} label="TeX" flash={unsupportedFlash} />
        <FormatChip icon={FileText} label="Markdown" flash={unsupportedFlash} />
      </div>

      {unsupportedFlash && (
        <div className="text-xs text-danger mb-2 font-medium">
          Unsupported format. We accept .pdf, .tex, .md, or .mmd.
        </div>
      )}

      {dropErrorFlash && (
        <div className="text-xs text-danger mb-2 font-medium">
          {dropErrorFlash}
        </div>
      )}

      <div
        role="button"
        tabIndex={0}
        aria-label="Choose a paper to import"
        className={cn(
          'rounded-xl border-2 border-dashed px-6 py-10 text-center',
          'transition-colors duration-200 cursor-pointer mb-6',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40',
          isDragOver
            ? 'border-accent bg-accent/5'
            : state.filePath
              ? 'border-success/40 bg-success/[0.03]'
              : unsupportedFlash || dropErrorFlash
                ? 'border-danger/60 bg-danger/5'
                : 'border-paper-300 hover:border-paper-400',
        )}
        onClick={handleBrowse}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            handleBrowse()
          }
        }}
        onDrop={handleDrop}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragOver(true)
        }}
        onDragLeave={() => setIsDragOver(false)}
      >
        {state.filePath ? (
          <div className="flex items-center justify-center gap-3">
            <FileCheck size={20} className="text-success" strokeWidth={1.7} />
            <span className="font-mono text-sm text-ink truncate max-w-xs">
              {state.filePath.split('/').pop()}
            </span>
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation()
                dispatch({ type: 'CLEAR_FILE' })
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
              Drop a paper here, or click to choose
            </p>
            <p className="text-xs text-ink-faint mt-1">.pdf · .tex · .md · .mmd</p>
          </>
        )}
      </div>

      {/* Format-specific sub-section */}
      {state.filePath && state.fileType && (
        <div className="mb-2">
          {state.fileType === 'pdf' && (
            <PdfParserSection
              apiBase={apiBase}
              apiToken={apiToken}
              isLoading={isLoadingParsers}
              mineru={mineruInfo}
              mathpix={mathpixInfo}
              selected={state.parserChoice}
              onSelect={(parser) => dispatch({ type: 'SET_PARSER', parser })}
              onRefresh={fetchParsers}
            />
          )}
          {state.fileType === 'tex' && (
            <ReadyParserRow
              title="Pandoc"
              description={
                pandocInfo?.available
                  ? 'LaTeX → Markdown via Pandoc. No configuration needed.'
                  : 'Pandoc not installed — falling back to built-in tex-basic parser.'
              }
              available={pandocInfo?.available ?? true}
            />
          )}
          {state.fileType === 'md' && (
            <ReadyParserRow
              title="Markdown (passthrough)"
              description="No configuration needed."
              available={markdownInfo?.available ?? true}
            />
          )}
        </div>
      )}
    </div>
  )
}

function FormatChip({
  icon: Icon,
  label,
  flash,
}: {
  icon: typeof FileCode
  label: string
  flash: boolean
}): JSX.Element {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full',
        'border text-xs font-medium transition-colors duration-150',
        flash
          ? 'border-danger/50 bg-danger/10 text-danger'
          : 'border-paper-300 bg-paper-50 text-ink-tertiary',
      )}
    >
      <Icon size={11} strokeWidth={1.8} />
      {label}
    </span>
  )
}

// ── PDF parser sub-section ─────────────────────────────────────────────

function PdfParserSection({
  apiBase,
  apiToken,
  isLoading,
  mineru,
  mathpix,
  selected,
  onSelect,
  onRefresh,
}: {
  apiBase: string
  apiToken: string
  isLoading: boolean
  mineru: ParserInfo | undefined
  mathpix: ParserInfo | undefined
  selected: ParserChoice
  onSelect: (parser: ParserChoice) => void
  onRefresh: () => void
}): JSX.Element {
  return (
    <div>
      <div className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-2">
        Choose a PDF parser
      </div>
      {isLoading ? (
        <div className="flex items-center gap-2 text-xs text-ink-tertiary py-2">
          <Loader2 size={12} className="animate-spin" />
          Detecting parsers...
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <ModeCard
              icon={Cpu}
              title="MinerU"
              description="Local · private · GPU/MPS"
              isSelected={selected === 'mineru'}
              onClick={() => onSelect('mineru')}
              trailing={<StatusIndicator available={!!mineru?.available} />}
            />
            <ModeCard
              icon={Cloud}
              title="Mathpix"
              description="Cloud · ~$0.01 per page"
              isSelected={selected === 'mathpix'}
              onClick={() => onSelect('mathpix')}
              trailing={<StatusIndicator available={!!mathpix?.available} />}
            />
          </div>

          {selected === 'mineru' && !mineru?.available && (
            <MineruSetupPanel
              installHint={mineru?.install_hint || "pip install 'mineru[all]'"}
              onRecheck={onRefresh}
            />
          )}
          {selected === 'mathpix' && !mathpix?.available && (
            <MathpixSetupPanel
              apiBase={apiBase}
              apiToken={apiToken}
              onSaved={onRefresh}
            />
          )}
        </>
      )}
    </div>
  )
}

function StatusIndicator({ available }: { available: boolean }): JSX.Element {
  return (
    <div
      className={cn(
        'w-2 h-2 rounded-full shrink-0',
        available ? 'bg-success' : 'bg-paper-400',
      )}
    />
  )
}

function MineruSetupPanel({
  installHint,
  onRecheck,
}: {
  installHint: string
  onRecheck: () => void
}): JSX.Element {
  const [copied, setCopied] = useState(false)

  const handleCopy = async (): Promise<void> => {
    try {
      await navigator.clipboard.writeText(installHint)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard may be unavailable in electron restricted contexts
    }
  }

  return (
    <div className="card px-4 py-4 bg-paper-100/60">
      <div className="text-xs font-semibold text-ink-secondary mb-2">
        MinerU isn't installed yet
      </div>
      <div className="text-xs text-ink-tertiary mb-3">
        Run this in your Python environment, then click Re-check:
      </div>
      <div className="flex items-center gap-2 mb-3">
        <code className="flex-1 font-mono text-[12px] text-ink bg-paper-200/80 px-3 py-2 rounded-md truncate">
          {installHint}
        </code>
        <button
          type="button"
          onClick={handleCopy}
          className="btn-ghost px-2.5 py-2"
          title="Copy to clipboard"
        >
          {copied ? (
            <ClipboardCheck size={13} className="text-success" />
          ) : (
            <Clipboard size={13} />
          )}
        </button>
      </div>
      <button
        type="button"
        onClick={onRecheck}
        className="btn-ghost px-3 py-1.5 text-xs"
      >
        <RefreshCw size={12} />
        Re-check installation
      </button>
    </div>
  )
}

function MathpixSetupPanel({
  apiBase,
  apiToken,
  onSaved,
}: {
  apiBase: string
  apiToken: string
  onSaved: () => void
}): JSX.Element {
  const [appId, setAppId] = useState('')
  const [appKey, setAppKey] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async (): Promise<void> => {
    if (!appId.trim() || !appKey.trim()) return
    setIsSaving(true)
    setError(null)
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        '/api/config/parsers/mathpix/credentials',
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            app_id: appId.trim(),
            app_key: appKey.trim(),
          }),
        },
      )
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || `Save failed (${response.status})`)
      }
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="card px-4 py-4 bg-paper-100/60">
      <div className="text-xs font-semibold text-ink-secondary mb-2">
        Mathpix needs credentials
      </div>
      <div className="text-xs text-ink-tertiary mb-3">
        Sign up at{' '}
        <span className="font-mono text-[11px]">accounts.mathpix.com</span>{' '}
        to get an App ID and App Key.
      </div>
      <div className="space-y-2">
        <input
          type="text"
          placeholder="App ID"
          value={appId}
          onChange={(e) => setAppId(e.target.value)}
          className="input font-mono text-sm"
        />
        <input
          type="password"
          placeholder="App Key"
          value={appKey}
          onChange={(e) => setAppKey(e.target.value)}
          className="input font-mono text-sm"
        />
        <div className="flex items-center gap-2 pt-1">
          <button
            type="button"
            onClick={handleSave}
            disabled={!appId.trim() || !appKey.trim() || isSaving}
            className="btn-primary px-4 py-2 text-sm"
          >
            {isSaving ? 'Saving...' : 'Save credentials'}
          </button>
          {error && (
            <span className="text-xs text-danger font-medium">{error}</span>
          )}
        </div>
      </div>
    </div>
  )
}

// ── TeX / Markdown ready row ──────────────────────────────────────────

function ReadyParserRow({
  title,
  description,
  available,
}: {
  title: string
  description: string
  available: boolean
}): JSX.Element {
  return (
    <div className="card flex items-center gap-3 px-4 py-3.5">
      <StatusIndicator available={available} />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-ink">{title}</div>
        <div className="text-xs text-ink-tertiary mt-0.5">{description}</div>
      </div>
    </div>
  )
}

