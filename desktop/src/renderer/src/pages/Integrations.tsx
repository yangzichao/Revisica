import { useState, useEffect, useRef } from 'react'
import {
  Loader2,
  Terminal,
  Cloud,
  FileText,
  Sparkles,
  Download,
  Trash2,
  AlertTriangle,
} from 'lucide-react'
import { apiFetch } from '@/lib/api'
import {
  ApiProviderCard,
  CliProviderRow,
  CollapsibleProviderCard,
  EMPTY_CARD_STATE,
  isApiProvider,
  type Provider,
  type ProviderCardState,
} from '@/components/ProviderCard'

// ── Types ──────────────────────────────────────────────────────────

interface Parser {
  name: string
  display_name: string
  available: boolean
  requires?: string
  handles?: string[]
  install_hint?: string
}

interface MathpixCreds {
  app_id: string
  app_key: string
}

const EMPTY_MATHPIX: MathpixCreds = { app_id: '', app_key: '' }

// ── Main Component ─────────────────────────────────────────────────

export default function Integrations({
  apiBase,
  apiToken,
}: {
  apiBase: string
  apiToken: string
}): JSX.Element {
  const [providers, setProviders] = useState<Provider[]>([])
  const [parsers, setParsers] = useState<Parser[]>([])
  const [cardStates, setCardStates] = useState<Record<string, ProviderCardState>>({})
  const [mathpixCreds, setMathpixCreds] = useState<MathpixCreds>(EMPTY_MATHPIX)
  const [mathpixSaving, setMathpixSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const getCardState = (name: string): ProviderCardState => {
    return cardStates[name] ?? EMPTY_CARD_STATE
  }

  const updateCardState = (
    name: string,
    patch: Partial<ProviderCardState>,
  ): void => {
    setCardStates((previous) => ({
      ...previous,
      [name]: { ...(previous[name] ?? EMPTY_CARD_STATE), ...patch },
    }))
  }

  const fetchProviders = async (): Promise<void> => {
    try {
      const response = await apiFetch(apiBase, apiToken, '/api/providers')
      if (response.ok) {
        const data = await response.json()
        setProviders(data.providers)
      }
    } catch {
      // Backend may not be ready yet
    }
  }

  const fetchParsers = async (): Promise<void> => {
    try {
      const response = await apiFetch(apiBase, apiToken, '/api/config/parsers')
      if (response.ok) {
        const data = await response.json()
        setParsers(data.parsers ?? [])
      }
    } catch {
      // Backend may not be ready yet
    }
  }

  useEffect(() => {
    Promise.all([fetchProviders(), fetchParsers()]).finally(() =>
      setIsLoading(false),
    )
  }, [apiBase, apiToken])

  const handleSaveApiKey = async (providerName: string): Promise<void> => {
    const state = getCardState(providerName)
    if (!state.apiKey.trim()) return

    updateCardState(providerName, { isSaving: true })
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        `/api/providers/${providerName}/config`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: state.apiKey.trim() }),
        },
      )
      if (response.ok) {
        await fetchProviders()
      }
    } catch {
      // Will show as "not configured" in UI
    }
    updateCardState(providerName, { isSaving: false })
  }

  const handleTestProvider = async (providerName: string): Promise<void> => {
    updateCardState(providerName, { isTesting: true, testResult: null })
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        `/api/providers/${providerName}/test`,
        { method: 'POST' },
      )
      if (!response.ok) {
        updateCardState(providerName, {
          isTesting: false,
          testResult: { ok: false, message: `Server error (${response.status})` },
        })
        return
      }
      const data = await response.json()
      updateCardState(providerName, {
        isTesting: false,
        testResult: {
          ok: data.status === 'ok',
          message: data.status === 'ok' ? 'Connected' : data.error || 'Failed',
        },
      })
    } catch {
      updateCardState(providerName, {
        isTesting: false,
        testResult: { ok: false, message: 'Unreachable' },
      })
    }
  }

  const handleSaveMathpix = async (): Promise<void> => {
    if (!mathpixCreds.app_id.trim() || !mathpixCreds.app_key.trim()) return
    setMathpixSaving(true)
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        '/api/config/parsers/mathpix/credentials',
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            app_id: mathpixCreds.app_id.trim(),
            app_key: mathpixCreds.app_key.trim(),
          }),
        },
      )
      if (response.ok) {
        setMathpixCreds(EMPTY_MATHPIX)
        await fetchParsers()
      }
    } catch {
      // Parser will remain "needs credentials" in UI
    }
    setMathpixSaving(false)
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="animate-spin text-ink-faint" size={24} />
      </div>
    )
  }

  const cliProviders = providers.filter((p) => !isApiProvider(p.name))
  const apiProviders = providers.filter((p) => isApiProvider(p.name))
  const mathpix = parsers.find((p) => p.name === 'mathpix')
  const mineru = parsers.find((p) => p.name === 'mineru')

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-lg mx-auto px-8 py-12">
        <header className="mb-10">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            Integrations
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Connect Revisica to AI models and document parsers
          </p>
        </header>

        {/* Document Parsing */}
        <section className="mb-10">
          <SectionHeader icon={FileText} title="Document Parsing" />
          <div className="space-y-3">
            <MathPixCard
              parser={mathpix}
              creds={mathpixCreds}
              isSaving={mathpixSaving}
              onChange={setMathpixCreds}
              onSave={handleSaveMathpix}
            />
            <MinerUCard parser={mineru} apiBase={apiBase} apiToken={apiToken} />
          </div>
        </section>

        {/* AI Models */}
        <section>
          <SectionHeader icon={Sparkles} title="AI Models" />

          <SubsectionHeader icon={Terminal} title="CLI" />
          <div className="space-y-2 mb-6">
            {cliProviders.map((provider) => (
              <CliProviderRow
                key={provider.name}
                provider={provider}
                state={getCardState(provider.name)}
                onTest={() => handleTestProvider(provider.name)}
              />
            ))}
          </div>

          <SubsectionHeader icon={Cloud} title="API" />
          <div className="space-y-3">
            {apiProviders.map((provider) => (
              <ApiProviderCard
                key={provider.name}
                provider={provider}
                state={getCardState(provider.name)}
                onApiKeyChange={(value) =>
                  updateCardState(provider.name, { apiKey: value })
                }
                onSave={() => handleSaveApiKey(provider.name)}
                onTest={() => handleTestProvider(provider.name)}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

// ── Section headers ────────────────────────────────────────────────

function SectionHeader({
  icon: Icon,
  title,
}: {
  icon: typeof Terminal
  title: string
}): JSX.Element {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon size={15} className="text-ink-tertiary" strokeWidth={1.6} />
      <span className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider">
        {title}
      </span>
      <div className="flex-1 h-px bg-paper-300 ml-2" />
    </div>
  )
}

function SubsectionHeader({
  icon: Icon,
  title,
}: {
  icon: typeof Terminal
  title: string
}): JSX.Element {
  return (
    <div className="flex items-center gap-1.5 mb-2 ml-1">
      <Icon size={12} className="text-ink-faint" strokeWidth={1.6} />
      <span className="text-[11px] font-medium text-ink-faint uppercase tracking-wider">
        {title}
      </span>
    </div>
  )
}

// ── Parsing provider cards ─────────────────────────────────────────

function MathPixCard({
  parser,
  creds,
  isSaving,
  onChange,
  onSave,
}: {
  parser: Parser | undefined
  creds: MathpixCreds
  isSaving: boolean
  onChange: (creds: MathpixCreds) => void
  onSave: () => void
}): JSX.Element {
  const available = parser?.available ?? false
  const canSave = creds.app_id.trim() !== '' && creds.app_key.trim() !== ''
  return (
    <CollapsibleProviderCard
      name={parser?.display_name ?? 'MathPix'}
      statusLabel={available ? 'ready' : 'needs credentials'}
      available={available}
    >
      <div className="space-y-2 mb-3">
        <input
          type="password"
          placeholder="App ID"
          value={creds.app_id}
          onChange={(event) =>
            onChange({ ...creds, app_id: event.target.value })
          }
          className="input font-mono text-sm"
        />
        <input
          type="password"
          placeholder="App Key"
          value={creds.app_key}
          onChange={(event) =>
            onChange({ ...creds, app_key: event.target.value })
          }
          className="input font-mono text-sm"
        />
      </div>

      <button
        type="button"
        onClick={onSave}
        disabled={!canSave || isSaving}
        className="btn-primary px-4 py-2 text-sm"
      >
        {isSaving ? '...' : 'Save credentials'}
      </button>
    </CollapsibleProviderCard>
  )
}

interface MinerUModel {
  model_type: string
  display_name: string
  repo_id: string
  installed: boolean
  downloading: boolean
  size_bytes: number
  last_error: string | null
  cache_path: string
}

function formatBytes(bytes: number): string {
  if (bytes <= 0) return '—'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = bytes
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

function MinerUCard({
  parser,
  apiBase,
  apiToken,
}: {
  parser: Parser | undefined
  apiBase: string
  apiToken: string
}): JSX.Element {
  const cliAvailable = parser?.available ?? false
  const installHint = parser?.install_hint
  const [models, setModels] = useState<MinerUModel[] | null>(null)
  const [pendingAction, setPendingAction] = useState<Record<string, 'download' | 'delete' | undefined>>({})
  const pollRef = useRef<number | null>(null)

  const fetchModels = async (): Promise<MinerUModel[] | null> => {
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        '/api/config/parsers/mineru/models',
      )
      if (!response.ok) return null
      const data = await response.json()
      setModels(data.models)
      return data.models as MinerUModel[]
    } catch {
      return null
    }
  }

  useEffect(() => {
    if (!cliAvailable) return
    void fetchModels()
  }, [cliAvailable, apiBase, apiToken])

  useEffect(() => {
    if (!models) return
    const anyDownloading = models.some((model) => model.downloading)
    if (!anyDownloading) {
      if (pollRef.current !== null) {
        window.clearInterval(pollRef.current)
        pollRef.current = null
      }
      return
    }
    if (pollRef.current !== null) return
    pollRef.current = window.setInterval(() => {
      void fetchModels()
    }, 2000)
    return () => {
      if (pollRef.current !== null) {
        window.clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [models])

  const handleDownload = async (modelType: string): Promise<void> => {
    setPendingAction((prev) => ({ ...prev, [modelType]: 'download' }))
    try {
      await apiFetch(
        apiBase,
        apiToken,
        `/api/config/parsers/mineru/models/${modelType}/download`,
        { method: 'POST' },
      )
      await fetchModels()
    } finally {
      setPendingAction((prev) => ({ ...prev, [modelType]: undefined }))
    }
  }

  const handleDelete = async (modelType: string): Promise<void> => {
    const confirmed = window.confirm(
      `Delete the cached ${modelType} model? You can re-download it later.`,
    )
    if (!confirmed) return
    setPendingAction((prev) => ({ ...prev, [modelType]: 'delete' }))
    try {
      await apiFetch(
        apiBase,
        apiToken,
        `/api/config/parsers/mineru/models/${modelType}`,
        { method: 'DELETE' },
      )
      await fetchModels()
    } finally {
      setPendingAction((prev) => ({ ...prev, [modelType]: undefined }))
    }
  }

  const overallStatusLabel = ((): string => {
    if (!cliAvailable) return 'not installed'
    if (!models) return 'checking…'
    if (models.some((model) => model.downloading)) return 'downloading…'
    const installedCount = models.filter((model) => model.installed).length
    if (installedCount === 0) return 'CLI ready · no models'
    if (installedCount === models.length) return 'installed'
    return `${installedCount}/${models.length} models`
  })()

  const overallAvailable =
    cliAvailable && !!models && models.every((model) => model.installed)

  return (
    <CollapsibleProviderCard
      name={parser?.display_name ?? 'MinerU'}
      statusLabel={overallStatusLabel}
      available={overallAvailable}
    >
      {!cliAvailable ? (
        <div className="text-sm text-ink-secondary">
          {installHint ?? (
            <>
              Install the <code className="code-inline">mineru</code> CLI to enable
              this parser. After install, you can download the model(s) here.
            </>
          )}
        </div>
      ) : models === null ? (
        <div className="flex items-center gap-2 text-sm text-ink-tertiary">
          <Loader2 size={14} className="animate-spin" />
          Checking model cache…
        </div>
      ) : (
        <div className="space-y-3">
          {models.map((model) => (
            <MinerUModelRow
              key={model.model_type}
              model={model}
              pendingAction={pendingAction[model.model_type]}
              onDownload={() => handleDownload(model.model_type)}
              onDelete={() => handleDelete(model.model_type)}
            />
          ))}
        </div>
      )}
    </CollapsibleProviderCard>
  )
}

function MinerUModelRow({
  model,
  pendingAction,
  onDownload,
  onDelete,
}: {
  model: MinerUModel
  pendingAction: 'download' | 'delete' | undefined
  onDownload: () => void
  onDelete: () => void
}): JSX.Element {
  const statusText = model.downloading
    ? 'downloading…'
    : model.installed
      ? formatBytes(model.size_bytes)
      : 'not downloaded'
  const statusColor = model.downloading
    ? 'text-accent'
    : model.installed
      ? 'text-success'
      : 'text-ink-faint'

  return (
    <div className="rounded-md border border-paper-200 bg-paper-50 px-3 py-2.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-ink truncate">
            {model.display_name}
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-[11px] min-w-0">
            <span className={`${statusColor} font-medium whitespace-nowrap shrink-0`}>
              {statusText}
            </span>
            <span className="text-ink-faint font-mono truncate min-w-0" title={model.repo_id}>
              {model.repo_id}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {model.installed ? (
            <button
              type="button"
              onClick={onDelete}
              disabled={model.downloading || pendingAction === 'delete'}
              className="btn-ghost px-2.5 py-1 text-xs"
              title="Delete cached model"
            >
              {pendingAction === 'delete' ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Trash2 size={12} />
              )}
              Delete
            </button>
          ) : (
            <button
              type="button"
              onClick={onDownload}
              disabled={model.downloading || pendingAction === 'download'}
              className="btn-primary px-2.5 py-1 text-xs"
              title={`Download via HuggingFace (${model.repo_id})`}
            >
              {model.downloading || pendingAction === 'download' ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <Download size={12} />
              )}
              {model.downloading ? 'Downloading' : 'Download'}
            </button>
          )}
        </div>
      </div>
      {model.last_error && !model.downloading && (
        <div className="mt-2 flex items-start gap-1.5 text-[11px] text-danger">
          <AlertTriangle size={12} className="shrink-0 mt-0.5" />
          <span className="break-words">{model.last_error}</span>
        </div>
      )}
    </div>
  )
}

