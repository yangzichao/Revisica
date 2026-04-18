import { useState, useEffect } from 'react'
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Terminal,
  Cloud,
  HardDrive,
  FileText,
  Sparkles,
  Download,
  Trash2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'

// ── Types ──────────────────────────────────────────────────────────

type Runtime = 'cli' | 'api' | 'local'

interface BackendProvider {
  name: string
  display_name: string
  model_family: string
  available: boolean
}

interface ProviderCardState {
  apiKey: string
  isTesting: boolean
  isSaving: boolean
  testResult: { ok: boolean; message: string } | null
}

const EMPTY_CARD_STATE: ProviderCardState = {
  apiKey: '',
  isTesting: false,
  isSaving: false,
  testResult: null,
}

function runtimeFor(providerName: string): Runtime {
  if (providerName.includes('api') || providerName.includes('anthropic') || providerName.includes('openai')) {
    return 'api'
  }
  return 'cli'
}

function descriptionFor(providerName: string): string {
  if (providerName.includes('claude')) return 'Uses your Claude subscription'
  if (providerName.includes('codex')) return 'Uses your Codex CLI subscription'
  if (providerName.includes('anthropic') || providerName.includes('openai')) {
    return 'Direct API access with your key'
  }
  return ''
}

// ── Main Component ─────────────────────────────────────────────────

export default function Providers({
  apiBase,
  apiToken,
}: {
  apiBase: string
  apiToken: string
}): JSX.Element {
  const [providers, setProviders] = useState<BackendProvider[]>([])
  const [cardStates, setCardStates] = useState<Record<string, ProviderCardState>>({})
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
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchProviders()
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

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="animate-spin text-ink-faint" size={24} />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-lg mx-auto px-8 py-12">
        <header className="mb-10">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            Providers
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Configure how Revisica connects to AI models and parsers
          </p>
        </header>

        {/* Document Parsing */}
        <section className="mb-10">
          <SectionHeader icon={FileText} title="Document Parsing" />
          <div className="space-y-3">
            <MathPixCard />
            <MinerUCard />
          </div>
        </section>

        {/* AI Models */}
        <section>
          <SectionHeader icon={Sparkles} title="AI Models" />
          <div className="space-y-3">
            {providers.map((provider) => {
              const state = getCardState(provider.name)
              return runtimeFor(provider.name) === 'api' ? (
                <ApiProviderCard
                  key={provider.name}
                  provider={provider}
                  state={state}
                  onApiKeyChange={(value) =>
                    updateCardState(provider.name, { apiKey: value })
                  }
                  onSave={() => handleSaveApiKey(provider.name)}
                  onTest={() => handleTestProvider(provider.name)}
                />
              ) : (
                <CliProviderCard
                  key={provider.name}
                  provider={provider}
                  state={state}
                  onTest={() => handleTestProvider(provider.name)}
                />
              )
            })}
          </div>
        </section>
      </div>
    </div>
  )
}

// ── Section + shared primitives ────────────────────────────────────

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

function StatusDot({ available }: { available: boolean }): JSX.Element {
  return (
    <div
      className={cn(
        'w-2.5 h-2.5 rounded-full shrink-0',
        available ? 'bg-success' : 'bg-paper-400',
      )}
    />
  )
}

function RuntimeBadge({ runtime }: { runtime: Runtime }): JSX.Element {
  const config = {
    cli: { icon: Terminal, label: 'CLI' },
    api: { icon: Cloud, label: 'API' },
    local: { icon: HardDrive, label: 'Local' },
  }[runtime]
  const Icon = config.icon
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-paper-200 text-[10px] font-medium text-ink-tertiary uppercase tracking-wider">
      <Icon size={10} strokeWidth={2} />
      {config.label}
    </span>
  )
}

