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
import LibraryPickerInline from './LibraryPickerInline'
import type {
  FileType,
  MineruBackend,
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
  // Optional opt-in: when the user drops more than one file, the host page
  // can take over (batch parse mode in ParsePage). If not provided, only the
  // first dropped file is consumed (the wizard's single-file behavior).
  onMultiFileDrop?: (paths: string[]) => void
}

export function detectFileType(path: string): FileType {
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
  onMultiFileDrop,
}: Step1Props): JSX.Element {
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUnsupportedFormatVisible, setIsUnsupportedFormatVisible] = useState(false)
  const [dropZoneErrorMessage, setDropZoneErrorMessage] = useState<string | null>(null)
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
        setIsUnsupportedFormatVisible(true)
        setTimeout(() => setIsUnsupportedFormatVisible(false), 1400)
        return
      }
      dispatch({ type: 'SET_FILE', filePath: path, fileType })
    },
    [dispatch],
  )

  const showDropError = useCallback((message: string): void => {
    setDropZoneErrorMessage(message)
    setTimeout(() => setDropZoneErrorMessage(null), 2400)
  }, [])

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      setIsDragOver(false)
      const files = event.dataTransfer.files
      if (files.length === 0) return

      // Multi-file path: only when the host page opted in. Collect every
      // local path (skipping cloud-only / sandboxed entries silently) and
      // hand them off as a batch.
      if (files.length > 1 && onMultiFileDrop) {
        const paths: string[] = []
        let unsupportedCount = 0
        let unreadableCount = 0
        for (let i = 0; i < files.length; i++) {
          const rawPath = window.api?.getPathForFile?.(files[i]) ?? ''
          const path = rawPath.trim()
          if (!path || !path.startsWith('/')) {
            unreadableCount += 1
            continue
          }
          if (!detectFileType(path)) {
            unsupportedCount += 1
            continue
          }
          paths.push(path)
        }
        if (paths.length === 0) {
          // Pick the message that best matches what actually went wrong.
          if (unsupportedCount > 0 && unreadableCount === 0) {
            setIsUnsupportedFormatVisible(true)
            setTimeout(() => setIsUnsupportedFormatVisible(false), 1400)
          } else {
            showDropError(
              "Couldn't read local paths for these files. Drag them from Finder, or use the browse button.",
            )
          }
          return
        }
        if (unsupportedCount > 0) {
          setIsUnsupportedFormatVisible(true)
          setTimeout(() => setIsUnsupportedFormatVisible(false), 1400)
        }
        // If after filtering only one usable file remains, prefer the
        // single-file UI (cleaner than a "Batch · 1 file" panel).
        if (paths.length === 1) {
          acceptPath(paths[0])
          return
        }
        onMultiFileDrop(paths)
        return
      }

      const file = files[0]
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
    [acceptPath, showDropError, onMultiFileDrop],
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
          Drop a new file, or pick one you've already parsed.
        </p>
      </header>

      <div
        className={cn(
          'flex items-center gap-2 mb-4 transition-colors duration-150',
          isUnsupportedFormatVisible && 'text-danger',
        )}
      >
        <FormatChip icon={FileType2} label="PDF" isUnsupportedFormatVisible={isUnsupportedFormatVisible} />
        <FormatChip icon={FileCode} label="TeX" isUnsupportedFormatVisible={isUnsupportedFormatVisible} />
        <FormatChip icon={FileText} label="Markdown" isUnsupportedFormatVisible={isUnsupportedFormatVisible} />
      </div>

      {isUnsupportedFormatVisible && (
        <div className="text-xs text-danger mb-2 font-medium">
          Unsupported format. We accept .pdf, .tex, .md, or .mmd.
        </div>
      )}

      {dropZoneErrorMessage && (
        <div className="text-xs text-danger mb-2 font-medium">
          {dropZoneErrorMessage}
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
              : isUnsupportedFormatVisible || dropZoneErrorMessage
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
              {onMultiFileDrop
                ? 'Drop one or more papers here, or click to choose'
                : 'Drop a paper here, or click to choose'}
            </p>
            <p className="text-xs text-ink-faint mt-1">.pdf · .tex · .md · .mmd</p>
          </>
        )}
      </div>

      {!state.filePath && (
        <LibraryPickerInline apiBase={apiBase} apiToken={apiToken} />
      )}

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
              mineruBackend={state.mineruBackend}
              onMineruBackendChange={(backend) =>
                dispatch({ type: 'SET_MINERU_BACKEND', backend })
              }
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
  isUnsupportedFormatVisible,
}: {
  icon: typeof FileCode
  label: string
  isUnsupportedFormatVisible: boolean
}): JSX.Element {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full',
        'border text-xs font-medium transition-colors duration-150',
        isUnsupportedFormatVisible
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
  mineruBackend,
  onMineruBackendChange,
}: {
  apiBase: string
  apiToken: string
  isLoading: boolean
  mineru: ParserInfo | undefined
  mathpix: ParserInfo | undefined
  selected: ParserChoice
  onSelect: (parser: ParserChoice) => void
  onRefresh: () => void
  mineruBackend: MineruBackend
  onMineruBackendChange: (backend: MineruBackend) => void
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

          {selected === 'mineru' && mineru?.available && (
            <MineruBackendToggle
              value={mineruBackend}
              onChange={onMineruBackendChange}
            />
          )}
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

function MineruBackendToggle({
  value,
  onChange,
}: {
  value: MineruBackend
  onChange: (backend: MineruBackend) => void
}): JSX.Element {
  return (
    <div className="mt-3">
      <div className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-2">
        MinerU mode
      </div>
      <div className="grid grid-cols-2 gap-2">
        <BackendPill
          title="Accurate"
          subtitle="VLM · best on complex layouts"
          hint="Slow on long PDFs"
          isSelected={value === 'vlm'}
          onClick={() => onChange('vlm')}
        />
        <BackendPill
          title="Fast"
          subtitle="Pipeline · classic OCR"
          hint="Recommended for books"
          isSelected={value === 'pipeline'}
          onClick={() => onChange('pipeline')}
        />
      </div>
    </div>
  )
}

function BackendPill({
  title,
  subtitle,
  hint,
  isSelected,
  onClick,
}: {
  title: string
  subtitle: string
  hint: string
  isSelected: boolean
  onClick: () => void
}): JSX.Element {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-lg border px-3 py-2 text-left transition-colors duration-150',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40',
        isSelected
          ? 'border-accent bg-accent/5'
          : 'border-paper-300 hover:border-paper-400 bg-paper-50',
      )}
    >
      <div className="text-sm font-semibold text-ink leading-tight">{title}</div>
      <div className="text-xs text-ink-secondary mt-0.5">{subtitle}</div>
      <div className="text-[11px] text-ink-faint mt-1 italic">{hint}</div>
    </button>
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
  const [saveCredentialsError, setSaveCredentialsError] = useState<string | null>(null)

  const handleSave = async (): Promise<void> => {
    if (!appId.trim() || !appKey.trim()) return
    setIsSaving(true)
    setSaveCredentialsError(null)
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
      setSaveCredentialsError(err instanceof Error ? err.message : 'Save failed')
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
          {saveCredentialsError && (
            <span className="text-xs text-danger font-medium">{saveCredentialsError}</span>
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

