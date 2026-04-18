import { useState, useCallback } from 'react'
import { Cpu, Loader2, Info, Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import { apiFetch } from '@/lib/api'
import {
  ApiProviderCard,
  CliProviderRow,
  EMPTY_CARD_STATE,
  StatusDot,
  type Provider,
  type ProviderCardState,
} from '@/components/ProviderCard'
import type { BackendMode, WizardState, WizardAction } from './types'

interface Step2Props {
  apiBase: string
  apiToken: string
  state: WizardState
  dispatch: React.Dispatch<WizardAction>
  providers: Provider[]
  isLoadingProviders: boolean
  onProvidersRefresh: () => void
}

const TABS: { key: BackendMode; label: string; caption: string }[] = [
  { key: 'auto', label: 'Auto', caption: 'Recommended' },
  { key: 'cli', label: 'CLI', caption: 'Subscription' },
  { key: 'api', label: 'API', caption: 'API key' },
  { key: 'ollama', label: 'Local', caption: 'Preview' },
]

function isApiProvider(name: string): boolean {
  return name.includes('api') || name.includes('anthropic') || name.includes('openai')
}

export default function Step2LlmAccess({
  apiBase,
  apiToken,
  state,
  dispatch,
  providers,
  isLoadingProviders,
  onProvidersRefresh,
}: Step2Props): JSX.Element {
  const [cardStates, setCardStates] = useState<Record<string, ProviderCardState>>({})

  const getCardState = useCallback(
    (name: string): ProviderCardState => cardStates[name] ?? EMPTY_CARD_STATE,
    [cardStates],
  )

  const updateCardState = (
    name: string,
    patch: Partial<ProviderCardState>,
  ): void => {
    setCardStates((previous) => ({
      ...previous,
      [name]: { ...(previous[name] ?? EMPTY_CARD_STATE), ...patch },
    }))
  }

  const handleSaveApiKey = async (providerName: string): Promise<void> => {
    const cardState = getCardState(providerName)
    if (!cardState.apiKey.trim()) return
    updateCardState(providerName, { isSaving: true })
    try {
      const response = await apiFetch(
        apiBase,
        apiToken,
        `/api/providers/${providerName}/config`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: cardState.apiKey.trim() }),
        },
      )
      if (response.ok) {
        onProvidersRefresh()
      }
    } catch {
      // ignore
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

  const switchTab = async (mode: BackendMode): Promise<void> => {
    dispatch({ type: 'SET_BACKEND_MODE', mode })
    if (mode === 'ollama') return
    try {
      await apiFetch(apiBase, apiToken, '/api/config/backend-mode', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backend_mode: mode }),
      })
    } catch {
      // Non-fatal — the backend still honors the default on review start
    }
  }

  const cliProviders = providers.filter((p) => !isApiProvider(p.name))
  const apiProviders = providers.filter((p) => isApiProvider(p.name))

  return (
    <div>
      <header className="mb-6">
        <h2 className="font-serif text-xl font-semibold text-ink tracking-tight">
          LLM access method
        </h2>
        <p className="font-serif text-sm text-ink-tertiary italic mt-1">
          How should Revisica talk to language models?
        </p>
      </header>

      {/* Tab selector */}
      <div
        role="tablist"
        className="flex gap-1 p-1 rounded-lg bg-paper-200/60 mb-5"
      >
        {TABS.map((tab) => {
          const isActive = state.backendMode === tab.key
          return (
            <button
              key={tab.key}
              role="tab"
              type="button"
              onClick={() => switchTab(tab.key)}
              className={cn(
                'flex-1 py-2.5 flex flex-col items-center gap-0.5',
                'text-sm font-semibold rounded-md',
                'transition-colors duration-150 border-none cursor-pointer',
                isActive
                  ? 'bg-paper-50 text-ink shadow-subtle'
                  : 'bg-transparent text-ink-tertiary hover:text-ink-secondary',
              )}
            >
              {tab.label}
              <span className="text-[10px] font-normal opacity-70">
                {tab.caption}
              </span>
            </button>
          )
        })}
      </div>

      {/* Tab panel */}
      {isLoadingProviders ? (
        <div className="flex items-center gap-2 text-xs text-ink-tertiary py-6">
          <Loader2 size={12} className="animate-spin" />
          Loading providers...
        </div>
      ) : state.backendMode === 'ollama' ? (
        <OllamaPreviewPanel />
      ) : state.backendMode === 'auto' ? (
        <AutoPanel
          providers={providers}
          getState={getCardState}
          onTest={handleTestProvider}
        />
      ) : state.backendMode === 'cli' ? (
        <CliPanel
          providers={cliProviders}
          getState={getCardState}
          onTest={handleTestProvider}
        />
      ) : (
        <ApiPanel
          providers={apiProviders}
          getState={getCardState}
          updateCardState={updateCardState}
          onSave={handleSaveApiKey}
          onTest={handleTestProvider}
        />
      )}
    </div>
  )
}

