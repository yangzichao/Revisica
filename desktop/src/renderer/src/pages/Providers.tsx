import { useState, useEffect } from 'react'
import { CheckCircle2, XCircle, Loader2, Terminal, Cloud } from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'

// ── Types ──────────────────────────────────────────────────────────

interface Provider {
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

function isApiProvider(providerName: string): boolean {
  return (
    providerName.includes('api') ||
    providerName.includes('anthropic') ||
    providerName.includes('openai')
  )
}

// ── Main Component ─────────────────────────────────────────────────

export default function Providers({
  apiBase,
  apiToken,
}: {
  apiBase: string
  apiToken: string
}): JSX.Element {
  const [providers, setProviders] = useState<Provider[]>([])
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

  const cliProviders = providers.filter(
    (provider) => !isApiProvider(provider.name),
  )
  const apiProviders = providers.filter((provider) =>
    isApiProvider(provider.name),
  )

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-lg mx-auto px-8 py-12">
        <header className="mb-10">
          <h1 className="font-serif text-2xl font-semibold text-ink tracking-tight">
            Providers
          </h1>
          <p className="font-serif text-sm text-ink-tertiary italic mt-1">
            Configure how Revisica connects to AI models
          </p>
        </header>

        {/* CLI Providers */}
        <section className="mb-10">
          <SectionHeader icon={Terminal} title="CLI Providers" />
          <div className="space-y-2">
            {cliProviders.map((provider) => (
              <CliProviderRow
                key={provider.name}
                provider={provider}
                state={getCardState(provider.name)}
                onTest={() => handleTestProvider(provider.name)}
              />
            ))}
          </div>
        </section>

        {/* API Providers */}
        <section>
          <SectionHeader icon={Cloud} title="API Providers" />
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

// ── Sub-components ─────────────────────────────────────────────────

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

function CliProviderRow({
  provider,
  state,
  onTest,
}: {
  provider: Provider
  state: ProviderCardState
  onTest: () => void
}): JSX.Element {
  return (
    <div className="card flex items-center gap-3 px-4 py-3.5">
      <StatusDot available={provider.available} />
      <div className="flex-1 min-w-0">
        <span className="text-sm font-medium text-ink">
          {provider.display_name}
        </span>
        <span className="text-xs text-ink-faint ml-2">
          {provider.available ? 'ready' : 'not found'}
        </span>
      </div>
      <button
        onClick={onTest}
        disabled={state.isTesting}
        className="btn-ghost px-3 py-1.5"
      >
        {state.isTesting && <Loader2 size={12} className="animate-spin" />}
        Test
      </button>
      {state.testResult && <TestResultBadge result={state.testResult} />}
    </div>
  )
}

function ApiProviderCard({
  provider,
  state,
  onApiKeyChange,
  onSave,
  onTest,
}: {
  provider: Provider
  state: ProviderCardState
  onApiKeyChange: (value: string) => void
  onSave: () => void
  onTest: () => void
}): JSX.Element {
  return (
    <div className="card px-5 py-5">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <StatusDot available={provider.available} />
        <span className="text-sm font-medium text-ink">
          {provider.display_name}
        </span>
        <span className="text-xs text-ink-faint">
          {provider.available ? 'ready' : 'needs API key'}
        </span>
      </div>

      {/* API key input */}
      <div className="flex gap-2 mb-3">
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

      {/* Test button */}
      <div className="flex items-center gap-3">
        <button
          onClick={onTest}
          disabled={state.isTesting}
          className="btn-ghost px-3 py-1.5"
        >
          {state.isTesting && <Loader2 size={12} className="animate-spin" />}
          Test connection
        </button>
        {state.testResult && <TestResultBadge result={state.testResult} />}
      </div>
    </div>
  )
}
