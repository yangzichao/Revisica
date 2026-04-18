import { useState, type ReactNode } from 'react'
import { CheckCircle2, ChevronDown, ChevronUp, Loader2, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface Provider {
  name: string
  display_name: string
  model_family: string
  available: boolean
}

export interface ProviderCardState {
  apiKey: string
  isTesting: boolean
  isSaving: boolean
  testResult: { ok: boolean; message: string } | null
}

export const EMPTY_CARD_STATE: ProviderCardState = {
  apiKey: '',
  isTesting: false,
  isSaving: false,
  testResult: null,
}

export function isApiProvider(providerName: string): boolean {
  return (
    providerName.includes('api') ||
    providerName.includes('anthropic') ||
    providerName.includes('openai')
  )
}

export function StatusDot({ available }: { available: boolean }): JSX.Element {
  return (
    <div
      className={cn(
        'w-2.5 h-2.5 rounded-full shrink-0',
        available ? 'bg-success' : 'bg-paper-400',
      )}
    />
  )
}

export function TestResultBadge({
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

export function CollapsibleProviderCard({
  name,
  statusLabel,
  available,
  defaultExpanded = false,
  children,
}: {
  name: string
  statusLabel: string
  available: boolean
  defaultExpanded?: boolean
  children: ReactNode
}): JSX.Element {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <div className="card overflow-hidden">
      <button
        type="button"
        aria-expanded={isExpanded}
        onClick={() => setIsExpanded((previous) => !previous)}
        className="w-full flex items-center gap-3 px-4 py-3.5 text-left hover:bg-paper-100/60 transition-colors"
      >
        <StatusDot available={available} />
        <div className="flex-1 min-w-0 flex items-baseline gap-2">
          <span className="text-sm font-medium text-ink truncate">{name}</span>
          <span className="text-xs text-ink-faint shrink-0">{statusLabel}</span>
        </div>
        {isExpanded ? (
          <ChevronUp size={14} className="text-ink-faint shrink-0" strokeWidth={1.8} />
        ) : (
          <ChevronDown size={14} className="text-ink-faint shrink-0" strokeWidth={1.8} />
        )}
      </button>
      {isExpanded && (
        <div className="px-5 pb-5 pt-4 border-t border-paper-200/70">
          {children}
        </div>
      )}
    </div>
  )
}

export function CliProviderRow({
  provider,
  state,
  onTest,
}: {
  provider: Provider
  state: ProviderCardState
  onTest: () => void
}): JSX.Element {
  return (
    <CollapsibleProviderCard
      name={provider.display_name}
      statusLabel={provider.available ? 'ready' : 'not found'}
      available={provider.available}
    >
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onTest}
          disabled={state.isTesting}
          className="btn-ghost px-3 py-1.5"
        >
          {state.isTesting && <Loader2 size={12} className="animate-spin" />}
          Test
        </button>
        {state.testResult && <TestResultBadge result={state.testResult} />}
      </div>
    </CollapsibleProviderCard>
  )
}

export function ApiProviderCard({
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
    <CollapsibleProviderCard
      name={provider.display_name}
      statusLabel={provider.available ? 'ready' : 'needs API key'}
      available={provider.available}
    >
      <div className="flex gap-2 mb-3">
        <input
          type="password"
          placeholder="sk-..."
          value={state.apiKey}
          onChange={(event) => onApiKeyChange(event.target.value)}
          className="input font-mono text-sm"
        />
        <button
          type="button"
          onClick={onSave}
          disabled={!state.apiKey.trim() || state.isSaving}
          className="btn-primary px-4 py-2 text-sm shrink-0"
        >
          {state.isSaving ? '...' : 'Save'}
        </button>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onTest}
          disabled={state.isTesting}
          className="btn-ghost px-3 py-1.5"
        >
          {state.isTesting && <Loader2 size={12} className="animate-spin" />}
          Test connection
        </button>
        {state.testResult && <TestResultBadge result={state.testResult} />}
      </div>
    </CollapsibleProviderCard>
  )
}
