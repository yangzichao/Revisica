import { Sparkles, BookOpen, ArrowRight } from 'lucide-react'
import ModeCard from '@/components/ModeCard'
import ProviderStatusBadge from '@/components/ProviderStatusBadge'
import type { Provider } from '@/components/ProviderCard'
import EnginePicker from './EnginePicker'
import { VENUE_PROFILES } from './types'
import type { Engine, WizardAction, WizardState } from './types'

interface Step2ReviewPlanProps {
  state: WizardState
  dispatch: React.Dispatch<WizardAction>
  providers: Provider[]
  isLoadingProviders: boolean
  onSubmit: () => void
  isSubmitting: boolean
  errorMessage: string | null
}

export default function Step2ReviewPlan({
  state,
  dispatch,
  providers,
  isLoadingProviders,
  onSubmit,
  isSubmitting,
  errorMessage,
}: Step2ReviewPlanProps): JSX.Element {
  const hasAvailableProvider = providers.some((provider) => provider.available)
  const canSubmit = !isSubmitting && (isLoadingProviders || hasAvailableProvider)

  const handlePrimaryChange = (engine: Engine): void =>
    dispatch({ type: 'SET_PRIMARY_ENGINE', engine })

  const handleSecondaryEnabledChange = (enabled: boolean): void =>
    dispatch({ type: 'SET_SECONDARY_ENABLED', enabled })

  const handleSecondaryEngineChange = (engine: Engine): void =>
    dispatch({ type: 'SET_SECONDARY_ENGINE', engine })

  return (
    <div>
      <header className="mb-6">
        <h2 className="font-serif text-xl font-semibold text-ink tracking-tight">
          Review plan
        </h2>
        <p className="font-serif text-sm text-ink-tertiary italic mt-1">
          Pick a mode and start.
        </p>
      </header>

      <ProviderStatusBadge
        providers={providers}
        isLoading={isLoadingProviders}
      />

      <fieldset className="mb-6">
        <legend className="text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-3">
          Mode
        </legend>
        <div className="grid grid-cols-2 gap-3">
          <ModeCard
            icon={Sparkles}
            title="Polish"
            description="Writing style only"
            isSelected={state.mode === 'polish'}
            onClick={() => dispatch({ type: 'SET_MODE', mode: 'polish' })}
          />
          <ModeCard
            icon={BookOpen}
            title="Review"
            description="Full deep analysis"
            isSelected={state.mode === 'review'}
            onClick={() => dispatch({ type: 'SET_MODE', mode: 'review' })}
          />
        </div>
      </fieldset>

      {state.mode === 'review' && (
        <div className="mb-6 space-y-5">
          <div>
            <label className="block text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-2">
              Venue profile
            </label>
            <select
              value={state.venueProfile}
              onChange={(e) => dispatch({ type: 'SET_VENUE', venue: e.target.value })}
              className="input"
            >
              {VENUE_PROFILES.map((profile) => (
                <option key={profile} value={profile}>
                  {profile}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-3 cursor-pointer text-sm text-ink-secondary hover:text-ink transition-colors">
            <input
              type="checkbox"
              checked={state.llmProofReview}
              onChange={(e) =>
                dispatch({ type: 'TOGGLE_LLM_PROOF', value: e.target.checked })
              }
              className="w-4 h-4 rounded border-paper-400 accent-accent"
            />
            LLM proof review
            <span className="text-xs text-ink-faint">— deeper math analysis</span>
          </label>
        </div>
      )}

      <div className="mb-6">
        <EnginePicker
          primaryEngine={state.primaryEngine}
          secondaryEnabled={state.secondaryEnabled}
          secondaryEngine={state.secondaryEngine}
          onPrimaryChange={handlePrimaryChange}
          onSecondaryEnabledChange={handleSecondaryEnabledChange}
          onSecondaryChange={handleSecondaryEngineChange}
        />
      </div>

      {errorMessage && (
        <div className="rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger mb-4">
          {errorMessage}
        </div>
      )}

      <button
        type="button"
        onClick={onSubmit}
        disabled={!canSubmit}
        className="btn-primary w-full py-3"
      >
        {isSubmitting ? (
          'Starting...'
        ) : (
          <>
            {state.mode === 'polish' ? 'Start Polish' : 'Start Review'}
            <ArrowRight size={16} strokeWidth={2.2} />
          </>
        )}
      </button>
    </div>
  )
}