// ── Panels ──────────────────────────────────────────────────────────

function AutoPanel({
  providers,
  getState,
  onTest,
}: {
  providers: Provider[]
  getState: (name: string) => ProviderCardState
  onTest: (name: string) => void
}): JSX.Element {
  return (
    <div>
      <p className="text-xs text-ink-tertiary mb-3 leading-relaxed">
        Revisica will prefer any installed CLI, then fall back to saved API
        keys. Below is a combined view of every provider it can reach.
      </p>
      <div className="space-y-2">
        {providers.map((provider) => (
          <div
            key={provider.name}
            className="card flex items-center gap-3 px-4 py-3"
          >
            <StatusDot available={provider.available} />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-ink">
                {provider.display_name}
              </div>
              <div className="text-xs text-ink-faint mt-0.5">
                {isApiProvider(provider.name) ? 'API' : 'CLI'} ·{' '}
                {provider.available ? 'ready' : 'not configured'}
              </div>
            </div>
            <button
              type="button"
              onClick={() => onTest(provider.name)}
              disabled={getState(provider.name).isTesting}
              className="btn-ghost px-3 py-1.5 text-xs"
            >
              {getState(provider.name).isTesting && (
                <Loader2 size={12} className="animate-spin" />
              )}
              Test
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

function CliPanel({
  providers,
  getState,
  onTest,
}: {
  providers: Provider[]
  getState: (name: string) => ProviderCardState
  onTest: (name: string) => void
}): JSX.Element {
  return (
    <div className="space-y-2">
      {providers.map((provider) => (
        <CliProviderRow
          key={provider.name}
          provider={provider}
          state={getState(provider.name)}
          onTest={() => onTest(provider.name)}
        />
      ))}
      {providers.length === 0 && (
        <div className="text-xs text-ink-tertiary italic px-1">
          No CLI providers detected. Install Claude or Codex CLIs, or switch to
          API mode.
        </div>
      )}
    </div>
  )
}

function ApiPanel({
  providers,
  getState,
  updateCardState,
  onSave,
  onTest,
}: {
  providers: Provider[]
  getState: (name: string) => ProviderCardState
  updateCardState: (name: string, patch: Partial<ProviderCardState>) => void
  onSave: (name: string) => void
  onTest: (name: string) => void
}): JSX.Element {
  return (
    <div className="space-y-3">
      {providers.map((provider) => (
        <ApiProviderCard
          key={provider.name}
          provider={provider}
          state={getState(provider.name)}
          onApiKeyChange={(value) => updateCardState(provider.name, { apiKey: value })}
          onSave={() => onSave(provider.name)}
          onTest={() => onTest(provider.name)}
        />
      ))}
    </div>
  )
}

function OllamaPreviewPanel(): JSX.Element {
  return (
    <div>
      <div className="card px-5 py-5">
        <div className="flex items-center gap-3 mb-4">
          <Cpu size={18} className="text-accent" strokeWidth={1.5} />
          <span className="text-sm font-semibold text-ink">Ollama</span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-accent/10 text-accent">
            Coming soon
          </span>
        </div>
        <div className="text-xs text-ink-tertiary mb-4 leading-relaxed">
          Run open-weight models locally through an Ollama server. The UI is a
          preview this release — backend integration is deferred.
        </div>

        <label className="block text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-2">
          Endpoint
        </label>
        <input
          type="text"
          value="http://localhost:11434"
          disabled
          className="input font-mono text-sm mb-3 opacity-60"
        />

        <button
          type="button"
          disabled
          className="btn-ghost px-3 py-2 text-xs opacity-50 cursor-not-allowed"
        >
          <Search size={12} />
          Scan local models
        </button>
      </div>

      <div className="flex items-start gap-2 px-1 pt-4 text-xs text-ink-tertiary">
        <Info size={13} className="shrink-0 mt-0.5" />
        <span>
          Ollama support is in preview — please choose another access method
          to continue.
        </span>
      </div>
    </div>
  )
}

/**
 * Returns true when the selected backend mode has at least one available
 * provider. Used for Next-button validation.
 */
export function hasAvailableProviderForMode(
  providers: Provider[],
  mode: BackendMode,
): boolean {
  if (mode === 'ollama') return false
  const matches = providers.filter((p) => {
    if (mode === 'auto') return true
    const isApi = isApiProvider(p.name)
    return mode === 'api' ? isApi : !isApi
  })
  return matches.some((p) => p.available)
}
