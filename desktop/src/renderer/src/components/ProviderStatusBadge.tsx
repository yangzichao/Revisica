import { Link } from 'react-router-dom'
import { ArrowRight, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Provider } from './ProviderCard'

interface ProviderStatusBadgeProps {
  providers: Provider[]
  isLoading: boolean
}

function summarizeProviders(providers: Provider[]): string {
  const readyNames = providers
    .filter((provider) => provider.available)
    .map((provider) => provider.display_name)
  if (readyNames.length === 0) return 'No provider configured'
  if (readyNames.length <= 2) return readyNames.join(' · ')
  return `${readyNames.slice(0, 2).join(' · ')} +${readyNames.length - 2}`
}

export default function ProviderStatusBadge({
  providers,
  isLoading,
}: ProviderStatusBadgeProps): JSX.Element {
  const hasAvailable = providers.some((provider) => provider.available)

  if (isLoading) {
    return (
      <div className="card flex items-center gap-3 px-4 py-3 mb-5 text-sm text-ink-tertiary">
        <Loader2 size={13} className="animate-spin shrink-0" />
        Checking provider status...
      </div>
    )
  }

  if (!hasAvailable) {
    return (
      <Link
        to="/integrations"
        className={cn(
          'card flex items-center gap-3 px-4 py-3 mb-5',
          'border-danger/30 bg-danger/5 hover:border-danger/50',
          'transition-colors no-underline',
        )}
      >
        <AlertTriangle size={15} className="text-danger shrink-0" strokeWidth={1.8} />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-ink">
            No LLM provider configured
          </div>
          <div className="text-xs text-ink-tertiary mt-0.5">
            Add a provider in Integrations to start a review
          </div>
        </div>
        <ArrowRight size={13} className="text-danger shrink-0" strokeWidth={1.8} />
      </Link>
    )
  }

  return (
    <Link
      to="/integrations"
      className={cn(
        'card flex items-center gap-3 px-4 py-3 mb-5',
        'hover:border-paper-400 transition-colors no-underline',
      )}
    >
      <CheckCircle2 size={15} className="text-success shrink-0" strokeWidth={1.8} />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider">
          Providers
        </div>
        <div className="text-sm text-ink truncate">
          {summarizeProviders(providers)}
        </div>
      </div>
      <span className="text-xs text-ink-faint shrink-0">Manage</span>
    </Link>
  )
}
