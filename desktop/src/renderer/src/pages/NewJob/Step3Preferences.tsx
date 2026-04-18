import { useState, useEffect, useMemo } from 'react'
import { Sparkles, BookOpen, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react'
import { apiFetch } from '@/lib/api'
import ModeCard from '@/components/ModeCard'
import { VENUE_PROFILES } from './types'
import type { WizardState, WizardAction } from './types'

interface Step3Props {
  apiBase: string
  apiToken: string
  state: WizardState
  dispatch: React.Dispatch<WizardAction>
  onSubmit: () => void
  isSubmitting: boolean
  errorMessage: string | null
}

interface ModelChoice {
  value: string
  label: string
}

interface ModelRoutes {
  backend_mode: string
  writing: ModelChoice[]
  math: ModelChoice[]
}

export default function Step3Preferences({
  apiBase,
  apiToken,
  state,
  dispatch,
  onSubmit,
  isSubmitting,
  errorMessage,
}: Step3Props): JSX.Element {
  const [modelRoutes, setModelRoutes] = useState<ModelRoutes | null>(null)
  const [showOverrides, setShowOverrides] = useState(false)

  useEffect(() => {
    const load = async (): Promise<void> => {
      try {
        const response = await apiFetch(
          apiBase,
          apiToken,
          '/api/config/model-routes',
        )
        if (response.ok) {
          const data = await response.json()
          setModelRoutes(data)
        }
      } catch {
        // Leave as null — the override dropdowns gracefully degrade
      }
    }
    load()
    // Refetch when backend mode changes so the candidate list reflects the
    // provider set the user just picked in Step 2.
  }, [apiBase, apiToken, state.backendMode])

  const summaryLine = useMemo(() => {
    const labelFor = (override: string | null, options?: ModelChoice[]): string => {
      if (!override) return 'Auto'
      const match = options?.find((o) => o.value === override)
      return match?.label ?? override
    }
    const writing = labelFor(state.writingModelOverride, modelRoutes?.writing)
    const math = labelFor(state.mathModelOverride, modelRoutes?.math)
    if (writing === 'Auto' && math === 'Auto') return 'Auto'
    return `${writing} · ${math}`
  }, [state.writingModelOverride, state.mathModelOverride, modelRoutes])

  return (
    <div>
      <header className="mb-6">
        <h2 className="font-serif text-xl font-semibold text-ink tracking-tight">
          Preferences
        </h2>
        <p className="font-serif text-sm text-ink-tertiary italic mt-1">
          Pick a mode and start. Advanced options are collapsed below.
        </p>
      </header>

      {/* Mode cards */}
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

      {/* Review-only options */}
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

      {/* Model override disclosure */}
      <div className="mb-6">
        <button
          type="button"
          onClick={() => setShowOverrides((v) => !v)}
          className="flex items-center justify-between w-full text-xs uppercase tracking-wider text-ink-tertiary font-semibold py-2 border-none bg-transparent cursor-pointer"
        >
          <span className="flex items-center gap-2">
            Models: <span className="normal-case tracking-normal text-ink-secondary font-medium">{summaryLine}</span>
          </span>
          <span className="flex items-center gap-1">
            Customize
            {showOverrides ? (
              <ChevronUp size={13} />
            ) : (
              <ChevronDown size={13} />
            )}
          </span>
        </button>

        {showOverrides && (
          <div className="card px-4 py-4 mt-2 space-y-4">
            <ModelOverrideRow
              label="Writing model"
              description="Used for prose, structure, and venue review."
              value={state.writingModelOverride}
              options={modelRoutes?.writing}
              onChange={(value) =>
                dispatch({ type: 'SET_MODEL_OVERRIDE', role: 'writing', value })
              }
            />
            <ModelOverrideRow
              label="Math model"
              description="Used for proof review and adjudication."
              value={state.mathModelOverride}
              options={modelRoutes?.math}
              onChange={(value) =>
                dispatch({ type: 'SET_MODEL_OVERRIDE', role: 'math', value })
              }
            />
            <div className="text-[11px] text-ink-faint italic pt-1">
              Overrides apply to this run only — not saved.
            </div>
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger mb-4">
          {errorMessage}
        </div>
      )}

      <button
        type="button"
        onClick={onSubmit}
        disabled={isSubmitting}
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

function ModelOverrideRow({
  label,
  description,
  value,
  options,
  onChange,
}: {
  label: string
  description: string
  value: string | null
  options: ModelChoice[] | undefined
  onChange: (value: string | null) => void
}): JSX.Element {
  return (
    <div>
      <label className="block text-xs font-semibold text-ink-tertiary uppercase tracking-wider mb-1">
        {label}
      </label>
      <div className="text-[11px] text-ink-faint mb-2">{description}</div>
      <select
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value || null)}
        className="input"
      >
        <option value="">Auto (recommended)</option>
        {options?.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}
