import { useState, useEffect } from 'react'
import {
  Loader2,
  Terminal,
  Cloud,
  FileText,
  Sparkles,
  Download,
  Trash2,
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
            <MinerUCard parser={mineru} />
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

function MinerUCard({ parser }: { parser: Parser | undefined }): JSX.Element {
  const available = parser?.available ?? false
  const installHint = parser?.install_hint
  return (
    <CollapsibleProviderCard
      name={parser?.display_name ?? 'MinerU'}
      statusLabel={available ? 'installed' : 'not installed'}
      available={available}
    >
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs text-ink-tertiary">
          <span className="shrink-0">Model</span>
          <select
            disabled
            className="flex-1 px-2 py-1 rounded-md bg-paper-100 border border-paper-300 text-ink-tertiary text-xs"
          >
            <option>
              {available ? 'mineru-base' : 'mineru-base (not installed)'}
            </option>
          </select>
        </div>

        <div>
          <div className="flex items-center justify-between text-[11px] text-ink-faint mb-1.5">
            <span>{available ? 'Installed' : 'Not downloaded'}</span>
            <span className="font-mono">— / —</span>
          </div>
          <div className="h-1.5 rounded-full bg-paper-200 overflow-hidden">
            <div
              className={`h-full ${available ? 'w-full bg-success/50' : 'w-0 bg-accent/40'} transition-all`}
            />
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

      {!available && installHint && (
        <div className="mt-3 text-xs text-ink-faint">
          {installHint}
        </div>
      )}
      {!available && !installHint && (
        <div className="mt-3 text-xs text-ink-faint">
          Download management coming soon. Install{' '}
          <code className="code-inline">mineru</code> CLI manually for now.
        </div>
      )}
    </CollapsibleProviderCard>
  )
}