function TestResultBadge({
  result,
}: {
  result: { ok: boolean; message: string }
}): JSX.Element {
  return (
    <span
      className={cn(
        'flex items-center gap-1 text-xs font-medium',
        result.ok ? 'text-success' : 'text-danger',
      )}
    >
      {result.ok ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
      {result.message}
    </span>
  )
}

// ── Provider card shell ────────────────────────────────────────────

function ProviderCardShell({
  available,
  displayName,
  runtime,
  description,
  children,
  footer,
}: {
  available: boolean
  displayName: string
  runtime: Runtime
  description?: string
  children?: React.ReactNode
  footer?: React.ReactNode
}): JSX.Element {
  return (
    <div className="card px-5 py-4">
      <div className="flex items-center gap-3">
        <StatusDot available={available} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-ink">{displayName}</span>
            <RuntimeBadge runtime={runtime} />
          </div>
          {description && (
            <div className="text-xs text-ink-tertiary mt-0.5">{description}</div>
          )}
        </div>
      </div>
      {children && <div className="mt-4">{children}</div>}
      {footer && (
        <div className="mt-3 flex items-center gap-3">{footer}</div>
      )}
    </div>
  )
}

// ── AI Model cards (CLI + API) ─────────────────────────────────────

function CliProviderCard({
  provider,
  state,
  onTest,
}: {
  provider: BackendProvider
  state: ProviderCardState
  onTest: () => void
}): JSX.Element {
  return (
    <ProviderCardShell
      available={provider.available}
      displayName={provider.display_name}
      runtime="cli"
      description={descriptionFor(provider.name)}
      footer={
        <>
          <span className="text-xs text-ink-faint">
            {provider.available ? 'Ready' : 'Binary not found on PATH'}
          </span>
          <div className="flex-1" />
          <button
            onClick={onTest}
            disabled={state.isTesting || !provider.available}
            className="btn-ghost px-3 py-1.5"
          >
            {state.isTesting && <Loader2 size={12} className="animate-spin" />}
            Test
          </button>
          {state.testResult && <TestResultBadge result={state.testResult} />}
        </>
      }
    />
  )
}

function ApiProviderCard({
  provider,
  state,
  onApiKeyChange,
  onSave,
  onTest,
}: {
  provider: BackendProvider
  state: ProviderCardState
  onApiKeyChange: (value: string) => void
  onSave: () => void
  onTest: () => void
}): JSX.Element {
  return (
    <ProviderCardShell
      available={provider.available}
      displayName={provider.display_name}
      runtime="api"
      description={descriptionFor(provider.name)}
      footer={
        <>
          <button
            onClick={onTest}
            disabled={state.isTesting}
            className="btn-ghost px-3 py-1.5"
          >
            {state.isTesting && <Loader2 size={12} className="animate-spin" />}
            Test connection
          </button>
          {state.testResult && <TestResultBadge result={state.testResult} />}
        </>
      }
    >
      <div className="flex gap-2">
        <input
          type="password"
          placeholder="sk-..."
          value={state.apiKey}
          onChange={(event) => onApiKeyChange(event.target.value)}
          className="input font-mono text-sm"
        />
        <button
          onClick={onSave}
          disabled={!state.apiKey.trim() || state.isSaving}
          className="btn-primary px-4 py-2 text-sm shrink-0"
        >
          {state.isSaving ? '...' : 'Save'}
        </button>
      </div>
    </ProviderCardShell>
  )
}

// ── Parsing provider placeholders ──────────────────────────────────
// Backend for parsers lives in ingestion/ and is not yet exposed via
// /api/providers. These cards show the final shape; hook up real
// state when the backend endpoint lands.

function MathPixCard(): JSX.Element {
  return (
    <ProviderCardShell
      available={false}
      displayName="MathPix"
      runtime="api"
      description="Cloud PDF → Markdown with OCR"
    >
      <div className="space-y-2">
        <input
          type="password"
          placeholder="App ID"
          disabled
          className="input font-mono text-sm"
        />
        <input
          type="password"
          placeholder="App Key"
          disabled
          className="input font-mono text-sm"
        />
      </div>
      <div className="mt-3 text-xs text-ink-faint">
        For now, set <code className="code-inline">MATHPIX_APP_ID</code> and{' '}
        <code className="code-inline">MATHPIX_APP_KEY</code> in your environment.
      </div>
    </ProviderCardShell>
  )
}

function MinerUCard(): JSX.Element {
  return (
    <ProviderCardShell
      available={false}
      displayName="MinerU"
      runtime="local"
      description="Local PDF → Markdown model"
    >
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs text-ink-tertiary">
          <span className="shrink-0">Model</span>
          <select
            disabled
            className="flex-1 px-2 py-1 rounded-md bg-paper-100 border border-paper-300 text-ink-tertiary text-xs"
          >
            <option>mineru-base (not installed)</option>
          </select>
        </div>

        <div>
          <div className="flex items-center justify-between text-[11px] text-ink-faint mb-1.5">
            <span>Not downloaded</span>
            <span className="font-mono">— / —</span>
          </div>
          <div className="h-1.5 rounded-full bg-paper-200 overflow-hidden">
            <div className="h-full w-0 bg-accent/40 transition-all" />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button disabled className="btn-ghost px-3 py-1.5">
            <Download size={12} />
            Download model
          </button>
          <button disabled className="btn-ghost px-3 py-1.5">
            <Trash2 size={12} />
            Delete
          </button>
        </div>
      </div>
      <div className="mt-3 text-xs text-ink-faint">
        Download management coming soon. Install{' '}
        <code className="code-inline">mineru</code> CLI manually for now.
      </div>
    </ProviderCardShell>
  )
}
